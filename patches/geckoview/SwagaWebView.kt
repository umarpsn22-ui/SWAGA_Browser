package app.swaga.browser.engine

import android.content.Context
import android.os.Handler
import android.os.Looper
import org.json.JSONObject
import org.mozilla.geckoview.GeckoRuntime
import org.mozilla.geckoview.GeckoSession
import org.mozilla.geckoview.GeckoSessionSettings
import org.mozilla.geckoview.GeckoView
import org.mozilla.geckoview.StorageController
import org.mozilla.geckoview.WebExtension
import app.swaga.browser.tabs.Tab
import java.util.concurrent.atomic.AtomicLong

/**
 * Gecko-backed tab adapter. Page JavaScript is executed by a privileged,
 * APK-bundled WebExtension and returned over a session-scoped native port.
 */
class SwagaGeckoTab private constructor(
    private val context: Context,
    private val tab: Tab,
    private var privateMode: Boolean,
) {
    val view: GeckoView = GeckoView(context)
    private var session: GeckoSession = newSession()

    private data class PendingJsCall(
        val payload: JSONObject,
        val callback: (String?) -> Unit,
        var sentPort: WebExtension.Port? = null,
    )

    private val mainHandler = Handler(Looper.getMainLooper())
    private val pendingJsCalls = LinkedHashMap<String, PendingJsCall>()
    private var bridgePort: WebExtension.Port? = null

    inner class EngineSettings {
        var textZoom: Int = tab.textZoom
            set(value) {
                field = value.coerceIn(70, 200)
                runtime(context).settings.fontSizeFactor = field / 100f
            }
        var userAgentString: String? = null
            set(value) {
                field = value
                session.settings.userAgentOverride = value
            }
        var domStorageEnabled: Boolean = true
        var cacheMode: Int = 0
    }
    val settings = EngineSettings()

    private fun attachJavaScriptBridge(target: GeckoSession) {
        runtime(context).webExtensionController
            .ensureBuiltIn(BRIDGE_EXTENSION_URI, BRIDGE_EXTENSION_ID)
            .accept({ extension ->
                if (target.isOpen) {
                    target.webExtensionController.setMessageDelegate(
                        extension,
                        object : WebExtension.MessageDelegate {
                            override fun onConnect(port: WebExtension.Port) {
                                if (port.sender.session !== target) {
                                    port.disconnect()
                                    return
                                }
                                port.setDelegate(object : WebExtension.PortDelegate {
                                    override fun onPortMessage(
                                        message: Any,
                                        receivedPort: WebExtension.Port,
                                    ) {
                                        val response = message as? JSONObject ?: return
                                        val requestId = response.optString("id")
                                        val pending = pendingJsCalls.remove(requestId) ?: return
                                        val result = if (
                                            response.has("result") && !response.isNull("result")
                                        ) response.optString("result") else null
                                        pending.callback(result)
                                        flushJavaScriptQueue()
                                    }

                                    override fun onDisconnect(disconnectedPort: WebExtension.Port) {
                                        if (bridgePort === disconnectedPort) bridgePort = null
                                        pendingJsCalls.values.forEach { it.sentPort = null }
                                    }
                                })
                                bridgePort = port
                                flushJavaScriptQueue()
                            }
                        },
                        BRIDGE_NATIVE_APP,
                    )
                }
            }, {
                // Requests time out cleanly if the bundled extension cannot be installed.
            })
    }

    private fun flushJavaScriptQueue() {
        val port = bridgePort ?: return
        pendingJsCalls.values.forEach { pending ->
            if (pending.sentPort !== port) {
                try {
                    port.postMessage(pending.payload)
                    pending.sentPort = port
                } catch (_: RuntimeException) {
                    pending.sentPort = null
                }
            }
        }
    }

    private fun newSession(): GeckoSession {
        val options = GeckoSessionSettings.Builder()
            .allowJavascript(true)
            .usePrivateMode(privateMode)
            .useTrackingProtection(SwagaWebView.trackingProtectionEnabled)
            .userAgentMode(
                if (tab.desktopMode) GeckoSessionSettings.USER_AGENT_MODE_DESKTOP
                else GeckoSessionSettings.USER_AGENT_MODE_MOBILE
            )
            .viewportMode(
                if (tab.desktopMode) GeckoSessionSettings.VIEWPORT_MODE_DESKTOP
                else GeckoSessionSettings.VIEWPORT_MODE_MOBILE
            )
            .build()
        return GeckoSession(options).also { created ->
            created.setContentDelegate(object : GeckoSession.ContentDelegate {
                override fun onTitleChange(session: GeckoSession, title: String?) {
                    if (!title.isNullOrBlank()) tab.title = title
                }
            })
            created.setProgressDelegate(object : GeckoSession.ProgressDelegate {
                override fun onPageStart(session: GeckoSession, url: String) {
                    tab.loading = true
                    tab.progress = 0
                    tab.error = null
                }

                override fun onPageStop(session: GeckoSession, success: Boolean) {
                    tab.loading = false
                    tab.progress = 100
                    if (success) tab.onPageLoaded?.invoke(tab)
                    else tab.error = "Не удалось загрузить страницу."
                }

                override fun onProgressChange(session: GeckoSession, progress: Int) {
                    tab.progress = progress
                    tab.loading = progress < 100
                }
            })
            created.setNavigationDelegate(object : GeckoSession.NavigationDelegate {
                override fun onCanGoBack(session: GeckoSession, canGoBack: Boolean) {
                    tab.canGoBack = canGoBack
                }

                override fun onCanGoForward(session: GeckoSession, canGoForward: Boolean) {
                    tab.canGoForward = canGoForward
                }

                override fun onLocationChange(
                    session: GeckoSession,
                    url: String?,
                    perms: List<GeckoSession.PermissionDelegate.ContentPermission>,
                    hasUserGesture: Boolean,
                ) {
                    if (!url.isNullOrBlank() && !url.startsWith("about:")) tab.url = url
                }
            })
            created.open(runtime(context))
            attachJavaScriptBridge(created)
            view.setSession(created)
        }
    }

    fun consume() {
        val request = tab.navRequest
        if (request != null && !request.handled) {
            request.handled = true
            session.loadUri(request.url)
        }
    }

    fun loadUrl(url: String) = session.loadUri(url)
    fun reload() = session.reload()
    fun goBack() = session.goBack()
    fun goForward() = session.goForward()
    fun stopLoading() = session.stop()
    fun clearHistory() = session.purgeHistory()
    fun clearCache(@Suppress("UNUSED_PARAMETER") includeDiskFiles: Boolean) = Unit
    fun clearFormData() = Unit
    fun onPause() = session.setActive(false)
    fun onResume() = session.setActive(true)

    fun evaluateJavascript(script: String, callback: (String?) -> Unit) {
        val requestId = nextRequestId.incrementAndGet().toString()
        val payload = JSONObject()
            .put("type", "evaluate")
            .put("id", requestId)
            .put("script", script)
        pendingJsCalls[requestId] = PendingJsCall(payload, callback)
        mainHandler.postDelayed({
            val expired = pendingJsCalls.remove(requestId)
            expired?.callback?.invoke(null)
        }, JS_REQUEST_TIMEOUT_MS)
        flushJavaScriptQueue()
    }

    fun findAllAsync(query: String) {
        session.finder.setDisplayFlags(GeckoSession.FINDER_DISPLAY_HIGHLIGHT_ALL)
        session.finder.find(query, GeckoSession.FINDER_FIND_FORWARD)
    }

    fun findNext(forward: Boolean) {
        session.finder.find(
            null,
            if (forward) GeckoSession.FINDER_FIND_FORWARD else GeckoSession.FINDER_FIND_BACKWARDS
        )
    }

    fun clearMatches() = session.finder.clear()

    fun setDesktopMode(enabled: Boolean) {
        session.settings.userAgentMode = if (enabled) {
            GeckoSessionSettings.USER_AGENT_MODE_DESKTOP
        } else {
            GeckoSessionSettings.USER_AGENT_MODE_MOBILE
        }
        session.settings.viewportMode = if (enabled) {
            GeckoSessionSettings.VIEWPORT_MODE_DESKTOP
        } else {
            GeckoSessionSettings.VIEWPORT_MODE_MOBILE
        }
        session.reload()
    }

    fun setTrackingProtection(enabled: Boolean) {
        session.settings.useTrackingProtection = enabled
        session.reload()
    }

    fun setPrivateMode(enabled: Boolean) {
        if (privateMode == enabled) return
        val currentUrl = tab.url
        bridgePort?.disconnect()
        bridgePort = null
        pendingJsCalls.values.forEach { it.callback(null) }
        pendingJsCalls.clear()
        if (view.session != null) view.releaseSession()
        if (session.isOpen) session.close()
        privateMode = enabled
        session = newSession()
        if (!currentUrl.isNullOrBlank()) session.loadUri(currentUrl)
    }

    fun release() {
        bridgePort?.disconnect()
        bridgePort = null
        pendingJsCalls.values.forEach { it.callback(null) }
        pendingJsCalls.clear()
        if (view.session != null) view.releaseSession()
        if (session.isOpen) session.close()
        if (tab.webView === this) tab.webView = null
    }

    companion object {
        private const val BRIDGE_EXTENSION_URI =
            "resource://android/assets/web_extensions/swaga_bridge/"
        private const val BRIDGE_EXTENSION_ID = "swaga-js-bridge@swaga.browser"
        private const val BRIDGE_NATIVE_APP = "swaga_browser"
        private const val JS_REQUEST_TIMEOUT_MS = 15_000L
        private val nextRequestId = AtomicLong(0)

        @Volatile private var sharedRuntime: GeckoRuntime? = null

        private fun runtime(context: Context): GeckoRuntime =
            sharedRuntime ?: synchronized(this) {
                sharedRuntime ?: GeckoRuntime.create(context.applicationContext).also {
                    sharedRuntime = it
                }
            }

        fun create(context: Context, tab: Tab, privateMode: Boolean): SwagaGeckoTab =
            SwagaGeckoTab(context.applicationContext, tab, privateMode)

        fun desktopUserAgent(@Suppress("UNUSED_PARAMETER") context: Context): String =
            GeckoSession.getDefaultUserAgent()

        fun clearSiteData(context: Context) {
            runtime(context).storageController.clearData(StorageController.ClearFlags.SITE_DATA)
        }
    }
}

/** Compatibility holder for browser preferences consumed by BrowserViewModel. */
object SwagaWebView {
    @Volatile var trackingProtectionEnabled: Boolean = true
}
