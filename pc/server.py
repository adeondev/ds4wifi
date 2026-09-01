import socket
import json
import sys
import os
import subprocess
import threading
import time
import msvcrt
import vgamepad as vg

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.columns import Columns
from rich import box

# Configurações do Servidor
PORT = 12345
HOST = '0.0.0.0'

# Ativa processamento de cores ANSI e UTF-8 no terminal do Windows
if sys.platform == 'win32':
    os.system('')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

console = Console()

# ──────────────────────────────────────────────
#  Paleta de Cores DS4Wifi (usando Rich markup)
# ──────────────────────────────────────────────
# Gradient: deep blue → cyan → teal
GRAD = [
    "#6C63FF",  # Indigo/Purple
    "#5B86E5",  # Blue
    "#36D1DC",  # Cyan
    "#00C9A7",  # Teal
    "#00B4D8",  # Sky
    "#48CAE4",  # Light Blue
]

# Mapeamento de botões normais (Android -> vgamepad DS4)
BUTTON_MAP = {
    "cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
    "circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
    "square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
    "triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
    "l1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
    "r1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
    "l2_btn": vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT,
    "r2_btn": vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT,
    "share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
    "options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
    "l3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
    "r3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
}

SPECIAL_BUTTON_MAP = {
    "ps": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS
}

# Estado do Servidor e Controle
server_status = "disconnected"
adb_status = "not_run"
connected_device = "none"
client_ip = "---"

# Estado em tempo real do controle (guardado globalmente para o renderizador)
current_state = {
    "lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0,
    "lt": 0.0, "rt": 0.0, "dpad_x": 0, "dpad_y": 0,
    "cross": False, "circle": False, "square": False, "triangle": False,
    "l1": False, "r1": False, "l2_btn": False, "r2_btn": False,
    "share": False, "options": False, "ps": False, "l3": False, "r3": False,
    "battery": -1
}

current_conn = None
gamepad = None

# Mutex para proteger a leitura e escrita do estado do controle
state_lock = threading.Lock()

# ──────────────────────────────────────────────
#  Sistema de Idiomas / Language System
# ──────────────────────────────────────────────

current_lang = "en"

TRANSLATIONS = {
    "en": {
        # Language selector
        "lang_title": "Select Language",
        "lang_hint": "Up/Down = Navigate  |  Enter = Select",
        "lang_en": "English",
        "lang_pt": "Portugues",
        "lang_es": "Espanol",
        # Main menu
        "subtitle": "Wireless DualShock 4 Controller Emulator",
        "menu_select": "--- Select an option ---",
        "menu_start_title": ">> Start Full Server",
        "menu_start_desc": "Starts the server + ADB Reverse automatically",
        "menu_adb_title": ">> ADB Reverse Only",
        "menu_adb_desc": "Runs only the port forwarding",
        "menu_exit_title": ">> Exit",
        "menu_exit_desc": "Close the program",
        "menu_hint": "Up/Down = Navigate  |  Enter = Select  |  ESC = Exit",
        # Dashboard
        "dash_subtitle": "*  DS4Wifi Controller  -  Wireless DualShock 4 Emulator  *",
        "dash_status": ">> Status",
        "dash_port": ":: Port",
        "dash_device": "[] USB Device",
        "dash_adb": "<> ADB Reverse",
        "dash_ip": "-- Phone IP",
        "dash_battery": "%% Battery",
        "dash_shortcuts": "Shortcuts",
        "dash_shortcut_exit": "Ctrl+C = Exit",
        "dash_panel_status": "[ Connection & Status ]",
        "dash_panel_controller": "[ Controller Viewer ]",
        "dash_footer_exit": "Ctrl+C to exit",
        # Status values
        "status_disconnected": "Disconnected",
        "status_not_run": "Not executed",
        "status_none": "None",
        "status_waiting": "Waiting for Phone",
        "status_connected": "Phone Connected",
        "status_none_detected": "None detected",
        "status_port_redirect": "Port {port} redirected",
        "status_port_busy": "Error: port {port} busy",
        # Loading
        "loading_init_controller": "... Initializing virtual DualShock 4 controller",
        "loading_init_success": "[+] Virtual controller created successfully!",
        "loading_init_error": "[X] ERROR: Could not initialize virtual controller",
        "loading_init_hint": "Make sure ViGEmBus driver is installed and try again.",
        "loading_error_title": "Fatal Error",
        "loading_press_key": "Press any key to exit...",
        "loading_adb": "... Running ADB Reverse",
        "loading_result": "Result:",
        # Exit
        "exit_bye": "*  Goodbye!  *",
        "exit_server_bye": "*  Server stopped. Goodbye!  *",
    },
    "pt": {
        # Language selector
        "lang_title": "Selecione o Idioma",
        "lang_hint": "Cima/Baixo = Navegar  |  Enter = Selecionar",
        "lang_en": "English",
        "lang_pt": "Portugues",
        "lang_es": "Espanol",
        # Main menu
        "subtitle": "Emulador de Controle DualShock 4 sem Fio",
        "menu_select": "--- Selecione uma opcao ---",
        "menu_start_title": ">> Iniciar Servidor Completo",
        "menu_start_desc": "Inicia o servidor + ADB Reverse automaticamente",
        "menu_adb_title": ">> Apenas ADB Reverse",
        "menu_adb_desc": "Executa somente o redirecionamento de porta",
        "menu_exit_title": ">> Sair",
        "menu_exit_desc": "Encerrar o programa",
        "menu_hint": "Cima/Baixo = Navegar  |  Enter = Selecionar  |  ESC = Sair",
        # Dashboard
        "dash_subtitle": "*  DS4Wifi Controller  -  Emulador DualShock 4 sem Fio  *",
        "dash_status": ">> Status",
        "dash_port": ":: Porta",
        "dash_device": "[] Dispositivo USB",
        "dash_adb": "<> ADB Reverse",
        "dash_ip": "-- IP do Celular",
        "dash_battery": "%% Bateria",
        "dash_shortcuts": "Atalhos",
        "dash_shortcut_exit": "Ctrl+C = Encerrar",
        "dash_panel_status": "[ Conexao & Status ]",
        "dash_panel_controller": "[ Visualizador do Controle ]",
        "dash_footer_exit": "Ctrl+C para sair",
        # Status values
        "status_disconnected": "Desconectado",
        "status_not_run": "Nao executado",
        "status_none": "Nenhum",
        "status_waiting": "Aguardando Celular",
        "status_connected": "Celular Conectado",
        "status_none_detected": "Nenhum detectado",
        "status_port_redirect": "Porta {port} redirecionada",
        "status_port_busy": "Erro: porta {port} ocupada",
        # Loading
        "loading_init_controller": "... Inicializando controle DualShock 4 virtual",
        "loading_init_success": "[+] Controle virtual criado com sucesso!",
        "loading_init_error": "[X] ERRO: Nao foi possivel inicializar o controle virtual",
        "loading_init_hint": "Certifique-se de que o driver ViGEmBus esta instalado e tente novamente.",
        "loading_error_title": "Erro Fatal",
        "loading_press_key": "Aperte qualquer tecla para sair...",
        "loading_adb": "... Executando ADB Reverse",
        "loading_result": "Resultado:",
        # Exit
        "exit_bye": "*  Ate mais!  *",
        "exit_server_bye": "*  Servidor encerrado. Ate mais!  *",
    },
    "es": {
        # Language selector
        "lang_title": "Seleccionar Idioma",
        "lang_hint": "Arriba/Abajo = Navegar  |  Enter = Seleccionar",
        "lang_en": "English",
        "lang_pt": "Portugues",
        "lang_es": "Espanol",
        # Main menu
        "subtitle": "Emulador de Control DualShock 4 Inalambrico",
        "menu_select": "--- Seleccione una opcion ---",
        "menu_start_title": ">> Iniciar Servidor Completo",
        "menu_start_desc": "Inicia el servidor + ADB Reverse automaticamente",
        "menu_adb_title": ">> Solo ADB Reverse",
        "menu_adb_desc": "Ejecuta solo el redireccionamiento de puerto",
        "menu_exit_title": ">> Salir",
        "menu_exit_desc": "Cerrar el programa",
        "menu_hint": "Arriba/Abajo = Navegar  |  Enter = Seleccionar  |  ESC = Salir",
        # Dashboard
        "dash_subtitle": "*  DS4Wifi Controller  -  Emulador DualShock 4 Inalambrico  *",
        "dash_status": ">> Estado",
        "dash_port": ":: Puerto",
        "dash_device": "[] Dispositivo USB",
        "dash_adb": "<> ADB Reverse",
        "dash_ip": "-- IP del Telefono",
        "dash_battery": "%% Bateria",
        "dash_shortcuts": "Atajos",
        "dash_shortcut_exit": "Ctrl+C = Salir",
        "dash_panel_status": "[ Conexion & Estado ]",
        "dash_panel_controller": "[ Visualizador del Control ]",
        "dash_footer_exit": "Ctrl+C para salir",
        # Status values
        "status_disconnected": "Desconectado",
        "status_not_run": "No ejecutado",
        "status_none": "Ninguno",
        "status_waiting": "Esperando Telefono",
        "status_connected": "Telefono Conectado",
        "status_none_detected": "Ninguno detectado",
        "status_port_redirect": "Puerto {port} redirigido",
        "status_port_busy": "Error: puerto {port} ocupado",
        # Loading
        "loading_init_controller": "... Inicializando control DualShock 4 virtual",
        "loading_init_success": "[+] Control virtual creado exitosamente!",
        "loading_init_error": "[X] ERROR: No se pudo inicializar el control virtual",
        "loading_init_hint": "Asegurese de que el driver ViGEmBus esta instalado e intente de nuevo.",
        "loading_error_title": "Error Fatal",
        "loading_press_key": "Presione cualquier tecla para salir...",
        "loading_adb": "... Ejecutando ADB Reverse",
        "loading_result": "Resultado:",
        # Exit
        "exit_bye": "*  Hasta luego!  *",
        "exit_server_bye": "*  Servidor detenido. Hasta luego!  *",
    },
}

def t(key, **kwargs):
    """Get translated string for current language."""
    text = TRANSLATIONS.get(current_lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# ──────────────────────────────────────────────
#  Funções de Gradiente e Estilo
# ──────────────────────────────────────────────

def gradient_text(text_str, colors=None):
    """Cria um Text com gradiente de cores aplicado caractere a caractere."""
    if colors is None:
        colors = GRAD
    rich_text = Text()
    visible_chars = [c for c in text_str if c != '\n']
    total = max(len(visible_chars), 1)
    char_idx = 0
    for ch in text_str:
        if ch == '\n':
            rich_text.append('\n')
        else:
            # Interpola posição no gradiente
            pos = char_idx / total * (len(colors) - 1)
            color = colors[min(int(pos), len(colors) - 1)]
            rich_text.append(ch, style=f"bold {color}")
            char_idx += 1
    return rich_text

BANNER_LINES = [
    "  ██████╗  ██████╗██╗  ██╗██╗██╗██╗███████╗██╗",
    "  ██╔══██╗██╔════╝██║  ██║██║██║██║██╔════╝██║",
    "  ██║  ██║╚█████╗ ███████║██║██║██║█████╗  ██║",
    "  ██║  ██║ ╚═══██╗╚════██║██║██║██║██╔══╝  ╚═╝",
    "  ██████╔╝██████╔╝     ██║╚█████╔╝██║     ██╗",
    "  ╚═════╝ ╚═════╝      ╚═╝ ╚════╝ ╚═╝     ╚═╝",
]

def render_gradient_banner():
    """Renderiza o banner ASCII com gradiente linha a linha."""
    line_colors = [
        ["#6C63FF", "#7B73FF", "#8A83FF"],
        ["#5B86E5", "#6B96F5", "#7BA6FF"],
        ["#36D1DC", "#46E1EC", "#56F1FC"],
        ["#00C9A7", "#10D9B7", "#20E9C7"],
        ["#00B4D8", "#10C4E8", "#20D4F8"],
        ["#48CAE4", "#58DAF4", "#68EAFF"],
    ]
    text = Text(justify="center")
    for i, line in enumerate(BANNER_LINES):
        colors = line_colors[i % len(line_colors)]
        chunk_size = max(len(line) // len(colors), 1)
        for j, ch in enumerate(line):
            ci = min(j // chunk_size, len(colors) - 1)
            text.append(ch, style=f"bold {colors[ci]}")
        text.append("\n")
    return text

# ──────────────────────────────────────────────
#  Funções de Rede e Controle
# ──────────────────────────────────────────────

def run_adb_reverse():
    global adb_status, connected_device
    local_appdata = os.environ.get('LOCALAPPDATA')
    if not local_appdata:
        adb_status = "Erro: LOCALAPPDATA n/f"
        return False

    adb_path = os.path.join(local_appdata, 'Android', 'Sdk', 'platform-tools', 'adb.exe')
    
    if os.path.exists(adb_path):
        try:
            # Lista os dispositivos conectados
            devices_result = subprocess.run([adb_path, "devices"], capture_output=True, text=True)
            lines = devices_result.stdout.strip().split('\n')
            if len(lines) > 1 and lines[1].strip():
                connected_device = lines[1].split()[0]
            else:
                connected_device = "none_detected"

            # Executa o reverse
            result = subprocess.run([adb_path, "reverse", f"tcp:{PORT}", f"tcp:{PORT}"], capture_output=True, text=True)
            if result.returncode == 0:
                adb_status = "port_redirected"
                return True
            else:
                adb_status = f"ADB Error: {result.stderr.strip()}"
        except Exception as e:
            adb_status = f"Error: {str(e)}"
    else:
        adb_status = "adb.exe not found"
    return False

def rumble_callback(client, target, large_motor, small_motor, led_number, user_data):
    global current_conn
    if current_conn:
        try:
            packet = {
                "type": "rumble",
                "large": large_motor,
                "small": small_motor
            }
            payload = json.dumps(packet) + "\n"
            current_conn.sendall(payload.encode('utf-8'))
        except Exception:
            pass

def safe_clamp(value, lo, hi):
    """Converte para float de forma defensiva e limita ao intervalo [lo, hi].

    Protege contra valores ausentes, NaN/Infinity ou tipos inesperados num pacote
    corrompido — qualquer um deles deixaria o controle virtual num estado bizarro.
    """
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if f != f:  # NaN
        return 0.0
    if f == float('inf'):
        return hi
    if f == float('-inf'):
        return lo
    return max(lo, min(f, hi))

def safe_axis(value):
    """Lê um eixo do D-pad garantindo que seja exatamente -1, 0 ou 1."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return 0
    return max(-1, min(v, 1))

def get_dpad_direction(x, y):
    if x == 0 and y == -1: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH
    elif x == 1 and y == -1: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST
    elif x == 1 and y == 0: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST
    elif x == 1 and y == 1: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST
    elif x == 0 and y == 1: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH
    elif x == -1 and y == 1: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST
    elif x == -1 and y == 0: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST
    elif x == -1 and y == -1: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST
    else: return vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE

# ──────────────────────────────────────────────
#  Funções do Dashboard (Rich Live)
# ──────────────────────────────────────────────

def draw_stick_visual(x_val, y_val, label):
    """Desenha uma representação visual 2D do analógico como um mini-grid."""
    size = 7
    center = size // 2
    # Mapeia -1..1 para 0..size-1
    px = int((x_val + 1.0) / 2.0 * (size - 1))
    py = int((y_val + 1.0) / 2.0 * (size - 1))
    px = max(0, min(px, size - 1))
    py = max(0, min(py, size - 1))

    lines = []
    for row in range(size):
        row_chars = []
        for col in range(size):
            if row == py and col == px:
                row_chars.append("[bold #00FF88]O[/]")
            elif row == center and col == center:
                row_chars.append("[dim white]+[/]")
            elif row == center:
                row_chars.append("[dim #333333]-[/]")
            elif col == center:
                row_chars.append("[dim #333333]|[/]")
            else:
                row_chars.append("[dim #1a1a2e].[/]")
        lines.append(" ".join(row_chars))

    header = f"  [bold #48CAE4]{label}[/] [dim]X:[/][#36D1DC]{x_val:+.2f}[/] [dim]Y:[/][#36D1DC]{y_val:+.2f}[/]"
    return header + "\n" + "\n".join(lines)

def draw_trigger_bar_fancy(val, label, color_on="#00FF88", color_off="#1a1a2e"):
    """Gera uma barrinha de progresso estilizada para os gatilhos."""
    width = 20
    fill = int(val * width)
    fill = max(0, min(fill, width))
    bar = f"[{color_on}]{'█' * fill}[/][{color_off}]{'░' * (width - fill)}[/]"
    pct = int(val * 100)
    return f"  [bold #FFD93D]{label}[/] {bar} [bold white]{pct:3d}%[/]"

def make_layout() -> Layout:
    layout = Layout()
    
    # Check terminal size for responsiveness
    is_small = console.width < 110
    
    layout.split(
        Layout(name="header", size=9),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    
    if is_small:
        # Stack vertically on small screens
        layout["body"].split_column(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
    else:
        # Side-by-side on wide screens
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3)
        )
    return layout

def render_dashboard() -> Layout:
    layout = make_layout()
    
    # ── HEADER ──
    banner = render_gradient_banner()
    subtitle = Text(f"  {t('dash_subtitle')}  ", style="bold #5B86E5", justify="center")
    header_group = Text()
    header_group.append_text(banner)
    header_group.append_text(subtitle)
    layout["header"].update(
        Panel(header_group, border_style="#3a3a5c", box=box.DOUBLE_EDGE)
    )

    # ── PAINEL ESQUERDO (Status) ──
    status_table = Table.grid(padding=(0, 2))
    status_table.add_column(style="bold #FFD93D", justify="right", min_width=22)
    status_table.add_column(style="bold white")
    
    # Resolve status display
    status_map = {
        "connected": ("[bold #00FF88][+] ", t("status_connected")),
        "waiting": ("[bold #FFD93D][~] ", t("status_waiting")),
        "disconnected": ("[bold #FF6B6B][x] ", t("status_disconnected")),
    }
    prefix, status_text = status_map.get(server_status, ("[bold #FF6B6B][x] ", server_status))
    st_display = f"{prefix}{status_text}[/]"

    # Resolve device display
    if connected_device in ("none", "none_detected"):
        dev_display = t("status_none") if connected_device == "none" else t("status_none_detected")
        dev_line = f"[#FF6B6B]x {dev_display}[/]"
    else:
        dev_line = f"[#00FF88]+ {connected_device}[/]"

    # Resolve ADB display
    if adb_status == "port_redirected":
        adb_display = f"[#00FF88]+ {t('status_port_redirect', port=PORT)}[/]"
    elif adb_status == "not_run":
        adb_display = f"[#FF6B6B]{t('status_not_run')}[/]"
    else:
        adb_display = f"[#FF6B6B]{adb_status}[/]"

    status_table.add_row(t("dash_status"), st_display)
    status_table.add_row(t("dash_port"), f"[#48CAE4]{PORT}[/]")
    status_table.add_row(t("dash_device"), dev_line)
    status_table.add_row(t("dash_adb"), adb_display)
    status_table.add_row(t("dash_ip"), f"[bold #48CAE4]{client_ip}[/]")
    
    # Resolve battery display
    with state_lock:
        bat_val = current_state.get("battery", -1)
    
    if bat_val >= 0:
        if bat_val > 50:
            bat_color = "#00FF88"
        elif bat_val > 20:
            bat_color = "#FFD93D"
        else:
            bat_color = "#FF6B6B"
        bat_display = f"[{bat_color}]{bat_val}%[/]"
    else:
        bat_display = "[grey62]N/A[/]"
    
    status_table.add_row(t("dash_battery"), bat_display)
    
    # Separator
    status_table.add_row("", "")
    status_table.add_row(f"[dim #5B86E5]{t('dash_shortcuts')}[/]", f"[dim #aaa]{t('dash_shortcut_exit')}[/]")

    layout["left"].update(
        Panel(
            status_table,
            title=f"[bold #FFD93D]{t('dash_panel_status')}[/]",
            border_style="#3a3a5c",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    # ── PAINEL DIREITO (Controle) ──
    with state_lock:
        s = current_state.copy()

    # Botões com cores temáticas do DualShock
    def btn(name, label, color_on="#00FF88", color_off="#333333"):
        if s.get(name):
            return f"[bold {color_on}]# {label}[/]"
        else:
            return f"[{color_off}]- {label}[/]"

    # D-PAD visual
    dpad_u = "[bold #00FF88]UP[/]" if s.get("dpad_y") == -1 else "[#333333]UP[/]"
    dpad_d = "[bold #00FF88]DN[/]" if s.get("dpad_y") == 1 else "[#333333]DN[/]"
    dpad_l = "[bold #00FF88]LF[/]" if s.get("dpad_x") == -1 else "[#333333]LF[/]"
    dpad_r = "[bold #00FF88]RT[/]" if s.get("dpad_x") == 1 else "[#333333]RT[/]"

    # Face buttons com cores oficiais do PlayStation
    tri = btn("triangle", "TRI", color_on="#00D084")    # Verde
    sqr = btn("square", "SQR", color_on="#E879F9")      # Rosa
    cir = btn("circle", "CIR", color_on="#FF6B6B")      # Vermelho
    crs = btn("cross", "CRS", color_on="#60A5FA")       # Azul

    # Shoulder buttons
    l1 = btn("l1", "L1", color_on="#FFD93D")
    r1 = btn("r1", "R1", color_on="#FFD93D")
    l2d = btn("l2_btn", "L2", color_on="#FF9F43")
    r2d = btn("r2_btn", "R2", color_on="#FF9F43")
    share = btn("share", "SHARE", color_on="#48CAE4")
    ps = btn("ps", "PS", color_on="#6C63FF")
    options = btn("options", "OPTIONS", color_on="#48CAE4")
    l3 = btn("l3", "L3", color_on="#36D1DC")
    r3 = btn("r3", "R3", color_on="#36D1DC")

    # Layout de botões estilizado
    buttons_section = f"""
  {l1}                       {r1}
  {l2d}                       {r2d}

        {dpad_u}                   {tri}
     {dpad_l}    {dpad_r}              {sqr}     {cir}
        {dpad_d}                   {crs}

     {share}    {ps}    {options}
       {l3}                  {r3}
"""

    # Analógicos visuais 2D
    stick_l = draw_stick_visual(s['lx'], s['ly'], "L-Stick")
    stick_r = draw_stick_visual(s['rx'], s['ry'], "R-Stick")

    # Gatilhos
    trigger_l = draw_trigger_bar_fancy(s['lt'], "L2")
    trigger_r = draw_trigger_bar_fancy(s['rt'], "R2")

    full_content = f"""{buttons_section}
{stick_l}

{stick_r}

{trigger_l}
{trigger_r}
"""

    layout["right"].update(
        Panel(
            full_content,
            title=f"[bold #00FF88]{t('dash_panel_controller')}[/]",
            border_style="#3a3a5c",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )

    # ── FOOTER ──
    footer_text = Text.from_markup(
        "  [dim #5B86E5]DS4Wifi[/] [dim #3a3a5c]|[/] "
        "[dim #aaa]v1.0[/] [dim #3a3a5c]|[/] "
        "[dim #36D1DC]github.com/Deon/DS4Wifi[/] [dim #3a3a5c]|[/] "
        f"[dim #FFD93D]{t('dash_footer_exit')}[/]",
        justify="center"
    )
    layout["footer"].update(
        Panel(footer_text, border_style="#3a3a5c", box=box.HORIZONTALS)
    )

    return layout

# ──────────────────────────────────────────────
#  Receiver de Socket
# ──────────────────────────────────────────────

def socket_receiver():
    """Thread dedicada para gerenciar a conexão socket e processar os pacotes do celular"""
    global server_status, client_ip, current_conn, gamepad
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    try:
        server.bind((HOST, PORT))
    except Exception:
        server_status = "port_busy"
        return

    server.listen(1)
    server_status = "waiting"

    try:
        while True:
            conn, addr = server.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            client_ip = addr[0]
            server_status = "connected"
            current_conn = conn
            
            gamepad.reset()
            gamepad.update()

            f = conn.makefile('r', encoding='utf-8')
            try:
                for line in f:
                    if not line:
                        break
                    
                    try:
                        packet = json.loads(line)
                        
                        # Atualiza o estado global para renderização
                        with state_lock:
                            for key in current_state.keys():
                                if key in packet:
                                    current_state[key] = packet[key]
                        
                        # 1. Atualiza Analógicos
                        # No Android, puxar o analógico para cima gera Y negativo (-1.0).
                        # Para o vgamepad / DirectX interpretar cima como cima, o eixo Y precisa ser invertido (-ly / -ry).
                        lx = safe_clamp(packet.get("lx", 0.0), -1.0, 1.0)
                        ly = safe_clamp(packet.get("ly", 0.0), -1.0, 1.0)
                        rx = safe_clamp(packet.get("rx", 0.0), -1.0, 1.0)
                        ry = safe_clamp(packet.get("ry", 0.0), -1.0, 1.0)
                        gamepad.left_joystick_float(lx, -ly)
                        gamepad.right_joystick_float(rx, -ry)

                        # 2. Atualiza Gatilhos
                        lt = safe_clamp(packet.get("lt", 0.0), 0.0, 1.0)
                        rt = safe_clamp(packet.get("rt", 0.0), 0.0, 1.0)
                        gamepad.left_trigger_float(lt)
                        gamepad.right_trigger_float(rt)

                        # 3. Atualiza DPAD
                        dpad_x = safe_axis(packet.get("dpad_x", 0))
                        dpad_y = safe_axis(packet.get("dpad_y", 0))
                        gamepad.directional_pad(get_dpad_direction(dpad_x, dpad_y))

                        # 4. Atualiza Botões Comuns
                        for name, button_const in BUTTON_MAP.items():
                            if bool(packet.get(name, False)):
                                gamepad.press_button(button_const)
                            else:
                                gamepad.release_button(button_const)

                        # 5. Atualiza Botões Especiais
                        for name, button_const in SPECIAL_BUTTON_MAP.items():
                            if bool(packet.get(name, False)):
                                gamepad.press_special_button(button_const)
                            else:
                                gamepad.release_special_button(button_const)

                        gamepad.update()

                    except Exception:
                        pass
                        
            except socket.error:
                pass
            finally:
                current_conn = None
                conn.close()
                gamepad.reset()
                gamepad.update()
                server_status = "waiting"
                client_ip = "---"
                # Limpa estado
                with state_lock:
                    for k in current_state.keys():
                        if k == "battery":
                            current_state[k] = -1
                        elif isinstance(current_state[k], bool):
                            current_state[k] = False
                        elif isinstance(current_state[k], float):
                            current_state[k] = 0.0
                        else:
                            current_state[k] = 0
                
    except Exception:
        pass
    finally:
        server.close()

# ──────────────────────────────────────────────
#  Seletor de Idioma / Language Selector
# ──────────────────────────────────────────────

def render_lang_menu(selected):
    """Renderiza o seletor de idioma."""
    langs = [
        {"key": "en", "label": "English"},
        {"key": "pt", "label": "Portugues"},
        {"key": "es", "label": "Espanol"},
    ]

    banner = render_gradient_banner()
    header_panel = Panel(
        Align.center(banner),
        border_style="#3a3a5c",
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    )

    from rich.console import Group
    parts = []
    parts.append(Text("Select Language / Selecione o Idioma / Seleccionar Idioma", style="bold #5B86E5", justify="center"))
    parts.append(Text(""))

    for idx, lang in enumerate(langs):
        is_sel = idx == selected
        if is_sel:
            style = "bold #00FF88"
            border = "#00FF88"
            arrow = "  > "
        else:
            style = "#777"
            border = "#2a2a3e"
            arrow = "    "

        opt_text = Text()
        opt_text.append(arrow, style=style)
        opt_text.append(lang["label"], style=style)

        panel = Panel(
            opt_text,
            border_style=border,
            box=box.ROUNDED if is_sel else box.SIMPLE,
            width=40,
            padding=(0, 1),
        )
        parts.append(Align.center(panel))

    parts.append(Text(""))
    parts.append(Text("Up/Down = Navigate  |  Enter = Select", style="dim #555", justify="center"))

    layout = Layout()
    layout.split(
        Layout(name="header", size=9),
        Layout(name="body"),
    )
    layout["header"].update(header_panel)
    layout["body"].update(Align.center(Group(*parts), vertical="top"))
    return layout

def language_menu():
    """Seletor de idioma sem flicker."""
    global current_lang
    langs = ["en", "pt", "es"]
    selected = 0

    with Live(render_lang_menu(selected), refresh_per_second=30, screen=True, console=console) as live:
        while True:
            key = msvcrt.getch()
            if key == b'\xe0' or key == b'\x00':
                arrow = msvcrt.getch()
                if arrow == b'H':
                    selected = (selected - 1) % 3
                elif arrow == b'P':
                    selected = (selected + 1) % 3
            elif key == b'\r':
                current_lang = langs[selected]
                return
            live.update(render_lang_menu(selected))

# ──────────────────────────────────────────────
#  Menu Principal Interativo
# ──────────────────────────────────────────────

def render_menu(selected):
    """Renderiza o menu como um Layout Rich (sem limpar tela)."""
    menu_options = [
        {"title": t("menu_start_title"), "desc": t("menu_start_desc")},
        {"title": t("menu_adb_title"), "desc": t("menu_adb_desc")},
        {"title": t("menu_exit_title"), "desc": t("menu_exit_desc")},
    ]

    banner = render_gradient_banner()
    subtitle = Text(t("subtitle"), style="bold #5B86E5", justify="center")
    header_group = Text()
    header_group.append_text(banner)
    header_group.append_text(subtitle)

    header_panel = Panel(
        Align.center(header_group),
        border_style="#3a3a5c",
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    )

    from rich.console import Group
    options_parts = []
    options_parts.append(Text(t("menu_select"), style="dim #3a3a5c", justify="center"))
    options_parts.append(Text(""))

    for idx, opt in enumerate(menu_options):
        is_sel = idx == selected
        if is_sel:
            title_style = "bold #00FF88"
            desc_style = "#aaa"
            border = "#00FF88"
            arrow = "  > "
        else:
            title_style = "#777"
            desc_style = "#444"
            border = "#2a2a3e"
            arrow = "    "

        option_text = Text()
        option_text.append(arrow, style=title_style)
        option_text.append(opt["title"], style=title_style)
        option_text.append(f"\n       {opt['desc']}", style=desc_style)

        panel = Panel(
            option_text,
            border_style=border,
            box=box.ROUNDED if is_sel else box.SIMPLE,
            width=58,
            padding=(0, 1),
        )
        options_parts.append(Align.center(panel))

    options_parts.append(Text(""))
    options_parts.append(Text(f"  {t('menu_hint')}", style="dim #555", justify="center"))

    menu_body = Group(*options_parts)

    layout = Layout()
    layout.split(
        Layout(name="header", size=9),
        Layout(name="body"),
    )
    layout["header"].update(header_panel)
    layout["body"].update(Align.center(menu_body, vertical="top"))
    return layout

def main_menu():
    """Menu interativo sem flicker usando Rich Live."""
    selected = 0
    num_options = 3

    with Live(render_menu(selected), refresh_per_second=30, screen=True, console=console) as live:
        while True:
            key = msvcrt.getch()
            if key == b'\xe0' or key == b'\x00':
                arrow = msvcrt.getch()
                if arrow == b'H':
                    selected = (selected - 1) % num_options
                elif arrow == b'P':
                    selected = (selected + 1) % num_options
            elif key == b'\r':
                return selected
            elif key == b'\x1b':
                return 2
            live.update(render_menu(selected))

# ──────────────────────────────────────────────
#  Ponto de Entrada
# ──────────────────────────────────────────────

def start_application():
    global gamepad
    
    # 0. Seletor de idioma
    language_menu()

    # 1. Executa Menu Interativo
    choice = main_menu()
    
    if choice == 2:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print()
        console.print(Align.center(Text(t("exit_bye"), style="bold #FFD93D")))
        console.print()
        time.sleep(0.5)
        sys.exit(0)

    # 2. Tela de loading com inicialização
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print()
    banner = render_gradient_banner()
    console.print(Panel(
        Align.center(banner),
        border_style="#3a3a5c",
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    ))
    console.print()

    # Inicializa o controle virtual
    try:
        console.print(Align.center(Text(t("loading_init_controller"), style="bold #48CAE4")))
        gamepad = vg.VDS4Gamepad()
        gamepad.reset()
        gamepad.update()
        console.print(Align.center(Text(t("loading_init_success"), style="bold #00FF88")))
    except Exception as e:
        console.print()
        console.print(Panel(
            f"[bold #FF6B6B]{t('loading_init_error')}[/]\n\n"
            f"[#FF9F43]{e}[/]\n\n"
            f"[dim #aaa]{t('loading_init_hint')}[/]",
            title=f"[bold #FF6B6B]{t('loading_error_title')}[/]",
            border_style="#FF6B6B",
            box=box.DOUBLE_EDGE,
            padding=(1, 2),
        ))
        console.print()
        console.print(Align.center(Text(t("loading_press_key"), style="dim #777")))
        msvcrt.getch()
        sys.exit(1)

    if choice == 0:
        # Roda o redirecionamento automático
        console.print(Align.center(Text(t("loading_adb"), style="bold #48CAE4")))
        run_adb_reverse()
        
        if adb_status == "port_redirected":
            console.print(Align.center(Text(f"[+] {t('status_port_redirect', port=PORT)}", style="bold #00FF88")))
        else:
            console.print(Align.center(Text(f"[!] {adb_status}", style="bold #FFD93D")))
        
        time.sleep(0.8)

        # Inicia a thread receptora do socket
        thread = threading.Thread(target=socket_receiver, daemon=True)
        thread.start()

        # Inicia a renderização do Dashboard interativo
        os.system('cls' if os.name == 'nt' else 'clear')
        with Live(render_dashboard(), refresh_per_second=30, screen=True) as live:
            try:
                while True:
                    live.update(render_dashboard())
                    time.sleep(0.03)
            except KeyboardInterrupt:
                pass
            finally:
                console.print()
                console.print(Align.center(Text(t("exit_server_bye"), style="bold #FFD93D")))
                console.print()
                
    elif choice == 1:
        # Apenas executa ADB reverse
        console.print(Align.center(Text(t("loading_adb"), style="bold #48CAE4")))
        console.print()
        run_adb_reverse()
        
        if adb_status == "port_redirected":
            result_text = t('status_port_redirect', port=PORT)
        else:
            result_text = adb_status
        
        console.print(Panel(
            f"[bold #FFD93D]{t('loading_result')}[/]\n\n"
            f"[bold white]{result_text}[/]",
            title="[bold #48CAE4]<> ADB Reverse[/]",
            border_style="#3a3a5c",
            box=box.ROUNDED,
            padding=(1, 2),
            width=50,
        ))
        console.print()
        console.print(Align.center(Text(t("loading_press_key"), style="dim #777")))
        msvcrt.getch()

if __name__ == "__main__":
    start_application()
