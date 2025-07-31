package ch.upass.ui.register

import android.content.Intent
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import ch.upass.R
import ch.upass.crypto.CryptoManager
import ch.upass.databinding.ActivityRegisterBinding
import ch.upass.repository.VaultRepository
import ch.upass.session.SessionManager
import ch.upass.ui.login.LoginActivity
import ch.upass.ui.vault.VaultActivity

/**
 * Registration activity for creating new vaults.
 */
class RegisterActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityRegisterBinding
    private lateinit var viewModel: RegisterViewModel
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegisterBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        initializeViewModel()
        setupUI()
        observeViewModel()
    }
    
    private fun initializeViewModel() {
        val sessionManager = SessionManager(this)
        val cryptoManager = CryptoManager()
        val vaultRepository = VaultRepository(sessionManager, cryptoManager)
        
        viewModel = RegisterViewModel(vaultRepository, sessionManager)
    }
    
    private fun setupUI() {
        binding.btnCreateVault.setOnClickListener {
            performRegistration()
        }
        
        binding.btnBackToLogin.setOnClickListener {
            navigateToLogin()
        }
        
        // Setup password strength monitoring
        binding.etMasterPassword.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                updatePasswordStrength(s?.toString() ?: "")
                validatePasswordMatch()
            }
        })
        
        // Setup password confirmation monitoring
        binding.etConfirmPassword.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                validatePasswordMatch()
            }
        })
    }
    
    private fun observeViewModel() {
        viewModel.isLoading.observe(this) { isLoading ->
            binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
            binding.btnCreateVault.isEnabled = !isLoading
        }
        
        viewModel.errorMessage.observe(this) { errorMessage ->
            if (errorMessage != null) {
                showError(errorMessage)
                viewModel.clearError()
            }
        }
        
        viewModel.registrationSuccess.observe(this) { success ->
            if (success) {
                val username = binding.etUsername.text.toString()
                val serverUrl = getServerUrl()
                navigateToVault(username, serverUrl)
            }
        }
    }
    
    private fun performRegistration() {
        val username = binding.etUsername.text.toString().trim()
        val masterPassword = binding.etMasterPassword.text.toString()
        val confirmPassword = binding.etConfirmPassword.text.toString()
        val serverUrl = getServerUrl()
        
        // Validate inputs
        if (username.isEmpty()) {
            showError("Username cannot be empty")
            return
        }
        
        if (masterPassword.isEmpty()) {
            showError("Master password cannot be empty")
            return
        }
        
        if (masterPassword != confirmPassword) {
            showError("Passwords do not match")
            return
        }
        
        if (serverUrl.isEmpty()) {
            showError("Server URL cannot be empty")
            return
        }
        
        hideError()
        viewModel.register(username, masterPassword, serverUrl)
    }
    
    private fun updatePasswordStrength(password: String) {
        if (password.isEmpty()) {
            binding.llPasswordStrength.visibility = View.GONE
            return
        }
        
        val strength = calculatePasswordStrength(password)
        binding.llPasswordStrength.visibility = View.VISIBLE
        binding.tvPasswordStrength.text = strength.first
        binding.tvPasswordStrength.setTextColor(ContextCompat.getColor(this, strength.second))
    }
    
    private fun validatePasswordMatch() {
        val password = binding.etMasterPassword.text.toString()
        val confirmPassword = binding.etConfirmPassword.text.toString()
        
        if (confirmPassword.isNotEmpty() && password != confirmPassword) {
            binding.tilConfirmPassword.error = "Passwords do not match"
        } else {
            binding.tilConfirmPassword.error = null
        }
    }
    
    private fun calculatePasswordStrength(password: String): Pair<String, Int> {
        var score = 0
        
        // Length
        if (password.length >= 8) score++
        if (password.length >= 12) score++
        
        // Character types
        if (password.any { it.isLowerCase() }) score++
        if (password.any { it.isUpperCase() }) score++
        if (password.any { it.isDigit() }) score++
        if (password.any { !it.isLetterOrDigit() }) score++
        
        return when {
            score <= 2 -> Pair("Weak", R.color.error)
            score <= 4 -> Pair("Medium", R.color.warning)
            else -> Pair("Strong", R.color.success)
        }
    }
    
    private fun getServerUrl(): String {
        val url = binding.etServerUrl.text.toString().trim()
        return if (url.startsWith("http://") || url.startsWith("https://")) {
            url
        } else {
            "https://$url"
        }
    }
    
    private fun showError(message: String) {
        binding.tvError.text = message
        binding.tvError.visibility = View.VISIBLE
    }
    
    private fun hideError() {
        binding.tvError.visibility = View.GONE
    }
    
    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        startActivity(intent)
        finish()
    }
    
    private fun navigateToVault(username: String, serverUrl: String) {
        val intent = Intent(this, VaultActivity::class.java).apply {
            putExtra("username", username)
            putExtra("serverUrl", serverUrl)
        }
        startActivity(intent)
        finish()
    }
}