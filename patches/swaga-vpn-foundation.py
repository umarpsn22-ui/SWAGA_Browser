from pathlib import Path
import sys

root = Path(sys.argv[1])
base = root / "app/src/main/java/app/swaga/browser/vpn"
base.mkdir(parents=True, exist_ok=True)

(base / "VpnProvider.kt").write_text("""package app.swaga.browser.vpn

import android.net.VpnService
import android.os.ParcelFileDescriptor

/**
 * Contract for a provider adapter.
 *
 * An adapter may only be implemented against a provider-supported API/SDK or
 * an explicitly supported configuration export. Do not scrape private APIs.
 * The adapter owns the userspace tunnel and must forward packets read from the
 * returned TUN descriptor to the authenticated provider connection.
 */
interface VpnProvider {
    val id: String
    val displayName: String

    suspend fun connect(
        service: VpnService,
        builder: VpnService.Builder,
        browserPackage: String,
    ): ProviderTunnel

    suspend fun disconnect()
}

interface ProviderTunnel {
    val tun: ParcelFileDescriptor
    val serverName: String
    val protocol: String
    fun close()
}
""", encoding="utf-8")

(base / "VpnState.kt").write_text("""package app.swaga.browser.vpn

sealed interface VpnState {
    data object Disconnected : VpnState
    data class Preparing(val providerId: String) : VpnState
    data class Connected(
        val providerId: String,
        val serverName: String,
        val protocol: String,
    ) : VpnState
    data class Error(val message: String) : VpnState
}
""", encoding="utf-8")

(base / "VpnProviderRegistry.kt").write_text("""package app.swaga.browser.vpn

/**
 * Provider implementations are registered only after their supported
 * authentication and tunnel APIs have been verified.
 *
 * Intentionally empty in this foundation build: a UI must never report a
 * successful VPN connection until a real provider tunnel is active.
 */
object VpnProviderRegistry {
    private val providers = linkedMapOf<String, VpnProvider>()

    fun get(id: String): VpnProvider? = providers[id]

    fun available(): List<VpnProvider> = providers.values.toList()

    @Synchronized
    fun register(provider: VpnProvider) {
        providers[provider.id] = provider
    }
}
""", encoding="utf-8")

(base / "SwagaVpnManager.kt").write_text("""package app.swaga.browser.vpn

import android.content.Context
import android.content.Intent
import android.net.VpnService
import androidx.activity.result.ActivityResultLauncher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Browser-scoped VPN coordinator. Android's allowed-application list is
 * configured by the service, so other apps are not routed into this tunnel.
 */
object SwagaVpnManager {
    private val mutableState = MutableStateFlow<VpnState>(VpnState.Disconnected)
    val state: StateFlow<VpnState> = mutableState.asStateFlow()

    fun permissionIntent(context: Context): Intent? = VpnService.prepare(context)

    fun requestPermission(
        context: Context,
        launcher: ActivityResultLauncher<Intent>,
    ) {
        val intent = permissionIntent(context)
        if (intent == null) {
            mutableState.value = VpnState.Error("Разрешение Android уже выдано.")
            return
        }
        launcher.launch(intent)
    }

    fun setPreparing(providerId: String) {
        mutableState.value = VpnState.Preparing(providerId)
    }

    fun setConnected(providerId: String, server: String, protocol: String) {
        mutableState.value = VpnState.Connected(providerId, server, protocol)
    }

    fun setError(message: String) {
        mutableState.value = VpnState.Error(message)
    }

    fun setDisconnected() {
        mutableState.value = VpnState.Disconnected
    }
}
""", encoding="utf-8")

(base / "SwagaVpnService.kt").write_text("""package app.swaga.browser.vpn

import android.content.Intent
import android.net.VpnService
import android.os.IBinder

/**
 * Owns the Android VPN lifecycle. No TUN interface is established until a
 * real provider adapter is available. This prevents a fake "connected" state
 * or accidentally black-holing browser traffic in builds without an adapter.
 */
class SwagaVpnService : VpnService() {
    override fun onBind(intent: Intent?): IBinder? = super.onBind(intent)

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val providerId = intent?.getStringExtra(EXTRA_PROVIDER_ID).orEmpty()
        val provider = VpnProviderRegistry.get(providerId)
        if (provider == null) {
            SwagaVpnManager.setError(
                "Провайдер $providerId пока не подключён: нет подтверждённого API/SDK и VPN-туннеля."
            )
            stopSelf(startId)
            return START_NOT_STICKY
        }

        // A provider-specific foreground/tunnel lifecycle is added together
        // with its supported adapter, not simulated here.
        SwagaVpnManager.setError(
            "Адаптер провайдера найден, но запуск туннеля ещё не реализован."
        )
        stopSelf(startId)
        return START_NOT_STICKY
    }

    companion object {
        const val EXTRA_PROVIDER_ID = "app.swaga.browser.vpn.PROVIDER_ID"
    }
}
""", encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
if 'android:name=".vpn.SwagaVpnService"' not in m:
    anchor = """        <activity
            android:name=".MainActivity""" 
    service = """        <service
            android:name=".vpn.SwagaVpnService"
            android:permission="android.permission.BIND_VPN_SERVICE"
            android:exported="false">
            <intent-filter>
                <action android:name="android.net.VpnService" />
            </intent-filter>
        </service>

"""
    if anchor not in m:
        raise SystemExit("Manifest activity insertion point not found")
    m = m.replace(anchor, service + anchor, 1)
manifest.write_text(m, encoding="utf-8")

# Verify GeckoView is still the browser engine; fail the patch if this changes.
gradle = (root / "app/build.gradle.kts").read_text(encoding="utf-8")
if "org.mozilla.geckoview:geckoview" not in gradle:
    raise SystemExit("GeckoView dependency missing; refusing VPN patch")
engine = root / "app/src/main/java/app/swaga/browser/engine/SwagaWebView.kt"
if not engine.exists() or "GeckoSession" not in engine.read_text(encoding="utf-8"):
    raise SystemExit("GeckoView session adapter missing")
print("Added Swaga VPN lifecycle foundation; no provider is falsely marked available.")
