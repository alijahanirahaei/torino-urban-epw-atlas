import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_supplement import PACKAGE, build, safe_path, validate


class SupplementTests(unittest.TestCase):
    def test_published_package(self):
        result = validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["heat_configurations"], 105)
        self.assertEqual(result["version"], "1.1.0")

    def test_versioned_archive_is_reproducible(self):
        import hashlib
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as tmp:
            first = build(Path(tmp) / "first")[0]
            second = build(Path(tmp) / "second")[0]
            self.assertEqual(first.name, "torino_uwg_supplement_v1.1.0.zip")
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(),
                             hashlib.sha256(second.read_bytes()).digest())
            with ZipFile(first) as archive:
                self.assertTrue(all(safe_path(n) for n in archive.namelist()))

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
