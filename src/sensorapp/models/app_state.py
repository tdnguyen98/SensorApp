"""Application state management using the Observer pattern."""

import time
import threading
import queue

from pymodbus.exceptions import ModbusException

from ..observers.base import Subject
from .sensors.sensor import Sensor, SENSOR_REGISTRY, fetch_sensors_list, SensorProtocol
from ..services.client import SDI12Client, SerialClient


class AppState(Subject):
    """
    Manage the different states of the application using the Observer
    design pattern.

    Stores the attributes of the application such as:
        - selected sensor
        - serial client
    """
    def __init__(self) -> None:
        super().__init__()
        self._selected_sensor: Sensor
        self._slave_id: int | None = None
        self._client: SerialClient | None = None
        self._is_client_connected: bool = False
        self._debug_mode: bool = False
        self._restart_missing: bool = False

        self._cancel_fetch = threading.Event()
        self._fetch_thread: threading.Thread | None = None
        self._client_lock = threading.Lock()

        self._cancel_test = threading.Event()
        self._test_thread: threading.Thread | None = None
        self._test_thread_sdi12: threading.Thread | None = None

        sensor_name = fetch_sensors_list()[0]
        self.selected_sensor = SENSOR_REGISTRY[sensor_name]()
        self.queue: queue.Queue[tuple[str, dict]] = queue.Queue()

    def check_queue(self):
        """Check the queue for any messages and process them."""
        try:
            while True:
                event_type, data = self.queue.get_nowait()
                self.notify(event_type=event_type, **data)
        except queue.Empty:
            pass

    def _queue_notify(self, event_type: str, **kwargs) -> None:
        """Thread-safe way to queue notifications from background threads."""
        self.queue.put((event_type, kwargs))

    def fetch_slave_id_thread(self):
        """Fetch the slave ID using the current client and selected sensor."""
        self._cancel_fetch.clear()
        if self.slave_id is not None:
            self._queue_notify(
                event_type="verifying_current_id", slave_id=self.slave_id
            )
            if self.test_current_id():
                self._queue_notify(
                    event_type="current_id_valid", slave_id=self.slave_id
                )
                return
        if self.restart_missing:
            self._queue_notify(event_type="reboot_required")
            return
        self._queue_notify(event_type="fetching_slave_id")
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
                        event_type="slave_id_invalid", slave_id=self._slave_id
                    )
                    return False
                try:
                    self._selected_sensor.read_sensor(
                        client=self._client.client, slave_id=self._slave_id
                    )
                    self._queue_notify(
                        event_type="slave_id_valid", slave_id=self._slave_id
                    )
                    return True
                except ModbusException:
                    self._queue_notify(
                        event_type="slave_id_invalid", slave_id=self._slave_id
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
                    self._queue_notify(event_type="slave_id_fetch_cancelled")
                    return
                self._queue_notify(
                    event_type="fetching_slave_id", slave_id=s_id
                )
                with self._client_lock:
                    try:
                        slave_id = self._selected_sensor.try_current_slave_id(
                            client=self._client.client, slave_id=s_id
                        )
                    except OSError as e:
                        print(f"OSError during slave ID fetch: {e}")
                        self._queue_notify(
                            event_type="slave_id_fetch_cancelled"
                        )
                        return

                if slave_id != -1:
                    self._queue_notify(
                        event_type="slave_id_fetched", slave_id=slave_id
                    )
                    return
            self._queue_notify(event_type="slave_id_fetch_error")

    def test_sensor_thread(self):
        """Test the sensor using the current client and selected sensor."""
        self._cancel_test.clear()
        if self._client is not None and self._selected_sensor is not None:
            while not self._cancel_test.is_set():
                with self._client_lock:
                    client = self._client
                    sensor = self._selected_sensor
                    slave_id = self._slave_id
                   # Check if we have valid objects (outside the lock)
                if client is None or sensor is None or slave_id is None:
                    self._queue_notify(event_type="sensor_test_cancelled")
                    return
                
                # Perform I/O operation WITHOUT holding the lock
                try:
                    data = sensor.read_sensor(
                        client=client.client, slave_id=slave_id
                    )
                    
                    if self._cancel_test.is_set():
                        self._queue_notify(event_type="sensor_test_cancelled")
                        return
                    
                    self._queue_notify(event_type="sensor_test_success", **data)
                except ModbusException as e:
                    if self._cancel_test.is_set():
                        self._queue_notify(
                            event_type="sensor_test_cancelled"
                        )
                        return
                    print(f"ModbusException during sensor test: {e}")
                    self._queue_notify(
                        event_type="sensor_test_failure",
                        error_message=str(e),
                    )
                time.sleep(1)

    def test_sensor_thread_sdi12(self):
        """Test the SDI-12 sensor using the current client and selected sensor."""
        self._cancel_test.clear()
        if self._client is not None and self._selected_sensor is not None:
            while not self._cancel_test.is_set():
                with self._client_lock:
                    client = self._client
                    sensor = self._selected_sensor
                    slave_id = self._slave_id
                   # Check if we have valid objects (outside the lock)
                if client is None or sensor is None or slave_id is None:
                    self._queue_notify(event_type="sensor_test_cancelled")
                    return
                
                # Perform I/O operation WITHOUT holding the lock
                try:
                    sensor.request_to_take_measurements(
                        client=client.client, slave_id=slave_id
                    )
                    if self._cancel_test.is_set():
                        self._queue_notify(event_type="sensor_test_cancelled")
                        return
                    data = sensor.read_sensor(
                        client=client.client, slave_id=slave_id
                    )
                    if self._cancel_test.is_set():
                        self._queue_notify(event_type="sensor_test_cancelled")
                        return
                    
                    self._queue_notify(event_type="sensor_test_success", **data)
                except Exception as e:
                    if self._cancel_test.is_set():
                        self._queue_notify(
                            event_type="sensor_test_cancelled"
                        )
                        return
                    print(f"Exception during SDI-12 sensor test: {e}")
                    self._queue_notify(
                        event_type="sensor_test_failure",
                        error_message=str(e),
                    )
                time.sleep(1)

    def cancel_fetch(self):
        """Cancel the ongoing slave ID fetch operation."""
        self._cancel_fetch.set()

    def cancel_test(self):
        """Cancel the ongoing sensor test operation."""
        self._cancel_test.set()

    def test_sensor(self, tab: int):
        """Start the sensor test thread."""
        if tab == 0:
            self.cancel_test()
            if isinstance(self._test_thread, threading.Thread) and self._test_thread.is_alive():
                self._test_thread.join(timeout=2.0)
                if self._test_thread.is_alive():
                    print("Warning: Test thread did not stop in time")
            return
        else:
            if self._test_thread is None or not self._test_thread.is_alive():
                if isinstance(self._client, SDI12Client):
                    self._test_thread_sdi12 = threading.Thread(
                        target=self.test_sensor_thread_sdi12, daemon=True
                    )
                    self._test_thread_sdi12.start()
                else:
                    self._test_thread = threading.Thread(
                        target=self.test_sensor_thread, daemon=True
                    )
                    self._test_thread.start()

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
            if self._client.protocol == SensorProtocol.MODBUS:
                self.disconnect_modbus_client()

            elif self._client.protocol == SensorProtocol.SDI_12:
                self.cancel_test()
                if self._test_thread is not None and self._test_thread.is_alive():
                    print("Waiting for test thread to stop...")
                    self._test_thread.join(timeout=2.0)
                    if self._test_thread.is_alive():
                        print("Warning: Test thread did not stop in time")
                # Acquire lock and safely close client
                with self._client_lock:
                    old_client = self._client
                    self._client = None  # Set to None FIRST so threads see it's gone

                    # Now safe to disconnect
                    if old_client is not None:
                        try:
                            print("Closing serial connection...")
                            old_client.disconnect()
                            print("Serial connection closed")
                        except OSError as e:
                            print(f"Error disconnecting client: {e}")
            self.is_client_connected = False
            self.notify(event_type="client_disconnected")

        # If connecting
        elif value is not None:
            print("Setting new client")
            if value.protocol == SensorProtocol.MODBUS:
                self.connect_modbus_client(value=value)
            elif value.protocol == SensorProtocol.SDI_12:
                self.connect_sdi12_client(value=value)

    def disconnect_modbus_client(self):
        """Disconnect the Modbus client."""
        # Signal threads to stop
        self.cancel_fetch()
        self.cancel_test()

        # Wait for threads to finish
        if self._fetch_thread.is_alive():
            print("Waiting for fetch thread to stop...")
            self._fetch_thread.join(timeout=2.0)
            if self._fetch_thread.is_alive():
                print("Warning: Fetch thread did not stop in time")

        if self._test_thread is not None and self._test_thread.is_alive():
            print("Waiting for test thread to stop...")
            self._test_thread.join(timeout=2.0)
            if self._test_thread.is_alive():
                print("Warning: Test thread did not stop in time")

        # Acquire lock and safely close client
        with self._client_lock:
            old_client = self._client
            self._client = None  # Set to None FIRST so threads see it's gone

            # Now safe to disconnect
            if old_client is not None:
                try:
                    print("Closing serial connection...")
                    old_client.disconnect()
                    print("Serial connection closed")
                except OSError as e:
                    print(f"Error disconnecting client: {e}")

    def connect_modbus_client(self, *, value: SerialClient):
        """Connect the Modbus client."""
        with self._client_lock:
            print("Client lock acquired")
            self._client = value
            self.is_client_connected = True
            self.notify(event_type="client_connected")
        self._fetch_thread = threading.Thread(
            target=self.fetch_slave_id_thread, daemon=True
        )
        self._fetch_thread.start()

    def connect_sdi12_client(self, *, value: SerialClient):
        """Connect the SDI-12 client."""
        self._client = value
        self.is_client_connected = True
        self.notify(event_type="client_connected")
        if isinstance(self._client, SDI12Client):
            self.slave_id = self._client.fetch_id()
            print("Fetched slave ID:", self.slave_id)
            if self.slave_id is not None:
                self.notify(
                    event_type="SDI_12_slave_id_fetched", slave_id=self.slave_id
                )

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
        self.notify(
            event_type="selected_sensor_changed", sensor_name=sensor_name
        )

    @property
    def slave_id(self) -> int | None:
        """Get the current slave ID."""
        return self._slave_id

    @slave_id.setter
    def slave_id(self, value: int | None):
        self._slave_id = value
        self.notify(event_type="slave_id_changed")

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
        self.notify(event_type="debug_mode_changed")

    @property
    def restart_missing(self) -> bool:
        """Get the current restart missing flag."""
        return self._restart_missing

    @restart_missing.setter
    def restart_missing(self, value: bool):
        self._restart_missing = value
