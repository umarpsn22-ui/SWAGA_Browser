from pathlib import Path
import re
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: python3 patches/swaga-premium-ux.py <android-project-root>")

root = Path(sys.argv[1]).resolve()
app = root / "app"
source = Path(__file__).resolve().parent / "premium-src" / "app" / "src" / "main" / "java"
destination = app / "src" / "main" / "java"

if not (app / "build.gradle.kts").is_file():
    raise SystemExit("Android app module not found")
if not (destination / "app/swaga/browser/engine/SwagaWebView.kt").is_file():
    raise SystemExit("GeckoView adapter missing; refusing to apply Swaga premium UI")
if not source.is_dir():
    raise SystemExit("Premium Kotlin source overlay is missing")

copied = []
for item in sorted(source.rglob("*.kt")):
    relative = item.relative_to(source)
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(item, target)
    copied.append(relative.as_posix())

required = {
    "app/swaga/browser/vpn/SwagaVpnManager.kt",
    "app/swaga/browser/vpn/SwagaVpnSheet.kt",
    "app/swaga/browser/ai/SwagaAiCore.kt",
    "app/swaga/browser/ai/SwagaAiSheet.kt",
    "app/swaga/browser/ui/BrowserApp.kt",
    "app/swaga/browser/ui/BottomBar.kt",
}
missing = required.difference(copied)
if missing:
    raise SystemExit("Missing premium source files: " + ", ".join(sorted(missing)))

gradle = app / "build.gradle.kts"
content = gradle.read_text(encoding="utf-8")
content, code_count = re.subn(r"versionCode\s*=\s*\d+", "versionCode = 5", content, count=1)
content, name_count = re.subn(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.3.0-vpn-ai"', content, count=1)
if code_count != 1 or name_count != 1:
    raise SystemExit("Could not update the app version safely")
gradle.write_text(content, encoding="utf-8")

manifest = app / "src/main/AndroidManifest.xml"
manifest_text = manifest.read_text(encoding="utf-8")
if "android.permission.INTERNET" not in manifest_text:
    raise SystemExit("INTERNET permission is required for Swaga_AI API providers")

print("Applied Swaga VPN Control Center and Swaga_AI.")
print("Copied Kotlin sources:")
for name in copied:
    print(" - " + name)
print("Set app version to 1.3.0-vpn-ai (versionCode 5).")
