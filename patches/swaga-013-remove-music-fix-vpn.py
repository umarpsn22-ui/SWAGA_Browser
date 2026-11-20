from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
src = root / "app/src/main/java/app/swaga/browser"
manifest = root / "app/src/main/AndroidManifest.xml"
gradle = root / "app/build.gradle.kts"

def read(rel):
    return (src / rel).read_text(encoding="utf-8")

def write(rel, value):
    (src / rel).write_text(value, encoding="utf-8")

def once(value, old, new, label):
    if new in value:
        return value
    if old not in value:
        raise SystemExit("Missing expected fragment: " + label)
    return value.replace(old, new, 1)

# Remove the standalone music library/player UI, while keeping media controls
# for audio/video elements already playing inside the current website.
p = src / "ui/BrowserApp.kt"
s = p.read_text(encoding="utf-8")
for line in (
    "import app.swaga.browser.media.MusicMiniPlayerSettings\n",
    "import app.swaga.browser.media.SwagaMusicPlayer\n",
):
    s = s.replace(line, "")
s = re.sub(r'    var miniPlayerPosition by remember \{ mutableStateOf\(MusicMiniPlayerSettings\.position\(context\)\) \}\n    LaunchedEffect\(Unit\) \{\n        while \(true\) \{\n            SwagaMusicPlayer\.refresh\(\)\n            miniPlayerPosition = MusicMiniPlayerSettings\.position\(context\)\n            kotlinx\.coroutines\.delay\(500\)\n        \}\n    \}\n', "", s, count=1)
s = s.replace('    var showMedia by remember { mutableStateOf(false) }\n', "")
s = s.replace('                    onMedia = { showMedia = true },\n', "")
s = re.sub(r'\n            if \(SwagaMusicPlayer\.currentTrack != null && vm\.pluginSettings\.externalPlayer\) \{.*?\n            \}\n\n            SnackbarHost', '\n            SnackbarHost', s, count=1, flags=re.S)
s = s.replace('                onMedia = { showSettings = false; showMedia = true },\n', "")
s = re.sub(r'\n        if \(showMedia\) \{\n            MusicLibrarySheet\(.*?\n        \}\n', '\n', s, count=1, flags=re.S)
if "SwagaMusicPlayer" in s or "MusicLibrarySheet" in s or "onMedia =" in s:
    raise SystemExit("BrowserApp still references the standalone music player")
p.write_text(s, encoding="utf-8")

# Remove the music library entry from Settings.
p = src / "ui/Sheets.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("    onMedia: () -> Unit,\n", "")
s = re.sub(r'\n                Button\(onClick = \{ onDismiss\(\); onMedia\(\) \},.*?\n                    Text\("Открыть Swaga Music"\)\n                \}\n', "\n", s, count=1, flags=re.S)
if "onMedia" in s or "Swaga Music" in s:
    raise SystemExit("SettingsSheet still references the standalone player")
p.write_text(s, encoding="utf-8")

# Remove the standalone player item from the browser overflow menu.
p = src / "ui/BottomBar.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("    onMedia: () -> Unit,\n", "")
s = re.sub(r'\n                DropdownMenuItem\(\n                    text = \{ Text\("Swaga Music · медиатека"\) \},.*?\n                \)\n', "\n", s, count=1, flags=re.S)
if "onMedia" in s or "Swaga Music" in s:
    raise SystemExit("BottomBar still references the standalone player")
p.write_text(s, encoding="utf-8")

# Keep the website media-control switch, but remove the music-player tab.
p = src / "ui/PluginSettingsSheet.kt"
s = p.read_text(encoding="utf-8")
s = s.replace('listOf("Text Animation", "MD3 Loader", "Music Player")', 'listOf("Text Animation", "MD3 Loader", "Медиа сайта")')
s = re.sub(
    r'                    else -> \{\n                        PluginGroup\("Music Player Actions"\) \{.*?\n                        \}\n                    \}',
    '''                    else -> {
                        PluginGroup("Управление медиа сайта") {
                            PluginSwitch("Управление аудио и видео на странице", p.mediaControls) { update { copy(mediaControls = it) } }
                            Text("Это только управление воспроизведением элементов текущего сайта. Отдельной музыкальной библиотеки, очереди песен и фонового музыкального сервиса в браузере больше нет.", color = c.dim, fontSize = 11.sp, lineHeight = 15.sp)
                        }
                    }''',
    s, count=1, flags=re.S
)
if "Music Player" in s or "Swaga Pleer" in s:
    raise SystemExit("Plugin settings still contain standalone player copy")
p.write_text(s, encoding="utf-8")

# Remove Media3-only dependencies and the media playback foreground service.
g = gradle.read_text(encoding="utf-8")
g = re.sub(r'^\s*implementation\("androidx\.media3:media3-(?:exoplayer|session):[^"]+"\)\s*\n', "", g, flags=re.M)
gradle.write_text(g, encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
m = m.replace('    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />\n', "")
m = re.sub(r'\s*<service\s+android:name="\.media\.SwagaPlaybackService".*?</service>\s*', "\n", m, flags=re.S)
manifest.write_text(m, encoding="utf-8")

for rel in (
    "ui/MusicLibrarySheet.kt",
    "ui/SwagaMiniPlayer.kt",
    "media/MusicLibrary.kt",
    "media/SwagaPlaybackService.kt",
):
    file = src / rel
    if file.exists():
        file.unlink()

# Make routing scope a property of the saved original profile, not a one-time
# rewrite at import. This allows changing browser-only/full-device without
# re-importing the .conf file.
p = src / "vpn/SwagaVpnManager.kt"
s = p.read_text(encoding="utf-8")
s = once(
    s,
    '        val sanitized = applyRoutingScope(raw, context.packageName, wholeDevice)\n        val parsed = Config.parse(ByteArrayInputStream(sanitized.toByteArray(Charsets.UTF_8)))',
    '        val scoped = applyRoutingScope(raw, context.packageName, wholeDevice)\n        val parsed = Config.parse(ByteArrayInputStream(scoped.toByteArray(Charsets.UTF_8)))',
    "import scope validation"
)
s = once(s, '        VpnConfigStore.save(context, sanitized, providerId, server, wholeDevice)\n', '        VpnConfigStore.save(context, raw, providerId, server, wholeDevice)\n', "save original profile")
s = once(
    s,
    '    suspend fun connect(context: Context) = withContext(Dispatchers.IO) {\n        mutableState.value = VpnState.Preparing(VpnConfigStore.provider(context))\n        try {\n            val raw = VpnConfigStore.load(context) ?: error("Сначала импортируй конфигурацию WireGuard.")\n            val config = Config.parse(ByteArrayInputStream(raw.toByteArray(Charsets.UTF_8)))',
    '''    suspend fun setWholeDevice(context: Context, enabled: Boolean) = withContext(Dispatchers.IO) {
        check(mutableState.value !is VpnState.Connected && mutableState.value !is VpnState.Preparing) {
            "Отключи VPN перед изменением области действия."
        }
        val raw = VpnConfigStore.load(context)
        if (raw != null) {
            val scoped = applyRoutingScope(raw, context.packageName, enabled)
            val parsed = Config.parse(ByteArrayInputStream(scoped.toByteArray(Charsets.UTF_8)))
            require(parsed.peers.isNotEmpty()) { "В профиле не найден WireGuard-сервер." }
            val routes = Regex("(?im)^\\\\s*AllowedIPs\\\\s*=\\\\s*([^\\\\r\\\\n]+)")
                .findAll(scoped).flatMap { it.groupValues[1].split(',').asSequence() }
                .map { it.trim() }.toSet()
            require("0.0.0.0/0" in routes && "::/0" in routes) {
                "Этот профиль не содержит маршруты всего трафика IPv4 и IPv6 (0.0.0.0/0 и ::/0). Создай full-tunnel конфигурацию у провайдера."
            }
        }
        VpnConfigStore.setWholeDevice(context, enabled)
    }

    suspend fun connect(context: Context) = withContext(Dispatchers.IO) {
        mutableState.value = VpnState.Preparing(VpnConfigStore.provider(context))
        try {
            val raw = VpnConfigStore.load(context) ?: error("Сначала импортируй конфигурацию WireGuard.")
            val wholeDevice = VpnConfigStore.wholeDevice(context)
            val scoped = applyRoutingScope(raw, context.packageName, wholeDevice)
            val config = Config.parse(ByteArrayInputStream(scoped.toByteArray(Charsets.UTF_8)))
            if (wholeDevice) {
                check(config.getInterface().getIncludedApplications().isEmpty()) {
                    "Профиль всё ещё ограничивает список приложений. Проверь настройки WireGuard."
                }
                check(config.getInterface().getExcludedApplications().isEmpty()) {
                    "В профиле есть исключённые приложения. Удали ограничения приложений из .conf."
                }
            } else {
                check(config.getInterface().getIncludedApplications().contains(context.packageName)) {
                    "Не удалось ограничить VPN только браузером."
                }
            }''',
    "connect applies selected scope"
)
if "val sanitized" in s:
    raise SystemExit("Old sanitized-profile storage remains")
p.write_text(s, encoding="utf-8")

# Add a preference setter without touching the encrypted raw configuration.
p = src / "vpn/VpnConfigStore.kt"
s = p.read_text(encoding="utf-8")
s = once(
    s,
    '    fun wholeDevice(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)\n        .getBoolean("whole_device", false)\n',
    '''    fun wholeDevice(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .getBoolean("whole_device", false)
    fun setWholeDevice(context: Context, enabled: Boolean) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putBoolean("whole_device", enabled).apply()
    }
''',
    "whole-device preference setter"
)
p.write_text(s, encoding="utf-8")

# Persist scope changes immediately and remove the misleading re-import gate.
p = src / "vpn/SwagaVpnSheet.kt"
s = p.read_text(encoding="utf-8")
s = s.replace('    var storedWholeDevice by remember { mutableStateOf(SwagaVpnManager.wholeDevice(context)) }\n', "")
s = s.replace('                storedWholeDevice = wholeDevice\n', "")
s = s.replace('''        if (wholeDevice != storedWholeDevice) {
            error = "Повторно импортируй .conf после смены режима маршрутизации."
            return
        }
''', "")
s = s.replace('''                        onClick = { wholeDevice = false },
                        enabled = state !is VpnState.Connected && state !is VpnState.Preparing,''',
'''                        onClick = {
                            scope.launch {
                                runCatching { SwagaVpnManager.setWholeDevice(context, false); wholeDevice = false }
                                    .onFailure { error = it.message ?: "Не удалось изменить режим VPN." }
                            }
                        },
                        enabled = state !is VpnState.Connected && state !is VpnState.Preparing,''')
s = s.replace('''                        onClick = { wholeDevice = true },
                        enabled = state !is VpnState.Connected && state !is VpnState.Preparing,''',
'''                        onClick = {
                            scope.launch {
                                runCatching { SwagaVpnManager.setWholeDevice(context, true); wholeDevice = true }
                                    .onFailure { error = it.message ?: "Не удалось включить режим всего устройства." }
                            }
                        },
                        enabled = state !is VpnState.Connected && state !is VpnState.Preparing,''')
s = s.replace('''                if (hasConfig && wholeDevice != storedWholeDevice) {
                    Text("Режим изменён. Повторно импортируй конфигурацию, чтобы безопасно применить новые маршруты.", color = Color(0xFFE5B35C), fontSize = 11.sp)
                }
''', "")
s = s.replace(
    '"Весь сетевой трафик приложений телефона будет направляться через импортированный WireGuard-туннель. Android отдельно запросит системное разрешение."',
    '"После подключения Android направляет сетевой трафик приложений через WireGuard. Нужен профиль с маршрутами 0.0.0.0/0 и ::/0. Режим применяется сразу, без повторного импорта файла."'
)
s = s.replace(
    '"Конфигурация ещё не добавлена"',
    '"Конфигурация ещё не добавлена"'
)
if "storedWholeDevice" in s or "Повторно импортируй .conf после смены" in s:
    raise SystemExit("VPN sheet still requires re-import after scope change")
p.write_text(s, encoding="utf-8")

print("Removed standalone music player and made WireGuard routing scope apply at connect time.")
