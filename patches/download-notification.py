from pathlib import Path

root = Path("android-project")
base = root / "app/src/main/java/app/swaga/browser"

downloads = base / "Downloads.kt"
s = downloads.read_text(encoding="utf-8")
if "var bannerItem by mutableStateOf<DownloadItem?>(null)" not in s:
    s = s.replace(
        '    val items = mutableStateListOf<DownloadItem>()\n    private val main = Handler(Looper.getMainLooper())',
        '    val items = mutableStateListOf<DownloadItem>()\n    var bannerItem by mutableStateOf<DownloadItem?>(null)\n        private set\n    private val main = Handler(Looper.getMainLooper())'
    )
    s = s.replace(
        '        main.post { items.add(0, item) }',
        '        main.post {\n            items.add(0, item)\n            bannerItem = item\n        }'
    )
    s = s.replace(
        '    fun pause(item: DownloadItem)',
        '    fun dismissBanner() { bannerItem = null }\n\n    fun pause(item: DownloadItem)'
    )
    downloads.write_text(s, encoding="utf-8")

app = base / "ui/BrowserApp.kt"
s = app.read_text(encoding="utf-8")
if "DownloadStartedBanner" not in s:
    s = s.replace(
        'import androidx.compose.animation.scaleOut\n',
        'import androidx.compose.animation.scaleOut\nimport androidx.compose.foundation.clickable\nimport androidx.compose.foundation.shape.RoundedCornerShape\nimport androidx.compose.material3.Card\nimport androidx.compose.material3.CardDefaults\n'
    )
    s = s.replace(
        'import app.swaga.browser.BrowserViewModel\n',
        'import app.swaga.browser.BrowserViewModel\nimport app.swaga.browser.DownloadsController\n'
    )
    s = s.replace(
        '    val snackbar = remember { SnackbarHostState() }',
        '    val snackbar = remember { SnackbarHostState() }\n    var showDownloads by remember { mutableStateOf(false) }\n    val downloadBanner = DownloadsController.bannerItem'
    )
    s = s.replace(
        '    LaunchedEffect(vm.ghostModeEnabled) {',
        '    LaunchedEffect(downloadBanner?.id) {\n        if (downloadBanner != null) {\n            kotlinx.coroutines.delay(5000)\n            if (DownloadsController.bannerItem?.id == downloadBanner.id) DownloadsController.dismissBanner()\n        }\n    }\n\n    LaunchedEffect(vm.ghostModeEnabled) {'
    )
    s = s.replace(
        '            SnackbarHost(\n                snackbar,',
        '            if (downloadBanner != null) {\n                DownloadStartedBanner(\n                    fileName = downloadBanner.name,\n                    onClick = { DownloadsController.dismissBanner(); showDownloads = true },\n                    modifier = Modifier.align(Alignment.TopCenter).padding(horizontal = 14.dp, vertical = 10.dp),\n                )\n            }\n\n            SnackbarHost(\n                snackbar,'
    )
    s = s.replace(
        '        if (showSettings) {',
        '        if (showDownloads) {\n            DownloadsSheet(onDismiss = { showDownloads = false })\n        }\n        if (showSettings) {'
    )
    s += '''

@Composable
private fun DownloadStartedBanner(
    fileName: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val c = LocalSwaga.current
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = c.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 5.dp),
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp)) {
            Text("Скачивание началось", color = c.text, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
            Text(fileName, color = c.dim, fontSize = 12.sp, maxLines = 1)
            Spacer(Modifier.height(8.dp))
            LinearProgressIndicator(
                modifier = Modifier.fillMaxWidth().height(2.dp),
                color = c.accent,
                trackColor = c.outline,
            )
            Text("Нажми, чтобы открыть загрузки", color = c.dim, fontSize = 11.sp, modifier = Modifier.padding(top = 6.dp))
        }
    }
}
'''
    app.write_text(s, encoding="utf-8")
print("Download start banner patch applied")
