# observers/base.py
from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update_event(self, event_type: str, **kwargs) -> None:
        """Receive update when notification is sent from Subject."""


class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, *, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, *, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, *, event_type: str, **kwargs) -> None:
        for observer in self._observers:
            observer.update_event(event_type=event_type, **kwargs)
