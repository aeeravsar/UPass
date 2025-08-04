package ch.upass.ui.vault

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import ch.upass.databinding.ItemVaultEntryBinding
import ch.upass.models.VaultEntry
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit

/**
 * RecyclerView adapter for vault entries.
 */
class VaultAdapter(
    private val onItemClick: (VaultEntry) -> Unit,
    private val onItemLongClick: (VaultEntry) -> Unit,
    private val onCopyPassword: (String) -> Unit
) : ListAdapter<VaultEntry, VaultAdapter.VaultEntryViewHolder>(VaultEntryDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VaultEntryViewHolder {
        val binding = ItemVaultEntryBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return VaultEntryViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: VaultEntryViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    inner class VaultEntryViewHolder(
        private val binding: ItemVaultEntryBinding
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(entry: VaultEntry) {
            binding.tvNote.text = entry.note
            binding.tvUsername.text = entry.username
            binding.tvLastModified.text = formatTimestamp(entry.updatedAt)
            
            // Show TOTP indicator if entry has TOTP
            if (!entry.totpSecret.isNullOrEmpty()) {
                binding.tvTotpIndicator.visibility = android.view.View.VISIBLE
            } else {
                binding.tvTotpIndicator.visibility = android.view.View.GONE
            }
            
            binding.root.setOnClickListener {
                onItemClick(entry)
            }
            
            binding.root.setOnLongClickListener {
                onItemLongClick(entry)
                true
            }
            
            binding.btnCopyPassword.setOnClickListener {
                onCopyPassword(entry.password)
            }
        }
        
        private fun formatTimestamp(timestamp: String): String {
            return try {
                val instant = Instant.parse(timestamp)
                val now = Instant.now()
                val duration = ChronoUnit.HOURS.between(instant, now)
                
                when {
                    duration < 1 -> "Just now"
                    duration < 24 -> "${duration}h ago"
                    duration < 24 * 7 -> "${duration / 24}d ago"
                    else -> DateTimeFormatter.ofPattern("MMM dd").format(instant)
                }
            } catch (e: Exception) {
                "Unknown"
            }
        }
    }
}

/**
 * DiffUtil callback for vault entries.
 */
class VaultEntryDiffCallback : DiffUtil.ItemCallback<VaultEntry>() {
    override fun areItemsTheSame(oldItem: VaultEntry, newItem: VaultEntry): Boolean {
        return oldItem.note == newItem.note
    }
    
    override fun areContentsTheSame(oldItem: VaultEntry, newItem: VaultEntry): Boolean {
        return oldItem == newItem
    }
}