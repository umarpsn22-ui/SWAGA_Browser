from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
src = root / "app/src/main/java/app/swaga/browser"
res = root / "app/src/main/res"
manifest = root / "app/src/main/AndroidManifest.xml"

# Direct AI launcher: open the existing AI sheet from the home-screen widget.
p = src / "BrowserViewModel.kt"
s = p.read_text(encoding="utf-8")
if "var openAiRequested by mutableStateOf(false)" not in s:
    s = s.replace("class BrowserViewModel(app: Application) : AndroidViewModel(app) {",
                  "class BrowserViewModel(app: Application) : AndroidViewModel(app) {\n\n    var openAiRequested by mutableStateOf(false)")
if "import app.swaga.browser.widgets.SwagaWidgetUpdater" not in s:
    s = s.replace("import app.swaga.browser.themes.ThemeId\n",
                  "import app.swaga.browser.themes.ThemeId\nimport app.swaga.browser.widgets.SwagaWidgetUpdater\n")
s = s.replace('fun setTheme(t: ThemeId) { themeId = t; prefs.edit().putString("theme", t.name).apply() }',
              'fun setTheme(t: ThemeId) { themeId = t; prefs.edit().putString("theme", t.name).apply(); SwagaWidgetUpdater.refresh(getApplication()) }')
s = s.replace('fun setAccent(i: Int) { accentIndex = i; prefs.edit().putInt("accent", i).apply() }',
              'fun setAccent(i: Int) { accentIndex = i; prefs.edit().putInt("accent", i).apply(); SwagaWidgetUpdater.refresh(getApplication()) }')
p.write_text(s, encoding="utf-8")

p = src / "MainActivity.kt"
s = p.read_text(encoding="utf-8")
if "swaga_open_ai" not in s:
    s = s.replace("    private fun handleIntent(i: Intent?) {",
                  '    private fun handleIntent(i: Intent?) {\n        if (i?.getBooleanExtra("swaga_open_ai", false) == true) vm.openAiRequested = true')
s = s.replace('''    override fun onStop() {
        vm.persist()
        super.onStop()
    }''', '''    override fun onStop() {
        vm.persist()
        SwagaWidgetUpdater.refresh(this)
        super.onStop()
    }''')
p.write_text(s, encoding="utf-8")

p = src / "ui/BrowserApp.kt"
s = p.read_text(encoding="utf-8")
if "LaunchedEffect(vm.openAiRequested)" not in s:
    s = s.replace("    var showAi by remember { mutableStateOf(false) }",
                  "    var showAi by remember { mutableStateOf(false) }\n    LaunchedEffect(vm.openAiRequested) { if (vm.openAiRequested) { showAi = true; vm.openAiRequested = false } }")
p.write_text(s, encoding="utf-8")

# Extend widget updater with AI and recent-tabs providers, and sync accent color.
p = src / "widgets/SwagaWidgets.kt"
s = p.read_text(encoding="utf-8")
if "private fun widgetAccent" not in s:
    s = s.replace("object SwagaWidgetUpdater {", '''private fun widgetAccent(context: Context): Int = when (context.getSharedPreferences("swaga", Context.MODE_PRIVATE).getInt("accent", 0)) {
    1 -> android.graphics.Color.rgb(34, 160, 107)
    2 -> android.graphics.Color.rgb(139, 111, 232)
    3 -> android.graphics.Color.rgb(224, 120, 120)
    4 -> android.graphics.Color.rgb(208, 166, 75)
    5 -> android.graphics.Color.rgb(241, 243, 245)
    else -> android.graphics.Color.rgb(59, 130, 246)
}

private fun openAi(context: Context, request: Int): PendingIntent {
    val intent = Intent(context, app.swaga.browser.MainActivity::class.java).putExtra("swaga_open_ai", true)
    return PendingIntent.getActivity(context, request, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
}

object SwagaWidgetUpdater {''')
s = s.replace("            SwagaDownloadsWidget::class.java,\n",
              "            SwagaDownloadsWidget::class.java,\n            SwagaAiWidget::class.java,\n            SwagaRecentTabsWidget::class.java,\n")
s = s.replace("                SwagaDownloadsWidget::class.java -> SwagaDownloadsWidget().onUpdate(context, manager, ids)\n",
              "                SwagaDownloadsWidget::class.java -> SwagaDownloadsWidget().onUpdate(context, manager, ids)\n                SwagaAiWidget::class.java -> SwagaAiWidget().onUpdate(context, manager, ids)\n                SwagaRecentTabsWidget::class.java -> SwagaRecentTabsWidget().onUpdate(context, manager, ids)\n")
s = s.replace('''            views.setOnClickPendingIntent(R.id.widget_search_action, openPage(context, "https://www.google.com", 100 + id))
            views.setOnClickPendingIntent(R.id.widget_search_logo, openPage(context, "https://www.google.com", 200 + id))''',
'''            views.setInt(R.id.widget_search_action, "setBackgroundColor", widgetAccent(context))
            val start = PendingIntent.getActivity(context, 100 + id, Intent(context, app.swaga.browser.MainActivity::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            views.setOnClickPendingIntent(R.id.widget_search_action, start)
            views.setOnClickPendingIntent(R.id.widget_search_logo, start)''')
s = s.replace('''            links.forEachIndexed { index, pair -> views.setOnClickPendingIntent(pair.first, openPage(context, pair.second, 300 + id * 10 + index)) }''',
'''            links.forEachIndexed { index, pair ->
                views.setOnClickPendingIntent(pair.first, openPage(context, pair.second, 300 + id * 10 + index))
                views.setInt(pair.first, "setBackgroundColor", if (index % 2 == 0) widgetAccent(context) else 0xFF242631.toInt())
            }''')
s = s.replace('''            views.setTextViewText(R.id.widget_privacy_count, total.toString())''',
'''            views.setTextViewText(R.id.widget_privacy_count, total.toString())
            views.setTextColor(R.id.widget_privacy_count, widgetAccent(context))''')
s = s.replace('''            views.setTextViewText(R.id.widget_download_count, count.toString())''',
'''            views.setTextViewText(R.id.widget_download_count, count.toString())
            views.setTextColor(R.id.widget_download_count, widgetAccent(context))''')
if "class SwagaAiWidget" not in s:
    s += '''

class SwagaAiWidget : AppWidgetProvider() {
    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        ids.forEach { id ->
            val views = RemoteViews(context.packageName, R.layout.widget_sw_ai)
            views.setInt(R.id.widget_ai_action, "setBackgroundColor", widgetAccent(context))
            views.setOnClickPendingIntent(R.id.widget_ai_action, openAi(context, 600 + id))
            manager.updateAppWidget(id, views)
        }
    }
}

class SwagaRecentTabsWidget : AppWidgetProvider() {
    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        val tabs = runCatching {
            val raw = context.getSharedPreferences("swaga", Context.MODE_PRIVATE).getString("tabs_json", "[]") ?: "[]"
            val array = org.json.JSONArray(raw)
            (0 until array.length()).mapNotNull { index ->
                val item = array.optJSONObject(index) ?: return@mapNotNull null
                val url = item.optString("u").takeIf { it.startsWith("https://") || it.startsWith("http://") } ?: return@mapNotNull null
                (item.optString("t").ifBlank { android.net.Uri.parse(url).host ?: url }) to url
            }.takeLast(2)
        }.getOrDefault(emptyList())
        ids.forEach { id ->
            val views = RemoteViews(context.packageName, R.layout.widget_sw_recent)
            val targets = listOf(R.id.widget_recent_one, R.id.widget_recent_two)
            targets.forEachIndexed { index, viewId ->
                val item = tabs.getOrNull(index)
                views.setTextViewText(viewId, item?.first ?: if (index == 0) "Пока нет вкладок" else "Открой сайт в браузере")
                if (item != null) views.setOnClickPendingIntent(viewId, openPage(context, item.second, 700 + id * 10 + index))
            }
            views.setTextColor(R.id.widget_recent_one, widgetAccent(context))
            manager.updateAppWidget(id, views)
        }
    }
}
'''
p.write_text(s, encoding="utf-8")

extra = {
"widget_sw_ai.xml": '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="horizontal" android:gravity="center_vertical" android:padding="16dp" android:background="#17171D"><LinearLayout android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1" android:orientation="vertical"><TextView android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="SWAGA AI" android:textColor="#FFFFFF" android:textStyle="bold" android:textSize="15sp"/><TextView android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="Помощник всегда под рукой" android:textColor="#AAA7B5" android:textSize="11sp"/></LinearLayout><TextView android:id="@+id/widget_ai_action" android:layout_width="wrap_content" android:layout_height="42dp" android:gravity="center" android:paddingHorizontal="14dp" android:text="Открыть AI  ✦" android:textColor="#FFFFFF" android:textStyle="bold" android:background="#7056B8"/></LinearLayout>''',
"widget_sw_recent.xml": '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="vertical" android:padding="14dp" android:background="#17171D"><TextView android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="НЕДАВНИЕ ВКЛАДКИ" android:textColor="#AAA7B5" android:textStyle="bold" android:textSize="11sp" android:paddingBottom="6dp"/><TextView android:id="@+id/widget_recent_one" android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1" android:gravity="center_vertical" android:text="Пока нет вкладок" android:textColor="#FFFFFF" android:textSize="13sp" android:maxLines="1"/><TextView android:id="@+id/widget_recent_two" android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1" android:gravity="center_vertical" android:text="Открой сайт в браузере" android:textColor="#AAA7B5" android:textSize="12sp" android:maxLines="1"/></LinearLayout>'''
}
for name, xml in extra.items():
    (res / "layout" / name).write_text(xml, encoding="utf-8")
for name, layout in [("widget_sw_ai_info.xml", "widget_sw_ai"), ("widget_sw_recent_info.xml", "widget_sw_recent")]:
    (res / "xml" / name).write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android" android:minWidth="180dp" android:minHeight="72dp" android:initialLayout="@layout/{layout}" android:resizeMode="horizontal|vertical" android:widgetCategory="home_screen" android:updatePeriodMillis="0" android:label="@string/app_name" android:description="@string/app_name" />''', encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
if ".widgets.SwagaAiWidget" not in m:
    m = m.replace("    </application>", '''        <receiver android:name=".widgets.SwagaAiWidget" android:exported="true">
            <intent-filter><action android:name="android.appwidget.action.APPWIDGET_UPDATE" /></intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/widget_sw_ai_info" />
        </receiver>
        <receiver android:name=".widgets.SwagaRecentTabsWidget" android:exported="true">
            <intent-filter><action android:name="android.appwidget.action.APPWIDGET_UPDATE" /></intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/widget_sw_recent_info" />
        </receiver>
    </application>''')
manifest.write_text(m, encoding="utf-8")

p = root / "app/build.gradle.kts"
s = p.read_text(encoding="utf-8").replace("versionCode = 7", "versionCode = 8").replace('versionName = "0.1.1-beta"', 'versionName = "0.1.2-beta"')
p.write_text(s, encoding="utf-8")
print("Added Swaga AI and recent-tabs widgets; synced widget accent and bumped version to 0.1.2-beta.")
