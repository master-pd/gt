package com.personal.autobackup.worker

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.personal.autobackup.service.BackupService
import com.personal.autobackup.utils.SharedPrefManager
import kotlinx.coroutines.delay
import timber.log.Timber

class BackupWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        Timber.d("BackupWorker started")
        
        return try {
            // Check if auto backup is enabled
            val sharedPref = SharedPrefManager(applicationContext)
            
            if (!sharedPref.isAutoBackupEnabled()) {
                Timber.d("Auto backup is disabled")
                return Result.success()
            }
            
            // Check WiFi only setting
            if (sharedPref.isWifiOnly()) {
                val connectivityManager = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE)
                    as android.net.ConnectivityManager
                
                val network = connectivityManager.activeNetwork
                val capabilities = connectivityManager.getNetworkCapabilities(network)
                
                if (capabilities?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) != true) {
                    Timber.d("WiFi not available, skipping backup")
                    return Result.success()
                }
            }
            
            // Start backup service
            val serviceIntent = android.content.Intent(applicationContext, BackupService::class.java)
            
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                applicationContext.startForegroundService(serviceIntent)
            } else {
                applicationContext.startService(serviceIntent)
            }
            
            Timber.d("Backup service started from worker")
            
            // Wait for a while
            delay(5000)
            
            Result.success()
            
        } catch (e: Exception) {
            Timber.e(e, "BackupWorker failed")
            Result.failure()
        }
    }
}
