package ch.upass.ui.vault

import android.app.Dialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Build
import android.os.Bundle
import androidx.fragment.app.DialogFragment
import ch.upass.R
import ch.upass.databinding.DialogEntryDetailsBinding
import ch.upass.models.VaultEntry
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import java.text.SimpleDateFormat
import java.util.*

/**
 * Dialog for viewing entry details.
 */
class EntryDetailsDialog : DialogFragment() {
    
    private var _binding: DialogEntryDetailsBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var entry: VaultEntry
    private var onEditClickListener: (() -> Unit)? = null
    private var onDeleteClickListener: (() -> Unit)? = null
    private var isPasswordVisible = false
    
    companion object {
        private const val ARG_ENTRY = "entry"
        
        fun newInstance(entry: VaultEntry): EntryDetailsDialog {
            return EntryDetailsDialog().apply {
                arguments = Bundle().apply {
                    putSerializable(ARG_ENTRY, entry)
                }
            }
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        entry = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            arguments?.getSerializable(ARG_ENTRY, VaultEntry::class.java)!!
        } else {
            @Suppress("DEPRECATION")
            arguments?.getSerializable(ARG_ENTRY) as VaultEntry
        }
    }
    
    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        _binding = DialogEntryDetailsBinding.inflate(layoutInflater)
        
        setupUI()
        populateData()
        
        return MaterialAlertDialogBuilder(requireContext())
            .setView(binding.root)
            .create()
    }
    
    private fun setupUI() {
        binding.btnTogglePassword.setOnClickListener {
            togglePasswordVisibility()
        }
        
        binding.btnCopyUsername.setOnClickListener {
            copyToClipboard(entry.username, "Username copied")
        }
        
        binding.btnCopyPassword.setOnClickListener {
            copyToClipboard(entry.password, "Password copied")
        }
        
        binding.btnEdit.setOnClickListener {
            onEditClickListener?.invoke()
            dismiss()
        }
        
        binding.btnDelete.setOnClickListener {
            onDeleteClickListener?.invoke()
            dismiss()
        }
        
        binding.btnClose.setOnClickListener {
            dismiss()
        }
    }
    
    private fun populateData() {
        binding.tvTitle.text = entry.note
        binding.tvNote.text = entry.note
        binding.tvUsername.text = entry.username
        binding.tvCreated.text = formatTimestamp(entry.createdAt)
        binding.tvModified.text = formatTimestamp(entry.updatedAt)
        
        updatePasswordDisplay()
    }
    
    private fun togglePasswordVisibility() {
        isPasswordVisible = !isPasswordVisible
        updatePasswordDisplay()
    }
    
    private fun updatePasswordDisplay() {
        if (isPasswordVisible) {
            binding.tvPassword.text = entry.password
            binding.btnTogglePassword.setIconResource(R.drawable.ic_visibility_off)
        } else {
            binding.tvPassword.text = "••••••••"
            binding.btnTogglePassword.setIconResource(R.drawable.ic_visibility)
        }
    }
    
    private fun copyToClipboard(text: String, message: String) {
        val clipboard = requireContext().getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("UPass", text)
        clipboard.setPrimaryClip(clip)
        
        view?.let { view ->
            Snackbar.make(view, message, Snackbar.LENGTH_SHORT).show()
        }
    }
    
    private fun formatTimestamp(timestamp: String): String {
        return try {
            // Parse ISO timestamp (e.g., "2024-01-15T10:30:45.123Z")
            val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.getDefault())
            inputFormat.timeZone = TimeZone.getTimeZone("UTC")
            
            val outputFormat = SimpleDateFormat("MMM dd, yyyy 'at' HH:mm", Locale.getDefault())
            outputFormat.timeZone = TimeZone.getDefault()
            
            val date = inputFormat.parse(timestamp)
            date?.let { outputFormat.format(it) } ?: "Unknown"
        } catch (e: Exception) {
            // Try alternative format without milliseconds
            try {
                val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.getDefault())
                inputFormat.timeZone = TimeZone.getTimeZone("UTC")
                
                val outputFormat = SimpleDateFormat("MMM dd, yyyy 'at' HH:mm", Locale.getDefault())
                outputFormat.timeZone = TimeZone.getDefault()
                
                val date = inputFormat.parse(timestamp)
                date?.let { outputFormat.format(it) } ?: "Unknown - $timestamp"
            } catch (e2: Exception) {
                "Unknown - $timestamp"
            }
        }
    }
    
    fun setOnEditClickListener(listener: () -> Unit) {
        onEditClickListener = listener
    }
    
    fun setOnDeleteClickListener(listener: () -> Unit) {
        onDeleteClickListener = listener
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}