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
if "import org.mozilla.geckoview.ContentBlocking" not in s:
    s = s.replace("import org.mozilla.geckoview.GeckoSession\n", "import org.mozilla.geckoview.GeckoSession\nimport org.mozilla.geckoview.ContentBlocking\n")
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


# ---- Blend the original animated mascot backdrop into the browser theme ----
import shutil as _shutil
import subprocess as _subprocess
import tempfile as _tempfile
import cv2 as _cv2
import numpy as _np

hero_video = root / "app/src/main/res/raw/swaga_hero.mp4"
if not hero_video.exists():
    raise SystemExit("Mascot source video not found: " + str(hero_video))
ffmpeg = _shutil.which("ffmpeg")
if not ffmpeg:
    raise SystemExit("ffmpeg is required to blend the mascot backdrop")

capture = _cv2.VideoCapture(str(hero_video))
fps = capture.get(_cv2.CAP_PROP_FPS)
if not fps or fps < 1:
    fps = 10.0
frame_index = 0
target_bgr = _np.array([18, 13, 11], dtype=_np.uint8)  # #0B0D12
with _tempfile.TemporaryDirectory(prefix="swaga-mascot-bg-") as temp_name:
    frame_dir = Path(temp_name)
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            dark = (_np.max(frame, axis=2) < 34).astype(_np.uint8)
            count, labels, stats, _ = _cv2.connectedComponentsWithStats(dark, 8)
            edge_labels = set()
            if count > 1:
                edge_labels.update(_np.unique(labels[0, :]).tolist())
                edge_labels.update(_np.unique(labels[-1, :]).tolist())
                edge_labels.update(_np.unique(labels[:, 0]).tolist())
                edge_labels.update(_np.unique(labels[:, -1]).tolist())
            background_mask = _np.isin(labels, list(edge_labels))
            background_mask &= dark.astype(bool)
            frame[background_mask] = target_bgr
            frame_path = frame_dir / ("frame_%05d.png" % frame_index)
            if not _cv2.imwrite(str(frame_path), frame):
                raise SystemExit("Could not write mascot frame " + str(frame_index))
            frame_index += 1
    finally:
        capture.release()

    if frame_index < 2:
        raise SystemExit("Mascot video did not contain enough frames")
    blended_video = frame_dir / "swaga_hero_blended.mp4"
    _subprocess.run(
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", ("%.3f" % fps),
            "-i", str(frame_dir / "frame_%05d.png"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(blended_video),
        ],
        check=True,
    )
    _shutil.copy2(blended_video, hero_video)

start_page = base / "ui/StartPage.kt"
hs = start_page.read_text(encoding="utf-8")
for line in [
    "import android.widget.ImageView\n",
    "import android.os.Build\n",
    "import android.graphics.drawable.Drawable\n",
    "import android.graphics.drawable.BitmapDrawable\n",
    "import android.graphics.drawable.AnimatedImageDrawable\n",
    "import android.graphics.ImageDecoder\n",
    "import android.graphics.BitmapFactory\n",
]:
    hs = hs.replace(line, "")
if "import android.net.Uri\n" not in hs:
    hs = hs.replace("package app.swaga.browser.ui\n", "package app.swaga.browser.ui\nimport android.net.Uri\n", 1)
if "import android.widget.VideoView\n" not in hs:
    hs = hs.replace("package app.swaga.browser.ui\n", "package app.swaga.browser.ui\nimport android.widget.VideoView\n", 1)
if "import androidx.compose.ui.graphics.toArgb\n" not in hs:
    hs = hs.replace("package app.swaga.browser.ui\n", "package app.swaga.browser.ui\nimport androidx.compose.ui.graphics.toArgb\n", 1)
hs = hs.replace("import androidx.compose.runtime.DisposableEffect\n", "")
import re as _re
hero_match = _re.search(r'(?m)^(?:@Suppress\("NewApi"\)\s*\n)?@Composable\s*\nprivate fun SwagaHeroVideo\(\)\s*\{', hs)
if not hero_match:
    raise SystemExit("SwagaHeroVideo composable was not found in StartPage.kt")
start_at = hero_match.start()
brace_at = hs.index("{", hero_match.start())
depth = 0
end_at = None
for pos in range(brace_at, len(hs)):
    if hs[pos] == "{":
        depth += 1
    elif hs[pos] == "}":
        depth -= 1
        if depth == 0:
            end_at = pos + 1
            break
if end_at is None:
    raise SystemExit("Could not find the end of SwagaHeroVideo composable")
new_hero = '''@Composable
private fun SwagaHeroVideo() {
    val c = LocalSwaga.current
    AndroidView(
        factory = { viewContext ->
            VideoView(viewContext).apply {
                setBackgroundColor(c.bg.toArgb())
                setVideoURI(Uri.parse("android.resource://" + viewContext.packageName + "/" + R.raw.swaga_hero))
                setOnPreparedListener { player ->
                    player.isLooping = true
                    player.setVolume(0f, 0f)
                    start()
                }
                setOnErrorListener { _, _, _ -> true }
            }
        },
        update = { videoView ->
            videoView.setBackgroundColor(c.bg.toArgb())
            if (!videoView.isPlaying) videoView.start()
        },
        modifier = Modifier.size(width = 92.dp, height = 92.dp),
    )
}
'''
hs = hs[:start_at] + new_hero + hs[end_at:]
start_page.write_text(hs, encoding="utf-8")

bottom_file = base / "ui/BottomBar.kt"
bs = bottom_file.read_text(encoding="utf-8")
if "Копировать ссылку без трекеров" not in bs:
    anchor = '''                DropdownMenuItem(
                    text = { Text("Копировать заголовок и адрес") },
'''
    if anchor not in bs:
        raise SystemExit("Clean-link menu insertion point not found")
    clean_item = '''                DropdownMenuItem(
                    text = { Text("Копировать ссылку без трекеров") },
                    enabled = onPage && !tab?.url.isNullOrBlank(),
                    onClick = {
                        menu = false
                        val original = tab?.url
                        if (!original.isNullOrBlank()) {
                            val parsed = Uri.parse(original)
                            val clean = parsed.buildUpon().clearQuery().apply {
                                parsed.queryParameterNames.forEach { key ->
                                    val lower = key.lowercase()
                                    val tracking = lower.startsWith("utm_") ||
                                        lower in setOf("fbclid", "gclid", "dclid", "msclkid", "igshid", "mc_cid", "mc_eid", "ref_src")
                                    if (!tracking) {
                                        parsed.getQueryParameters(key).forEach { value ->
                                            appendQueryParameter(key, value)
                                        }
                                    }
                                }
                            }.build().toString()
                            val clipboard = ctx.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as ClipboardManager
                            clipboard.setPrimaryClip(ClipData.newPlainText("Чистая ссылка", clean))
                            vm.message = if (clean == original) {
                                "Метки отслеживания не найдены."
                            } else {
                                "Ссылка без распространённых меток скопирована."
                            }
                        }
                    },
                )
'''
    bs = bs.replace(anchor, clean_item + anchor, 1)
bottom_file.write_text(bs, encoding="utf-8")

print("Restored full mascot video with theme-matched backdrop and added clean-link copy")
