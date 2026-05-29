import sys
import os
import unittest
import zipfile
import io
import urllib.request
import tempfile
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

# Ensure workspace source code is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Temporarily mock version to trigger the update check
import config
config.VERSION = "1.2.2"  # Simulating that we are running 1.2.2 so it detects 1.2.3 from GitHub

from src.gui.main_window import FramelessCamplifeLoader

def safe_print(text):
    """Safely print text on Windows consoles by encoding/decoding as ascii (ignoring errors)"""
    print(text.encode('ascii', errors='ignore').decode('ascii'))

class TestInteractiveUpdater(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a single QApplication instance for all tests
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_interactive_update_flow(self):
        safe_print("\n=== STARTING INTERACTIVE GUI QTEST (WITH LOCAL ZIP MOCK) ===")
        
        # Proactively clean up any stale temp ZIP from previous runs to prevent file corruption/size mismatches
        temp_path = os.path.join(tempfile.gettempdir(), "Camplife_DataLoader_new.zip")
        if os.path.exists(temp_path):
            safe_print(f"Cleaning stale temp ZIP file: {temp_path}")
            try:
                os.remove(temp_path)
                safe_print("[OK] Successfully deleted stale temp ZIP.")
            except Exception as e:
                safe_print(f"[WARNING] Could not delete stale temp ZIP: {e}. It might be locked by another process.")

        # 1. Create a tiny valid mock ZIP in memory to bypass the slow 75MB network download
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add a mock executable starting with Windows MZ header
            zip_file.writestr('Camplife DataLoader/Camplife DataLoader.exe', b'MZ_mock_executable_pe_header_data_here')
            zip_file.writestr('Camplife DataLoader/_internal/apply_update.bat', b'@echo off\necho Mock Update Swapper!')
            zip_file.writestr('Camplife DataLoader/_internal/app_icon.png', b'mock_png_data')
        
        zip_data = zip_buffer.getvalue()
        safe_print(f"[OK] Created mock update zip payload ({len(zip_data)} bytes)")

        # Keep track of test assertions
        self.update_detected = False
        self.download_started = False
        self.download_completed = False
        self.subprocess_launched = False
        self.launched_args = []

        # Mock subprocess.Popen so we don't actually run the updater batch script during the test
        def mock_popen(args, **kwargs):
            self.subprocess_launched = True
            self.launched_args = args
            safe_print(f"[OK] Blocked real batch script execution. Intercepted subprocess.Popen args: {args}")
            # Return a mock process
            proc = MagicMock()
            proc.pid = 99999
            return proc

        # Mock urllib.request.urlopen response to serve our in-memory ZIP when downloader calls it
        class MockUrllibResponse:
            def __init__(self, data):
                self.data_io = io.BytesIO(data)
                self.headers = {'Content-Length': str(len(data))}
            
            def info(self):
                return self.headers
            
            def read(self, amt=None):
                return self.data_io.read(amt)
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        # Mock both zip download and GitHub API check requests to prevent network dependencies in sandboxes.
        original_urlopen = urllib.request.urlopen
        
        def mock_urlopen(req, *args, **kwargs):
            url_str = req.full_url if hasattr(req, 'full_url') else str(req)
            if "releases/download" in url_str or "zipball" in url_str:
                safe_print(f"[OK] Intercepted update download request for {url_str} - serving mock ZIP payload...")
                return MockUrllibResponse(zip_data)
            elif "api.github.com/repos/" in url_str and "releases/latest" in url_str:
                safe_print(f"[OK] Intercepted update check request for {url_str} - serving mock release JSON...")
                mock_json = b'{"tag_name": "v1.2.3", "body": "Mocked test release notes.", "zipball_url": "https://api.github.com/repos/Travishulse/camplife_dataloader/zipball/v1.2.3", "assets": [{"name": "Camplife_DataLoader.zip", "browser_download_url": "https://github.com/Travishulse/camplife_dataloader/releases/download/v1.2.3/Camplife_DataLoader.zip"}]}'
                return MockUrllibResponse(mock_json)
            return original_urlopen(req, *args, **kwargs)

        # Patch subprocess.Popen and urllib.request.urlopen
        with patch('subprocess.Popen', side_effect=mock_popen), patch('urllib.request.urlopen', side_effect=mock_urlopen):
            
            # Override VERSION inside the main_window module to avoid cached import issues from unittest discovery
            import src.gui.main_window
            src.gui.main_window.VERSION = "1.2.2"
            
            # 2. Instantiate the main window inside the patch context
            window = FramelessCamplifeLoader()
            window.show()

            # Intercept QApplication.quit and window.close so the app doesn't close during our test
            window.close = MagicMock(return_value=True)
            self.app.quit = MagicMock()

            # Step 1: Wait for the background UpdateChecker thread to finish query
            safe_print("Checking update detection...")
            
            # We will use a small loop to process events until the update banner is shown
            for _ in range(100):
                QApplication.processEvents()
                QTest.qWait(50)
                if window.update_banner.isVisible():
                    self.update_detected = True
                    break

            self.assertTrue(self.update_detected, "[FAIL] Update banner was not shown! Check your internet connection or GitHub API.")
            safe_print(f"[OK] Update banner detected! Latest version found: {window.update_latest_version}")
            safe_print(f"[OK] Label Text: '{window.update_label.text()}'")

            # Step 2: Click the 'Update Now' button programmatically using QTest
            safe_print("Simulating human mouse click on 'Update Now' button...")
            self.assertTrue(window.update_btn.isEnabled(), "Update button should be enabled.")
            QTest.mouseClick(window.update_btn, Qt.LeftButton)
            
            # Step 3: Verify download starts and monitor progress
            safe_print("Monitoring download progress...")
            
            for i in range(100):
                QApplication.processEvents()
                QTest.qWait(50)
                btn_text = window.update_btn.text()
                if "Downloading" in btn_text:
                    self.download_started = True
                
                if i % 10 == 0 and self.download_started:
                    safe_print(f"Current progress label: '{btn_text}'")
                    
                if "Restart to Apply" in btn_text or "complete" in window.update_label.text().lower():
                    self.download_completed = True
                    break

            self.assertTrue(self.download_started, "[FAIL] Download progress did not start!")
            self.assertTrue(self.download_completed, "[FAIL] Download did not complete!")
            safe_print(f"[OK] Download completed successfully! Label Text: '{window.update_label.text()}'")

            # Step 4: Click the 'Restart to Apply' button programmatically
            safe_print("Simulating human mouse click on 'Restart to Apply' button...")
            self.assertTrue(window.update_btn.isEnabled(), "Restart button should be enabled.")
            QTest.mouseClick(window.update_btn, Qt.LeftButton)
            
            # Process remaining event loop cycles to trigger click slot
            safe_print("Processing event loop to allow swapper thread to run...")
            for _ in range(20):
                QApplication.processEvents()
                QTest.qWait(50)

            # Debug diagnostics if fails
            safe_print(f"[DIAGNOSTIC] Final Update Label Text: '{window.update_label.text()}'")
            safe_print(f"[DIAGNOSTIC] Current Working Dir apply_update.bat exists: {os.path.exists('apply_update.bat')}")
            safe_print(f"[DIAGNOSTIC] RESOURCE_DIR value: {config.RESOURCE_DIR}")
            safe_print(f"[DIAGNOSTIC] temp_path path: '{temp_path}'")
            if os.path.exists(temp_path):
                safe_print(f"[DIAGNOSTIC] temp_path size: {os.path.getsize(temp_path)}")
                try:
                    with open(temp_path, 'rb') as f:
                        magic = f.read(4)
                    safe_print(f"[DIAGNOSTIC] temp_path magic bytes: {magic}")
                except Exception as e:
                    safe_print(f"[DIAGNOSTIC] failed to read temp_path: {e}")
            else:
                safe_print("[DIAGNOSTIC] temp_path does not exist!")

            # Step 5: Assert that apply_update.bat was launched with correct arguments
            self.assertTrue(self.subprocess_launched, "[FAIL] subprocess.Popen was not called!")
            self.assertTrue(any("apply_update.bat" in arg for arg in self.launched_args), 
                            "[FAIL] Launched arguments do not contain apply_update.bat!")
            
            safe_print(f"[OK] Automated GUI click successfully triggered the swapper process!")
            safe_print(f"[OK] Parameter 1 (PID): {self.launched_args[1]}")
            safe_print(f"[OK] Parameter 2 (Dest Dir): {self.launched_args[2]}")
            safe_print(f"[OK] Parameter 3 (Temp Dir): {self.launched_args[3]}")
            safe_print(f"[OK] Parameter 4 (Exe Name): {self.launched_args[4]}")
            
            # Cleanup window
            window.hide()
            window.deleteLater()
            
            safe_print("\n=== INTERACTIVE GUI QTEST PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    unittest.main()
