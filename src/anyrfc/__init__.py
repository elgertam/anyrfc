"""AnyRFC - Complete RFC-compliant protocol implementations using AnyIO structured concurrency."""

# Version information
__version__ = "0.2.2"
__author__ = "Andrew M. Elgert"
__description__ = "RFC-compliant protocol clients using AnyIO structured concurrency"

# Import main protocol clients
from .websocket import WebSocketClient, WSFrame, OpCode, CloseCode
from .email import SMTPClient, IMAPClient, IMAPCommandBuilder, IMAPSequenceSet

# Import core utilities
from .core import (
    ProtocolClient,
    ProtocolState,
    RFCCompliance,
    AnyIOStreamHelpers,
    URIParser,
    TLSHelper
)

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',

    # WebSocket
    'WebSocketClient',
    'WSFrame',
    'OpCode',
    'CloseCode',

    # Email
    'SMTPClient',
    'IMAPClient',
    'IMAPCommandBuilder',
    'IMAPSequenceSet',

    # Core
    'ProtocolClient',
    'ProtocolState',
    'RFCCompliance',
    'AnyIOStreamHelpers',
    'URIParser',
    'TLSHelper'
]
