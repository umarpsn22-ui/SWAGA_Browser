package app.swaga.browser.vpn

sealed interface VpnState {
    data object Disconnected : VpnState
    data class Preparing(val providerId: String) : VpnState
    data class Connected(val providerId: String, val serverName: String, val protocol: String) : VpnState
    data class Error(val message: String) : VpnState
}
