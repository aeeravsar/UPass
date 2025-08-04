package ch.upass.ui.login

import android.content.Intent
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import android.view.WindowInsetsController
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import ch.upass.R
import ch.upass.crypto.CryptoManager
import ch.upass.databinding.ActivityLoginBinding
import ch.upass.repository.VaultRepository
import ch.upass.session.SessionManager
import ch.upass.ui.vault.VaultActivity
import ch.upass.ui.register.RegisterActivity

/**
 * Login activity.
 */
class LoginActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityLoginBinding
    private lateinit var viewModel: LoginViewModel
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupSystemUI()
        initializeViewModel()
        setupUI()
        observeViewModel()
        checkExistingSession()
    }
    
    private fun setupSystemUI() {
        // Enable edge-to-edge display
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        // Set status bar color and appearance
        window.statusBarColor = ContextCompat.getColor(this, R.color.md_theme_light_primary)
        
        // Ensure status bar icons are visible
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
            window.insetsController?.setSystemBarsAppearance(
                0, // Clear light status bar flag (use dark icons on light background)
                WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
            )
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = window.decorView.systemUiVisibility and 
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR.inv()
        }
    }
    
    private fun initializeViewModel() {
        val sessionManager = SessionManager(this)
        val cryptoManager = CryptoManager()
        val vaultRepository = VaultRepository(sessionManager, cryptoManager)
        
        viewModel = LoginViewModel(vaultRepository, sessionManager)
    }
    
    private fun setupUI() {
        binding.btnLogin.setOnClickListener {
            performLogin()
        }
        
        binding.btnCreateVault.setOnClickListener {
            navigateToRegister()
        }
        
        
        // Clear error when user starts typing
        val clearErrorWatcher = object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                viewModel.clearError()
            }
        }
        
        binding.etUsername.addTextChangedListener(clearErrorWatcher)
        binding.etMasterPassword.addTextChangedListener(clearErrorWatcher)
        binding.etServerUrl.addTextChangedListener(clearErrorWatcher)
    }
    
    private fun observeViewModel() {
        viewModel.loginState.observe(this) { state ->
            when (state) {
                is LoginState.Success -> {
                    navigateToVault(state.username, state.serverUrl)
                }
                else -> {
                    // Handle other states if needed
                }
            }
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
            binding.btnLogin.isEnabled = !isLoading
            binding.btnCreateVault.isEnabled = !isLoading
        }
        
        viewModel.errorMessage.observe(this) { errorMessage ->
            if (errorMessage != null) {
                binding.tvError.text = errorMessage
                binding.tvError.visibility = View.VISIBLE
            } else {
                binding.tvError.visibility = View.GONE
            }
        }
    }
    
    private fun checkExistingSession() {
        viewModel.checkAndValidateExistingSession()
    }
    
    private fun performLogin() {
        val username = binding.etUsername.text.toString().trim()
        val masterPassword = binding.etMasterPassword.text.toString()
        val serverUrl = viewModel.normalizeServerUrl(binding.etServerUrl.text.toString())
        
        viewModel.login(username, masterPassword, serverUrl)
    }
    
    private fun navigateToRegister() {
        val intent = Intent(this, RegisterActivity::class.java)
        startActivity(intent)
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