"""Thread-safe EventBus -> PyQt6 signal mapping bridge"""

import logging
from typing import Any, Dict

from PyQt6.QtCore import QObject, pyqtSignal

from core.event_bus import EventBus

logger = logging.getLogger(__name__)


class PyQtEventBridge(QObject):
    """Subscribes to async EventBus and thread-safely emits PyQt signalls"""

    event_received = pyqtSignal(str, dict)

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self._handlers: Dict[str, Any] = {}
        self._subscribe_all()
        logger.info("PyQtEventBridge is initialized and subscribed to core events")
    
    def _subscribe_all(self) -> None:
        core_events = [
            "audio.listening_started",
            "audio.listening_stopped"
        ]

        for ev in core_events:
            handler = self._make_handler(ev)
            self._handlers[ev] = handler
            self.event_bus.subscribe(ev, handler)
        
    def _make_handler(self, event_name: str):
        """Creates a thread-safe callback handler for EventBus"""
        def handle_event(payload: Dict[str, Any]) -> None:
            logger.debug("Bridge marshaling event '%s' to GUI thread", event_name)
            self.event_received.emit(event_name, payload or {})
        return handle_event

    def _unsubscribe_all(self) -> None:
        """Cleanup subscribed event on shutdown"""
        for ev, handler in self._handlers.items():
            try:
                self.event_bus.unsubscribe(ev, handler)
            except Exception as e:
                logger.warning("Error unsubscribing event '%s': %s", ev, e)
        self._handlers.clear()
        logger.info("PyQtEventBridge cleaned up subscriptions")
