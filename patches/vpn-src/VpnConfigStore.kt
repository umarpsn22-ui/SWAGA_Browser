package app.swaga.browser.vpn

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.io.File
import java.nio.ByteBuffer
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

internal object VpnConfigStore {
    private const val ALIAS = "swaga_vpn_config_v1"
    private const val FILE = "swaga-vpn-profile.bin"
    private const val PREFS = "swaga_vpn_profile_meta"

    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(ALIAS, null) as? SecretKey)?.let { return it }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(
            KeyGenParameterSpec.Builder(
                ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build(),
        )
        return generator.generateKey()
    }

    fun save(context: Context, config: String, provider: String, server: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val encrypted = cipher.doFinal(config.toByteArray(Charsets.UTF_8))
        val data = ByteBuffer.allocate(4 + cipher.iv.size + encrypted.size)
            .putInt(cipher.iv.size).put(cipher.iv).put(encrypted).array()
        File(context.filesDir, FILE).writeBytes(data)
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString("provider", provider).putString("server", server).apply()
    }

    fun load(context: Context): String? {
        val file = File(context.filesDir, FILE)
        if (!file.isFile) return null
        val b = ByteBuffer.wrap(file.readBytes())
        if (b.remaining() < 5) return null
        val size = b.int
        if (size !in 12..16 || b.remaining() <= size) return null
        val iv = ByteArray(size).also { b.get(it) }
        val encrypted = ByteArray(b.remaining()).also { b.get(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, iv))
        return cipher.doFinal(encrypted).toString(Charsets.UTF_8)
    }

    fun exists(context: Context) = File(context.filesDir, FILE).isFile
    fun provider(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .getString("provider", "custom").orEmpty()
    fun server(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .getString("server", "WireGuard сервер").orEmpty()
    fun clear(context: Context) {
        File(context.filesDir, FILE).delete()
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()
    }
}
