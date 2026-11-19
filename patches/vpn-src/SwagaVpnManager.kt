package app.swaga.browser.vpn

import android.content.Context
import com.wireguard.android.backend.GoBackend
import com.wireguard.android.backend.Tunnel
import com.wireguard.config.Config
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import java.io.ByteArrayInputStream

object SwagaVpnManager {
    private val mutableState = MutableStateFlow<VpnState>(VpnState.Disconnected)
    val state: StateFlow<VpnState> = mutableState.asStateFlow()
    @Volatile private var backend: GoBackend? = null
    @Volatile private var activeProvider = "custom"
    @Volatile private var activeServer = "WireGuard сервер"

    private val tunnel = object : Tunnel {
        override fun getName() = "swaga"
        override fun onStateChange(newState: Tunnel.State) {
            mutableState.value = if (newState == Tunnel.State.DOWN) VpnState.Disconnected
            else VpnState.Connected(activeProvider, activeServer, "WireGuard")
        }
    }

    fun hasConfig(context: Context) = VpnConfigStore.exists(context)
    fun savedProvider(context: Context) = VpnConfigStore.provider(context)
    fun savedServer(context: Context) = VpnConfigStore.server(context)

    suspend fun importConfig(context: Context, raw: String, providerId: String) = withContext(Dispatchers.IO) {
        require(raw.length in 1..256_000) { "Файл конфигурации пустой или слишком большой." }
        val sanitized = browserOnlyConfig(raw, context.packageName)
        val parsed = Config.parse(ByteArrayInputStream(sanitized.toByteArray(Charsets.UTF_8)))
        require(parsed.peers.isNotEmpty()) { "В конфигурации не найден VPN-сервер." }
        val routes = Regex("(?im)^\\s*AllowedIPs\\s*=\\s*([^\\r\\n]+)")
            .findAll(sanitized).flatMap { it.groupValues[1].split(',').asSequence() }
            .map { it.trim() }.toSet()
        require("0.0.0.0/0" in routes && "::/0" in routes) {
            "Нужен full-tunnel профиль с маршрутами 0.0.0.0/0 и ::/0, чтобы IPv4 и IPv6 не обходили туннель."
        }
        val server = Regex("(?im)^\\s*Endpoint\\s*=\\s*([^\\s#]+)")
            .find(sanitized)?.groupValues?.get(1) ?: "WireGuard сервер"
        VpnConfigStore.save(context, sanitized, providerId, server)
        server
    }

    private fun browserOnlyConfig(raw: String, packageName: String): String {
        val out = StringBuilder()
        var inInterface = false
        raw.lineSequence().forEach { line ->
            val trimmed = line.trim()
            if (trimmed.startsWith("[")) {
                inInterface = trimmed.equals("[Interface]", ignoreCase = true)
                out.append(line).append('\n')
                if (inInterface) out.append("IncludedApplications = ").append(packageName).append('\n')
            } else if (!(inInterface && Regex("(?i)^\\s*(IncludedApplications|ExcludedApplications)\\s*=").containsMatchIn(line))) {
                out.append(line).append('\n')
            }
        }
        return out.toString()
    }

    suspend fun connect(context: Context) = withContext(Dispatchers.IO) {
        mutableState.value = VpnState.Preparing(VpnConfigStore.provider(context))
        try {
            val raw = VpnConfigStore.load(context) ?: error("Сначала импортируй конфигурацию WireGuard.")
            val config = Config.parse(ByteArrayInputStream(raw.toByteArray(Charsets.UTF_8)))
            activeProvider = VpnConfigStore.provider(context)
            activeServer = VpnConfigStore.server(context)
            val engine = backend ?: GoBackend(context.applicationContext).also { backend = it }
            check(engine.setState(tunnel, Tunnel.State.UP, config) == Tunnel.State.UP) {
                "WireGuard не подтвердил запуск туннеля."
            }
            mutableState.value = VpnState.Connected(activeProvider, activeServer, "WireGuard")
        } catch (t: Throwable) {
            mutableState.value = VpnState.Error(t.message?.take(220) ?: "Не удалось подключить VPN.")
            throw t
        }
    }

    suspend fun disconnect() = withContext(Dispatchers.IO) {
        try {
            backend?.setState(tunnel, Tunnel.State.DOWN, null)
        } finally {
            mutableState.value = VpnState.Disconnected
        }
    }

    suspend fun removeProfile(context: Context) = withContext(Dispatchers.IO) {
        runCatching { backend?.setState(tunnel, Tunnel.State.DOWN, null) }
        VpnConfigStore.clear(context)
    }
}
