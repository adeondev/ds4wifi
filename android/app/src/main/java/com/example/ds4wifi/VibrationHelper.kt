package com.example.ds4wifi

import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.InputDevice

object VibrationHelper {
    private var gamepadDeviceId: Int = -1

    fun setGamepadDeviceId(id: Int) {
        gamepadDeviceId = id
    }

    fun triggerVibration(large: Int, small: Int) {
        if (gamepadDeviceId == -1) return
        val device = InputDevice.getDevice(gamepadDeviceId) ?: return
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = device.vibratorManager
            val vibratorIds = vibratorManager.vibratorIds
            
            if (vibratorIds.isNotEmpty()) {
                // Motor Esquerdo (Lado Forte / Motor Grande)
                val leftVib = vibratorManager.getVibrator(vibratorIds[0])
                if (large > 0) {
                    val amp = large.coerceIn(1, 255)
                    leftVib.vibrate(VibrationEffect.createOneShot(150, amp))
                } else {
                    leftVib.cancel()
                }
                
                // Motor Direito (Lado Fraco / Motor Pequeno)
                if (vibratorIds.size > 1) {
                    val rightVib = vibratorManager.getVibrator(vibratorIds[1])
                    if (small > 0) {
                        val amp = small.coerceIn(1, 255)
                        rightVib.vibrate(VibrationEffect.createOneShot(150, amp))
                    } else {
                        rightVib.cancel()
                    }
                }
            } else {
                // Fallback para dispositivos que não separam os motores
                fallbackVibrate(device.vibrator, large, small)
            }
        } else {
            // Fallback para versões anteriores ao Android 12
            fallbackVibrate(device.vibrator, large, small)
        }
    }

    private fun fallbackVibrate(vibrator: Vibrator, large: Int, small: Int) {
        val maxVal = maxOf(large, small)
        if (maxVal == 0) {
            vibrator.cancel()
        } else {
            val amplitude = maxVal.coerceIn(1, 255)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(150, amplitude))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(150)
            }
        }
    }
}
