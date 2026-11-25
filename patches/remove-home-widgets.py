from pathlib import Path
import sys\nimport re
root = Path(sys.argv[1])
manifest = root/'app/src/main/AndroidManifest.xml'
lines = manifest.read_text().splitlines()
out, block = [], []
inside = False
for line in lines:
    if not inside and '<receiver' in line:
        inside = True
        block = [line]
    elif inside:
        block.append(line)
    else:
        out.append(line)
    if inside and '</receiver>' in line:
        chunk = '\n'.join(block)
        if '.widgets.' not in chunk:
            out.extend(block)
        block, inside = [], False
if inside:
    raise SystemExit('Unclosed receiver block in AndroidManifest.xml')
manifest.write_text('\n'.join(out)+'\n')
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
# Remove the updater calls left behind in browser services and lifecycle hooks.
for source in (root/'app/src/main/java').rglob('*.kt'):
    code = source.read_text()
    code = code.replace('import app.swaga.browser.widgets.SwagaWidgetUpdater\\n', '')
    code = re.sub(r'SwagaWidgetUpdater\\.refresh\\([^)]*\\)', '', code)
    source.write_text(code)

# combinedClickable is still experimental in the Compose version used by this project.
start_page = root/'app/src/main/java/app/swaga/browser/ui/StartPage.kt'
code = start_page.read_text()
if 'import androidx.compose.foundation.ExperimentalFoundationApi' not in code:
    code = code.replace('import androidx.compose.foundation.combinedClickable',
                        'import androidx.compose.foundation.combinedClickable\\nimport androidx.compose.foundation.ExperimentalFoundationApi')
code = code.replace('@Composable\\nprivate fun Tile(', '@OptIn(ExperimentalFoundationApi::class)\\n@Composable\\nprivate fun Tile(')
start_page.write_text(code)
assert 'APPWIDGET_UPDATE' not in manifest.read_text(), 'Widget receiver remains in manifest'
assert not widgets.exists(), 'Widget provider source remains'
print('Home-screen widgets removed from manifest, Kotlin source and resources.')
