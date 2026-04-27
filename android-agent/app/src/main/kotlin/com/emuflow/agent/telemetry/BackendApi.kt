package com.emuflow.agent.telemetry

import com.emuflow.agent.BuildConfig
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

/**
 * Backend API-respons op heartbeat.
 */
@JsonClass(generateAdapter = true)
data class HeartbeatResponse(
    @Json(name = "ok") val ok: Boolean,
    @Json(name = "message") val message: String? = null
)

/**
 * Retrofit service-interface voor EmuFlow backend.
 *
 * Endpoints:
 * - POST /devices/heartbeat — verstuur heartbeat met hardware-info en save-stats
 *
 * Backend-URL is geconfigureerd via BuildConfig.BACKEND_URL
 * (instelbaar via gradle.properties of CI-parameter).
 */
interface BackendApiService {

    /**
     * Verstuur heartbeat naar backend.
     *
     * In fase 1: deze methode wordt NIET aangeroepen — HeartbeatService logt alleen.
     * Implementatie-PR zal de echte HTTP-call activeren.
     */
    @POST("/devices/heartbeat")
    suspend fun sendHeartbeat(@Body payload: HeartbeatPayload): Response<HeartbeatResponse>
}

/**
 * Factory/singleton voor de Retrofit-instantie.
 *
 * Gebruik:
 * ```kotlin
 * val api = BackendApi.service
 * val response = api.sendHeartbeat(payload)
 * ```
 */
object BackendApi {

    /**
     * Geconfigureerde Retrofit service.
     * Lazy-geïnitialiseerd zodat de app niet faalt als netwerk niet beschikbaar is.
     */
    val service: BackendApiService by lazy { createService() }

    private fun createService(): BackendApiService {
        val moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            // Alleen headers loggen in debug — body bevat device-ID (privacy)
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.HEADERS
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(BuildConfig.BACKEND_URL)
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(BackendApiService::class.java)
    }
}
