"""WebSocket protocol state machine per RFC 6455."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
from enum import Enum
from typing import Dict, Tuple
from ..core.state_machine import ProtocolStateMachine, StateTransition

class WSState(Enum):
    """WebSocket connection states per RFC 6455."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    HANDSHAKE = "handshake"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"

class WSEvent(Enum):
    """WebSocket events that trigger state transitions."""
    CONNECT = "connect"
    HANDSHAKE_COMPLETE = "handshake_complete"
    HANDSHAKE_FAILED = "handshake_failed"
    CLOSE_INITIATED = "close_initiated"
    CLOSE_RECEIVED = "close_received"
    CLOSE_COMPLETE = "close_complete"
    ERROR_OCCURRED = "error_occurred"
    DISCONNECT = "disconnect"

class WebSocketStateMachine(ProtocolStateMachine[WSState, WSEvent]):
    """WebSocket protocol state machine following RFC 6455."""
    
    def __init__(self):
        super().__init__(WSState.DISCONNECTED)
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Setup valid state transitions per RFC 6455."""
        transitions = [
            # From DISCONNECTED
            StateTransition(WSState.DISCONNECTED, WSEvent.CONNECT, WSState.CONNECTING),
            
            # From CONNECTING
            StateTransition(WSState.CONNECTING, WSEvent.HANDSHAKE_COMPLETE, WSState.OPEN),
            StateTransition(WSState.CONNECTING, WSEvent.HANDSHAKE_FAILED, WSState.ERROR),
            StateTransition(WSState.CONNECTING, WSEvent.ERROR_OCCURRED, WSState.ERROR),
            StateTransition(WSState.CONNECTING, WSEvent.DISCONNECT, WSState.DISCONNECTED),
            
            # From OPEN
            StateTransition(WSState.OPEN, WSEvent.CLOSE_INITIATED, WSState.CLOSING),
            StateTransition(WSState.OPEN, WSEvent.CLOSE_RECEIVED, WSState.CLOSING),
            StateTransition(WSState.OPEN, WSEvent.ERROR_OCCURRED, WSState.ERROR),
            StateTransition(WSState.OPEN, WSEvent.DISCONNECT, WSState.DISCONNECTED),
            
            # From CLOSING
            StateTransition(WSState.CLOSING, WSEvent.CLOSE_COMPLETE, WSState.CLOSED),
            StateTransition(WSState.CLOSING, WSEvent.ERROR_OCCURRED, WSState.ERROR),
            StateTransition(WSState.CLOSING, WSEvent.DISCONNECT, WSState.DISCONNECTED),
            
            # From CLOSED
            StateTransition(WSState.CLOSED, WSEvent.DISCONNECT, WSState.DISCONNECTED),
            StateTransition(WSState.CLOSED, WSEvent.CONNECT, WSState.CONNECTING),
            
            # From ERROR
            StateTransition(WSState.ERROR, WSEvent.DISCONNECT, WSState.DISCONNECTED),
            StateTransition(WSState.ERROR, WSEvent.CONNECT, WSState.CONNECTING),
        ]
        
        for transition in transitions:
            self.add_transition(transition)
    
    def get_valid_transitions(self) -> Dict[Tuple[WSState, WSEvent], WSState]:
        """Get all valid transitions for WebSocket protocol."""
        return {
            (t.from_state, t.event): t.to_state 
            for t in self._transitions.values()
        }
    
    def is_valid_transition(self, from_state: WSState, event: WSEvent, to_state: WSState) -> bool:
        """Check if a transition is valid according to RFC 6455."""
        key = (from_state, event)
        if key not in self._transitions:
            return False
        return self._transitions[key].to_state == to_state
    
    def can_send_data(self) -> bool:
        """Check if data frames can be sent in current state."""
        return self.current_state == WSState.OPEN
    
    def can_send_control(self) -> bool:
        """Check if control frames can be sent in current state."""
        # Control frames can be sent in OPEN and CLOSING states
        return self.current_state in {WSState.OPEN, WSState.CLOSING}
    
    def is_connected(self) -> bool:
        """Check if WebSocket is in connected state."""
        return self.current_state == WSState.OPEN
    
    def is_closing(self) -> bool:
        """Check if WebSocket is in closing state."""
        return self.current_state == WSState.CLOSING
    
    def is_closed(self) -> bool:
        """Check if WebSocket is closed."""
        return self.current_state in {WSState.CLOSED, WSState.DISCONNECTED}
    
    def is_error(self) -> bool:
        """Check if WebSocket is in error state."""
        return self.current_state == WSState.ERROR