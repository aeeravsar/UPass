import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from datetime import datetime
import os
import sys


def get_icon_path(icon_name):
    """Get the correct icon path for current environment (PNG for Windows, SVG for Linux)"""
    base_path = None
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundled environment
        base_path = os.path.join(sys._MEIPASS, 'gui', 'icons')
    else:
        # Development environment
        base_path = os.path.join(os.path.dirname(__file__), '..', 'icons')
    
    # Try PNG first (Windows compatibility), then SVG
    png_path = os.path.join(base_path, f'{icon_name}.png')
    if os.path.exists(png_path):
        return png_path
    
    svg_path = os.path.join(base_path, f'{icon_name}.svg')
    if os.path.exists(svg_path):
        return svg_path
    
    return None


class EntryDialog(Gtk.Dialog):
    """Dialog for adding/editing vault entries"""
    
    def __init__(self, parent, session, vault_commands, entry=None):
        super().__init__(
            title="Edit Entry" if entry else "Add Entry",
            transient_for=parent,
            flags=0
        )
        
        self.session = session
        self.vault_commands = vault_commands
        self.entry = entry
        self.is_new = entry is None
        self.totp_timer_id = None
        self.current_totp_secret = None
        
        self._setup_ui()
        
        # Load entry data if editing
        if entry:
            self._load_entry_data()
        
        # Update TOTP display visibility based on entry state
        self._update_totp_display_visibility()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.set_default_size(400, 300)
        
        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        save_button = self.add_button("Save", Gtk.ResponseType.OK)
        save_button.get_style_context().add_class("suggested-action")
        
        # Content area
        content = self.get_content_area()
        content.set_spacing(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_left(12)
        content.set_margin_right(12)
        
        # Form grid
        grid = Gtk.Grid()
        grid.set_row_spacing(12)
        grid.set_column_spacing(12)
        content.pack_start(grid, True, True, 0)
        
        # Title field
        note_label = Gtk.Label("Title:", xalign=0)
        grid.attach(note_label, 0, 0, 1, 1)
        
        self.note_entry = Gtk.Entry()
        self.note_entry.set_placeholder_text("e.g., GitHub, Gmail, etc.")
        self.note_entry.set_hexpand(True)
        grid.attach(self.note_entry, 1, 0, 2, 1)
        
        # Account field  
        account_label = Gtk.Label("Account:", xalign=0)
        grid.attach(account_label, 0, 1, 1, 1)
        
        self.username_entry = Gtk.Entry()
        self.username_entry.set_placeholder_text("Account username or email")
        grid.attach(self.username_entry, 1, 1, 2, 1)
        
        # Password field
        password_label = Gtk.Label("Password:", xalign=0)
        grid.attach(password_label, 0, 2, 1, 1)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_placeholder_text("Enter password")
        grid.attach(self.password_entry, 1, 2, 1, 1)
        
        # Password visibility toggle
        self.visibility_button = Gtk.ToggleButton()
        # Use custom icon for Windows compatibility
        reveal_icon_path = get_icon_path('view-reveal')
        if reveal_icon_path:
            self.visibility_button.set_image(Gtk.Image.new_from_file(reveal_icon_path))
        else:
            self.visibility_button.set_image(
                Gtk.Image.new_from_icon_name("view-reveal-symbolic", Gtk.IconSize.BUTTON)
            )
        self.visibility_button.set_tooltip_text("Show/hide password")
        self.visibility_button.connect("toggled", self._on_visibility_toggled)
        grid.attach(self.visibility_button, 2, 2, 1, 1)
        
        # Generate password button
        generate_button = Gtk.Button("Generate")
        generate_button.connect("clicked", self._on_generate_clicked)
        grid.attach(generate_button, 0, 3, 1, 1)
        
        # Password options
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.length_spin = Gtk.SpinButton()
        self.length_spin.set_range(8, 128)
        self.length_spin.set_value(16)
        self.length_spin.set_increments(1, 8)
        options_box.pack_start(Gtk.Label("Length:"), False, False, 0)
        options_box.pack_start(self.length_spin, False, False, 0)
        
        self.special_check = Gtk.CheckButton("Special chars")
        self.special_check.set_active(True)
        options_box.pack_start(self.special_check, False, False, 0)
        
        grid.attach(options_box, 1, 3, 2, 1)
        
        # TOTP Section
        totp_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(totp_separator, 0, 4, 3, 1)
        
        # TOTP checkbox
        self.totp_check = Gtk.CheckButton("Add Two-Factor Authentication (2FA)")
        self.totp_check.connect("toggled", self._on_totp_toggled)
        grid.attach(self.totp_check, 0, 5, 3, 1)
        
        # TOTP secret field
        totp_secret_label = Gtk.Label("2FA Secret:", xalign=0)
        grid.attach(totp_secret_label, 0, 6, 1, 1)
        
        self.totp_secret_entry = Gtk.Entry()
        self.totp_secret_entry.set_placeholder_text("Base32 secret (e.g., JBSWY3DPEHPK3PXP)")
        self.totp_secret_entry.set_sensitive(False)
        grid.attach(self.totp_secret_entry, 1, 6, 2, 1)
        
        
        # TOTP Display Section (for existing entries with TOTP)
        self.totp_display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.totp_display_box.set_margin_top(12)
        self.totp_display_box.set_margin_bottom(12)
        grid.attach(self.totp_display_box, 0, 7, 3, 1)
        
        # TOTP code display
        totp_display_grid = Gtk.Grid()
        totp_display_grid.set_column_spacing(12)
        totp_display_grid.set_row_spacing(6)
        self.totp_display_box.pack_start(totp_display_grid, False, False, 0)
        
        # Current 2FA code label
        self.totp_current_label = Gtk.Label("Current 2FA Code:", xalign=0)
        self.totp_current_label.set_markup("<b>Current 2FA Code:</b>")
        totp_display_grid.attach(self.totp_current_label, 0, 0, 1, 1)
        
        # TOTP code display
        self.totp_code_label = Gtk.Label("", xalign=0.5)  # Center align
        self.totp_code_label.set_markup("<span font_family='monospace' size='x-large' color='red'><b>123 456</b></span>")
        totp_display_grid.attach(self.totp_code_label, 1, 0, 1, 1)
        
        # Copy TOTP button
        copy_totp_button = Gtk.Button("Copy")
        copy_totp_button.connect("clicked", self._on_copy_totp_clicked)
        totp_display_grid.attach(copy_totp_button, 2, 0, 1, 1)
        
        # Countdown display
        self.totp_countdown_label = Gtk.Label("30s remaining", xalign=0)
        self.totp_countdown_label.get_style_context().add_class("dim-label")
        totp_display_grid.attach(self.totp_countdown_label, 1, 1, 1, 1)
        
        # Progress bar
        self.totp_progress = Gtk.ProgressBar()
        self.totp_progress.set_fraction(0.5)
        totp_display_grid.attach(self.totp_progress, 1, 2, 1, 1)
        
        # Initially hide TOTP display
        self.totp_display_box.set_visible(False)
        
        # Timestamps (for existing entries)
        timestamp_row = 8  # Updated row number
        if self.entry:
            # Timestamps separator
            ts_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            grid.attach(ts_separator, 0, timestamp_row, 3, 1)
            timestamp_row += 1
            
            # Created
            if hasattr(self.entry, 'created_at') and self.entry.created_at:
                created_label = Gtk.Label("Created:", xalign=0)
                created_label.get_style_context().add_class("dim-label")
                grid.attach(created_label, 0, timestamp_row, 1, 1)
                
                created_value = Gtk.Label(xalign=0)
                created_value.get_style_context().add_class("dim-label")
                try:
                    dt = datetime.fromisoformat(self.entry.created_at.replace('Z', '+00:00'))
                    created_value.set_text(dt.strftime("%Y-%m-%d %H:%M"))
                except:
                    created_value.set_text(self.entry.created_at)
                grid.attach(created_value, 1, timestamp_row, 2, 1)
                timestamp_row += 1
            
            # Updated
            if hasattr(self.entry, 'updated_at') and self.entry.updated_at:
                updated_label = Gtk.Label("Updated:", xalign=0)
                updated_label.get_style_context().add_class("dim-label")
                grid.attach(updated_label, 0, timestamp_row, 1, 1)
                
                updated_value = Gtk.Label(xalign=0)
                updated_value.get_style_context().add_class("dim-label")
                try:
                    dt = datetime.fromisoformat(self.entry.updated_at.replace('Z', '+00:00'))
                    updated_value.set_text(dt.strftime("%Y-%m-%d %H:%M"))
                except:
                    updated_value.set_text(self.entry.updated_at)
                grid.attach(updated_value, 1, timestamp_row, 2, 1)
        
        # Show all widgets
        self.show_all()
        
        # Focus note field
        self.note_entry.grab_focus()
    
    def _load_entry_data(self):
        """Load existing entry data"""
        if not self.entry:
            return
        
        self.note_entry.set_text(getattr(self.entry, 'note', ''))
        self.username_entry.set_text(getattr(self.entry, 'username', ''))
        self.password_entry.set_text(getattr(self.entry, 'password', ''))
        
        # Load TOTP data if present
        if hasattr(self.entry, 'totp_secret') and getattr(self.entry, 'totp_secret'):
            self.totp_check.set_active(True)
            self.totp_secret_entry.set_text(getattr(self.entry, 'totp_secret', ''))
            
            # Start TOTP display
            self.current_totp_secret = getattr(self.entry, 'totp_secret')
            self.totp_display_box.set_visible(True)
            self._start_totp_timer()
        
        # Disable note editing for existing entries
        self.note_entry.set_sensitive(False)
    
    def _on_visibility_toggled(self, button):
        """Toggle password visibility"""
        visible = button.get_active()
        self.password_entry.set_visibility(visible)
        
        # Update icon with custom icons for Windows compatibility
        icon_name = "view-conceal" if visible else "view-reveal"
        icon_path = get_icon_path(icon_name)
        if icon_path:
            button.set_image(Gtk.Image.new_from_file(icon_path))
        else:
            # Fallback to system icons
            system_icon_name = "view-conceal-symbolic" if visible else "view-reveal-symbolic"
            button.set_image(
                Gtk.Image.new_from_icon_name(system_icon_name, Gtk.IconSize.BUTTON)
            )
    
    def _on_totp_toggled(self, checkbox):
        """Toggle TOTP fields sensitivity"""
        enabled = checkbox.get_active()
        self.totp_secret_entry.set_sensitive(enabled)
        
        if not enabled:
            # Clear fields when disabled
            self.totp_secret_entry.set_text("")
            self._stop_totp_timer()
            self.current_totp_secret = None
        
        # Update display visibility
        self._update_totp_display_visibility()
    
    def _on_generate_clicked(self, button):
        """Generate password"""
        length = int(self.length_spin.get_value())
        special = self.special_check.get_active()
        
        password = self.session.crypto.generate_password(length, special)
        self.password_entry.set_text(password)
        
        # Show password when generated
        self.visibility_button.set_active(True)
    
    def _on_copy_totp_clicked(self, button):
        """Copy current TOTP code to clipboard"""
        if self.current_totp_secret:
            try:
                # Import TOTP manager
                import sys, os
                cli_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cli')
                if cli_path not in sys.path:
                    sys.path.insert(0, cli_path)
                from core.totp import TOTPManager
                
                code = TOTPManager.generate_totp(self.current_totp_secret)
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(code, -1)
                
                # Show feedback
                button.set_label("Copied!")
                GLib.timeout_add(1000, lambda: button.set_label("Copy"))
            except Exception as e:
                print(f"Failed to copy TOTP code: {e}")
    
    def _start_totp_timer(self):
        """Start the TOTP update timer"""
        self._stop_totp_timer()  # Stop any existing timer
        self._update_totp_display()  # Initial update
        self.totp_timer_id = GLib.timeout_add(1000, self._update_totp_display)
    
    def _stop_totp_timer(self):
        """Stop the TOTP update timer"""
        if self.totp_timer_id:
            GLib.source_remove(self.totp_timer_id)
            self.totp_timer_id = None
    
    def _update_totp_display(self):
        """Update TOTP code display"""
        if not self.current_totp_secret:
            return False  # Stop timer
        
        try:
            # Import TOTP manager
            import sys, os
            cli_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cli')
            if cli_path not in sys.path:
                sys.path.insert(0, cli_path)
            from core.totp import TOTPManager
            
            # Generate current code
            code = TOTPManager.generate_totp(self.current_totp_secret)
            formatted_code = TOTPManager.format_code(code)
            
            # Update display
            self.totp_code_label.set_markup(
                f"<span font_family='monospace' size='x-large' color='red'><b>{formatted_code}</b></span>"
            )
            
            # Update countdown
            remaining = TOTPManager.get_remaining_seconds()
            self.totp_countdown_label.set_text(f"{remaining}s remaining")
            
            # Update progress bar
            progress = remaining / 30.0
            self.totp_progress.set_fraction(progress)
            
            return True  # Continue timer
        except Exception as e:
            print(f"Error updating TOTP display: {e}")
            self.totp_code_label.set_markup("<span color='red'>Error</span>")
            return False  # Stop timer
    
    def _update_totp_display_visibility(self):
        """Update TOTP display visibility based on current state"""
        # Only show TOTP display if:
        # 1. We're editing an existing entry (not adding new)
        # 2. TOTP is enabled/checked
        # 3. We have a current TOTP secret
        should_show = (
            not self.is_new and  # Not adding new entry
            self.totp_check.get_active() and  # TOTP is enabled
            self.current_totp_secret  # Has TOTP secret
        )
        
        if should_show:
            self.totp_display_box.set_visible(True)
            self._start_totp_timer()
        else:
            self.totp_display_box.set_visible(False)
            self._stop_totp_timer()
    
    def do_response(self, response_id):
        """Handle dialog response"""
        if response_id == Gtk.ResponseType.OK:
            # Validate inputs
            note = self.note_entry.get_text().strip()
            username = self.username_entry.get_text().strip()
            password = self.password_entry.get_text()
            
            if not note:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Title is required"
                )
                dialog.run()
                dialog.destroy()
                return  # Don't close dialog
            
            if not username:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Account is required"
                )
                dialog.run()
                dialog.destroy()
                return  # Don't close dialog
            
            if not password:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Password is required"
                )
                dialog.run()
                dialog.destroy()
                return  # Don't close dialog
            
            # Get TOTP data
            totp_secret = None
            if self.totp_check.get_active():
                totp_secret = self.totp_secret_entry.get_text().strip().upper().replace(' ', '')
                
                # Validate TOTP secret if provided
                if totp_secret:
                    try:
                        # Import TOTP manager for validation
                        import sys, os
                        cli_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cli')
                        if cli_path not in sys.path:
                            sys.path.insert(0, cli_path)
                        from core.totp import TOTPManager
                        
                        if not TOTPManager.is_valid_secret(totp_secret):
                            dialog = Gtk.MessageDialog(
                                transient_for=self,
                                flags=0,
                                message_type=Gtk.MessageType.ERROR,
                                buttons=Gtk.ButtonsType.OK,
                                text="Invalid 2FA secret. Must be a valid Base32 string."
                            )
                            dialog.run()
                            dialog.destroy()
                            return  # Don't close dialog
                    except Exception as e:
                        dialog = Gtk.MessageDialog(
                            transient_for=self,
                            flags=0,
                            message_type=Gtk.MessageType.ERROR,
                            buttons=Gtk.ButtonsType.OK,
                            text=f"Error validating 2FA secret: {e}"
                        )
                        dialog.run()
                        dialog.destroy()
                        return  # Don't close dialog
            
            # Save entry
            if self.is_new:
                # Check if note already exists
                for entry in self.session.vault.entries:
                    if getattr(entry, 'note', '').lower() == note.lower():
                        dialog = Gtk.MessageDialog(
                            transient_for=self,
                            flags=0,
                            message_type=Gtk.MessageType.ERROR,
                            buttons=Gtk.ButtonsType.OK,
                            text=f"An entry with note '{note}' already exists"
                        )
                        dialog.run()
                        dialog.destroy()
                        return  # Don't close dialog
                
                # Add new entry using the vault's add_entry method
                self.session.vault.add_entry(username, password, note, totp_secret)
            else:
                # Update existing entry using the vault's update_entry method
                self.session.vault.update_entry(
                    note=getattr(self.entry, 'note', ''),
                    username=username,
                    password=password,
                    totp_secret=totp_secret
                )
            
            # Save vault
            if not self.session.save_vault():
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Failed to save vault"
                )
                dialog.run()
                dialog.destroy()
                return  # Don't close dialog
        
        # Close dialog properly
        if response_id in [Gtk.ResponseType.OK, Gtk.ResponseType.CANCEL]:
            self._stop_totp_timer()  # Clean up timer
            self.destroy()