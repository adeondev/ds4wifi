package com.example.ds4wifi

import android.content.Context
import android.hardware.input.InputManager
import android.os.Bundle
import android.os.Vibrator
import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.ds4wifi.theme.DS4WifiTheme

class MainActivity : ComponentActivity(), InputManager.InputDeviceListener {
    private lateinit var inputManager: InputManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        inputManager = getSystemService(Context.INPUT_SERVICE) as InputManager
        inputManager.registerInputDeviceListener(this, null)
        updateConnectedControllers()

        // Auto-connect to PC on launch
        NetworkManager.connect("127.0.0.1", 12345)

        enableEdgeToEdge()
        setContent {
            DS4WifiTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    MainNavigation()
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        inputManager.unregisterInputDeviceListener(this)
        NetworkManager.disconnect()
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        // Intercept gamepad button key events
        val sources = event.source
        if ((sources and InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD ||
            (sources and InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK ||
            (sources and InputDevice.SOURCE_KEYBOARD) == InputDevice.SOURCE_KEYBOARD // Fallback: some replica controllers register as keyboard
        ) {
            updateBatteryFromEvent(event.deviceId)
            val isPressed = event.action == KeyEvent.ACTION_DOWN
            if (ControllerManager.gamepadState.updateKey(event.keyCode, isPressed)) {
                val json = ControllerManager.gamepadState.toJsonString()
                NetworkManager.sendState(json)
                ControllerManager.updatePacket()
                return true
            }
        }
        return super.dispatchKeyEvent(event)
    }

    override fun dispatchGenericMotionEvent(event: MotionEvent): Boolean {
        val sources = event.source
        if ((sources and InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK ||
            (sources and InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD
        ) {
            updateBatteryFromEvent(event.deviceId)
        }
        if (ControllerManager.gamepadState.updateMotion(event)) {
            val json = ControllerManager.gamepadState.toJsonString()
            NetworkManager.sendState(json)
            ControllerManager.updatePacket()
            return true
        }
        return super.dispatchGenericMotionEvent(event)
    }

    override fun onInputDeviceAdded(deviceId: Int) {
        updateConnectedControllers()
    }

    override fun onInputDeviceRemoved(deviceId: Int) {
        updateConnectedControllers()
    }

    override fun onInputDeviceChanged(deviceId: Int) {
        updateConnectedControllers()
    }

    private fun updateBatteryFromEvent(deviceId: Int) {
        var batteryLevel: Int = -1
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
            val device = InputDevice.getDevice(deviceId)
            if (device != null) {
                val capacity = device.batteryState.capacity
                if (!capacity.isNaN()) {
                    batteryLevel = (capacity * 100).toInt()
                }
            }
        }
        ControllerManager.setBatteryLevel(if (batteryLevel >= 0) batteryLevel else null)
        ControllerManager.gamepadState.battery = batteryLevel
    }

    private fun updateConnectedControllers() {
        val deviceIds = InputDevice.getDeviceIds()
        var foundController = "Nenhum controle detectado"
        var activeId = -1
        var batteryLevel: Int? = null
        for (id in deviceIds) {
            val device = InputDevice.getDevice(id) ?: continue
            val sources = device.sources
            if ((sources and InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD ||
                (sources and InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK
            ) {
                foundController = device.name
                activeId = id
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                    val capacity = device.batteryState.capacity
                    if (!capacity.isNaN()) {
                        batteryLevel = (capacity * 100).toInt()
                    }
                }
                break
            }
        }
        ControllerManager.setControllerName(foundController)
        ControllerManager.setBatteryLevel(batteryLevel)
        ControllerManager.gamepadState.battery = batteryLevel ?: -1
        VibrationHelper.setGamepadDeviceId(activeId)
    }
}
