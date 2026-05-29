import os
import json
import time
from datetime import datetime
from pprint import pformat
import pandas as pd

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QPlainTextEdit, QLabel, QMessageBox,
    QProgressBar, QWidget, QGridLayout
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QColor

from config import LOG_DIR
from src.core.uploader import UploadWorker, validate_dataframe

UTILIZED_FIELDS = [
    "Camplife ID", "Member Number", "Membership Type",
    "Effective From", "Effective To", "Tag", "Note",
]
OVERRIDABLE_FIELDS = {"Membership Type", "Tag", "Note"}

# ---------------- Response Dialog ----------------
class ResponseDialog(QDialog):
    def __init__(self, parent, row_index, log_entry):
        super().__init__(parent)
        self.setWindowTitle(f"Row {row_index} - Request / Response Log")
        self.resize(1000, 700)
        layout = QVBoxLayout(self)

        info_label = QLabel(f"Row: {row_index}")
        layout.addWidget(info_label)

        # Multi-line read-only text area
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        # Pretty format the log entry with URL, method, headers (sans auth), request, response
        display_lines = []
        display_lines.append(f"Log generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")
        for k in ("membership", "note", "tag"):
            entry = log_entry.get(k)
            display_lines.append(f"=== {k.upper()} ===")
            if not entry:
                display_lines.append("Not attempted / skipped.\n")
                continue
            method = entry.get("method", "PUT")
            url = entry.get("url")
            headers = entry.get("headers") or {}
            headers_no_auth = {hk: hv for hk, hv in (headers.items() if isinstance(headers, dict) else []) if hk.lower() != "authorization"}
            req = entry.get("request")
            resp = entry.get("response")
            timestamp = entry.get("timestamp")
            if timestamp:
                display_lines.append(f"TIMESTAMP: {timestamp}")
            if url:
                display_lines.append(f"URL: {url}")
            display_lines.append(f"METHOD: {method}")
            if headers_no_auth:
                display_lines.append("HEADERS (no auth):")
                try:
                    display_lines.append(pformat(headers_no_auth))
                except Exception:
                    display_lines.append(str(headers_no_auth))
            display_lines.append("REQUEST:")
            try:
                display_lines.append(pformat(req))
            except Exception:
                display_lines.append(str(req))
            display_lines.append("\nRESPONSE:")
            if resp is None:
                display_lines.append("No response (exception occurred).")
            else:
                try:
                    display_lines.append(f"HTTP {resp.get('status_code')}")
                    if resp.get("json"):
                        display_lines.append(pformat(resp["json"]))
                    else:
                        txt = resp.get("text", "")
                        if txt and len(txt) > 4000:
                            display_lines.append(txt[:4000] + "\n\n...truncated...")
                        else:
                            display_lines.append(txt)
                except Exception:
                    display_lines.append(str(resp))
            display_lines.append("\n")

        self.text.setPlainText("\n".join(display_lines))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

# ---------------- Preview Dialog ----------------
class PreviewDialog(QDialog):
    """
    Clean PreviewDialog that uses UploadWorker to
    perform uploads in a separate thread and update the table row-by-row.
    """
    def __init__(self, parent, df, column_map, top_fields, cg_alias, api_client):
        super().__init__(parent)
        self.setWindowTitle("Upload Screen")
        self.resize(1200, 700)
        self.df = df.copy().reset_index(drop=True)
        self.column_map = column_map.copy()
        self.top_fields = top_fields.copy()
        self.cg_alias = cg_alias
        self.api_client = api_client
        self.parent_status_signal = getattr(parent, "update_status", None)

        self.upload_logs = {}  # per-row logs
        self.error_counter = {}

        layout = QVBoxLayout(self)

        # Build display fields: only show utilized fields that are mapped or have an override
        self.display_fields = []
        self.display_headers = []
        for field in UTILIZED_FIELDS:
            has_override = field in self.top_fields
            has_mapping = self.column_map.get(field) not in (None, "N/A", "")
            if has_override or has_mapping:
                self.display_fields.append(field)
                header = field + (" (Override)" if has_override else "")
                self.display_headers.append(header)

        self.membership_col_index = len(self.display_fields)
        self.tag_col_index = len(self.display_fields) + 1
        self.note_col_index = len(self.display_fields) + 2

        # Table: display fields + Membership + Tag + Note
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.display_fields) + 3)
        self.table.setHorizontalHeaderLabels(self.display_headers + ["Membership", "Tag", "Note"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setRowCount(len(self.df))

        for r in range(len(self.df)):
            for c, field in enumerate(self.display_fields):
                if field in self.top_fields:
                    cell_value = str(self.top_fields[field])
                else:
                    col_name = self.column_map.get(field)
                    val = self.df.iloc[r][col_name]
                    cell_value = "" if pd.isna(val) else str(val)
                self.table.setItem(r, c, QTableWidgetItem(cell_value))
            # initially blank membership/tag/note
            self.table.setItem(r, self.membership_col_index, QTableWidgetItem(""))
            self.table.setItem(r, self.tag_col_index, QTableWidgetItem(""))
            self.table.setItem(r, self.note_col_index, QTableWidgetItem(""))

        self.table.setToolTip("Click a row after upload to view the request/response details.")
        layout.addWidget(self.table)

        # Progress bar section (initially hidden)
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 0)

        self.status_label = QLabel("Starting upload...")
        progress_layout.addWidget(self.status_label)

        self.eta_label = QLabel("ETA: calculating...")
        self.eta_label.setStyleSheet("font-weight: bold;")
        progress_layout.addWidget(self.eta_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.df))
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # Response counter grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(2)
        progress_layout.addWidget(self.grid_container)

        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)

        btn_row = QHBoxLayout()
        self.upload_btn = QPushButton("Start Upload")
        self.upload_btn.clicked.connect(self.start_upload)
        self.upload_btn.setToolTip("Perform API calls for each row (Membership, Note, Tag).")
        btn_row.addWidget(self.upload_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setToolTip("Pause upload after current row completes.")
        btn_row.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("Emergency Stop")
        self.stop_btn.clicked.connect(self.emergency_stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #c23a3a; color: white;")
        self.stop_btn.setToolTip("Immediately stop upload and save partial results.")
        btn_row.addWidget(self.stop_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        # connect cell click
        self.table.cellClicked.connect(self.on_cell_clicked)

        # Keep references to worker so GC doesn't kill it
        self._worker = None
        self._status_counts = {}
        self._active_row = -1
        self._is_paused = False

    @Slot(int)
    def on_cell_clicked(self, row, col):
        log_entry = self.upload_logs.get(row)
        if log_entry:
            dlg = ResponseDialog(self, row, log_entry)
            dlg.exec()

    @Slot(int, int)
    def on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Uploading row {current} of {total}")

        if current == 0:
            self.eta_label.setText("ETA: calculating...")
            return

        elapsed = time.time() - self._start_time
        rate = elapsed / current
        remaining = (total - current) * rate

        mins, secs = divmod(int(remaining), 60)
        hrs, mins = divmod(mins, 60)

        if hrs > 0:
            eta_text = f"ETA: {hrs}h {mins}m {secs}s"
        elif mins > 0:
            eta_text = f"ETA: {mins}m {secs}s"
        else:
            eta_text = f"ETA: {secs}s"

        self.eta_label.setText(eta_text)

    def toggle_pause(self):
        if self._is_paused:
            self._is_paused = False
            self.pause_btn.setText("Pause")
            if self._worker:
                self._worker.request_resume()
        else:
            self._is_paused = True
            self.pause_btn.setText("Resume")
            if self._worker:
                self._worker.request_pause()

    def emergency_stop(self):
        if self._worker:
            self._worker.request_cancel()
            self.stop_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.status_label.setText("Emergency stop requested — finishing current request...")

    @Slot()
    def _on_worker_paused(self):
        self.pause_btn.setText("Resume")

    @Slot()
    def _on_worker_resumed(self):
        self.pause_btn.setText("Pause")

    def record_status(self, status_code):
        status_str = str(status_code)
        if status_str not in self._status_counts:
            self._status_counts[status_str] = 0
        self._status_counts[status_str] += 1
        self._refresh_status_grid()

    def _refresh_status_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row = 0
        for status, count in self._status_counts.items():
            if count == 0:
                continue
            color = self._get_status_color(status)

            status_label = QLabel(status)
            status_label.setStyleSheet(f"background-color: {color}; color: white; padding: 2px;")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setFixedWidth(60)
            self.grid_layout.addWidget(status_label, row, 0)

            count_label = QLabel(str(count))
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setFixedWidth(40)
            self.grid_layout.addWidget(count_label, row, 1)

            row += 1

    def _get_status_color(self, status_code):
        try:
            code = int(status_code)
            if 200 <= code < 300:
                return "#5a8f69"
            elif 300 <= code < 400:
                return "#c27a3a"
            elif 400 <= code:
                return "#c23a3a"
        except ValueError:
            return "#c27a3a"

    def start_upload(self):
        # Validate rows before upload
        invalid_rows = validate_dataframe(self.df, self.column_map, self.top_fields)

        if invalid_rows:
            # Highlight invalid rows in red
            invalid_row_nums = set(row_info["row"] for row_info in invalid_rows)
            for row_num in invalid_row_nums:
                for col_idx in range(self.table.columnCount()):
                    item = self.table.item(row_num, col_idx)
                    if item:
                        item.setBackground(QColor("#FFE0E0"))

            # Build warning message
            msg_lines = ["The following rows have missing required fields:\n"]
            for row_info in invalid_rows:
                row_num = row_info["row"]
                issues = row_info["issues"]
                msg_lines.append(f"  Row {row_num + 1}: {', '.join(issues)}")

            msg_text = "\n".join(msg_lines) + "\n\nProceed with upload anyway?"

            reply = QMessageBox.warning(
                self,
                "Validation Warning",
                msg_text,
                QMessageBox.Yes | QMessageBox.Cancel
            )

            if reply != QMessageBox.Yes:
                self.upload_btn.setEnabled(True)
                return

        self.upload_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self._is_paused = False
        self.pause_btn.setText("Pause")
        self._status_counts = {}
        self._start_time = time.time()

        total_rows = len(self.df)
        self._worker = UploadWorker(self.df, self.column_map, self.top_fields, self.cg_alias, self.api_client)

        # wire signals
        self._worker.progress.connect(self.on_progress)
        self._worker.row_finished.connect(self._on_row_finished)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        if hasattr(self._worker, 'paused'):
            self._worker.paused.connect(self._on_worker_paused)
        if hasattr(self._worker, 'resumed'):
            self._worker.resumed.connect(self._on_worker_resumed)

        # show progress container
        self.progress_container.setVisible(True)

        # start the worker thread
        self._worker.start()

    @Slot(int, dict)
    def _on_row_finished(self, row_index, log_entry):
        try:
            self.upload_logs[row_index] = log_entry

            mem_resp_status = None
            note_status = None
            tag_status = None

            if log_entry.get("membership") and isinstance(log_entry["membership"], dict):
                mem_resp_status = log_entry["membership"].get("response", {}).get("status_code")
            if log_entry.get("note") and isinstance(log_entry["note"], dict):
                note_status = log_entry["note"].get("response", {}).get("status_code")
            if log_entry.get("tag") and isinstance(log_entry["tag"], dict):
                tag_status = log_entry["tag"].get("response", {}).get("status_code")

            # Record status codes in response counter grid
            for code in (mem_resp_status, note_status, tag_status):
                if code is not None:
                    self.record_status(code)

            # Populate Membership column
            mem_display = "✅" if (mem_resp_status in (200, 201)) else ("❌" if mem_resp_status else "—")
            if mem_resp_status:
                mem_display += f" {mem_resp_status}"
            self.table.setItem(row_index, self.membership_col_index, QTableWidgetItem(mem_display))

            # Populate Tag column
            tag_display = "✅" if (tag_status in (200, 201)) else ("❌" if tag_status else "—")
            if tag_status:
                tag_display += f" {tag_status}"
            self.table.setItem(row_index, self.tag_col_index, QTableWidgetItem(tag_display))

            # Populate Note column
            note_display = "✅" if (note_status in (200, 201)) else ("❌" if note_status else "—")
            if note_status:
                note_display += f" {note_status}"
            self.table.setItem(row_index, self.note_col_index, QTableWidgetItem(note_display))

            # Auto-scroll to current row
            self.table.scrollTo(self.table.model().index(row_index, 0))

            # Remove highlight from previous active row
            if self._active_row >= 0 and self._active_row != row_index:
                for col_idx in range(self.table.columnCount()):
                    item = self.table.item(self._active_row, col_idx)
                    if item:
                        item.setBackground(QColor(Qt.transparent))

            for code in (mem_resp_status, note_status, tag_status):
                if code and code not in (200, 201):
                    self.error_counter[code] = self.error_counter.get(code, 0) + 1
            error_summary = ", ".join(f"{k}:{v}" for k, v in self.error_counter.items())

            if self.parent_status_signal and error_summary:
                self.parent_status_signal(f"Errors: {error_summary}", 5000)

        except Exception as e:
            self.table.setItem(row_index, self.membership_col_index, QTableWidgetItem("❌"))
            self.table.setItem(row_index, self.tag_col_index, QTableWidgetItem("❌"))
            self.table.setItem(row_index, self.note_col_index, QTableWidgetItem(f"Error: {e}"))
            self.upload_logs[row_index] = {"membership": None, "note": None, "tag": None, "exception": str(e)}

    @Slot()
    def _on_worker_finished(self):
        self.save_upload_log()
        self.upload_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self._is_paused = False
        self.status_label.setText("Upload finished")
        if self.parent_status_signal:
            self.parent_status_signal("Upload finished", 4000)

    @Slot(str)
    def _on_worker_error(self, errmsg):
        if self.parent_status_signal:
            self.parent_status_signal(f"Upload worker error: {errmsg}", 7000)
        self.upload_btn.setEnabled(True)

    def save_upload_log(self):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            log_rows = []
            for row_index, entry in self.upload_logs.items():
                mem = entry.get("membership", {})
                mem_req = mem.get("request") if isinstance(mem, dict) else None
                mem_resp = mem.get("response") if isinstance(mem, dict) else None

                note = entry.get("note", {})
                note_req = note.get("request") if isinstance(note, dict) else None
                note_resp = note.get("response") if isinstance(note, dict) else None

                tag = entry.get("tag", {})
                tag_req = tag.get("request") if isinstance(tag, dict) else None
                tag_resp = tag.get("response") if isinstance(tag, dict) else None

                log_rows.append({
                    "Row Index": row_index,
                    "Membership URL": mem.get("url") if isinstance(mem, dict) else None,
                    "Membership Method": mem.get("method") if isinstance(mem, dict) else None,
                    "Membership Request": str(mem_req) if mem_req else None,
                    "Membership Status": mem_resp.get("status_code") if isinstance(mem_resp, dict) else None,
                    "Membership JSON": str(mem_resp.get("json")) if isinstance(mem_resp, dict) else None,
                    "Membership Text": str(mem_resp.get("text")) if isinstance(mem_resp, dict) else None,
                    "Note URL": note.get("url") if isinstance(note, dict) else None,
                    "Note Method": note.get("method") if isinstance(note, dict) else None,
                    "Note Request": str(note_req) if note_req else None,
                    "Note Status": note_resp.get("status_code") if isinstance(note_resp, dict) else None,
                    "Note JSON": str(note_resp.get("json")) if isinstance(note_resp, dict) else None,
                    "Note Text": str(note_resp.get("text")) if isinstance(note_resp, dict) else None,
                    "Tag URL": tag.get("url") if isinstance(tag, dict) else None,
                    "Tag Method": tag.get("method") if isinstance(tag, dict) else None,
                    "Tag Request": str(tag_req) if tag_req else None,
                    "Tag Status": tag_resp.get("status_code") if isinstance(tag_resp, dict) else None,
                    "Tag JSON": str(tag_resp.get("json")) if isinstance(tag_resp, dict) else None,
                    "Tag Text": str(tag_resp.get("text")) if isinstance(tag_resp, dict) else None,
                    "Exception": entry.get("exception"),
                })

            if not log_rows:
                return

            df = pd.DataFrame(log_rows)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"Camplife_Upload_Log_{timestamp}.xlsx"
            filepath = os.path.join(LOG_DIR, filename)
            df.to_excel(filepath, index=False)

            if self.parent_status_signal:
                self.parent_status_signal(f"Upload log saved: {filename}", 7000)

        except Exception as exc:
            try:
                emergency_name = f"Camplife_Upload_Log_ERROR_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
                emergency_path = os.path.join(LOG_DIR, emergency_name)
                with open(emergency_path, "w", encoding="utf-8") as f:
                    f.write("FAILED TO WRITE EXCEL LOG\n")
                    f.write(f"Error: {str(exc)}\n\n")
                    f.write("RAW LOG DATA:\n")
                    f.write(json.dumps(self.upload_logs, indent=2, default=str))
            except Exception:
                pass
