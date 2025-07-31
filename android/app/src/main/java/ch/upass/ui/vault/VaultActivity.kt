package ch.upass.ui.vault

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.Menu
import android.view.MenuItem
import android.view.View
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import ch.upass.R
import ch.upass.crypto.CryptoManager
import ch.upass.databinding.ActivityVaultBinding
import ch.upass.models.VaultEntry
import ch.upass.repository.VaultRepository
import ch.upass.session.SessionManager
import ch.upass.ui.login.LoginActivity
import com.google.android.material.snackbar.Snackbar

/**
 * Main vault activity displaying password entries.
 */
class VaultActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityVaultBinding
    private lateinit var viewModel: VaultViewModel
    private lateinit var vaultAdapter: VaultAdapter
    
    private var username: String = ""
    private var serverUrl: String = ""
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityVaultBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        extractIntentData()
        initializeViewModel()
        setupUI()
        observeViewModel()
        
        viewModel.initialize(serverUrl)
    }
    
    private fun extractIntentData() {
        username = intent.getStringExtra("username") ?: ""
        serverUrl = intent.getStringExtra("serverUrl") ?: ""
        
        if (username.isEmpty() || serverUrl.isEmpty()) {
            navigateToLogin()
            return
        }
    }
    
    private fun initializeViewModel() {
        val sessionManager = SessionManager(this)
        val cryptoManager = CryptoManager()
        val vaultRepository = VaultRepository(sessionManager, cryptoManager)
        
        viewModel = VaultViewModel(vaultRepository, cryptoManager)
    }
    
    private fun setupUI() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.title = "Vault - $username"
        
        // Setup RecyclerView
        vaultAdapter = VaultAdapter(
            onItemClick = { entry -> showEntryDetails(entry) },
            onItemLongClick = { entry -> showEntryOptions(entry) },
            onCopyPassword = { password -> copyToClipboard(password) }
        )
        
        binding.rvVaultEntries.apply {
            layoutManager = LinearLayoutManager(this@VaultActivity)
            adapter = vaultAdapter
        }
        
        // Setup search
        binding.etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                viewModel.searchEntries(s?.toString() ?: "")
            }
        })
        
        // Setup FAB
        binding.fabAddEntry.setOnClickListener {
            showAddEntryDialog()
        }
    }
    
    private fun observeViewModel() {
        viewModel.filteredEntries.observe(this) { entries ->
            vaultAdapter.submitList(entries)
            updateEmptyState(entries.isEmpty())
            updateVaultStats()
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            binding.llLoadingState.visibility = if (isLoading) View.VISIBLE else View.GONE
        }
        
        viewModel.errorMessage.observe(this) { errorMessage ->
            errorMessage?.let {
                showSnackbar(it, isError = true)
                viewModel.clearError()
            }
        }
        
        viewModel.successMessage.observe(this) { successMessage ->
            successMessage?.let {
                showSnackbar(it, isError = false)
                viewModel.clearSuccess()
            }
        }
    }
    
    private fun updateEmptyState(isEmpty: Boolean) {
        binding.llEmptyState.visibility = if (isEmpty) View.VISIBLE else View.GONE
        binding.rvVaultEntries.visibility = if (isEmpty) View.GONE else View.VISIBLE
    }
    
    private fun updateVaultStats() {
        val stats = viewModel.getVaultStats()
        binding.llVaultStats.visibility = View.VISIBLE
        binding.tvVaultStats.text = "Entries: ${stats.entryCount}/${stats.maxEntries}"
        binding.tvWarning.visibility = if (stats.isNearLimit) View.VISIBLE else View.GONE
    }
    
    private fun showEntryDetails(entry: VaultEntry) {
        val dialog = EntryDetailsDialog.newInstance(entry)
        dialog.setOnEditClickListener { showEditEntryDialog(entry) }
        dialog.setOnDeleteClickListener { confirmDeleteEntry(entry) }
        dialog.show(supportFragmentManager, "EntryDetailsDialog")
    }
    
    private fun showEntryOptions(entry: VaultEntry) {
        val options = arrayOf("View Details", "Edit", "Copy Password", "Delete")
        
        AlertDialog.Builder(this)
            .setTitle(entry.note)
            .setItems(options) { _, which ->
                when (which) {
                    0 -> showEntryDetails(entry)
                    1 -> showEditEntryDialog(entry)
                    2 -> copyToClipboard(entry.password)
                    3 -> confirmDeleteEntry(entry)
                }
            }
            .show()
    }
    
    private fun showAddEntryDialog() {
        val dialog = AddEditEntryDialog.newInstance()
        dialog.setOnSaveClickListener { entry ->
            viewModel.addEntry(entry)
        }
        dialog.show(supportFragmentManager, "AddEntryDialog")
    }
    
    private fun showEditEntryDialog(entry: VaultEntry) {
        val dialog = AddEditEntryDialog.newInstance(entry)
        dialog.setOnSaveClickListener { newEntry ->
            viewModel.updateEntry(entry, newEntry)
        }
        dialog.show(supportFragmentManager, "EditEntryDialog")
    }
    
    private fun confirmDeleteEntry(entry: VaultEntry) {
        AlertDialog.Builder(this)
            .setTitle("Delete Entry")
            .setMessage("Are you sure you want to delete '${entry.note}'?")
            .setPositiveButton("Delete") { _, _ ->
                viewModel.deleteEntry(entry)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun copyToClipboard(text: String) {
        val clipboard = getSystemService(CLIPBOARD_SERVICE) as android.content.ClipboardManager
        val clip = android.content.ClipData.newPlainText("UPass", text)
        clipboard.setPrimaryClip(clip)
        showSnackbar("Copied to clipboard", isError = false)
    }
    
    private fun showSnackbar(message: String, isError: Boolean) {
        val snackbar = Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG)
        if (isError) {
            snackbar.setBackgroundTint(getColor(R.color.error))
        }
        snackbar.show()
    }
    
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.vault_menu, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_refresh -> {
                viewModel.loadVaultEntries(forceRefresh = true)
                true
            }
            R.id.action_website -> {
                openWebsite()
                true
            }
            R.id.action_logout -> {
                confirmLogout()
                true
            }
            R.id.action_delete_vault -> {
                confirmDeleteVault()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    private fun openWebsite() {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://upass.ch"))
            startActivity(intent)
        } catch (e: Exception) {
            showSnackbar("Unable to open website", isError = true)
        }
    }
    
    private fun confirmLogout() {
        AlertDialog.Builder(this)
            .setTitle("Logout")
            .setMessage("Are you sure you want to logout?")
            .setPositiveButton("Logout") { _, _ ->
                viewModel.logout()
                navigateToLogin()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun confirmDeleteVault() {
        AlertDialog.Builder(this)
            .setTitle("Delete Vault")
            .setMessage("Are you sure you want to permanently delete your entire vault? This action cannot be undone.")
            .setPositiveButton("Delete") { _, _ ->
                viewModel.deleteVault()
                navigateToLogin()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        startActivity(intent)
        finish()
    }
}