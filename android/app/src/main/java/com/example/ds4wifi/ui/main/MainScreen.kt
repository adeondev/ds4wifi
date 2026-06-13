package com.example.ds4wifi.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.ds4wifi.NetworkManager
import org.json.JSONObject

@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: MainScreenViewModel = viewModel(),
) {
    val connectionState by viewModel.connectionState.collectAsStateWithLifecycle()
    val controllerName by viewModel.controllerName.collectAsStateWithLifecycle()
    val batteryLevel by viewModel.batteryLevel.collectAsStateWithLifecycle()
    val lastPacket by viewModel.lastPacket.collectAsStateWithLifecycle()

    var host by remember { mutableStateOf("127.0.0.1") }
    var portString by remember { mutableStateOf("12345") }

    // PowerShell / classic blue terminal colors
    val darkBackground = Color(0xFF012456)
    val accentBlue = Color(0xFF00D2FF)
    val warningRed = Color(0xFFEF4444)
    val textPrimary = Color(0xFFFFFFFF)
    val textSecondary = Color(0xFF8AB4F8)

    val terminalFont = FontFamily.Monospace
    val scrollState = rememberScrollState()

    val batteryText = batteryLevel?.let { "$it%" } ?: "N/A"

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(darkBackground)
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth()
        ) {
            // Status Header
            Text(
                text = """
                    PS C:\DS4Wifi> ./status
                    =======================================
                    DS4WIFI MOBILE SYSTEM v1.0
                    =======================================
                    CONTROLE : $controllerName
                    BATERIA  : $batteryText
                    STATUS   : ${
                        when (connectionState) {
                            is NetworkManager.ConnectionState.Connected -> "CONECTADO AO PC"
                            is NetworkManager.ConnectionState.Connecting -> "CONECTANDO..."
                            is NetworkManager.ConnectionState.Error -> "ERRO DE CONEXAO"
                            else -> "DESCONECTADO"
                        }
                    }
                    =======================================
                """.trimIndent(),
                fontFamily = terminalFont,
                color = textPrimary,
                fontSize = 12.sp,
                lineHeight = 16.sp,
                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
            )

            // Config Prompt
            Text(
                text = "PS C:\\DS4Wifi> ./config",
                fontFamily = terminalFont,
                color = textSecondary,
                fontSize = 12.sp,
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
            )

            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
            ) {
                Text("IP ALVO : [ ", fontFamily = terminalFont, color = textPrimary, fontSize = 14.sp)
                BasicTextField(
                    value = host,
                    onValueChange = { host = it },
                    textStyle = androidx.compose.ui.text.TextStyle(fontFamily = terminalFont, color = accentBlue, fontSize = 14.sp),
                    cursorBrush = androidx.compose.ui.graphics.SolidColor(accentBlue),
                    modifier = Modifier.weight(1f),
                    enabled = connectionState is NetworkManager.ConnectionState.Disconnected || connectionState is NetworkManager.ConnectionState.Error
                )
                Text(" ]", fontFamily = terminalFont, color = textPrimary, fontSize = 14.sp)
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
            ) {
                Text("PORTA   : [ ", fontFamily = terminalFont, color = textPrimary, fontSize = 14.sp)
                BasicTextField(
                    value = portString,
                    onValueChange = { portString = it },
                    textStyle = androidx.compose.ui.text.TextStyle(fontFamily = terminalFont, color = accentBlue, fontSize = 14.sp),
                    cursorBrush = androidx.compose.ui.graphics.SolidColor(accentBlue),
                    modifier = Modifier.weight(1f),
                    enabled = connectionState is NetworkManager.ConnectionState.Disconnected || connectionState is NetworkManager.ConnectionState.Error
                )
                Text(" ]", fontFamily = terminalFont, color = textPrimary, fontSize = 14.sp)
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Connection Action
            Text(
                text = "PS C:\\DS4Wifi> ./connect",
                fontFamily = terminalFont,
                color = textSecondary,
                fontSize = 12.sp,
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
            )

            Button(
                onClick = {
                    if (connectionState is NetworkManager.ConnectionState.Connected || connectionState is NetworkManager.ConnectionState.Connecting) {
                        viewModel.disconnect()
                    } else {
                        val portVal = portString.toIntOrNull() ?: 12345
                        viewModel.connect(host, portVal)
                    }
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Transparent,
                    contentColor = if (connectionState is NetworkManager.ConnectionState.Connected) warningRed else accentBlue
                ),
                shape = androidx.compose.ui.graphics.RectangleShape,
                border = androidx.compose.foundation.BorderStroke(1.dp, if (connectionState is NetworkManager.ConnectionState.Connected) warningRed else accentBlue),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(45.dp)
            ) {
                Text(
                    text = if (connectionState is NetworkManager.ConnectionState.Connected || connectionState is NetworkManager.ConnectionState.Connecting) "> DESCONECTAR" else "> CONECTAR",
                    fontSize = 14.sp,
                    fontFamily = terminalFont,
                    fontWeight = FontWeight.Bold,
                )
            }

            if (connectionState is NetworkManager.ConnectionState.Error) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = ">>> ERRO: ${(connectionState as NetworkManager.ConnectionState.Error).message}",
                    color = warningRed,
                    fontFamily = terminalFont,
                    fontSize = 12.sp,
                    modifier = Modifier.fillMaxWidth()
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Telemetry Prompt
            Text(
                text = "PS C:\\DS4Wifi> ./telemetry --live",
                fontFamily = terminalFont,
                color = textSecondary,
                fontSize = 12.sp,
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
            )

            val json = remember(lastPacket) {
                try {
                    JSONObject(lastPacket)
                } catch (e: Exception) {
                    null
                }
            }

            if (json != null) {
                val lx = json.optDouble("lx", 0.0)
                val ly = json.optDouble("ly", 0.0)
                val rx = json.optDouble("rx", 0.0)
                val ry = json.optDouble("ry", 0.0)
                val lt = json.optDouble("lt", 0.0)
                val rt = json.optDouble("rt", 0.0)
                val dpadX = json.optInt("dpad_x", 0)
                val dpadY = json.optInt("dpad_y", 0)

                val pressedButtons = remember(json) {
                    val list = mutableListOf<String>()
                    val keys = listOf("cross", "circle", "square", "triangle", "l1", "r1", "l2_btn", "r2_btn", "share", "options", "ps", "l3", "r3")
                    for (k in keys) {
                        if (json.optBoolean(k, false)) {
                            list.add(k.uppercase())
                        }
                    }
                    if (dpadX != 0 || dpadY != 0) {
                        list.add("DPAD(${dpadX},${dpadY})")
                    }
                    list
                }

                Text(
                    text = """
                        [TELEMETRIA AO VIVO]
                        STICKS : L(x=%+.2f, y=%+.2f) | R(x=%+.2f, y=%+.2f)
                        TRIGS  : L2: %.2f | R2: %.2f
                        BOTOES : ${if (pressedButtons.isEmpty()) "NENHUM" else pressedButtons.joinToString(" ")}
                        PACOTE : ${lastPacket.trim()}
                    """.trimIndent().format(lx, ly, rx, ry, lt, rt),
                    fontFamily = terminalFont,
                    color = textPrimary,
                    fontSize = 11.sp,
                    lineHeight = 16.sp,
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, textSecondary.copy(alpha = 0.5f))
                        .padding(12.dp)
                )
            } else {
                Text(
                    text = "Aguardando conexao ou sinal do controle...",
                    fontFamily = terminalFont,
                    color = textSecondary.copy(alpha = 0.6f),
                    fontSize = 11.sp,
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, textSecondary.copy(alpha = 0.3f))
                        .padding(12.dp)
                )
            }
        }
    }
}
