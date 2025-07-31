# UPass GTK GUI Client

A GTK3-based graphical user interface for the UPass zero-knowledge password manager.

## Features

- **Open Vault/Create Vault**: Secure vault access with master password
- **Vault Management**: View, add, edit, and delete password entries
- **Search**: Quick search through vault entries
- **Password Generation**: Built-in secure password generator with customizable options
- **Session Management**: Automatic session persistence and timeout
- **Clipboard Integration**: Copy passwords and usernames to clipboard
- **Zero-Knowledge**: All encryption/decryption happens locally

## Requirements

### System Dependencies

Install GTK3 and Python bindings via your system package manager:

**Ubuntu/Debian:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk3-devel
```

**Arch Linux:**
```bash
sudo pacman -S python-gobject gtk3
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Running the GUI

```bash
# Make executable
chmod +x upass-gui

# Run with default server (https://server.upass.ch)
./upass-gui

# Use a custom server
./upass-gui --server https://my.company.com

# Use local development server
./upass-gui -s http://localhost:8000
```

Or:

```bash
# With Python directly
python3 main.py --server https://my.server.com
```

### Server Configuration

The GUI supports multiple UPass servers with complete isolation:

- **Default server**: `https://server.upass.ch`
- **Custom servers**: Specify with `--server` argument
- **Server switching**: Use the server button in header bar
- **Per-server storage**: Each server gets isolated config in `~/.upass/{server}_{port}/`

#### Server Selection Dialog

Click the server button in the header bar to:
1. **View configured servers** with last used usernames
2. **Select from existing servers** to switch quickly  
3. **Add new custom server** by entering URL
4. **Switch servers** with automatic logout/reconnect

### First Time Setup

1. Launch the GUI application
2. Click "Create Vault" to create a new vault
3. Enter a vault name and secure master password
4. Your vault will be created and you can start adding entries

### Adding Entries

1. Click the "+" button in the header bar
2. Fill in the note, account, and password fields
3. Optionally use the "Generate" button for secure passwords
4. Click "Save" to add the entry

### Managing Entries

- **View/Edit**: Double-click an entry or right-click → Edit
- **Copy Password**: Right-click → Copy Password (or middle-click)
- **Copy Account**: Right-click → Copy Account
- **Delete**: Right-click → Delete
- **Search**: Use the search bar at the top

### Password Generation

- Click the "Generate" button in the header bar for standalone password generation
- Use "Generate" in the add/edit dialog to generate passwords for entries
- Customize length and character sets as needed

## Configuration

The GUI client uses the same configuration system as the CLI:

- **Config directory**: `~/.upass/`
- **Session file**: `~/.upass/session.dat`
- **Config file**: `~/.upass/config`

### Environment Variables

- `UPASS_SERVER_URL`: Server URL (default: http://localhost:8000)
- `UPASS_TIMEOUT`: Request timeout in seconds (default: 10)

## Security Features

- **Master password never stored**: Only derived keys are cached
- **Session timeout**: Automatic logout after 1 hour of inactivity
- **Secure password generation**: Uses cryptographically secure random number generation
- **Memory protection**: Sensitive data cleared on logout
- **Local encryption**: All vault data encrypted locally before transmission

## Keyboard Shortcuts

- **Ctrl+F**: Focus search bar
- **Ctrl+N**: Add new entry
- **Ctrl+R**: Refresh vault
- **Ctrl+Q**: Quit application
- **Enter**: Login/Register (in login screen)
- **Escape**: Cancel dialogs

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError` for GTK-related modules:
1. Ensure GTK3 development packages are installed
2. Check that `python3-gi` is properly installed
3. Try running with `python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"`

### Connection Errors

1. Ensure the UPass server is running
2. Check the `UPASS_SERVER_URL` environment variable
3. Verify network connectivity

### Session Issues

If you encounter session-related problems:
1. Delete `~/.upass/session.dat`
2. Restart the application
3. Login again

## Integration with CLI

The GUI client uses the same backend modules as the CLI client:
- Shared session storage and management
- Same configuration system
- Compatible vault format
- Identical cryptographic operations

You can switch between GUI and CLI seamlessly.