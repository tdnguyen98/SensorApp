"""Application state management using the Observer pattern."""

from ..observers.base import Subject
from .sensors.sensor import Sensor, SENSOR_REGISTRY, fetch_sensors_list
from ..services.client import SerialClient


class AppState(Subject):
    """
    Manage the different states of the application using the Observer
    design pattern.

    Stores the attributes of the application such as:
        - selected sensor
        - serial client
    """

    def __init__(self):
        super().__init__()
        self._selected_sensor: Sensor  # Default to first sensor
        self._slave_id: int | None = None
        self._client: SerialClient | None = None
        self._is_client_connected: bool = False
        self._debug_mode: bool = False

        self.selected_sensor = fetch_sensors_list()[0]


########################################################################
#                          GETTERS & SETTERS                           #
########################################################################

    @property
    def client(self) -> SerialClient | None:
        """Get the current serial client."""
        return self._client

    @client.setter
    def client(self, value: SerialClient | None):
        self._client = value
        self.notify(event_type="client_changed", data=value)

    @property
    def selected_sensor(self) -> Sensor:
        """Get the currently selected sensor."""
        return self._selected_sensor

    @selected_sensor.setter
    def selected_sensor(self, value: Sensor | str):
        if isinstance(value, str):
            if value in SENSOR_REGISTRY:
                self._selected_sensor = SENSOR_REGISTRY[value]()
        elif isinstance(value, Sensor):
            self._selected_sensor = value
        self.notify(event_type="selected_sensor_changed", data=value)

    @property
    def slave_id(self) -> int | None:
        """Get the current slave ID."""
        return self._slave_id

    @slave_id.setter
    def slave_id(self, value: int | None):
        self._slave_id = value
        self.notify(event_type="slave_id_changed", data=value)

    @property
    def is_client_connected(self) -> bool:
        """Check if the client is connected."""
        return self._is_client_connected

    @is_client_connected.setter
    def is_client_connected(self, value: bool):
        self._is_client_connected = value
        self.notify(event_type="client_connection_changed", data=value)

    @property
    def debug_mode(self) -> bool:
        """Get the current debug mode."""
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: bool):
        self._debug_mode = value
        self.notify(event_type="debug_mode_changed", data=value)
