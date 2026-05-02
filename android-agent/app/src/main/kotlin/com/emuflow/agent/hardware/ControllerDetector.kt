package com.emuflow.agent.hardware

import android.util.Log
import android.view.InputDevice
import android.view.MotionEvent

private const val TAG = "ControllerDetector"

/**
 * Gedetailleerde informatie over een gedetecteerde gamepad/controller.
 */
data class ControllerInfo(
    val deviceId: Int,
    val deviceName: String,
    val isInternal: Boolean,
    val hasAnalogSticks: Boolean,
    val hasLeftStick: Boolean,
    val hasRightStick: Boolean,
    val hasAnalogTriggers: Boolean,
    val hasL3R3: Boolean,
    val vendorId: Int,
    val productId: Int,
    val vidPidString: String?
)

/**
 * Detecteert alle beschikbare controllers (intern en extern).
 *
 * Uitbreiding op de detectie in [HardwareProfileDetector] — geeft
 * meer gedetailleerde informatie per controller.
 *
 * Gebruik:
 * - Scherm-layout bepalen (dual_stick / no_stick)
 * - Valideren of interne controller actief is (AYANEO USB-quirk)
 * - VID:PID loggen voor telemetrie
 */
object ControllerDetector {

    /**
     * Detecteert de interne gamepad van het device.
     *
     * Intern = niet verbonden via Bluetooth of USB (isExternal == false).
     * Op AYANEO Pocket Micro Classic: interne controller kan tijdelijk uitgeschakeld zijn
     * vanwege gedeelde USB-data-lines (quirk 1 uit doc 14).
     *
     * @return [ControllerInfo] of null als geen interne gamepad gevonden
     */
    fun detectInternalGamepad(): ControllerInfo? {
        val allDevices: List<InputDevice> = collectInputDevices()

        val gamepadDevices: List<InputDevice> = allDevices.filter { device ->
            val src: Int = device.sources
            (src and InputDevice.SOURCE_GAMEPAD) != 0 ||
                (src and InputDevice.SOURCE_JOYSTICK) != 0
        }

        Log.d(TAG, "Gevonden input-devices: ${gamepadDevices.map { it.name }}")

        val internalGamepad: InputDevice = gamepadDevices.firstOrNull { !it.isExternal }
            ?: run {
                Log.w(TAG, "Geen interne gamepad gevonden — mogelijk tijdelijk uitgeschakeld (AYANEO quirk)")
                return null
            }

        return buildControllerInfo(internalGamepad, isInternal = true)
    }

    /**
     * Verzamelt alle [InputDevice]-instanties expliciet zodat overload-resolutie
     * niet faalt op de [IntArray] return-type van [InputDevice.getDeviceIds].
     */
    private fun collectInputDevices(): List<InputDevice> {
        val ids: IntArray = InputDevice.getDeviceIds() ?: return emptyList()
        val result = ArrayList<InputDevice>(ids.size)
        for (id in ids) {
            val device: InputDevice? = InputDevice.getDevice(id)
            if (device != null) result.add(device)
        }
        return result
    }

    /**
     * Detecteert alle extern verbonden controllers (BT, USB).
     *
     * @return Lijst van gedetecteerde externe controllers
     */
    fun detectExternalControllers(): List<ControllerInfo> {
        val externals: List<ControllerInfo> = collectInputDevices()
            .filter { device ->
                val src: Int = device.sources
                device.isExternal &&
                    ((src and InputDevice.SOURCE_GAMEPAD) != 0 ||
                        (src and InputDevice.SOURCE_JOYSTICK) != 0)
            }
            .map { buildControllerInfo(it, isInternal = false) }
        Log.d(TAG, "Externe controllers: ${externals.map { it.deviceName }}")
        return externals
    }

    /**
     * Bouwt [ControllerInfo] op basis van [InputDevice].
     */
    private fun buildControllerInfo(device: InputDevice, isInternal: Boolean): ControllerInfo {
        val hasLeftStick = device.getMotionRange(MotionEvent.AXIS_X) != null
            && device.getMotionRange(MotionEvent.AXIS_Y) != null
        val hasRightStick = device.getMotionRange(MotionEvent.AXIS_Z) != null
            && device.getMotionRange(MotionEvent.AXIS_RZ) != null
        val hasAnalogSticks = hasLeftStick && hasRightStick
        val hasAnalogTriggers = device.getMotionRange(MotionEvent.AXIS_LTRIGGER) != null
            && device.getMotionRange(MotionEvent.AXIS_RTRIGGER) != null
        // L3/R3 zijn knoppen, niet axes — check via hasKeys
        val hasL3R3 = device.hasKeys(
            android.view.KeyEvent.KEYCODE_BUTTON_THUMBL,
            android.view.KeyEvent.KEYCODE_BUTTON_THUMBR
        ).all { it }

        val vidPidString = if (device.vendorId != 0 && device.productId != 0) {
            "%04x:%04x".format(device.vendorId, device.productId)
        } else null

        return ControllerInfo(
            deviceId = device.id,
            deviceName = device.name ?: "unknown",
            isInternal = isInternal,
            hasAnalogSticks = hasAnalogSticks,
            hasLeftStick = hasLeftStick,
            hasRightStick = hasRightStick,
            hasAnalogTriggers = hasAnalogTriggers,
            hasL3R3 = hasL3R3,
            vendorId = device.vendorId,
            productId = device.productId,
            vidPidString = vidPidString
        )
    }

    /**
     * Bepaalt controller-layout op basis van gedetecteerde gamepad.
     *
     * @return Een van [ControllerLayout.DUAL_STICK], [ControllerLayout.NO_STICK],
     *         [ControllerLayout.SINGLE_STICK]
     */
    fun determineLayout(info: ControllerInfo?): String {
        if (info == null) return ControllerLayout.NO_STICK
        return when {
            info.hasLeftStick && info.hasRightStick -> ControllerLayout.DUAL_STICK
            info.hasLeftStick -> ControllerLayout.SINGLE_STICK
            else -> ControllerLayout.NO_STICK
        }
    }
}
