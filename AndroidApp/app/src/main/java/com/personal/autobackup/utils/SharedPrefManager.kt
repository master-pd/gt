package com.personal.autobackup.utils

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

class SharedPrefManager(private val context: Context) {
    
    private val sharedPref: SharedPreferences by lazy {
        context.getSharedPreferences("auto_backup_prefs", Context.MODE_PRIVATE)
    }
    
    private val gson = Gson()
    
    // Device ID
    fun getDeviceId(): String {
        var deviceId = sharedPref.getString("device_id", null)
        
        if (deviceId == null) {
            deviceId = generateDeviceId()
            saveDeviceId(deviceId)
        }
        
        return deviceId
    }
    
    private fun saveDeviceId(deviceId: String) {
        sharedPref.edit().putString("device_id", deviceId).apply()
    }
    
    private fun generateDeviceId(): String {
        return "${android.os.Build.MODEL}_${System.currentTimeMillis()}"
    }
    
    // Uploaded files
    fun getUploadedFiles(): Set<String> {
        val json = sharedPref.getString("uploaded_files", "[]")
        val type = object : TypeToken<Set<String>>() {}.type
        return gson.fromJson(json, type) ?: emptySet()
    }
    
    fun addUploadedFile(fileHash: String) {
        val uploadedFiles = getUploadedFiles().toMutableSet()
        uploadedFiles.add(fileHash)
        
        val json = gson.toJson(uploadedFiles)
        sharedPref.edit().putString("uploaded_files", json).apply()
    }
    
    fun clearUploadedFiles() {
        sharedPref.edit().remove("uploaded_files").apply()
    }
    
    // Settings
    fun isAutoBackupEnabled(): Boolean {
        return sharedPref.getBoolean("auto_backup", true)
    }
    
    fun setAutoBackupEnabled(enabled: Boolean) {
        sharedPref.edit().putBoolean("auto_backup", enabled).apply()
    }
    
    fun isWifiOnly(): Boolean {
        return sharedPref.getBoolean("wifi_only", false)
    }
    
    fun setWifiOnly(enabled: Boolean) {
        sharedPref.edit().putBoolean("wifi_only", enabled).apply()
    }
    
    fun getScanInterval(): Long {
        return sharedPref.getLong("scan_interval", 15 * 60 * 1000L) // 15 minutes
    }
    
    fun setScanInterval(interval: Long) {
        sharedPref.edit().putLong("scan_interval", interval).apply()
    }
    
    // Last scan time
    fun getLastScanTime(): Long {
        return sharedPref.getLong("last_scan_time", 0L)
    }
    
    fun saveLastScanTime(time: Long) {
        sharedPref.edit().putLong("last_scan_time", time).apply()
    }
    
    // Clear all data
    fun clearAll() {
        sharedPref.edit().clear().apply()
    }
}
