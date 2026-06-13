package com.example.ds4wifi

import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent

class GamepadState {
    var cross: Boolean = false
    var circle: Boolean = false
    var square: Boolean = false
    var triangle: Boolean = false
    var l1: Boolean = false
    var r1: Boolean = false
    var l2Btn: Boolean = false
    var r2Btn: Boolean = false
    var share: Boolean = false
    var options: Boolean = false
    var ps: Boolean = false
    var l3: Boolean = false
    var r3: Boolean = false
    
    var lx: Float = 0.0f
    var ly: Float = 0.0f
    var rx: Float = 0.0f
    var ry: Float = 0.0f
    
    var lt: Float = 0.0f
    var rt: Float = 0.0f
    
    var dpadX: Int = 0
    var dpadY: Int = 0
    var battery: Int = -1

    fun updateKey(keyCode: Int, isPressed: Boolean): Boolean {
        var handled = true
        when (keyCode) {
            KeyEvent.KEYCODE_BUTTON_A -> cross = isPressed
            KeyEvent.KEYCODE_BUTTON_B -> circle = isPressed
            KeyEvent.KEYCODE_BUTTON_X -> square = isPressed
            KeyEvent.KEYCODE_BUTTON_Y -> triangle = isPressed
            KeyEvent.KEYCODE_BUTTON_L1 -> l1 = isPressed
            KeyEvent.KEYCODE_BUTTON_R1 -> r1 = isPressed
            KeyEvent.KEYCODE_BUTTON_L2 -> l2Btn = isPressed
            KeyEvent.KEYCODE_BUTTON_R2 -> r2Btn = isPressed
            KeyEvent.KEYCODE_BUTTON_SELECT -> share = isPressed
            KeyEvent.KEYCODE_BUTTON_START -> options = isPressed
            KeyEvent.KEYCODE_BUTTON_MODE -> ps = isPressed
            KeyEvent.KEYCODE_BUTTON_THUMBL -> l3 = isPressed
            KeyEvent.KEYCODE_BUTTON_THUMBR -> r3 = isPressed
            KeyEvent.KEYCODE_DPAD_UP -> if (isPressed) dpadY = -1 else if (dpadY == -1) dpadY = 0
            KeyEvent.KEYCODE_DPAD_DOWN -> if (isPressed) dpadY = 1 else if (dpadY == 1) dpadY = 0
            KeyEvent.KEYCODE_DPAD_LEFT -> if (isPressed) dpadX = -1 else if (dpadX == -1) dpadX = 0
            KeyEvent.KEYCODE_DPAD_RIGHT -> if (isPressed) dpadX = 1 else if (dpadX == 1) dpadX = 0
            else -> handled = false
        }
        return handled
    }

    fun updateMotion(event: MotionEvent): Boolean {
        if (event.source and InputDevice.SOURCE_JOYSTICK == InputDevice.SOURCE_JOYSTICK &&
            event.action == MotionEvent.ACTION_MOVE
        ) {
            lx = event.getAxisValue(MotionEvent.AXIS_X)
            ly = event.getAxisValue(MotionEvent.AXIS_Y)
            rx = event.getAxisValue(MotionEvent.AXIS_Z)
            ry = event.getAxisValue(MotionEvent.AXIS_RZ)
            
            val l2AxisVal = event.getAxisValue(MotionEvent.AXIS_BRAKE)
            lt = if (l2AxisVal != 0.0f) l2AxisVal else event.getAxisValue(MotionEvent.AXIS_LTRIGGER)
            
            val r2AxisVal = event.getAxisValue(MotionEvent.AXIS_GAS)
            rt = if (r2AxisVal != 0.0f) r2AxisVal else event.getAxisValue(MotionEvent.AXIS_RTRIGGER)

            val hatX = event.getAxisValue(MotionEvent.AXIS_HAT_X)
            val hatY = event.getAxisValue(MotionEvent.AXIS_HAT_Y)
            
            if (hatX != 0.0f || hatY != 0.0f) {
                dpadX = hatX.toInt()
                dpadY = hatY.toInt()
            } else {
                dpadX = 0
                dpadY = 0
            }
            return true
        }
        return false
    }

    fun toJsonString(): String {
        return "{" +
                "\"cross\":$cross," +
                "\"circle\":$circle," +
                "\"square\":$square," +
                "\"triangle\":$triangle," +
                "\"l1\":$l1," +
                "\"r1\":$r1," +
                "\"l2_btn\":$l2Btn," +
                "\"r2_btn\":$r2Btn," +
                "\"share\":$share," +
                "\"options\":$options," +
                "\"ps\":$ps," +
                "\"l3\":$l3," +
                "\"r3\":$r3," +
                "\"lx\":$lx," +
                "\"ly\":$ly," +
                "\"rx\":$rx," +
                "\"ry\":$ry," +
                "\"lt\":$lt," +
                "\"rt\":$rt," +
                "\"dpad_x\":$dpadX," +
                "\"dpad_y\":$dpadY," +
                "\"battery\":$battery" +
                "}\n"
    }
}
