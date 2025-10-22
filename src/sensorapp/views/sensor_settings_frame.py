"""
This module contains the SensorSettingsFrame class that is used to display the Serial configurations
on the first row of the GUI to the right.
"""

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from typing import Any, Dict

# from insolab.sensor_app.logging_system import log_message
from ..models.sensors.utilites import scan_com_ports
from ..models.app_state import AppState
from ..observers.base import Observer


class SensorSettingsFrame(tk.LabelFrame, Observer):
    def __init__(self, parent, *, app_state: AppState):
        super().__init__(parent)
        self.app_state = app_state
        self.settings: Dict[str, Any] | None = None

        # Add title in the frame border
        self.configure(text="Serial configurations", font=tkFont.Font(size=18))

        # Create the frames for the Sensor and Color Code tabs and display them
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the label and comvoboxes of the Serial configurations frame
        """
        # Create the first label and combobox for the COM port
        self.client_com_port_label = ttk.Label(self, text="COM Port")
        self.client_com_port_box = ttk.Combobox(self, state="readonly")
        
        self.update_com_ports()
        self.client_com_port_box.bind("<Button-1>", self.update_com_ports)

        # Create the label and combobox for the sensor settings
        self.sensor_settings_label = ttk.Label(self, text="Sensor settings")
        self.sensor_settings_combobox = ttk.Combobox(self, width=10, state="readonly")

        self.sensor_settings_combobox.bind(
            "<<ComboboxSelected>>",
            lambda e: self.app_state.notify(event_type="sensor_settings_changed"),
        )

        # Create the parity and baudrate comboboxes to display or custom the settings
        self.client_parity_label = ttk.Label(self, text="Parity")
        self.client_parity_combobox = ttk.Combobox(self, width=5, state="disable")
        self.client_baudrate_label = ttk.Label(self, text="Baudrate")
        self.client_baudrate_combobox = ttk.Combobox(self, width=6, state="disable")
        self.update_settings()

        # Create the connect button to connect to the client
        self.connect_button = ttk.Button(
            self,
            text="Connect",
            width=8,
            command=lambda: self.app_state.notify(event_type="button_connect"),
        )

    def layout_widgets(self):
        """
        Layout the widgets for the Serial configurations frame
        """
        # Column 0
        self.client_com_port_label.grid(
            row=0, column=0, sticky="sw", padx=10, pady=(10, 0)
        )
        self.client_com_port_box.grid(row=1, column=0, padx=10, sticky="sw")

        # Column 1
        self.sensor_settings_label.grid(
            row=0, column=1, sticky="sw", padx=10, pady=(10, 0)
        )
        self.sensor_settings_combobox.grid(row=1, column=1, padx=10, sticky="sw")

        # Column 2
        self.client_parity_label.grid(
            row=0, column=2, sticky="sw", padx=10, pady=(10, 0)
        )
        self.client_parity_combobox.grid(row=1, column=2, padx=10, sticky="sw")
        self.client_baudrate_label.grid(row=2, column=2, sticky="sw", padx=10)
        self.client_baudrate_combobox.grid(
            row=3, column=2, padx=10, pady=(0, 20), sticky="sw"
        )
        self.connect_button.grid(row=4, column=2, sticky="se", padx=10, pady=(0, 10))

    def update_settings(self) -> None:
        """
        Update the settings in the sensor settings combobox
        Called everytime a new sensor is selected
        """
        self.settings = self.app_state.selected_sensor.settings
        print("Settings updated:", self.settings)
        if self.settings is None:
            # log_message(level="debug", message="No settings found for the selected sensor")
            return
        self.sensor_settings_combobox.configure(values=list(self.settings.keys()))
        self.sensor_settings_combobox.set("insolight")
        self.select_bus_settings()

    def update_com_ports(self, event=None) -> None:
        """
        Update the COM port list in the client_com_port Combobox
        """
        com_port_list = scan_com_ports()
        self.client_com_port_box["values"] = com_port_list
        if com_port_list:
            self.client_com_port_box.set(com_port_list[-1])

    def select_bus_settings(self, event=None) -> None:  # pylint: disable=unused-argument
        """
        Fetch the corresponding settings and set them in the parity and baudrate comboboxes
        """
        print("Selecting bus settings")
        if self.settings is not None:
            selected_bus = self.sensor_settings_combobox.get()
            if selected_bus == "custom":
                self.client_parity_combobox.configure(
                    values=self.settings[selected_bus]["p_values"]
                )
                self.client_baudrate_combobox.configure(
                    values=self.settings[selected_bus]["b_values"]
                )
            self.client_parity_combobox.set(self.settings[selected_bus]["parity"])
            self.client_baudrate_combobox.set(self.settings[selected_bus]["baudrate"])
            self.client_parity_combobox.configure(
                state=self.settings[selected_bus]["state"]
            )
            self.client_baudrate_combobox.configure(
                state=self.settings[selected_bus]["state"]
            )

    def update_event(self, event_type: str, data: Any = None) -> None:
        """
        Update the SensorSettingsFrame based on the event type
        """
        print(f"SensorSettingsFrame received event: {event_type} with data: {data}")
        if event_type == "selected_sensor_changed":
            self.update_settings()
        elif event_type == "sensor_settings_changed":
            self.select_bus_settings()
