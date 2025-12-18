"""
This module contain the sensor ID and test selection notebook widget used in the
second row of the GUI.
One frame of the notebook is for the sensor ID and setup and the other is for the
test of the sensor.
"""

import re
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
        if (
            self.new_slave_id_text.get() == ""
            or not self.new_slave_id_text.get().isdigit()
        ):
            self.app_state.notify(
                event_type="error",
                error_message="Please enter a valid slave ID.",
            )
            return
        if (
            int(self.new_slave_id_text.get()) < 0
            or int(self.new_slave_id_text.get()) > 255
        ):
            self.app_state.notify(
                event_type="error",
                error_message="Slave ID must be between 0 and 255.",
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
                self.app_state.notify(
                    event_type="error",
                    error_message="Client not connected or slave ID not set.",
                )
        except Exception as e:
            self.app_state.notify(
                event_type="error",
                error_message="Error while changing sensor settings: " + str(e),
            )
            return
        self.app_state.slave_id = int(self.new_slave_id_text.get())
        self.app_state.notify(
            event_type="apply_sensor_settings",
            new_baudrate=int(self.new_baudrate_combobox.get()),
            new_parity=self.new_parity_combobox.get(),
        )
        self.app_state.restart_missing = True
        self.new_slave_id_text.delete(0, tk.END)
        self.new_baudrate_combobox.set("9600")
        self.new_parity_combobox.set("N")


class SensorTestFrame(ttk.Frame):
    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)
        self.app_state = app_state

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Create the widgets for the Test Selection frame
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the Test Selection frame
        """
        self.log_text = tk.Text(self, height=5, state="disabled", wrap="word")

    def layout_widgets(self):
        """
        Layout the widgets for the Test Selection frame
        """
        # Layout the widgets for the Test Selection frame
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        # self.validate_restart_button.grid(
        #     row=0, column=1, padx=10, pady=10, sticky="sw"
        # )


class SensorIdFrameSdi12(ttk.Frame):
    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)
        self.app_state = app_state
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Create the widgets for the SDI12 Sensor ID frame
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the SDI12 Sensor ID frame
        """
        self.new_slave_id_label = ttk.Label(self, text="New slave ID")
        self.new_slave_id_text = ttk.Entry(self, width=5)
        self.apply_button = ttk.Button(
            self, text="Apply", command=self.change_sensor_id
        )

    def layout_widgets(self):
        """
        Layout the widgets for the SDI12 Sensor ID frame
        """
        self.new_slave_id_label.grid(row=0, column=2, padx=10, pady=10, sticky="se")
        self.new_slave_id_text.grid(row=0, column=3, padx=10, pady=10, sticky="se")
        self.apply_button.grid(
            row=2, column=3, columnspan=2, padx=10, pady=(10, 5), sticky="se"
        )

    def change_sensor_id(self, event=None) -> None:  # pylint: disable=unused-argument
        """
        Change the sensor ID for SDI-12 sensors
        """
        new_id = self.new_slave_id_text.get()
        print(f"Changing SDI-12 sensor ID to: {new_id}")
        print(f"new id size: {len(new_id)}")
        if new_id == "" or len(new_id) != 1 or re.match(r"[^0-9a-zA-Z]", new_id):
            self.app_state.notify(
                event_type="error",
                error_message="Please enter a valid single character slave ID (0-9, A-Z, a-z).",
            )
            return
        try:
            if (
                self.app_state.client is not None
                and self.app_state.slave_id is not None
            ):
                self.app_state.client.setup_sensor(
                    current_slave_id=self.app_state.slave_id,
                    new_slave_id=ord(new_id),
                )
            else:
                self.app_state.notify(
                    event_type="error",
                    error_message="Client not connected or slave ID not set.",
                )
        except Exception as e:
            self.app_state.notify(
                event_type="error",
                error_message="Error while changing sensor ID: " + str(e),
            )
            return
        self.app_state.slave_id = ord(new_id)
        self.new_slave_id_text.delete(0, tk.END)
        self.app_state.notify(
            event_type="apply_sensor_settings_sdi12",
        )


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
        self.tab(1, state="disabled")

    def create_widgets(self):
        """
        Create the widgets frames for the Sensor ID and Sensor Test frame
        """
        # Create the frames for the Sensor ID and Test Selection tabs
        self.sensor_id_frame = SensorIdFrame(self, app_state=self.app_state)
        self.sensor_id_frame_sdi12 = SensorIdFrameSdi12(self, app_state=self.app_state)
        self.sensor_test_frame = SensorTestFrame(self, app_state=self.app_state)

        # Add the frames to the notebook
        self.add(self.sensor_id_frame, text="Sensor Configuration")
        self.current_config_frame = "modbus"
        self.add(self.sensor_test_frame, text="Test Selection")
        self.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):  # pylint: disable=unused-argument
        selected = self.select()
        if selected:
            selected_index = self.index(selected)
            self.app_state.notify(
                event_type="tab_configure_test_changed",
                selected_tab=selected_index,
            )

    def switch_to_modbus_frame(self):
        """Switch tab 0 to show Modbus configuration frame"""
        if self.current_config_frame != "modbus":
            # Remove current frame from tab 0
            self.forget(0)
            # Insert Modbus frame at position 0
            self.insert(0, self.sensor_id_frame, text="Sensor Configuration")
            self.current_config_frame = "modbus"
            print("Switched to Modbus configuration frame")

    def switch_to_sdi12_frame(self):
        """Switch tab 0 to show SDI-12 configuration frame"""
        if self.current_config_frame != "sdi12":
            # Remove current frame from tab 0
            self.forget(0)
            # Insert SDI-12 frame at position 0
            self.insert(0, self.sensor_id_frame_sdi12, text="Sensor Configuration")
            self.current_config_frame = "sdi12"
            print("Switched to SDI-12 configuration frame")

    def update_event(self, event_type, **kwargs) -> None:
        if event_type == "current_id_valid" or event_type == "slave_id_fetched":
            self.switch_to_modbus_frame()
            self.tab(0, state="normal")
            self.select(0)
            self.tab(1, state="normal")
        elif event_type == "SDI_12_slave_id_fetched":
            self.switch_to_sdi12_frame()
            self.tab(0, state="normal")
            self.select(0)
            self.tab(1, state="normal")
        elif event_type == "client_disconnected":
            self.tab(0, state="disabled")
            self.tab(1, state="disabled")
        elif event_type == "tab_configure_test_changed":
            current_tab = kwargs.get("selected_tab", 0)
            self.app_state.test_sensor(tab=current_tab)
            self.update_idletasks()
        elif event_type == "sensor_test_success":
            self.sensor_test_frame.log_text.configure(state="normal")
            self.sensor_test_frame.log_text.delete(1.0, tk.END)
            for key, value in kwargs.items():
                self.sensor_test_frame.log_text.insert(tk.END, f"{key}: {value}\n")
            self.sensor_test_frame.log_text.configure(state="disabled")
