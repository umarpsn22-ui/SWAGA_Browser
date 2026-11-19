import base64, gzip, io, tarfile
from pathlib import Path
root = Path(__file__).resolve().parents[1] / "android-project"
payload = base64.b64decode("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")
with tarfile.open(fileobj=io.BytesIO(gzip.decompress(payload)), mode="r:") as archive:
    archive.extractall(root)
base = root / "app/src/main/java/app/swaga/browser"
engine = base / "engine/SwagaWebView.kt"
s = engine.read_text()
s = s.replace("import app.swaga.browser.ProtectionStats\\n", "import app.swaga.browser.ProtectionStats\\nimport app.swaga.browser.DownloadsController\\n")
needle = """                override fun onTitleChange(session: GeckoSession, title: String?) {
                    if (!title.isNullOrBlank()) tab.title = title
                }
"""
replacement = needle + """
                override fun onExternalResponse(session: GeckoSession, response: org.mozilla.geckoview.WebResponse) {
                    DownloadsController.accept(context, response)
                }
"""
if "DownloadsController.accept(context, response)" not in s:
    if needle not in s: raise SystemExit("GeckoView download callback anchor missing")
    s = s.replace(needle, replacement, 1)
engine.write_text(s)
bottom = base / "ui/BottomBar.kt"
s = bottom.read_text()
s = s.replace("import app.swaga.browser.BrowserViewModel\\n", "import app.swaga.browser.BrowserViewModel\\nimport app.swaga.browser.DownloadsController\\n")
s = s.replace("    var showProtection by remember { mutableStateOf(false) }\\n", "    var showProtection by remember { mutableStateOf(false) }\\n    var showDownloads by remember { mutableStateOf(false) }\\n")
needle = '''                DropdownMenuItem(
                    text = { Text("Найти на странице") },
'''
insert = '''                DropdownMenuItem(
                    text = { Text("Загрузки") },
                    onClick = { menu = false; showDownloads = true },
                )
''' + needle
if "text = { Text(\"Загрузки\") }" not in s:
    if needle not in s: raise SystemExit("Downloads menu anchor missing")
    s = s.replace(needle, insert, 1)
s = s.replace("    if (showProtection) ProtectionSheet(vm = vm, tab = tab, onDismiss = { showProtection = false })\\n", "    if (showProtection) ProtectionSheet(vm = vm, tab = tab, onDismiss = { showProtection = false })\\n    if (showDownloads) DownloadsSheet(onDismiss = { showDownloads = false })\\n")
bottom.write_text(s)
print("Installed GeckoView download manager sources")
