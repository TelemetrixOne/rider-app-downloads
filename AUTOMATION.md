# Audited downloads publication

**Owner decision: automation pending.** The private source queue workflow is manually disabled; normal Android build CI remains active. This repository's publisher stays guarded without incoming requests. Do not provision credentials or re-enable the queue until the owner resumes activation. Future public releases require explicit owner authorization while automation is pending.

**Authorized manual release, 29 October 2026:** v2.12.1 (code 24) is published from successful audited Android build `40770054545`, source `90bada583a242d76ca19efb4b59f3953432fa4b6`, APK SHA-256 `c3cf5cc53d99a61a35c8ebaa5e9ee0bbed9c3efdb24c874e988b4b15668c4edc`. All five draft assets were downloaded and byte-verified before promotion to latest. This one-off local publication did not enable automation or provision/store credentials in CI or either repository.

This repository contains distribution assets and publisher infrastructure only, never Android application source or private app configuration.

## Trust boundary

The private Android repo's `Queue audited Rider download` workflow runs only after a completed successful main build (or an explicit main-only recovery dispatch). It independently checks the original workflow, successful build/audit steps, main ancestry, artifact ZIP digest, source SHA/version, APK checksum, non-debuggable manifest and upgrade certificate. It then forwards exactly three files: the versioned APK, canonical checksum sidecar and whitelisted release metadata.

The handoff uses a **short-lived GitHub App installation token restricted to this repository**. No personal GitHub token or app-signing private key is copied here. Private CI's GITHUB_TOKEN has only contents/read and actions/read. The token-creation action requests only this repository and Contents/write; the queue additionally verifies `/installation/repositories` reports exactly this single repository, rejecting broader tokens. It is revoked after the job. Its Git authorization header is passed through process environment only, never a URL, Git config file or commit.

**Activation requires one human setup:** register/install a GitHub App with Contents/read-write and Metadata/read, selecting only `rider-app-downloads`. Set private Android repo variable `RIDER_DOWNLOADS_APP_ID` and secret `RIDER_DOWNLOADS_APP_PRIVATE_KEY`. Do not paste the private key into chat. Deploy-key provisioning was explicitly rejected by GitHub: deploy keys are disabled for this repository. That policy was not changed and no deploy key/SSH secret was created. Do not substitute a broad PAT. Until the App is configured, equal/older builds safely skip; a newer candidate stops with a clear provisioning error before any public write.

After owner-authorized App setup, re-enable `Queue audited Rider download` in the private Android Actions UI or with `gh workflow enable queue-rider-download.yml --repo TelemetrixOne/trike-phone-app`. Its current disabled state is intentional, not a build failure.

Private CI serializes HTTPS pushes to `publication-requests`. That branch contains the current three-file `request/` and publisher infrastructure inherited from main. It is not a source branch. Request Git history contains distribution APK bytes, not app source. No force pushes or ambient credential helpers are used.

Every source wake-up rediscovers the highest-code eligible successful main build, regardless of completion order. The queue checks the existing branch request immediately before committing and skips equal/older codes. Thus GitHub concurrency's single pending slot cannot cause a lower-code completion to replace or lose a newer candidate. Public workflow reruns recover failed promotion attempts without rewriting the same queued request.

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

For a future successful build whose request failed, dispatch `Queue audited Rider download` on private main with its build run ID. It re-verifies everything, skips already-published codes and pushes only if newer. If a partially uploaded draft has a mismatching asset, review it manually rather than enabling overwrite. Keep main publisher policy reviewed and the App installed only on this repository. No fake app version or overwrite of code22 is needed to test equal-code rejection.
