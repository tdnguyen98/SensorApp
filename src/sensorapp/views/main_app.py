"""Main application window for the sensor app."""
import tkinter as tk

from .sensor_selection_notebook import SensorSelectionNoteBook
from .sensor_settings_frame import SensorSettingsFrame
from .sensor_id_test_notebook import SensorIdTestNoteBook
from .logging_frame import LoggingFrame

from ..models.app_state import AppState

class MainApp(tk.Tk):
    """Root window of the application."""
    def __init__(self, *, app_state: AppState, title="Sensor Application"):
        super().__init__()
        self.app_state = app_state

        # Main Setup
        self.title(title)
        self.resizable(False, False)
        self.rowconfigure((0, 1, 2), weight=1)
        self.columnconfigure((0, 1), weight=1)

        # Add widgets to main window
        self.sensor_selection_notebook = SensorSelectionNoteBook(self, app_state=self.app_state)
        self.sensor_selection_notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.app_state.attach(observer=self.sensor_selection_notebook)

        self.sensor_id_test_notebook = SensorIdTestNoteBook(self, app_state=self.app_state)
        self.sensor_id_test_notebook.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.app_state.attach(observer=self.sensor_id_test_notebook)

        self.logging_frame = LoggingFrame(self, app_state=self.app_state)
        self.logging_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.app_state.attach(observer=self.logging_frame)

        self.sensor_settings_frame = SensorSettingsFrame(self, app_state=self.app_state)
        self.sensor_settings_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.app_state.attach(observer=self.sensor_settings_frame)
        self._check_queue()
        # Run
        self.mainloop()

    def _check_queue(self):
        """Check the app state queue for messages."""
        self.app_state.check_queue()
        self.after(100, self._check_queue)  # Check again after 100 ms