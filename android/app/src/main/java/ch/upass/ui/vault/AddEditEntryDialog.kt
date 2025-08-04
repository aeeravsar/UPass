package ch.upass.ui.vault

import android.app.Dialog
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.DialogFragment
import ch.upass.crypto.CryptoManager
import ch.upass.crypto.TOTPManager
import ch.upass.databinding.DialogAddEditEntryBinding
import ch.upass.models.VaultEntry
import ch.upass.ui.qr.QRScannerActivity
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar

/**
 * Dialog for adding or editing vault entries.
 */
class AddEditEntryDialog : DialogFragment() {
    
    private var _binding: DialogAddEditEntryBinding? = null
    private val binding get() = _binding!!
    
    private var existingEntry: VaultEntry? = null
    private var onSaveClickListener: ((VaultEntry) -> Unit)? = null
    private val cryptoManager = CryptoManager()
    
    private val qrScannerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            val data = result.data
            val totpSecret = data?.getStringExtra(QRScannerActivity.EXTRA_TOTP_SECRET)
            val accountName = data?.getStringExtra(QRScannerActivity.EXTRA_ACCOUNT_NAME)
            
            if (!totpSecret.isNullOrEmpty()) {
                // Auto-fill the TOTP secret
                binding.cbAddTotp.isChecked = true
                binding.llTotpSection.visibility = View.VISIBLE
                binding.etTotpSecret.setText(totpSecret)
                
                // Optionally set the account name if the entry is new and fields are empty
                if (existingEntry == null && binding.etNote.text.isNullOrEmpty() && !accountName.isNullOrEmpty()) {
                    binding.etNote.setText(accountName)
                }
                
                Snackbar.make(binding.root, "2FA secret scanned successfully!", Snackbar.LENGTH_SHORT).show()
            }
        }
    }
    
    companion object {
        private const val ARG_ENTRY = "entry"
        
        fun newInstance(entry: VaultEntry? = null): AddEditEntryDialog {
            return AddEditEntryDialog().apply {
                arguments = Bundle().apply {
                    entry?.let { putSerializable(ARG_ENTRY, it) }
                }
            }
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        existingEntry = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            arguments?.getSerializable(ARG_ENTRY, VaultEntry::class.java)
        } else {
            @Suppress("DEPRECATION")
            arguments?.getSerializable(ARG_ENTRY) as? VaultEntry
        }
    }
    
    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        _binding = DialogAddEditEntryBinding.inflate(layoutInflater)
        
        setupUI()
        setupExistingEntry()
        
        return MaterialAlertDialogBuilder(requireContext())
            .setView(binding.root)
            .create()
    }
    
    private fun setupUI() {
        // Set title
        binding.tvTitle.text = if (existingEntry == null) "Add Entry" else "Edit Entry"
        
        // Setup password generation
        binding.btnGeneratePassword.setOnClickListener {
            togglePasswordOptions()
        }
        
        // Setup TOTP
        binding.cbAddTotp.setOnCheckedChangeListener { _, isChecked ->
            binding.llTotpSection.visibility = if (isChecked) View.VISIBLE else View.GONE
            if (!isChecked) {
                // Clear TOTP fields when unchecked
                binding.etTotpSecret.setText("")
            }
        }
        
        binding.btnScanQR.setOnClickListener {
            val intent = Intent(requireContext(), QRScannerActivity::class.java)
            qrScannerLauncher.launch(intent)
        }
        
        binding.sliderLength.addOnChangeListener { _, value, _ ->
            binding.tvLength.text = value.toInt().toString()
        }
        
        binding.sliderLength.addOnSliderTouchListener(object : com.google.android.material.slider.Slider.OnSliderTouchListener {
            override fun onStartTrackingTouch(slider: com.google.android.material.slider.Slider) {}
            override fun onStopTrackingTouch(slider: com.google.android.material.slider.Slider) {
                generatePassword()
            }
        })
        
        binding.cbSpecialChars.setOnCheckedChangeListener { _, _ ->
            if (binding.llPasswordOptions.visibility == View.VISIBLE) {
                generatePassword()
            }
        }
        
        // Setup buttons
        binding.btnCancel.setOnClickListener {
            dismiss()
        }
        
        binding.btnSave.setOnClickListener {
            saveEntry()
        }
    }
    
    private fun setupExistingEntry() {
        existingEntry?.let { entry ->
            binding.etNote.setText(entry.note)
            binding.etUsername.setText(entry.username)
            binding.etPassword.setText(entry.password)
            
            // Setup TOTP if exists
            if (!entry.totpSecret.isNullOrEmpty()) {
                binding.cbAddTotp.isChecked = true
                binding.llTotpSection.visibility = View.VISIBLE
                binding.etTotpSecret.setText(entry.totpSecret)
            }
        }
    }
    
    private fun togglePasswordOptions() {
        val isVisible = binding.llPasswordOptions.visibility == View.VISIBLE
        binding.llPasswordOptions.visibility = if (isVisible) View.GONE else View.VISIBLE
        
        if (!isVisible) {
            generatePassword()
        }
    }
    
    private fun generatePassword() {
        val length = binding.sliderLength.value.toInt()
        val includeSpecialChars = binding.cbSpecialChars.isChecked
        
        val password = cryptoManager.generatePassword(length, includeSpecialChars)
        binding.etPassword.setText(password)
    }
    
    private fun saveEntry() {
        val note = binding.etNote.text.toString().trim()
        val username = binding.etUsername.text.toString().trim()
        val password = binding.etPassword.text.toString()
        
        // Get TOTP fields if enabled
        val totpSecret = if (binding.cbAddTotp.isChecked) {
            binding.etTotpSecret.text.toString().trim().uppercase().replace(" ", "")
        } else null
        
        if (!validateInput(note, username, password, totpSecret)) {
            return
        }
        
        val entry = if (existingEntry != null) {
            VaultEntry(
                username = username,
                password = password,
                note = note,
                createdAt = existingEntry!!.createdAt,
                updatedAt = java.time.Instant.now().toString(),
                totpSecret = totpSecret
            )
        } else {
            VaultEntry(
                username = username,
                password = password,
                note = note,
                totpSecret = totpSecret
            )
        }
        
        onSaveClickListener?.invoke(entry)
        dismiss()
    }
    
    private fun validateInput(note: String, username: String, password: String, totpSecret: String?): Boolean {
        return when {
            note.isBlank() -> {
                binding.etNote.error = "Note cannot be empty"
                false
            }
            note.length > VaultEntry.MAX_NOTE_LENGTH -> {
                binding.etNote.error = "Note must be ${VaultEntry.MAX_NOTE_LENGTH} characters or less"
                false
            }
            username.length > VaultEntry.MAX_USERNAME_LENGTH -> {
                binding.etUsername.error = "Username must be ${VaultEntry.MAX_USERNAME_LENGTH} characters or less"
                false
            }
            password.isBlank() -> {
                binding.etPassword.error = "Password cannot be empty"
                false
            }
            password.length > VaultEntry.MAX_PASSWORD_LENGTH -> {
                binding.etPassword.error = "Password must be ${VaultEntry.MAX_PASSWORD_LENGTH} characters or less"
                false
            }
            totpSecret != null && totpSecret.isNotEmpty() -> {
                when {
                    !TOTPManager.isValidSecret(totpSecret) -> {
                        binding.etTotpSecret.error = "Invalid 2FA secret. Must be a valid Base32 string."
                        false
                    }
                    totpSecret.length > VaultEntry.MAX_TOTP_SECRET_LENGTH -> {
                        binding.etTotpSecret.error = "2FA secret must be ${VaultEntry.MAX_TOTP_SECRET_LENGTH} characters or less"
                        false
                    }
                    else -> true
                }
            }
            else -> true
        }
    }
    
    fun setOnSaveClickListener(listener: (VaultEntry) -> Unit) {
        onSaveClickListener = listener
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}