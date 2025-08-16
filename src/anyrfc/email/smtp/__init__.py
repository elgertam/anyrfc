"""SMTP client implementation per RFC 5321."""

from .client import SMTPClient, SMTPState, SMTPResponseCode

__all__ = [
    'SMTPClient',
    'SMTPState', 
    'SMTPResponseCode'
]