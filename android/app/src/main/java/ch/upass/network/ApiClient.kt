package ch.upass.network

import ch.upass.models.*
import ch.upass.crypto.SigningManager
import com.google.gson.Gson
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * API client for communicating with UPass server.
 * Handles request signing and response processing.
 */
class ApiClient(
    private val baseUrl: String = "https://server.upass.ch/",
    private val signingManager: SigningManager
) {
    
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(httpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val apiService = retrofit.create(UPassApiService::class.java)
    private val gson = Gson()
    
    /**
     * Checks server health.
     */
    suspend fun checkHealth(): ApiResult<HealthResponse> {
        return safeApiCall {
            apiService.getHealth()
        }
    }
    
    /**
     * Checks if a vault exists for the given username.
     */
    suspend fun checkVaultExists(username: String): ApiResult<VaultExistsResponse> {
        return safeApiCall {
            apiService.checkVaultExists(username)
        }
    }
    
    /**
     * Gets vault for the specified username.
     */
    suspend fun getVault(username: String): ApiResult<GetVaultResponse> {
        val timestamp = System.currentTimeMillis() / 1000
        val signature = signingManager.signGetVault(timestamp)
        val publicKey = signingManager.getPublicKeyB64()
        
        val request = GetVaultRequest(
            publicKey = publicKey,
            signingKey = signingManager.getSigningKeyB64(),
            timestamp = timestamp,
            signature = signature
        )
        
        return safeApiCall {
            apiService.getVault(username, request)
        }
    }
    
    /**
     * Saves vault for the specified username.
     */
    suspend fun saveVault(username: String, vaultBlob: String, createIfMissing: Boolean = true): ApiResult<SuccessResponse> {
        val timestamp = System.currentTimeMillis() / 1000
        val signature = signingManager.signPutVault(vaultBlob, timestamp)
        val publicKey = signingManager.getPublicKeyB64()
        
        val request = SaveVaultRequest(
            publicKey = publicKey,
            signingKey = signingManager.getSigningKeyB64(),
            timestamp = timestamp,
            vaultBlob = vaultBlob,
            signature = signature,
            createIfMissing = createIfMissing
        )
        
        return safeApiCall {
            apiService.saveVault(username, request)
        }
    }
    
    /**
     * Deletes vault for the specified username.
     */
    suspend fun deleteVault(username: String): ApiResult<SuccessResponse> {
        val timestamp = System.currentTimeMillis() / 1000
        val signature = signingManager.signDeleteVault(timestamp)
        val publicKey = signingManager.getPublicKeyB64()
        
        val request = DeleteVaultRequest(
            publicKey = publicKey,
            signingKey = signingManager.getSigningKeyB64(),
            timestamp = timestamp,
            signature = signature
        )
        
        return safeApiCall {
            apiService.deleteVault(username, request)
        }
    }
    
    /**
     * Safely executes API calls and handles errors.
     */
    private suspend fun <T> safeApiCall(apiCall: suspend () -> Response<T>): ApiResult<T> {
        return try {
            val response = apiCall()
            
            if (response.isSuccessful) {
                response.body()?.let { body ->
                    ApiResult.Success(body)
                } ?: ApiResult.Error("Empty response body")
            } else {
                val errorMessage = response.errorBody()?.string()?.let { errorBody ->
                    try {
                        gson.fromJson(errorBody, ErrorResponse::class.java).error
                    } catch (e: Exception) {
                        "HTTP ${response.code()}: ${response.message()}"
                    }
                } ?: "Unknown error"
                
                ApiResult.Error(errorMessage, response.code())
            }
        } catch (e: Exception) {
            ApiResult.Error("Network error: ${e.message}")
        }
    }
}