package com.emuflow.agent

import android.app.Application
import android.util.Log
import com.emuflow.agent.shizuku.ShizukuManager
import com.emuflow.agent.telemetry.DeviceIdManager

/**
 * EmuFlow Application-klasse.
 *
 * Initialiseer hier singleton-componenten die de volledige app-lifecycle nodig hebben.
 * Houd het licht — zware initialisatie gebeurt lazy of in coroutines.
 */
class EmuFlowApplication : Application() {

    companion object {
        private const val TAG = "EmuFlowApplication"
        lateinit var instance: EmuFlowApplication
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        Log.i(TAG, "EmuFlow Agent gestart — versie ${BuildConfig.AGENT_VERSION}")

        // Initialiseer Shizuku-binding zodra de app start
        // Shizuku is optioneel — als het niet beschikbaar is, werken features met fallback
        ShizukuManager.init(this)

        // Zorg dat device-ID bestaat bij eerste start
        val deviceId = DeviceIdManager.getOrCreateDeviceId(this)
        Log.i(TAG, "Device-ID: $deviceId")
    }

    override fun onTerminate() {
        super.onTerminate()
        ShizukuManager.release()
    }
}
