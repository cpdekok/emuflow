package com.emuflow.agent.telemetry

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.emuflow.agent.BuildConfig
import com.emuflow.agent.R
import com.emuflow.agent.hardware.detectHardwareProfile
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.time.Instant

private const val TAG = "HeartbeatService"
private const val NOTIFICATION_CHANNEL_ID = "emuflow_heartbeat"
private const val NOTIFICATION_ID = 1001
private const val HEARTBEAT_INTERVAL_MS = 60_000L // 60 seconden

/**
 * HeartbeatService — foreground service die periodiek telemetrie-data stuurt.
 *
 * Fase 1 STUB: De service logt het heartbeat-payload maar verstuurt het NIET.
 * Activeer de echte HTTP-call in BackendApi.service.sendHeartbeat() in een latere PR.
 *
 * Permissie-afhandeling per SDK-versie (doc taak):
 * - FOREGROUND_SERVICE: basis (alle versies)
 * - FOREGROUND_SERVICE_DATA_SYNC: vereist API 34+
 * - POST_NOTIFICATIONS: runtime-request vereist op API 33+
 *
 * Start: via startForegroundService() vanuit MainActivity of EmuFlowApplication
 * Stop: via stopService() of interne logica
 */
class HeartbeatService : Service() {

    private val serviceJob = SupervisorJob()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)
    private var heartbeatJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "HeartbeatService gestart")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())
        startHeartbeatLoop()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY // Herstart service als Android hem beëindigt
    }

    override fun onBind(intent: Intent?): IBinder? = null // Niet bindable

    override fun onDestroy() {
        super.onDestroy()
        heartbeatJob?.cancel()
        serviceJob.cancel()
        Log.i(TAG, "HeartbeatService gestopt")
    }

    /**
     * Heartbeat-lus: elke 60 seconden een payload bouwen en loggen.
     *
     * STUB: vervang Log.i() door BackendApi.service.sendHeartbeat() in implementatie-PR.
     */
    private fun startHeartbeatLoop() {
        heartbeatJob = serviceScope.launch {
            while (true) {
                try {
                    val payload = buildHeartbeatPayload()
                    // STUB: Alleen loggen, geen echte HTTP-call
                    Log.i(TAG, "Heartbeat [STUB, niet verstuurd]: device=${payload.hardware.model}, " +
                        "api=${payload.hardware.androidApi}, " +
                        "sticks=${payload.hardware.hasAnalogSticks}")

                    // TODO(implementatie-PR): Activeer wanneer backend-endpoint live is
                    // val response = BackendApi.service.sendHeartbeat(payload)
                    // if (!response.isSuccessful) {
                    //     Log.w(TAG, "Heartbeat mislukt: ${response.code()}")
                    // }
                } catch (e: Exception) {
                    Log.e(TAG, "Heartbeat-fout: ${e.message}")
                }

                delay(HEARTBEAT_INTERVAL_MS)
            }
        }
    }

    /**
     * Bouwt het heartbeat-payload op basis van actuele hardware-detectie.
     */
    private fun buildHeartbeatPayload(): HeartbeatPayload {
        val hardwareProfile = detectHardwareProfile(applicationContext)
        val deviceId = DeviceIdManager.getOrCreateDeviceId(applicationContext)

        return HeartbeatPayload(
            deviceId = deviceId,
            agentVersion = BuildConfig.AGENT_VERSION,
            timestampIso = Instant.now().toString(),
            hardware = HardwarePayload.from(hardwareProfile),
            saveEvents24h = null, // TODO(implementatie-PR): koppelen aan VaultManager statistieken
            ayaneoQuirks = null   // TODO(implementatie-PR): detectie van AYANEO USB-quirk
        )
    }

    /**
     * Maakt het notificatiekanaal aan voor Android 8+ (API 26+).
     */
    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            NOTIFICATION_CHANNEL_ID,
            "EmuFlow Agent",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "EmuFlow achtergrondservice voor telemetrie en save-backup"
            setShowBadge(false)
        }
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.createNotificationChannel(channel)
    }

    /**
     * Bouwt de persistent notificatie voor de foreground service.
     */
    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("EmuFlow Agent actief")
            .setContentText("Save-backup en telemetrie actief")
            .setSmallIcon(android.R.drawable.ic_dialog_info) // Vervangen door eigen icon in fase 2
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }

    companion object {
        /**
         * Start de HeartbeatService als foreground service.
         *
         * Conditionele permissie: op API 34+ is FOREGROUND_SERVICE_DATA_SYNC vereist.
         * Op eerdere versies is alleen FOREGROUND_SERVICE nodig.
         */
        fun start(context: Context) {
            val intent = Intent(context, HeartbeatService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
            Log.i(TAG, "HeartbeatService gestart via start()")
        }

        /**
         * Stop de HeartbeatService.
         */
        fun stop(context: Context) {
            context.stopService(Intent(context, HeartbeatService::class.java))
            Log.i(TAG, "HeartbeatService gestopt via stop()")
        }
    }
}
