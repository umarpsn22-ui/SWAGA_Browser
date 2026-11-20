# SwagaBrowser release signing

Distributable release APKs must use one persistent Android signing key. Never commit the keystore or its passwords to this repository.

## GitHub Actions secrets

Create these four repository secrets in **Settings → Secrets and variables → Actions**:

- `SWAGA_KEYSTORE_BASE64`: one-line Base64 encoding of the `swaga-release.jks` file.
- `SWAGA_KEYSTORE_PASSWORD`: keystore password.
- `SWAGA_KEY_ALIAS`: key alias (for the generated project key: `swaga-release`).
- `SWAGA_KEY_PASSWORD`: private-key password.

On macOS, after downloading the keystore, copy its Base64 value with:

```bash
base64 -i ~/Downloads/swaga-release.jks | tr -d '\n' | pbcopy
```

Paste that value into the `SWAGA_KEYSTORE_BASE64` secret. Add the other three secrets separately. Do not paste the keystore or passwords into source files, issues, pull requests, or chat logs.

Then run **Actions → Build SwagaBrowser APK → Run workflow**. When all secrets are present, the workflow signs the release APK with the persistent key and verifies its signature. Without the key, CI only creates a debug compile-check artifact; that artifact is deliberately not labelled or published as an update APK.

## One-time transition from old beta builds

Earlier CI beta APKs were signed with GitHub runner debug keys. Those private keys were not retained, so they cannot be reused for an update. Android will reject a new persistent-key APK as an in-place update over one of those older installations. The old beta must be uninstalled once before installing the first persistent-key release. Uninstalling clears local app data; export anything important first if the installed app provides an export option. Every release after the transition will use the same key and install as a normal update.
