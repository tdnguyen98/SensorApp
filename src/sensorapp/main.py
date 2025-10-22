"""Main entry point for the application. Sets up the application state and launches the main GUI."""
from .models.app_state import AppState
from .views.main_app import MainApp

def main():
    """Main entry point for the application."""
    app_state = AppState()
    MainApp(app_state=app_state, title="Sensor Connection App")


if __name__ == "__main__":
    main()
