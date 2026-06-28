"""
A lightweight async eventbus
"""

import inspect
from collections import defaultdict
from typing import Any, Awaitable, Callable, DefaultDict, Dict, List

EventHandler = Callable[[Dict[str, Any]], Any] | Callable[[Dict[str, Any]], Awaitable[Any]]


class EventBus:
    """Simple pub/sub event bus"""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, List[EventHandler]] = defaultdict(list)
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)
    
    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        if handler not in self._handlers:
            return
        self._handlers[event_name] = [h for h in self._handlers[event_name] if h != handler]
    
    async def publish(self, event_name: str, payload: Dict[str, Any] | None = None) -> None:
        payload = payload or {}
        handlers = list(self._handlers.get(event_name, []))
        if not handlers:
            return

        for handler in handlers:
            result = handler(payload)
            if inspect.isawaitable(result):
                await result
    
    async def publish_many(self, events: List[tuple[str, Dict[str, Any]]]) -> None:
        for event_name, payload in events:
            await self.publish(event_name, payload)
