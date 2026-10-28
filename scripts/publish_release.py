"""Downloads-only release publisher. Payloads are data, never executable policy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "TelemetrixOne/rider-app-downloads"
SOURCE = "TelemetrixOne/trike-phone-app"
CERT = "1060741ff698085d3d1cb7ad4276a7da94a96c6b9ae81196a6672c69062ff853"
APP = "com.hpr.gpspublisher"
STABLE = "TelemetrixOne-Rider-App.apk"
BASE = "https://github.com/" + REPOSITORY + "/releases"
LIMIT = 32 * 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def decode(data):
    return json.loads(data, object_pairs_hook=unique_object)


def validate_metadata(meta, queued=False):
    require(type(meta.get("version_code")) is int and meta["version_code"] >= 22, "Unsupported version code")
    version = str(meta.get("version_name", ""))
    require(re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version) and tuple(map(int, version.split('.'))) >= (2, 11, 1), "Unsupported stable app version")
    require(meta.get("application_id") == APP and meta.get("build_type") == "release" and meta.get("debuggable") is False, "Not a distribution build")
    require(meta.get("signing_certificate_sha256") == CERT, "Unexpected signing certificate")
    require(re.fullmatch(r"[0-9a-f]{64}", str(meta.get("sha256", ""))), "Invalid checksum")
    require(re.fullmatch(r"[0-9a-f]{40}", str(meta.get("source_commit", ""))), "Invalid source commit")
    require(type(meta.get("minimum_android_api")) is int and meta["minimum_android_api"] >= 26, "Invalid minimum Android API")
    if queued:
        allowed = {"version_name", "version_code", "application_id", "build_type", "debuggable", "sha256", "signing_certificate_sha256", "minimum_android_api", "source_commit", "source_repository", "source_workflow_run_id"}
        require(set(meta) == allowed, "Unexpected public metadata fields")
        require(meta["source_repository"] == SOURCE and type(meta["source_workflow_run_id"]) is int and meta["source_workflow_run_id"] > 0, "Invalid build provenance")


class Api:
    def __init__(self, token):
        self.token = token

    def request(self, path, method="GET", data=None, binary=False, upload=False):
        host = "https://uploads.github.com" if upload else "https://api.github.com"
        headers = {"Accept": "application/octet-stream" if binary else "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if data is not None:
            headers["Content-Type"] = "application/octet-stream" if upload else "application/json"
            if not upload:
                data = json.dumps(data).encode()
        request = urllib.request.Request(host + path, data=data, method=method, headers=headers)
        # Do not forward credentials to a redirected object-storage URL.
        if self.token:
            request.add_unredirected_header("Authorization", "Bearer " + self.token)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                require(response.url.startswith("https://"), "Insecure redirect")
                body = response.read(LIMIT + 1)
                require(len(body) <= LIMIT, "Oversized API response")
                return body if binary else decode(body)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise ValueError("GitHub request failed with HTTP " + str(error.code)) from None

    def releases(self):
        for page in range(1, 101):
            values = self.request(f"/repos/{REPOSITORY}/releases?per_page=100&page={page}")
            require(isinstance(values, list), "Cannot list releases")
            yield from values
            if len(values) < 100:
                return
        raise ValueError("Release pagination bound exceeded")

    def assets(self, release_id):
        result = self.request(f"/repos/{REPOSITORY}/releases/{release_id}/assets?per_page=100")
        require(isinstance(result, list) and len(result) < 100, "Invalid/oversized asset list")
        return result

    def download(self, asset):
        data = self.request(f"/repos/{REPOSITORY}/releases/assets/{int(asset['id'])}", binary=True)
        require(data is not None, "Missing release asset")
        return data


def highest_published(api):
    highest = 0
    for release in api.releases():
        if release["draft"]:
            continue
        assets = [item for item in api.assets(release["id"]) if item["name"] == "release.json"]
        require(len(assets) == 1, "Published release lacks unique trusted metadata; review manually")
        meta = decode(api.download(assets[0]))
        validate_metadata(meta)
        require(release["tag_name"] == "v" + meta["version_name"], "Published tag/metadata mismatch")
        highest = max(highest, meta["version_code"])
    return highest


def discover(payload_root):
    result = subprocess.run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "--no-renames", "HEAD"], cwd=payload_root, capture_output=True, text=True, check=True)
    paths = [value for value in result.stdout.splitlines() if value == "request/release.json"]
    require(len(paths) == 1, "Push must contain exactly one publication request")
    return payload_root / "request"


def load_candidate(folder):
    folder = folder.resolve(strict=True)
    meta_file = folder / "release.json"
    require(meta_file.is_file() and not meta_file.is_symlink() and meta_file.stat().st_size <= 16384, "Invalid request metadata")
    meta = decode(meta_file.read_bytes())
    validate_metadata(meta, queued=True)
    name = f"TelemetrixOne-Rider-App-v{meta['version_name']}-release.apk"
    require({p.name for p in folder.iterdir()} == {name, name + ".sha256", "release.json"}, "Unexpected request files")
    apk = folder / name
    checksum = folder / (name + ".sha256")
    require(all(p.is_file() and not p.is_symlink() for p in (apk, checksum)), "Invalid request file type")
    require(0 < apk.stat().st_size <= LIMIT and checksum.stat().st_size <= 1024, "Invalid request size")
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    require(meta["sha256"] == digest, "APK checksum mismatch")
    require(checksum.read_text().strip().split() == [digest, name], "Checksum sidecar mismatch")
    return meta, apk


def verify_apk(meta, apk, build_tools):
    def run(name, args):
        suffix = (".bat" if name == "apksigner" else ".exe") if os.name == "nt" else ""
        result = subprocess.run([str(build_tools / (name + suffix)), *args], capture_output=True, text=True)
        require(result.returncode == 0, "Android verification failed")
        return result.stdout
    manifest = run("aapt", ["dump", "xmltree", str(apk), "AndroidManifest.xml"])
    require(all(line.endswith("(type 0x12)0x0") for line in manifest.splitlines() if "A: android:debuggable(" in line), "Debuggable APK")
    require(any("A: android:allowBackup(" in line and line.endswith("(type 0x12)0x0") for line in manifest.splitlines()), "Backup must remain disabled")
    badging = run("aapt", ["dump", "badging", str(apk)])
    package = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    require(package and package.groups() == (APP, str(meta["version_code"]), meta["version_name"]), "APK identity/version mismatch")
    require(int(re.search(r"sdkVersion:'(\d+)'", badging).group(1)) == meta["minimum_android_api"], "APK minimum API mismatch")
    certs = run("apksigner", ["verify", "--print-certs", str(apk)])
    require(re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)", certs) == [CERT], "APK upgrade certificate mismatch")


def stage_files(meta, apk, created_at):
    manifest = dict(meta, release_created_at=created_at,
                    versioned_download_url=f"{BASE}/download/v{meta['version_name']}/{apk.name}",
                    download_url=f"{BASE}/latest/download/{STABLE}")
    payload = apk.read_bytes()
    return {apk.name: payload, STABLE: payload,
            apk.name + ".sha256": f"{meta['sha256']}  {apk.name}\n".encode(),
            "SHA256SUMS.txt": f"{meta['sha256']}  {apk.name}\n{meta['sha256']}  {STABLE}\n".encode(),
            "release.json": (json.dumps(manifest, indent=2) + "\n").encode()}


def promote(api, meta, apk, dry_run=False):
    if meta["version_code"] <= highest_published(api):
        print("SKIP: equal/older version code; existing releases and latest are unchanged.")
        return False
    if dry_run:
        print("DRY RUN: candidate is newer and verified; no public writes performed.")
        return False
    tag = "v" + meta["version_name"]
    release = api.request(f"/repos/{REPOSITORY}/releases/tags/{tag}")
    if release is None:
        release = api.request(f"/repos/{REPOSITORY}/releases", "POST", {
            "tag_name": tag, "target_commitish": "main", "name": "TelemetrixOne Rider App " + tag,
            "body": "Audited Android release. Install over the existing app; do not uninstall or clear data.",
            "draft": True, "prerelease": False, "make_latest": "false"})
    require(release["draft"] and not release["prerelease"], "Refusing to alter a published release")
    files = stage_files(meta, apk, release["created_at"])
    assets = api.assets(release["id"])
    require(len({a['name'] for a in assets}) == len(assets) and all(a["name"] in files for a in assets), "Draft contains unexpected assets")
    existing = {a["name"]: a for a in assets}
    for name, body in files.items():
        if name not in existing:
            uploaded = api.request(f"/repos/{REPOSITORY}/releases/{release['id']}/assets?name={urllib.parse.quote(name)}", "POST", body, upload=True)
            require(uploaded is not None, "Asset upload failed")
    assets = api.assets(release["id"])
    require({a["name"] for a in assets} == set(files) and len(assets) == len(files), "Incomplete draft")
    for asset in assets:
        require(api.download(asset) == files[asset["name"]], "Uploaded draft asset differs; manual review required")
    # Check again after uploads: another/manual publisher must not be superseded by older code.
    require(meta["version_code"] > highest_published(api), "A newer/equal release appeared; draft left unpublished")
    result = api.request(f"/repos/{REPOSITORY}/releases/{release['id']}", "PATCH", {"draft": False, "prerelease": False, "make_latest": "true"})
    require(result and not result["draft"], "Promotion not confirmed")
    print("PUBLISHED: complete verified release promoted to latest.")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-root", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--build-tools", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    require(bool(args.candidate) != bool(args.payload_root), "Choose exactly one request source")
    folder = args.candidate or discover(args.payload_root)
    if args.payload_root:
        require(not folder.is_symlink() and folder.resolve().is_relative_to(args.payload_root.resolve()), "Request escaped checkout")
    meta, apk = load_candidate(folder)
    verify_apk(meta, apk, args.build_tools)
    token = os.environ.get("DOWNLOADS_TOKEN", "")
    require(args.dry_run or token, "Missing downloads-only publication token")
    promote(Api(token), meta, apk, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL: " + str(error), file=sys.stderr)
        sys.exit(1)
