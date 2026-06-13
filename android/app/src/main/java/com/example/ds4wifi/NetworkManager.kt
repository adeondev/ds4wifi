package com.example.ds4wifi

import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket

object NetworkManager {
    private const val TAG = "NetworkManager"
    private var socket: Socket? = null
    private var outputStream: OutputStream? = null
    
    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState

    private val scope = CoroutineScope(Dispatchers.IO)
    
    // High performance channel for sequential packet queue
    private val sendChannel = Channel<String>(Channel.UNLIMITED)

    private var lastHost: String = "127.0.0.1"
    private var lastPort: Int = 12345
    private var isReconnecting = false
    private var autoConnectEnabled = true

    sealed class ConnectionState {
        object Disconnected : ConnectionState()
        object Connecting : ConnectionState()
        object Connected : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }

    init {
        startSenderLoop()
    }

    fun connect(host: String, port: Int) {
        lastHost = host
        lastPort = port
        autoConnectEnabled = true
        connectInternal()
    }

    private fun connectInternal() {
        scope.launch {
            _connectionState.value = ConnectionState.Connecting
            try {
                disconnectInternal() // Clear old connections
                val newSocket = Socket()
                newSocket.tcpNoDelay = true
                newSocket.connect(InetSocketAddress(lastHost, lastPort), 2000)
                socket = newSocket
                outputStream = newSocket.getOutputStream()
                _connectionState.value = ConnectionState.Connected
                Log.d(TAG, "Connected to $lastHost:$lastPort")
                startReader(newSocket)
            } catch (e: Exception) {
                Log.e(TAG, "Connection failed", e)
                _connectionState.value = ConnectionState.Error(e.message ?: "Unknown error")
                disconnectInternal()
                triggerReconnection()
            }
        }
    }

    fun disconnect() {
        autoConnectEnabled = false // Disable reconnect on explicit user disconnect
        scope.launch {
            disconnectInternal()
        }
    }

    private fun disconnectInternal() {
        try {
            outputStream?.close()
            socket?.close()
        } catch (e: Exception) {
            Log.e(TAG, "Error closing socket", e)
        } finally {
            socket = null
            outputStream = null
            _connectionState.value = ConnectionState.Disconnected
            Log.d(TAG, "Disconnected")
        }
    }

    private fun triggerReconnection() {
        if (!autoConnectEnabled || isReconnecting) return
        isReconnecting = true
        scope.launch {
            delay(2000)
            isReconnecting = false
            if (autoConnectEnabled && _connectionState.value !is ConnectionState.Connected) {
                Log.d(TAG, "Attempting automatic reconnection...")
                connectInternal()
            }
        }
    }

    private fun startSenderLoop() {
        scope.launch(Dispatchers.IO) {
            for (msg in sendChannel) {
                if (_connectionState.value == ConnectionState.Connected) {
                    try {
                        outputStream?.write(msg.toByteArray())
                        outputStream?.flush()
                    } catch (e: Exception) {
                        Log.e(TAG, "Send failed in loop", e)
                        _connectionState.value = ConnectionState.Error("Connection lost: ${e.message}")
                        disconnectInternal()
                        triggerReconnection()
                    }
                }
            }
        }
    }

    fun sendState(json: String) {
        if (_connectionState.value != ConnectionState.Connected) return
        sendChannel.trySend(json)
    }

    private fun startReader(socket: Socket) {
        scope.launch(Dispatchers.IO) {
            try {
                val reader = socket.getInputStream().bufferedReader()
                var line: String? = null
                while (connectionState.value == ConnectionState.Connected && reader.readLine().also { line = it } != null) {
                    line?.let { parseServerMessage(it) }
                }
            } catch (e: Exception) {
                Log.d(TAG, "Reader loop terminated: ${e.message}")
            } finally {
                if (_connectionState.value == ConnectionState.Connected) {
                    _connectionState.value = ConnectionState.Error("Connection lost")
                    disconnectInternal()
                    triggerReconnection()
                }
            }
        }
    }

    private fun parseServerMessage(line: String) {
        try {
            val json = org.json.JSONObject(line)
            if (json.optString("type") == "rumble") {
                val large = json.optInt("large", 0)
                val small = json.optInt("small", 0)
                VibrationHelper.triggerVibration(large, small)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse server message", e)
        }
    }
}
