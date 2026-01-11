package com.personal.autobackup

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.work.*
import com.personal.autobackup.worker.BackupWorker
import timber.log.Timber
import java.util.concurrent.TimeUnit

class AutoBackupApp : Application() {
    
    companion object {
        const val CHANNEL_ID = "backup_channel"
        const val WORKER_TAG = "auto_backup_worker"
    }
    
    override fun onCreate() {
        super.onCreate()
        
        // Timber লগিং
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }
        
        // Notification Channel তৈরি
        createNotificationChannel()
        
        // Work Manager সেটআপ
        setupWorkManager()
        
        Timber.d("✅ AutoBackup অ্যাপ শুরু হয়েছে")
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = getString(R.string.channel_name)
            val descriptionText = getString(R.string.channel_description)
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun setupWorkManager() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(true)
            .build()
        
        val backupRequest = PeriodicWorkRequestBuilder<BackupWorker>(
            15, TimeUnit.MINUTES  // প্রতি ১৫ মিনিটে চেক করবে
        )
            .setConstraints(constraints)
            .addTag(WORKER_TAG)
            .build()
        
        WorkManager.getInstance(this)
            .enqueueUniquePeriodicWork(
                "auto_backup",
                ExistingPeriodicWorkPolicy.KEEP,
                backupRequest
            )
        
        Timber.d("✅ Work Manager সেটআপ সম্পূর্ণ")
    }
}
