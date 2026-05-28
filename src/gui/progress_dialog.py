import time
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget, QGridLayout, QPushButton
from PySide6.QtCore import Signal, Slot, Qt

class UploadProgressDialog(QDialog):
    """
    Modal progress dialog with:
    - Standard progress bar
    - Dynamic response status grid (color-coded)
    - Live ETA calculation
    - Cancel support
    """

    cancel_requested = Signal()

    def __init__(self, total, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Uploading — Progress")
        self.setMinimumWidth(520)

        self._total = total
        self._status_counts = {}
        self._start_time = time.time()

        layout = QVBoxLayout(self)

        # ---------- STATUS TEXT ----------
        self.status_label = QLabel("Starting upload...")
        layout.addWidget(self.status_label)

        # ---------- ETA LABEL ----------
        self.eta_label = QLabel("ETA: calculating...")
        self.eta_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.eta_label)

        # ---------- PROGRESS BAR ----------
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # ---------- STATUS GRID ----------
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(2)
        layout.addWidget(self.grid_container)

        # ---------- CANCEL BUTTON ----------
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    # =========================================================
    # STATUS GRID
    # =========================================================

    def record_status(self, status_code):
        """Record a response status and update the status grid"""
        status_str = str(status_code)

        if status_str not in self._status_counts:
            self._status_counts[status_str] = 0
        self._status_counts[status_str] += 1

        self._refresh_status_grid()

    def _get_status_color(self, status_code):
        """Return color based on status code"""
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

    def _refresh_status_grid(self):
        """Redraw the status grid, only showing statuses with count > 0"""
        # Clear grid
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
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setFixedWidth(60)
            self.grid_layout.addWidget(status_label, row, 0)

            count_label = QLabel(str(count))
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_label.setFixedWidth(40)
            self.grid_layout.addWidget(count_label, row, 1)

            row += 1

    # =========================================================
    # PROGRESS + ETA
    # =========================================================

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

    # =========================================================
    # CANCEL
    # =========================================================

    def _on_cancel(self):
        self.cancel_requested.emit()
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancel requested — finishing current request...")
