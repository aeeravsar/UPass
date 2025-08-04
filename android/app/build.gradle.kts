import java.util.Properties
import java.io.FileInputStream

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

// Read version from root VERSION file
val rootVersionFile = rootProject.file("../../VERSION")
val projectVersion = if (rootVersionFile.exists()) {
    rootVersionFile.readText().trim()
} else {
    "0.1.0"
}

// Convert semantic version to Android version code
// Formula: Major * 10000 + Minor * 100 + Patch
// Examples: v1.2.3 -> 10203, v0.9.0 -> 900
fun versionNameToCode(version: String): Int {
    return try {
        val parts = version.split(".")
        val major = parts.getOrNull(0)?.toIntOrNull() ?: 0
        val minor = parts.getOrNull(1)?.toIntOrNull() ?: 0
        val patch = parts.getOrNull(2)?.toIntOrNull() ?: 0
        major * 10000 + minor * 100 + patch
    } catch (e: Exception) {
        1 // Fallback version code
    }
}

android {
    namespace = "ch.upass"
    compileSdk = 36

    defaultConfig {
        applicationId = "ch.upass"
        minSdk = 28
        targetSdk = 36
        versionCode = versionNameToCode(projectVersion)
        versionName = projectVersion

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            // Load keystore properties from external file (not committed to git)
            val keystorePropertiesFile = project.file("../keystore.properties")
            if (keystorePropertiesFile.exists()) {
                val keystoreProperties = Properties()
                keystoreProperties.load(FileInputStream(keystorePropertiesFile))
                
                val keystoreFile = project.file(keystoreProperties["storeFile"].toString())
                if (keystoreFile.exists()) {
                    storeFile = keystoreFile
                    storePassword = keystoreProperties["storePassword"].toString()
                    keyAlias = keystoreProperties["keyAlias"].toString()
                    keyPassword = keystoreProperties["keyPassword"].toString()
                }
            } else {
                // Fallback to debug keystore for development when keystore.properties missing
                println("Warning: keystore.properties not found. Copy keystore.properties.template to keystore.properties and configure your signing keys.")
                val debugKeystore = project.file("${System.getProperty("user.home")}/.android/debug.keystore")
                if (debugKeystore.exists()) {
                    storeFile = debugKeystore
                    storePassword = "android"
                    keyAlias = "androiddebugkey"
                    keyPassword = "android"
                }
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        viewBinding = true
        buildConfig = true
    }
}

dependencies {
    // Core Android
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.activity.ktx)
    implementation(libs.fragment.ktx)
    
    // Lifecycle
    implementation(libs.lifecycle.viewmodel)
    implementation(libs.lifecycle.livedata)
    
    // Crypto
    implementation(libs.tink.android)
    implementation(libs.argon2)
    
    // Networking
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    
    // JSON
    implementation(libs.gson)
    
    // Security
    implementation(libs.security.crypto)
    
    // QR Code scanning
    implementation("com.google.mlkit:barcode-scanning:17.3.0")
    implementation("androidx.camera:camera-core:1.3.4")
    implementation("androidx.camera:camera-camera2:1.3.4")
    implementation("androidx.camera:camera-lifecycle:1.3.4")
    implementation("androidx.camera:camera-view:1.3.4")
    
    // Testing
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}