import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import random
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Import the modularized components
from src.gui.main_window import FramelessCamplifeLoader
from src.gui.preview_dialog import PreviewDialog

# Mock main_app for compatibility with the rest of the script
class MainAppMock:
    pass
main_app = MainAppMock()
main_app.FramelessCamplifeLoader = FramelessCamplifeLoader
main_app.PreviewDialog = PreviewDialog

app = QApplication(sys.argv)

def generate_test_data(row_count, error_percentage=0.10):
    """Generate test data with specified row count and error percentage (max 10%)."""
    error_percentage = min(error_percentage, 0.10)
    num_errors = max(1, int(row_count * error_percentage))
    error_rows = set(random.sample(range(row_count), num_errors))

    membership_types = ["Standard", "Premium", "VIP", "Family", "Youth"]
    tags = ["Tag1", "Tag2", "Tag3", "Tag4", "Tag5"]
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
        # Introduce errors in 10% of rows
        if i in error_rows:
            error_type = random.choice(["missing_id", "missing_number", "invalid_date", "missing_membership"])
            if error_type == "missing_id":
                data["Camplife ID"].append("")
                data["Member Number"].append(str(10000 + i))
                data["Membership Type"].append(random.choice(membership_types))
                data["Effective From"].append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
                data["Effective To"].append((base_date + timedelta(days=365+i)).strftime("%Y-%m-%d"))
                data["Tag"].append(random.choice(tags))
                data["Note"].append(f"Test note with error - {i}")
            elif error_type == "missing_number":
                data["Camplife ID"].append(str(5000000 + i))
                data["Member Number"].append("")
                data["Membership Type"].append(random.choice(membership_types))
                data["Effective From"].append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
                data["Effective To"].append((base_date + timedelta(days=365+i)).strftime("%Y-%m-%d"))
                data["Tag"].append(random.choice(tags))
                data["Note"].append(f"Test note with error - {i}")
            elif error_type == "invalid_date":
                data["Camplife ID"].append(str(5000000 + i))
                data["Member Number"].append(str(10000 + i))
                data["Membership Type"].append(random.choice(membership_types))
                data["Effective From"].append("")
                data["Effective To"].append((base_date + timedelta(days=365+i)).strftime("%Y-%m-%d"))
                data["Tag"].append(random.choice(tags))
                data["Note"].append(f"Test note with error - {i}")
            else:  # missing_membership
                data["Camplife ID"].append(str(5000000 + i))
                data["Member Number"].append(str(10000 + i))
                data["Membership Type"].append("")
                data["Effective From"].append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
                data["Effective To"].append((base_date + timedelta(days=365+i)).strftime("%Y-%m-%d"))
                data["Tag"].append(random.choice(tags))
                data["Note"].append(f"Test note with error - {i}")
        else:
            data["Camplife ID"].append(str(5000000 + i))
            data["Member Number"].append(str(10000 + i))
            data["Membership Type"].append(random.choice(membership_types))
            data["Effective From"].append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            data["Effective To"].append((base_date + timedelta(days=365+i)).strftime("%Y-%m-%d"))
            data["Tag"].append(random.choice(tags))
            data["Note"].append(f"Test note - {i}")

    return pd.DataFrame(data)

def test_templates():
    """Generate 3 test templates: 10, 100, 1000 accounts."""
    test_dir = os.path.dirname(__file__)

    print("Generating test templates with max 10% errors per template...")

    # Template 1: 10 accounts (1 error)
    df_10 = generate_test_data(10, 0.10)
    path_10 = os.path.join(test_dir, "test_data_10.csv")
    df_10.to_csv(path_10, index=False)
    print(f"[OK] Template 1: 10 accounts created at {path_10}")

    # Template 2: 100 accounts (10 errors)
    df_100 = generate_test_data(100, 0.10)
    path_100 = os.path.join(test_dir, "test_data_100.csv")
    df_100.to_csv(path_100, index=False)
    print(f"[OK] Template 2: 100 accounts created at {path_100}")

    # Template 3: 1000 accounts (100 errors)
    df_1000 = generate_test_data(1000, 0.10)
    path_1000 = os.path.join(test_dir, "test_data_1000.csv")
    df_1000.to_csv(path_1000, index=False)
    print(f"[OK] Template 3: 1000 accounts created at {path_1000}")

    return df_10, df_100, df_1000

try:
    # Generate test templates
    df_10, df_100, df_1000 = test_templates()

    window = main_app.FramelessCamplifeLoader()

    # Test file load and mapping with 10-account template
    print("\nTesting column mapping with 10-account template...")
    window.loaded_df = df_10
    window.populate_column_dropdowns()
    window.auto_select_matching_columns()

    print("[OK] Mapping test passed.")
    print(f"     Camplife ID mapping: {window.camplife_id_col.currentText()}")

    # Manually instantiate PreviewDialog to test it
    column_map = {
        "Camplife ID": window.camplife_id_col.currentText(),
        "Member Number": window.member_number_col.currentText(),
        "Membership Type": window.membership_col.currentText(),
        "Effective From": window.effective_from_col.currentText(),
        "Effective To": window.effective_to_col.currentText(),
        "Tag": window.tag_col.currentText(),
        "Note": window.note_col.currentText()
    }
    top_fields = {}
    cg_alias = "test_alias"
    preview = main_app.PreviewDialog(window, df_10, column_map, top_fields, cg_alias, window.api_client)
    print("[OK] Preview dialog instantiated.")

    # Try saving a log to see if it works without errors
    preview.upload_logs = {
        0: {"membership": {"response": {"status_code": 200}}, "tag": {"response": {"status_code": 201}}, "note": {"response": {"status_code": 200}}},
        1: {"membership": {"response": {"status_code": 200}}, "tag": None, "note": {"response": {"status_code": 400}}}
    }
    preview.save_upload_log()
    print("[OK] Upload log saved.")

    print("\n[SUCCESS] All tests passed without blocking.")

except Exception as e:
    import traceback
    print(f"\n[ERROR] Test failed with error:")
    traceback.print_exc()

# QTimer.singleShot(100, app.quit)
# app.exec()
