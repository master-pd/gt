package com.personal.autobackup.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.work.*
import com.personal.autobackup.worker.BackupWorker
import timber.log.Timber
import java.util.concurrent.TimeUnit

class BootReceiver : BroadcastReceiver() {
    
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Timber.d("Boot completed, starting backup worker")
            
            // Schedule backup worker
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()
            
            val backupRequest = PeriodicWorkRequestBuilder<BackupWorker>(
                15, TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .build()
            
            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(
                    "auto_backup_boot",
                    ExistingPeriodicWorkPolicy.KEEP,
                    backupRequest
                )
            
            Timber.d("Backup worker scheduled after boot")
        }
    }
}
