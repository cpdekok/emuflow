package com.emuflow.agent.hardware

import android.app.ActivityManager
import android.content.Context
import android.hardware.input.InputManager
import android.os.Build
import android.util.DisplayMetrics
import android.util.Log
import android.view.InputDevice
import android.view.MotionEvent
import android.view.WindowManager
import com.emuflow.agent.shizuku.ShizukuManager

private const val TAG = "HardwareProfileDetector"

/**
 * Detecteert het hardware-profiel van het huidige device.
 *
 * Bouwt een [HardwareProfile] op basis van Android system APIs:
 * - Build.* properties voor manufacturer, model, SoC-info
 * - ActivityManager voor RAM
 * - InputDevice voor controller-detectie
 * - Display metrics voor schermresolutie
 *
 * Stub-opmerkingen:
 * - gpuFamily detectie via OpenGL-ES is alleen mogelijk met een actieve GL-context.
 *   In fase 1 detecteren we dit via Build.HARDWARE heuristiek als fallback.
 * - pageSize via Os.sysconf(OsConstants._SC_PAGESIZE) vereist android.system.Os import;
 *   hier als stub met System.getProperty fallback.
 *
 * @param context Android Context
 * @return Volledig ingevuld [HardwareProfile]
 */
fun detectHardwareProfile(context: Context): HardwareProfile {
    Log.d(TAG, "Start hardware-profiel detectie voor ${Build.MANUFACTURER} ${Build.MODEL}")

    val socVendor = detectSocVendor()
    val socChip = detectSocChip()
    val gpuFamily = detectGpuFamily()
    val pageSize = detectPageSize()
    val ramMb = detectRamMb(context)
    val (displayWidth, displayHeight, displayDensity) = detectDisplay(context)
    val controllerInfo = detectControllerInfo()
    val vendorPackages = detectVendorShellPackages(context)
    val shizukuAvailable = ShizukuManager.isAvailable()
    val shizukuVersion = ShizukuManager.getVersion()
    val isRooted = detectRooted()

    val profile = HardwareProfile(
        manufacturer = Build.MANUFACTURER ?: "unknown",
        model = Build.MODEL ?: "unknown",
        androidRelease = Build.VERSION.RELEASE ?: "unknown",
        androidApi = Build.VERSION.SDK_INT,
        socVendor = socVendor,
        socChip = socChip,
        gpuFamily = gpuFamily,
        pageSize = pageSize,
        ramMb = ramMb,
        displayWidth = displayWidth,
        displayHeight = displayHeight,
        displayDensity = displayDensity,
        hasAnalogSticks = controllerInfo.hasAnalogSticks,
        hasAnalogTriggers = controllerInfo.hasAnalogTriggers,
        controllerLayout = controllerInfo.layout,
        internalGamepadVidPid = controllerInfo.vidPid,
        vendorShellPackages = vendorPackages,
        isShizukuAvailable = shizukuAvailable,
        shizukuVersion = shizukuVersion,
        isRooted = isRooted
    )

    Log.i(TAG, "Hardware-profiel gedetecteerd: mfr=${profile.manufacturer}, model=${profile.model}, " +
        "soc=${profile.socVendor}/${profile.socChip}, gpu=${profile.gpuFamily}, " +
        "sticks=${profile.hasAnalogSticks}, layout=${profile.controllerLayout}")

    return profile
}

/**
 * Detecteert SoC-vendor via Build.SOC_MANUFACTURER (API 31+) of heuristiek op Build.HARDWARE.
 *
 * Heuristiek op basis van doc 13:
 * - "qcom" / "sdm" / "sm" → qualcomm
 * - "mt" → mediatek
 * - "exynos" / "s5" → samsung
 * - "kirin" / "hi" → hisilicon
 * - "rk" → rockchip
 * - "sun" → allwinner
 */
private fun detectSocVendor(): String {
    // API 31+ — directe methode
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        val socMfr = Build.SOC_MANUFACTURER.lowercase()
        return when {
            socMfr.contains("qualcomm") -> SocVendor.QUALCOMM
            socMfr.contains("mediatek") || socMfr.contains("mtk") -> SocVendor.MEDIATEK
            socMfr.contains("samsung") -> SocVendor.SAMSUNG
            socMfr.contains("hisilicon") -> SocVendor.HISILICON
            socMfr.contains("rockchip") -> SocVendor.ROCKCHIP
            socMfr.contains("allwinner") -> SocVendor.ALLWINNER
            socMfr != Build.UNKNOWN.lowercase() -> socMfr
            else -> detectSocVendorFromHardware()
        }
    }
    return detectSocVendorFromHardware()
}

private fun detectSocVendorFromHardware(): String {
    val hw = Build.HARDWARE.lowercase()
    return when {
        hw.startsWith("qcom") || hw.startsWith("sdm") || hw.startsWith("sm") -> SocVendor.QUALCOMM
        hw.startsWith("mt") -> SocVendor.MEDIATEK
        hw.startsWith("exynos") || hw.startsWith("s5") -> SocVendor.SAMSUNG
        hw.startsWith("kirin") || hw.startsWith("hi") -> SocVendor.HISILICON
        hw.startsWith("rk") -> SocVendor.ROCKCHIP
        hw.startsWith("sun") -> SocVendor.ALLWINNER
        else -> SocVendor.UNKNOWN
    }
}

/**
 * Detecteert SoC-chip-naam via Build.SOC_MODEL (API 31+) of Build.HARDWARE heuristiek.
 */
private fun detectSocChip(): String {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        val socModel = Build.SOC_MODEL
        if (socModel.isNotBlank() && socModel != Build.UNKNOWN) {
            return socModel
        }
    }
    // Fallback: gebruik Build.HARDWARE als benadering
    return Build.HARDWARE.ifBlank { "unknown" }
}

/**
 * Detecteert GPU-familie via heuristiek op SoC-vendor.
 *
 * Directe OpenGL-ES-context detectie (via glGetString) vereist een actieve GL-context
 * die we hier niet hebben. In fase 1 leiden we de GPU-familie af uit de SoC-vendor
 * als pragmatische benadering (Snapdragon = Adreno, MediaTek = Mali in de meeste gevallen).
 *
 * Implementatie-notitie: in fase 2 kan een GLSurfaceView.Renderer worden gebruikt
 * om glGetString(GL10.GL_RENDERER) op te halen voor exacte detectie.
 */
private fun detectGpuFamily(): String {
    // Probeer via Build.HARDWARE product-string te detecteren
    val hardware = Build.HARDWARE.lowercase()
    val product = Build.PRODUCT.lowercase()

    return when {
        hardware.contains("adreno") || product.contains("adreno") -> GpuFamily.ADRENO
        hardware.contains("mali") || product.contains("mali") -> GpuFamily.MALI
        hardware.contains("powervr") -> GpuFamily.POWERVR
        // Fallback op SoC-vendor heuristiek (doc 13: Snapdragon→Adreno, MediaTek→Mali)
        else -> when (detectSocVendor()) {
            SocVendor.QUALCOMM -> GpuFamily.ADRENO
            SocVendor.MEDIATEK, SocVendor.SAMSUNG -> GpuFamily.MALI
            else -> GpuFamily.UNKNOWN
        }
    }
}

/**
 * Detecteert geheugen-paginagrootte.
 *
 * Op moderne SoCs (bijv. Snapdragon 8 Gen 3) kan dit 16384 zijn.
 * Op Snapdragon 865 en Helio G99 is dit typisch 4096.
 */
private fun detectPageSize(): Int {
    return try {
        // android.system.Os.sysconf(OsConstants._SC_PAGESIZE) vereist try/catch
        val osClass = Class.forName("android.system.Os")
        val sysconfMethod = osClass.getMethod("sysconf", Int::class.java)
        // OsConstants._SC_PAGESIZE = 39
        val result = sysconfMethod.invoke(null, 39) as? Long
        result?.toInt() ?: 4096
    } catch (e: Exception) {
        Log.d(TAG, "pageSize via Os.sysconf niet beschikbaar: ${e.message}")
        4096 // Veilige default
    }
}

/**
 * Detecteert totale RAM via ActivityManager.MemoryInfo.
 */
private fun detectRamMb(context: Context): Int {
    val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
    val memoryInfo = ActivityManager.MemoryInfo()
    activityManager.getMemoryInfo(memoryInfo)
    return (memoryInfo.totalMem / (1024 * 1024)).toInt()
}

/**
 * Detecteert schermresolutie en densiteit.
 * Returns Triple(width, height, density).
 */
@Suppress("DEPRECATION")
private fun detectDisplay(context: Context): Triple<Int, Int, Int> {
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val bounds = windowManager.currentWindowMetrics.bounds
        val displayMetrics = context.resources.displayMetrics
        Triple(bounds.width(), bounds.height(), displayMetrics.densityDpi)
    } else {
        val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val displayMetrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        windowManager.defaultDisplay.getRealMetrics(displayMetrics)
        Triple(displayMetrics.widthPixels, displayMetrics.heightPixels, displayMetrics.densityDpi)
    }
}

/**
 * Container voor controller-detectie resultaat.
 */
private data class ControllerDetectionResult(
    val hasAnalogSticks: Boolean,
    val hasAnalogTriggers: Boolean,
    val layout: String,
    val vidPid: String?
)

/**
 * Detecteert interne gamepad-eigenschappen via InputDevice API.
 *
 * Implementatie conform doc 13 sticks-detectie:
 * - Zoek InputDevice met SOURCE_GAMEPAD die niet extern is
 * - Controleer AXIS_X + AXIS_Y aanwezigheid voor analoge sticks
 * - Controleer AXIS_LTRIGGER / AXIS_RTRIGGER voor analoge triggers
 */
private fun detectControllerInfo(): ControllerDetectionResult {
    val ids: IntArray = InputDevice.getDeviceIds() ?: IntArray(0)
    var internalGamepad: InputDevice? = null
    for (id in ids) {
        val device: InputDevice = InputDevice.getDevice(id) ?: continue
        val src: Int = device.sources
        if ((src and InputDevice.SOURCE_GAMEPAD) != 0 && !device.isExternal) {
            internalGamepad = device
            break
        }
    }

    if (internalGamepad == null) {
        Log.d(TAG, "Geen interne gamepad gedetecteerd")
        return ControllerDetectionResult(
            hasAnalogSticks = false,
            hasAnalogTriggers = false,
            layout = ControllerLayout.NO_STICK,
            vidPid = null
        )
    }

    val hasAnalogSticks = internalGamepad.getMotionRange(MotionEvent.AXIS_X) != null
        && internalGamepad.getMotionRange(MotionEvent.AXIS_Y) != null
        && internalGamepad.getMotionRange(MotionEvent.AXIS_Z) != null
        && internalGamepad.getMotionRange(MotionEvent.AXIS_RZ) != null

    val hasAnalogTriggers = internalGamepad.getMotionRange(MotionEvent.AXIS_LTRIGGER) != null
        && internalGamepad.getMotionRange(MotionEvent.AXIS_RTRIGGER) != null

    val layout = when {
        hasAnalogSticks -> ControllerLayout.DUAL_STICK
        else -> ControllerLayout.NO_STICK
    }

    // VID:PID — beschikbaar via getVendorId() + getProductId()
    val vidPid = if (internalGamepad.vendorId != 0 && internalGamepad.productId != 0) {
        "%04x:%04x".format(internalGamepad.vendorId, internalGamepad.productId)
    } else {
        null
    }

    Log.d(TAG, "Gamepad: ${internalGamepad.name}, sticks=$hasAnalogSticks, triggers=$hasAnalogTriggers, vidpid=$vidPid")

    return ControllerDetectionResult(
        hasAnalogSticks = hasAnalogSticks,
        hasAnalogTriggers = hasAnalogTriggers,
        layout = layout,
        vidPid = vidPid
    )
}

/**
 * Detecteert geïnstalleerde vendor-shell packages.
 *
 * Lijsten uit doc 13 — scannen bij elke heartbeat.
 * Vereist QUERY_ALL_PACKAGES permissie (in manifest opgegeven).
 */
private fun detectVendorShellPackages(context: Context): List<String> {
    val knownVendorPackages = listOf(
        // Retroid
        "com.retroid.launcher",
        "com.retroid.console",
        // AYANEO
        "com.ayaneo.ayaspace",
        "com.ayaneo.master_controller",
        "com.ayaneo.gamemanager",
        "com.ayaneo.assistant",
        // AYN
        "com.ayn.console",
        // Anbernic
        "com.anbernic.launcher",
        // Game Players Direct
        "com.gpd.gamecenter"
    )

    val packageManager = context.packageManager
    return knownVendorPackages.filter { packageName ->
        try {
            packageManager.getPackageInfo(packageName, 0)
            true
        } catch (e: Exception) {
            false
        }
    }.also { found ->
        Log.d(TAG, "Vendor-packages gevonden: $found")
    }
}

/**
 * Eenvoudige root-detectie via su-binary aanwezigheid.
 *
 * Let op: dit is niet volledig betrouwbaar. Root-verbergende frameworks
 * (Magisk met Zygisk) kunnen su onzichtbaar maken voor apps.
 * In fase 1 voldoende als informatieve flag.
 */
private fun detectRooted(): Boolean {
    val suPaths = listOf(
        "/system/bin/su",
        "/system/xbin/su",
        "/sbin/su",
        "/data/local/su",
        "/data/local/bin/su"
    )
    return suPaths.any { java.io.File(it).exists() }
}
