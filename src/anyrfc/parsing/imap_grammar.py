"""
IMAP grammar definition using Arpeggio PEG parser.

This module defines RFC 9051 compliant IMAP grammar rules.
"""

from .._vendor.arpeggio import Optional as ArpeggioOptional, \
    ZeroOrMore, OneOrMore, EOF
from .._vendor.arpeggio import RegExMatch as _


# Basic IMAP Grammar Components

def sp(): return ' '  # Single space
def crlf(): return _("\\r\\n")

# Numbers and basic types
def number(): return _("\\d+")
def nz_number(): return _("[1-9]\\d*")

# Character classes
def atom_char(): return _("[^\\s\\(\\)\\{%\\*\"\\\\\\+\\]]")
def quoted_char(): return _('[^"\\\\]|\\\\.|""')

# Strings
def atom(): return OneOrMore(atom_char)
def quoted_string(): return '"', ZeroOrMore(quoted_char), '"'
def literal(): return '{', number, '}', crlf, _(".*", multiline=True)
def string(): return [quoted_string, literal, atom]
def nstring(): return [string, "NIL"]

# Lists
def sp_list_item(): return sp, [string, "NIL", paren_list]
def paren_list(): return '(', ArpeggioOptional([string, "NIL", paren_list], ZeroOrMore(sp_list_item)), ')'

# Flags
def flag_keyword(): return _("\\\\[A-Za-z]+")
def flag_extension(): return _("\\$[A-Za-z0-9_]+")
def flag(): return [flag_keyword, flag_extension, atom]
def flag_list(): return '(', ArpeggioOptional(flag, ZeroOrMore(sp, flag)), ')'

# FETCH response components
def uid_item(): return "UID", sp, nz_number
def flags_item(): return "FLAGS", sp, flag_list  
def internaldate_item(): return "INTERNALDATE", sp, quoted_string
def envelope_item(): return "ENVELOPE", sp, envelope
def bodystructure_item(): return "BODYSTRUCTURE", sp, paren_list

# Address structure: (name route mailbox host)
def address(): return '(', nstring, sp, nstring, sp, nstring, sp, nstring, ')'
def address_list(): return [paren_list, "NIL"]

# Envelope: (date subject from sender reply-to to cc bcc in-reply-to message-id)
def envelope(): return ('(', 
                       nstring, sp,       # date
                       nstring, sp,       # subject
                       address_list, sp,  # from
                       address_list, sp,  # sender  
                       address_list, sp,  # reply-to
                       address_list, sp,  # to
                       address_list, sp,  # cc
                       address_list, sp,  # bcc
                       nstring, sp,       # in-reply-to
                       nstring,           # message-id
                       ')')

# FETCH response items
def fetch_att(): return [uid_item, flags_item, internaldate_item, envelope_item, bodystructure_item]
def fetch_msg_att(): return '(', ArpeggioOptional(fetch_att, ZeroOrMore(sp, fetch_att)), ')'

# Main FETCH response
def fetch_response(): return '*', sp, number, sp, "FETCH", sp, fetch_msg_att

# Other response types (simplified)
def tag(): return _("[A-Z0-9]+")
def resp_cond_state(): return _("OK|NO|BAD")
def text(): return _(".*")

def response_tagged(): return tag, sp, resp_cond_state, sp, text
def response_untagged(): return '*', sp, text  
def response_continuation(): return '+', sp, text

# Top level response
def response(): return [fetch_response, response_tagged, response_untagged, response_continuation]