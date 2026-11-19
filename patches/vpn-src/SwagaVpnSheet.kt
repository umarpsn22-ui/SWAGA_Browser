package app.swaga.browser.vpn

import android.app.Activity
import android.net.VpnService
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import app.swaga.browser.themes.LocalSwaga
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SwagaVpnSheet(onDismiss: () -> Unit) {
    val context = LocalContext.current
    val colors = LocalSwaga.current
    val scope = rememberCoroutineScope()
    val state by SwagaVpnManager.state.collectAsState()
    var provider by remember { mutableStateOf("proton") }
    var hasConfig by remember { mutableStateOf(SwagaVpnManager.hasConfig(context)) }
    var server by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) scope.launch {
            runCatching {
                val raw = context.contentResolver.openInputStream(uri)?.use { input ->
                    val bytes = input.readBytes()
                    require(bytes.size <= 256_000) { "Файл больше 256 КБ." }
                    bytes.toString(Charsets.UTF_8)
                } ?: error("Не удалось прочитать файл.")
                server = SwagaVpnManager.importConfig(context, raw, provider)
                hasConfig = true
                error = null
            }.onFailure { error = it.message ?: "Не удалось импортировать профиль." }
        }
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) scope.launch {
            runCatching { SwagaVpnManager.connect(context) }
                .onFailure { error = it.message ?: "Подключение не удалось." }
        } else error = "Разрешение Android на VPN не выдано."
    }

    LaunchedEffect(Unit) {
        provider = SwagaVpnManager.savedProvider(context)
        hasConfig = SwagaVpnManager.hasConfig(context)
        if (hasConfig) server = SwagaVpnManager.savedServer(context)
    }

    ModalBottomSheet(onDismissRequest = onDismiss, containerColor = colors.surface) {
        Column(
            Modifier.fillMaxWidth().padding(horizontal = 20.dp).padding(bottom = 30.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Swaga VPN", style = MaterialTheme.typography.headlineSmall, color = colors.text)
            Text(
                "Встроенный WireGuard. В VPN включается только пакет SwagaBrowser, остальные приложения не перенаправляются.",
                color = colors.dim, style = MaterialTheme.typography.bodySmall,
            )
            Text("Профиль провайдера", color = colors.text, style = MaterialTheme.typography.titleSmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(provider == "proton", { provider = "proton" }, label = { Text("Proton VPN") })
                FilterChip(provider == "windscribe", { provider = "windscribe" }, label = { Text("Windscribe") })
            }
            FilterChip(provider == "custom", { provider = "custom" }, label = { Text("Другой WireGuard") })
            if (hasConfig) {
                Text("Конфигурация импортирована", color = colors.accent, style = MaterialTheme.typography.titleSmall)
                Text(server, color = colors.dim, style = MaterialTheme.typography.bodySmall)
            } else {
                Text(
                    "Импортируй WireGuard .conf, созданный в личном кабинете провайдера. Нужны маршруты IPv4 и IPv6 по умолчанию.",
                    color = colors.dim, style = MaterialTheme.typography.bodySmall,
                )
            }
            OutlinedButton(
                onClick = { picker.launch(arrayOf("text/*", "application/octet-stream", "application/x-wireguard-profile")) },
                modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp),
            ) { Text(if (hasConfig) "Заменить конфигурацию" else "Импортировать .conf") }

            when (val current = state) {
                is VpnState.Connected -> Text("Подключено · ${current.protocol}", color = colors.accent)
                is VpnState.Preparing -> Text("Подключение…", color = colors.dim)
                is VpnState.Error -> Text(current.message, color = MaterialTheme.colorScheme.error)
                VpnState.Disconnected -> Text("Отключено", color = colors.dim)
            }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
            val connected = state is VpnState.Connected
            Button(
                onClick = {
                    error = null
                    val request = VpnService.prepare(context)
                    if (request != null) permission.launch(request)
                    else scope.launch { runCatching { SwagaVpnManager.connect(context) }.onFailure { error = it.message } }
                },
                enabled = hasConfig && !connected && state !is VpnState.Preparing,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = colors.accent, contentColor = colors.onAccent),
            ) { Text("Подключить") }
            OutlinedButton(
                onClick = { scope.launch { runCatching { SwagaVpnManager.disconnect() }.onFailure { error = it.message } } },
                enabled = connected || state is VpnState.Preparing,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Отключить") }
            Text(
                "Конфигурация хранится локально в зашифрованном виде Android Keystore. Пароль аккаунта провайдера SwagaBrowser не получает.",
                color = colors.dim, style = MaterialTheme.typography.labelSmall,
            )
            Spacer(Modifier.height(4.dp))
        }
    }
}
