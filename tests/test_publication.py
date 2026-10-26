import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish_release as publication


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.expected = self.root / "expected"
        self.downloaded = self.root / "downloaded"
        self.expected.mkdir()
        self.downloaded.mkdir()
        self.bundle = self.expected / "atlas.zip"
        with ZipFile(self.bundle, "w", ZIP_STORED) as z:
            z.writestr("atlas/data.txt", b"verified data" * 100)
        self.checksum_name = "SHA256SUMS.txt"
        (self.expected / self.checksum_name).write_text("unused local formatting\n")
        self.assets = [self.bundle, self.expected / self.checksum_name]
        self.write_download()

    def write_download(self, payload=b"verified data" * 100, name="atlas/data.txt"):
        target = self.downloaded / self.bundle.name
        with ZipFile(target, "w", ZIP_DEFLATED) as z:
            z.writestr(name, payload)
        value = hashlib.sha256(target.read_bytes()).hexdigest()
        (self.downloaded / self.checksum_name).write_text(f"{value}  {target.name}\n")

    def test_identical_members_with_different_compression(self):
        self.assertNotEqual(self.bundle.read_bytes(), (self.downloaded / self.bundle.name).read_bytes())
        publication.verify_assets(self.assets, self.downloaded, self.checksum_name)

    def test_changed_archive_content_rejected(self):
        self.write_download(b"different")
        with self.assertRaisesRegex(ValueError, "differs from tagged source"):
            publication.verify_assets(self.assets, self.downloaded, self.checksum_name)

    def test_changed_archive_members_rejected(self):
        self.write_download(name="atlas/other.txt")
        with self.assertRaisesRegex(ValueError, "differs from tagged source"):
            publication.verify_assets(self.assets, self.downloaded, self.checksum_name)

    def test_bad_checksum_rejected(self):
        (self.downloaded / self.checksum_name).write_text("0" * 64 + "  atlas.zip\n")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            publication.verify_assets(self.assets, self.downloaded, self.checksum_name)

    def test_missing_document_rejected(self):
        missing = self.expected / "document.pdf"
        missing.write_bytes(b"pdf")
        with self.assertRaisesRegex(ValueError, "Missing release asset"):
            publication.verify_assets(self.assets + [missing], self.downloaded, self.checksum_name)

    def test_existing_release_verified_without_create_or_upload(self):
        release = {"tag_name": "v0.3.0", "draft": False,
                   "assets": [{"name": p.name} for p in self.assets]}
        with patch.object(publication, "run", side_effect=[json.dumps([[release]]), ""]) as run:
            with patch.object(publication, "verify_assets") as verify:
                result = publication.publish_or_verify("atlas", "v0.3.0", "owner/repo", self.root,
                                                       self.assets, self.checksum_name)
                verify.assert_called_once()
            self.assertEqual(result, "verified")
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args.args[:3], ("gh", "release", "download"))

    def test_missing_release_created_with_dynamic_title(self):
        with patch.object(publication, "run", side_effect=["[[]]", ""]) as run:
            result = publication.publish_or_verify("supplement", "supplement-v1.1.0", "owner/repo",
                                                   self.root, self.assets, self.checksum_name)
            self.assertEqual(result, "created")
            self.assertIn("Torino study supplementary material v1.1.0", run.call_args.args)
            self.assertNotIn("--clobber", run.call_args.args)

    def test_existing_incomplete_release_is_not_overwritten(self):
        release = {"tag_name": "v0.3.0", "draft": False, "assets": []}
        with patch.object(publication, "run", return_value=json.dumps([[release]])) as run:
            with self.assertRaisesRegex(ValueError, "incomplete"):
                publication.publish_or_verify("atlas", "v0.3.0", "owner/repo", self.root,
                                               self.assets, self.checksum_name)
            self.assertEqual(run.call_count, 1)

    def test_draft_is_not_silently_published(self):
        release = {"tag_name": "v0.3.0", "draft": True, "assets": []}
        with patch.object(publication, "run", return_value=json.dumps([[release]])):
            with self.assertRaisesRegex(ValueError, "unpublished draft"):
                publication.publish_or_verify("atlas", "v0.3.0", "owner/repo", self.root,
                                               self.assets, self.checksum_name)

    def test_tag_must_match_metadata(self):
        folder = self.root / "web/data"
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text('{"version":"0.3.0"}')
        publication.validate_tag("atlas", "v0.3.0", self.root)
        for tag in ("v0.4.0", "main", "supplement-v0.3.0", "v0.3.0/other"):
            with self.assertRaises(ValueError):
                publication.validate_tag("atlas", tag, self.root)


if __name__ == "__main__":
    unittest.main()
