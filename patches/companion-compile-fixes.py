from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: companion-compile-fixes.py <android-project-root>")

base = Path(sys.argv[1]).resolve() / "app/src/main/java/app/swaga/browser/ui"

bottom = base / "BottomBar.kt"
s = bottom.read_text(encoding="utf-8")
wrong = "import androidx.compose.animation.core.animateColorAsState"
right = "import androidx.compose.animation.animateColorAsState"
if wrong in s:
    s = s.replace(wrong, right, 1)
elif right not in s:
    raise SystemExit("BottomBar animateColorAsState import not found")
bottom.write_text(s, encoding="utf-8")

downloads = base / "DownloadsSheet.kt"
s = downloads.read_text(encoding="utf-8")
needed = "import androidx.compose.foundation.layout.fillMaxSize"
if needed not in s:
    anchor = "import androidx.compose.foundation.layout.fillMaxWidth"
    if anchor not in s:
        raise SystemExit("DownloadsSheet layout import anchor not found")
    s = s.replace(anchor, anchor + "\\n" + needed, 1)
downloads.write_text(s, encoding="utf-8")

print("Applied final Compose import fixes for address animation and MD3 download ring.")
