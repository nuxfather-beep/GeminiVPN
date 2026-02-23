import sys
import os
import ctypes
import traceback
import time
import tempfile
import urllib.request
import urllib.error
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_file = Path(__file__).parent / "crash_log.txt"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRITICAL:\n{error_msg}\n")
    except:
        pass
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, f"Критическая ошибка:\n{error_msg}", "GeminiVPN Error", 0x10)

sys.excepthook = global_exception_handler

try:
    from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, pyqtSignal, QByteArray, QThread, QUrl, QObject
    from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QIcon, QAction, QDesktopServices
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsOpacityEffect, QSystemTrayIcon, QMenu, QMessageBox
    from PyQt6.QtSvgWidgets import QSvgWidget
    from PyQt6.QtNetwork import QLocalServer, QLocalSocket
except ImportError:
    sys.exit(1)

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if sys.platform == 'win32' else "/etc/hosts"

LOGO_SVG = """
<svg viewBox="0 0 11 11" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="35%" stop-color="{c2}"/>
      <stop offset="67%" stop-color="{c3}"/>
    </linearGradient>
  </defs>
  <path fill="url(#g)" d="M9,1C7.488,1,5.4077,2.1459,4.0488,4H3C2.1988,4,1.8162,4.3675,1.5,5L1,6h1h1l1,1l1,1v1v1l1-0.5 C6.6325,9.1838,7,8.8012,7,8V6.9512C8.8541,5.5923,10,3.512,10,2V1H9z M7.5,3C7.7761,3,8,3.2239,8,3.5S7.7761,4,7.5,4 S7,3.7761,7,3.5S7.2239,3,7.5,3z M2.75,7.25L2.5,7.5C2,8,2,9,2,9s0.9448,0.0552,1.5-0.5l0.25-0.25L2.75,7.25z"/>
</svg>
"""

CTRL_SVG = """
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="{path}" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
"""

HEART_SVG = """
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="{color}"/>
</svg>
"""

class AppConfig:
    APP_NAME = "GeminiVPN"
    INSTANCE_LOCK_KEY = "geminivpn_instance_v6"
    WINDOW_WIDTH = 360
    WINDOW_HEIGHT = 600
    GRADIENT_OFF = [QColor("#9168C0"), QColor("#5684D1"), QColor("#1BA1E3")]
    GRADIENT_ON = [QColor("#10B981"), QColor("#059669"), QColor("#047857")]
    GRADIENT_CONN = [QColor("#F59E0B"), QColor("#D97706"), QColor("#B45309")]

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def check_installation():
    if not os.path.exists(HOSTS_PATH):
        return False
    try:
        with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            return "dns.malw.link" in f.read()
    except:
        return False

def safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

class SingleInstance(QObject):
    show_requested = pyqtSignal()

    def __init__(self, key):
        super().__init__()
        self.key = key
        self.server = QLocalServer(self)
        self.socket = QLocalSocket(self)
        self.socket.connectToServer(self.key)
        self.is_running = self.socket.waitForConnected(500)
        if not self.is_running:
            QLocalServer.removeServer(self.key)
            self.server.listen(self.key)
            self.server.newConnection.connect(self._handle_connection)

    def _handle_connection(self):
        client = self.server.nextPendingConnection()
        if client:
            client.waitForReadyRead(500)
            client.disconnectFromServer()
            self.show_requested.emit()

class HostsWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, action):
        super().__init__()
        self.action = action

    def run(self):
        if self.action in ("install", "update"):
            self.install()
        else:
            self.uninstall()

    def install(self):
        url = "https://raw.githubusercontent.com/ImMALWARE/dns.malw.link/refs/heads/master/hosts"
        add_url = "https://raw.githubusercontent.com/AvenCores/Goida-AI-Unlocker/refs/heads/main/additional_hosts.py"
        t_path = None
        s_path = None
        try:
            t_fd, t_path = tempfile.mkstemp()
            os.close(t_fd)
            req1 = urllib.request.Request(f"{url}?t={int(time.time())}", headers={'User-Agent': 'Mozilla/5.0'})
            content = urllib.request.urlopen(req1, timeout=15).read().decode("utf-8", errors="ignore")
            try:
                req2 = urllib.request.Request(f"{add_url}?t={int(time.time())}", headers={'User-Agent': 'Mozilla/5.0'})
                add_raw = urllib.request.urlopen(req2, timeout=15).read().decode("utf-8", errors="ignore")
                if 'hosts_add = """' in add_raw:
                    add_block = add_raw.split('hosts_add = """')[1].split('"""')[0].strip()
                    if add_block:
                        content += f"\n{add_block}\n"
            except:
                pass
            with open(t_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if sys.platform == 'win32':
                ps_c = f'$s="{t_path}";$d="{HOSTS_PATH}";Copy-Item -Path $s -Destination $d -Force;Clear-DnsClientCache;ipconfig /flushdns;ipconfig /release;ipconfig /renew;netsh winsock reset'
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.ps1', encoding='utf-8') as pf:
                    pf.write(ps_c)
                    s_path = pf.name
                cmd = ["powershell", "-WindowStyle", "Hidden", "-Command", f'Start-Process powershell -Verb runAs -WindowStyle Hidden -ArgumentList \'-NoProfile -ExecutionPolicy Bypass -File "{s_path}"\' -Wait']
                subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                fc = "resolvectl flush-caches || systemd-resolve --flush-caches || /etc/init.d/nscd restart || killall -HUP dnsmasq || true"
                if os.geteuid() == 0:
                    shutil.copy(t_path, HOSTS_PATH)
                    os.chmod(HOSTS_PATH, 0o644)
                    subprocess.run(fc, shell=True)
                else:
                    bc = f"cp '{t_path}' {HOSTS_PATH} && chmod 644 {HOSTS_PATH} && {fc}"
                    subprocess.run(["pkexec", "bash", "-c", bc], check=True)
            time.sleep(1)
            self.finished_signal.emit(True, self.action)
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            if t_path: safe_remove(t_path)
            if s_path: safe_remove(s_path)

    def uninstall(self):
        t_path = None
        s_path = None
        try:
            def_h = "127.0.0.1 localhost\n::1 localhost\n"
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as tf:
                tf.write(def_h)
                t_path = tf.name
            
            if sys.platform == 'win32':
                ps_c = f'$s="{t_path}";$d="{HOSTS_PATH}";Copy-Item -Path $s -Destination $d -Force;Clear-DnsClientCache;ipconfig /flushdns;ipconfig /release;ipconfig /renew;netsh winsock reset'
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.ps1', encoding='utf-8') as pf:
                    pf.write(ps_c)
                    s_path = pf.name
                cmd = ["powershell", "-WindowStyle", "Hidden", "-Command", f'Start-Process powershell -Verb runAs -WindowStyle Hidden -ArgumentList \'-NoProfile -ExecutionPolicy Bypass -File "{s_path}"\' -Wait']
                subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                fc = "resolvectl flush-caches || systemd-resolve --flush-caches || /etc/init.d/nscd restart || killall -HUP dnsmasq || true"
                if os.geteuid() == 0:
                    shutil.copy(t_path, HOSTS_PATH)
                    os.chmod(HOSTS_PATH, 0o644)
                    subprocess.run(fc, shell=True)
                else:
                    bc = f"cp '{t_path}' {HOSTS_PATH} && chmod 644 {HOSTS_PATH} && {fc}"
                    subprocess.run(["pkexec", "bash", "-c", bc], check=True)
            time.sleep(1)
            self.finished_signal.emit(True, "uninstall")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            if t_path: safe_remove(t_path)
            if s_path: safe_remove(s_path)

class ControlBtn(QWidget):
    clicked = pyqtSignal()

    def __init__(self, path_d, normal_hex, hover_hex):
        super().__init__()
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path_d = path_d
        self.normal_hex = normal_hex
        self.hover_hex = hover_hex
        self.setStyleSheet("QWidget { border: 2px solid #1A1A1D; border-radius: 8px; background: transparent; } QWidget:hover { background: #1A1A1D; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.svg = QSvgWidget()
        self.svg.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.svg)
        self._render(self.normal_hex)

    def _render(self, color):
        data = CTRL_SVG.format(path=self.path_d, color=color)
        self.svg.load(QByteArray(data.encode()))

    def enterEvent(self, e):
        self._render(self.hover_hex)

    def leaveEvent(self, e):
        self._render(self.normal_hex)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

class GeminiVPN(QWidget):
    def __init__(self, app_icon):
        super().__init__()
        self._app_icon = app_icon
        self._is_connected = False
        self._is_processing = False
        self._drag_pos = None
        self.c_cur = [QColor(c) for c in AppConfig.GRADIENT_OFF]
        self.worker = None
        self.donate_url = "https://www.donationalerts.com/r/verloft"
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)
        self.setWindowIcon(self._app_icon)
        
        self._build_ui()
        self._setup_tray()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer_label)
        self.timer.start(1000)

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_status_loop)
        self.check_timer.start(2000)
        
        self._init_state()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 35)
        
        self.bar = QWidget()
        self.bar.setFixedHeight(60)
        bar_l = QHBoxLayout(self.bar)
        bar_l.setContentsMargins(25, 10, 20, 0)
        
        title = QLabel(AppConfig.APP_NAME.upper())
        title.setStyleSheet("color: #555; font-size: 10px; font-weight: 900; letter-spacing: 2px;")
        
        min_btn = ControlBtn("M5 12h14", "#555555", "#FFFFFF")
        close_btn = ControlBtn("M18 6L6 18M6 6l12 12", "#555555", "#FF4444")
        
        min_btn.clicked.connect(self.showMinimized)
        close_btn.clicked.connect(self.hide)
        
        bar_l.addWidget(title)
        bar_l.addStretch()
        bar_l.addWidget(min_btn)
        bar_l.addSpacing(6)
        bar_l.addWidget(close_btn)
        root.addWidget(self.bar)

        self.logo = QSvgWidget()
        self.logo.setFixedSize(90, 90)
        self._draw_logo()
        root.addSpacing(10)
        root.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_stat = QLabel("ОТКЛЮЧЕНО")
        self.lbl_stat.setStyleSheet("color: #666; font-size: 14px; font-weight: 700; margin-top: 15px;")
        root.addWidget(self.lbl_stat, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: 300;")
        self.opac = QGraphicsOpacityEffect()
        self.opac.setOpacity(0.0)
        self.lbl_time.setGraphicsEffect(self.opac)
        root.addWidget(self.lbl_time, alignment=Qt.AlignmentFlag.AlignCenter)
        
        root.addStretch()
        
        self.btn_main = QPushButton("ПОДКЛЮЧИТЬСЯ")
        self.btn_main.setFixedSize(240, 58)
        self.btn_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_main.clicked.connect(self._handle_main_btn)
        root.addWidget(self.btn_main, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(5)

        self.btn_update = QPushButton("ОБНОВИТЬ БАЗУ")
        self.btn_update.setFixedSize(240, 58)
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.clicked.connect(self._handle_update_btn)
        self.btn_update.setVisible(False)
        root.addWidget(self.btn_update, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(5)
        
        self.btn_donate = QPushButton(" ДОНАТ")
        self.btn_donate.setFixedSize(240, 58)
        self.btn_donate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.donate_url)))
        
        don_lyt = QHBoxLayout()
        don_lyt.setContentsMargins(0, 0, 0, 0)
        
        h_svg = QSvgWidget()
        h_svg.setFixedSize(18, 18)
        h_svg.load(QByteArray(HEART_SVG.format(color="#888888").encode()))
        h_svg.setStyleSheet("background: transparent; border: none;")
        
        don_btn_lyt = QHBoxLayout(self.btn_donate)
        don_btn_lyt.setContentsMargins(65, 0, 0, 0)
        don_btn_lyt.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        don_btn_lyt.addWidget(h_svg)
        
        don_lyt.addWidget(self.btn_donate, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addLayout(don_lyt)
        
        self._update_style()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width()-2, self.height()-2, 30, 30)
        p.fillPath(path, QColor("#0A0A0C"))
        p.strokePath(path, QPen(QColor("#1A1A1D"), 2))

    def _draw_logo(self):
        d = LOGO_SVG.format(c1=self.c_cur[0].name(), c2=self.c_cur[1].name(), c3=self.c_cur[2].name())
        self.logo.load(QByteArray(d.encode()))

    def _update_style(self):
        btn_tpl = "QPushButton {{ background: {bg}; color: {tc}; border-radius: 18px; font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }} QPushButton:hover {{ background: {hbg}; }} QPushButton:pressed {{ background: {pbg}; }}"
        
        if self._is_processing:
            m_bg, m_tc, m_hbg, m_pbg = "#333333", "#888888", "#333333", "#333333"
        elif self._is_connected:
            m_bg, m_tc, m_hbg, m_pbg = "#10B981", "#FFFFFF", "#059669", "#047857"
        else:
            m_bg, m_tc, m_hbg, m_pbg = "#121214", "#A0A0A0", "#1A1A1D", "#0A0A0C"
            
        self.btn_main.setStyleSheet(btn_tpl.format(bg=m_bg, tc=m_tc, hbg=m_hbg, pbg=m_pbg))
        self.btn_update.setStyleSheet(btn_tpl.format(bg="#1BA1E3", tc="#FFFFFF", hbg="#147EAF", pbg="#0F6085"))
        self.btn_donate.setStyleSheet(btn_tpl.format(bg="#121214", tc="#888888", hbg="#1A1A1D", pbg="#0A0A0C"))

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self._app_icon)
        self.menu = QMenu()
        self.menu.setStyleSheet("QMenu { background: #0A0A0C; color: #A0A0A0; border: 1px solid #1A1A1D; } QMenu::item:selected { background: #1A1A1D; color: #FFF; }")
        
        self.show_act = QAction("Открыть", self)
        self.show_act.triggered.connect(self._show_me)
        
        self.toggle_act = QAction("Подключиться", self)
        self.toggle_act.triggered.connect(self._handle_main_btn)
        
        self.timer_act = QAction("Время: 00:00:00", self)
        self.timer_act.setEnabled(False)
        self.timer_act.setVisible(False)
        
        self.exit_act = QAction("Выход", self)
        self.exit_act.triggered.connect(QApplication.quit)
        
        self.menu.addAction(self.show_act)
        self.menu.addAction(self.toggle_act)
        self.menu.addAction(self.timer_act)
        self.menu.addSeparator()
        self.menu.addAction(self.exit_act)
        
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(lambda r: self._show_me() if r in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick) else None)
        self.tray.show()

    def handle_second_instance(self):
        self.show_act.setText("Закрыть")
        self.show_act.triggered.disconnect()
        self.show_act.triggered.connect(QApplication.quit)

    def _show_me(self):
        self.showNormal()
        self.activateWindow()

    def _init_state(self):
        if check_installation():
            self._is_connected = True
            self._set_ui_connected()
        else:
            self._is_connected = False
            self._set_ui_disconnected()

    def _check_status_loop(self):
        if self._is_processing:
            return
        st = check_installation()
        if st and not self._is_connected:
            self._is_connected = True
            self._set_ui_connected()
        elif not st and self._is_connected:
            self._is_connected = False
            self._set_ui_disconnected()

    def _handle_main_btn(self):
        if self._is_processing:
            return
        self._is_processing = True
        self.btn_main.setEnabled(False)
        self.btn_update.setEnabled(False)
        self.toggle_act.setEnabled(False)
        self.timer_act.setVisible(False)
        self._anim_opac(False)
        
        if self._is_connected:
            self.btn_main.setText("ОТКЛЮЧЕНИЕ...")
            self.lbl_stat.setText("ОТКЛЮЧЕНИЕ...")
            self.lbl_stat.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;")
            self._anim_logo_to(AppConfig.GRADIENT_CONN)
            self.worker = HostsWorker("uninstall")
        else:
            self.btn_main.setText("ПОДКЛЮЧЕНИЕ...")
            self.lbl_stat.setText("ПОДКЛЮЧЕНИЕ...")
            self.lbl_stat.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;")
            self._anim_logo_to(AppConfig.GRADIENT_CONN)
            self.worker = HostsWorker("install")
            
        self._update_style()
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _handle_update_btn(self):
        if self._is_processing:
            return
        self._is_processing = True
        self.btn_main.setEnabled(False)
        self.btn_update.setEnabled(False)
        self.toggle_act.setEnabled(False)
        self.timer_act.setVisible(False)
        self._anim_opac(False)
        
        self.btn_update.setText("ОБНОВЛЕНИЕ...")
        self.lbl_stat.setText("ОБНОВЛЕНИЕ БАЗЫ...")
        self.lbl_stat.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;")
        self._anim_logo_to(AppConfig.GRADIENT_CONN)
        
        self.worker = HostsWorker("update")
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self, success, action):
        self._is_processing = False
        self.btn_main.setEnabled(True)
        self.btn_update.setEnabled(True)
        self.toggle_act.setEnabled(True)
        self.btn_update.setText("ОБНОВИТЬ БАЗУ")
        
        if success:
            if action in ("install", "update"):
                self._is_connected = True
                self._set_ui_connected()
            else:
                self._is_connected = False
                self._set_ui_disconnected()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось выполнить операцию.\nПроверьте права доступа и сеть.")
            if self._is_connected:
                self._set_ui_connected()
            else:
                self._set_ui_disconnected()

    def _set_ui_connected(self):
        if not check_installation():
            self._set_ui_disconnected()
            return
        self.btn_main.setText("ОТКЛЮЧИТЬСЯ")
        self.lbl_stat.setText("ПОДКЛЮЧЕНО")
        self.btn_update.setVisible(True)
        self.lbl_stat.setStyleSheet("color: #10B981; font-size: 14px; font-weight: 700; margin-top: 15px;")
        self.toggle_act.setText("Отключиться")
        if not self._is_processing:
            self.timer_act.setVisible(True)
            self._anim_opac(True)
        self._anim_logo_to(AppConfig.GRADIENT_ON)
        self._update_style()
        self._update_timer_label()

    def _set_ui_disconnected(self):
        self.btn_main.setText("ПОДКЛЮЧИТЬСЯ")
        self.lbl_stat.setText("ОТКЛЮЧЕНО")
        self.btn_update.setVisible(False)
        self.lbl_stat.setStyleSheet("color: #666; font-size: 14px; font-weight: 700; margin-top: 15px;")
        self.toggle_act.setText("Подключиться")
        self.timer_act.setVisible(False)
        self._anim_opac(False)
        self._anim_logo_to(AppConfig.GRADIENT_OFF)
        self._update_style()

    def _update_timer_label(self):
        if self._is_connected and not self._is_processing and os.path.exists(HOSTS_PATH):
            try:
                mtime = os.path.getmtime(HOSTS_PATH)
                diff = int(time.time() - mtime)
                if diff < 0:
                    diff = 0
                t_str = f"{diff//3600:02d}:{(diff%3600)//60:02d}:{diff%60:02d}"
                self.lbl_time.setText(t_str)
                self.timer_act.setText(f"Время: {t_str}")
            except:
                pass
        self.update()

    def _anim_logo_to(self, target_gradient):
        self.a_col = QVariantAnimation(self)
        self.a_col.setDuration(400)
        s = [QColor(c) for c in self.c_cur]
        self.a_col.valueChanged.connect(lambda v: self._step_logo(v, s, target_gradient))
        self.a_col.setStartValue(0.0)
        self.a_col.setEndValue(1.0)
        self.a_col.start()

    def _step_logo(self, v, s, e):
        for i in range(3):
            r = int(s[i].red() + (e[i].red() - s[i].red()) * v)
            g = int(s[i].green() + (e[i].green() - s[i].green()) * v)
            b = int(s[i].blue() + (e[i].blue() - s[i].blue()) * v)
            self.c_cur[i] = QColor(r, g, b)
        self._draw_logo()

    def _anim_opac(self, show):
        self.a_op = QVariantAnimation(self)
        self.a_op.setDuration(250)
        self.a_op.setStartValue(self.opac.opacity())
        self.a_op.setEndValue(1.0 if show else 0.0)
        self.a_op.valueChanged.connect(self.opac.setOpacity)
        self.a_op.start()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.pos().y() <= 60:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

def main():
    if sys.platform == 'win32':
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'geminivpn.v6')
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    instance = SingleInstance(AppConfig.INSTANCE_LOCK_KEY)
    if instance.is_running:
        return 0
    
    icon_file = get_resource_path("icon.ico")
    app_icon = QIcon(icon_file) if os.path.exists(icon_file) else app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon)
    
    window = GeminiVPN(app_icon)
    instance.show_requested.connect(window.handle_second_instance)
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())