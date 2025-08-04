package ch.upass.models

import com.google.gson.annotations.SerializedName
import java.io.Serializable
import java.time.Instant

/**
 * Represents a single entry in the vault.
 */
data class VaultEntry(
    @SerializedName("username")
    val username: String,
    
    @SerializedName("password")
    val password: String,
    
    @SerializedName("note")
    val note: String,
    
    @SerializedName("created_at")
    val createdAt: String = Instant.now().toString(),
    
    @SerializedName("updated_at")
    val updatedAt: String = Instant.now().toString(),
    
    // TOTP fields (optional)
    @SerializedName("totp_secret")
    val totpSecret: String? = null
) : Serializable {
    companion object {
        const val MAX_NOTE_LENGTH = 128
        const val MAX_USERNAME_LENGTH = 64
        const val MAX_PASSWORD_LENGTH = 128
        const val MAX_TOTP_SECRET_LENGTH = 64
        const val MAX_VAULT_ENTRIES = 1024
        const val MAX_VAULT_SIZE_KB = 1024
        
        /**
         * Validates a vault entry according to protocol constraints.
         * Uses relaxed validation to match CLI behavior.
         */
        fun validate(entry: VaultEntry): Boolean {
            return entry.note.isNotBlank() &&
                   entry.note.length <= MAX_NOTE_LENGTH &&
                   entry.username.length <= MAX_USERNAME_LENGTH &&
                   entry.password.isNotBlank() &&
                   entry.password.length <= MAX_PASSWORD_LENGTH &&
                   (entry.totpSecret == null || entry.totpSecret.length <= MAX_TOTP_SECRET_LENGTH)
        }
    }
    
    /**
     * Creates a copy of this entry with updated timestamp.
     */
    fun withUpdatedTimestamp(): VaultEntry {
        return copy(updatedAt = Instant.now().toString())
    }
}