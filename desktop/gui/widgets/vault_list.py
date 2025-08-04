import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib
from datetime import datetime


class VaultListWidget(Gtk.TreeView):
    """Widget for displaying vault entries"""
    
    __gsignals__ = {
        'entry-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'entry-copied': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }
    
    def __init__(self, session, vault_commands):
        super().__init__()
        self.session = session
        self.vault_commands = vault_commands
        self.filter_text = ""
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup tree view"""
        # Create list store: note, username, 2FA, created, updated, entry_object
        self.store = Gtk.ListStore(str, str, str, str, str, object)
        self.filtered_store = self.store.filter_new()
        self.filtered_store.set_visible_func(self._filter_func)
        
        # Create sorted model
        self.sorted_store = Gtk.TreeModelSort(self.filtered_store)
        self.set_model(self.sorted_store)
        
        # Title column
        note_renderer = Gtk.CellRendererText()
        note_column = Gtk.TreeViewColumn("Title", note_renderer, text=0)
        note_column.set_sort_column_id(0)
        note_column.set_expand(True)
        self.append_column(note_column)
        
        # Account column (for the account username within each entry)
        account_renderer = Gtk.CellRendererText()
        account_column = Gtk.TreeViewColumn("Account", account_renderer, text=1)
        account_column.set_sort_column_id(1)
        self.append_column(account_column)
        
        # 2FA column
        totp_renderer = Gtk.CellRendererText()
        totp_column = Gtk.TreeViewColumn("2FA", totp_renderer, text=2)
        totp_column.set_sort_column_id(2)
        totp_column.set_min_width(50)
        self.append_column(totp_column)
        
        # Created column
        created_renderer = Gtk.CellRendererText()
        created_column = Gtk.TreeViewColumn("Created", created_renderer, text=3)
        created_column.set_sort_column_id(3)
        self.append_column(created_column)
        
        # Updated column
        updated_renderer = Gtk.CellRendererText()
        updated_column = Gtk.TreeViewColumn("Updated", updated_renderer, text=4)
        updated_column.set_sort_column_id(4)
        self.append_column(updated_column)
        
        # Enable search
        self.set_enable_search(True)
        self.set_search_column(0)
        
        # Enable sorting
        self.set_headers_clickable(True)
        
        # Connect signals
        self.connect("row-activated", self._on_row_activated)
        self.connect("button-press-event", self._on_button_press)
        
        # Create context menu
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Create right-click context menu"""
        self.context_menu = Gtk.Menu()
        
        # Copy password
        copy_item = Gtk.MenuItem("Copy Password")
        copy_item.connect("activate", self._on_copy_password)
        self.context_menu.append(copy_item)
        
        # Copy account
        copy_user_item = Gtk.MenuItem("Copy Account")
        copy_user_item.connect("activate", self._on_copy_username)
        self.context_menu.append(copy_user_item)
        
        # Copy TOTP (will be shown/hidden based on entry)
        self.copy_totp_item = Gtk.MenuItem("Copy 2FA Code")
        self.copy_totp_item.connect("activate", self._on_copy_totp)
        self.context_menu.append(self.copy_totp_item)
        
        # Separator
        self.context_menu.append(Gtk.SeparatorMenuItem())
        
        # Edit
        edit_item = Gtk.MenuItem("Edit")
        edit_item.connect("activate", self._on_edit_entry)
        self.context_menu.append(edit_item)
        
        # Delete
        delete_item = Gtk.MenuItem("Delete")
        delete_item.connect("activate", self._on_delete_entry)
        self.context_menu.append(delete_item)
        
        self.context_menu.show_all()
    
    def _filter_func(self, model, iter, data):
        """Filter function for search"""
        if not self.filter_text:
            return True
        
        note = model[iter][0].lower()
        username = model[iter][1].lower()
        search = self.filter_text.lower()
        
        return search in note or search in username
    
    def set_filter(self, text):
        """Set search filter"""
        self.filter_text = text
        self.filtered_store.refilter()
    
    def update_session(self, session, vault_commands):
        """Update session and vault commands references"""
        self.session = session
        self.vault_commands = vault_commands
    
    def refresh(self):
        """Refresh vault entries"""
        self.store.clear()
        
        if not self.session.vault:
            return
        
        for entry in self.session.vault.entries:
            # Format dates
            created = ""
            updated = ""
            
            if hasattr(entry, 'created_at') and entry.created_at:
                try:
                    dt = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00'))
                    created = dt.strftime("%Y-%m-%d")
                except:
                    created = entry.created_at
            
            if hasattr(entry, 'updated_at') and entry.updated_at:
                try:
                    dt = datetime.fromisoformat(entry.updated_at.replace('Z', '+00:00'))
                    updated = dt.strftime("%Y-%m-%d")
                except:
                    updated = entry.updated_at
            
            # Check if entry has TOTP
            has_totp = "Yes" if (hasattr(entry, 'totp_secret') and getattr(entry, 'totp_secret')) else "No"
            
            self.store.append([
                getattr(entry, 'note', ''),
                getattr(entry, 'username', ''),
                has_totp,
                created,
                updated,
                entry
            ])
    
    def _get_selected_entry(self):
        """Get currently selected entry"""
        selection = self.get_selection()
        model, iter = selection.get_selected()
        if iter:
            # Get from sorted/filtered model
            return model[iter][5]  # Updated index for entry object
        return None
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle row double-click"""
        model = self.get_model()
        iter = model.get_iter(path)
        entry = model[iter][5]  # Updated index for entry object
        self.emit('entry-selected', entry)
    
    def _on_button_press(self, widget, event):
        """Handle mouse button press"""
        if event.button == 3:  # Right click
            # Select row under cursor
            result = self.get_path_at_pos(int(event.x), int(event.y))
            if result:
                path, column, x, y = result
                self.get_selection().select_path(path)
                
                # Update context menu based on selected entry
                entry = self._get_selected_entry()
                if entry and hasattr(entry, 'totp_secret') and entry.totp_secret:
                    self.copy_totp_item.show()
                else:
                    self.copy_totp_item.hide()
                
                # Show context menu
                self.context_menu.popup_at_pointer(event)
                return True
        return False
    
    def _on_copy_password(self, menu_item):
        """Copy password to clipboard"""
        entry = self._get_selected_entry()
        if entry:
            password = getattr(entry, 'password', '')
            if password:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(password, -1)
                self.emit('entry-copied', getattr(entry, 'note', ''))
    
    def _on_copy_username(self, menu_item):
        """Copy username to clipboard"""
        entry = self._get_selected_entry()
        if entry:
            username = getattr(entry, 'username', '')
            if username:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(username, -1)
    
    def _on_copy_totp(self, menu_item):
        """Copy TOTP code to clipboard"""
        entry = self._get_selected_entry()
        if entry and hasattr(entry, 'totp_secret') and entry.totp_secret:
            try:
                # Import TOTP manager
                import sys, os
                cli_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cli')
                if cli_path not in sys.path:
                    sys.path.insert(0, cli_path)
                from core.totp import TOTPManager
                
                code = TOTPManager.generate_totp(entry.totp_secret)
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(code, -1)
                print(f"2FA code copied for {getattr(entry, 'note', '')}")
            except Exception as e:
                print(f"Failed to generate TOTP code: {e}")
    
    def _on_edit_entry(self, menu_item):
        """Edit selected entry"""
        entry = self._get_selected_entry()
        if entry:
            self.emit('entry-selected', entry)
    
    def _on_delete_entry(self, menu_item):
        """Delete selected entry"""
        entry = self._get_selected_entry()
        if not entry:
            return
        
        # Confirm deletion
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete entry '{getattr(entry, 'note', '')}'?"
        )
        dialog.format_secondary_text("This action cannot be undone.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Find and remove entry
            for i, e in enumerate(self.session.vault.entries):
                if getattr(e, 'note', '') == getattr(entry, 'note', ''):
                    self.session.vault.entries.pop(i)
                    break
            
            # Save vault
            if self.session.save_vault():
                self.refresh()
                
                # Show status in main window
                window = self.get_toplevel()
                if hasattr(window, 'show_message'):
                    window.show_message("Entry deleted", Gtk.MessageType.INFO)