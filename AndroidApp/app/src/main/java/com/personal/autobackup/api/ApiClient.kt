package com.personal.autobackup.api

import android.content.Context
import com.personal.autobackup.BuildConfig
import com.personal.autobackup.api.response.UploadResponse
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface ApiService {
    @GET("api/status")
    suspend fun getStatus(
        @Header("X-API-Key") apiKey: String
    ): StatusResponse
    
    @Multipart
    @POST("api/upload")
    suspend fun uploadFile(
        @Part file: MultipartBody.Part,
        @Header("X-API-Key") apiKey: String,
        @Header("device_id") deviceId: String
    ): Response<UploadResponse>
    
    @GET("api/files")
    suspend fun getFiles(
        @Header("X-API-Key") apiKey: String,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): FilesResponse
    
    @GET("api/scan")
    suspend fun scanFiles(
        @Header("X-API-Key") apiKey: String,
        @Header("device_id") deviceId: String
    ): ScanResponse
}

data class StatusResponse(
    val status: String,
    val total_files: Int,
    val total_size_mb: Double,
    val last_backup: String?
)

data class FilesResponse(
    val files: List<FileItem>,
    val count: Int,
    val total: Int
)

data class FileItem(
    val id: Int,
    val filename: String,
    val file_size: Long,
    val file_type: String,
    val cloudinary_url: String,
    val upload_date: String
)

data class ScanResponse(
    val new_files: List<NewFile>,
    val count: Int,
    val folders_scanned: Int
)

data class NewFile(
    val path: String,
    val name: String,
    val size: Long,
    val hash: String
)

class ApiClient(private val context: Context) {
    
    private val apiService: ApiService by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
        
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                    .addHeader("User-Agent", "AutoBackup/1.0.0")
                    .addHeader("Accept", "application/json")
                    .build()
                chain.proceed(request)
            }
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
        
        Retrofit.Builder()
            .baseUrl(BuildConfig.SERVER_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
    
    suspend fun getStatus(): StatusResponse? {
        return try {
            apiService.getStatus(BuildConfig.API_KEY)
        } catch (e: Exception) {
            null
        }
    }
    
    suspend fun uploadFile(
        file: MultipartBody.Part,
        deviceId: String
    ): Response<UploadResponse> {
        return apiService.uploadFile(file, BuildConfig.API_KEY, deviceId)
    }
    
    suspend fun getFiles(limit: Int = 50, offset: Int = 0): FilesResponse? {
        return try {
            apiService.getFiles(BuildConfig.API_KEY, limit, offset)
        } catch (e: Exception) {
            null
        }
    }
    
    suspend fun scanFiles(deviceId: String): ScanResponse? {
        return try {
            apiService.scanFiles(BuildConfig.API_KEY, deviceId)
        } catch (e: Exception) {
            null
        }
    }
}
