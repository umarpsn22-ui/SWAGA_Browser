package app.swaga.browser.engine

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import app.swaga.browser.tabs.Tab

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
        onDispose { owner.lifecycle.removeObserver(observer) }
    }

    AndroidView(
        modifier = modifier.fillMaxSize(),
        factory = { context ->
            SwagaGeckoTab.create(context, tab, tab.ghostSession).also {
                tab.webView = it
            }.view
        },
        update = { tab.webView?.consume() },
        onRelease = { tab.webView?.release() },
    )
}
