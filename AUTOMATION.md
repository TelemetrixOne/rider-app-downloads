# Audited downloads publication

**Latest authorized manual release, 23 November 2026:** v3.0.2 (code 30) fixes calibration with publishing off and improves Race Readiness and launch branding. Successful audited build `45102447030`, source `ef3749dbbe961cf34b67e436250fc88d57286ecb`, SHA-256 `203989d2f04a0a3ad04e298c8c37b622fa553000df0b25ed53419c2cdbf700b0`. The upgrade-compatible signed APK and all five draft assets were verified before promotion. Both anonymous APK downloads and public metadata were verified.

**Authorized manual release, 23 November 2026:** v3.0.1 (code 29) improves validation feedback and adds bounded numeric controls. Successful audited build `45100350049`, source `6ad1ad081668164149f023138e646a6d29247701`, SHA-256 `6d76cc0b72bed3fc776642d47725014d2476d040c1bb1312fa44a19202ccced9`. The signed artifact and all five draft assets were verified before promotion. Anonymous versioned and stable downloads and the TM1 Rider App page metadata match v3.0.1.

**Authorized manual release, 23 November 2026:** v3.0.0 (code 28) was published as latest after re-verifying audited Android build `45073083160`, source `b78401f3f6fd9212cdc7918c584a9b04fd62a708`, and established upgrade certificate. APK SHA-256 `181cc2aa6081c90327f5c72841aa0db98ce7dfe6209903ad0437f89db1c8596f`. All five draft assets were downloaded and compared before promotion, and anonymous downloads matched the checksum at both versioned and stable URLs. The TM1 download page uses the stable GitHub URL. This publication upgraded the public download only. The physical acceptance check and companion rider webpage deployment remain separate.

**Authorized manual release, 19 November 2026:** v2.13.2 (code 27) adds native audible pit-message alerts, with phone-local Audible Pit Alerts and Test Sound controls. Successful audited Android build `44444919426` (attempt 2), source `a63913654fc0615db714330495b632006955381e`, APK SHA-256 `fc222a0860096f5df005a1521e281cbbf12e6e731c7195c1a580fb141462b04f`. All 72 Android tests completed with zero failures and one optional public-network probe skipped; 14 publication/JavaScript tests passed. The immutable artifact, non-debuggable APK and established upgrade signer were reverified. All five draft assets were downloaded and byte-compared before promotion. Anonymous versioned/stable APKs and metadata identify the same release. Testing used isolated loopback MQTT, Robolectric audio and mocked rider data. Live TM1 services, production MQTT, website files and race phones were not contacted or changed. Physical phone acoustics remain to be checked with Test Sound on a spare phone or after the race. No credentials provisioning or automation activation occurred; the source queue remains manually disabled. Install in place after the race, without uninstalling or clearing data.

**Authorized manual release, 2 November 2026:** v2.13.1 (code 26) restores single-press calibration and earlier valid saved calibration references. Successful audited Android build `41365633372`, source `a05fc97e3f9408f6ee1d2449319e764ec5b3bc19`, APK SHA-256 `59a3177068d17936816aa225d425eb48fe68d0875d25cb0945da01ba475032a6`. The immutable CI artifact and established signer were reverified. All five draft assets were downloaded and byte-compared before promotion; anonymous versioned/stable APK downloads match the checksum, and versioned metadata plus a fresh latest-metadata request identify v2.13.1. No phone installation, pairing changes, credentials provisioning or automation activation occurred. The correction supersedes the v2.13.0 multi-stage calibration instructions; install in place and use Calibrate Now once with the mounted phone and trike upright and still.

**Owner decision: automation pending.** The private source queue workflow is manually disabled; normal Android build CI remains active. This repository's publisher stays guarded without incoming requests. Do not provision credentials or re-enable the queue until the owner resumes activation. The owner’s standing instruction from 23 November 2026 is to publish audited Rider releases to the TM1 Rider App page by default unless the owner says otherwise. This instruction applies to publication as part of release work. The separate queue automation remains pending.

**Authorized manual release, 29 October 2026:** v2.12.1 (code 24) is published from successful audited Android build `40770054545`, source `90bada583a242d76ca19efb4b59f3953432fa4b6`, APK SHA-256 `c3cf5cc53d99a61a35c8ebaa5e9ee0bbed9c3efdb24c874e988b4b15668c4edc`. All five draft assets were downloaded and byte-verified before promotion to latest. This one-off local publication did not enable automation or provision/store credentials in CI or either repository.

**Authorized manual release, 30 October 2026:** v2.13.0 (code 25) was published from successful audited Android build `40997958213`, source `cb5c2ad293e34df9433e94d21febcde2f389c22a`, APK SHA-256 `0f80cfa7358020f1153f60946c388e6f69023ac8e853f82f635b5506a28ff6e2`. The original immutable CI artifact and established signer were reverified. All five draft assets were downloaded and byte-compared before promotion; versioned/stable APKs and latest metadata were then verified anonymously. Native HiveMQ secure-WebSocket probes passed both prepared public hosts, including trusted TLS/hostname checks and anonymous MQTT authentication refusal. No phone installation, pairing changes, account rotation, CI credential provisioning or automation activation occurred. That release's two-pose calibration instructions are superseded by v2.13.1. Publication used the existing local signed-in GitHub CLI account without retaining a token in either repository or CI.

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
