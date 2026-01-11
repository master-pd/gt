package com.personal.autobackup

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.personal.autobackup.databinding.ActivityMainBinding
import com.personal.autobackup.service.BackupService
import timber.log.Timber

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    
    // Permission request
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.all { it.value }
        
        if (allGranted) {
            startBackupService()
            showSuccessDialog()
        } else {
            showPermissionDeniedDialog()
        }
    }
    
    // Manage storage permission (Android 11+)
    private val manageStorageLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R &&
            Environment.isExternalStorageManager()) {
            checkAndRequestPermissions()
        } else {
            Toast.makeText(this, "Storage permission denied", Toast.LENGTH_LONG).show()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        checkPermissions()
    }
    
    private fun setupUI() {
        // টাইটেল
        supportActionBar?.title = "My Auto Backup"
        supportActionBar?.subtitle = "Personal Backup System"
        
        // Start Backup Button
        binding.btnStartBackup.setOnClickListener {
            checkPermissions()
        }
        
        // Stop Backup Button
        binding.btnStopBackup.setOnClickListener {
            stopBackupService()
        }
        
        // Settings Button
        binding.btnSettings.setOnClickListener {
            showSettingsDialog()
        }
        
        // Status Button
        binding.btnStatus.setOnClickListener {
            checkBackupStatus()
        }
        
        // About Button
        binding.btnAbout.setOnClickListener {
            showAboutDialog()
        }
    }
    
    private fun checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // Android 11+ - Manage External Storage permission needed
            if (Environment.isExternalStorageManager()) {
                checkAndRequestPermissions()
            } else {
                requestManageStoragePermission()
            }
        } else {
            // Android 10 and below
            checkAndRequestPermissions()
        }
    }
    
    private fun requestManageStoragePermission() {
        val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
        intent.data = Uri.parse("package:$packageName")
        manageStorageLauncher.launch(intent)
    }
    
    private fun checkAndRequestPermissions() {
        val permissions = mutableListOf<String>()
        
        // Basic permissions
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.READ_EXTERNAL_STORAGE
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        
        if (permissions.isNotEmpty()) {
            requestPermissionLauncher.launch(permissions.toTypedArray())
        } else {
            startBackupService()
            showSuccessDialog()
        }
    }
    
    private fun startBackupService() {
        val serviceIntent = Intent(this, BackupService::class.java)
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
        
        updateUI(true)
        Toast.makeText(this, "✅ Backup service started", Toast.LENGTH_SHORT).show()
        Timber.d("Backup service started")
    }
    
    private fun stopBackupService() {
        val serviceIntent = Intent(this, BackupService::class.java)
        stopService(serviceIntent)
        
        updateUI(false)
        Toast.makeText(this, "⏸️ Backup service stopped", Toast.LENGTH_SHORT).show()
        Timber.d("Backup service stopped")
    }
    
    private fun updateUI(isRunning: Boolean) {
        binding.btnStartBackup.isEnabled = !isRunning
        binding.btnStopBackup.isEnabled = isRunning
        
        binding.tvStatus.text = if (isRunning) {
            "🟢 Backup service is running"
        } else {
            "🔴 Backup service is stopped"
        }
        
        binding.ivStatus.setImageResource(
            if (isRunning) R.drawable.ic_running else R.drawable.ic_stopped
        )
    }
    
    private fun checkBackupStatus() {
        // Implement status check logic
        Toast.makeText(this, "Checking backup status...", Toast.LENGTH_SHORT).show()
    }
    
    private fun showSuccessDialog() {
        AlertDialog.Builder(this)
            .setTitle("✅ Ready to Backup")
            .setMessage("Your files will be automatically backed up to your personal cloud storage.")
            .setPositiveButton("Great!") { dialog, _ ->
                dialog.dismiss()
            }
            .show()
    }
    
    private fun showPermissionDeniedDialog() {
        AlertDialog.Builder(this)
            .setTitle("⚠️ Permission Required")
            .setMessage("Backup service needs storage permission to work properly.")
            .setPositiveButton("Try Again") { dialog, _ ->
                dialog.dismiss()
                checkPermissions()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun showSettingsDialog() {
        val settings = listOf(
            "Upload Photos",
            "Upload Videos", 
            "Upload Documents",
            "Wi-Fi Only",
            "Battery Saver",
            "Notification"
        )
        
        val checkedItems = booleanArrayOf(true, true, true, false, true, true)
        
        AlertDialog.Builder(this)
            .setTitle("⚙️ Backup Settings")
            .setMultiChoiceItems(settings, checkedItems) { _, which, isChecked ->
                checkedItems[which] = isChecked
                // Save settings
            }
            .setPositiveButton("Save") { dialog, _ ->
                dialog.dismiss()
                Toast.makeText(this, "Settings saved", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun showAboutDialog() {
        AlertDialog.Builder(this)
            .setTitle("ℹ️ About My Auto Backup")
            .setMessage(
                """
                Version: 1.0.0
                Developer: Personal Use Only
                
                Features:
                • Auto backup photos
                • Auto backup videos
                • Auto backup documents
                • Secure cloud storage
                • No file size limit
                
                🔒 This app is for personal use only.
                Do not share with others.
                """.trimIndent()
            )
            .setPositiveButton("Close", null)
            .show()
    }
}
