import time
import logging
import threading
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
from PySide6.QtCore import QThread, Signal

from config import BASE_API

logger = logging.getLogger("camplife.upload")

def validate_dataframe(df, column_map, top_fields):
    """
    Validate rows for required fields before upload.
    Returns list of invalid rows: [{"row": int, "issues": [str]}, ...]
    Logic mirrors upload validation at run() line 119.
    """
    invalid_rows = []

    for r in range(len(df)):
        row_series = df.iloc[r]
        issues = []

        camplife_col = column_map.get("Camplife ID")
        camplife_id = None
        if camplife_col and camplife_col != "N/A":
            raw = row_series.get(camplife_col)
            if raw is None or pd.isna(raw):
                camplife_id = None
            else:
                if isinstance(raw, float):
                    camplife_id = str(int(raw))
                else:
                    camplife_id = str(raw).strip()

        if not camplife_id:
            issues.append("Missing Camplife ID")

        member_number = None
        mn_col = column_map.get("Member Number")
        if mn_col and mn_col != "N/A":
            raw = row_series.get(mn_col)
            member_number = str(raw).strip() if raw is not None and not pd.isna(raw) else None

        if not member_number:
            issues.append("Missing Member Number")

        membership_name = top_fields.get("Membership Type") or None
        if not membership_name:
            mcol = column_map.get("Membership Type")
            if mcol and mcol != "N/A":
                raw = row_series.get(mcol)
                membership_name = str(raw).strip() if raw is not None and not pd.isna(raw) else None

        if not membership_name:
            issues.append("Missing Membership Type")

        eff_from = None
        efcol = column_map.get("Effective From")
        if efcol and efcol != "N/A":
            eff_from = row_series.get(efcol)

        if eff_from is None or str(eff_from).strip() == "":
            issues.append("Missing Effective From")

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
                    row_series = self.df.iloc[r]

                    camplife_col = self.column_map.get("Camplife ID")
                    camplife_id = None
                    if camplife_col and camplife_col != "N/A":
                        raw = row_series.get(camplife_col)
                        if raw is None or pd.isna(raw):
                            camplife_id = None
                        else:
                            if isinstance(raw, float):
                                camplife_id = str(int(raw))
                            else:
                                camplife_id = str(raw).strip()

                    member_number = None
                    mn_col = self.column_map.get("Member Number")
                    if mn_col and mn_col != "N/A":
                        raw = row_series.get(mn_col)
                        member_number = str(raw).strip() if raw is not None and not pd.isna(raw) else None

                    membership_name = self.top_fields.get("Membership Type") or None
                    if not membership_name:
                        mcol = self.column_map.get("Membership Type")
                        if mcol and mcol != "N/A":
                            raw = row_series.get(mcol)
                            membership_name = str(raw).strip() if raw is not None and not pd.isna(raw) else None

                    eff_from = None
                    efcol = self.column_map.get("Effective From")
                    if efcol and efcol != "N/A":
                        eff_from = row_series.get(efcol)
                    eff_to = None
                    etcol = self.column_map.get("Effective To")
                    if etcol and etcol != "N/A":
                        eff_to = row_series.get(etcol)

                    tag_val = self.top_fields.get("Tag") or None
                    if tag_val is None:
                        tcol = self.column_map.get("Tag")
                        if tcol and tcol != "N/A":
                            raw = row_series.get(tcol)
                            tag_val = str(raw).strip() if raw is not None and not pd.isna(raw) else None

                    note_val = self.top_fields.get("Note") or None
                    if note_val is None:
                        ncol = self.column_map.get("Note")
                        if ncol and ncol != "N/A":
                            raw = row_series.get(ncol)
                            note_val = str(raw).strip() if raw is not None and not pd.isna(raw) else None

                    if not camplife_id or not membership_name or not member_number or (eff_from is None or str(eff_from).strip() == ""):
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
