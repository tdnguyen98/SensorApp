"""
This module contain the sensor ID and test selection notebook widget used in the second row of the GUI.
One frame of the notebook is for the sensor ID and setup and the other is for the test of the sensor.
"""

import tkinter as tk
from tkinter import ttk

from ..observers.base import Observer
from ..models.app_state import AppState


class SensorIdFrame(ttk.Frame):
    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)
        self.app_state = app_state

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # Create the widgets for the Sensor ID frame
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the Sensor ID frame
        """
        self.new_baudrate_label = ttk.Label(self, text="New baudrate")
        self.new_baudrate_combobox = ttk.Combobox(
            self,
            width=5,
            values=[
                "1200",
                "2400",
                "4800",
                "9600",
                "19200",
                "38400",
                "57600",
                "115200",
            ],
            state="readonly",
        )
        self.new_baudrate_combobox.set("9600")
        self.new_parity_label = ttk.Label(self, text="New parity")
        self.new_parity_combobox = ttk.Combobox(
            self, width=5, values=["N", "E", "O"], state="readonly"
        )
        self.new_parity_combobox.set("N")
        self.new_slave_id_label = ttk.Label(self, text="New slave ID")
        self.new_slave_id_text = ttk.Entry(self, width=5)
        self.apply_button = ttk.Button(
            self, text="Apply", command=self.change_sensor_settings
        )

    def layout_widgets(self):
        """
        Layout the widgets for the Sensor ID frame
        """
        self.new_baudrate_label.grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="sw"
        )
        self.new_baudrate_combobox.grid(
            row=0, column=1, padx=10, pady=(10, 5), sticky="sw"
        )
        self.new_parity_label.grid(row=1, column=0, padx=10, sticky="sw")
        self.new_parity_combobox.grid(row=1, column=1, padx=10, sticky="sw")
        self.new_slave_id_label.grid(row=0, column=2, padx=10, pady=10, sticky="se")
        self.new_slave_id_text.grid(row=0, column=3, padx=10, pady=10, sticky="se")
        self.apply_button.grid(
            row=2, column=3, columnspan=2, padx=10, pady=(10, 5), sticky="se"
        )

    def change_sensor_settings(self, event=None) -> None:  # pylint: disable=unused-argument
        """
        Test the sensor
        """
        if self.new_slave_id_text.get() == "" or not self.new_slave_id_text.get().isdigit():
            self.app_state.notify(
                event_type="error",
                data={"error_message": "Please enter a valid slave ID."},
            )
            return
        if int(self.new_slave_id_text.get()) < 0 or int(self.new_slave_id_text.get()) > 255:
            self.app_state.notify(
                event_type="error",
                data={"error_message": "Slave ID must be between 0 and 255."},
            )
            return
        try:
            if (
                self.app_state.client is not None
                and self.app_state.slave_id is not None
            ):
                self.app_state.client.setup_sensor(
                    current_slave_id=self.app_state.slave_id,
                    new_slave_id=int(self.new_slave_id_text.get()),
                    new_baudrate=int(self.new_baudrate_combobox.get()),
                    new_parity=self.new_parity_combobox.get(),
                )
            else:
                self.app_state.notify(event_type="error", data={"error_message": "Client not connected or slave ID not set."})
        except Exception as e:
            self.app_state.notify(event_type="error", data={"error_message": "Error while changing sensor settings: " + str(e)})
            return
        self.app_state.slave_id = int(self.new_slave_id_text.get())
        self.app_state.notify(
            event_type="apply_sensor_settings",
            data={
                "new_baudrate": int(self.new_baudrate_combobox.get()),
                "new_parity": self.new_parity_combobox.get(),
            },
        )
        self.app_state.restart_missing = True
        self.new_slave_id_text.delete(0, tk.END)
        self.new_baudrate_combobox.set("9600")
        self.new_parity_combobox.set("N")


class TestLogFrame(ttk.Frame):
    def __init__(self, parent, close_test_frame: Callable):
        super().__init__(parent)
        self.close = close_test_frame
        self.configure(relief="groove", padding=(10, 10))

        # Create the widgets for the Test frame
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the Test frame
        """
        self.text = tk.Text(self, width=40, height=42, state="disabled", wrap="word")
        self.close_button = ttk.Button(self, text="Close", command=self.close)

    def layout_widgets(self):
        """
        Layout the widgets for the Test frame
        """
        self.text.grid(row=0, column=0, sticky="nsew")
        self.close_button.grid(row=1, column=0, pady=(10, 0), sticky="se")


class SensorTestFrame(ttk.Frame):
    def __init__(self, parent, open_test_frame: Callable):
        super().__init__(parent)
        self.open_test_frame = open_test_frame

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Create the widgets for the Test Selection frame
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the Test Selection frame
        """
        # Create the widgets for the Test Selection frame
        self.validate_label = ttk.Label(
            self,
            text=(
                "If you changed the settings/ID of the sensor, please restart the sensor and tick to continue."
            ),
        )
        self.validate_restart_button = ttk.Checkbutton(self, command=self.on_tick)
        self.validate_restart_button.state(["!alternate"])

        # Create the log for the Test Selection frame
        self.log_sensor = tk.Text(
            self, height=10, width=30, state="disabled", wrap="word"
        )
        self.test_button = ttk.Button(
            self, text="Test sensor", command=self.open_test_frame
        )

    def layout_widgets(self):
        """
        Layout the widgets for the Test Selection frame
        """
        # Layout the widgets for the Test Selection frame
        self.validate_label.grid(row=0, column=0, sticky="sw", padx=10, pady=10)
        self.validate_restart_button.grid(
            row=0, column=1, padx=10, pady=10, sticky="sw"
        )

    def on_tick(self, event=None) -> None:  # pylint: disable=unused-argument
        """
        Tick the checkbutton to continue
        """
        if self.validate_restart_button.instate(["selected"]):
            self.test_button.grid(row=1, column=0, sticky="sw")
        else:
            self.log_sensor.grid_remove()
            self.test_button.grid_remove()


class SensorIdTestNoteBook(ttk.Notebook, Observer):
    def __init__(
        self,
        parent,
        app_state: AppState,
    ):
        super().__init__(parent)
        self.app_state = app_state

        # Create the widgets for the Sensor ID and Test Selection frame
        self.create_widgets()

        # Initially disable the tabs until the client is connected
        self.tab(0, state="disabled")
        # self.tab(1, state="disabled")

    def create_widgets(self):
        """
        Create the widgets frames for the Sensor ID and Sensor Test frame
        """
        # Create the frames for the Sensor ID and Test Selection tabs
        self.sensor_id_frame = SensorIdFrame(self, app_state=self.app_state)
        # self.sensor_test_frame = SensorTestFrame(self, self.open_test_frame)

        # Add the frames to the notebook
        self.add(self.sensor_id_frame, text="Sensor Configuration")
        # self.add(self.sensor_test_frame, text="Test Selection")
        # self.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def update_event(self, event_type, data=None):
        if event_type == "current_id_valid" or event_type == "slave_id_fetched":
            self.tab(0, state="normal")
            self.select(0)
            # self.tab(1, state="normal")
        elif event_type == "client_disconnected":
            self.tab(0, state="disabled")
            # self.tab(1, state="disabled")
