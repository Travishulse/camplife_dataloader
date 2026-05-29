import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd
import random
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication

# Ensure workspace source code is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.gui.main_window import FramelessCamplifeLoader
from src.gui.preview_dialog import PreviewDialog

class TestAppWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a QApplication instance for QWidget testing
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
            
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def generate_test_data(self, row_count):
        """Helper to generate clean mock dataframe with error rate."""
        membership_types = ["Standard", "Premium", "VIP"]
        tags = ["Tag1", "Tag2"]
        base_date = datetime(2026, 1, 1)

        data = {
            "Camplife ID": [],
            "Member Number": [],
            "Membership Type": [],
            "Effective From": [],
            "Effective To": [],
            "Tag": [],
            "Note": []
        }

        for i in range(row_count):
            data["Camplife ID"].append(str(5000000 + i))
            data["Member Number"].append(str(10000 + i))
            data["Membership Type"].append(random.choice(membership_types))
            data["Effective From"].append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            data["Effective To"].append((base_date + timedelta(days=365+i)).strftime("%Y-%m-%d"))
            data["Tag"].append(random.choice(tags))
            data["Note"].append(f"Test note - {i}")

        return pd.DataFrame(data)

    def test_file_ingestion_and_auto_mapping(self):
        # 1. Generate local data and write to temp CSV
        df = self.generate_test_data(10)
        temp_csv_path = os.path.join(self.temp_dir, "temp_data_10.csv")
        df.to_csv(temp_csv_path, index=False)
        
        # 2. Load into main loader window
        window = FramelessCamplifeLoader()
        window.loaded_df = df
        window.populate_column_dropdowns()
        window.auto_select_matching_columns()
        
        # 3. Assert auto-mapping worked correctly
        self.assertEqual(window.camplife_id_col.currentText(), "Camplife ID")
        self.assertEqual(window.member_number_col.currentText(), "Member Number")
        self.assertEqual(window.membership_col.currentText(), "Membership Type")
        self.assertEqual(window.effective_from_col.currentText(), "Effective From")
        
        # Clean up Qt widgets
        window.close()
        window.deleteLater()

    def test_preview_dialog_and_logging(self):
        df = self.generate_test_data(5)
        window = FramelessCamplifeLoader()
        
        column_map = {
            "Camplife ID": "Camplife ID",
            "Member Number": "Member Number",
            "Membership Type": "Membership Type",
            "Effective From": "Effective From",
            "Effective To": "Effective To",
            "Tag": "Tag",
            "Note": "Note"
        }
        
        # Instantiation check
        preview = PreviewDialog(window, df, column_map, {}, "test_alias", window.api_client)
        self.assertEqual(preview.table.rowCount(), 5)
        
        # Test log formatting and Excel output redirection
        preview.upload_logs = {
            0: {"membership": {"response": {"status_code": 200}}, "tag": {"response": {"status_code": 201}}, "note": {"response": {"status_code": 200}}},
            1: {"membership": {"response": {"status_code": 200}}, "tag": None, "note": {"response": {"status_code": 400}}}
        }
        
        # Inject temporary log path override
        import src.gui.preview_dialog
        original_log_dir = src.gui.preview_dialog.LOG_DIR
        src.gui.preview_dialog.LOG_DIR = self.temp_dir
        
        try:
            preview.save_upload_log()
            # Verify Excel log was generated in temp directory
            log_files = [f for f in os.listdir(self.temp_dir) if f.startswith("Camplife_Upload_Log_") and f.endswith(".xlsx")]
            self.assertEqual(len(log_files), 1)
        finally:
            src.gui.preview_dialog.LOG_DIR = original_log_dir
            
        # Clean up Qt widgets
        preview.close()
        preview.deleteLater()
        window.close()
        window.deleteLater()

if __name__ == "__main__":
    unittest.main()
