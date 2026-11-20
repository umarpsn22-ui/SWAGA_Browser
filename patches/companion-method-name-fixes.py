from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: companion-method-name-fixes.py <android-project-root>")

base = Path(sys.argv[1]).resolve() / "app/src/main/java/app/swaga/browser"
mapping = {
    "setMascotEnabled": "updateMascotEnabled",
    "setMascotMovementEnabled": "updateMascotMovementEnabled",
    "setTextMotionEnabled": "updateTextMotionEnabled",
    "setLiquidCursorEnabled": "updateLiquidCursorEnabled",
    "setMd3DownloadEnabled": "updateMd3DownloadEnabled",
    "setMd3WaveEnabled": "updateMd3WaveEnabled",
    "setMd3TrackEnabled": "updateMd3TrackEnabled",
    "setMediaControlsEnabled": "updateMediaControlsEnabled",
}

vm = base / "BrowserViewModel.kt"
s = vm.read_text(encoding="utf-8")
for old, new in mapping.items():
    declaration = f"fun {old}(value: Boolean)"
    if declaration in s:
        s = s.replace(declaration, f"fun {new}(value: Boolean)", 1)
    elif f"fun {new}(value: Boolean)" not in s:
        raise SystemExit(f"Missing ViewModel method: {old}")
vm.write_text(s, encoding="utf-8")

for rel in ["ui/Sheets.kt", "ui/SwagaCompanionUi.kt"]:
    p = base / rel
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    for old, new in mapping.items():
        s = s.replace(f"vm::{old}", f"vm::{new}")
    p.write_text(s, encoding="utf-8")

print("Renamed companion preference methods to avoid JVM property-setter clashes.")
