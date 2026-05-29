# Camplife DataLoader: QA Testing Procedure

This document serves as the master Quality Assurance (QA) checklist for the Camplife DataLoader. Run through this document after making any codebase changes or before releasing a new executable version to ensure all core functionality remains intact.

## Prerequisites for Testing
- Have the latest built executable (`Camplife DataLoader.exe`) or run from the source code (`python main.py`).
- Have a test CSV/Excel file ready containing at least two rows with the following test Camplife IDs:
  - **Row 1:** Camplife ID `4869657`
  - **Row 2:** Camplife ID `5043363`
- Ensure the test file has columns for: `Camplife ID`, `Member Number`, `Membership Type`, `Effective From`, `Effective To`, `Tag`, and `Note`.
- Have a valid `api_key` and `api_secret` ready.

---

## Phase 1: Launch & Configuration Tests

### 1.1 Application Launch
- **Task**: Open the application.
- **Criteria**: 
  - The loading screen appears centered on the screen.
  - The loading screen seamlessly transitions to the Main Window.
  - The Main Window is ~80% of the screen size, centered, and fully resizable.

### 1.2 Theme Toggling
- **Task**: Click the "🌓 Theme" button in the top right.
- **Criteria**: 
  - The interface immediately toggles between the Light (Tan/Sand) and Dark (Charcoal) themes.
  - All text remains readable and all buttons are clearly visible in both modes.

### 1.3 Setup & Credentials
- **Task**: Click the "⚙️ Setup" button. Enter valid API keys and click "Save".
- **Criteria**: 
  - The dialog closes.
  - The label on the main window updates to show "🔑 Keys saved (XXXXX...)".
  - A `config.json` file is correctly created/updated in the application directory.

### 1.4 API Connection & Data Loading
- **Task**: Click the "Connect" button next to the Resort dropdown.
- **Criteria**: 
  - The status label in the bottom right changes to "Connected" and turns green.
  - The "Resort" dropdown correctly populates with a list of properties.
  - The "Membership Type" override dropdown correctly populates with available memberships.

---

## Phase 2: File Ingestion & Mapping Tests

### 2.1 File Upload
- **Task**: Click "Select File" and choose the prepared Test CSV/Excel file.
- **Criteria**: 
  - The file name appears next to the button.
  - A success message appears in the bottom left status bar: "File loaded: [filename] ✅".

### 2.2 Auto-Mapping Validation
- **Task**: Review the Step 1 Column Mapping dropdowns immediately after loading the file.
- **Criteria**: 
  - The dropdowns (`Camplife ID`, `Member Number`, `Membership Type`, etc.) should automatically select the matching column headers from your file.

### 2.3 Override Validation
- **Task**: In "Step 2: Optional Overrides", enter a test Tag Name (e.g., `QA_TEST_TAG`) and a test Note (e.g., `QA Auto-Generated Note`).
- **Criteria**: 
  - The text is successfully entered into the input fields without UI glitches.

---

## Phase 3: Preview & Upload Execution Tests

### 3.1 Data Preview
- **Task**: Click the "Preview Data" button at the bottom of the main window.
- **Criteria**: 
  - A new "Preview Data" window opens.
  - The table displays your test rows (including IDs `4869657` and `5043363`).
  - The two right-most columns ("Status" and "Response") are initially blank.

### 3.2 Upload Process (The Core Engine)
- **Task**: In the Preview Data window, click "Start Upload".
- **Criteria**: 
  - A modal Progress Dialog appears.
  - The progress bar dynamically fills as rows process.
  - The ETA label actively counts down.
  - The "Start Upload" button is disabled during processing to prevent duplicate clicks.

### 3.3 Thread Non-Blocking Validation
- **Task**: While the upload progress bar is moving, attempt to move the main window around the screen.
- **Criteria**: 
  - The application window moves smoothly and does NOT say "Not Responding" in the title bar. (Validates that the background thread is working perfectly).

---

## Phase 4: Results & Logging Tests

### 4.1 UI Success Verification
- **Task**: Observe the Preview Data window after the progress bar reaches 100% and closes.
- **Criteria**: 
  - The "Status" column for IDs `4869657` and `5043363` shows a ✅ (if data was valid) or a ❌ (if data was invalid/missing).
  - The "Response" column shows HTTP status codes (e.g., `Membership:200, Note:201, Tag:200`).

### 4.2 Deep Log Inspection
- **Task**: Click directly on the row for Camplife ID `4869657` in the Preview table.
- **Criteria**: 
  - A detailed "Request / Response Log" dialog opens.
  - The dialog displays formatted JSON for the API Requests sent to the Membership, Note, and Tag endpoints.
  - Verify that the URL generated for the requests correctly includes the Camplife ID `4869657`.

### 4.3 Excel File Log Generation
- **Task**: Check the folder where the application is located.
- **Criteria**: 
  - A new Excel file named `Camplife_Upload_Log_YYYY-MM-DD_HH-MM-SS.xlsx` has been generated.
  - Opening the Excel file shows detailed columns for Membership, Note, and Tag URLs, Status Codes, and JSON Responses for both test IDs.

---

> [!CAUTION]
> If any of the above criteria fail during a routine QA test, the latest code changes have introduced a regression and should be reverted or patched immediately before building a new executable for end-users.
