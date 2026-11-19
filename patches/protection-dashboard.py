from pathlib import Path
import sys

root = Path(sys.argv[1])
base = root / "app/src/main/java/app/swaga/browser"

(base / "ProtectionStats.kt").write_text("""package app.swaga.browser

import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/** Counts only tracker-block events reported by GeckoView in this app process. */
object ProtectionStats {
    var blockedTotal by mutableIntStateOf(0)
        private set
    var lastBlockedHost by mutableStateOf("")
        private set
    private val perSite = mutableStateMapOf<String, Int>()

    fun record(blockedUri: String, pageUrl: String?) {
        val pageHost = Uri.parse(pageUrl.orEmpty()).host?.lowercase().orEmpty()
        val blockedHost = Uri.parse(blockedUri).host?.lowercase().orEmpty()
        blockedTotal += 1
        if (pageHost.isNotBlank()) perSite[pageHost] = (perSite[pageHost] ?: 0) + 1
        if (blockedHost.isNotBlank()) lastBlockedHost = blockedHost
    }

    fun blockedFor(url: String?): Int {
        val host = Uri.parse(url.orEmpty()).host?.lowercase().orEmpty()
        return if (host.isBlank()) 0 else perSite[host] ?: 0
    }
}
""", encoding="utf-8")

engine = base / "engine/SwagaWebView.kt"
s = engine.read_text(encoding="utf-8")
if "import app.swaga.browser.ProtectionStats" not in s:
    s = s.replace("import app.swaga.browser.tabs.Tab\n", "import app.swaga.browser.tabs.Tab\nimport app.swaga.browser.ProtectionStats\n")
needle = """            created.setContentDelegate(object : GeckoSession.ContentDelegate {
                override fun onTitleChange(session: GeckoSession, title: String?) {
                    if (!title.isNullOrBlank()) tab.title = title
                }
            })
"""
if "setContentBlockingDelegate" not in s:
    if needle not in s:
        raise SystemExit("GeckoSession delegate insertion point not found")
    s = s.replace(needle, needle + """            created.setContentBlockingDelegate(object : ContentBlocking.Delegate {
                override fun onContentBlocked(
                    session: GeckoSession,
                    event: ContentBlocking.BlockEvent
                ) {
                    ProtectionStats.record(event.uri, tab.url)
                }
            })
""", 1)
engine.write_text(s, encoding="utf-8")

bottom = base / "ui/BottomBar.kt"
s = bottom.read_text(encoding="utf-8")
if "import app.swaga.browser.ProtectionStats" not in s:
    s = s.replace("import app.swaga.browser.BrowserViewModel\n", "import app.swaga.browser.BrowserViewModel\nimport app.swaga.browser.ProtectionStats\n")
anchor = "        GhostModeButton(active = vm.ghostModeEnabled, onClick = vm::toggleGhostMode)\n\n"
if "clickable { showProtection = true }" not in s:
    if anchor not in s: raise SystemExit("Ghost button insertion point not found")
    s = s.replace(anchor, anchor + """        Row(
            Modifier.clip(RoundedCornerShape(16.dp))
                .clickable { showProtection = true }
                .padding(horizontal = 7.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Icon(Icons.Filled.Lock, contentDescription = "SwagaGuard",
                tint = if (vm.trackingProtectionEnabled) c.accent else c.dim,
                modifier = Modifier.size(16.dp))
            Text(ProtectionStats.blockedTotal.toString(), color = c.text,
                fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
        }

""", 1)
if "var showProtection by remember" not in s:
    s = s.replace("    var findQuery by remember { mutableStateOf(\"\") }\n",
                  "    var findQuery by remember { mutableStateOf(\"\") }\n    var showProtection by remember { mutableStateOf(false) }\n", 1)
if "if (showProtection) ProtectionSheet" not in s:
    s = s.replace("    if (showFind) {\n",
                  "    if (showProtection) ProtectionSheet(vm = vm, tab = tab, onDismiss = { showProtection = false })\n\n    if (showFind) {", 1)
bottom.write_text(s, encoding="utf-8")

(base / "ui/ProtectionSheet.kt").write_text("""package app.swaga.browser.ui

import android.os.SystemClock
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.swaga.browser.BrowserViewModel
import app.swaga.browser.ProtectionStats
import app.swaga.browser.tabs.Tab
import app.swaga.browser.themes.LocalSwaga
import kotlinx.coroutines.delay

@Composable
fun ProtectionSheet(vm: BrowserViewModel, tab: Tab?, onDismiss: () -> Unit) {
    val c = LocalSwaga.current
    var elapsed by remember(tab?.id, tab?.url) { mutableLongStateOf(0L) }
    LaunchedEffect(tab?.id, tab?.url, tab?.pageStartedAtElapsed) {
        val start = tab?.pageStartedAtElapsed ?: SystemClock.elapsedRealtime()
        while (true) {
            elapsed = ((SystemClock.elapsedRealtime() - start) / 1000L).coerceAtLeast(0L)
            delay(1000L)
        }
    }
    val h = elapsed / 3600
    val m = (elapsed % 3600) / 60
    val sec = elapsed % 60
    val clock = "%02d:%02d:%02d".format(h, m, sec)

    AppSheet(onDismiss) {
        Column(
            Modifier.fillMaxWidth().verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp).padding(bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text("SwagaGuard", fontSize = 21.sp, fontWeight = FontWeight.SemiBold)
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text("Защита от трекеров", fontWeight = FontWeight.Medium)
                    Text(if (vm.trackingProtectionEnabled) "Включена в GeckoView" else "Выключена",
                        color = c.dim, fontSize = 12.sp)
                }
                Switch(checked = vm.trackingProtectionEnabled, onCheckedChange = vm::setTrackingProtection)
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Metric("Заблокировано", ProtectionStats.blockedTotal.toString(), Modifier.weight(1f))
                Metric("На этом сайте", ProtectionStats.blockedFor(tab?.url).toString(), Modifier.weight(1f))
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Metric("Время на сайте", clock, Modifier.weight(1f))
                Metric("Статус", if (vm.trackingProtectionEnabled) "Активна" else "Отключена", Modifier.weight(1f))
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Последний заблокированный домен", color = c.dim, fontSize = 12.sp)
                Text(ProtectionStats.lastBlockedHost.ifBlank { "Пока нет событий" }, fontSize = 14.sp)
            }
            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text("Как работает счётчик", fontWeight = FontWeight.Medium)
                Text("Счётчик получает реальные события блокировки известных трекеров от GeckoView и обновляется во время загрузки страниц.",
                    color = c.dim, fontSize = 12.sp)
                Text("Это встроенная защита от трекеров, а не полный набор AdGuard/EasyList. Обычные рекламные баннеры и косметические элементы могут оставаться. Счётчик не добавляет неподтверждённые блокировки.",
                    color = c.dim, fontSize = 12.sp)
            }
            Button(onClick = onDismiss, modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = c.surface, contentColor = c.text)) {
                Text("Готово")
            }
        }
    }
}

@Composable
private fun Metric(label: String, value: String, modifier: Modifier = Modifier) {
    val c = LocalSwaga.current
    Column(modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
        Text(label, color = c.dim, fontSize = 11.sp)
        Text(value, color = c.text, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
    }
}
""", encoding="utf-8")


# Track the actual page start time reported by GeckoView.
tabFile = base / "tabs/Tab.kt"
ts = tabFile.read_text(encoding="utf-8")
if "mutableLongStateOf" not in ts:
    ts = ts.replace("import androidx.compose.runtime.mutableIntStateOf\n", "import androidx.compose.runtime.mutableIntStateOf\nimport androidx.compose.runtime.mutableLongStateOf\n")
if "pageStartedAtElapsed" not in ts:
    ts = ts.replace("    var progress by mutableIntStateOf(0)\n", "    var progress by mutableIntStateOf(0)\n    var pageStartedAtElapsed by mutableLongStateOf(android.os.SystemClock.elapsedRealtime())\n")
tabFile.write_text(ts, encoding="utf-8")

engineFile = base / "engine/SwagaWebView.kt"
es = engineFile.read_text(encoding="utf-8")
needle = "                override fun onPageStart(session: GeckoSession, url: String) {\n                    tab.loading = true"
if "tab.pageStartedAtElapsed =" not in es:
    if needle not in es:
        raise SystemExit("GeckoView page-start hook not found")
    es = es.replace(needle, "                override fun onPageStart(session: GeckoSession, url: String) {\n                    tab.pageStartedAtElapsed = android.os.SystemClock.elapsedRealtime()\n                    tab.loading = true", 1)
engineFile.write_text(es, encoding="utf-8")

print("Applied SwagaGuard live tracker dashboard")
