'''
    This module contains the LoggingFrame class who contain the logging display
    of the app.
'''
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from typing import Any

from ..services.logging_system import setup_logging, log_message
from ..models.app_state import AppState
from ..observers.base import Observer

class LoggingFrame(ttk.Frame, Observer):
    def __init__(self, parent, *, app_state: AppState):
        super().__init__(parent)
        self.app_state = app_state
        self.app_state.attach(self)
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
        '''
            Create the Text widget for displaying logs
        '''
        # Create a read-only Text widget for displaying logs
        self.log_status_text = tk.Text(self, height=2, state="disabled", wrap="word")
        self.log_status_text.configure(font=tkFont.Font(family="Consolas", size=14))
        # Create color tags for the log_status_text widget
        self.log_status_text.tag_configure("connected", foreground="green", font=tkFont.Font(weight="bold"))
        self.log_status_text.tag_configure("disconnected", foreground="red" , font=tkFont.Font(weight="bold"))

        self.log_text = tk.Text(self, height=10, state="disabled", wrap="word")
        self.log_text.configure(font=tkFont.Font(family="Consolas", size=14))

        # Create a button to toggle debug mode
        self.debug_button = ttk.Button(self, text="Debug", command=lambda: self.app_state.notify(event_type='button_debug'))

        # Create a button to clear the logs
        self.log_clear = ttk.Button(self, text="Clear", command=self.clear_log)


    def layout_logging_widgets(self):
        '''
            Layout the widgets for the Logging frame
        '''
        self.log_status_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        self.debug_button.grid(row=2, column=0, sticky="sw")
        self.log_clear.grid(row=2, column=0, sticky="se")


    def log_message(self, message, level="info"):
        '''
            Log a message with the given level
        '''
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n', level)
        self.log_text.config(state='disabled', wrap='word')
        self.log_text.see(tk.END)


    def clear_log(self):
        '''
            Clear the text within the log_text widget (inside the log_frame)
        '''
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

    def update_status_display(self, settings: list[str]) -> None:
        '''
            Update the status display based on the connection status
        '''
        if self.app_state.is_client_connected:
            self.log_status_text.config(state="normal")
            self.log_status_text.delete("1.0", tk.END)
            self.log_status_text.insert(tk.END, "Status: ")
            self.log_status_text.insert(tk.END, "Connected", "connected")
            self.log_status_text.insert(
                tk.END,
                " " * 5 
                + f"Sensor: {self.app_state.selected_sensor}"
                + " " * 5
                + f"Modbus settings: {settings[0]}"
                + " " * 5
                + f"baudrate: {settings[1]}"
                + " " * 5
                + f"parity: {settings[2]}\n",
                "default",
            )
        else:
            self.log_status_text.config(state="normal")
            self.log_status_text.delete("1.0", tk.END)
            self.log_status_text.insert(tk.END, "Status: ")
            self.log_status_text.insert(tk.END, "Disconnected\n", "disconnected")
            self.log_status_text.config(state="disabled")


    def update_event(self, event_type: str, data: Any = None) -> None:
        '''
            Observer pattern - react to AppState events
            This is where automatic logging happens!
        '''
        # Map events to log messages
        event_log_mapping = {
            'selected_sensor_changed': {
                'level': 'info',
                'message': f"Sensor selected: {self.app_state.selected_sensor.sensor_name}"
            }
        }
        if event_type == 'button_debug':
            # Toggle debug mode in AppState
            self.app_state.debug_mode = not self.app_state.debug_mode
            if self.app_state.debug_mode:
                self.debug_button.config(text="Stop Debug")
                setup_logging(self.log_message, debug=True)
                log_message(level='info', message="Debug mode enabled")
            else:
                self.debug_button.config(text="Debug")
                setup_logging(self.log_message, debug=False)
                log_message(level='info', message="Debug mode disabled")
            return

        # Handle connection status display
        if event_type == 'connected':
            self.update_status_display(["insolight", "9600", "N"])
        elif event_type == 'disconnected':
            self.update_status_display(["Disconnected"])

        # Auto-log events
        if event_type in event_log_mapping:
            log_config = event_log_mapping[event_type]
            message = log_config['message']
            level = log_config['level']
            log_message(level=level, message=message)
