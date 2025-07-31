import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
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


class GenerateDialog(Gtk.Dialog):
    """Dialog for generating passwords"""
    
    def __init__(self, parent, crypto_manager):
        super().__init__(
            title="Generate Password",
            transient_for=parent,
            flags=0
        )
        
        self.crypto = crypto_manager
        
        self._setup_ui()
        self._generate_password()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.set_default_size(450, -1)
        self.set_resizable(False)
        
        # Add buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        copy_button = self.add_button("Copy", Gtk.ResponseType.ACCEPT)
        copy_button.get_style_context().add_class("suggested-action")
        
        # Content area
        content = self.get_content_area()
        content.set_spacing(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_left(12)
        content.set_margin_right(12)
        
        # Password display
        password_frame = Gtk.Frame()
        password_frame.set_label("Generated Password")
        content.pack_start(password_frame, False, False, 0)
        
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        password_box.set_margin_top(6)
        password_box.set_margin_bottom(6)
        password_box.set_margin_left(6)
        password_box.set_margin_right(6)
        password_frame.add(password_box)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_editable(False)
        self.password_entry.set_can_focus(True)
        password_box.pack_start(self.password_entry, True, True, 0)
        
        # Copy button for password
        copy_icon_button = Gtk.Button()
        # Use custom icon for Windows compatibility
        copy_icon_path = get_icon_path('copy')
        if copy_icon_path:
            copy_icon_button.set_image(Gtk.Image.new_from_file(copy_icon_path))
        else:
            copy_icon_button.set_image(
                Gtk.Image.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.BUTTON)
            )
        copy_icon_button.set_tooltip_text("Copy password")
        copy_icon_button.connect("clicked", self._on_copy_clicked)
        password_box.pack_start(copy_icon_button, False, False, 0)
        
        # Show/hide toggle
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
        password_box.pack_start(self.visibility_button, False, False, 0)
        
        # Options frame
        options_frame = Gtk.Frame()
        options_frame.set_label("Options")
        content.pack_start(options_frame, False, False, 0)
        
        options_grid = Gtk.Grid()
        options_grid.set_row_spacing(6)
        options_grid.set_column_spacing(12)
        options_grid.set_margin_top(6)
        options_grid.set_margin_bottom(6)
        options_grid.set_margin_left(6)
        options_grid.set_margin_right(6)
        options_frame.add(options_grid)
        
        # Length setting
        length_label = Gtk.Label("Length:", xalign=0)
        options_grid.attach(length_label, 0, 0, 1, 1)
        
        self.length_spin = Gtk.SpinButton()
        self.length_spin.set_range(8, 128)
        self.length_spin.set_value(16)
        self.length_spin.set_increments(1, 8)
        self.length_spin.connect("value-changed", self._on_option_changed)
        options_grid.attach(self.length_spin, 1, 0, 1, 1)
        
        # Special characters checkbox
        self.special_check = Gtk.CheckButton("Include special characters")
        self.special_check.set_active(True)
        self.special_check.connect("toggled", self._on_option_changed)
        options_grid.attach(self.special_check, 0, 1, 2, 1)
        
        # Generate button
        generate_button = Gtk.Button("Generate New Password")
        generate_button.get_style_context().add_class("destructive-action")
        generate_button.connect("clicked", self._on_generate_clicked)
        options_grid.attach(generate_button, 0, 2, 2, 1)
        
        # Password strength indicator
        strength_frame = Gtk.Frame()
        strength_frame.set_label("Password Strength")
        content.pack_start(strength_frame, False, False, 0)
        
        strength_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        strength_box.set_margin_top(6)
        strength_box.set_margin_bottom(6)
        strength_box.set_margin_left(6)
        strength_box.set_margin_right(6)
        strength_frame.add(strength_box)
        
        self.strength_bar = Gtk.ProgressBar()
        self.strength_bar.set_show_text(True)
        strength_box.pack_start(self.strength_bar, False, False, 0)
        
        self.strength_label = Gtk.Label()
        self.strength_label.get_style_context().add_class("dim-label")
        strength_box.pack_start(self.strength_label, False, False, 0)
        
        # Show all widgets
        self.show_all()
        
        # Focus password entry for easy selection
        self.password_entry.grab_focus()
        self.password_entry.select_region(0, -1)
    
    def _generate_password(self):
        """Generate a new password"""
        length = int(self.length_spin.get_value())
        special = self.special_check.get_active()
        
        password = self.crypto.generate_password(length, special)
        self.password_entry.set_text(password)
        
        # Update strength indicator
        self._update_strength(password)
        
        # Select all text for easy copying
        self.password_entry.select_region(0, -1)
    
    def _update_strength(self, password):
        """Update password strength indicator"""
        length = len(password)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        # Calculate strength score (0-1)
        score = 0
        
        # Length score (max 0.4)
        if length >= 8:
            score += min(0.4, (length - 8) * 0.02 + 0.2)
        
        # Character variety score (max 0.6)
        variety_score = sum([has_lower, has_upper, has_digit, has_special]) * 0.15
        score += variety_score
        
        # Ensure score is between 0 and 1
        score = min(1.0, score)
        
        # Update progress bar
        self.strength_bar.set_fraction(score)
        
        # Determine strength level and color
        if score < 0.3:
            strength_text = "Weak"
            style_class = "error"
        elif score < 0.6:
            strength_text = "Fair"
            style_class = "warning"
        elif score < 0.8:
            strength_text = "Good"  
            style_class = "success"
        else:
            strength_text = "Strong"
            style_class = "success"
        
        self.strength_bar.set_text(f"{strength_text} ({int(score * 100)}%)")
        
        # Update label
        details = []
        if length >= 12:
            details.append("Good length")
        elif length >= 8:
            details.append("Adequate length")
        else:
            details.append("Short length")
        
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        details.append(f"{char_types}/4 character types")
        
        self.strength_label.set_text(" • ".join(details))
    
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
    
    def _on_option_changed(self, widget):
        """Handle option change"""
        self._generate_password()
    
    def _on_generate_clicked(self, button):
        """Handle generate button click"""
        self._generate_password()
    
    def _on_copy_clicked(self, button):
        """Handle copy button click"""
        password = self.password_entry.get_text()
        if password:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(password, -1)
            
            # Show feedback
            parent = self.get_transient_for()
            if hasattr(parent, 'show_message'):
                parent.show_message("Password copied to clipboard", Gtk.MessageType.INFO)
    
    def do_response(self, response_id):
        """Handle dialog response"""
        if response_id == Gtk.ResponseType.ACCEPT:
            # Copy password and close
            self._on_copy_clicked(None)
        
        # Close dialog properly
        if response_id in [Gtk.ResponseType.CLOSE, Gtk.ResponseType.ACCEPT]:
            self.destroy()