package ch.upass.utils

import ch.upass.BuildConfig

/**
 * Version utilities for UPass Android app
 */
object Version {
    
    /**
     * Get the current app version name (e.g., "1.2.3")
     */
    fun getVersionName(): String = BuildConfig.VERSION_NAME
    
    /**
     * Get the current app version code (e.g., 10203 for v1.2.3)
     */
    fun getVersionCode(): Int = BuildConfig.VERSION_CODE
    
    /**
     * Get formatted version string for display
     */
    fun getVersionString(): String = "UPass v${getVersionName()}"
    
    /**
     * Get detailed version information
     */
    fun getVersionInfo(): VersionInfo {
        val parts = getVersionName().split(".")
        return VersionInfo(
            versionName = getVersionName(),
            versionCode = getVersionCode(),
            major = parts.getOrNull(0)?.toIntOrNull() ?: 0,
            minor = parts.getOrNull(1)?.toIntOrNull() ?: 0,
            patch = parts.getOrNull(2)?.toIntOrNull() ?: 0
        )
    }
    
    /**
     * Data class containing version information
     */
    data class VersionInfo(
        val versionName: String,
        val versionCode: Int,
        val major: Int,
        val minor: Int,
        val patch: Int
    )
}