package ch.upass.ui.vault

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ch.upass.crypto.CryptoManager
import ch.upass.models.ApiResult
import ch.upass.models.VaultEntry
import ch.upass.repository.VaultRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for vault management screen.
 */
class VaultViewModel(
    private val vaultRepository: VaultRepository,
    private val cryptoManager: CryptoManager
) : ViewModel() {
    
    private val _vaultEntries = MutableLiveData<List<VaultEntry>>()
    val vaultEntries: LiveData<List<VaultEntry>> = _vaultEntries
    
    private val _filteredEntries = MutableLiveData<List<VaultEntry>>()
    val filteredEntries: LiveData<List<VaultEntry>> = _filteredEntries
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _errorMessage = MutableLiveData<String?>()
    val errorMessage: LiveData<String?> = _errorMessage
    
    private val _successMessage = MutableLiveData<String?>()
    val successMessage: LiveData<String?> = _successMessage
    
    private var currentServerUrl: String = ""
    private var searchQuery: String = ""
    
    /**
     * Initializes the vault with server URL.
     */
    fun initialize(serverUrl: String) {
        currentServerUrl = serverUrl
        loadVaultEntries()
    }
    
    /**
     * Loads vault entries from repository.
     */
    fun loadVaultEntries(forceRefresh: Boolean = false) {
        if (currentServerUrl.isEmpty()) return
        
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.getVaultEntries(currentServerUrl, forceRefresh)) {
                is ApiResult.Success -> {
                    _vaultEntries.value = result.data
                    applySearchFilter()
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Failed to load vault entries"
                }
            }
            _isLoading.value = false
        }
    }
    
    /**
     * Adds a new entry to the vault.
     */
    fun addEntry(entry: VaultEntry) {
        if (currentServerUrl.isEmpty()) return
        
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.addEntry(entry, currentServerUrl)) {
                is ApiResult.Success -> {
                    _successMessage.value = "Entry added successfully"
                    loadVaultEntries(forceRefresh = true)
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Failed to add entry"
                }
            }
            _isLoading.value = false
        }
    }
    
    /**
     * Updates an existing entry in the vault.
     */
    fun updateEntry(oldEntry: VaultEntry, newEntry: VaultEntry) {
        if (currentServerUrl.isEmpty()) return
        
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.updateEntry(oldEntry, newEntry, currentServerUrl)) {
                is ApiResult.Success -> {
                    _successMessage.value = "Entry updated successfully"
                    loadVaultEntries(forceRefresh = true)
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Failed to update entry"
                }
            }
            _isLoading.value = false
        }
    }
    
    /**
     * Deletes an entry from the vault.
     */
    fun deleteEntry(entry: VaultEntry) {
        if (currentServerUrl.isEmpty()) return
        
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.deleteEntry(entry, currentServerUrl)) {
                is ApiResult.Success -> {
                    _successMessage.value = "Entry deleted successfully"
                    loadVaultEntries(forceRefresh = true)
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Failed to delete entry"
                }
            }
            _isLoading.value = false
        }
    }
    
    /**
     * Searches entries by note and username.
     */
    fun searchEntries(query: String) {
        searchQuery = query
        applySearchFilter()
    }
    
    /**
     * Applies search filter to vault entries.
     */
    private fun applySearchFilter() {
        val entries = _vaultEntries.value ?: emptyList()
        val filtered = if (searchQuery.isBlank()) {
            entries
        } else {
            entries.filter { entry ->
                entry.note.contains(searchQuery, ignoreCase = true) ||
                entry.username.contains(searchQuery, ignoreCase = true)
            }
        }
        _filteredEntries.value = filtered.sortedBy { it.note.lowercase() }
    }
    
    /**
     * Generates a secure password.
     */
    fun generatePassword(length: Int = 16, includeSpecialChars: Boolean = true): String {
        return cryptoManager.generatePassword(length, includeSpecialChars)
    }
    
    /**
     * Validates entry data.
     */
    fun validateEntry(entry: VaultEntry): ValidationResult {
        return when {
            entry.username.isBlank() -> ValidationResult.Error("Username cannot be empty")
            entry.username.length > VaultEntry.MAX_USERNAME_LENGTH -> {
                ValidationResult.Error("Username must be ${VaultEntry.MAX_USERNAME_LENGTH} characters or less")
            }
            entry.password.isBlank() -> ValidationResult.Error("Password cannot be empty")
            entry.password.length > VaultEntry.MAX_PASSWORD_LENGTH -> {
                ValidationResult.Error("Password must be ${VaultEntry.MAX_PASSWORD_LENGTH} characters or less")
            }
            entry.note.isBlank() -> ValidationResult.Error("Note cannot be empty")
            else -> {
                // Check for duplicate notes
                val existingEntries = _vaultEntries.value ?: emptyList()
                if (existingEntries.any { it.note.equals(entry.note, ignoreCase = true) }) {
                    ValidationResult.Error("Entry with this note already exists")
                } else {
                    ValidationResult.Success
                }
            }
        }
    }
    
    /**
     * Checks if vault is approaching limits.
     */
    fun getVaultStats(): VaultStats {
        val entries = _vaultEntries.value ?: emptyList()
        val entryCount = entries.size
        val entryPercentage = (entryCount.toFloat() / VaultEntry.MAX_VAULT_ENTRIES * 100).toInt()
        
        return VaultStats(
            entryCount = entryCount,
            maxEntries = VaultEntry.MAX_VAULT_ENTRIES,
            entryPercentage = entryPercentage,
            isNearLimit = entryPercentage > 80
        )
    }
    
    /**
     * Deletes the entire vault.
     */
    fun deleteVault() {
        if (currentServerUrl.isEmpty()) return
        
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.deleteVault(currentServerUrl)) {
                is ApiResult.Success -> {
                    _successMessage.value = "Vault deleted successfully"
                    _vaultEntries.value = emptyList()
                    _filteredEntries.value = emptyList()
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Failed to delete vault"
                }
            }
            _isLoading.value = false
        }
    }
    
    /**
     * Logs out the current user.
     */
    fun logout() {
        if (currentServerUrl.isNotEmpty()) {
            vaultRepository.logout(currentServerUrl)
            _vaultEntries.value = emptyList()
            _filteredEntries.value = emptyList()
        }
    }
    
    /**
     * Clears error message.
     */
    fun clearError() {
        _errorMessage.value = null
    }
    
    /**
     * Clears success message.
     */
    fun clearSuccess() {
        _successMessage.value = null
    }
}

/**
 * Result of entry validation.
 */
sealed class ValidationResult {
    object Success : ValidationResult()
    data class Error(val message: String) : ValidationResult()
}

/**
 * Statistics about vault usage.
 */
data class VaultStats(
    val entryCount: Int,
    val maxEntries: Int,
    val entryPercentage: Int,
    val isNearLimit: Boolean
)