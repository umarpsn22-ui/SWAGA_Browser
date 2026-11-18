from pathlib import Path
import re

root = Path("android-project")
app = root / "app"
java = app / "src/main/java/app/swaga/browser"
engine = java / "engine"
patches = Path("patches/geckoview")

# Install the GeckoView session adapter, Compose host, and privileged JS bridge.
(engine / "SwagaWebView.kt").write_text(
    (patches / "SwagaWebView.kt").read_text(encoding="utf-8"),
    encoding="utf-8",
)
(engine / "WebViewHost.kt").write_text(
    (patches / "WebViewHost.kt").read_text(encoding="utf-8"),
    encoding="utf-8",
)
extension_source = patches / "swaga_bridge"
extension_target = app / "src/main/assets/web_extensions/swaga_bridge"
extension_target.mkdir(parents=True, exist_ok=True)
for name in ("manifest.json", "bridge.js"):
    (extension_target / name).write_text(
        (extension_source / name).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

# Replace the platform WebView reference with the Gecko-backed tab adapter.
tab_path = java / "tabs/Tab.kt"
tab = tab_path.read_text(encoding="utf-8")
tab = tab.replace("import android.webkit.WebView\n", "")
tab = tab.replace(
    "import androidx.compose.runtime.setValue\n",
    "import androidx.compose.runtime.setValue\nimport app.swaga.browser.engine.SwagaGeckoTab\n",
)
tab = tab.replace("var webView: WebView? = null", "var webView: SwagaGeckoTab? = null\n    var ghostSession: Boolean = false")
tab = tab.replace("Состояние одной вкладки. WebView существует только у активной вкладки:", "Состояние одной вкладки. GeckoView существует только у активной вкладки:")
tab_path.write_text(tab, encoding="utf-8")

# Adapt the existing browser controls to GeckoView.
vm_path = java / "BrowserViewModel.kt"
vm = vm_path.read_text(encoding="utf-8")
vm = vm.replace("import android.webkit.CookieManager\n", "")
vm = vm.replace("import android.webkit.WebSettings\n", "")
if "import app.swaga.browser.engine.SwagaGeckoTab" not in vm:
    vm = vm.replace(
        "package app.swaga.browser\n",
        "package app.swaga.browser\n\nimport app.swaga.browser.engine.SwagaGeckoTab\n",
        1,
    )
vm = vm.replace("activeTab?.webView?.reload()", "activeTab?.webView?.setTrackingProtection(enabled)")
vm = vm.replace(
    """        CookieManager.getInstance().removeAllCookies(null)
        CookieManager.getInstance().flush()
        tabs.forEach { tab ->
            tab.webView?.apply {
                clearHistory()
                clearCache(true)
                clearFormData()
            }
            tab.savedState = null
        }""",
    """        SwagaGeckoTab.clearSiteData(getApplication())
        tabs.forEach { tab ->
            tab.webView?.apply {
                clearHistory()
                clearCache(true)
                clearFormData()
            }
            tab.savedState = null
        }""",
)
vm = vm.replace(
    """        webView.settings.userAgentString = if (tab.desktopMode) {
            app.swaga.browser.engine.SwagaWebView.desktopUserAgent(getApplication())
        } else {
            WebSettings.getDefaultUserAgent(getApplication())
        }
        message = if (tab.desktopMode) "Версия для компьютера включена." else "Мобильная версия включена."
        webView.reload()""",
    """        webView.setDesktopMode(tab.desktopMode)
        message = if (tab.desktopMode) "Версия для компьютера включена." else "Мобильная версия включена." """,
)
vm = vm.replace(
    """            // WebView's cookie switch is process-wide. The app has one live WebView at a time.
            CookieManager.getInstance().setAcceptCookie(false)
            tab.webView?.apply {
                settings.domStorageEnabled = false
                settings.cacheMode = WebSettings.LOAD_NO_CACHE
                clearHistory()
                clearCache(true)
                clearFormData()
            }
            tab.savedState = null""",
    """            tab.ghostSession = true
            tab.webView?.setPrivateMode(true)
            tab.webView?.clearHistory()
            tab.savedState = null""",
)
vm = vm.replace(
    """            CookieManager.getInstance().setAcceptCookie(true)
            tab.webView?.apply {
                settings.domStorageEnabled = true
                settings.cacheMode = WebSettings.LOAD_DEFAULT
                clearHistory()
            }
            val returnUrl = restoreUrlAfterGhost""",
    """            tab.ghostSession = false
            tab.webView?.setPrivateMode(false)
            tab.webView?.clearHistory()
            val returnUrl = restoreUrlAfterGhost""",
)
if "CookieManager" in vm or "WebSettings" in vm:
    raise SystemExit("Legacy WebView imports/references remain in BrowserViewModel")
if "setPrivateMode(true)" not in vm or "setPrivateMode(false)" not in vm:
    raise SystemExit("Ghost Mode was not connected to Gecko private sessions")
vm_path.write_text(vm, encoding="utf-8")

# Add Mozilla's official Maven repository and the stable GeckoView artifact.
settings_path = root / "settings.gradle.kts"
settings = settings_path.read_text(encoding="utf-8")
if "https://maven.mozilla.org/maven2/" not in settings:
    marker = "dependencyResolutionManagement {"
    head, tail = settings.split(marker, 1)
    tail = tail.replace(
        "repositories {\n        google()\n        mavenCentral()\n",
        "repositories {\n        maven { url = uri(\"https://maven.mozilla.org/maven2/\") }\n        google()\n        mavenCentral()\n",
        1,
    )
    settings = head + marker + tail
settings_path.write_text(settings, encoding="utf-8")

gradle_path = app / "build.gradle.kts"
gradle = gradle_path.read_text(encoding="utf-8")
gradle = re.sub(r"compileSdk\s*=\s*\d+", "compileSdk = 36", gradle, count=1)
if "org.mozilla.geckoview:geckoview:" not in gradle:
    gradle = gradle.replace(
        'dependencies {\n',
        'dependencies {\n    implementation("org.mozilla.geckoview:geckoview:139.0.20250609112858")\n',
        1,
    )
gradle = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 3', gradle, count=1)
gradle = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.1.0-gecko"', gradle, count=1)
gradle_path.write_text(gradle, encoding="utf-8")

# Keep Kotlin Android and the Kotlin 2.x Compose compiler plugin on the same version.
root_gradle_path = root / "build.gradle.kts"
root_gradle = root_gradle_path.read_text(encoding="utf-8")
root_gradle = root_gradle.replace(
    'id("com.android.application") version "8.5.2"',
    'id("com.android.application") version "8.9.1"',
)
root_gradle = re.sub(
    r'id\("org\.jetbrains\.kotlin\.android"\)\s+version\s+"[^"]+"',
    'id("org.jetbrains.kotlin.android") version "2.2.20"',
    root_gradle,
    count=1,
)
root_gradle = re.sub(
    r'id\("org\.jetbrains\.kotlin\.plugin\.compose"\)\s+version\s+"[^"]+"',
    'id("org.jetbrains.kotlin.plugin.compose") version "2.2.20"',
    root_gradle,
    count=1,
)
if 'id("org.jetbrains.kotlin.plugin.compose") version "2.2.20"' not in root_gradle:
    raise SystemExit("Could not align Compose compiler plugin with Kotlin 2.2.20")
root_gradle_path.write_text(root_gradle, encoding="utf-8")

# Ensure the platform WebView and unsupported evaluateJS call are gone.
active = "\n".join(p.read_text(encoding="utf-8") for p in java.rglob("*.kt"))
if "android.webkit.WebView" in active or "WebViewClient" in active or "WebChromeClient" in active:
    raise SystemExit("A platform WebView dependency remains in active Kotlin source")
if "evaluateJS(" in active:
    raise SystemExit("Unsupported GeckoSession.evaluateJS call remains")
if "SwagaGeckoTab" not in active or "org.mozilla.geckoview" not in active:
    raise SystemExit("GeckoView integration did not land")
if not (extension_target / "manifest.json").exists() or not (extension_target / "bridge.js").exists():
    raise SystemExit("Bundled GeckoView JavaScript bridge was not installed")
print("GeckoView migration applied with Kotlin/Compose plugin versions aligned at 2.2.20.")
