# observers/base.py
from abc import ABC, abstractmethod
from typing import Any


class Observer(ABC):
    @abstractmethod
    def update_event(self, event_type: str, data: Any = None) -> None:
        """Receive update when notification is sent from Subject."""
        pass

class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, *, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, *, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, *, event_type: str, data: dict = {}) -> None:
        for observer in self._observers:
            observer.update_event(event_type=event_type, data=data)
