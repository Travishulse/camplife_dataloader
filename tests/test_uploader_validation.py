import unittest
import pandas as pd
from src.core.uploader import validate_dataframe

class TestUploaderValidation(unittest.TestCase):
    def setUp(self):
        self.column_map = {
            "Camplife ID": "Camplife ID",
            "Member Number": "Member Number",
            "Membership Type": "Membership Type",
            "Effective From": "Effective From",
            "Effective To": "Effective To",
            "Tag": "Tag",
            "Note": "Note"
        }
        self.top_fields = {}

    def test_membership_only_valid(self):
        # A completely valid membership-only row
        df = pd.DataFrame([{
            "Camplife ID": "12345",
            "Member Number": "MEM-100",
            "Membership Type": "Standard",
            "Effective From": "2026-01-01",
            "Effective To": "",
            "Tag": "",
            "Note": ""
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 0)

    def test_tag_only_valid(self):
        # A row with just Camplife ID and Tag (should be perfectly valid!)
        df = pd.DataFrame([{
            "Camplife ID": "12345",
            "Member Number": "",
            "Membership Type": "",
            "Effective From": "",
            "Effective To": "",
            "Tag": "ActiveCustomer",
            "Note": ""
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 0)

    def test_note_only_valid(self):
        # A row with just Camplife ID and Note (should be perfectly valid!)
        df = pd.DataFrame([{
            "Camplife ID": "12345",
            "Member Number": "",
            "Membership Type": "",
            "Effective From": "",
            "Effective To": "",
            "Tag": "",
            "Note": "Checked in early today"
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 0)

    def test_tag_and_note_combo_valid(self):
        # A row with Tag and Note, no Membership (perfectly valid!)
        df = pd.DataFrame([{
            "Camplife ID": "12345",
            "Member Number": "",
            "Membership Type": "",
            "Effective From": "",
            "Effective To": "",
            "Tag": "VIP_Guest",
            "Note": "High priority service requested"
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 0)

    def test_empty_row_invalid(self):
        # An empty row containing only a Camplife ID (invalid: no fields to upload)
        df = pd.DataFrame([{
            "Camplife ID": "12345",
            "Member Number": "",
            "Membership Type": "",
            "Effective From": "",
            "Effective To": "",
            "Tag": "",
            "Note": ""
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 1)
        self.assertIn("no upload data", issues[0]["issues"][0])

    def test_missing_id_invalid(self):
        # Missing Camplife ID (always invalid)
        df = pd.DataFrame([{
            "Camplife ID": "",
            "Member Number": "",
            "Membership Type": "",
            "Effective From": "",
            "Effective To": "",
            "Tag": "ActiveCustomer",
            "Note": ""
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 1)
        self.assertIn("Missing Camplife ID", issues[0]["issues"])

    def test_incomplete_membership_invalid(self):
        # Attempted membership but missing fields (invalid)
        df = pd.DataFrame([{
            "Camplife ID": "12345",
            "Member Number": "MEM-100",
            "Membership Type": "",  # missing type
            "Effective From": "2026-01-01",
            "Effective To": "",
            "Tag": "",
            "Note": ""
        }])
        issues = validate_dataframe(df, self.column_map, self.top_fields)
        self.assertEqual(len(issues), 1)
        self.assertIn("Missing Membership Type", issues[0]["issues"])

if __name__ == "__main__":
    unittest.main()
