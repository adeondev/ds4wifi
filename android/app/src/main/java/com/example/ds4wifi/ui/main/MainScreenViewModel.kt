package com.example.ds4wifi.ui.main

import androidx.lifecycle.ViewModel
import com.example.ds4wifi.ControllerManager
import com.example.ds4wifi.NetworkManager
import kotlinx.coroutines.flow.StateFlow

class MainScreenViewModel : ViewModel() {
    val connectionState: StateFlow<NetworkManager.ConnectionState> = NetworkManager.connectionState
    val controllerName: StateFlow<String> = ControllerManager.controllerName
    val batteryLevel: StateFlow<Int?> = ControllerManager.batteryLevel
    val lastPacket: StateFlow<String> = ControllerManager.lastPacket

    fun connect(host: String, port: Int) {
        NetworkManager.connect(host, port)
    }

    fun disconnect() {
        NetworkManager.disconnect()
    }
}
