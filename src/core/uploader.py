import time
import logging
import threading
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
from PySide6.QtCore import QThread, Signal

from config import BASE_API

logger = logging.getLogger("camplife.upload")

def parse_row_data(row_dict, column_map, top_fields):
    """
    Extract and clean all fields for a given row.
    Returns a dictionary of parsed and cleaned values:
    {
        "camplife_id": str or None,
        "member_number": str or None,
        "membership_name": str or None,
        "eff_from": str or None,
        "eff_to": str or None,
        "tag_val": str or None,
        "note_val": str or None
    }
    """
    parsed = {}

    # 1. Camplife ID
    camplife_col = column_map.get("Camplife ID")
    camplife_id = None
    if camplife_col and camplife_col != "N/A":
        raw = row_dict.get(camplife_col)
        if raw is not None and not pd.isna(raw):
            if isinstance(raw, float):
                camplife_id = str(int(raw))
            else:
                camplife_id = str(raw).strip()
    parsed["camplife_id"] = camplife_id

    # 2. Member Number
    member_number = None
    mn_col = column_map.get("Member Number")
    if mn_col and mn_col != "N/A":
        raw = row_dict.get(mn_col)
        if raw is not None and not pd.isna(raw):
            member_number = str(raw).strip()
    parsed["member_number"] = member_number

    # 3. Membership Type
    membership_name = top_fields.get("Membership Type") or None
    if not membership_name:
        mcol = column_map.get("Membership Type")
        if mcol and mcol != "N/A":
            raw = row_dict.get(mcol)
            if raw is not None and not pd.isna(raw):
                membership_name = str(raw).strip()
    parsed["membership_name"] = membership_name

    # 4. Effective From
    eff_from = None
    efcol = column_map.get("Effective From")
    if efcol and efcol != "N/A":
        raw = row_dict.get(efcol)
        if raw is not None and not pd.isna(raw):
            val_str = str(raw).strip()
            if val_str != "":
                eff_from = val_str
    parsed["eff_from"] = eff_from

    # 5. Effective To
    eff_to = None
    etcol = column_map.get("Effective To")
    if etcol and etcol != "N/A":
        raw = row_dict.get(etcol)
        if raw is not None and not pd.isna(raw):
            val_str = str(raw).strip()
            if val_str != "":
                eff_to = val_str
    parsed["eff_to"] = eff_to

    # 6. Tag
    tag_val = top_fields.get("Tag") or None
    if tag_val is None:
        tcol = column_map.get("Tag")
        if tcol and tcol != "N/A":
            raw = row_dict.get(tcol)
            if raw is not None and not pd.isna(raw):
                tag_val = str(raw).strip()
    parsed["tag_val"] = tag_val

    # 7. Note
    note_val = top_fields.get("Note") or None
    if note_val is None:
        ncol = column_map.get("Note")
        if ncol and ncol != "N/A":
            raw = row_dict.get(ncol)
            if raw is not None and not pd.isna(raw):
                note_val = str(raw).strip()
    parsed["note_val"] = note_val

    return parsed


def validate_dataframe(df, column_map, top_fields):
    """
    Validate rows for required fields and valid date formats before upload.
    Returns list of invalid rows: [{"row": int, "issues": [str]}, ...]
    """
    invalid_rows = []

    # Use to_dict('records') for highly efficient dict iteration
    for r, row_dict in enumerate(df.to_dict('records')):
        parsed = parse_row_data(row_dict, column_map, top_fields)
        issues = []

        if not parsed["camplife_id"]:
            issues.append("Missing Camplife ID")

        has_membership = bool(parsed["membership_name"] or parsed["member_number"] or parsed["eff_from"])
        has_tag = bool(parsed["tag_val"])
        has_note = bool(parsed["note_val"])

        # A row must have at least one action
        if not (has_membership or has_tag or has_note):
            issues.append("Row has no upload data (Membership, Tag, or Note must be supplied)")

        # If they attempted a membership upload, validate all required membership fields
        if has_membership:
            if not parsed["membership_name"]:
                issues.append("Missing Membership Type")
            if not parsed["member_number"]:
                issues.append("Missing Member Number")
            if not parsed["eff_from"]:
                issues.append("Missing Effective From")

        # Validate date formats for non-empty date fields to prevent silent worker crashes
        if parsed["eff_from"]:
            try:
                pd.to_datetime(parsed["eff_from"], errors='raise')
            except Exception:
                issues.append(f"Invalid 'Effective From' date format: '{parsed['eff_from']}'")

        if parsed["eff_to"]:
            try:
                pd.to_datetime(parsed["eff_to"], errors='raise')
            except Exception:
                issues.append(f"Invalid 'Effective To' date format: '{parsed['eff_to']}'")

        if issues:
            invalid_rows.append({"row": r, "issues": issues})

    return invalid_rows

class UploadWorker(QThread):
    """Thread worker to upload rows one-by-one without blocking the GUI."""
    progress = Signal(int, int)               # emitted with (current_index, total)
    row_finished = Signal(int, dict)          # emitted with (row_index, log_entry)
    finished = Signal()                       # emitted when all rows done or cancelled
    error = Signal(str)                       # emitted on fatal worker error
    paused = Signal()                         # emitted when pause is acknowledged
    resumed = Signal()                        # emitted when resume is acknowledged

    def __init__(self, df, column_map, top_fields, cg_alias, api_client):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.column_map = column_map.copy()
        self.top_fields = top_fields.copy()
        self.cg_alias = cg_alias
        self.api_client = api_client
        self._cancel_requested = False
        self._pause_event = threading.Event()
        self._pause_event.set()

    def request_cancel(self):
        self._cancel_requested = True

    def request_pause(self):
        self._pause_event.clear()

    def request_resume(self):
        self._pause_event.set()

    def _to_iso(self, value):
        """
        Convert any date/datetime-like value into a full ISO 8601 UTC string
        with Z suffix: YYYY-MM-DDTHH:MM:SSZ
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        try:
            if isinstance(value, str) and value.strip() == "":
                return None

            # Parse date with pandas (handles most formats)
            ts = pd.to_datetime(value, errors='coerce')

            if ts is None or pd.isna(ts):
                return None

            # Convert to UTC and drop timezone if needed
            ts = ts.tz_localize('UTC') if ts.tzinfo is None else ts.tz_convert('UTC')

            # Always format as full ISO with Z suffix
            return ts.strftime("%Y-%m-%dT%H:%M:%SZ")

        except Exception:
            return None

    def run(self):
        try:
            total = len(self.df)
            logger.info(f"Starting upload of {total} rows")
            headers_common = {"Content-Type": "application/json", "Accept": "application/json"}
            for r in range(total):
                # Check for pause request
                self._pause_event.wait()

                if self._cancel_requested:
                    logger.info("Upload cancelled by user")
                    break
                log_entry = {}
                try:
                    row_dict = self.df.iloc[r].to_dict()
                    parsed = parse_row_data(row_dict, self.column_map, self.top_fields)

                    camplife_id = parsed["camplife_id"]
                    member_number = parsed["member_number"]
                    membership_name = parsed["membership_name"]
                    eff_from = parsed["eff_from"]
                    eff_to = parsed["eff_to"]
                    tag_val = parsed["tag_val"]
                    note_val = parsed["note_val"]

                    has_membership = bool(membership_name or member_number or eff_from)
                    if not has_membership:
                        log_entry["membership"] = None
                    elif not camplife_id or not membership_name or not member_number or (eff_from is None or str(eff_from).strip() == ""):
                        logger.warning(f"Row {r}: missing required membership fields (ID:{camplife_id}, Name:{membership_name}, Num:{member_number}, From:{eff_from})")
                        log_entry["membership"] = {
                            "method": "PUT",
                            "url": None,
                            "headers": {**headers_common},
                            "request": None,
                            "response": {"status_code": None, "json": None, "text": "Missing required membership fields"},
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        membership_payload = {
                            membership_name: {
                                "memberNumber": str(member_number),
                                "effectiveFrom": self._to_iso(eff_from)
                            }
                        }
                        if eff_to is not None and str(eff_to).strip() != "":
                            membership_payload[membership_name]["effectiveTo"] = self._to_iso(eff_to)

                        mem_name_enc = quote_plus(membership_name)
                        mem_id_enc = quote_plus(camplife_id)
                        mem_url = f"{BASE_API}/customer/{mem_id_enc}/membership/{mem_name_enc}"

                        log_entry["membership"] = {
                            "method": "PUT",
                            "url": mem_url,
                            "headers": {**headers_common},
                            "request": membership_payload,
                            "response": None,
                            "timestamp": datetime.now().isoformat()
                        }
                        mem_resp = self.api_client.make_api_call_with_retry("PUT", mem_url, headers=headers_common, json_payload=membership_payload)
                        log_entry["membership"]["response"] = mem_resp

                    # ---------- Note ----------
                    if note_val and str(note_val).strip() != "":
                        if not camplife_id:
                            log_entry["note"] = {
                                "method": "POST",
                                "url": None,
                                "headers": {**headers_common},
                                "request": {"text": str(note_val)},
                                "response": {"status_code": None, "json": None, "text": "Note skipped - Camplife ID missing"},
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            note_payload = {"text": str(note_val)}
                            note_id_enc = quote_plus(camplife_id)
                            cg_enc = quote_plus(str(self.cg_alias))
                            note_url = f"{BASE_API}/customer/{note_id_enc}/note"
                            log_entry["note"] = {
                                "method": "POST",
                                "url": note_url,
                                "headers": {**headers_common},
                                "request": note_payload,
                                "response": None,
                                "timestamp": datetime.now().isoformat()
                            }
                            note_resp = self.api_client.make_api_call_with_retry("POST", note_url, headers=headers_common, json_payload=note_payload, params={'cgAlias': cg_enc})
                            log_entry["note"]["response"] = note_resp
                    else:
                        log_entry["note"] = None

                    # ---------- Tag ----------
                    if tag_val and str(tag_val).strip() != "":
                        if not camplife_id:
                            log_entry["tag"] = {
                                "method": "PUT",
                                "url": None,
                                "headers": {**headers_common},
                                "request": {"tagName": str(tag_val)},
                                "response": {"status_code": None, "json": None, "text": "Tag skipped - Camplife ID missing"},
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            tag_name = str(tag_val)
                            tag_name_enc = quote_plus(tag_name)
                            tag_id_enc = quote_plus(camplife_id)
                            cg_enc = quote_plus(str(self.cg_alias))
                            tag_url = f"{BASE_API}/customer/{tag_id_enc}/property/{cg_enc}/tag/{tag_name_enc}"
                            tag_payload = {"tagName": tag_name}
                            log_entry["tag"] = {
                                "method": "PUT",
                                "url": tag_url,
                                "headers": {**headers_common},
                                "request": tag_payload,
                                "response": None,
                                "timestamp": datetime.now().isoformat()
                            }
                            tag_resp = self.api_client.make_api_call_with_retry("PUT", tag_url, headers=headers_common, json_payload=tag_payload)
                            log_entry["tag"]["response"] = tag_resp
                    else:
                        log_entry["tag"] = None

                    # Emit row finished so GUI can update
                    self.row_finished.emit(r, log_entry)

                except Exception as e:
                    logger.exception(f"Row {r} processing failed")
                    self.row_finished.emit(r, {"membership": None, "note": None, "tag": None, "exception": str(e)})

                self.progress.emit(r + 1, total)

            logger.info(f"Upload complete: {total} rows processed")
            self.finished.emit()
        except Exception as exc:
            logger.exception("Upload worker failed with exception")
            self.error.emit(str(exc))
            self.finished.emit()
