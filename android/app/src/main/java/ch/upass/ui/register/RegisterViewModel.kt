package ch.upass.ui.register

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ch.upass.models.ApiResult
import ch.upass.repository.VaultRepository
import ch.upass.session.SessionManager
import kotlinx.coroutines.launch

/**
 * ViewModel for registration screen.
 */
class RegisterViewModel(
    private val vaultRepository: VaultRepository,
    private val sessionManager: SessionManager
) : ViewModel() {
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    private val _errorMessage = MutableLiveData<String?>()
    val errorMessage: LiveData<String?> = _errorMessage
    
    private val _registrationSuccess = MutableLiveData<Boolean>()
    val registrationSuccess: LiveData<Boolean> = _registrationSuccess
    
    /**
     * Registers a new user with the provided credentials.
     */
    fun register(username: String, masterPassword: String, serverUrl: String) {
        _isLoading.value = true
        _errorMessage.value = null
        
        viewModelScope.launch {
            when (val result = vaultRepository.registerUser(username, masterPassword, serverUrl)) {
                is ApiResult.Success -> {
                    _registrationSuccess.value = true
                }
                is ApiResult.Error -> {
                    _errorMessage.value = result.message
                }
                else -> {
                    _errorMessage.value = "Registration failed. Please try again."
                }
            }
            _isLoading.value = false
        }
    }
    
    /**
     * Clears error message.
     */
    fun clearError() {
        _errorMessage.value = null
    }
}