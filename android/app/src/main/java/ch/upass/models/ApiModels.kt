package ch.upass.models

import com.google.gson.annotations.SerializedName

/**
 * Request model for getting a vault.
 */
data class GetVaultRequest(
    @SerializedName("public_key")
    val publicKey: String,
    
    @SerializedName("signing_key")
    val signingKey: String,
    
    @SerializedName("timestamp")
    val timestamp: Long,
    
    @SerializedName("signature")
    val signature: String
)

/**
 * Response model for getting a vault.
 */
data class GetVaultResponse(
    @SerializedName("vault_blob")
    val vaultBlob: String
)

/**
 * Request model for saving/updating a vault.
 */
data class SaveVaultRequest(
    @SerializedName("public_key")
    val publicKey: String,
    
    @SerializedName("signing_key")
    val signingKey: String,
    
    @SerializedName("timestamp")
    val timestamp: Long,
    
    @SerializedName("vault_blob")
    val vaultBlob: String,
    
    @SerializedName("signature")
    val signature: String,
    
    @SerializedName("create_if_missing")
    val createIfMissing: Boolean = true
)

/**
 * Request model for deleting a vault.
 */
data class DeleteVaultRequest(
    @SerializedName("public_key")
    val publicKey: String,
    
    @SerializedName("signing_key")
    val signingKey: String,
    
    @SerializedName("timestamp")
    val timestamp: Long,
    
    @SerializedName("signature")
    val signature: String
)

/**
 * Generic success response.
 */
data class SuccessResponse(
    @SerializedName("success")
    val success: Boolean
)

/**
 * Health check response.
 */
data class HealthResponse(
    @SerializedName("status")
    val status: String
)

/**
 * Vault exists check response.
 */
data class VaultExistsResponse(
    @SerializedName("exists")
    val exists: Boolean
)

/**
 * Error response.
 */
data class ErrorResponse(
    @SerializedName("error")
    val error: String
)

/**
 * Sealed class for representing API results.
 */
sealed class ApiResult<T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error<T>(val message: String, val code: Int? = null) : ApiResult<T>()
    class Loading<T> : ApiResult<T>()
}

/**
 * Network exceptions for specific HTTP status codes.
 */
sealed class NetworkException(message: String, val code: Int) : Exception(message) {
    class BadRequest(message: String) : NetworkException(message, 400)
    class Unauthorized(message: String) : NetworkException(message, 401)
    class NotFound(message: String) : NetworkException(message, 404)
    class Conflict(message: String) : NetworkException(message, 409)
    class TooManyRequests(message: String) : NetworkException(message, 429)
    class InternalServerError(message: String) : NetworkException(message, 500)
    class Unknown(message: String, code: Int) : NetworkException(message, code)
}