"""
IMAP-specific parser implementation using PEG grammar.

This module implements RFC 9051 compliant IMAP response parsing using
a vendored PEG parser with proper grammar definitions.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

from .base import RFCParser, ParseError, ParseResult, ParserConfig
from .._vendor.arpeggio import ParserPython, SemanticError, NoMatch
from . import imap_grammar


# IMAP Data Structures
@dataclass
class IMAPEnvelope:
    """IMAP ENVELOPE structure."""

    date: Optional[str] = None
    subject: Optional[str] = None
    from_addr: Optional[List[Dict[str, str]]] = None
    sender: Optional[List[Dict[str, str]]] = None
    reply_to: Optional[List[Dict[str, str]]] = None
    to: Optional[List[Dict[str, str]]] = None
    cc: Optional[List[Dict[str, str]]] = None
    bcc: Optional[List[Dict[str, str]]] = None
    in_reply_to: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class IMAPFetchResponse:
    """IMAP FETCH response structure."""

    message_number: int
    uid: Optional[int] = None
    flags: Optional[List[str]] = None
    internal_date: Optional[datetime] = None
    envelope: Optional[IMAPEnvelope] = None
    body_structure: Optional[Dict] = None
    body: Optional[str] = None


# Grammar is now defined in imap_grammar.py


class IMAPParser(RFCParser):
    """IMAP parser using PEG grammar."""

    def __init__(self, config: Optional[ParserConfig] = None):
        """Initialize IMAP parser."""
        self.config = config or ParserConfig()

        # Create Arpeggio parser with skipws=False for precise IMAP parsing
        self._parser = ParserPython(
            imap_grammar.response,
            debug=self.config.debug,
            memoization=self.config.memoization,
            reduce_tree=self.config.reduce_tree,
            ignore_case=self.config.ignore_case,
            skipws=False,  # IMAP requires precise whitespace handling
        )

        # Specific parsers for different rules
        self._fetch_parser = ParserPython(imap_grammar.fetch_response, skipws=False)
        self._envelope_parser = ParserPython(imap_grammar.envelope, skipws=False)

    def parse(self, text: str, rule: Optional[str] = None) -> ParseResult:
        """Parse IMAP response text."""
        try:
            if rule:
                return self.parse_partial(text, rule)

            parse_tree = self._parser.parse(text.strip())
            result = self._transform_tree(parse_tree)
            return ParseResult.success_result(result)

        except (NoMatch, SemanticError) as e:
            error = ParseError(
                message=str(e),
                position=getattr(e, "position", None),
                line=getattr(e, "line", None),
                column=getattr(e, "col", None),
            )
            return ParseResult.error_result(error)
        except Exception as e:
            error = ParseError(f"Unexpected parsing error: {e}")
            return ParseResult.error_result(error)

    def parse_partial(self, text: str, rule: str) -> ParseResult:
        """Parse text starting from specific rule."""
        try:
            if rule == "fetch_response":
                parse_tree = self._fetch_parser.parse(text.strip())
                result = self._transform_fetch_response(parse_tree, text.strip())
            elif rule == "envelope":
                parse_tree = self._envelope_parser.parse(text.strip())
                result = self._transform_envelope(parse_tree)
            else:
                raise ParseError(f"Unknown rule: {rule}")

            return ParseResult.success_result(result)

        except (NoMatch, SemanticError) as e:
            error = ParseError(
                message=str(e),
                position=getattr(e, "position", None),
                line=getattr(e, "line", None),
                column=getattr(e, "col", None),
            )
            return ParseResult.error_result(error)
        except Exception as e:
            error = ParseError(f"Unexpected parsing error: {e}")
            return ParseResult.error_result(error)

    def parse_fetch_response(self, text: str) -> ParseResult:
        """Parse FETCH response specifically."""
        return self.parse_partial(text, "fetch_response")

    def parse_envelope(self, text: str) -> ParseResult:
        """Parse ENVELOPE data specifically."""
        return self.parse_partial(text, "envelope")

    def _transform_tree(self, tree) -> Any:
        """Transform parse tree to Python objects."""
        # This is a simplified transformation
        # In a full implementation, you'd use Arpeggio's visitor pattern
        return str(tree)

    def _transform_fetch_response(self, tree, original_text=None) -> IMAPFetchResponse:
        """Transform FETCH response parse tree."""
        # Extract data using tree structure navigation
        # The tree is: [*, sp, number, sp, FETCH, sp, fetch_msg_att]

        try:
            # Extract message number (position 2 in tree)
            message_number = int(tree[2].value) if len(tree) > 2 else 0
            result = IMAPFetchResponse(message_number=message_number)

            # Navigate to fetch_msg_att (the parenthesized list at position 6)
            if len(tree) > 6:
                fetch_att_list = tree[6]  # This is the fetch_msg_att

                # Parse fetch attributes by walking the tree
                self._extract_fetch_attributes(fetch_att_list, result, tree, original_text)

            return result

        except Exception:
            # Fallback to regex if tree navigation fails
            import re
            # Tree navigation failed, fall back to regex parsing

            # Get original text from tree - use the parse tree input if available
            if hasattr(tree, "_input"):
                # Tree has access to original input
                start_pos = getattr(tree, "_pos_start", 0)
                end_pos = getattr(tree, "_pos_end", len(tree._input))
                text = tree._input[start_pos:end_pos]
            else:
                # Fallback to tree string representation cleanup
                text = str(tree).replace(" | ", " ").replace("|", "")

            # Extract message number
            match = re.search(r"^\* (\d+) FETCH", text)
            message_number = int(match.group(1)) if match else 0

            result = IMAPFetchResponse(message_number=message_number)

            # Extract UID
            uid_match = re.search(r"UID (\d+)", text)
            if uid_match:
                result.uid = int(uid_match.group(1))

            # Extract flags
            flags_match = re.search(r"FLAGS \(([^)]*)\)", text)
            if flags_match:
                flags_str = flags_match.group(1).strip()
                result.flags = flags_str.split() if flags_str else []

            # Extract internal date
            date_match = re.search(r'INTERNALDATE "([^"]+)"', text)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    result.internal_date = datetime.strptime(date_str, "%d-%b-%Y %H:%M:%S %z")
                except ValueError:
                    result.internal_date = date_str

            return result

    def _extract_fetch_attributes(
        self,
        fetch_att_list,
        result: IMAPFetchResponse,
        original_tree=None,
        original_text=None,
    ):
        """Extract fetch attributes from the parsed list."""
        # This is a simplified extraction - would need more sophisticated logic
        # for a complete implementation

        # Walk the tree and collect nodes as a list so we can look ahead
        all_nodes = list(self._walk_tree(fetch_att_list))

        # Process nodes looking for patterns
        for i, node in enumerate(all_nodes):
            if hasattr(node, "value"):
                value = node.value
                if value == "UID":
                    # Look for next numeric value
                    for j in range(i + 1, len(all_nodes)):
                        next_node = all_nodes[j]
                        if hasattr(next_node, "value") and next_node.value.isdigit():
                            result.uid = int(next_node.value)
                            break
                elif value == "FLAGS":
                    # Look for flag keywords after this
                    flags = set()  # Use set to avoid duplicates
                    found_opening_paren = False
                    for j in range(i + 1, len(all_nodes)):
                        next_node = all_nodes[j]
                        if hasattr(next_node, "value"):
                            if next_node.value == "(":
                                found_opening_paren = True
                            elif next_node.value.startswith("\\") or next_node.value.startswith("$"):
                                flags.add(next_node.value)
                            elif next_node.value == ")":
                                break  # End of flags list
                    if found_opening_paren:
                        result.flags = list(flags)  # Set to empty list even if no flags
                elif value == "INTERNALDATE":
                    # Reconstruct date string from individual quoted chars
                    date_chars = []
                    capturing = False
                    for j in range(i + 1, len(all_nodes)):
                        next_node = all_nodes[j]
                        if hasattr(next_node, "value"):
                            if next_node.value == '"':
                                if capturing:
                                    break  # End quote
                                else:
                                    capturing = True  # Start quote
                            elif capturing:
                                date_chars.append(next_node.value)

                    if date_chars:
                        date_str = "".join(date_chars)
                        try:
                            result.internal_date = datetime.strptime(date_str, "%d-%b-%Y %H:%M:%S %z")
                        except ValueError:
                            result.internal_date = date_str
                elif value == "ENVELOPE":
                    # Extract ENVELOPE data using original text
                    if original_text:
                        # Extract ENVELOPE using balanced parentheses parsing
                        env_start = original_text.find("ENVELOPE ")
                        if env_start != -1:
                            paren_start = original_text.find("(", env_start)
                            if paren_start != -1:
                                envelope_text = self._extract_balanced_parentheses(original_text, paren_start)
                                env_match = True
                            else:
                                env_match = None
                        else:
                            env_match = None
                        if env_match:
                            result.envelope = self._parse_envelope_from_text(envelope_text)
                        # If no match, envelope remains None
                elif value == "BODYSTRUCTURE":
                    # Extract BODYSTRUCTURE data using balanced parentheses parsing
                    if original_text:
                        body_start = original_text.find("BODYSTRUCTURE ")
                        if body_start != -1:
                            paren_start = original_text.find("(", body_start)
                            if paren_start != -1:
                                bodystructure_text = self._extract_balanced_parentheses(original_text, paren_start)
                                result.body_structure = self._parse_bodystructure_from_text(bodystructure_text)

    def _get_original_text(self, tree):
        """Get original text from parse tree."""
        # Use the tree's position and input to reconstruct text
        if hasattr(tree, "_input") and hasattr(tree, "_pos_start") and hasattr(tree, "_pos_end"):
            return tree._input[tree._pos_start : tree._pos_end]
        else:
            # Fallback to string representation
            return str(tree).replace(" | ", " ").replace("|", "")

    def _walk_tree(self, node):
        """Walk the parse tree yielding all nodes."""
        yield node
        if hasattr(node, "__iter__"):
            try:
                for child in node:
                    yield from self._walk_tree(child)
            except TypeError:
                pass  # Node is not iterable

    def _find_next_number(self, start_node):
        """Find the next numeric value after a node."""
        # Simplified implementation
        return None

    def _find_next_flags(self, start_node):
        """Find flag list after FLAGS keyword."""
        # Simplified implementation
        return None

    def _find_next_quoted_string(self, start_node):
        """Find quoted string after a keyword."""
        # Simplified implementation
        return None

    def _transform_envelope(self, tree) -> IMAPEnvelope:
        """Transform ENVELOPE parse tree."""
        # Simplified transformation
        return IMAPEnvelope()

    def _extract_envelope_data(self, all_nodes, start_index):
        """Extract ENVELOPE data from nodes starting at given index."""
        # Simple approach: find the envelope parse tree node and extract original text
        # Then use regex to parse the envelope structure

        # Find the envelope parenthesized structure in the tree
        paren_count = 0
        capturing = False
        envelope_start = None
        envelope_end = None

        for i in range(start_index, len(all_nodes)):
            node = all_nodes[i]
            if hasattr(node, "value"):
                value = node.value
                if value == "(":
                    if not capturing:
                        capturing = True
                        envelope_start = i
                    paren_count += 1
                elif value == ")":
                    paren_count -= 1
                    if paren_count == 0 and capturing:
                        envelope_end = i
                        break

        if envelope_start is not None and envelope_end is not None:
            # Get original text from first node if available
            first_node = all_nodes[envelope_start]
            if hasattr(first_node, "_input") and hasattr(first_node, "_pos_start"):
                # Try to reconstruct envelope from original input
                import re

                input_text = first_node._input

                # Find ENVELOPE in the input
                env_match = re.search(r"ENVELOPE\s+(\([^)]+(?:\([^)]*\)[^)]*)*\))", input_text)
                if env_match:
                    envelope_text = env_match.group(1)
                    return self._parse_envelope_from_text(envelope_text)

        # Fallback: return None if we can't extract envelope data
        return None

    def _extract_bodystructure_data(self, all_nodes, start_index):
        """Extract BODYSTRUCTURE data from nodes starting at given index."""
        # For now, return a simplified representation
        # Full BODYSTRUCTURE parsing would be quite complex
        bodystructure_text = []
        paren_count = 0
        capturing = False

        for i in range(start_index, len(all_nodes)):
            node = all_nodes[i]
            if hasattr(node, "value"):
                value = node.value
                if value == "(":
                    if not capturing:
                        capturing = True
                    paren_count += 1
                    bodystructure_text.append(value)
                elif value == ")":
                    paren_count -= 1
                    bodystructure_text.append(value)
                    if paren_count == 0 and capturing:
                        break
                elif capturing:
                    bodystructure_text.append(value)

        if bodystructure_text:
            return {"raw": "".join(bodystructure_text)}
        return None

    def _reconstruct_field(self, field_parts):
        """Reconstruct a field from its parts."""
        if not field_parts:
            return None
        # Join parts, handling quotes properly
        result = "".join(str(part) for part in field_parts)
        return result

    def _clean_string(self, s):
        """Clean up a string by removing quotes and handling NIL."""
        if not s or s == "NIL":
            return None
        # Remove surrounding quotes
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        return s

    def _parse_address_list(self, addr_text):
        """Parse address list into structured format."""
        if not addr_text or addr_text == "NIL":
            return None

        # Parse address structure: (("name" NIL "mailbox" "host") ...)
        # Each address is: (name route mailbox host)
        addresses = []

        # Handle nested parentheses for address lists

        # Find individual address structures - handle nested parentheses better
        # Pattern for nested address lists like ((addr1)(addr2)) or (addr)
        if addr_text.startswith("(("):
            # Multiple addresses in nested format - extract inner parentheses content
            # Find content between outer parentheses, then extract individual addresses
            inner = addr_text[1:-1]  # Remove outer parentheses
            addr_pattern = r"\(([^)]+)\)"  # Simple pattern for inner addresses
            matches = re.findall(addr_pattern, inner)
        else:
            # Single address - remove parentheses
            matches = [addr_text.strip("()")]

        for match in matches:
            # Parse individual address: "name" NIL "mailbox" "host"
            parts = self._split_address_parts(match)
            if len(parts) >= 4:
                name = self._clean_string(parts[0]) if parts[0] != "NIL" else None
                route = self._clean_string(parts[1]) if parts[1] != "NIL" else None
                mailbox = self._clean_string(parts[2]) if parts[2] != "NIL" else None
                host = self._clean_string(parts[3]) if parts[3] != "NIL" else None

                # Construct email address
                if mailbox and host:
                    email = f"{mailbox}@{host}"
                    address_info = {
                        "name": name,
                        "email": email,
                        "mailbox": mailbox,
                        "host": host,
                    }
                    if route:
                        address_info["route"] = route
                    addresses.append(address_info)

        return addresses if addresses else None

    def _split_address_parts(self, address_text):
        """Split address text into parts, handling quoted strings."""
        parts = []
        current = ""
        in_quotes = False
        i = 0

        while i < len(address_text):
            char = address_text[i]
            if char == '"' and (i == 0 or address_text[i - 1] != "\\"):
                in_quotes = not in_quotes
                current += char
            elif char == " " and not in_quotes:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
            i += 1

        if current.strip():
            parts.append(current.strip())

        return parts

    def _parse_envelope_from_text(self, envelope_text):
        """Parse ENVELOPE from extracted text using regex."""

        # ENVELOPE structure: (date subject from sender reply-to to cc bcc in-reply-to message-id)
        # This is a simplified parser that handles basic cases

        # Remove outer parentheses
        if envelope_text.startswith("(") and envelope_text.endswith(")"):
            inner = envelope_text[1:-1]
        else:
            inner = envelope_text

        # Split on quoted strings and NIL, handling nested parentheses
        fields = []
        current = ""
        in_quotes = False
        paren_count = 0
        i = 0

        while i < len(inner):
            char = inner[i]
            if char == '"' and (i == 0 or inner[i - 1] != "\\"):
                in_quotes = not in_quotes
                current += char
            elif char == "(" and not in_quotes:
                paren_count += 1
                current += char
            elif char == ")" and not in_quotes:
                paren_count -= 1
                current += char
            elif char == " " and not in_quotes and paren_count == 0:
                # End of field
                if current.strip():
                    fields.append(current.strip())
                current = ""
            else:
                current += char
            i += 1

        # Add last field
        if current.strip():
            fields.append(current.strip())

        # Create envelope from fields
        if len(fields) >= 2:
            return IMAPEnvelope(
                date=self._clean_string(fields[0]) if len(fields) > 0 else None,
                subject=self._clean_string(fields[1]) if len(fields) > 1 else None,
                from_addr=self._parse_address_list(fields[2]) if len(fields) > 2 else None,
                sender=self._parse_address_list(fields[3]) if len(fields) > 3 else None,
                reply_to=self._parse_address_list(fields[4]) if len(fields) > 4 else None,
                to=self._parse_address_list(fields[5]) if len(fields) > 5 else None,
                cc=self._parse_address_list(fields[6]) if len(fields) > 6 else None,
                bcc=self._parse_address_list(fields[7]) if len(fields) > 7 else None,
                in_reply_to=self._clean_string(fields[8]) if len(fields) > 8 else None,
                message_id=self._clean_string(fields[9]) if len(fields) > 9 else None,
            )
        return None

    def _parse_bodystructure_from_text(self, bodystructure_text):
        """Parse BODYSTRUCTURE from extracted text to extract content types and structure."""

        # BODYSTRUCTURE can be either single-part or multi-part
        # Single-part: ("type" "subtype" params NIL NIL encoding size ...)
        # Multi-part: (part1 part2 ... "multipart-subtype" ...)

        result = {
            "raw": bodystructure_text,
            "parts": [],
            "content_type": None,
            "is_multipart": False,
            "size": None,
        }

        # Remove outer parentheses
        if bodystructure_text.startswith("(") and bodystructure_text.endswith(")"):
            inner = bodystructure_text[1:-1]
        else:
            inner = bodystructure_text

        # Try to detect if this is multipart by looking for nested structures
        if inner.count("(") > 0:
            # Check if it starts with a quoted string (single-part) or parentheses (multi-part)
            first_token = inner.strip().split()[0] if inner.strip() else ""

            if first_token.startswith('"'):
                # Single-part message
                result["is_multipart"] = False
                parts = self._split_bodystructure_parts(inner)
                if len(parts) >= 2:
                    main_type = self._clean_string(parts[0])
                    sub_type = self._clean_string(parts[1])
                    result["content_type"] = f"{main_type}/{sub_type}".lower()

                    # Try to extract size (usually around position 6-7)
                    for i, part in enumerate(parts[5:8]):  # Check positions 5, 6, 7
                        if part.isdigit():
                            result["size"] = int(part)
                            break
            else:
                # Multi-part message
                result["is_multipart"] = True

                # For multipart, find the subtype after the individual parts
                # Structure: (part1)(part2)..."subtype"...

                # Split by top-level elements to find the subtype
                elements = self._split_bodystructure_parts(inner)

                # Count actual parts (those starting with parentheses)
                part_count = 0
                subtype = None

                for element in elements:
                    if element.startswith("("):
                        part_count += 1
                    elif element.startswith('"') and element.endswith('"'):
                        # This is likely the multipart subtype
                        potential_subtype = element.strip('"').upper()
                        if potential_subtype in [
                            "ALTERNATIVE",
                            "MIXED",
                            "RELATED",
                            "PARALLEL",
                            "SIGNED",
                            "ENCRYPTED",
                        ]:
                            subtype = potential_subtype
                            break

                if subtype:
                    result["content_type"] = f"multipart/{subtype.lower()}"
                else:
                    result["content_type"] = "multipart/unknown"

                result["parts"] = [f"Part {i + 1}" for i in range(part_count)] if part_count > 0 else ["Part 1"]

        return result

    def _split_bodystructure_parts(self, text):
        """Split BODYSTRUCTURE parts, handling quoted strings and nested structures."""
        parts = []
        current = ""
        in_quotes = False
        paren_count = 0
        i = 0

        while i < len(text):
            char = text[i]
            if char == '"' and (i == 0 or text[i - 1] != "\\"):
                in_quotes = not in_quotes
                current += char
            elif char == "(" and not in_quotes:
                if paren_count == 0 and current.strip():
                    # We're starting a new parentheses group, save previous content
                    parts.append(current.strip())
                    current = ""
                paren_count += 1
                current += char
            elif char == ")" and not in_quotes:
                paren_count -= 1
                current += char
                if paren_count == 0:
                    # We've completed a parentheses group
                    if current.strip():
                        parts.append(current.strip())
                        current = ""
            elif char == " " and not in_quotes and paren_count == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
            i += 1

        if current.strip():
            parts.append(current.strip())

        return parts

    def _extract_balanced_parentheses(self, text, start_pos):
        """Extract a balanced parentheses expression starting at start_pos."""
        if start_pos >= len(text) or text[start_pos] != "(":
            return ""

        paren_count = 0
        result = ""

        for i in range(start_pos, len(text)):
            char = text[i]
            result += char

            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
                if paren_count == 0:
                    break

        return result


# Convenience functions for common IMAP parsing tasks
def parse_fetch_response(text: str) -> ParseResult:
    """Parse a FETCH response line."""
    parser = IMAPParser()
    return parser.parse_fetch_response(text)


def parse_envelope(text: str) -> ParseResult:
    """Parse ENVELOPE data."""
    parser = IMAPParser()
    return parser.parse_envelope(text)
