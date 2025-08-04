# 🔐 UPass - Zero-Knowledge Password Manager

UPass is a modern, secure password manager built with zero-knowledge architecture. Your data is encrypted client-side and never stored in plaintext on the server, ensuring complete privacy and security.

## ✨ Features

- **🔒 Zero-Knowledge Encryption**: All data is encrypted client-side using industry-standard cryptography
- **🔐 TOTP 2FA Support**: Generate time-based one-time passwords with QR code scanning
- **🌐 Cross-Platform**: Available on Desktop (Linux, Windows, macOS) and Android
- **🏠 Self-Hosted**: Run your own server for complete control over your data
- **📱 Multi-Device Sync**: Access your passwords across all your devices

*...and many more!*

## 🏗️ Architecture

UPass follows a client-server architecture with three main components:

### 🖥️ Desktop Application
- **GUI**: Modern GTK3-based interface for Linux, Windows, and macOS
- **CLI**: Command-line interface for power users and automation
- **Unified Launcher**: Single executable that automatically detects GUI vs CLI usage

### 📱 Android Application
- Native Android app built with Kotlin
- Material Design UI
- QR code scanning for easy TOTP setup
- Secure encrypted storage
- [Get it on Google Play](https://play.google.com/store/apps/details?id=ch.upass) or download APK from [releases page](https://github.com/aeeravsar/UPass/releases)

### 🌐 Server
- Flask-based REST API server
- SQLite database with encrypted vault storage
- Support for custom server deployments

## 🚀 Quick Start

### Desktop (GUI)
```bash
# Download the latest release for your platform
# Linux
./upass

# Windows
upass.exe

# With custom server
./upass --server https://your-server.com
```

### Desktop (CLI)
```bash
# Create a new vault
./upass create-vault

# Login to existing vault
./upass login

# Add a new password entry
./upass add github

# Get a password (copies to clipboard)
./upass get github

# List all entries
./upass list
```

### Server
```bash
cd server/
pip install -r requirements.txt
./run.py --port 8000
```

### Android
[Get it on Google Play](https://play.google.com/store/apps/details?id=ch.upass) or install the APK from the [releases page](https://github.com/aeeravsar/UPass/releases).

## 🔧 Installation

### From Releases
Download pre-built binaries from the [GitHub Releases](https://github.com/aeeravsar/UPass/releases) page.

### From Source

#### Desktop
```bash
cd desktop/
pip install -r requirements.txt

# Launch GUI (no arguments)
python upass.py

# Launch CLI (with command)
python upass.py login

# Build executable
pip install pyinstaller
cd build/
pyinstaller upass.spec
```

#### Android
```bash
cd android/
./gradlew assembleDebug
# APK will be in app/build/outputs/apk/debug/
```

#### Server
```bash
cd server/
pip install -r requirements.txt
python run.py
```

## 🔐 Security

UPass implements zero-knowledge encryption with the following security measures:

- **Client-Side Encryption**: All passwords are encrypted using AES-256-GCM before leaving your device
- **Key Derivation**: Master passwords are processed using Argon2id for secure key derivation
- **Digital Signatures**: All API requests are cryptographically signed using Ed25519
- **No Plaintext Storage**: The server never sees your unencrypted data

## 🤝 Contributing

UPass is barely a thing right now. But with your help it could grow.

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/aeeravsar/UPass/issues)
- **Contact**: For any questions or help, send emails to info@upass.ch

## 🎯 Roadmap

- [ ] Rewrite the desktop app fully in Rust
- [ ] Write the browser extension
- [ ] Write the iOS app
- [ ] Upgrade the UX
