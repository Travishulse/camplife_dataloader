from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer

from config import VERSION

class LoadingScreen(QWidget):
    """Lightweight loading screen that appears instantly"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Container with rounded corners and camping theme
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #15221b;
                border-radius: 15px;
                border: 2px solid #3b5747;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        
        # Title with emoji
        title = QLabel("🏕️ Camplife Data Loader")
        title.setStyleSheet("color: #e3e8e5; font-size: 24px; font-weight: bold; background: transparent; border: none;")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)
        
        # Version
        version_label = QLabel(f"v{VERSION}")
        version_label.setStyleSheet("color: #c27a3a; font-size: 14px; background: transparent; border: none;")
        version_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(version_label)
        
        # Loading message
        self.loading_label = QLabel("Loading application...")
        self.loading_label.setStyleSheet("color: #8fa898; font-size: 14px; font-style: italic; background: transparent; border: none;")
        self.loading_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.loading_label)
        
        # Simple animated dots
        self.dots = ""
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.animate_dots)
        self.dot_timer.start(500)
        
        container_layout.addStretch()
        layout.addWidget(container)
        self.setLayout(layout)
    
    def animate_dots(self):
        """Simple loading animation with dots"""
        self.dots = self.dots + "." if len(self.dots) < 3 else ""
        self.loading_label.setText(f"Loading application{self.dots}")
    
    def close_screen(self):
        """Stop timer and close"""
        self.dot_timer.stop()
        self.close()
