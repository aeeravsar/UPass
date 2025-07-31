package ch.upass.crypto

import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * SigningManager handles HMAC-SHA256 signature operations for UPass.
 * Uses standard HMAC-SHA256 for cross-platform compatibility.
 */
class SigningManager {
    
    private var signingKey: ByteArray? = null
    private var publicKeyBytes: ByteArray? = null
    
    /**
     * Initializes HMAC signing keys from the seed derived by CryptoManager.
     * Uses the same key derivation as the CLI for compatibility.
     */
    fun initializeKeys(seed: ByteArray) {
        try {
            // Use the 32-byte seed directly as HMAC signing key
            if (seed.size != 32) {
                throw CryptoException("Invalid seed size: expected 32 bytes, got ${seed.size}")
            }
            
            // Store the signing key
            signingKey = seed.copyOf()
            
            // Public key is SHA256 of the signing key (same as CLI)
            val digest = MessageDigest.getInstance("SHA-256")
            publicKeyBytes = digest.digest(seed)
            
        } catch (e: Exception) {
            throw CryptoException("Failed to initialize signing keys", e)
        }
    }
    
    /**
     * Signs a message using HMAC-SHA256.
     * Returns base64-encoded signature.
     */
    fun sign(message: String): String {
        val signingKey = this.signingKey 
            ?: throw CryptoException("Signing key not initialized")
        
        try {
            val messageBytes = message.toByteArray(StandardCharsets.UTF_8)
            val mac = Mac.getInstance("HmacSHA256")
            val keySpec = SecretKeySpec(signingKey, "HmacSHA256")
            mac.init(keySpec)
            val signature = mac.doFinal(messageBytes)
            
            return Base64.encodeToString(signature, Base64.NO_WRAP)
        } catch (e: Exception) {
            throw CryptoException("Failed to sign message", e)
        }
    }
    
    /**
     * Gets the base64-encoded public key (SHA256 of signing key).
     */
    fun getPublicKeyB64(): String {
        val publicKeyBytes = this.publicKeyBytes 
            ?: throw CryptoException("Public key not initialized")
        
        return Base64.encodeToString(publicKeyBytes, Base64.NO_WRAP)
    }
    
    /**
     * Gets the base64-encoded signing key for API requests.
     */
    fun getSigningKeyB64(): String {
        val signingKey = this.signingKey 
            ?: throw CryptoException("Signing key not initialized")
        
        return Base64.encodeToString(signingKey, Base64.NO_WRAP)
    }
    
    /**
     * Creates signature for GET vault operation.
     */
    fun signGetVault(timestamp: Long): String {
        val message = "get_vault$timestamp"
        return sign(message)
    }
    
    /**
     * Creates signature for PUT vault operation.
     */
    fun signPutVault(vaultBlob: String, timestamp: Long): String {
        val message = "$vaultBlob$timestamp"
        return sign(message)
    }
    
    /**
     * Creates signature for DELETE vault operation.
     */
    fun signDeleteVault(timestamp: Long): String {
        val message = "delete_vault$timestamp"
        return sign(message)
    }
    
    /**
     * Clears sensitive key material from memory.
     */
    fun clearKeys() {
        signingKey?.fill(0)
        signingKey = null
        publicKeyBytes = null
    }
}