# observers/base.py
from abc import ABC, abstractmethod


class Observer(ABC):
    """Abstract base class for observers."""
    @abstractmethod
    def update_event(self, event_type: str, **kwargs) -> None:
        """Receive update when notification is sent from Subject."""


class Subject:
    """Subject class that maintains a list of observers and notifies them of events."""
    def __init__(self):
        self._observers = []

    def attach(self, *, observer: Observer) -> None:
        """Attach an observer to the subject."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, *, observer: Observer) -> None:
        """Detach an observer from the subject."""
        self._observers.remove(observer)

    def notify(self, *, event_type: str, **kwargs) -> None:
        """Notify all observers about an event."""
        for observer in self._observers:
            observer.update_event(event_type=event_type, **kwargs)
