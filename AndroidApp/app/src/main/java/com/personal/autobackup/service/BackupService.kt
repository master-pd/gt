package com.personal.autobackup.service

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.*
import androidx.core.app.NotificationCompat
import com.personal.autobackup.AutoBackupApp
import com.personal.autobackup.MainActivity
import com.personal.autobackup.R
import com.personal.autobackup.api.ApiClient
import com.personal.autobackup.api.response.UploadResponse
import com.personal.autobackup.utils.FileScanner
import com.personal.autobackup.utils.SharedPrefManager
import kotlinx.coroutines.*
import okhttp3.MediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import timber.log.Timber
import java.io.File

class BackupService : Service() {
    
    private val serviceJob = Job()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)
    
    private lateinit var fileScanner: FileScanner
    private lateinit var sharedPref: SharedPrefManager
    private lateinit var apiClient: ApiClient
    
    private var isRunning = false
    private var scanInterval = 15 * 60 * 1000L // 15 minutes
    private var lastScanTime = 0L
    
    private val handler = Handler(Looper.getMainLooper())
    private val scanRunnable = object : Runnable {
        override fun run() {
            if (isRunning) {
                scanForNewFiles()
                handler.postDelayed(this, scanInterval)
            }
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        
        Timber.d("BackupService created")
        
        fileScanner = FileScanner(this)
        sharedPref = SharedPrefManager(this)
        apiClient = ApiClient(this)
        
        startForegroundService()
        isRunning = true
        
        // Start scanning
        handler.post(scanRunnable)
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Timber.d("BackupService started")
        return START_STICKY
    }
    
    private fun startForegroundService() {
        val notification = createNotification()
        startForeground(1, notification)
        Timber.d("Foreground service started")
    }
    
    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, AutoBackupApp.CHANNEL_ID)
            .setContentTitle("My Auto Backup")
            .setContentText("Auto backup is running...")
            .setSmallIcon(R.drawable.ic_backup)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }
    
    private fun scanForNewFiles() {
        serviceScope.launch {
            try {
                updateNotification("Scanning for new files...")
                
                val newFiles = fileScanner.scanForNewFiles()
                Timber.d("Found ${newFiles.size} new files")
                
                if (newFiles.isNotEmpty()) {
                    uploadFiles(newFiles)
                } else {
                    updateNotification("No new files found")
                }
                
                lastScanTime = System.currentTimeMillis()
                sharedPref.saveLastScanTime(lastScanTime)
                
            } catch (e: Exception) {
                Timber.e(e, "Error scanning files")
                updateNotification("Error: ${e.message}")
            }
        }
    }
    
    private suspend fun uploadFiles(files: List<File>) {
        files.forEach { file ->
            try {
                if (file.exists() && file.length() > 0) {
                    updateNotification("Uploading: ${file.name}")
                    
                    val response = uploadFileToServer(file)
                    
                    if (response.isSuccessful) {
                        val uploadResponse = response.body()
                        if (uploadResponse?.success == true) {
                            // Mark as uploaded
                            fileScanner.markFileAsUploaded(file.absolutePath)
                            Timber.d("Uploaded: ${file.name}")
                            
                            // Update notification
                            updateNotification("Uploaded: ${file.name}")
                        }
                    }
                    
                    // Delay between uploads to avoid rate limiting
                    delay(1000)
                }
            } catch (e: Exception) {
                Timber.e(e, "Error uploading file: ${file.name}")
            }
        }
    }
    
    private suspend fun uploadFileToServer(file: File): Response<UploadResponse> {
        return withContext(Dispatchers.IO) {
            val requestFile = RequestBody.create(
                MediaType.parse("multipart/form-data"),
                file
            )
            
            val body = MultipartBody.Part.createFormData(
                "file",
                file.name,
                requestFile
            )
            
            val deviceId = sharedPref.getDeviceId()
            
            apiClient.uploadFile(body, deviceId)
        }
    }
    
    private fun updateNotification(message: String) {
        val notification = NotificationCompat.Builder(this, AutoBackupApp.CHANNEL_ID)
            .setContentTitle("My Auto Backup")
            .setContentText(message)
            .setSmallIcon(R.drawable.ic_backup)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
        
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(1, notification)
    }
    
    override fun onDestroy() {
        Timber.d("BackupService destroyed")
        
        isRunning = false
        handler.removeCallbacks(scanRunnable)
        serviceJob.cancel()
        
        stopForeground(true)
        stopSelf()
        
        super.onDestroy()
    }
    
    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
}
