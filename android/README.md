# Android Build Setup

## Release Signing Configuration

To build release APKs, you need to configure signing keys:

1. **Copy the template file:**
   ```bash
   cp keystore.properties.template keystore.properties
   ```

2. **Edit `keystore.properties`** with your actual keystore values:
   ```properties
   storePassword=YOUR_ACTUAL_PASSWORD
   keyPassword=YOUR_ACTUAL_PASSWORD
   keyAlias=upass
   storeFile=../upass-release.keystore
   ```

3. **Build release APK:**
   ```bash
   ./gradlew assembleRelease
   ```

## Security Notes

- **Never commit `keystore.properties`** - it's already in `.gitignore`
- **Never commit `*.keystore` files** - they're also in `.gitignore`
- Keep your keystore and passwords safe - you need them for app updates
- The template file `keystore.properties.template` can be safely committed

## Fallback Behavior

If `keystore.properties` is missing, the build will fall back to using the Android debug keystore for development builds.