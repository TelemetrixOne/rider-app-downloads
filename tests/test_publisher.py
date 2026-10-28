import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("publisher", Path(__file__).parents[1] / "scripts/publish_release.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def metadata(code=23):
    return {"version_name": "2.11.2", "version_code": code, "application_id": p.APP,
            "build_type": "release", "debuggable": False, "sha256": hashlib.sha256(b"synthetic-apk").hexdigest(),
            "signing_certificate_sha256": p.CERT, "minimum_android_api": 26, "source_commit": "a" * 40,
            "source_repository": p.SOURCE, "source_workflow_run_id": 123}


class FakeApi:
    def __init__(self, current=22):
        self.current = current
        self.writes = []
        self.stored = {}
        self.race = False
        self.corrupt = False
        self.list_count = 0

    def releases(self):
        self.list_count += 1
        if self.current:
            yield {"id": 1, "draft": False, "tag_name": "v2.11.2"}

    def assets(self, release_id):
        if release_id == 1:
            return [{"id": 1, "name": "release.json"}]
        return [{"id": index + 10, "name": name} for index, name in enumerate(self.stored)]

    def download(self, asset):
        if asset["id"] == 1:
            code = 99 if self.race and self.list_count > 1 else self.current
            return json.dumps(metadata(code)).encode()
        body = self.stored[asset["name"]]
        return body + b"corrupt" if self.corrupt else body

    def request(self, path, method="GET", data=None, **kwargs):
        if method == "GET":
            return None
        self.writes.append((method, path))
        if kwargs.get("upload"):
            name = p.urllib.parse.parse_qs(p.urllib.parse.urlsplit(path).query)["name"][0]
            self.stored[name] = data
            return {"id": 10, "name": name}
        if method == "POST":
            return {"id": 2, "draft": True, "prerelease": False, "created_at": "2026-10-28T00:00:00Z"}
        return {"id": 2, "draft": False}


class PublisherTest(unittest.TestCase):
    def apk(self, folder):
        apk = Path(folder) / "TelemetrixOne-Rider-App-v2.11.2-release.apk"
        apk.write_bytes(b"synthetic-apk")
        return apk

    def test_old_or_equal_code_never_writes(self):
        for code in (22, 23, 24):
            api = FakeApi(code)
            with tempfile.TemporaryDirectory() as folder:
                self.assertFalse(p.promote(api, metadata(22), self.apk(folder)))
            self.assertEqual([], api.writes)

    def test_dry_run_never_writes_even_for_newer_code(self):
        api = FakeApi()
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(p.promote(api, metadata(), self.apk(folder), True))
        self.assertEqual([], api.writes)

    def test_complete_draft_verified_before_single_promotion(self):
        api = FakeApi()
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(p.promote(api, metadata(), self.apk(folder)))
        self.assertEqual(5, len(api.stored))
        self.assertEqual(api.stored[p.STABLE], api.stored["TelemetrixOne-Rider-App-v2.11.2-release.apk"])
        self.assertEqual("PATCH", api.writes[-1][0])
        self.assertEqual(1, sum(method == "PATCH" for method, path in api.writes))

    def test_corrupt_uploaded_asset_never_promotes(self):
        api = FakeApi(); api.corrupt = True
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                p.promote(api, metadata(), self.apk(folder))
        self.assertFalse(any(method == "PATCH" for method, path in api.writes))

    def test_newer_release_during_upload_never_promotes_older_candidate(self):
        api = FakeApi(); api.race = True
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                p.promote(api, metadata(), self.apk(folder))
        self.assertFalse(any(method == "PATCH" for method, path in api.writes))

    def test_bad_version_certificate_debug_flag_or_unknown_metadata_rejected(self):
        for key, value in (("version_code", 21), ("version_code", True), ("version_name", "2.11.0"),
                           ("debuggable", True), ("signing_certificate_sha256", "b" * 64), ("extra-secret", "not-allowed")):
            meta = metadata(); meta[key] = value
            with self.assertRaises(ValueError):
                p.validate_metadata(meta, True)

    def test_checksum_and_unexpected_files_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = self.apk(folder)
            meta = metadata()
            (Path(folder) / "release.json").write_text(json.dumps(meta))
            sidecar = Path(str(apk) + ".sha256")
            sidecar.write_text(meta["sha256"] + "  " + apk.name + "\n")
            self.assertEqual(meta, p.load_candidate(Path(folder))[0])
            sidecar.write_text("0" * 64 + "  " + apk.name)
            with self.assertRaises(ValueError):
                p.load_candidate(Path(folder))
            (Path(folder) / "source.kt").write_text("must not be published")
            with self.assertRaises(ValueError):
                p.load_candidate(Path(folder))


if __name__ == "__main__":
    unittest.main()
