ICON_CLOSE = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

ICON_MIN = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

ICON_MAX = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect x="5" y="5" width="14" height="14" rx="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

DARK_THEME = """
/* Global Nature Dark Theme */
QWidget {
    background-color: #222426;
    color: #E8E9F3;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
}
#TitleBar {
    background-color: #1a1c1e;
}
#TitleLabel {
    color: #E8E9F3;
    font-size: 16px;
    font-weight: bold;
    background: transparent;
}
#minBtn, #maxBtn, #closeBtn {
    background-color: transparent;
    color: #8fa898;
    border: none;
    font-weight: bold;
}
#minBtn:hover, #maxBtn:hover {
    background-color: #3b5747;
    color: #e3e8e5;
}
#closeBtn:hover {
    background-color: #c23a3a;
    color: white;
}
#SetupBtn, #ThemeBtn {
    font-weight: bold;
    padding: 4px;
    background-color: #2C2F33;
    color: #E8E9F3;
    border-radius: 4px;
}
#SetupBtn:hover, #ThemeBtn:hover {
    background-color: #3b5747;
}
#ApiInfoLabel, #FileLabel {
    color: #8fa898;
    font-style: italic;
    background: transparent;
}
#ConnLabel {
    color: #c23a3a;
    font-weight: bold;
    background: transparent;
}
#ConnLabel[connected="true"] {
    color: #5a8f69;
}
QLineEdit, QTextEdit, QComboBox, QPlainTextEdit {
    background-color: #2C2F33;
    border: 1px solid #4a4d53;
    border-radius: 6px;
    padding: 6px;
    color: #E8E9F3;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #5a8f69;
    background-color: #383c42;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #2C2F33;
    border: 1px solid #4a4d53;
    selection-background-color: #4a4d53;
}
QPushButton {
    background-color: #D98D48;
    color: #ffffff;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}
QPushButton:hover { background-color: #e5a467; }
QPushButton:pressed { background-color: #a8682e; }
QPushButton:disabled { background-color: #4a4d53; color: #8fa898; }
QGroupBox {
    background-color: #2C2F33;
    border-radius: 10px;
    border: 1px solid #4a4d53;
    margin-top: 20px;
    padding: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #8fa898;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #222426;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4a4d53;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover { background: #5a8f69; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QTableWidget {
    background-color: #2C2F33;
    alternate-background-color: #222426;
    gridline-color: #4a4d53;
    border: 1px solid #4a4d53;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #222426;
    color: #E8E9F3;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #5a8f69;
    font-weight: bold;
}
QStatusBar {
    background-color: #1a1c1e;
    color: #8fa898;
    border-top: 1px solid #4a4d53;
}
QProgressBar {
    border: 1px solid #4a4d53;
    border-radius: 6px;
    background-color: #222426;
    text-align: center;
    color: white;
}
QProgressBar::chunk {
    background-color: #5a8f69;
    border-radius: 5px;
}
"""

LIGHT_THEME = """
/* Global Nature Light Theme */
QWidget {
    background-color: #FDFBF7;
    color: #2C251F;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
}
#TitleBar {
    background-color: #E8E3D8;
}
#TitleLabel {
    color: #2C251F;
    font-size: 16px;
    font-weight: bold;
    background: transparent;
}
#minBtn, #maxBtn, #closeBtn {
    background-color: transparent;
    color: #6C665F;
    border: none;
    font-weight: bold;
}
#minBtn:hover, #maxBtn:hover {
    background-color: #D3CEC4;
    color: #2C251F;
}
#closeBtn:hover {
    background-color: #c23a3a;
    color: white;
}
#SetupBtn, #ThemeBtn {
    font-weight: bold;
    padding: 4px;
    background-color: #FDFBF7;
    color: #2C251F;
    border: 1px solid #D3CEC4;
    border-radius: 4px;
}
#SetupBtn:hover, #ThemeBtn:hover {
    background-color: #D3CEC4;
}
#ApiInfoLabel, #FileLabel {
    color: #6C665F;
    font-style: italic;
    background: transparent;
}
#ConnLabel {
    color: #c23a3a;
    font-weight: bold;
    background: transparent;
}
#ConnLabel[connected="true"] {
    color: #5a8f69;
}
QLineEdit, QTextEdit, QComboBox, QPlainTextEdit {
    background-color: #F4F1EA;
    border: 1px solid #D3CEC4;
    border-radius: 6px;
    padding: 6px;
    color: #2C251F;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border: 1px solid #7DA27E;
    background-color: #FFFFFF;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #F4F1EA;
    border: 1px solid #D3CEC4;
    selection-background-color: #D3CEC4;
    selection-color: #2C251F;
}
QPushButton {
    background-color: #D98D48;
    color: #ffffff;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}
QPushButton:hover { background-color: #e5a467; }
QPushButton:pressed { background-color: #a8682e; }
QPushButton:disabled { background-color: #D3CEC4; color: #6C665F; }
QGroupBox {
    background-color: #F4F1EA;
    border-radius: 10px;
    border: 1px solid #D3CEC4;
    margin-top: 20px;
    padding: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #6C665F;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #FDFBF7;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #D3CEC4;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover { background: #7DA27E; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QTableWidget {
    background-color: #FDFBF7;
    alternate-background-color: #F4F1EA;
    gridline-color: #D3CEC4;
    border: 1px solid #D3CEC4;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #E8E3D8;
    color: #2C251F;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #7DA27E;
    font-weight: bold;
}
QStatusBar {
    background-color: #E8E3D8;
    color: #6C665F;
    border-top: 1px solid #D3CEC4;
}
QProgressBar {
    border: 1px solid #D3CEC4;
    border-radius: 6px;
    background-color: #FDFBF7;
    text-align: center;
    color: #2C251F;
}
QProgressBar::chunk {
    background-color: #7DA27E;
    border-radius: 5px;
}
"""
