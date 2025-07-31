package ch.upass.ui.login

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ch.upass.models.ApiResult
import ch.upass.repository.VaultRepository
import ch.upass.session.SessionManager
import kotlinx.coroutines.launch

/**
 * ViewModel for login screen.
 */
class LoginViewModel(
    private val vaultRepository: VaultRepository,
    private val sessionManager: SessionManager
) : ViewModel() {
    
    private val _loginState = MutableLiveData<LoginState>()
    val loginState: LiveData<LoginState> = _loginState
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _errorMessage = MutableLiveData<String?>()
    val errorMessage: LiveData<String?> = _errorMessage
    
    /**
     * Attempts to login existing user.
     */
    fun login(username: String, masterPassword: String, serverUrl: String) {
        if (!validateInput(username, masterPassword, serverUrl)) {
            return
        }
        
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.loginUser(username, masterPassword, serverUrl)) {
                is ApiResult.Success -> {
                    _loginState.value = LoginState.Success(username, serverUrl)
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Login failed"
                }
            }
            _isLoading.value = false
        }
    }
    
    
    /**
     * Checks and validates existing session, navigates if valid.
     */
    fun checkAndValidateExistingSession() {
        _isLoading.value = true
        
        viewModelScope.launch {
            val sessions = sessionManager.getAllSessions()
            
            // Try the most recent session first
            for ((serverUrl, username) in sessions) {
                if (sessionManager.hasValidSession(serverUrl)) {
                    // Validate session by trying to get vault
                    val restored = sessionManager.restoreManagers(serverUrl)
                    if (restored != null) {
                        when (val result = vaultRepository.getVaultEntries(serverUrl, forceRefresh = true)) {
                            is ApiResult.Success -> {
                                // Session is valid, navigate to vault
                                _loginState.value = LoginState.Success(username, serverUrl)
                                _isLoading.value = false
                                return@launch
                            }
                            is ApiResult.Error -> {
                                // Session invalid, clear it
                                sessionManager.clearSession(serverUrl)
                            }
                            is ApiResult.Loading -> {
                                // Should not happen with our implementation, but handle it
                                sessionManager.clearSession(serverUrl)
                            }
                        }
                    }
                }
            }
            
            // No valid session found
            _isLoading.value = false
        }
    }
    
    /**
     * Validates input fields.
     */
    private fun validateInput(username: String, masterPassword: String, serverUrl: String): Boolean {
        when {
            username.isBlank() -> {
                _errorMessage.value = "Username cannot be empty"
                return false
            }
            username.length > 32 -> {
                _errorMessage.value = "Username must be 32 characters or less"
                return false
            }
            !username.matches(Regex("^[a-zA-Z0-9]+$")) -> {
                _errorMessage.value = "Username can only contain letters and numbers"
                return false
            }
            masterPassword.isBlank() -> {
                _errorMessage.value = "Master password cannot be empty"
                return false
            }
            serverUrl.isBlank() -> {
                _errorMessage.value = "Server URL cannot be empty"
                return false
            }
            !isValidUrl(serverUrl) -> {
                _errorMessage.value = "Invalid server URL format"
                return false
            }
        }
        return true
    }
    
    /**
     * Validates URL format.
     */
    private fun isValidUrl(url: String): Boolean {
        return try {
            val normalizedUrl = if (!url.startsWith("http://") && !url.startsWith("https://")) {
                "https://$url"
            } else {
                url
            }
            java.net.URL(normalizedUrl)
            true
        } catch (e: Exception) {
            false
        }
    }
    
    /**
     * Clears error message.
     */
    fun clearError() {
        _errorMessage.value = null
    }
    
    
    /**
     * Normalizes server URL.
     */
    fun normalizeServerUrl(url: String): String {
        var normalized = url.trim()
        if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
            normalized = "https://$normalized"
        }
        if (normalized.endsWith("/")) {
            normalized = normalized.dropLast(1)
        }
        return normalized
    }
}

/**
 * Represents the state of login operation.
 */
sealed class LoginState {
    object Idle : LoginState()
    data class Success(val username: String, val serverUrl: String) : LoginState()
}

/**
 * Password strength levels.
 */
enum class PasswordStrength {
    WEAK, MEDIUM, STRONG
}