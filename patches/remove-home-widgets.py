from pathlib import Path
import re, sys
root = Path(sys.argv[1])
manifest = root/'app/src/main/AndroidManifest.xml'
text = manifest.read_text()
text = re.sub(r'\\s*<receiver\\s+android:name="\\.widgets\\.[^"]+".*?</receiver>', '', text, flags=re.S)
manifest.write_text(text)
widgets = root/'app/src/main/java/app/swaga/browser/widgets/SwagaWidgets.kt'
if widgets.exists(): widgets.unlink()
for folder in ('layout', 'xml', 'drawable'):
    base = root/'app/src/main/res'/folder
    if not base.exists(): continue
    for p in list(base.glob('widget_sw_*.xml')): p.unlink()
    if folder == 'drawable':
        for name in ('swaga_widget_bg.xml', 'swaga_widget_tile.xml', 'swaga_widget_pill.xml'):
            p = base/name
            if p.exists(): p.unlink()
package_dir = root/'app/src/main/java/app/swaga/browser/widgets'
if package_dir.exists():
    try: package_dir.rmdir()
    except OSError: pass
assert 'APPWIDGET_UPDATE' not in manifest.read_text(), 'Widget receiver remains in manifest'
assert not widgets.exists(), 'Widget provider source remains'
print('Home-screen widgets removed from manifest, Kotlin source and resources.')
