from pathlib import Path
import sys

root = Path(sys.argv[1])
base = root / "app/src/main/java/app/swaga/browser"

bottom = base / "ui/BottomBar.kt"
s = bottom.read_text(encoding="utf-8")
start = s.index('            ) {\n                if (!vm.ghostModeEnabled) {', s.index('DropdownMenu('))
end_marker = '\n            }\n        }\n    }\n\n    if (showFind)'
end = s.index(end_marker, start)
replacement = """            ) {
                DropdownMenuItem(
                    text = { Text("Вперёд") },
                    enabled = tab?.canGoForward == true,
                    onClick = { menu = false; tab?.webView?.goForward() },
                )
                DropdownMenuItem(
                    text = { Text(if (tab?.loading == true) "Остановить загрузку" else "Обновить страницу") },
                    enabled = onPage,
                    onClick = {
                        menu = false
                        if (tab?.loading == true) tab.webView?.stopLoading() else tab?.webView?.reload()
                    },
                )
                if (!vm.ghostModeEnabled) {
                    DropdownMenuItem(
                        text = { Text(if (vm.isBookmarked(tab?.url)) "Убрать из закладок" else "Добавить в закладки") },
                        enabled = onPage,
                        onClick = { menu = false; vm.toggleBookmark(tab) },
                    )
                }
                DropdownMenuItem(
                    text = { Text("Найти на странице") },
                    enabled = onPage,
                    onClick = { menu = false; findQuery = ""; showFind = true },
                )
                DropdownMenuItem(
                    text = { Text("Режим чтения") },
                    enabled = onPage,
                    onClick = { menu = false; onReader() },
                )
                DropdownMenuItem(
                    text = { Text(if (tab?.desktopMode == true) "Мобильная версия" else "Версия для компьютера") },
                    enabled = onPage,
                    onClick = { menu = false; tab?.let(vm::toggleDesktopMode) },
                )
                DropdownMenuItem(
                    text = { Text("Перевести страницу") },
                    enabled = onPage && !tab?.url.isNullOrBlank(),
                    onClick = {
                        menu = false
                        val url = tab?.url
                        if (!url.isNullOrBlank()) vm.submit("https://translate.google.com/translate?sl=auto&tl=ru&u=${Uri.encode(url)}")
                    },
                )
                DropdownMenuItem(
                    text = { Text("Поделиться ссылкой") },
                    enabled = onPage,
                    onClick = {
                        menu = false
                        val url = tab?.url
                        if (url != null) {
                            val send = Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_TEXT, url)
                            }
                            ctx.startActivity(Intent.createChooser(send, null))
                        }
                    },
                )
                DropdownMenuItem(
                    text = { Text("Копировать адрес") },
                    enabled = onPage,
                    onClick = {
                        menu = false
                        val url = tab?.url
                        if (!url.isNullOrBlank()) {
                            val clipboard = ctx.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as ClipboardManager
                            clipboard.setPrimaryClip(ClipData.newPlainText("Адрес страницы", url))
                            vm.message = "Адрес скопирован."
                        }
                    },
                )
            }"""
s = s[:start] + replacement + s[end + len("\n            }"):]
bottom.write_text(s, encoding="utf-8")

sheets = base / "ui/Sheets.kt"
s = sheets.read_text(encoding="utf-8")
s = s.replace("import androidx.compose.ui.unit.sp\n", "import androidx.compose.ui.unit.sp\nimport android.app.DownloadManager\nimport android.content.Intent\nimport androidx.compose.ui.platform.LocalContext\n")
s = s.replace(
    "fun SettingsSheet(vm: BrowserViewModel, onDismiss: () -> Unit, onEngines: () -> Unit) {\n    val c = LocalSwaga.current",
    """fun SettingsSheet(
    vm: BrowserViewModel,
    onDismiss: () -> Unit,
    onEngines: () -> Unit,
    onBookmarks: () -> Unit,
    onHistory: () -> Unit,
) {
    val c = LocalSwaga.current
    val context = LocalContext.current"""
)
old = """            Group("Защита от трекеров") {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                        Text("Блокировать известные трекеры и рекламные запросы", fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text("Локальный список доменов. Некоторые сайты могут загружаться иначе.", color = c.dim, fontSize = 12.sp)
                    }
                    Switch(checked = vm.trackingProtectionEnabled, onCheckedChange = vm::setTrackingProtection)
                }
            }
"""
new = """            Group("Блокировка рекламы и трекеров") {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                        Text("Защита от известных трекеров", fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text("Встроенная защита GeckoView блокирует известные отслеживающие ресурсы. Это не полный фильтр AdGuard: часть рекламы может оставаться.", color = c.dim, fontSize = 12.sp)
                    }
                    Switch(checked = vm.trackingProtectionEnabled, onCheckedChange = vm::setTrackingProtection)
                }
                Text(
                    if (vm.trackingProtectionEnabled) "Защита включена" else "Защита выключена",
                    color = if (vm.trackingProtectionEnabled) c.accent else c.dim,
                    fontSize = 12.sp,
                )
            }
            Group("Вкладки и библиотека") {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { vm.newTab(); onDismiss() },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = c.surface, contentColor = c.text),
                    ) { Text("Новая вкладка") }
                    Button(
                        onClick = { vm.restoreClosedTab(); onDismiss() },
                        modifier = Modifier.weight(1f),
                        enabled = vm.closedTabs.isNotEmpty(),
                        colors = ButtonDefaults.buttonColors(containerColor = c.surface, contentColor = c.text),
                    ) { Text("Восстановить") }
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { onDismiss(); onBookmarks() },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = c.surface, contentColor = c.text),
                    ) { Text("Закладки") }
                    Button(
                        onClick = { onDismiss(); onHistory() },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = c.surface, contentColor = c.text),
                    ) { Text("История") }
                }
                Button(
                    onClick = { onDismiss(); runCatching { context.startActivity(Intent(DownloadManager.ACTION_VIEW_DOWNLOADS)) } },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = c.surface, contentColor = c.text),
                ) { Text("Загрузки") }
            }
"""
if old not in s:
    raise SystemExit("Tracking protection settings block not found")
s = s.replace(old, new, 1)
sheets.write_text(s, encoding="utf-8")

app = base / "ui/BrowserApp.kt"
s = app.read_text(encoding="utf-8")
old = """            SettingsSheet(
                vm = vm,
                onDismiss = { showSettings = false },
                onEngines = { showSettings = false; showEngines = true },
            )"""
new = """            SettingsSheet(
                vm = vm,
                onDismiss = { showSettings = false },
                onEngines = { showSettings = false; showEngines = true },
                onBookmarks = { showBookmarks = true },
                onHistory = { showHistory = true },
            )"""
if old not in s:
    raise SystemExit("SettingsSheet call site not found")
s = s.replace(old, new, 1)
app.write_text(s, encoding="utf-8")

print("Compact website menu, moved global tab/library actions into Settings, and clarified GeckoView tracker protection.")
