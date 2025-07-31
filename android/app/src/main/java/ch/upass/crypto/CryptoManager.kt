package ch.upass.crypto

import android.util.Base64
import org.signal.argon2.Argon2
import org.signal.argon2.MemoryCost
import org.signal.argon2.Type
import org.signal.argon2.Version
import java.nio.charset.StandardCharsets
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * CryptoManager handles all cryptographic operations for UPass.
 * Implements Argon2id key derivation and AES-GCM encryption as specified in the protocol.
 */
class CryptoManager {
    
    companion object {
        // Argon2id parameters
        private const val OPSLIMIT = 4
        private const val MEMLIMIT = 1073741824 // 1GB
        private const val SALT_SIZE = 16
        private const val KEY_SIZE = 32
        
        // AES-GCM parameters
        private const val GCM_IV_LENGTH = 12
        private const val GCM_TAG_LENGTH = 16
    }
    
    /**
     * Derives keys from master password and username using Argon2id.
     * Returns CryptoKeys containing both signing key seed and vault encryption key.
     */
    fun deriveKeys(masterPassword: String, username: String): CryptoKeys {
        val salt = createSalt(username)
        
        // Derive Ed25519 signing key seed
        val signingKeySeed = deriveArgon2Key(masterPassword, salt)
        
        // Derive AES vault encryption key
        val vaultPassword = masterPassword + "vault"
        val vaultEncryptionKey = deriveArgon2Key(vaultPassword, salt)
        
        return CryptoKeys(
            signingKeySeed = signingKeySeed,
            vaultEncryptionKey = vaultEncryptionKey
        )
    }
    
    /**
     * Creates a deterministic salt from username.
     * Username is UTF-8 encoded, padded/truncated to 16 bytes.
     */
    private fun createSalt(username: String): ByteArray {
        val usernameBytes = username.toByteArray(StandardCharsets.UTF_8)
        val salt = ByteArray(SALT_SIZE)
        
        // Copy username bytes to salt, padding with zeros if needed
        val copyLength = minOf(usernameBytes.size, SALT_SIZE)
        System.arraycopy(usernameBytes, 0, salt, 0, copyLength)
        
        return salt
    }
    
    /**
     * Derives a key using Argon2id with specified parameters.
     */
    private fun deriveArgon2Key(password: String, salt: ByteArray): ByteArray {
        return try {
            val argon2 = Argon2.Builder(Version.V13)
                .type(Type.Argon2id)
                .memoryCost(MemoryCost.MiB(1024)) // 1GB
                .parallelism(1)
                .iterations(OPSLIMIT)
                .build()
            
            val result = argon2.hash(password.toByteArray(StandardCharsets.UTF_8), salt)
            result.hash.copyOfRange(0, KEY_SIZE)
        } catch (e: Exception) {
            throw CryptoException("Failed to derive key with Argon2id", e)
        }
    }
    
    /**
     * Encrypts vault data using AES-GCM.
     * Returns base64-encoded encrypted data with IV prepended.
     */
    fun encryptVault(vaultJson: String, encryptionKey: ByteArray): String {
        try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            val secretKey = SecretKeySpec(encryptionKey, "AES")
            
            // Generate random IV
            val iv = ByteArray(GCM_IV_LENGTH)
            SecureRandom().nextBytes(iv)
            
            val gcmParameterSpec = GCMParameterSpec(GCM_TAG_LENGTH * 8, iv)
            cipher.init(Cipher.ENCRYPT_MODE, secretKey, gcmParameterSpec)
            
            val encryptedData = cipher.doFinal(vaultJson.toByteArray(StandardCharsets.UTF_8))
            
            // Prepend IV to encrypted data
            val result = ByteArray(iv.size + encryptedData.size)
            System.arraycopy(iv, 0, result, 0, iv.size)
            System.arraycopy(encryptedData, 0, result, iv.size, encryptedData.size)
            
            return Base64.encodeToString(result, Base64.NO_WRAP)
        } catch (e: Exception) {
            throw CryptoException("Failed to encrypt vault", e)
        }
    }
    
    /**
     * Decrypts vault data using AES-GCM.
     * Expects base64-encoded data with IV prepended.
     */
    fun decryptVault(encryptedVaultB64: String, encryptionKey: ByteArray): String {
        try {
            val encryptedData = Base64.decode(encryptedVaultB64, Base64.NO_WRAP)
            
            if (encryptedData.size < GCM_IV_LENGTH) {
                throw CryptoException("Invalid encrypted data: too short")
            }
            
            // Extract IV and encrypted data
            val iv = ByteArray(GCM_IV_LENGTH)
            val cipherData = ByteArray(encryptedData.size - GCM_IV_LENGTH)
            System.arraycopy(encryptedData, 0, iv, 0, GCM_IV_LENGTH)
            System.arraycopy(encryptedData, GCM_IV_LENGTH, cipherData, 0, cipherData.size)
            
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            val secretKey = SecretKeySpec(encryptionKey, "AES")
            val gcmParameterSpec = GCMParameterSpec(GCM_TAG_LENGTH * 8, iv)
            
            cipher.init(Cipher.DECRYPT_MODE, secretKey, gcmParameterSpec)
            val decryptedData = cipher.doFinal(cipherData)
            
            return String(decryptedData, StandardCharsets.UTF_8)
        } catch (e: Exception) {
            throw CryptoException("Failed to decrypt vault", e)
        }
    }
    
    /**
     * Generates a cryptographically secure password.
     */
    fun generatePassword(
        length: Int = 16,
        includeSpecialChars: Boolean = true
    ): String {
        val lowercase = "abcdefghijklmnopqrstuvwxyz"
        val uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        val numbers = "0123456789"
        val specials = "!@#$%^&*-_=+"
        
        val allChars = lowercase + uppercase + numbers + if (includeSpecialChars) specials else ""
        val password = StringBuilder()
        val random = SecureRandom()
        
        // Ensure at least one of each type
        password.append(lowercase[random.nextInt(lowercase.length)])
        password.append(uppercase[random.nextInt(uppercase.length)])
        password.append(numbers[random.nextInt(numbers.length)])
        if (includeSpecialChars && length > 3) {
            password.append(specials[random.nextInt(specials.length)])
        }
        
        // Fill remaining length
        val remainingLength = length - password.length
        repeat(remainingLength) {
            password.append(allChars[random.nextInt(allChars.length)])
        }
        
        // Shuffle the password
        val chars = password.toString().toCharArray()
        for (i in chars.indices) {
            val j = random.nextInt(chars.size)
            val temp = chars[i]
            chars[i] = chars[j]
            chars[j] = temp
        }
        
        return String(chars)
    }
    
    /**
     * Data class to hold derived cryptographic keys.
     */
    data class CryptoKeys(
        val signingKeySeed: ByteArray,
        val vaultEncryptionKey: ByteArray
    ) {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            
            other as CryptoKeys
            
            if (!signingKeySeed.contentEquals(other.signingKeySeed)) return false
            if (!vaultEncryptionKey.contentEquals(other.vaultEncryptionKey)) return false
            
            return true
        }
        
        override fun hashCode(): Int {
            var result = signingKeySeed.contentHashCode()
            result = 31 * result + vaultEncryptionKey.contentHashCode()
            return result
        }
    }
}

/**
 * Exception thrown when cryptographic operations fail.
 */
class CryptoException(message: String, cause: Throwable? = null) : Exception(message, cause)