"""TLS configuration helpers."""
import ssl
from typing import Optional, Set
from dataclasses import dataclass

@dataclass
class TLSConfig:
    """TLS configuration for secure connections."""
    verify_hostname: bool = True
    check_hostname: bool = True
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    ca_file: Optional[str] = None
    ca_path: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    minimum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2
    maximum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_3
    cipher_suites: Optional[Set[str]] = None

class TLSHelper:
    """Helper for creating secure TLS contexts."""
    
    @staticmethod
    def create_client_context(config: Optional[TLSConfig] = None) -> ssl.SSLContext:
        """Create secure client TLS context."""
        if config is None:
            config = TLSConfig()
        
        context = ssl.create_default_context()
        
        # Set verification settings
        context.check_hostname = config.check_hostname
        context.verify_mode = config.verify_mode
        
        # Set TLS version bounds
        context.minimum_version = config.minimum_version
        context.maximum_version = config.maximum_version
        
        # Load certificates if provided
        if config.ca_file or config.ca_path:
            context.load_verify_locations(cafile=config.ca_file, capath=config.ca_path)
        
        if config.cert_file:
            context.load_cert_chain(config.cert_file, config.key_file)
        
        # Set cipher suites if specified
        if config.cipher_suites:
            context.set_ciphers(':'.join(config.cipher_suites))
        
        return context
    
    @staticmethod
    def create_default_client_context() -> ssl.SSLContext:
        """Create default secure client context."""
        return TLSHelper.create_client_context()
    
    @staticmethod
    def create_unverified_context() -> ssl.SSLContext:
        """Create unverified context (NOT recommended for production)."""
        config = TLSConfig(
            verify_hostname=False,
            check_hostname=False,
            verify_mode=ssl.CERT_NONE
        )
        return TLSHelper.create_client_context(config)