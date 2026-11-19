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


# ---- Transparent animated mascot and small tab utilities ----
import shutil as _shutil
import subprocess as _subprocess
import tempfile as _tempfile

import cv2 as _cv2
import numpy as _np

# Cut the black video backdrop without damaging the dark outline of the nut.
# The source stays in the repository; CI deterministically regenerates the alpha WebP.
hero_video = root / "app/src/main/res/raw/swaga_hero.mp4"
hero_output = root / "app/src/main/res/raw/swaga_hero_transparent.webp"
if not hero_video.exists():
    raise SystemExit("Mascot source video not found: " + str(hero_video))
ffmpeg = _shutil.which("ffmpeg")
if not ffmpeg:
    raise SystemExit("ffmpeg is required to encode the transparent animated mascot")

capture = _cv2.VideoCapture(str(hero_video))
fps = capture.get(_cv2.CAP_PROP_FPS)
if not fps or fps < 1:
    fps = 10.0
frame_index = 0
with _tempfile.TemporaryDirectory(prefix="swaga-mascot-") as temp_name:
    frame_dir = Path(temp_name)
    try:
        while True:
            ok, bgr = capture.read()
            if not ok:
                break
            rgb = _cv2.cvtColor(bgr, _cv2.COLOR_BGR2RGB)
            candidate = (_np.max(rgb, axis=2) > 125).astype(_np.uint8)
            close_kernel = _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (3, 3))
            candidate = _cv2.morphologyEx(
                candidate, _cv2.MORPH_CLOSE, close_kernel, iterations=2
            )
            count, labels, stats, _ = _cv2.connectedComponentsWithStats(candidate, 8)
            if count <= 1:
                raise SystemExit("Could not isolate mascot in video frame " + str(frame_index))
            largest = 1 + int(_np.argmax(stats[1:, _cv2.CC_STAT_AREA]))
            mask = (labels == largest).astype(_np.uint8)
            outline_kernel = _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (5, 5))
            mask = _cv2.dilate(mask, outline_kernel, iterations=1)
            alpha = _cv2.GaussianBlur(mask.astype(_np.float32), (0, 0), 0.8)
            alpha = _np.uint8(_np.clip(alpha, 0.0, 1.0) * 255.0)
            rgba = _np.dstack((rgb, alpha))
            bgra = _cv2.cvtColor(rgba, _cv2.COLOR_RGBA2BGRA)
            frame_path = frame_dir / ("frame_%03d.png" % frame_index)
            if not _cv2.imwrite(str(frame_path), bgra):
                raise SystemExit("Could not write transparent mascot frame " + str(frame_index))
            frame_index += 1
    finally:
        capture.release()

    if frame_index < 2:
        raise SystemExit("Mascot video did not contain enough frames to animate")
    hero_output.parent.mkdir(parents=True, exist_ok=True)
    _subprocess.run(
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", ("%.3f" % fps),
            "-i", str(frame_dir / "frame_%03d.png"),
            "-vf", "scale=96:96:flags=lanczos",
            "-loop", "0", "-c:v", "libwebp_anim", "-lossless", "0",
            "-q:v", "75", "-compression_level", "6", "-an",
            str(hero_output),
        ],
        check=True,
    )
print("Created transparent animated mascot (%d frames, %d bytes)" % (
    frame_index, hero_output.stat().st_size
))

# Replace the opaque VideoView/card with the alpha-capable animated WebP.
start_page = base / "ui/StartPage.kt"
hs = start_page.read_text(encoding="utf-8")
hs = hs.replace("import android.net.Uri\n", "")
hs = hs.replace("import android.widget.VideoView\n", "")
new_imports = [
    "import android.graphics.BitmapFactory",
    "import android.graphics.ImageDecoder",
    "import android.graphics.drawable.AnimatedImageDrawable",
    "import android.graphics.drawable.BitmapDrawable",
    "import android.graphics.drawable.Drawable",
    "import android.os.Build",
    "import android.widget.ImageView",
]
for line in new_imports:
    if line not in hs:
        hs = hs.replace(
            "package app.swaga.browser.ui\n",
            "package app.swaga.browser.ui\n" + line + "\n",
            1,
        )
start_token = "@Composable\nprivate fun SwagaHeroVideo() {"
end_token = "\n@Composable\nprivate fun StartAction"
if start_token not in hs or end_token not in hs:
    raise SystemExit("SwagaHeroVideo replacement points not found")
start_at = hs.index(start_token)
end_at = hs.index(end_token, start_at)
new_hero = '''@Suppress("NewApi")
@Composable
private fun SwagaHeroVideo() {
    val context = LocalContext.current
    val mascot: Drawable = remember(context) {
        val animated = if (Build.VERSION.SDK_INT >= 28) {
            runCatching {
                ImageDecoder.decodeDrawable(
                    ImageDecoder.createSource(
                        context.resources,
                        R.raw.swaga_hero_transparent,
                    ),
                )
            }.getOrNull() as? AnimatedImageDrawable
        } else {
            null
        }
        animated?.apply {
            repeatCount = AnimatedImageDrawable.REPEAT_INFINITE
        } ?: BitmapDrawable(
            context.resources,
            BitmapFactory.decodeResource(context.resources, R.raw.swaga_hero_transparent),
        )
    }

    DisposableEffect(mascot) {
        (mascot as? AnimatedImageDrawable)?.start()
        onDispose { (mascot as? AnimatedImageDrawable)?.stop() }
    }

    AndroidView(
        factory = { viewContext ->
            ImageView(viewContext).apply {
                scaleType = ImageView.ScaleType.FIT_CENTER
                background = null
                setImageDrawable(mascot)
                contentDescription = "Анимированный орех Swaga"
            }
        },
        update = { imageView ->
            if (imageView.drawable !== mascot) imageView.setImageDrawable(mascot)
            (mascot as? AnimatedImageDrawable)?.let {
                if (!it.isRunning) it.start()
            }
        },
        modifier = Modifier.size(56.dp),
    )
}
'''
hs = hs[:start_at] + new_hero + hs[end_at:]
start_page.write_text(hs, encoding="utf-8")

# Duplicate the current normal tab and close every non-active tab from the tab switcher.
vm_file = base / "BrowserViewModel.kt"
vs = vm_file.read_text(encoding="utf-8")
if "fun duplicateTab(" not in vs:
    anchor = "    fun restoreClosedTab() {\n"
    addition = '''    fun duplicateTab(source: Tab? = activeTab) {
        if (ghostModeEnabled) return
        val current = source ?: return
        val url = current.url
        if (url.isNullOrBlank()) {
            message = "Нет страницы для дублирования."
            return
        }
        val duplicate = newTab(url)
        duplicate.desktopMode = current.desktopMode
        duplicate.textZoom = current.textZoom
        message = "Вкладка продублирована."
    }

    fun closeOtherTabs() {
        if (ghostModeEnabled) return
        val keep = activeTab ?: return
        val others = tabs.toList().filter { it.id != keep.id }
        if (others.isEmpty()) {
            message = "Других вкладок нет."
            return
        }
        others.forEach { closeTab(it) }
        activeTabId = keep.id
        persist()
        message = "Закрыто вкладок: " + others.size
    }

'''
    if anchor not in vs:
        raise SystemExit("BrowserViewModel restoreClosedTab insertion point not found")
    vs = vs.replace(anchor, addition + anchor, 1)
vm_file.write_text(vs, encoding="utf-8")

# Add one-tap duplicate, title/address copy, and local page-text copy actions.
bottom_file = base / "ui/BottomBar.kt"
bs = bottom_file.read_text(encoding="utf-8")
bookmark_anchor = '''                if (!vm.ghostModeEnabled) {
                    DropdownMenuItem(
                        text = { Text(if (vm.isBookmarked(tab?.url)) "Убрать из закладок" else "Добавить в закладки") },
'''
if "Дублировать вкладку" not in bs:
    if bookmark_anchor not in bs:
        raise SystemExit("BottomBar bookmark menu insertion point not found")
    duplicate_item = '''                DropdownMenuItem(
                    text = { Text("Дублировать вкладку") },
                    enabled = onPage && !vm.ghostModeEnabled,
                    onClick = { menu = false; vm.duplicateTab(tab) },
                )
'''
    bs = bs.replace(bookmark_anchor, duplicate_item + bookmark_anchor, 1)

copy_address_anchor = '''                DropdownMenuItem(
                    text = { Text("Ярлык на главный экран") },
'''
if "Копировать заголовок и адрес" not in bs:
    if copy_address_anchor not in bs:
        raise SystemExit("BottomBar shortcut menu insertion point not found")
    copy_items = '''                DropdownMenuItem(
                    text = { Text("Копировать заголовок и адрес") },
                    enabled = onPage,
                    onClick = {
                        menu = false
                        val current = tab
                        val url = current?.url
                        if (current != null && !url.isNullOrBlank()) {
                            val title = current.title.ifBlank { Uri.parse(url).host ?: "Страница" }
                            val clipboard = ctx.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as ClipboardManager
                            clipboard.setPrimaryClip(ClipData.newPlainText("Страница", "$title\\\\n$url"))
                            vm.message = "Заголовок и адрес скопированы."
                        }
                    },
                )
                DropdownMenuItem(
                    text = { Text("Копировать текст страницы") },
                    enabled = onPage,
                    onClick = {
                        menu = false
                        val current = tab
                        val target = current?.webView
                        if (target == null) {
                            vm.message = "Страница ещё загружается."
                        } else {
                            target.evaluateJavascript(
                                "(document.body?.innerText || document.documentElement?.innerText || '').slice(0, 30000)"
                            ) { raw ->
                                val pageText = runCatching {
                                    org.json.JSONTokener(raw ?: "null").nextValue() as? String
                                }.getOrNull()?.trim().orEmpty()
                                if (pageText.isBlank()) {
                                    vm.message = "На странице не найден доступный текст."
                                } else {
                                    val clipboard = ctx.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as ClipboardManager
                                    clipboard.setPrimaryClip(ClipData.newPlainText("Текст страницы", pageText))
                                    vm.message = if (pageText.length >= 30000) {
                                        "Скопированы первые 30 000 символов страницы."
                                    } else {
                                        "Текст страницы скопирован."
                                    }
                                }
                            }
                        }
                    },
                )
'''
    bs = bs.replace(copy_address_anchor, copy_items + copy_address_anchor, 1)

# Share title together with the page URL.
bs = bs.replace(
    'putExtra(Intent.EXTRA_TEXT, url)',
    'putExtra(Intent.EXTRA_TEXT, (tab?.title?.takeIf { it.isNotBlank() } ?: Uri.parse(url).host ?: "Страница") + "\\\\n" + url)',
)
bottom_file.write_text(bs, encoding="utf-8")

# Put the close-others action in the tab overview. Closed tabs remain restorable.
switcher_file = base / "ui/TabSwitcher.kt"
ts = switcher_file.read_text(encoding="utf-8")
restore_anchor = '''            if (vm.closedTabs.isNotEmpty()) {
                TextButton(onClick = { vm.restoreClosedTab(); onClose() }) {
                    Text("Вернуть закрытую", color = c.accent)
                }
            }
'''
if "Закрыть другие" not in ts:
    if restore_anchor not in ts:
        raise SystemExit("TabSwitcher restore button insertion point not found")
    ts = ts.replace(
        restore_anchor,
        restore_anchor + '''            if (vm.tabs.size > 1) {
                TextButton(onClick = { vm.closeOtherTabs() }) {
                    Text("Закрыть другие", color = c.accent)
                }
            }
''',
        1,
    )
switcher_file.write_text(ts, encoding="utf-8")

print("Added tab duplication, page-text copy, title/address copy, and close-other-tabs")
