package ch.upass.session

import android.content.Context
import android.content.SharedPreferences
import android.util.Base64
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import ch.upass.crypto.CryptoManager
import ch.upass.crypto.SigningManager
import java.net.URL

/**
 * Manages user sessions with encrypted storage.
 * Handles session creation, validation, and cleanup.
 */
class SessionManager(private val context: Context) {
    
    companion object {
        private const val SESSION_TIMEOUT_MS = 86400000L // 24 hours (was 1 hour)
        private const val PREF_KEY_USERNAME = "username"
        private const val PREF_KEY_PUBLIC_KEY = "public_key_b64"
        private const val PREF_KEY_SIGNING_KEY = "signing_key_bytes"
        private const val PREF_KEY_SECRET_BOX_KEY = "secret_box_key"
        private const val PREF_KEY_TIMESTAMP = "timestamp"
        private const val PREF_KEY_AUTHENTICATED = "authenticated"
        private const val PREF_KEY_SERVER_URL = "server_url"
        private const val PREF_KEY_VAULT_KNOWN_TO_EXIST = "vault_known_to_exist"
        private const val PREF_NAME_SESSION_LIST = "upass_session_list"
    }
    
    private fun getSharedPreferences(serverUrl: String): SharedPreferences {
        val serverHash = serverUrl.hashCode().toString()
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        
        return EncryptedSharedPreferences.create(
            context,
            "upass_session_$serverHash",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    private fun getSessionListPreferences(): SharedPreferences {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        
        return EncryptedSharedPreferences.create(
            context,
            PREF_NAME_SESSION_LIST,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    /**
     * Creates a new session after successful authentication.
     */
    fun createSession(
        username: String,
        serverUrl: String,
        cryptoKeys: CryptoManager.CryptoKeys,
        signingManager: SigningManager
    ) {
        val prefs = getSharedPreferences(serverUrl)
        val timestamp = System.currentTimeMillis()
        
        prefs.edit()
            .putString(PREF_KEY_USERNAME, username)
            .putString(PREF_KEY_PUBLIC_KEY, signingManager.getPublicKeyB64())
            .putString(PREF_KEY_SIGNING_KEY, Base64.encodeToString(cryptoKeys.signingKeySeed, Base64.NO_WRAP))
            .putString(PREF_KEY_SECRET_BOX_KEY, Base64.encodeToString(cryptoKeys.vaultEncryptionKey, Base64.NO_WRAP))
            .putLong(PREF_KEY_TIMESTAMP, timestamp)
            .putBoolean(PREF_KEY_AUTHENTICATED, true)
            .putString(PREF_KEY_SERVER_URL, serverUrl)
            .putBoolean(PREF_KEY_VAULT_KNOWN_TO_EXIST, true) // New vault, so it exists
            .apply()
        
        // Add to session list
        addToSessionList(serverUrl, username)
    }
    
    /**
     * Validates an existing session and returns session data if valid.
     */
    fun validateSession(serverUrl: String): SessionData? {
        val prefs = getSharedPreferences(serverUrl)
        
        if (!prefs.getBoolean(PREF_KEY_AUTHENTICATED, false)) {
            return null
        }
        
        val timestamp = prefs.getLong(PREF_KEY_TIMESTAMP, 0)
        val currentTime = System.currentTimeMillis()
        
        // Check if session has expired
        if (currentTime - timestamp > SESSION_TIMEOUT_MS) {
            clearSession(serverUrl)
            return null
        }
        
        val username = prefs.getString(PREF_KEY_USERNAME, null) ?: return null
        val publicKeyB64 = prefs.getString(PREF_KEY_PUBLIC_KEY, null) ?: return null
        val signingKeyB64 = prefs.getString(PREF_KEY_SIGNING_KEY, null) ?: return null
        val secretBoxKeyB64 = prefs.getString(PREF_KEY_SECRET_BOX_KEY, null) ?: return null
        
        return try {
            val signingKeySeed = Base64.decode(signingKeyB64, Base64.NO_WRAP)
            val vaultEncryptionKey = Base64.decode(secretBoxKeyB64, Base64.NO_WRAP)
            
            SessionData(
                username = username,
                serverUrl = serverUrl,
                publicKeyB64 = publicKeyB64,
                signingKeySeed = signingKeySeed,
                vaultEncryptionKey = vaultEncryptionKey,
                timestamp = timestamp
            )
        } catch (e: Exception) {
            clearSession(serverUrl)
            null
        }
    }
    
    /**
     * Updates the session timestamp to extend the session.
     */
    fun refreshSession(serverUrl: String) {
        val prefs = getSharedPreferences(serverUrl)
        if (prefs.getBoolean(PREF_KEY_AUTHENTICATED, false)) {
            prefs.edit()
                .putLong(PREF_KEY_TIMESTAMP, System.currentTimeMillis())
                .apply()
        }
    }
    
    /**
     * Clears the session data.
     */
    fun clearSession(serverUrl: String) {
        val prefs = getSharedPreferences(serverUrl)
        prefs.edit().clear().apply()
        
        // Remove from session list
        removeFromSessionList(serverUrl)
    }
    
    /**
     * Checks if there's a valid session for the given server.
     */
    fun hasValidSession(serverUrl: String): Boolean {
        return validateSession(serverUrl) != null
    }
    
    /**
     * Gets the current username for the session, if any.
     */
    fun getCurrentUsername(serverUrl: String): String? {
        return validateSession(serverUrl)?.username
    }
    
    /**
     * Restores crypto managers from session data.
     */
    fun restoreManagers(serverUrl: String): RestoredManagers? {
        val sessionData = validateSession(serverUrl) ?: return null
        
        val cryptoKeys = CryptoManager.CryptoKeys(
            signingKeySeed = sessionData.signingKeySeed,
            vaultEncryptionKey = sessionData.vaultEncryptionKey
        )
        
        val signingManager = SigningManager().apply {
            initializeKeys(sessionData.signingKeySeed)
        }
        
        return RestoredManagers(
            cryptoKeys = cryptoKeys,
            signingManager = signingManager
        )
    }
    
    /**
     * Gets all active sessions.
     */
    fun getAllSessions(): List<Pair<String, String>> {
        val listPrefs = getSessionListPreferences()
        val sessions = mutableListOf<Pair<String, String>>()
        
        val allEntries = listPrefs.all
        for ((key, value) in allEntries) {
            if (key.startsWith("session_") && value is String) {
                val serverUrl = key.removePrefix("session_")
                sessions.add(Pair(serverUrl, value))
            }
        }
        
        // Sort by timestamp (most recent first)
        return sessions.sortedByDescending { (serverUrl, _) ->
            getSharedPreferences(serverUrl).getLong(PREF_KEY_TIMESTAMP, 0)
        }
    }
    
    /**
     * Adds a session to the session list.
     */
    private fun addToSessionList(serverUrl: String, username: String) {
        val listPrefs = getSessionListPreferences()
        listPrefs.edit()
            .putString("session_$serverUrl", username)
            .apply()
    }
    
    /**
     * Removes a session from the session list.
     */
    private fun removeFromSessionList(serverUrl: String) {
        val listPrefs = getSessionListPreferences()
        listPrefs.edit()
            .remove("session_$serverUrl")
            .apply()
    }
    
    /**
     * Data class representing session information.
     */
    data class SessionData(
        val username: String,
        val serverUrl: String,
        val publicKeyB64: String,
        val signingKeySeed: ByteArray,
        val vaultEncryptionKey: ByteArray,
        val timestamp: Long
    ) {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            
            other as SessionData
            
            if (username != other.username) return false
            if (serverUrl != other.serverUrl) return false
            if (publicKeyB64 != other.publicKeyB64) return false
            if (!signingKeySeed.contentEquals(other.signingKeySeed)) return false
            if (!vaultEncryptionKey.contentEquals(other.vaultEncryptionKey)) return false
            if (timestamp != other.timestamp) return false
            
            return true
        }
        
        override fun hashCode(): Int {
            var result = username.hashCode()
            result = 31 * result + serverUrl.hashCode()
            result = 31 * result + publicKeyB64.hashCode()
            result = 31 * result + signingKeySeed.contentHashCode()
            result = 31 * result + vaultEncryptionKey.contentHashCode()
            result = 31 * result + timestamp.hashCode()
            return result
        }
    }
    
    /**
     * Data class for restored crypto managers.
     */
    data class RestoredManagers(
        val cryptoKeys: CryptoManager.CryptoKeys,
        val signingManager: SigningManager
    )
    
    /**
     * Checks if vault is known to exist for the session.
     */
    fun isVaultKnownToExist(serverUrl: String): Boolean {
        val prefs = getSharedPreferences(serverUrl)
        return prefs.getBoolean(PREF_KEY_VAULT_KNOWN_TO_EXIST, false)
    }
    
    /**
     * Sets vault existence state.
     */
    fun setVaultKnownToExist(serverUrl: String, exists: Boolean) {
        val prefs = getSharedPreferences(serverUrl)
        prefs.edit()
            .putBoolean(PREF_KEY_VAULT_KNOWN_TO_EXIST, exists)
            .apply()
    }
}