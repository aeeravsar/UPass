import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os

# Add CLI path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'cli'))

from utils.config import get_config

class ServerSelectionDialog(Gtk.Dialog):
    """Dialog for selecting or adding UPass servers"""
    
    def __init__(self, parent, current_server=None):
        super().__init__(
            title="Select UPass Server",
            parent=parent,
            flags=0
        )
        
        self.current_server = current_server
        self.selected_server = None
        
        # Set dialog properties
        self.set_default_size(500, 400)
        self.set_modal(True)
        
        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Connect", Gtk.ResponseType.OK)
        
        # Create content
        self._create_content()
        self._load_servers()
        
        # Connect signals
        self.connect('response', self._on_response)
    
    def _create_content(self):
        """Create dialog content"""
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        content_area.set_margin_start(12)
        content_area.set_margin_end(12)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Choose UPass Server</b>")
        title_label.set_halign(Gtk.Align.START)
        content_area.pack_start(title_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_text("Select an existing server or add a new one:")
        desc_label.set_halign(Gtk.Align.START)
        content_area.pack_start(desc_label, False, False, 0)
        
        # Server list
        self._create_server_list(content_area)
        
        # Custom server entry
        self._create_custom_server_entry(content_area)
        
        self.show_all()
    
    def _create_server_list(self, content_area):
        """Create server list view"""
        # List store: server_url, last_username, display_text
        self.server_store = Gtk.ListStore(str, str, str)
        
        # Tree view
        self.server_tree = Gtk.TreeView(model=self.server_store)
        self.server_tree.set_headers_visible(True)
        
        # Columns
        server_column = Gtk.TreeViewColumn("Server")
        server_renderer = Gtk.CellRendererText()
        server_column.pack_start(server_renderer, True)
        server_column.add_attribute(server_renderer, "text", 2)
        self.server_tree.append_column(server_column)
        
        # Selection
        self.server_selection = self.server_tree.get_selection()
        self.server_selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.server_selection.connect('changed', self._on_server_selected)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        scrolled.add(self.server_tree)
        
        content_area.pack_start(scrolled, True, True, 0)
    
    def _create_custom_server_entry(self, content_area):
        """Create custom server URL entry"""
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_area.pack_start(separator, False, False, 6)
        
        # Custom server section
        custom_label = Gtk.Label()
        custom_label.set_markup("<b>Or add a new server:</b>")
        custom_label.set_halign(Gtk.Align.START)
        content_area.pack_start(custom_label, False, False, 0)
        
        # URL entry
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("https://your-server.com")
        self.url_entry.connect('changed', self._on_url_changed)
        self.url_entry.connect('activate', self._on_url_activate)
        content_area.pack_start(self.url_entry, False, False, 0)
        
        # Add button
        self.add_button_widget = Gtk.Button(label="Add Server")
        self.add_button_widget.connect('clicked', self._on_add_server)
        self.add_button_widget.set_sensitive(False)
        content_area.pack_start(self.add_button_widget, False, False, 0)
    
    def _load_servers(self):
        """Load configured servers"""
        config = get_config()
        servers = config.list_servers()
        
        # Add default server if no servers configured
        if not servers:
            servers = [{
                'server_url': 'https://server.upass.ch',
                'last_username': None,
                'dir': 'default'
            }]
        
        # Populate list
        for server in servers:
            display_text = server['server_url']
            if server['last_username']:
                display_text += f" ({server['last_username']})"
            
            iter = self.server_store.append([
                server['server_url'],
                server['last_username'] or '',
                display_text
            ])
            
            # Select current server
            if server['server_url'] == self.current_server:
                self.server_selection.select_iter(iter)
    
    def _on_server_selected(self, selection):
        """Handle server selection"""
        model, treeiter = selection.get_selected()
        if treeiter:
            self.selected_server = model[treeiter][0]
            # Clear custom URL entry
            self.url_entry.set_text("")
    
    def _on_url_changed(self, entry):
        """Handle URL entry changes"""
        text = entry.get_text().strip()
        self.add_button_widget.set_sensitive(bool(text))
        
        # Clear server selection if typing
        if text:
            self.server_selection.unselect_all()
            self.selected_server = text
    
    def _on_url_activate(self, entry):
        """Handle URL entry activation (Enter key)"""
        if self.add_button_widget.get_sensitive():
            self._on_add_server(self.add_button_widget)
    
    def _on_add_server(self, button):
        """Handle add server button"""
        url = self.url_entry.get_text().strip()
        if not url:
            return
        
        # Validate URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
        
        # Add to list
        display_text = url + " (new)"
        iter = self.server_store.append([url, '', display_text])
        self.server_selection.select_iter(iter)
        self.selected_server = url
        
        # Clear entry
        self.url_entry.set_text("")
        self.add_button_widget.set_sensitive(False)
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response"""
        if response_id == Gtk.ResponseType.OK:
            if not self.selected_server:
                # Show error if no server selected
                error_dialog = Gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Please select a server or enter a custom URL"
                )
                error_dialog.run()
                error_dialog.destroy()
                return True  # Don't close dialog
        
        return False  # Allow dialog to close
    
    def get_selected_server(self):
        """Get the selected server URL"""
        return self.selected_server