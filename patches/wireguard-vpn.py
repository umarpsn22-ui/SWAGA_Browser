from pathlib import Path
import re
import shutil
import sys

root = Path(sys.argv[1])
app = root / "app"
src = root / "patches/vpn-src"
dst = app / "src/main/java/app/swaga/browser/vpn"
dst.mkdir(parents=True, exist_ok=True)
for name in ("VpnConfigStore.kt", "SwagaVpnManager.kt", "SwagaVpnSheet.kt", "VpnState.kt"):
    shutil.copy2(src / name, dst / name)

gradle = app / "build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if "com.wireguard.android:tunnel" not in g:
    g = g.replace(
        '    implementation("org.mozilla.geckoview:geckoview:139.0.20250609112858")',
        '    implementation("org.mozilla.geckoview:geckoview:139.0.20250609112858")\n'
        '    implementation("com.wireguard.android:tunnel:1.0.20260102")\n'
        '    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")'
    )
if "isCoreLibraryDesugaringEnabled = true" not in g:
    g = g.replace(
        "        targetCompatibility = JavaVersion.VERSION_17\n",
        "        targetCompatibility = JavaVersion.VERSION_17\n        isCoreLibraryDesugaringEnabled = true\n"
    )
gradle.write_text(g, encoding="utf-8")

manifest = app / "src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
m = re.sub(r'\s*<service\s+android:name="\.vpn\.SwagaVpnService".*?</service>\s*', "\n", m, flags=re.S)
manifest.write_text(m, encoding="utf-8")

for name in ("VpnProvider.kt", "VpnProviderRegistry.kt", "SwagaVpnService.kt"):
    stale = dst / name
    if stale.exists():
        stale.unlink()

sheets = app / "src/main/java/app/swaga/browser/ui/Sheets.kt"
s = sheets.read_text(encoding="utf-8")
if "import app.swaga.browser.vpn.SwagaVpnSheet" not in s:
    s = s.replace(
        "import app.swaga.browser.themes.panel\n",
        "import app.swaga.browser.themes.panel\nimport app.swaga.browser.vpn.SwagaVpnSheet\n"
    )
if "var showVpn by remember" not in s:
    s = s.replace(
        "    val context = LocalContext.current\n",
        "    val context = LocalContext.current\n    var showVpn by remember { mutableStateOf(false) }\n",
        1
    )
if 'Group("Встроенный VPN")' not in s:
    s = s.replace(
        '            Group("Приватность") {',
        '''            Group("Встроенный VPN") {
                Text("Настоящий WireGuard-туннель только для SwagaBrowser. Импортируй профиль Proton VPN, Windscribe или другого совместимого провайдера.", color = c.dim, fontSize = 12.sp)
                Button(
                    onClick = { showVpn = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = c.accent, contentColor = c.onAccent),
                ) { Text("Открыть Swaga VPN") }
            }
            Group("Приватность") {''',
        1
    )
needle = "    }\n}\n\n@Composable\nprivate fun Group"
if needle in s and "if (showVpn) SwagaVpnSheet" not in s:
    s = s.replace(
        needle,
        "    }\n    if (showVpn) SwagaVpnSheet(onDismiss = { showVpn = false })\n}\n\n@Composable\nprivate fun Group",
        1
    )
sheets.write_text(s, encoding="utf-8")

engine = app / "src/main/java/app/swaga/browser/engine/SwagaWebView.kt"
if not engine.exists() or "GeckoSession" not in engine.read_text(encoding="utf-8"):
    raise SystemExit("GeckoView session adapter missing; refusing VPN patch")
if "org.mozilla.geckoview:geckoview" not in g:
    raise SystemExit("GeckoView dependency missing")
print("Embedded WireGuard tunnel, encrypted profile import and browser-only routing applied.")
