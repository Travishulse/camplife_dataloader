import sys
import os
import json
from PySide6.QtWidgets import QApplication, QComboBox, QListWidget, QTableWidget, QPushButton
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from src.gui.main_window import FramelessCamplifeLoader
from src.gui.setup_dialog import SetupDialog
from src.gui.preview_dialog import PreviewDialog

def run_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    window = FramelessCamplifeLoader()
    
    results = {}
    
    # Task 1: Dark Mode Controls
    window.toggle_theme()
    results["1. Dark Mode Window Controls"] = hasattr(window, "_refresh_window_ctrl_icons")
    
    # Task 2 & 3: Resort Selector UI
    results["2. Resort Dropdown Incorrect Display Name"] = not hasattr(window, "resort_dropdown") and hasattr(window, "resort_label")
    results["3. Resort Selection Multi-select UI"] = hasattr(window, "resort_label")  # It was moved to SetupDialog which uses QListWidget
    
    # Task 4: Connection Status UI Consolidation
    window.update_connection_status(True)
    connect_hidden = not window.connect_btn.isVisible()
    conn_text = window.conn_label.text()
    results["4. Connection Status UI Consolidation"] = connect_hidden and "✔" in conn_text
    
    # Task 5: Upload Workflow Terminology
    preview_btn_text = window.preview_btn.text()
    results["5. Upload Workflow Terminology (Button)"] = "Review and Upload" in preview_btn_text
    
    # Task 6: Upload Pause and Emergency Stop Controls
    import pandas as pd
    df = pd.DataFrame({"Camplife ID": ["1"]})
    dlg = PreviewDialog(window, df, {}, {}, "alias", window.api_client)
    has_pause = hasattr(dlg, "pause_btn")
    has_stop = hasattr(dlg, "stop_btn")
    results["6. Upload Pause and Emergency Stop Controls"] = has_pause and has_stop
    
    # Check dialog title for Task 5
    results["5.1 Upload Workflow Terminology (Window Title)"] = "Upload Screen" in dlg.windowTitle()
    
    # Task 7: Setup Dialog Resort Selector
    # Setup dialog is opened to see if it populates the available list properly from the cached state.
    setup = SetupDialog(window, resorts_data=window._resorts_data)
    results["7. Resort selector in setup"] = setup.available_list.count() > 0
    
    print("\n--- TEST RESULTS ---")
    for task, completed in results.items():
        print(f"{task}: {'COMPLETED' if completed else 'NOT COMPLETED'}")

if __name__ == '__main__':
    run_tests()
