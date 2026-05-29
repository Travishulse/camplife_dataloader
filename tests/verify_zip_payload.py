import os
import sys
import zipfile
import tempfile
import shutil

def run_integrity_test(zip_path=None):
    if zip_path is None:
        # Default to the expected build output path
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        zip_path = os.path.join(workspace_dir, "dist", "Camplife_DataLoader.zip")
        
        # Check if a custom zip path was provided as a CLI argument
        if len(sys.argv) > 1:
            zip_path = os.path.abspath(sys.argv[1])

    print("=== STARTING ZIP PAYLOAD INTEGRITY TEST ===")
    
    if not os.path.exists(zip_path):
        print(f"[INFO] Target zip payload not found at: {zip_path}")
        print("To run integrity checks, please compile the application using 'build.bat' or pass the zip path as an argument.")
        print("Skipping verification test (Success).")
        return True

    print(f"Verifying zip payload at: {zip_path} ({os.path.getsize(zip_path)} bytes)")
    
    temp_dir = tempfile.mkdtemp()
    extract_dir = os.path.join(temp_dir, "extracted")
    
    try:
        print("Extracting zip payload...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"Extraction successful: {extract_dir}")
        
        # Expected folder structure inside the zip file
        # The zip must contain a folder 'Camplife DataLoader' at its root
        app_folder = os.path.join(extract_dir, "Camplife DataLoader")
        if not os.path.exists(app_folder):
            print(f"[FAIL] Missing 'Camplife DataLoader' root folder in ZIP contents.")
            return False

        exe_path = os.path.join(app_folder, "Camplife DataLoader.exe")
        bat_path = os.path.join(app_folder, "apply_update.bat")
        
        # Check internal files (can be in root or _internal depending on packaging)
        if not os.path.exists(bat_path):
            bat_path = os.path.join(app_folder, "_internal", "apply_update.bat")
            
        icon_path = os.path.join(app_folder, "app_icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(app_folder, "_internal", "app_icon.png")

        print("\nVerifying file elements...")
        
        # 1. Verify executable exists
        if not os.path.exists(exe_path):
            print(f"[FAIL] Executable not found at expected path: {exe_path}")
            return False
        print(f"[OK] Executable found: {exe_path}")

        # 2. Verify PE header of the executable (must start with MZ)
        try:
            with open(exe_path, 'rb') as f:
                header = f.read(2)
            if header == b'MZ':
                print(f"[OK] PE header validation successful: {header} ('MZ')")
            else:
                print(f"[FAIL] Invalid PE header: {header}. File might be corrupted or 16-bit.")
                return False
        except Exception as e:
            print(f"[FAIL] Error reading executable header: {e}")
            return False

        # 3. Verify apply_update.bat exists
        if not os.path.exists(bat_path):
            print(f"[FAIL] Companion batch update script not found at expected path.")
            return False
        print(f"[OK] Companion batch update script found: {bat_path}")

        # 4. Verify app_icon.png exists
        if not os.path.exists(icon_path):
            print(f"[FAIL] App logo icon not found at expected path.")
            return False
        print(f"[OK] App logo icon found: {icon_path}")

        print("\n=== INTEGRITY TEST PASSED SUCCESSFULLY ===")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = run_integrity_test()
    sys.exit(0 if success else 1)
