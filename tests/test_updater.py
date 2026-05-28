import unittest
from src.core.updater import is_newer_version

class TestUpdaterVersionCheck(unittest.TestCase):
    def test_version_comparison(self):
        # Basic semver
        self.assertTrue(is_newer_version("1.1.0", "1.2.0"))
        self.assertTrue(is_newer_version("1.1.0", "2.0.0"))
        self.assertTrue(is_newer_version("1.1.0", "1.1.1"))
        
        # String 'v' prefix
        self.assertTrue(is_newer_version("v1.1.0", "v1.1.1"))
        self.assertTrue(is_newer_version("1.1.0", "v1.1.1"))
        self.assertTrue(is_newer_version("v1.1.0", "1.1.1"))
        
        # Mismatched lengths
        self.assertTrue(is_newer_version("1.1", "1.1.1"))
        self.assertTrue(is_newer_version("1.0", "1.0.1"))
        
        # No updates
        self.assertFalse(is_newer_version("1.2.0", "1.1.0"))
        self.assertFalse(is_newer_version("1.1.0", "1.1.0"))
        self.assertFalse(is_newer_version("1.1.1", "1.1"))
        
        # Fail safe fallback comparison
        self.assertTrue(is_newer_version("1.1.0-alpha", "1.1.0-beta"))

if __name__ == "__main__":
    unittest.main()
