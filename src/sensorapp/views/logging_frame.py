"""
This module contains the LoggingFrame class who contain the logging display
of the app.
"""

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import time

from ..services.logging_system import setup_logging, log_message
from ..models.app_state import AppState
from ..observers.base import Observer
from ..services.client import SerialClient, SDI12Client

class LoggingFrame(ttk.Frame, Observer):
    """Frame for displaying logs in the application."""
    def __init__(self, parent, *, app_state: AppState):
        super().__init__(parent)
        self.app_state = app_state
        # self.app_state.attach(observer=self)
        self._spinner_step = 0
        self._spinner_running = True
        self._spinner_after_id = None
        self._spinner_message: str = ""
        # Set up logging with the custom handler for the log_text widget
        setup_logging(self.log_message)

        # Add a border and padding to the frame
        self.configure(relief="groove", padding=(20, 10))

        # Create the Text widget for displaying logs
        self.create_logging_widgets()
        self.layout_logging_widgets()

        # Configure tags for different log levels
        self.log_text.tag_configure("info", foreground="white")
        self.log_text.tag_configure("debug", foreground="white")
        self.log_text.tag_configure("warning", foreground="yellow")
        self.log_text.tag_configure("error", foreground="red")

        self.update_status_display(["Disconnected"])

    def create_logging_widgets(self):
        """
        Create the Text widget for displaying logs
        """
        # Create a read-only Text widget for displaying logs
        self.log_status_text = tk.Text(self, height=1, state="disabled", wrap="word")
        self.log_status_text.configure(font=tkFont.Font(family="Consolas", size=14))
        # Create color tags for the log_status_text widget
        self.log_status_text.tag_configure(
            "connected", foreground="green", font=tkFont.Font(weight="bold")
        )
        self.log_status_text.tag_configure(
            "disconnected", foreground="red", font=tkFont.Font(weight="bold")
        )

        self.log_text = tk.Text(self, height=10, state="disabled", wrap="word")
        self.log_text.configure(font=tkFont.Font(family="Consolas", size=14))

        # Create a button to toggle debug mode
        self.debug_button = ttk.Button(
            self,
            text="Debug",
            command=lambda: self.app_state.notify(event_type="button_debug"),
        )

        # Create a button to clear the logs
        self.log_clear = ttk.Button(self, text="Clear", command=self.clear_log)

    def layout_logging_widgets(self):
        """
        Layout the widgets for the Logging frame
        """
        self.log_status_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        self.debug_button.grid(row=2, column=0, sticky="sw")
        self.log_clear.grid(row=2, column=0, sticky="se")

    def log_message(self, message, level="info"):
        """
        Log a message with the given level
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n", level)
        self.log_text.config(state="disabled", wrap="word")
        self.log_text.see(tk.END)

    def clear_log(self):
        """
        Clear the text within the log_text widget (inside the log_frame)
        """
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def update_status_display(self, settings: list[str]) -> None:
        """
        Update the status display based on the connection status
        """
        print(f"settings received for status update: {settings}")
        if self.app_state.is_client_connected:
            self.log_status_text.config(state="normal")
            self.log_status_text.delete("1.0", tk.END)
            self.log_status_text.insert(tk.END, "Status: ")
            self.log_status_text.insert(tk.END, "Connected", "connected")
            self.log_status_text.insert(
                tk.END,
                " " * 5
                + f"Sensor: {self.app_state.selected_sensor.sensor_name}"
                + " " * 5
                + f"baudrate: {settings[0]}"
                + " " * 5
                + f"parity: {settings[1]}"
                + " " * 5
                + f"slave ID: {chr(self.app_state.slave_id) if isinstance(self.app_state.client, SDI12Client) and self.app_state.slave_id is not None else self.app_state.slave_id}",
                "default",
            )
        else:
            self.log_status_text.config(state="normal")
            self.log_status_text.delete("1.0", tk.END)
            self.log_status_text.insert(tk.END, "Status: ")
            self.log_status_text.insert(tk.END, "Disconnected\n", "disconnected")
        self.log_status_text.config(state="disabled")

    def update_status_display_fetching_id(self, settings: list[str]) -> None:
        """
        Update the status display based on the connection status
        """
        if not self._spinner_running:
            return
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_char = spinners[self._spinner_step % len(spinners)]
        if self.app_state.is_client_connected:
            self.log_status_text.config(state="normal")
            self.log_status_text.delete("1.0", tk.END)
            self.log_status_text.insert(tk.END, "Status: ")
            self.log_status_text.insert(tk.END, "Connected", "connected")
            self.log_status_text.insert(
                tk.END,
                " " * 5
                + f"Sensor: {self.app_state.selected_sensor.sensor_name}"
                + " " * 5
                + f"baudrate: {settings[0]}"
                + " " * 5
                + f"parity: {settings[1]}"
                + " " * 5
                + f"slave ID: {spinner_char}",
                "default",
            )
        self.log_status_text.config(state="disabled")
        self.after(100, lambda: self.update_status_display_fetching_id(settings))

    def update_event(self, event_type: str, **kwargs) -> None:
        """
        Observer pattern - react to AppState events
        This is where automatic logging happens!
        """
        # Map events to log messages
        event_log_mapping = {
            "selected_sensor_changed": {
                "level": "info",
                "message": f"Sensor selected: {self.app_state.selected_sensor.sensor_name}",
            },
            "client_connected": {
                "level": "info",
                "message": f"{self.app_state.selected_sensor.protocol} client connected.",
            },
            "client_disconnected": {
                "level": "warning",
                "message": f"{self.app_state.selected_sensor.protocol} client disconnected.",
            },
            "slave_id_fetch_cancelled": {
                "level": "warning",
                "message": "Slave ID fetch cancelled.",
            },
            "slave_id_fetch_error": {
                "level": "error",
                "message": "Error fetching slave ID.",
            },
            "apply_sensor_settings": {
                "level": "info",
                "message": "Sensor settings successfully changed, reconnecting client.",
            },
            "apply_sensor_settings_sdi12": {
                "level": "info",
                "message": "SDI-12 sensor settings successfully changed",
            },
            "reboot_required": {
                "level": "warning",
                "message": "Sensor reboot required. Please reboot the sensor for changes to take effect before reconnecting.",
            },
        }
        if event_type == "error":
            error_message = kwargs.get("error_message", "Unknown error")
            log_message(level="error", message=error_message)
        if event_type == "button_debug":
            # Toggle debug mode in AppState
            self.app_state.debug_mode = not self.app_state.debug_mode
            if self.app_state.debug_mode:
                self.debug_button.config(text="Stop Debug")
                setup_logging(self.log_message, debug=True)
                log_message(level="info", message="Debug mode enabled")
            else:
                self.debug_button.config(text="Debug")
                setup_logging(self.log_message, debug=False)
                log_message(level="info", message="Debug mode disabled")
            return

        # Handle connection status display
        if event_type == "client_connected":
            # if self.app_state.slave_id is not None:
            if isinstance(self.app_state.client, SerialClient):
                self.update_status_display(
                    [
                        str(self.app_state.client.baudrate),
                        self.app_state.client.parity,
                        str(self.app_state.slave_id)
                        if self.app_state.slave_id is not None
                        else "N/A",
                    ]
                )
            return

        elif event_type == "client_disconnected":
            self.update_status_display(["Disconnected"])
            if self._spinner_running:
                self.stop_spinner()
            return

        if event_type == "fetching_slave_id":
            if self._spinner_running and self._spinner_after_id is not None:
                self._spinner_running = False  # ← Sets flag to False
                self.after_cancel(
                    self._spinner_after_id
                )  # ← Cancels scheduled after() callback
                # time.sleep(0.1)  # ← Waits 100ms
            message = f"Fetching slave ID {kwargs.get('slave_id', '?')}/255..."
            self.start_spinner(message)
            return

        if event_type == "verifying_current_id":
            if self._spinner_running and self._spinner_after_id is not None:
                self._spinner_running = False  # ← Sets flag to False
                self.after_cancel(
                    self._spinner_after_id
                )  # ← Cancels scheduled after() callback
                # time.sleep(0.1)  # ← Waits 100ms
            message = f"Verifying current slave ID {kwargs.get('slave_id', '?')}/255..."
            self.start_spinner(message)
            return

        if event_type == "current_id_valid":
            self.stop_spinner("Current slave ID is valid")
            if self.app_state.client is not None:
                self.update_status_display(
                    [
                        str(self.app_state.client.baudrate),
                        self.app_state.client.parity,
                        str(self.app_state.slave_id)
                        if self.app_state.slave_id is not None
                        else "N/A",
                    ]
                )
            return

        if event_type == "slave_id_changed" or event_type == "slave_id_valid":
            if self._spinner_running:
                self.stop_spinner("Slave ID fetched")
            self.app_state.restart_missing = False
            if self.app_state.client is not None:
                self.update_status_display(
                    [
                        str(self.app_state.client.baudrate),
                        self.app_state.client.parity,
                        str(self.app_state.slave_id)
                        if self.app_state.slave_id is not None
                        else "N/A",
                    ]
                )
            return

        if event_type == "slave_id_invalid":
            self.stop_spinner("Slave ID invalid")
            if self.app_state.client is not None:
                self.update_status_display(
                    [
                        str(self.app_state.client.baudrate),
                        self.app_state.client.parity,
                        "Invalid",
                    ]
                )
            return

        # Auto-log events
        if event_type in event_log_mapping:
            log_config = event_log_mapping[event_type]
            message = log_config["message"]
            level = log_config["level"]
            log_message(level=level, message=message)

    def start_spinner(self, message: str):
        """Start a non-blocking spinner animation."""
        print("Starting spinner...")
        self._spinner_message = message
        self._spinner_running = True
        self._animate_spinner()
        if isinstance(self.app_state.client, SerialClient):
            self.update_status_display_fetching_id(
                [
                    "Insolight",
                    str(self.app_state.client.baudrate),
                    self.app_state.client.parity,
                ]
            )

        # Auto-stop after duration
        # self.after(duration_ms, self.stop_spinner)

    def _animate_spinner(self):
        """Animate the spinner (called repeatedly via after())."""
        if not self._spinner_running:
            return

        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_char = spinners[self._spinner_step % len(spinners)]
        message_with_spinner = f"{self._spinner_message} {spinner_char}"

        # Update spinner display
        self.log_text.config(state="normal")
        try:
            last_line = self.log_text.get("end-2l", "end-1l")
            if any(char in last_line for char in spinners):
                self.log_text.delete("end-2l", "end-1l")
        except tk.TclError:
            pass

        self.log_text.insert(tk.END, message_with_spinner + "\n", "info")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)

        self._spinner_step += 1
        # Schedule next animation frame
        self._spinner_after_id = self.after(100, self._animate_spinner)

    def stop_spinner(self, completion_message: str = ""):
        """Stop the spinner and show completion."""
        self._spinner_running = False
        self.log_text.config(state="normal")
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        try:
            last_line = self.log_text.get("end-2l", "end-1l")
            if any(char in last_line for char in spinners):
                self.log_text.delete("end-2l", "end-1l")
        except tk.TclError:
            pass

        if completion_message == "":
            time.sleep(0.2)
            return

        self.log_text.insert(tk.END, completion_message + "\n", "info")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)
