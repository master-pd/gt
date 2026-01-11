package com.personal.autobackup.utils

import android.content.Context
import android.os.Environment
import android.os.StatFs
import timber.log.Timber
import java.io.File
import java.security.MessageDigest
import java.util.*

class FileScanner(private val context: Context) {
    
    private val sharedPref = SharedPrefManager(context)
    
    // Monitor these folders
    private val monitoredFolders = listOf(
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DCIM),
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES),
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS),
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MUSIC),
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MOVIES)
    )
    
    // Allowed file extensions
    private val allowedExtensions = setOf(
        // Images
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        // Videos
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        // Documents
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt",
        // Audio
        ".mp3", ".wav", ".aac", ".flac", ".m4a",
        // Archives
        ".zip", ".rar", ".7z",
        // Apps
        ".apk"
    )
    
    fun scanForNewFiles(): List<File> {
        val newFiles = mutableListOf<File>()
        val uploadedFiles = sharedPref.getUploadedFiles()
        
        monitoredFolders.forEach { folder ->
            if (folder.exists() && folder.isDirectory) {
                val files = getAllFiles(folder)
                
                files.forEach { file ->
                    val fileHash = calculateFileHash(file)
                    
                    if (fileHash !in uploadedFiles) {
                        if (isFileAllowed(file)) {
                            newFiles.add(file)
                            Timber.d("New file found: ${file.name}")
                        }
                    }
                }
            }
        }
        
        Timber.d("Total new files: ${newFiles.size}")
        return newFiles
    }
    
    fun markFileAsUploaded(filePath: String) {
        val file = File(filePath)
        val fileHash = calculateFileHash(file)
        sharedPref.addUploadedFile(fileHash)
    }
    
    fun getStorageInfo(): StorageInfo {
        val stat = StatFs(Environment.getExternalStorageDirectory().path)
        val blockSize = stat.blockSizeLong
        val totalBlocks = stat.blockCountLong
        val availableBlocks = stat.availableBlocksLong
        
        val totalGB = (totalBlocks * blockSize) / (1024 * 1024 * 1024)
        val availableGB = (availableBlocks * blockSize) / (1024 * 1024 * 1024)
        val usedGB = totalGB - availableGB
        
        return StorageInfo(
            totalGB = totalGB,
            usedGB = usedGB,
            availableGB = availableGB
        )
    }
    
    private fun getAllFiles(directory: File): List<File> {
        val files = mutableListOf<File>()
        
        if (directory.exists() && directory.isDirectory) {
            directory.listFiles()?.forEach { file ->
                if (file.isDirectory) {
                    files.addAll(getAllFiles(file))
                } else {
                    files.add(file)
                }
            }
        }
        
        return files
    }
    
    private fun isFileAllowed(file: File): Boolean {
        val extension = file.extension.lowercase(Locale.US)
        return ".$extension" in allowedExtensions
    }
    
    private fun calculateFileHash(file: File): String {
        return try {
            val digest = MessageDigest.getInstance("SHA-256")
            val bytes = file.readBytes()
            val hashBytes = digest.digest(bytes)
            hashBytes.joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            "${file.name}_${file.length()}_${file.lastModified()}"
        }
    }
    
    data class StorageInfo(
        val totalGB: Long,
        val usedGB: Long,
        val availableGB: Long
    )
}
