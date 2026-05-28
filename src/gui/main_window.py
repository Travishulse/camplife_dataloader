import os
import sys
import json
import pandas as pd
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QLineEdit, QTextEdit, QGroupBox, QFileDialog,
    QStatusBar, QGridLayout, QSizeGrip, QApplication, QDialog
)
from PySide6.QtGui import QMouseEvent, QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtSvg import QSvgRenderer

from config import VERSION, CONFIG_FILE, CACHE_FILE, UPDATE_REPO_OWNER, UPDATE_REPO_NAME, APP_DIR
from src.api.client import CamplifeAPIClient
from src.gui.themes import DARK_THEME, LIGHT_THEME, ICON_MIN, ICON_MAX, ICON_CLOSE
from src.gui.setup_dialog import SetupDialog
from src.gui.preview_dialog import PreviewDialog
from src.core.updater import UpdateChecker, UpdateDownloader
import subprocess

class FramelessCamplifeLoader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Camplife Data Loader 🏕️ v{VERSION}")
        
        # Set Window Icon
        icon_path = os.path.join(APP_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        screen_geo = QApplication.primaryScreen().availableGeometry()
        w = min(750, int(screen_geo.width() * 0.85))
        h = min(550, int(screen_geo.height() * 0.85))
        self.resize(w, h)
        x = screen_geo.x() + (screen_geo.width() - w) // 2
        y = screen_geo.y() + (screen_geo.height() - h) // 2
        self.move(x, y)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.old_pos = None
        self.is_dark_theme = False

        self.loaded_df = None
        self._resorts_data = []
        self._current_resort_alias = None

        # Setup API Client
        self.api_client = CamplifeAPIClient()
        self.api_client.status_msg.connect(self.update_status)
        self.api_client.connection_changed.connect(self.update_connection_status)
        self.api_client.resorts_loaded.connect(self.populate_resorts)
        self.api_client.memberships_loaded.connect(self.populate_memberships)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._init_gui(main_layout)
        self._load_cache()

        # Check for updates in the background
        self.update_checker = UpdateChecker(VERSION, UPDATE_REPO_OWNER, UPDATE_REPO_NAME)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.start()

    def _init_gui(self, main_layout):
        # Title bar
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        tlay = QHBoxLayout(title_bar)
        tlay.setContentsMargins(10, 2, 10, 2)
        self.title_label = QLabel(f"🏕️ Camplife Data Loader v{VERSION}")
        self.title_label.setObjectName("TitleLabel")
        tlay.addWidget(self.title_label)
        tlay.addStretch()

        # Resort label (displays selected resort from config)
        self.resort_label = QLabel("No resort selected")
        self.resort_label.setToolTip("Default resort (configured in Setup)")
        tlay.addWidget(QLabel("Resort:"))
        tlay.addWidget(self.resort_label)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.start_async_connect)
        tlay.addWidget(self.connect_btn)

        self.setup_btn = QPushButton("⚙️ Setup")
        self.setup_btn.setObjectName("SetupBtn")
        self.setup_btn.clicked.connect(self.open_setup_dialog)
        tlay.addWidget(self.setup_btn)

        self.theme_btn = QPushButton("🌓 Theme")
        self.theme_btn.setObjectName("ThemeBtn")
        self.theme_btn.clicked.connect(self.toggle_theme)
        tlay.addWidget(self.theme_btn)

        # Title bar buttons with SVG icons
        self.min_btn = self._create_icon_btn(ICON_MIN, self.showMinimized, "minBtn")
        self.max_btn = self._create_icon_btn(ICON_MAX, self.toggle_max_restore, "maxBtn")
        self.close_btn = self._create_icon_btn(ICON_CLOSE, self.close, "closeBtn")
        
        tlay.addWidget(self.min_btn)
        tlay.addWidget(self.max_btn)
        tlay.addWidget(self.close_btn)

        main_layout.addWidget(title_bar)

        # Central area
        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(15, 15, 15, 15)
        cl.setSpacing(10)
        main_layout.addWidget(central)

        # API info
        self.api_info_label = QLabel()
        self.api_info_label.setObjectName("ApiInfoLabel")
        cl.addWidget(self.api_info_label)
        self.load_api_info()

        # Define all column dropdown references
        self.camplife_id_col = QComboBox()
        self.member_number_col = QComboBox()
        self.membership_col = QComboBox()
        self.effective_from_col = QComboBox()
        self.effective_to_col = QComboBox()
        self.tag_col = QComboBox()
        self.note_col = QComboBox()

        # Optional Overrides fields
        self.membership_dropdown = QComboBox()
        self.membership_dropdown.setToolTip("If set, this membership type will be applied to all rows (override). Leave blank to use mapped column.")
        
        self.tag_entry = QLineEdit()
        self.tag_entry.setPlaceholderText("Enter tag here...")
        self.tag_entry.setToolTip("If set, this tag will be applied to all rows. Otherwise, use mapped column.")
        
        self.note_entry = QTextEdit()
        self.note_entry.setMaximumHeight(60)
        self.note_entry.setPlaceholderText("Enter note here...")
        self.note_entry.setToolTip("If set, this note will be applied to all rows. Otherwise, use mapped column.")

        # File upload & mapping
        file_box = self.create_card_group("📁 Step 1: File Upload & Column Mapping")
        file_layout = QVBoxLayout()
        file_select = QHBoxLayout()
        self.file_btn = QPushButton("Select File")
        self.file_btn.clicked.connect(self.load_file)
        self.file_btn.setToolTip("Load a CSV or Excel file to map columns")
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("FileLabel")
        file_select.addWidget(self.file_btn)
        file_select.addWidget(self.file_label)
        file_layout.addLayout(file_select)

        # Mapping grid
        mapping_grid = QGridLayout()
        mapping_grid.addWidget(QLabel("Camplife ID"), 0, 0)
        mapping_grid.addWidget(self.camplife_id_col, 1, 0)
        mapping_grid.addWidget(QLabel("Member Number"), 0, 1)
        mapping_grid.addWidget(self.member_number_col, 1, 1)
        mapping_grid.addWidget(QLabel("Membership Type"), 0, 2)
        mapping_grid.addWidget(self.membership_col, 1, 2)
        mapping_grid.addWidget(QLabel("Effective From"), 2, 0)
        mapping_grid.addWidget(self.effective_from_col, 3, 0)
        mapping_grid.addWidget(QLabel("Effective To"), 2, 1)
        mapping_grid.addWidget(self.effective_to_col, 3, 1)
        mapping_grid.addWidget(QLabel("Tag"), 2, 2)
        mapping_grid.addWidget(self.tag_col, 3, 2)
        mapping_grid.addWidget(QLabel("Note"), 2, 3)
        mapping_grid.addWidget(self.note_col, 3, 3)
        file_layout.addLayout(mapping_grid)
        file_box.setLayout(file_layout)
        cl.addWidget(file_box)

        # Overrides section
        overrides_box = self.create_card_group("⚙️ Step 2: Optional Overrides")
        overrides_layout = QGridLayout()
        overrides_layout.addWidget(QLabel("Membership Type:"), 0, 0)
        overrides_layout.addWidget(self.membership_dropdown, 1, 0)
        overrides_layout.addWidget(QLabel("Tag Name:"), 0, 1)
        overrides_layout.addWidget(self.tag_entry, 1, 1)
        overrides_layout.addWidget(QLabel("Note:"), 0, 2)
        overrides_layout.addWidget(self.note_entry, 1, 2)
        overrides_box.setLayout(overrides_layout)
        cl.addWidget(overrides_box)

        # Preview button
        self.preview_btn = QPushButton("Review and Upload")
        self.preview_btn.setToolTip("Open a preview of the loaded file and start upload from there")
        self.preview_btn.clicked.connect(self.open_preview)
        cl.addWidget(self.preview_btn)

        # Update Banner (Hidden by default)
        self.update_banner = QWidget()
        self.update_banner.setObjectName("UpdateBanner")
        self.update_banner.setStyleSheet("""
            #UpdateBanner {
                background-color: #3b5747;
                border: 1px solid #5a8f69;
                border-radius: 6px;
                margin-top: 5px;
            }
            #UpdateLabel {
                color: #e3e8e5;
                font-weight: bold;
                font-size: 13px;
                background: transparent;
            }
            #UpdateBtn {
                background-color: #D98D48;
                color: white;
                font-size: 12px;
                padding: 4px 10px;
                border-radius: 4px;
                border: none;
            }
            #UpdateBtn:hover {
                background-color: #e5a467;
            }
            #UpdateBtn:disabled {
                background-color: #4a4d53;
                color: #8fa898;
            }
        """)
        
        ub_layout = QHBoxLayout(self.update_banner)
        ub_layout.setContentsMargins(10, 6, 10, 6)
        
        self.update_label = QLabel("A new version is available!")
        self.update_label.setObjectName("UpdateLabel")
        ub_layout.addWidget(self.update_label)
        
        ub_layout.addStretch()
        
        self.update_btn = QPushButton("Update Now")
        self.update_btn.setObjectName("UpdateBtn")
        self.update_btn.setFixedSize(130, 26)
        self.update_btn.clicked.connect(self.start_update_download)
        ub_layout.addWidget(self.update_btn)
        
        self.update_banner.hide()
        cl.addWidget(self.update_banner)

        # Status bar
        self.status = QStatusBar()
        self.status.showMessage("Ready")
        cl.addWidget(self.status)

        self.conn_label = QLabel("Disconnected")
        self.conn_label.setObjectName("ConnLabel")
        self.status.addPermanentWidget(self.conn_label)

        size_grip = QSizeGrip(self)
        self.status.addPermanentWidget(size_grip)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            QApplication.instance().setStyleSheet(DARK_THEME)
        else:
            QApplication.instance().setStyleSheet(LIGHT_THEME)
        self._refresh_window_ctrl_icons()

    def open_setup_dialog(self):
        dialog = SetupDialog(self, resorts_data=self._resorts_data)
        if dialog.exec() == QDialog.Accepted:
            self.load_api_info()
            self._current_resort_alias = dialog.selected_resort_alias
            self.load_resort_from_config()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                resorts = cache.get("resorts", [])
                memberships = cache.get("memberships", [])
                if resorts:
                    self._resorts_data = resorts
                    self.load_resort_from_config()
                if memberships:
                    self.populate_memberships(memberships)
            except Exception:
                pass

    def _save_cache(self):
        try:
            cache = {
                "resorts": self._resorts_data,
                "memberships": [self.membership_dropdown.itemText(i)
                                 for i in range(self.membership_dropdown.count())
                                 if self.membership_dropdown.itemText(i)]
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception:
            pass

    def load_api_info(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    k = data.get("api_key", "")
                    s = data.get("api_secret", "")
                    if k and s:
                        self.api_info_label.setText(f"🔑 Keys saved ({k[:5]}...)")
                    else:
                        self.api_info_label.setText("🔑 Config exists, missing keys.")
            except Exception as e:
                self.api_info_label.setText(f"🔑 Error reading config: {str(e)}")
        else:
            self.api_info_label.setText("🔑 No API credentials found. Please click Setup.")

    def load_resort_from_config(self):
        """Load default resort alias from config.json and update label."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    resort_alias = data.get("resort_alias", "")
                    self._current_resort_alias = resort_alias

                    if resort_alias and self._resorts_data:
                        # Find resort name matching the alias
                        for r in self._resorts_data:
                            if r.get("alias") == resort_alias:
                                display_name = r.get("propertyName") or r.get("name") or r.get("organizationName") or resort_alias
                                self.resort_label.setText(display_name)
                                return
                    self.resort_label.setText(resort_alias if resort_alias else "Not configured")
            except Exception:
                self.resort_label.setText("Error loading resort")

    @Slot(str, int)
    def update_status(self, msg, duration=0):
        self.status.showMessage(msg, duration)

    @Slot(bool)
    def update_connection_status(self, connected):
        self.connect_btn.setEnabled(True)
        if connected:
            self.connect_btn.setVisible(False)
            self.conn_label.setText("✔ Connected")
            self.conn_label.setProperty("connected", "true")
        else:
            self.connect_btn.setVisible(True)
            self.connect_btn.setText("Connect")
            self.conn_label.setText("Disconnected")
            self.conn_label.setProperty("connected", "false")
        self.conn_label.style().unpolish(self.conn_label)
        self.conn_label.style().polish(self.conn_label)

    def start_async_connect(self):
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        self.api_client.connect()

    @Slot(list)
    def populate_resorts(self, resorts_data):
        self._resorts_data = resorts_data
        self.load_resort_from_config()
        self._save_cache()

    @Slot(list)
    def populate_memberships(self, memberships_list):
        self.membership_dropdown.clear()
        self.membership_dropdown.addItem("")
        self.membership_dropdown.addItems(memberships_list)
        self._save_cache()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
        self.file_label.setText(os.path.basename(file_path))
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                self.loaded_df = pd.read_excel(file_path, dtype=str)
            else:
                self.loaded_df = pd.read_csv(file_path, dtype=str)
            self.populate_column_dropdowns()
            self.auto_select_matching_columns()
            self.status.showMessage(f"File loaded: {os.path.basename(file_path)} ✅", 4000)
        except Exception as e:
            self.status.showMessage(f"File load error: {str(e)}", 7000)

    def populate_column_dropdowns(self):
        if self.loaded_df is None:
            return
        cols = list(self.loaded_df.columns)
        for dd in (self.camplife_id_col, self.member_number_col, self.membership_col,
                   self.effective_from_col, self.effective_to_col, self.tag_col, self.note_col):
            dd.clear()
            dd.addItem("N/A")
            dd.addItems(cols)
            dd.setCurrentIndex(0)

    def auto_select_matching_columns(self):
        mapping_names = {
            "Camplife ID": self.camplife_id_col,
            "Member Number": self.member_number_col,
            "Membership Type": self.membership_col,
            "Effective From": self.effective_from_col,
            "Effective To": self.effective_to_col,
            "Tag": self.tag_col,
            "Note": self.note_col
        }
        for expected, combo in mapping_names.items():
            found_index = None
            for idx, h in enumerate(self.loaded_df.columns):
                if h.strip().lower() == expected.strip().lower():
                    found_index = idx + 1
                    break
            if found_index is None:
                variants = [expected.lower(), expected.replace(" ", "").lower(), expected.split()[0].lower()]
                for idx, h in enumerate(self.loaded_df.columns):
                    if any(v in h.strip().lower() for v in variants):
                        found_index = idx + 1
                        break
            if found_index:
                combo.setCurrentIndex(found_index)
            else:
                combo.setCurrentIndex(0)

    def open_preview(self):
        if self.loaded_df is None:
            self.status.showMessage("No file loaded to preview.", 4000)
            return

        if not self._current_resort_alias:
            self.status.showMessage("Please configure a default resort in Setup.", 4000)
            return

        column_map = {
            "Camplife ID": self.camplife_id_col.currentText(),
            "Member Number": self.member_number_col.currentText(),
            "Membership Type": self.membership_col.currentText(),
            "Effective From": self.effective_from_col.currentText(),
            "Effective To": self.effective_to_col.currentText(),
            "Tag": self.tag_col.currentText(),
            "Note": self.note_col.currentText()
        }
        top_fields = {}
        if self.membership_dropdown.currentText():
            top_fields["Membership Type"] = self.membership_dropdown.currentText()
        if self.tag_entry.text().strip():
            top_fields["Tag"] = self.tag_entry.text().strip()
        if self.note_entry.toPlainText().strip():
            top_fields["Note"] = self.note_entry.toPlainText().strip()

        dlg = PreviewDialog(self, self.loaded_df, column_map, top_fields, self._current_resort_alias, self.api_client)
        dlg.exec()

    def create_card_group(self, title):
        return QGroupBox(title)

    def _create_icon_btn(self, svg_data, callback, obj_name):
        btn = QPushButton()
        btn.setObjectName(obj_name)
        btn.setFixedSize(30, 30)
        btn.clicked.connect(callback)
        btn._svg_data = svg_data
        self._render_icon_btn(btn, svg_data)
        return btn

    def _render_icon_btn(self, btn, svg_data):
        renderer = QSvgRenderer(svg_data.encode())
        pixmap = QPixmap(QSize(16, 16))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        btn.setIcon(QIcon(pixmap))
        btn.setIconSize(QSize(16, 16))

    def _refresh_window_ctrl_icons(self):
        for btn in [self.min_btn, self.max_btn, self.close_btn]:
            if hasattr(btn, '_svg_data'):
                self._render_icon_btn(btn, btn._svg_data)

    def on_update_available(self, version, notes, download_url):
        self.update_download_url = download_url
        self.update_latest_version = version
        self.update_label.setText(f"🚀 Version {version} is available!")
        self.update_banner.show()

    def start_update_download(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Downloading 0%")
        
        # Spawn download thread
        filename = "Camplife_DataLoader_new.exe"
        self.update_downloader = UpdateDownloader(self.update_download_url, filename)
        self.update_downloader.progress.connect(self.on_download_progress)
        self.update_downloader.finished.connect(self.on_download_finished)
        self.update_downloader.error.connect(self.on_update_error)
        self.update_downloader.start()

    def on_download_progress(self, percent):
        self.update_btn.setText(f"Downloading {percent}%")

    def on_download_finished(self, temp_path):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("Restart to Apply")
        try:
            self.update_btn.clicked.disconnect(self.start_update_download)
        except Exception:
            pass
        self.update_btn.clicked.connect(lambda: self.apply_update_restart(temp_path))
        self.update_label.setText("✅ Download complete! Click to restart and update.")

    def on_update_error(self, err_msg):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("Retry Update")
        self.update_label.setText(f"❌ Update download failed: {err_msg[:40]}...")

    def apply_update_restart(self, temp_path):
        # Path to current running executable
        current_exe = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
        current_exe_abs = os.path.abspath(current_exe)
        
        # Path to apply_update.bat (same directory as config/exe)
        app_dir = os.path.dirname(current_exe_abs)
        bat_path = os.path.join(app_dir, "apply_update.bat")
        
        if not os.path.exists(bat_path):
            # Try running in root workspace folder
            bat_path = os.path.join(os.getcwd(), "apply_update.bat")
            
        if os.path.exists(bat_path):
            pid = os.getpid()
            # Launch batch script detached
            subprocess.Popen([bat_path, str(pid), current_exe_abs, temp_path], 
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            # Exit application
            self.close()
            QApplication.quit()
        else:
            self.update_label.setText("❌ apply_update.bat not found. Restart manually.")
