"""Tests for URI parsing functionality."""
import pytest
from anyrfc.core.uri import URIParser


class TestURIParser:
    """Test URI parsing per RFC 3986."""
    
    def test_websocket_uri_parsing(self):
        """Test WebSocket URI parsing."""
        uri = "wss://example.com:443/path?param=value"
        parsed = URIParser.parse(uri)
        
        assert parsed.scheme == "wss"
        assert parsed.hostname == "example.com"
        assert parsed.port == 443
        assert parsed.path == "/path"
        assert "param" in parsed.query
        assert parsed.query["param"] == ["value"]
    
    def test_default_ports(self):
        """Test default port handling."""
        # WebSocket default ports
        ws_uri = URIParser.parse("ws://example.com/")
        assert ws_uri.effective_port == 80
        
        wss_uri = URIParser.parse("wss://example.com/")
        assert wss_uri.effective_port == 443
    
    def test_explicit_ports(self):
        """Test explicit port handling."""
        uri = URIParser.parse("ws://example.com:8080/")
        assert uri.port == 8080
        assert uri.effective_port == 8080
    
    def test_query_parameter_parsing(self):
        """Test query parameter parsing."""
        uri = URIParser.parse("ws://example.com/?a=1&b=2&a=3")
        
        # Multiple values for same parameter
        assert uri.query["a"] == ["1", "3"]
        assert uri.query["b"] == ["2"]
    
    def test_path_handling(self):
        """Test URI path handling."""
        # Test with path
        uri = URIParser.parse("ws://example.com/some/path")
        assert uri.path == "/some/path"
        
        # Test without explicit path (defaults to "/")
        uri = URIParser.parse("ws://example.com")
        assert uri.path == "/" or uri.path == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])