"""
IMAP grammar definition using Arpeggio PEG parser.

This module defines RFC 9051 compliant IMAP grammar rules.
"""

from .._vendor.arpeggio import Optional as ArpeggioOptional, ZeroOrMore, OneOrMore
from .._vendor.arpeggio import RegExMatch as _


# Basic IMAP Grammar Components


def sp():
    return " "  # Single space


def crlf():
    return _("\\r\\n")


# Numbers and basic types
def number():
    return _("\\d+")


def nz_number():
    return _("[1-9]\\d*")


# Character classes
def atom_char():
    return _('[^\\s\\(\\)\\{%\\*"\\\\\\+\\]]')


def quoted_char():
    return _('[^"\\\\]|\\\\.|""')


# Strings
def atom():
    return OneOrMore(atom_char)


def quoted_string():
    return '"', ZeroOrMore(quoted_char), '"'


def literal():
    return "{", number, "}", crlf, _(".*", multiline=True)


def string():
    return [quoted_string, literal, atom]


def nstring():
    return [string, "NIL"]


# Lists - simplified to handle nested structures better
def paren_list():
    return "(", ZeroOrMore([string, "NIL", sp, paren_list]), ")"


# Flags
def flag_keyword():
    return _("\\\\[A-Za-z]+")


def flag_extension():
    return _("\\$[A-Za-z0-9_]+")


def flag():
    return [flag_keyword, flag_extension, atom]


def flag_list():
    return "(", ArpeggioOptional(flag, ZeroOrMore(sp, flag)), ")"


# FETCH response components
def uid_item():
    return "UID", sp, nz_number


def flags_item():
    return "FLAGS", sp, flag_list


def internaldate_item():
    return "INTERNALDATE", sp, quoted_string


def envelope_item():
    return "ENVELOPE", sp, envelope


# Address structure: (name route mailbox host)
def address():
    return "(", nstring, sp, nstring, sp, nstring, sp, nstring, ")"


def address_list():
    return [paren_list, "NIL"]


# Envelope: (date subject from sender reply-to to cc bcc in-reply-to message-id)
def envelope():
    return (
        "(",
        nstring,
        sp,  # date
        nstring,
        sp,  # subject
        address_list,
        sp,  # from
        address_list,
        sp,  # sender
        address_list,
        sp,  # reply-to
        address_list,
        sp,  # to
        address_list,
        sp,  # cc
        address_list,
        sp,  # bcc
        nstring,
        sp,  # in-reply-to
        nstring,  # message-id
        ")",
    )


# FETCH response items
def fetch_att():
    return [uid_item, flags_item, internaldate_item, envelope_item, bodystructure_item]


def fetch_msg_att():
    return "(", ArpeggioOptional(fetch_att, ZeroOrMore(sp, fetch_att)), ")"


# Main FETCH response
def fetch_response():
    return "*", sp, number, sp, "FETCH", sp, fetch_msg_att


# Other response types (simplified)
def tag():
    return _("[A-Z0-9]+")


def resp_cond_state():
    return _("OK|NO|BAD")


def text():
    return _(".*")


def response_tagged():
    return tag, sp, resp_cond_state, sp, text


def response_untagged():
    return "*", sp, text


def response_continuation():
    return "+", sp, text


# RFC 9051 BODYSTRUCTURE ABNF Grammar Implementation


# Numbers for BODYSTRUCTURE
def number64():
    return number  # Same as number for our purposes


# Media types
def media_basic():
    return quoted_string, sp, quoted_string  # type/subtype


def media_message():
    return '"MESSAGE"', sp, '"', ["RFC822", "GLOBAL"], '"'


def media_text():
    return '"TEXT"', sp, quoted_string


def media_subtype():
    return quoted_string


# Body field definitions
def body_fld_param():
    return ["(", string, sp, string, ZeroOrMore(sp, string, sp, string), ")", "NIL"]


def body_fld_id():
    return nstring


def body_fld_desc():
    return nstring


def body_fld_enc():
    return ['"', ["7BIT", "8BIT", "BINARY", "BASE64", "QUOTED-PRINTABLE"], '"', string]


def body_fld_octets():
    return number


def body_fld_lines():
    return number64


def body_fld_md5():
    return nstring


def body_fld_dsp():
    return ["(", string, sp, body_fld_param, ")", "NIL"]


def body_fld_lang():
    return [nstring, "(", string, ZeroOrMore(sp, string), ")"]


def body_fld_loc():
    return nstring


# Body extensions
def body_extension():
    return [
        nstring,
        number,
        number64,
        "(",
        body_extension,
        ZeroOrMore(sp, body_extension),
        ")",
    ]


# Core body fields
def body_fields():
    return (
        body_fld_param,
        sp,
        body_fld_id,
        sp,
        body_fld_desc,
        sp,
        body_fld_enc,
        sp,
        body_fld_octets,
    )


# Body extensions
def body_ext_1part():
    return body_fld_md5, ArpeggioOptional(
        sp,
        body_fld_dsp,
        ArpeggioOptional(
            sp,
            body_fld_lang,
            ArpeggioOptional(sp, body_fld_loc, ZeroOrMore(sp, body_extension)),
        ),
    )


def body_ext_mpart():
    return body_fld_param, ArpeggioOptional(
        sp,
        body_fld_dsp,
        ArpeggioOptional(
            sp,
            body_fld_lang,
            ArpeggioOptional(sp, body_fld_loc, ZeroOrMore(sp, body_extension)),
        ),
    )


# Body types
def body_type_basic():
    return media_basic, sp, body_fields


def body_type_msg():
    return media_message, sp, body_fields, sp, envelope, sp, body, sp, body_fld_lines


def body_type_text():
    return media_text, sp, body_fields, sp, body_fld_lines


def body_type_1part():
    return [body_type_basic, body_type_msg, body_type_text], ArpeggioOptional(sp, body_ext_1part)


def body_type_mpart():
    return OneOrMore(body), sp, media_subtype, ArpeggioOptional(sp, body_ext_mpart)


# Main body definition (RFC 9051 compliant)
def body():
    return "(", [body_type_1part, body_type_mpart], ")"


# BODYSTRUCTURE - Use simplified nested list structure for robustness
def bodystructure_item():
    return "BODYSTRUCTURE", sp, paren_list


# Top level response
def response():
    return [fetch_response, response_tagged, response_untagged, response_continuation]
