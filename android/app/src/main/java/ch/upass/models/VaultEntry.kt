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
    val updatedAt: String = Instant.now().toString()
) : Serializable {
    companion object {
        const val MAX_USERNAME_LENGTH = 32
        const val MAX_PASSWORD_LENGTH = 128
        const val MAX_VAULT_ENTRIES = 256
        const val MAX_VAULT_SIZE_KB = 100
        
        /**
         * Validates a vault entry according to protocol constraints.
         * Uses relaxed validation to match CLI behavior.
         */
        fun validate(entry: VaultEntry): Boolean {
            return entry.password.isNotBlank() &&
                   entry.password.length <= MAX_PASSWORD_LENGTH &&
                   entry.note.isNotBlank()
        }
    }
    
    /**
     * Creates a copy of this entry with updated timestamp.
     */
    fun withUpdatedTimestamp(): VaultEntry {
        return copy(updatedAt = Instant.now().toString())
    }
}