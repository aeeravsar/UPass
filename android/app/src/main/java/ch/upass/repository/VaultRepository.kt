package ch.upass.repository

import ch.upass.crypto.CryptoManager
import ch.upass.crypto.SigningManager
import ch.upass.models.*
import ch.upass.network.ApiClient
import ch.upass.session.SessionManager
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Repository for vault operations.
 * Handles local caching, encryption/decryption, and server synchronization.
 */
class VaultRepository(
    private val sessionManager: SessionManager,
    private val cryptoManager: CryptoManager
) {
    
    private val gson = Gson()
    
    // In-memory cache for vault entries
    private var cachedEntries: List<VaultEntry>? = null
    private var cacheTimestamp: Long = 0
    private val cacheTimeout = 300000L // 5 minutes
    
    /**
     * Logs in existing user.
     */
    suspend fun loginUser(
        username: String, 
        masterPassword: String, 
        serverUrl: String
    ): ApiResult<Unit> = withContext(Dispatchers.IO) {
        
        // Validate username
        if (!isValidUsername(username)) {
            return@withContext ApiResult.Error("Invalid username format")
        }
        
        try {
            // First check if vault exists
            val tempApiClient = ApiClient(serverUrl, SigningManager()) // Temporary client for existence check
            
            when (val existsResult = tempApiClient.checkVaultExists(username)) {
                is ApiResult.Success -> {
                    if (!existsResult.data.exists) {
                        return@withContext ApiResult.Error("User does not exist. Please register first.")
                    }
                }
                is ApiResult.Error -> {
                    return@withContext ApiResult.Error("Failed to check user existence: ${existsResult.message}")
                }
                else -> {
                    return@withContext ApiResult.Error("Network error during login")
                }
            }
            
            // Derive cryptographic keys
            val cryptoKeys = cryptoManager.deriveKeys(masterPassword, username)
            val signingManager = SigningManager().apply {
                initializeKeys(cryptoKeys.signingKeySeed)
            }
            
            // Create API client with proper authentication
            val apiClient = ApiClient(serverUrl, signingManager)
            
            // Try to get existing vault
            when (val result = apiClient.getVault(username)) {
                is ApiResult.Success -> {
                    // Existing user - validate by trying to decrypt vault
                    try {
                        cryptoManager.decryptVault(result.data.vaultBlob, cryptoKeys.vaultEncryptionKey)
                        // Decryption successful - create session
                        sessionManager.createSession(username, serverUrl, cryptoKeys, signingManager)
                        ApiResult.Success(Unit)
                    } catch (e: Exception) {
                        ApiResult.Error("Invalid master password")
                    }
                }
                is ApiResult.Error -> {
                    ApiResult.Error("Login failed: ${result.message}")
                }
                else -> ApiResult.Error("Network error during login")
            }
        } catch (e: Exception) {
            ApiResult.Error("Login error: ${e.message}")
        }
    }
    
    /**
     * Registers new user and creates empty vault.
     */
    suspend fun registerUser(
        username: String, 
        masterPassword: String, 
        serverUrl: String
    ): ApiResult<Unit> = withContext(Dispatchers.IO) {
        
        // Validate username
        if (!isValidUsername(username)) {
            return@withContext ApiResult.Error("Invalid username format")
        }
        
        try {
            // First check if vault already exists
            val tempApiClient = ApiClient(serverUrl, SigningManager()) // Temporary client for existence check
            
            when (val existsResult = tempApiClient.checkVaultExists(username)) {
                is ApiResult.Success -> {
                    if (existsResult.data.exists) {
                        return@withContext ApiResult.Error("Username already exists. Please login instead.")
                    }
                }
                is ApiResult.Error -> {
                    return@withContext ApiResult.Error("Failed to check user existence: ${existsResult.message}")
                }
                else -> {
                    return@withContext ApiResult.Error("Network error during registration")
                }
            }
            
            // Derive cryptographic keys
            val cryptoKeys = cryptoManager.deriveKeys(masterPassword, username)
            val signingManager = SigningManager().apply {
                initializeKeys(cryptoKeys.signingKeySeed)
            }
            
            // Create API client
            val apiClient = ApiClient(serverUrl, signingManager)
            
            // Create empty vault
            val emptyVault = emptyList<VaultEntry>()
            val vaultJson = gson.toJson(emptyVault)
            val encryptedVault = cryptoManager.encryptVault(vaultJson, cryptoKeys.vaultEncryptionKey)
            
            when (val result = apiClient.saveVault(username, encryptedVault)) {
                is ApiResult.Success -> {
                    // Registration successful - create session
                    sessionManager.createSession(username, serverUrl, cryptoKeys, signingManager)
                    ApiResult.Success(Unit)
                }
                is ApiResult.Error -> {
                    ApiResult.Error("Registration failed: ${result.message}")
                }
                else -> ApiResult.Error("Network error during registration")
            }
        } catch (e: Exception) {
            ApiResult.Error("Registration error: ${e.message}")
        }
    }
    
    /**
     * Gets vault entries from cache or server.
     */
    suspend fun getVaultEntries(serverUrl: String, forceRefresh: Boolean = false): ApiResult<List<VaultEntry>> = withContext(Dispatchers.IO) {
        
        // Check cache first (unless forcing refresh)
        if (!forceRefresh && isCacheValid()) {
            return@withContext ApiResult.Success(cachedEntries ?: emptyList())
        }
        
        // Restore session and managers
        val restored = sessionManager.restoreManagers(serverUrl)
            ?: return@withContext ApiResult.Error("No valid session")
        
        val username = sessionManager.getCurrentUsername(serverUrl)
            ?: return@withContext ApiResult.Error("No current user")
        
        try {
            val apiClient = ApiClient(serverUrl, restored.signingManager)
            
            when (val result = apiClient.getVault(username)) {
                is ApiResult.Success -> {
                    try {
                        val decryptedJson = cryptoManager.decryptVault(
                            result.data.vaultBlob, 
                            restored.cryptoKeys.vaultEncryptionKey
                        )
                        
                        val listType = object : TypeToken<List<VaultEntry>>() {}.type
                        val entries: List<VaultEntry> = gson.fromJson(decryptedJson, listType)
                        
                        // Update cache
                        cachedEntries = entries
                        cacheTimestamp = System.currentTimeMillis()
                        
                        // Mark vault as known to exist
                        sessionManager.setVaultKnownToExist(serverUrl, true)
                        
                        // Refresh session
                        sessionManager.refreshSession(serverUrl)
                        
                        ApiResult.Success(entries)
                    } catch (e: Exception) {
                        ApiResult.Error("Failed to decrypt vault: ${e.message}")
                    }
                }
                is ApiResult.Error -> {
                    // Handle vault not found
                    if (result.code == 404) {
                        sessionManager.setVaultKnownToExist(serverUrl, false)
                    }
                    ApiResult.Error(result.message, result.code)
                }
                else -> ApiResult.Error("Unexpected error")
            }
        } catch (e: Exception) {
            ApiResult.Error("Failed to get vault: ${e.message}")
        }
    }
    
    /**
     * Saves vault entries to server.
     */
    suspend fun saveVaultEntries(entries: List<VaultEntry>, serverUrl: String): ApiResult<Unit> = withContext(Dispatchers.IO) {
        
        // Validate vault constraints
        if (!validateVault(entries)) {
            return@withContext ApiResult.Error("Vault validation failed")
        }
        
        val restored = sessionManager.restoreManagers(serverUrl)
            ?: return@withContext ApiResult.Error("No valid session")
        
        val username = sessionManager.getCurrentUsername(serverUrl)
            ?: return@withContext ApiResult.Error("No current user")
        
        try {
            val vaultJson = gson.toJson(entries)
            val encryptedVault = cryptoManager.encryptVault(vaultJson, restored.cryptoKeys.vaultEncryptionKey)
            
            val apiClient = ApiClient(serverUrl, restored.signingManager)
            
            // Check if we should allow vault creation
            val vaultKnownToExist = sessionManager.isVaultKnownToExist(serverUrl)
            
            when (val result = apiClient.saveVault(username, encryptedVault, createIfMissing = vaultKnownToExist)) {
                is ApiResult.Success -> {
                    // Update cache
                    cachedEntries = entries
                    cacheTimestamp = System.currentTimeMillis()
                    
                    // Mark vault as known to exist
                    sessionManager.setVaultKnownToExist(serverUrl, true)
                    
                    // Refresh session
                    sessionManager.refreshSession(serverUrl)
                    
                    ApiResult.Success(Unit)
                }
                is ApiResult.Error -> {
                    // Handle vault not found during save
                    if (result.code == 404) {
                        sessionManager.setVaultKnownToExist(serverUrl, false)
                    }
                    ApiResult.Error(result.message, result.code)
                }
                else -> ApiResult.Error("Unexpected error")
            }
        } catch (e: Exception) {
            ApiResult.Error("Failed to save vault: ${e.message}")
        }
    }
    
    /**
     * Adds a new entry to the vault.
     */
    suspend fun addEntry(entry: VaultEntry, serverUrl: String): ApiResult<Unit> {
        if (!VaultEntry.validate(entry)) {
            return ApiResult.Error("Invalid entry data")
        }
        
        val currentEntries = when (val result = getVaultEntries(serverUrl)) {
            is ApiResult.Success -> result.data.toMutableList()
            is ApiResult.Error -> return ApiResult.Error(result.message, result.code)
            else -> return ApiResult.Error("Failed to get current entries")
        }
        
        // Check for duplicate notes (case-insensitive)
        if (currentEntries.any { it.note.equals(entry.note, ignoreCase = true) }) {
            return ApiResult.Error("Entry with this note already exists")
        }
        
        currentEntries.add(entry)
        return saveVaultEntries(currentEntries, serverUrl)
    }
    
    /**
     * Updates an existing entry in the vault.
     */
    suspend fun updateEntry(oldEntry: VaultEntry, newEntry: VaultEntry, serverUrl: String): ApiResult<Unit> {
        if (!VaultEntry.validate(newEntry)) {
            return ApiResult.Error("Invalid entry data")
        }
        
        val currentEntries = when (val result = getVaultEntries(serverUrl)) {
            is ApiResult.Success -> result.data.toMutableList()
            is ApiResult.Error -> return ApiResult.Error(result.message, result.code)
            else -> return ApiResult.Error("Failed to get current entries")
        }
        
        val index = currentEntries.indexOfFirst { it.note.equals(oldEntry.note, ignoreCase = true) }
        if (index == -1) {
            return ApiResult.Error("Entry not found")
        }
        
        // Check for duplicate notes if note changed
        if (!oldEntry.note.equals(newEntry.note, ignoreCase = true)) {
            if (currentEntries.any { it.note.equals(newEntry.note, ignoreCase = true) }) {
                return ApiResult.Error("Entry with this note already exists")
            }
        }
        
        currentEntries[index] = newEntry.withUpdatedTimestamp()
        return saveVaultEntries(currentEntries, serverUrl)
    }
    
    /**
     * Deletes an entry from the vault.
     */
    suspend fun deleteEntry(entry: VaultEntry, serverUrl: String): ApiResult<Unit> {
        val currentEntries = when (val result = getVaultEntries(serverUrl)) {
            is ApiResult.Success -> result.data.toMutableList()
            is ApiResult.Error -> return ApiResult.Error(result.message, result.code)
            else -> return ApiResult.Error("Failed to get current entries")
        }
        
        val removed = currentEntries.removeIf { it.note.equals(entry.note, ignoreCase = true) }
        if (!removed) {
            return ApiResult.Error("Entry not found")
        }
        
        return saveVaultEntries(currentEntries, serverUrl)
    }
    
    /**
     * Deletes the entire vault.
     */
    suspend fun deleteVault(serverUrl: String): ApiResult<Unit> = withContext(Dispatchers.IO) {
        val restored = sessionManager.restoreManagers(serverUrl)
            ?: return@withContext ApiResult.Error("No valid session")
        
        val username = sessionManager.getCurrentUsername(serverUrl)
            ?: return@withContext ApiResult.Error("No current user")
        
        try {
            val apiClient = ApiClient(serverUrl, restored.signingManager)
            
            when (val result = apiClient.deleteVault(username)) {
                is ApiResult.Success -> {
                    // Clear cache and session
                    clearCache()
                    sessionManager.clearSession(serverUrl)
                    ApiResult.Success(Unit)
                }
                is ApiResult.Error -> ApiResult.Error(result.message, result.code)
                else -> ApiResult.Error("Unexpected error")
            }
        } catch (e: Exception) {
            ApiResult.Error("Failed to delete vault: ${e.message}")
        }
    }
    
    /**
     * Logs out the current user.
     */
    fun logout(serverUrl: String) {
        clearCache()
        sessionManager.clearSession(serverUrl)
    }
    
    /**
     * Clears the in-memory cache.
     */
    fun clearCache() {
        cachedEntries = null
        cacheTimestamp = 0
    }
    
    /**
     * Checks if the in-memory cache is still valid.
     */
    private fun isCacheValid(): Boolean {
        return cachedEntries != null && 
               (System.currentTimeMillis() - cacheTimestamp) < cacheTimeout
    }
    
    /**
     * Validates username format.
     */
    private fun isValidUsername(username: String): Boolean {
        return username.isNotBlank() &&
               username.length <= VaultEntry.MAX_USERNAME_LENGTH
    }
    
    /**
     * Validates vault constraints.
     */
    private fun validateVault(entries: List<VaultEntry>): Boolean {
        if (entries.size > VaultEntry.MAX_VAULT_ENTRIES) {
            return false
        }
        
        // Check vault size
        val vaultJson = gson.toJson(entries)
        val vaultSizeKB = vaultJson.toByteArray().size / 1024
        if (vaultSizeKB > VaultEntry.MAX_VAULT_SIZE_KB) {
            return false
        }
        
        // Validate each entry
        return entries.all { VaultEntry.validate(it) }
    }
}