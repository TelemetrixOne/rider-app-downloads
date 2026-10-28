# Audited downloads publication

This repository contains distribution assets and publisher infrastructure only, never Android application source or private app configuration.

## Trust boundary

The private Android repo's `Queue audited Rider download` workflow runs only after a completed successful main build (or an explicit main-only recovery dispatch). It independently checks the original workflow, successful build/audit steps, main ancestry, artifact ZIP digest, source SHA/version, APK checksum, non-debuggable manifest and upgrade certificate. It then forwards exactly three files: the versioned APK, canonical checksum sidecar and whitelisted release metadata.

The handoff uses a dedicated **write deploy key attached only to this repository**, stored as `RIDER_DOWNLOADS_SSH_KEY` in the private Android repository's Actions secrets. No personal GitHub token or app-signing private key is copied here. Private CI's GITHUB_TOKEN has only contents/read and actions/read. The SSH key cannot read the private app repository. It has repository-wide write access here (not branch-only access), has no automatic expiration, and should be revoked/replaced if compromised. A GitHub App is an alternative future credential path; do not replace this key with a broad PAT.

Private CI serializes pushes to `publication-requests`. That branch contains the current three-file `request/` and publisher infrastructure inherited from main. It is not a source branch. Request Git history contains already-public APK bytes, not app source. No force pushes are used. Known SSH host keys are fetched from GitHub's HTTPS metadata, with strict host verification and no agent forwarding or ambient identities.

## Public publisher

`Publish audited Rider APK` listens only to request-directory pushes on `publication-requests`. It executes policy checked out from **main**, not code supplied by the request. Request files are data only. Its own public-repository GITHUB_TOKEN has contents/write solely here. GitHub Actions is serialized with cancel-in-progress false.

Before writing it verifies the APK again with Android build tools: package, manifest, versionCode >=22, stable version >=2.11.1, non-debuggable, backup disabled, minimum API, checksum, exact established certificate. It reads all published release metadata to find the highest versionCode. An equal/older code is a no-op, including reruns with different bytes; a new build must increase code to publish. Unknown or malformed published metadata fails closed.

A newer release is created as a draft with make_latest false. All five assets must be present and each is downloaded and byte-verified before promotion. Partial/mismatching drafts remain unpublished for manual review; existing published assets are never overwritten or deleted. Code ordering is checked again immediately before promotion. Only then is the complete draft published with make_latest true. All manual publishers must follow the same increasing-code rule and must not race the automated promoter.

Assets:

- `TelemetrixOne-Rider-App-vVERSION-release.apk`
- identical `TelemetrixOne-Rider-App.apk`
- versioned `.apk.sha256`
- `SHA256SUMS.txt` for both APK names
- `release.json`

Metadata retains audited version, code, package, build type, debug flag, digest, signer, Android API and source SHA. Queued releases additionally include source repository/run ID, release_created_at, versioned_download_url and the fixed download_url. release_created_at is the draft creation time, not a claim about the exact promotion time. No credential fields or arbitrary extra request metadata are accepted.

Stable links (no browser credentials required):

- `/releases/latest/download/TelemetrixOne-Rider-App.apk`
- `/releases/latest/download/release.json`

## Verification and recovery

Pure publisher tests exercise failed/old/equal inputs, changed upload bytes, parallel newer releases and incomplete/unexpected payloads using a fake API; these tests create no real release. A real signed v2.11.1 equal-code request may be used to test the entire pipeline safely: it must finish SKIP and leave the existing latest release unchanged. Never invent a new app version just to test deployment.

For a future successful build whose request failed, dispatch `Queue audited Rider download` on private main with its build run ID. It re-verifies everything, skips already-published codes and pushes only if newer. If a partially uploaded draft has a mismatching asset, review it manually rather than enabling overwrite. Keep main publisher policy reviewed; anyone holding a write deploy key can modify this public repository, so the key must remain an Actions secret.
