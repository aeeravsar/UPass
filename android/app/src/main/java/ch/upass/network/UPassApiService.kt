package ch.upass.network

import ch.upass.models.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Retrofit API service interface for UPass server communication.
 */
interface UPassApiService {
    
    /**
     * Health check endpoint.
     */
    @GET("health")
    suspend fun getHealth(): Response<HealthResponse>
    
    /**
     * Check if a vault exists for a username.
     */
    @GET("vaults/{username}/exists")
    suspend fun checkVaultExists(
        @Path("username") username: String
    ): Response<VaultExistsResponse>
    
    /**
     * Retrieve vault contents with authentication.
     */
    @POST("vaults/{username}/retrieve")
    suspend fun getVault(
        @Path("username") username: String,
        @Body request: GetVaultRequest
    ): Response<GetVaultResponse>
    
    /**
     * Save or update vault for a specific username.
     */
    @PUT("vaults/{username}")
    suspend fun saveVault(
        @Path("username") username: String,
        @Body request: SaveVaultRequest
    ): Response<SuccessResponse>
    
    /**
     * Delete vault for a specific username.
     */
    @POST("vaults/{username}/delete")
    suspend fun deleteVault(
        @Path("username") username: String,
        @Body request: DeleteVaultRequest
    ): Response<SuccessResponse>
}