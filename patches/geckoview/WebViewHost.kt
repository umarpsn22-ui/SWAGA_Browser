package app.swaga.browser.engine

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import app.swaga.browser.tabs.Tab

/**
 * Keeps each GeckoSession alive when its tab is temporarily removed from the
 * composition. This avoids throwing away page state and reloading on every
 * tab switch. Sessions are released only when a tab is actually closed.
 */
@Composable
fun WebViewHost(tab: Tab, modifier: Modifier = Modifier) {
    val owner = LocalLifecycleOwner.current

    DisposableEffect(owner, tab) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_PAUSE -> tab.webView?.onPause()
                Lifecycle.Event.ON_RESUME -> tab.webView?.onResume()
                else -> Unit
            }
        }
        owner.lifecycle.addObserver(observer)
        onDispose {
            owner.lifecycle.removeObserver(observer)
            tab.webView?.onPause()
        }
    }

    AndroidView(
        modifier = modifier.fillMaxSize(),
        factory = { context ->
            val adapter = tab.webView ?: SwagaGeckoTab.create(
                context,
                tab,
                tab.ghostSession,
            ).also { tab.webView = it }
            adapter.onResume()
            adapter.view
        },
        update = { tab.webView?.consume() },
        // Do not release the session here. AndroidView is removed when the
        // user switches tabs; the GeckoSession must survive that transition.
        onRelease = { tab.webView?.onPause() },
    )
}
