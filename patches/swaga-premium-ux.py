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

# Kotlin compile corrections for expression bodies and the multiline system prompt.
ai_core = destination / "app/swaga/browser/ai/SwagaAiCore.kt"
ai_text = ai_core.read_text(encoding="utf-8")
ai_fixes = [
    ('private const val SYSTEM_PROMPT = """', 'private val SYSTEM_PROMPT = """'),
    ("        content.trim()\n    }\n\n    private fun completeGemini", "        return content.trim()\n    }\n\n    private fun completeGemini"),
    ("        answer\n    }\n\n    suspend fun loadOpenRouterFreeModels", "        return answer\n    }\n\n    suspend fun loadOpenRouterFreeModels"),
    ("            response\n        } finally", "            return response\n        } finally"),
]
for before, after in ai_fixes:
    if before not in ai_text:
        raise SystemExit("Expected Swaga_AI Kotlin fix site not found: " + before[:70])
    ai_text = ai_text.replace(before, after, 1)
ai_core.write_text(ai_text, encoding="utf-8")

gradle = app / "build.gradle.kts"
gradle_text = gradle.read_text(encoding="utf-8")
gradle_text, code_count = re.subn(r"versionCode\s*=\s*\d+", "versionCode = 5", gradle_text, count=1)
gradle_text, name_count = re.subn(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.3.0-vpn-ai"', gradle_text, count=1)
if code_count != 1 or name_count != 1:
    raise SystemExit("Could not update the app version safely")
gradle.write_text(gradle_text, encoding="utf-8")

manifest = app / "src/main/AndroidManifest.xml"
manifest_text = manifest.read_text(encoding="utf-8")
if "android.permission.INTERNET" not in manifest_text:
    raise SystemExit("INTERNET permission is required for Swaga_AI API providers")

print("Applied Swaga VPN Control Center and Swaga_AI.")
print("Copied Kotlin sources:")
for name in copied:
    print(" - " + name)
print("Set app version to 1.3.0-vpn-ai (versionCode 5).")
