"""Protocol state machine base implementation."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from abc import ABC, abstractmethod
from typing import Dict, Set, Callable, Optional, Any, Generic, TypeVar
from enum import Enum
from dataclasses import dataclass

StateType = TypeVar('StateType', bound=Enum)
EventType = TypeVar('EventType')

@dataclass
class StateTransition(Generic[StateType, EventType]):
    """Represents a state transition."""
    from_state: StateType
    event: EventType
    to_state: StateType
    guard: Optional[Callable[[], bool]] = None
    action: Optional[Callable[[], Any]] = None

class ProtocolStateMachine(ABC, Generic[StateType, EventType]):
    """Base class for protocol state machines."""
    
    def __init__(self, initial_state: StateType):
        self._current_state = initial_state
        self._transitions: Dict[tuple[StateType, EventType], StateTransition] = {}
        self._state_lock = anyio.Lock()  # AnyIO lock only
        self._state_changed_event = anyio.Event()
        self._listeners: Set[Callable[[StateType, StateType], Any]] = set()
    
    @property
    def current_state(self) -> StateType:
        """Get current state."""
        return self._current_state
    
    def add_transition(self, transition: StateTransition[StateType, EventType]) -> None:
        """Add a state transition."""
        key = (transition.from_state, transition.event)
        self._transitions[key] = transition
    
    def add_listener(self, listener: Callable[[StateType, StateType], Any]) -> None:
        """Add state change listener."""
        self._listeners.add(listener)
    
    def remove_listener(self, listener: Callable[[StateType, StateType], Any]) -> None:
        """Remove state change listener."""
        self._listeners.discard(listener)
    
    async def send_event(self, event: EventType) -> bool:
        """Send event to state machine."""
        async with self._state_lock:
            key = (self._current_state, event)
            
            if key not in self._transitions:
                return False
            
            transition = self._transitions[key]
            
            # Check guard condition
            if transition.guard and not transition.guard():
                return False
            
            # Perform state transition
            old_state = self._current_state
            self._current_state = transition.to_state
            
            # Execute action
            if transition.action:
                result = transition.action()
                if hasattr(result, '__await__'):
                    await result
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    result = listener(old_state, self._current_state)
                    if hasattr(result, '__await__'):
                        await result
                except Exception:
                    # Don't let listener exceptions break state machine
                    pass
            
            # Signal state change
            self._state_changed_event.set()
            self._state_changed_event = anyio.Event()  # Reset for next change
            
            return True
    
    async def wait_for_state(self, target_state: StateType, timeout: Optional[float] = None) -> bool:
        """Wait for state machine to reach target state."""
        if self._current_state == target_state:
            return True
        
        if timeout is not None:
            with anyio.move_on_after(timeout):
                while self._current_state != target_state:
                    await self._state_changed_event.wait()
                return True
            return False
        else:
            while self._current_state != target_state:
                await self._state_changed_event.wait()
            return True
    
    @abstractmethod
    def get_valid_transitions(self) -> Dict[tuple[StateType, EventType], StateType]:
        """Get all valid transitions for this protocol."""
        pass
    
    @abstractmethod
    def is_valid_transition(self, from_state: StateType, event: EventType, to_state: StateType) -> bool:
        """Check if a transition is valid according to protocol rules."""
        pass