"""Application state management using the Observer pattern."""
import time
import threading
import queue

from pymodbus.exceptions import ModbusException

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
        self._selected_sensor: Sensor
        self._slave_id: int | None = None
        self._client: SerialClient | None = None
        self._is_client_connected: bool = False
        self._debug_mode: bool = False
        self._restart_missing: bool = False

        self._cancel_fetch = threading.Event()
        self._fetch_thread = None
        self._client_lock = threading.Lock()

        self.selected_sensor = fetch_sensors_list()[0]
        self.queue = queue.Queue()

    def check_queue(self):
        """Check the queue for any messages and process them."""
        try:
            while True:
                event_type, data = self.queue.get_nowait()
                self.notify(event_type=event_type, data=data)
        except queue.Empty:
            pass

    def _queue_notify(self, event_type: str, data: dict = {}):
        """Thread-safe way to queue notifications from background threads."""
        self.queue.put((event_type, data))

    def fetch_slave_id_thread(self):
        """Fetch the slave ID using the current client and selected sensor."""
        self._cancel_fetch.clear()
        if self.slave_id is not None:
            self._queue_notify(
                event_type="verifying_current_id", data={"slave_id": self.slave_id}
            )
            if self.test_current_id():
                self._queue_notify(event_type="current_id_valid", data={"slave_id": self.slave_id})
                return
        if self.restart_missing:
            self._queue_notify(event_type="reboot_required", data={})
            return
        self._queue_notify(event_type="fetching_slave_id", data={})
        self.fetch_sensor_id()

    def test_current_id(self) -> bool:
        """Test the current slave ID using the current client and selected sensor."""
        if self._cancel_fetch.is_set():
            return False

        if (
            self._client is not None
            and self._selected_sensor is not None
            and self._slave_id is not None
        ):
            with self._client_lock:
                if self._client is None or self._cancel_fetch.is_set():
                    self._queue_notify(
                        event_type="slave_id_invalid", data={"slave_id": self._slave_id}
                    )
                    return False
                try:
                    self._selected_sensor.read_sensor(
                        client=self._client.client, slave_id=self._slave_id
                    )
                    self._queue_notify(
                        event_type="slave_id_valid", data={"slave_id": self._slave_id}
                    )
                    return True
                except ModbusException:
                    self._queue_notify(
                        event_type="slave_id_invalid", data={"slave_id": self._slave_id}
                    )
                    print(f"ModbusException: Slave ID {self._slave_id} is invalid.")
                    return False
        return False

    def fetch_sensor_id(self) -> None:
        """Fetch the sensor ID using the current client and selected sensor."""
        if self._client is not None and self._selected_sensor is not None:
            slave_id: int = 0
            for s_id in range(0, 255):
                if self._cancel_fetch.is_set():
                    self._queue_notify(event_type="slave_id_fetch_cancelled", data={})
                    return
                self._queue_notify(
                    event_type="fetching_slave_id", data={"slave_id": s_id}
                )
                with self._client_lock:
                    try:
                        slave_id = self._selected_sensor.try_current_slave_id(
                            client=self._client.client, slave_id=s_id
                        )
                    except OSError as e:
                        print(f"OSError during slave ID fetch: {e}")
                        self._queue_notify(
                            event_type="slave_id_fetch_cancelled", data={}
                        )
                        return

                if slave_id != -1:
                    self._queue_notify(
                        event_type="slave_id_fetched", data={"slave_id": slave_id}
                    )
                    return
            self._queue_notify(event_type="slave_id_fetch_error", data={})

    def cancel_fetch(self):
        """Cancel the ongoing slave ID fetch operation."""
        self._cancel_fetch.set()

    ########################################################################
    #                          GETTERS & SETTERS                           #
    ########################################################################

    @property
    def client(self) -> SerialClient | None:
        """Get the current serial client."""
        return self._client

    @client.setter
    def client(self, value: SerialClient | None):
        # If disconnecting, cancel any ongoing operations first
        if value is None and self._client is not None:
            # Cancel fetch before disconnecting
            self.notify(event_type="cancelling ID fetch", data={})
            # Step 1: Signal threads to stop
            self.cancel_fetch()

            # Step 2: Wait for threads to finish (with timeout)
            if self._fetch_thread is not None and self._fetch_thread.is_alive():
                print("Waiting for fetch thread to stop...")
                self._fetch_thread.join(timeout=2.0)
                if self._fetch_thread.is_alive():
                    print("Warning: Fetch thread did not stop in time")

            # Step 3: Acquire lock and safely close client
            with self._client_lock:
                old_client = self._client
                self._client = None  # Set to None FIRST so threads see it's gone

                # Now safe to disconnect
                if old_client is not None:
                    try:
                        print("Closing serial connection...")
                        old_client.disconnect()
                        print("Serial connection closed")
                    except (OSError, Exception) as e:
                        print(f"Error disconnecting client: {e}")

            # Step 4: Update state
            self.is_client_connected = False
            self.notify(event_type="client_disconnected", data={})

        # If connecting
        elif value is not None:
            print("Setting new client")
            with self._client_lock:
                print("Client lock acquired")
                self._client = value
                self.is_client_connected = True
                self.notify(event_type="client_connected", data={})
            self._fetch_thread = threading.Thread(
                target=self.fetch_slave_id_thread, daemon=True
            )
            self._fetch_thread.start()

    @property
    def selected_sensor(self) -> Sensor:
        """Get the currently selected sensor."""
        return self._selected_sensor

    @selected_sensor.setter
    def selected_sensor(self, value: Sensor | str):
        sensor_name: str = ""
        if isinstance(value, str):
            if value in SENSOR_REGISTRY:
                self._selected_sensor = SENSOR_REGISTRY[value]()
                sensor_name = value
        elif isinstance(value, Sensor):
            self._selected_sensor = value
            sensor_name = value.sensor_name
        self.notify(event_type="selected_sensor_changed", data={"sensor_name": sensor_name})

    @property
    def slave_id(self) -> int | None:
        """Get the current slave ID."""
        return self._slave_id

    @slave_id.setter
    def slave_id(self, value: int | None):
        self._slave_id = value
        self.notify(event_type="slave_id_changed", data={})

    @property
    def is_client_connected(self) -> bool:
        """Check if the client is connected."""
        return self._is_client_connected

    @is_client_connected.setter
    def is_client_connected(self, value: bool):
        self._is_client_connected = value

    @property
    def debug_mode(self) -> bool:
        """Get the current debug mode."""
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: bool):
        self._debug_mode = value
        self.notify(event_type="debug_mode_changed", data={})

    @property
    def restart_missing(self) -> bool:
        """Get the current restart missing flag."""
        return self._restart_missing
    
    @restart_missing.setter
    def restart_missing(self, value: bool):
        self._restart_missing = value
