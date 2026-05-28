import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from config import CONFIG_FILE, CACHE_FILE
from src.core.security import encrypt_secret, decrypt_secret
from src.api.auth_utils import perform_hmac_auth
from src.api.workers import FetchStaticDataWorker


class TestConnectionWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, api_key, api_secret, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.api_secret = api_secret

    def run(self):
        result = perform_hmac_auth(self.api_key, self.api_secret)
        if result["success"]:
            self.finished.emit(True, "Connected successfully")
        else:
            self.finished.emit(False, result["error"])


class SetupDialog(QDialog):
    def __init__(self, parent=None, resorts_data=None):
        super().__init__(parent)
        self.setWindowTitle("Setup API Credentials & Resort Selection")
        self.setMinimumWidth(620)
        self.setMinimumHeight(480)
        self.resorts_data = resorts_data or []
        self.selected_resort_alias = None
        self._test_worker = None
        self._fetch_worker = None

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # API Key
        layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        layout.addWidget(self.api_key_input)

        # API Secret
        layout.addWidget(QLabel("API Secret:"))
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_secret_input)

        # Test Connection button + status label
        test_row = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setToolTip("Verify API credentials are valid")
        self.test_btn.clicked.connect(self._test_connection)
        test_row.addWidget(self.test_btn)
        self.test_status_label = QLabel("")
        test_row.addWidget(self.test_status_label)
        test_row.addStretch()
        layout.addLayout(test_row)

        # Resort dual-panel selector
        layout.addWidget(QLabel("Default Resort:"))
        resort_selector = QHBoxLayout()
        resort_selector.setSpacing(6)

        # Left panel — available resorts
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("Available"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.available_list.setToolTip("All resorts from API")
        self.available_list.itemDoubleClicked.connect(self._move_to_selected)
        left_col.addWidget(self.available_list)
        resort_selector.addLayout(left_col)

        # Arrow buttons (centered vertically)
        btn_col = QVBoxLayout()
        btn_col.addStretch()
        self.add_btn = QPushButton("→")
        self.add_btn.setFixedWidth(32)
        self.add_btn.setToolTip("Set as default resort")
        self.add_btn.clicked.connect(self._move_to_selected)
        self.remove_btn = QPushButton("←")
        self.remove_btn.setFixedWidth(32)
        self.remove_btn.setToolTip("Remove default resort")
        self.remove_btn.clicked.connect(self._move_to_available)
        btn_col.addWidget(self.add_btn)
        btn_col.addWidget(self.remove_btn)
        btn_col.addStretch()
        resort_selector.addLayout(btn_col)

        # Right panel — selected resort (max 1)
        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("Selected (max 1)"))
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.selected_list.setToolTip("The default resort used for uploads")
        self.selected_list.itemDoubleClicked.connect(self._move_to_available)
        right_col.addWidget(self.selected_list)
        resort_selector.addLayout(right_col)

        layout.addLayout(resort_selector)

        # Populate resorts if available
        if self.resorts_data:
            self._populate_resorts()

        # Refresh button + status label
        refresh_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Resort & Membership Data")
        self.refresh_btn.setToolTip("Re-fetch resort and membership data from the API and update the cache")
        self.refresh_btn.clicked.connect(self._refresh_data)
        refresh_row.addWidget(self.refresh_btn)
        self.refresh_status_label = QLabel("")
        refresh_row.addWidget(self.refresh_status_label)
        refresh_row.addStretch()
        layout.addLayout(refresh_row)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_config)
        save_button.setToolTip("Save API Key, Secret, and Resort selection")
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.load_config()

    def _populate_resorts(self):
        """Fill the available list from resorts_data, keeping any already-selected resort in place."""
        selected_alias = self._get_selected_alias()

        self.available_list.clear()
        self.selected_list.clear()

        for r in self.resorts_data:
            display_name = r.get("propertyName") or r.get("name") or r.get("organizationName")
            alias = r.get("alias")
            if not display_name or not alias:
                continue
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, alias)
            if alias == selected_alias:
                self.selected_list.addItem(item)
            else:
                self.available_list.addItem(item)

    def _get_selected_alias(self):
        if self.selected_list.count() > 0:
            return self.selected_list.item(0).data(Qt.UserRole)
        return self.selected_resort_alias or ""

    def _move_to_selected(self):
        item = self.available_list.currentItem()
        if item is None:
            return
        if self.selected_list.count() >= 1:
            # Swap: push the current selection back to available first
            existing = self.selected_list.takeItem(0)
            self.available_list.addItem(existing)
        row = self.available_list.row(item)
        self.available_list.takeItem(row)
        self.selected_list.addItem(item)

    def _move_to_available(self):
        item = self.selected_list.currentItem()
        if item is None:
            return
        row = self.selected_list.row(item)
        self.selected_list.takeItem(row)
        self.available_list.addItem(item)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_key_input.setText(data.get("api_key", ""))
                    raw_secret = data.get("api_secret", "")
                    self.api_secret_input.setText(decrypt_secret(raw_secret))
                    self.selected_resort_alias = data.get("resort_alias", "")
            except Exception:
                pass

    def save_config(self):
        if not self.api_key_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "API Key cannot be empty.")
            return

        if not self.api_secret_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "API Secret cannot be empty.")
            return

        if self.available_list.count() > 0 and self.selected_list.count() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a default resort.")
            return

        resort_alias = ""
        if self.selected_list.count() > 0:
            resort_alias = self.selected_list.item(0).data(Qt.UserRole)

        data = {
            "api_key": self.api_key_input.text(),
            "api_secret": encrypt_secret(self.api_secret_input.text()),
            "resort_alias": resort_alias
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

        self.selected_resort_alias = resort_alias
        self.accept()

    def _test_connection(self):
        key = self.api_key_input.text().strip()
        secret = self.api_secret_input.text().strip()
        if not key or not secret:
            self.test_status_label.setText("⚠️ Enter key and secret first")
            return

        self.test_btn.setEnabled(False)
        self.test_status_label.setText("Testing...")
        self._test_worker = TestConnectionWorker(key, secret, self)
        self._test_worker.finished.connect(self._on_test_finished)
        self._test_worker.start()

    def _on_test_finished(self, success, message):
        self.test_btn.setEnabled(True)
        if success:
            self.test_status_label.setText(f"✅ {message}")
        else:
            self.test_status_label.setText(f"❌ {message}")

    def _refresh_data(self):
        key = self.api_key_input.text().strip()
        secret = self.api_secret_input.text().strip()
        if not key or not secret:
            self.refresh_status_label.setText("⚠️ Enter key and secret first")
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_status_label.setText("Fetching...")
        self._fetch_worker = FetchStaticDataWorker(key, secret, self)
        self._fetch_worker.resorts_loaded.connect(self._on_resorts_refreshed)
        self._fetch_worker.memberships_loaded.connect(self._on_memberships_refreshed)
        self._fetch_worker.finished.connect(self._on_refresh_finished)
        self._fetch_worker.start()

    def _on_resorts_refreshed(self, resorts):
        self.resorts_data = resorts
        self._populate_resorts()

    def _on_memberships_refreshed(self, memberships):
        self._refreshed_memberships = memberships

    def _on_refresh_finished(self, success, message):
        self.refresh_btn.setEnabled(True)
        if success:
            self.refresh_status_label.setText(f"✅ {message}")
            try:
                memberships = getattr(self, "_refreshed_memberships", [])
                cache = {"resorts": self.resorts_data, "memberships": memberships}
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except Exception:
                pass
        else:
            self.refresh_status_label.setText(f"❌ {message}")
