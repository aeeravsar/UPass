package ch.upass.crypto

import java.nio.ByteBuffer
import java.security.InvalidKeyException
import java.security.NoSuchAlgorithmException
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlin.experimental.and

/**
 * Manages Time-based One-Time Password (TOTP) generation.
 * Implements RFC 6238 TOTP algorithm.
 */
object TOTPManager {
    
    private const val DEFAULT_TIME_STEP = 30L // seconds
    private const val DEFAULT_DIGITS = 6
    private const val DEFAULT_ALGORITHM = "HmacSHA1"
    
    /**
     * Generates a TOTP code from the given secret.
     * 
     * @param secret Base32 encoded secret
     * @param timeStep Time step in seconds (default: 30)
     * @param digits Number of digits (default: 6)
     * @param algorithm HMAC algorithm (default: SHA1)
     * @return TOTP code as string with leading zeros if necessary
     */
    fun generateTOTP(
        secret: String,
        timeStep: Long = DEFAULT_TIME_STEP,
        digits: Int = DEFAULT_DIGITS,
        algorithm: String = DEFAULT_ALGORITHM
    ): String {
        val key = base32Decode(secret)
        val timeCounter = System.currentTimeMillis() / 1000L / timeStep
        
        return generateHOTP(key, timeCounter, digits, algorithm)
    }
    
    /**
     * Gets the remaining seconds until the current TOTP expires.
     * 
     * @param timeStep Time step in seconds (default: 30)
     * @return Remaining seconds
     */
    fun getRemainingSeconds(timeStep: Long = DEFAULT_TIME_STEP): Int {
        val currentSeconds = System.currentTimeMillis() / 1000L
        return (timeStep - (currentSeconds % timeStep)).toInt()
    }
    
    /**
     * Generates HOTP value.
     */
    private fun generateHOTP(
        key: ByteArray,
        counter: Long,
        digits: Int,
        algorithm: String
    ): String {
        val counterBytes = ByteBuffer.allocate(8).putLong(counter).array()
        
        val mac = try {
            Mac.getInstance(algorithm).apply {
                init(SecretKeySpec(key, "RAW"))
            }
        } catch (e: NoSuchAlgorithmException) {
            throw IllegalArgumentException("Invalid algorithm: $algorithm", e)
        } catch (e: InvalidKeyException) {
            throw IllegalArgumentException("Invalid key", e)
        }
        
        val hash = mac.doFinal(counterBytes)
        val offset = (hash[hash.size - 1] and 0x0F).toInt()
        
        val truncatedHash = ByteBuffer.wrap(hash, offset, 4).int and 0x7FFFFFFF
        val otp = truncatedHash % Math.pow(10.0, digits.toDouble()).toInt()
        
        return otp.toString().padStart(digits, '0')
    }
    
    /**
     * Decodes a Base32 string to bytes.
     * Implements standard Base32 decoding (RFC 4648).
     */
    private fun base32Decode(base32: String): ByteArray {
        val alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
        val lookup = IntArray(128) { -1 }
        alphabet.forEachIndexed { index, char -> lookup[char.code] = index }
        
        val input = base32.uppercase().replace(" ", "").trimEnd('=')
        val output = mutableListOf<Byte>()
        
        var buffer = 0
        var bitsLeft = 0
        
        for (char in input) {
            val value = lookup.getOrNull(char.code) ?: -1
            if (value == -1) {
                throw IllegalArgumentException("Invalid Base32 character: $char")
            }
            
            buffer = (buffer shl 5) or value
            bitsLeft += 5
            
            if (bitsLeft >= 8) {
                output.add((buffer shr (bitsLeft - 8)).toByte())
                bitsLeft -= 8
            }
        }
        
        return output.toByteArray()
    }
    
    /**
     * Validates a TOTP secret.
     * 
     * @param secret Base32 encoded secret
     * @return true if valid, false otherwise
     */
    fun isValidSecret(secret: String): Boolean {
        return try {
            val decoded = base32Decode(secret)
            decoded.isNotEmpty() && decoded.size >= 10 // At least 80 bits
        } catch (e: Exception) {
            false
        }
    }
    
    /**
     * Formats a TOTP code for display (e.g., "123456" -> "123 456")
     */
    fun formatCode(code: String): String {
        return if (code.length == 6) {
            "${code.substring(0, 3)} ${code.substring(3)}"
        } else {
            code
        }
    }
    
    /**
     * Extracts TOTP parameters from a standard otpauth URI.
     * Format: otpauth://totp/Account?secret=BASE32SECRET
     */
    fun parseOtpauthUri(uri: String): OtpAuthParams? {
        if (!uri.startsWith("otpauth://totp/")) return null
        
        try {
            val uriWithoutScheme = uri.removePrefix("otpauth://totp/")
            val parts = uriWithoutScheme.split("?")
            if (parts.size != 2) return null
            
            val pathPart = parts[0]
            val queryPart = parts[1]
            
            // Parse query parameters
            val params = queryPart.split("&").associate {
                val keyValue = it.split("=", limit = 2)
                if (keyValue.size == 2) keyValue[0] to keyValue[1] else "" to ""
            }
            
            val secret = params["secret"] ?: return null
            
            // Parse label (account only, ignore issuer)
            val labelParts = pathPart.split(":", limit = 2)
            val account = if (labelParts.size == 2) {
                labelParts[1]  // Use account part after colon
            } else {
                labelParts[0]  // Use full label as account
            }
            
            return OtpAuthParams(
                secret = secret,
                account = account,
                digits = params["digits"]?.toIntOrNull() ?: DEFAULT_DIGITS,
                period = params["period"]?.toLongOrNull() ?: DEFAULT_TIME_STEP,
                algorithm = when (params["algorithm"]?.uppercase()) {
                    "SHA256" -> "HmacSHA256"
                    "SHA512" -> "HmacSHA512"
                    else -> DEFAULT_ALGORITHM
                }
            )
        } catch (e: Exception) {
            return null
        }
    }
    
    data class OtpAuthParams(
        val secret: String,
        val account: String,
        val digits: Int = DEFAULT_DIGITS,
        val period: Long = DEFAULT_TIME_STEP,
        val algorithm: String = DEFAULT_ALGORITHM
    )
}