package ch.upass.ui.vault

import android.app.Dialog
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.DialogFragment
import ch.upass.crypto.CryptoManager
import ch.upass.databinding.DialogAddEditEntryBinding
import ch.upass.models.VaultEntry
import com.google.android.material.dialog.MaterialAlertDialogBuilder

/**
 * Dialog for adding or editing vault entries.
 */
class AddEditEntryDialog : DialogFragment() {
    
    private var _binding: DialogAddEditEntryBinding? = null
    private val binding get() = _binding!!
    
    private var existingEntry: VaultEntry? = null
    private var onSaveClickListener: ((VaultEntry) -> Unit)? = null
    private val cryptoManager = CryptoManager()
    
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
        
        if (!validateInput(note, username, password)) {
            return
        }
        
        val entry = VaultEntry(
            username = username,
            password = password,
            note = note
        )
        
        onSaveClickListener?.invoke(entry)
        dismiss()
    }
    
    private fun validateInput(note: String, username: String, password: String): Boolean {
        return when {
            note.isBlank() -> {
                binding.etNote.error = "Note cannot be empty"
                false
            }
            username.isBlank() -> {
                binding.etUsername.error = "Username cannot be empty"
                false
            }
            username.length > 32 -> {
                binding.etUsername.error = "Username must be 32 characters or less"
                false
            }
            password.isBlank() -> {
                binding.etPassword.error = "Password cannot be empty"
                false
            }
            password.length > 128 -> {
                binding.etPassword.error = "Password must be 128 characters or less"
                false
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