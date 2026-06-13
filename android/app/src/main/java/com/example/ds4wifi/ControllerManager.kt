package com.example.ds4wifi

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

object ControllerManager {
    val gamepadState = GamepadState()
    
    private val _controllerName = MutableStateFlow("Nenhum controle detectado")
    val controllerName: StateFlow<String> = _controllerName

    private val _batteryLevel = MutableStateFlow<Int?>(null)
    val batteryLevel: StateFlow<Int?> = _batteryLevel
    
    private val _lastPacket = MutableStateFlow("")
    val lastPacket: StateFlow<String> = _lastPacket

    fun setControllerName(name: String) {
        _controllerName.value = name
    }

    fun setBatteryLevel(level: Int?) {
        _batteryLevel.value = level
    }

    fun updatePacket() {
        _lastPacket.value = gamepadState.toJsonString()
    }
}
