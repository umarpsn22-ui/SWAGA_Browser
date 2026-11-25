from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
vm = root / "app/src/main/java/app/swaga/browser/BrowserViewModel.kt"
source = vm.read_text(encoding="utf-8")
for old, new in {
    "setTextMotionEnabled": "updateTextMotionEnabled",
    "setLiquidCursorEnabled": "updateLiquidCursorEnabled",
    "setMd3DownloadEnabled": "updateMd3DownloadEnabled",
    "setMd3WaveEnabled": "updateMd3WaveEnabled",
    "setMd3TrackEnabled": "updateMd3TrackEnabled",
    "setMediaControlsEnabled": "updateMediaControlsEnabled",
}.items():
    source = source.replace(f"fun {old}(", f"fun {new}(")
vm.write_text(source, encoding="utf-8")
print("Resolved legacy ViewModel setter JVM signature clashes.")
