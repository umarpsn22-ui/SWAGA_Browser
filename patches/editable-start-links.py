from pathlib import Path
import sys
p = Path(sys.argv[1])/'app/src/main/java/app/swaga/browser/ui/StartPage.kt'
s = p.read_text()
def once(old, new, label):
    global s
    if old not in s: raise SystemExit('Cannot patch StartPage: missing '+label)
    s = s.replace(old, new, 1)
once('import androidx.compose.foundation.clickable', 'import androidx.compose.foundation.clickable\nimport androidx.compose.foundation.combinedClickable', 'clickable import')
once('import androidx.compose.material3.IconButton', 'import androidx.compose.material3.IconButton\nimport androidx.compose.material3.AlertDialog\nimport androidx.compose.material3.OutlinedTextField', 'material imports')
once('private val quickLinks = listOf(', 'private val defaultQuickLinks = listOf(', 'default links')
# Add persistent link storage helpers.
anchor='\n\nprivate fun decodeStartWallpaper'
helpers='''
\n\nprivate fun loadQuickLinks(context: Context): List<QuickLink> = runCatching {
    val raw = context.getSharedPreferences("swaga_start_links", Context.MODE_PRIVATE).getString("items", null)
        ?: return@runCatching defaultQuickLinks
    val array = org.json.JSONArray(raw)
    (0 until array.length()).mapNotNull { index ->
        val item = array.optJSONObject(index) ?: return@mapNotNull null
        val title = item.optString("title").trim()
        val url = item.optString("url").trim()
        if (title.isBlank() || url.isBlank()) null else QuickLink(title.take(32), url)
    }
}.getOrDefault(defaultQuickLinks)

private fun saveQuickLinks(context: Context, links: List<QuickLink>) {
    val array = org.json.JSONArray()
    links.forEach { link ->
        array.put(org.json.JSONObject().put("title", link.title).put("url", link.url))
    }
    context.getSharedPreferences("swaga_start_links", Context.MODE_PRIVATE)
        .edit().putString("items", array.toString()).apply()
}
'''
once(anchor, helpers+anchor, 'wallpaper helper anchor')
# State + editor dialog.
anchor='''    val focusManager = LocalFocusManager.current
    var query by remember { mutableStateOf("") }'''
replacement='''    val focusManager = LocalFocusManager.current
    var query by remember { mutableStateOf("") }
    var links by remember { mutableStateOf(loadQuickLinks(context)) }
    var editorIndex by remember { mutableStateOf<Int?>(null) }
    var editorTitle by remember { mutableStateOf("") }
    var editorUrl by remember { mutableStateOf("") }
    var editorError by remember { mutableStateOf<String?>(null) }
    fun openLinkEditor(index: Int?) {
        editorIndex = index
        editorTitle = index?.let { links.getOrNull(it)?.title }.orEmpty()
        editorUrl = index?.let { links.getOrNull(it)?.url }.orEmpty()
        editorError = null
    }
    if (editorIndex != null || editorIndex == -1) {
        AlertDialog(
            onDismissRequest = { editorIndex = null },
            title = { Text(if (editorIndex == -1) "Добавить сайт" else "Изменить сайт") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    OutlinedTextField(value = editorTitle, onValueChange = { editorTitle = it }, singleLine = true, label = { Text("Название") })
                    OutlinedTextField(value = editorUrl, onValueChange = { editorUrl = it }, singleLine = true, label = { Text("Адрес сайта") })
                    editorError?.let { Text(it, color = Color(0xFFE57373), fontSize = 12.sp) }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val title = editorTitle.trim()
                    var url = editorUrl.trim()
                    if (title.isBlank() || url.isBlank()) {
                        editorError = "Заполни название и адрес."
                    } else {
                        if (!url.contains("://")) url = "https://$url"
                        if (!url.startsWith("https://") && !url.startsWith("http://")) {
                            editorError = "Укажи адрес сайта с http:// или https://."
                        } else {
                            val next = links.toMutableList()
                            val item = QuickLink(title.take(32), url)
                            if (editorIndex == -1) next.add(item) else next[editorIndex!!] = item
                            links = next
                            saveQuickLinks(context, next)
                            editorIndex = null
                        }
                    }
                }) { Text("Сохранить") }
            },
            dismissButton = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (editorIndex != -1) TextButton(onClick = {
                        val next = links.toMutableList()
                        next.removeAt(editorIndex!!)
                        links = next
                        saveQuickLinks(context, next)
                        editorIndex = null
                    }) { Text("Удалить", color = Color(0xFFE57373)) }
                    TextButton(onClick = { editorIndex = null }) { Text("Отмена") }
                }
            },
        )
    }'''
once(anchor,replacement,'StartPage state')
# The editor uses -1 as add sentinel; initialize nullable state to null as above.
# Add a small add action before shortcut grid and swap the backing collection.
anchor='''            Spacer(Modifier.height(22.dp))
            quickLinks.chunked(4).forEach { row ->'''
replacement='''            Spacer(Modifier.height(22.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                TextButton(onClick = { openLinkEditor(-1) }) { Text("+ Настроить сайты", color = c.accent, fontSize = 12.sp) }
            }
            links.chunked(4).forEachIndexed { rowIndex, row ->'''
once(anchor,replacement,'quick links grid')
# Each tile opens editor on long press; ordinary tap still navigates.
once('''                        Tile(link.title, Modifier.weight(1f)) { vm.submit(link.url) }''','''                        val linkIndex = rowIndex * 4 + row.indexOf(link)
                        Tile(link.title, Modifier.weight(1f), onLongClick = { openLinkEditor(linkIndex) }) { vm.submit(link.url) }''','tile call')
# Extend Tile API and use long-press gesture.
once('''private fun Tile(title: String, modifier: Modifier, onClick: () -> Unit) {''','''private fun Tile(title: String, modifier: Modifier, onLongClick: (() -> Unit)? = null, onClick: () -> Unit) {''','Tile signature')
once('''.appButton(RoundedCornerShape(18.dp), elevated = true, onClick = onClick)
            .padding(vertical = 6.dp),''','''.combinedClickable(onClick = onClick, onLongClick = onLongClick)
            .clip(RoundedCornerShape(18.dp))
            .background(c.surfaceHigh)
            .padding(vertical = 6.dp),''','Tile modifier')
p.write_text(s)
print('Added persistent editable quick links with long-press edit and delete.')
