import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_supplement import PACKAGE, safe_path, validate


class SupplementTests(unittest.TestCase):
    def test_published_package(self):
        result = validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["heat_configurations"], 105)

    def test_member_paths(self):
        for path in ("../file", "/absolute", "folder/../../file", "C:\\file", "C:/file", ""):
            self.assertFalse(safe_path(path), path)
        self.assertTrue(safe_path("tables/S1_minimax_curve.csv"))

    def test_modified_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "package"
            shutil.copytree(PACKAGE, copy)
            with (copy / "README.md").open("a") as f:
                f.write("\nChanged content.\n")
            with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                validate(copy)


if __name__ == "__main__":
    unittest.main()
