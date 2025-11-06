"""
This module contain the sensor selection notebook widget used in the first row of the GUI.
"""

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk

from typing import Any

from ..observers.base import Observer

from ..models.app_state import AppState
from ..models.sensors.sensor import Sensor, fetch_sensors_list


class SensorSelectionNoteBook(ttk.Notebook, Observer):
    """
    Notebook widget containing two tabs:
        - Sensor selection tab
        - Color code help tab, for sensor connections
    """

    def __init__(self, parent, app_state: AppState):
        self.app_state = app_state
        super().__init__(parent)

        # Create the frames for the Sensor and Color Code tabs and display them
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        """
        Create the widgets for the Sensor selection and Color Code tabs Notebook
        """
        # Create the Notebook containing the Sensor and Color Code frames
        self.select_sensor_frame = ttk.Frame(self)
        self.sensor_color_help_frame = ttk.Frame(self)

        # Add the frames to the notebook
        self.add(self.select_sensor_frame, text="Sensor")
        self.add(self.sensor_color_help_frame, text="Color Codes")
        self.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Create the "Choose Sensor" frame inside the notebook
        self.select_sensor_label = ttk.Label(
            self.select_sensor_frame, text="Sensor selection", style="Underlined.TLabel"
        )
        self.select_sensor_label.configure(font=tkFont.Font(size=18, underline=True))
        self.sensor_combobox_label = ttk.Label(
            self.select_sensor_frame, text="Choose Sensor"
        )
        self.sensor_combobox = ttk.Combobox(
            self.select_sensor_frame,
            values=fetch_sensors_list(),
            width=13,
            state="readonly",
        )
        self.sensor_combobox.set(fetch_sensors_list()[0])

        # Update the sensor data when the combobox selection changes
        self.sensor_combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected)

    def layout_widgets(self):
        """
        Layout the widgets for the Sensor selection within the Notebook
        """
        self.select_sensor_label.grid(
            row=0, column=0, columnspan=3, pady=(10, 5), padx=10, sticky="nw"
        )
        self.sensor_combobox_label.grid(row=1, column=0, sticky="sw", padx=10, pady=10)
        self.sensor_combobox.grid(
            row=2, column=0, padx=(30, 0), pady=(0, 10), sticky="sw"
        )

    def update_color_wires(self) -> None:
        """Update the color wires in the sensor_color_help_frame"""
        # Clear existing widgets
        for widget in self.sensor_color_help_frame.winfo_children():
            widget.destroy()

        sensor: Sensor = self.app_state.selected_sensor

        # Get wire configurations
        configs = sensor.wire_color_configurations
        if not configs:
            label = ttk.Label(
                self.sensor_color_help_frame,
                text="No wire configuration \navailable for this sensor",
                style="Italic.TLabel",
            )
            label.grid(row=0, column=0, columnspan=2, padx=10, pady=(50, 20))
            return

        # Create wire displays
        for i, config in enumerate(configs):
            # Create label
            label = ttk.Label(self.sensor_color_help_frame, text=config.label, width=6)
            label.grid(row=1 + i, column=0, sticky="e", padx=(5, 0), pady=(10, 0))

            # Create canvas
            canvas = tk.Canvas(
                self.sensor_color_help_frame, width=108, height=20, highlightthickness=0
            )
            canvas.grid(row=1 + i, column=1, sticky="w", padx=(5, 0), pady=(10, 0))

            # Draw sections
            # Normalize color and text to sequences so zip() always gets iterables
            def _as_list(val):
                if val is None:
                    return []
                if isinstance(val, (list, tuple)):
                    return list(val)
                return [val]

            color_seq = _as_list(config.color)
            text_seq = _as_list(config.text)
            # If text sequence is shorter than colors, pad with empty strings
            if len(text_seq) < len(color_seq):
                text_seq.extend([""] * (len(color_seq) - len(text_seq)))

            for j, (color, text) in enumerate(zip(color_seq, text_seq)):
                x1 = j * 36
                x2 = (j + 1) * 36
                canvas.create_rectangle(x1, 0, x2, 20, fill=color, outline="")
                if text:
                    if color == "white":
                        canvas.create_text(
                            (x1 + x2) // 2,
                            11,
                            text=text,
                            fill="black",
                            font=("Helvetica", 10),
                        )
                    elif color == "yellow":
                        canvas.create_text(
                            (x1 + x2) // 2,
                            11,
                            text=text,
                            fill="black",
                            font=("Helvetica", 10),
                        )
                    else:
                        canvas.create_text(
                            (x1 + x2) // 2,
                            11,
                            text=text,
                            fill="white",
                            font=("Helvetica", 10),
                        )

    def on_combobox_selected(self, event=None):  # pylint: disable=unused-argument
        """
        Update the selected sensor and color wires when the combobox selection changes
        """
        self.app_state.selected_sensor = self.sensor_combobox.get()

    def on_tab_change(self, event=None):  # pylint: disable=unused-argument
        """
        Notify the app state that the tab has changed to update the notebook
        """
        data = None
        # If the user switch to the Color Codes tab, add flag to update the wires colors
        if self.index(self.select()) == 1:
            data = "Color Codes"
        self.app_state.notify(event_type="sensor_tab_changed", data=data)

    def update_event(self, event_type: str, data: Any = None) -> None:
        """
        Receive update when notification is sent from Subject.
        """
        if event_type == "sensor_tab_changed":
            if data == "Color Codes":
                self.update_color_wires()
            self.update_idletasks()
        elif event_type == "client_connected" or event_type == "client_disconnected":
            state = "disabled" if self.app_state.is_client_connected else "readonly"
            self.sensor_combobox.configure(state=state)
