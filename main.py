import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.gui.themes import LIGHT_THEME
from src.gui.loading_screen import LoadingScreen
from src.gui.main_window import FramelessCamplifeLoader
from src.core.logger import setup_logger
from config import CONFIG_FILE, LOG_DIR

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = setup_logger()
    logger.info("Application started")
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_THEME)
    
    # Show loading screen immediately
    loading_screen = LoadingScreen()
    loading_screen.show()
    app.processEvents()
    
    # Create main window but don't show it yet
    window = FramelessCamplifeLoader()
    
    def on_connection_attempt_finished(success):
        """Callback to transition from loading screen to main window."""
        # Disconnect to prevent multiple calls
        try:
            window.api_client.connection_changed.disconnect(on_connection_attempt_finished)
        except Exception:
            pass
        
        loading_screen.close_screen()
        window.show()

    # Setup connection handling
    window.api_client.connection_changed.connect(on_connection_attempt_finished)
    
    # Safety timeout: if connection takes longer than 15s, show window anyway
    QTimer.singleShot(15000, lambda: on_connection_attempt_finished(False))
    
    # Start auto-connect if config exists
    if os.path.exists(CONFIG_FILE):
        loading_screen.loading_label.setText("Connecting to Camplife API...")
        window.api_client.connect()
    else:
        # No config, just show the window
        QTimer.singleShot(500, lambda: on_connection_attempt_finished(False))
    
    sys.exit(app.exec())
