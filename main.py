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
import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_file = Path(tempfile.gettempdir()) / "geminivpn_crash.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRITICAL:\n{error_msg}\n")
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, f"Критическая ошибка. Лог: {log_file}\n\n{error_msg[:500]}", "GeminiVPN Error", 0x10)
    except Exception:
        pass

sys.excepthook = global_exception_handler

try:
    from PyQt6.QtCore import (Qt, QTimer, QVariantAnimation, pyqtSignal, QByteArray, QThread, 
                              QUrl, QObject, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint)
    from PyQt6.QtGui import (QColor, QPainter, QPainterPath, QPen, QIcon, QAction, QDesktopServices)
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QSystemTrayIcon, QMenu, QMessageBox, QLineEdit, QGraphicsBlurEffect)
    from PyQt6.QtSvgWidgets import QSvgWidget
    from PyQt6.QtNetwork import QLocalServer, QLocalSocket
except ImportError as _imp_err:
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, f"Не удалось импортировать PyQt6.\n{_imp_err}", "GeminiVPN Error", 0x10)
    sys.exit(1)


HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts") if sys.platform == "win32" else Path("/etc/hosts")
DEFAULT_HOSTS = (
    "# Copyright (c) 1993-2009 Microsoft Corp.\n#\n"
    "# localhost name resolution is handled within DNS itself.\n"
    "#\t127.0.0.1       localhost\n#\t::1             localhost\n"
)

HOSTS_URL = "https://raw.githubusercontent.com/ImMALWARE/dns.malw.link/refs/heads/master/hosts"
ADD_HOSTS_URL = "https://raw.githubusercontent.com/AvenCores/Goida-AI-Unlocker/refs/heads/main/additional_hosts.py"
HOSTS_MARKER = "dns.malw.link"
PROMO_WEBHOOK_URL = "https://formspree.io/f/xjgpezvd"
VERSION = "1.0.0-GoldenAlpha"

class AppConfig:
    APP_NAME = "GeminiVPN"
    INSTANCE_LOCK_KEY = "geminivpn_instance_golden_alpha"
    WINDOW_WIDTH, WINDOW_HEIGHT = 360, 600
    GRADIENT_OFF = [QColor("#9168C0"), QColor("#5684D1"), QColor("#1BA1E3")]
    GRADIENT_ON = [QColor("#10B981"), QColor("#059669"), QColor("#047857")]
    GRADIENT_CONN = [QColor("#F59E0B"), QColor("#D97706"), QColor("#B45309")]
    CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GeminiVPN_Cache"
    CACHE_FILE = CACHE_DIR / "hosts_cache.txt"
    ETAG_FILE = CACHE_DIR / "hosts_etag.txt"


LOGO_SVG = '<svg viewBox="0 0 11 11" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g" x1="1" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{c1}"/><stop offset="35%" stop-color="{c2}"/><stop offset="67%" stop-color="{c3}"/></linearGradient></defs><path fill="url(#g)" d="M9,1C7.488,1,5.4077,2.1459,4.0488,4H3C2.1988,4,1.8162,4.3675,1.5,5L1,6h1h1l1,1l1,1v1v1l1-0.5 C6.6325,9.1838,7,8.8012,7,8V6.9512C8.8541,5.5923,10,3.512,10,2V1H9z M7.5,3C7.7761,3,8,3.2239,8,3.5S7.7761,4,7.5,4 S7,3.7761,7,3.5S7.2239,3,7.5,3z M2.75,7.25L2.5,7.5C2,8,2,9,2,9s0.9448,0.0552,1.5-0.5l0.25-0.25L2.75,7.25z"/></svg>'
CTRL_SVG = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="{path}" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'
HEART_SVG = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="{color}"/></svg>'
GIFT_SVG = '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 12H19V17.8C19 18.9201 19 19.4802 18.782 19.908C18.5903 20.2843 18.2843 20.5903 17.908 20.782C17.4802 21 16.9201 21 15.8 21H8.2C7.07989 21 6.51984 21 6.09202 20.782C5.71569 20.5903 5.40973 20.2843 5.21799 19.908C5 19.4802 5 18.9201 5 17.8V12ZM4.6 12H19.4C19.9601 12 20.2401 12 20.454 11.891C20.6422 11.7951 20.7951 11.6422 20.891 11.454C21 11.2401 21 10.9601 21 10.4V8.6C21 8.03995 21 7.75992 20.891 7.54601C20.7951 7.35785 20.6422 7.20487 20.454 7.10899C20.2401 7 19.9601 7 19.4 7H4.6C4.03995 7 3.75992 7 3.54601 7.10899C3.35785 7.20487 3.20487 7.35785 3.10899 7.54601C3 7.75992 3 8.03995 3 8.6V10.4C3 10.9601 3 11.2401 3.10899 11.454C3.20487 11.6422 3.35785 11.7951 3.54601 11.891C3.75992 12 4.03995 12 4.6 12Z" fill="{color}"/><path d="M12 7V20M12 7H8.46429C7.94332 7 7.4437 6.78929 7.07533 6.41421C6.70695 6.03914 6.5 5.53043 6.5 5C6.5 4.46957 6.70695 3.96086 7.07533 3.58579C7.4437 3.21071 7.94332 3 8.46429 3C11.2143 3 12 7 12 7ZM12 7H15.5357C16.0567 7 16.5563 6.78929 16.9247 6.41421C17.293 6.03914 17.5 5.53043 17.5 5C17.5 4.46957 17.293 3.96086 16.9247 3.58579C16.5563 3.21071 16.0567 3 15.5357 3C12.7857 3 12 7 12 7Z" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def check_installation():
    if not HOSTS_PATH.exists(): return False
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            return HOSTS_MARKER in f.read()
    except Exception: return False

def flush_dns_sync():
    try:
        if sys.platform == "win32":
            cf = subprocess.CREATE_NO_WINDOW
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=5, creationflags=cf)
            subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", "Clear-DnsClientCache"], capture_output=True, timeout=5, creationflags=cf)
        else:
            subprocess.run("resolvectl flush-caches || systemd-resolve --flush-caches", shell=True, timeout=5, capture_output=True)
    except Exception: pass

def get_resource_path(relative_path):
    try:
        if hasattr(sys, "_MEIPASS"): return os.path.join(sys._MEIPASS, relative_path)
    except Exception: pass
    return os.path.join(os.path.abspath("."), relative_path)


class CacheManager:
    @staticmethod
    def fetch_hosts(force_update=False):
        AppConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": f"GeminiVPN/{VERSION}"}
        
        if not force_update and AppConfig.ETAG_FILE.exists() and AppConfig.CACHE_FILE.exists():
            headers["If-None-Match"] = AppConfig.ETAG_FILE.read_text(encoding="utf-8").strip()

        req1 = urllib.request.Request(f"{HOSTS_URL}?t={int(time.time())}", headers=headers)
        
        try:
            with urllib.request.urlopen(req1, timeout=10) as response:
                content = response.read().decode("utf-8", errors="ignore")
                etag = response.headers.get("ETag")
                
                try:
                    req2 = urllib.request.Request(f"{ADD_HOSTS_URL}?t={int(time.time())}", headers={"User-Agent": headers["User-Agent"]})
                    add_raw = urllib.request.urlopen(req2, timeout=10).read().decode("utf-8", errors="ignore")
                    if 'hosts_add = """' in add_raw:
                        add_block = add_raw.split('hosts_add = """')[1].split('"""')[0].strip()
                        if add_block: content += f"\n{add_block}\n"
                except Exception: pass

                tmp_cache = AppConfig.CACHE_FILE.with_suffix('.tmp')
                tmp_cache.write_text(content, encoding="utf-8")
                tmp_cache.replace(AppConfig.CACHE_FILE)
                
                if etag: AppConfig.ETAG_FILE.write_text(etag, encoding="utf-8")
                return content
                
        except urllib.error.HTTPError as e:
            if e.code == 304 and AppConfig.CACHE_FILE.exists():
                return AppConfig.CACHE_FILE.read_text(encoding="utf-8")
            raise e
        except Exception:
            if AppConfig.CACHE_FILE.exists():
                return AppConfig.CACHE_FILE.read_text(encoding="utf-8")
            raise

class HostsWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, action):
        super().__init__()
        self.action = action

    def run(self):
        try:
            if self.action in ("install", "update"):
                content = CacheManager.fetch_hosts(force_update=(self.action == "update"))
                if not content or HOSTS_MARKER not in content:
                    self.finished_signal.emit(False, "Полученные данные пусты или повреждены.")
                    return
                self._apply_hosts(content)
            else:
                self._apply_hosts(DEFAULT_HOSTS)
                
            flush_dns_sync()
            
            actual = False
            expected = (self.action in ("install", "update"))
            for _ in range(5):
                time.sleep(0.5)
                actual = check_installation()
                if actual == expected:
                    break
                    
            if actual == expected:
                self.finished_signal.emit(True, self.action)
            else:
                self.finished_signal.emit(False, "Изменения не применились. Проверьте антивирус.")
        except Exception as e:
            self.finished_signal.emit(False, f"Ошибка: {str(e)}")

    def _apply_hosts(self, content):
        try:
            if sys.platform == "win32":
                subprocess.run(["attrib", "-R", "-S", "-H", str(HOSTS_PATH)], creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

        if is_admin():
            for _ in range(5):
                try:
                    HOSTS_PATH.write_text(content, encoding="utf-8")
                    return
                except Exception:
                    time.sleep(0.5)
                    
        tmp_file = Path(tempfile.gettempdir()) / f"geminivpn_hosts_{int(time.time())}.tmp"
        tmp_file.write_text(content, encoding="utf-8")
        
        ps_script = f"""
        try {{
            if (Test-Path '{HOSTS_PATH}') {{
                Set-ItemProperty -Path '{HOSTS_PATH}' -Name IsReadOnly -Value $false
            }}
            [System.IO.File]::WriteAllText('{HOSTS_PATH}', [System.IO.File]::ReadAllText('{tmp_file}', [System.Text.Encoding]::UTF8), (New-Object System.Text.UTF8Encoding $false))
            Clear-DnsClientCache
        }} catch {{ exit 1 }}
        """
        ps_file = tmp_file.with_suffix('.ps1')
        ps_file.write_text(ps_script, encoding="utf-8")
        
        cmd = ["powershell", "-WindowStyle", "Hidden", "-Command", f"Start-Process powershell -Verb runAs -WindowStyle Hidden -ArgumentList '-ExecutionPolicy Bypass -File \"{ps_file}\"' -Wait"]
        subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        try: 
            tmp_file.unlink(missing_ok=True)
            ps_file.unlink(missing_ok=True)
        except: pass

class PromoWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, link):
        super().__init__()
        self.link = link

    def run(self):
        try:
            req = urllib.request.Request(PROMO_WEBHOOK_URL, data=json.dumps({"video_link": self.link}).encode(), headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            urllib.request.urlopen(req, timeout=10)
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class SingleInstance(QObject):
    show_requested = pyqtSignal()
    def __init__(self, key):
        super().__init__()
        self.key = key
        sock = QLocalSocket()
        sock.connectToServer(self.key)
        self.is_running = sock.waitForConnected(500)
        sock.deleteLater()
        if not self.is_running:
            QLocalServer.removeServer(self.key)
            self.server = QLocalServer(self)
            self.server.listen(self.key)
            self.server.newConnection.connect(self._handle_connection)

    def _handle_connection(self):
        client = self.server.nextPendingConnection()
        if client:
            client.waitForReadyRead(500)
            client.deleteLater()
            self.show_requested.emit()

class ControlBtn(QWidget):
    clicked = pyqtSignal()
    def __init__(self, path_d, normal_hex, hover_hex):
        super().__init__()
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path_d, self.normal_hex, self.hover_hex = path_d, normal_hex, hover_hex
        self._hovered = False
        self.setStyleSheet("QWidget { border: 2px solid #1A1A1D; border-radius: 8px; background: transparent; } QWidget:hover { background: #1A1A1D; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.svg = QSvgWidget()
        self.svg.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.svg)
        self._render(self.normal_hex)

    def _render(self, color): self.svg.load(QByteArray(CTRL_SVG.format(path=self.path_d, color=color).encode()))
    def enterEvent(self, e): self._hovered = True; self._render(self.hover_hex); super().enterEvent(e)
    def leaveEvent(self, e): self._hovered = False; self._render(self.normal_hex); super().leaveEvent(e)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._hovered: self.clicked.emit()
        super().mouseReleaseEvent(e)

class PromoDialog(QWidget):
    closed_signal = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 480)
        self._drag_pos = None
        self._is_hiding = False

        self.setWindowOpacity(0.0)
        self.anim_group = QParallelAnimationGroup(self)
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.anim_group.addAnimation(self.opacity_anim)
        self.anim_group.addAnimation(self.pos_anim)
        
        self._build_ui()

    def show_animated(self, target_pos):
        self._is_hiding = False
        self.setWindowOpacity(0.0)
        start_pos = target_pos - QPoint(0, 30)
        self.move(start_pos)
        self.show()

        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.pos_anim.setDuration(400)
        self.pos_anim.setStartValue(start_pos)
        self.pos_anim.setEndValue(target_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.anim_group.start()

    def hide_animated(self):
        if self._is_hiding: return
        self._is_hiding = True

        self.opacity_anim.setDuration(250)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        current_pos = self.pos()
        self.pos_anim.setDuration(250)
        self.pos_anim.setStartValue(current_pos)
        self.pos_anim.setEndValue(current_pos - QPoint(0, 20))

        self.anim_group.finished.connect(self._on_hide_finished)
        self.anim_group.start()

    def _on_hide_finished(self):
        try: self.anim_group.finished.disconnect(self._on_hide_finished)
        except TypeError: pass
        self.hide()
        self.closed_signal.emit()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 30)

        self.bar = QWidget()
        self.bar.setFixedHeight(60)
        bar_l = QHBoxLayout(self.bar)
        bar_l.setContentsMargins(25, 10, 20, 0)

        title = QLabel("БОНУС ЗА ПРОДВИЖЕНИЕ")
        title.setStyleSheet("color: #1BA1E3; font-size: 10px; font-weight: 900; letter-spacing: 1px;")

        close_btn = ControlBtn("M18 6L6 18M6 6l12 12", "#555555", "#FF4444")
        close_btn.clicked.connect(self.hide_animated)
        bar_l.addWidget(title); bar_l.addStretch(); bar_l.addWidget(close_btn)
        root.addWidget(self.bar)

        self.content_l = QVBoxLayout()
        self.content_l.setContentsMargins(25, 5, 25, 10)
        self.content_l.setSpacing(15)

        self.gift_icon = QSvgWidget()
        self.gift_icon.setFixedSize(70, 70)
        self.gift_icon.load(QByteArray(GIFT_SVG.format(color="#1BA1E3").encode()))
        self.gift_icon.setStyleSheet("background: transparent; border: none;")
        self.content_l.addWidget(self.gift_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl_desc = QLabel("Помогите продвинуть наш проект,\nа мы отблагодарим вас наградой!")
        lbl_desc.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_l.addWidget(lbl_desc)

        lbl_terms = QLabel("Опубликуйте видео про GeminiVPN\nв TikTok или YouTube Shorts и прикрепите\nссылку. После проверки вы получите награду.")
        lbl_terms.setStyleSheet("color: #888888; font-size: 12px; font-weight: 500;")
        lbl_terms.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_l.addWidget(lbl_terms)
        self.content_l.addStretch()

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Вставьте ссылку на видео...")
        self.input_url.setFixedHeight(50)
        self.input_url.setStyleSheet("QLineEdit { background: #121214; color: #FFFFFF; border-radius: 12px; border: 2px solid #1A1A1D; padding: 0 15px; font-size: 13px; font-weight: 600; } QLineEdit:focus { border: 2px solid #1BA1E3; }")
        self.content_l.addWidget(self.input_url)

        self.btn_send = QPushButton("ПРОВЕРИТЬ")
        self.btn_send.setFixedSize(310, 58)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_default_send_style()
        self.btn_send.clicked.connect(self._send_promo)
        self.content_l.addWidget(self.btn_send)

        root.addLayout(self.content_l)

    def _apply_default_send_style(self):
        self.btn_send.setStyleSheet("QPushButton { background: #1BA1E3; color: #FFFFFF; border-radius: 18px; font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; } QPushButton:hover { background: #147EAF; } QPushButton:pressed { background: #0F6085; } QPushButton:disabled { background: #333333; color: #888888; }")

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(1.0, 1.0, float(self.width() - 2), float(self.height() - 2), 30.0, 30.0)
        p.fillPath(path, QColor("#0A0A0C"))
        p.strokePath(path, QPen(QColor("#1A1A1D"), 2))

    def _send_promo(self):
        if not self.input_url.text().strip(): return
        self.btn_send.setEnabled(False)
        self.btn_send.setText("ОТПРАВКА...")
        self.worker = PromoWorker(self.input_url.text().strip())
        self.worker.finished_signal.connect(self._on_sent)
        self.worker.start()

    def _on_sent(self, success, msg):
        self.btn_send.setEnabled(True)
        if success:
            self.btn_send.setText("УСПЕШНО ОТПРАВЛЕНО")
            self.btn_send.setStyleSheet("QPushButton { background: #10B981; color: #FFFFFF; border-radius: 18px; font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }")
            self.input_url.clear()
        else:
            self.btn_send.setText("ОШИБКА ОТПРАВКИ")
            self.btn_send.setStyleSheet("QPushButton { background: #EF4444; color: #FFFFFF; border-radius: 18px; font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }")
        QTimer.singleShot(3000, lambda: [self.btn_send.setText("ПРОВЕРИТЬ"), self._apply_default_send_style()])

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.pos().y() <= 60: self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self._drag_pos is not None: self.move(e.globalPosition().toPoint() - self._drag_pos)
    def mouseReleaseEvent(self, e): self._drag_pos = None

class BgWidget(QWidget):
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(1.0, 1.0, float(self.width() - 2), float(self.height() - 2), 30.0, 30.0)
        p.fillPath(path, QColor("#0A0A0C"))
        p.strokePath(path, QPen(QColor("#1A1A1D"), 2))

class GeminiVPN(QWidget):
    def __init__(self, app_icon):
        super().__init__()
        self._app_icon = app_icon
        self._is_connected = False
        self._is_processing = False
        self._connect_timestamp = 0
        self.c_cur = [QColor(c) for c in AppConfig.GRADIENT_OFF]
        self._promo_visible = False

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)
        self.setWindowIcon(self._app_icon)

        self.bg_widget = BgWidget(self)
        self.bg_widget.setFixedSize(self.width(), self.height())
        self.content_widget = QWidget(self.bg_widget)
        self.content_widget.setFixedSize(self.width(), self.height())
        
        self.block_overlay = QWidget(self.bg_widget)
        self.block_overlay.setFixedSize(self.width(), self.height())
        self.block_overlay.setStyleSheet("background: transparent;")
        self.block_overlay.hide()

        self.promo_win = PromoDialog()
        self.promo_win.closed_signal.connect(self._remove_blur)

        self._build_ui()
        self._setup_tray()

        self.timer = QTimer(self); self.timer.timeout.connect(self._update_timer_label); self.timer.start(1000)
        self.check_timer = QTimer(self); self.check_timer.timeout.connect(self._check_status_loop); self.check_timer.start(3000)

        self._init_state()

    def _show_promo(self):
        if self._promo_visible: return
        self._promo_visible = True
        geom = self.frameGeometry()
        
        self.block_overlay.show(); self.block_overlay.raise_()
        self.blur_effect = QGraphicsBlurEffect(self.content_widget)
        self.content_widget.setGraphicsEffect(self.blur_effect)
        
        self.blur_anim = QVariantAnimation(self)
        self.blur_anim.setDuration(300)
        self.blur_anim.setStartValue(0.0)
        self.blur_anim.setEndValue(15.0)
        self.blur_anim.valueChanged.connect(lambda v: self.blur_effect.setBlurRadius(float(v)))
        self.blur_anim.start()
        
        self.promo_win.show_animated(QPoint(geom.left() + (geom.width() - self.promo_win.width()) // 2, geom.top() + (geom.height() - self.promo_win.height()) // 2))

    def _remove_blur(self):
        self._promo_visible = False
        self.block_overlay.hide()
        self.blur_anim = QVariantAnimation(self)
        self.blur_anim.setDuration(250)
        self.blur_anim.setStartValue(15.0)
        self.blur_anim.setEndValue(0.0)
        self.blur_anim.valueChanged.connect(lambda v: self.blur_effect.setBlurRadius(float(v)))
        self.blur_anim.finished.connect(lambda: self.content_widget.setGraphicsEffect(None))
        self.blur_anim.start()

    def _build_ui(self):
        root = QVBoxLayout(self.content_widget)
        root.setContentsMargins(0, 0, 0, 0)

        self.bar = QWidget()
        self.bar.setFixedHeight(60)
        bar_l = QHBoxLayout(self.bar)
        bar_l.setContentsMargins(25, 10, 20, 0)
        title = QLabel("GEMINIVPN")
        title.setStyleSheet("color: #555; font-size: 10px; font-weight: 900; letter-spacing: 2px;")
        min_btn = ControlBtn("M5 12h14", "#555555", "#FFFFFF")
        close_btn = ControlBtn("M18 6L6 18M6 6l12 12", "#555555", "#FF4444")
        min_btn.clicked.connect(self.showMinimized); close_btn.clicked.connect(self.hide)
        bar_l.addWidget(title); bar_l.addStretch(); bar_l.addWidget(min_btn); bar_l.addSpacing(6); bar_l.addWidget(close_btn)
        root.addWidget(self.bar)

        self.logo = QSvgWidget()
        self.logo.setFixedSize(90, 90)
        self._draw_logo()
        root.addSpacing(10); root.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_stat = QLabel("ОТКЛЮЧЕНО")
        self.lbl_stat.setFixedSize(250, 40)
        self.lbl_stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stat.setStyleSheet("color: #666; font-size: 14px; font-weight: 700; margin-top: 15px;")
        root.addWidget(self.lbl_stat, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setFixedSize(250, 45)
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet("color: rgba(255, 255, 255, 0); font-size: 32px; font-weight: 300;")
        root.addWidget(self.lbl_time, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addStretch()

        bottom_lyt = QVBoxLayout()
        bottom_lyt.setContentsMargins(25, 0, 25, 25)
        bottom_lyt.setSpacing(10)

        self.btn_main = QPushButton("ПОДКЛЮЧИТЬСЯ")
        self.btn_main.setFixedSize(310, 58)
        self.btn_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_main.clicked.connect(self._handle_main_btn)
        bottom_lyt.addWidget(self.btn_main)

        self.btn_update = QPushButton("ОБНОВИТЬ БАЗУ")
        self.btn_update.setFixedSize(310, 58)
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.clicked.connect(self._handle_update_btn)
        self.btn_update.setVisible(False)
        bottom_lyt.addWidget(self.btn_update)

        h_btn_lyt = QHBoxLayout(); h_btn_lyt.setContentsMargins(0, 0, 0, 0); h_btn_lyt.setSpacing(10)
        
        self.btn_promo = QPushButton()
        self.btn_promo.setFixedSize(150, 58)
        self.btn_promo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_promo.clicked.connect(self._show_promo)
        p_lyt = QHBoxLayout(self.btn_promo); p_lyt.setContentsMargins(0,0,0,0); p_lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p_lyt.addWidget(self._create_icon_lbl(GIFT_SVG, "БОНУС"))

        self.btn_donate = QPushButton()
        self.btn_donate.setFixedSize(150, 58)
        self.btn_donate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.donationalerts.com/r/verloft")))
        d_lyt = QHBoxLayout(self.btn_donate); d_lyt.setContentsMargins(0,0,0,0); d_lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_lyt.addWidget(self._create_icon_lbl(HEART_SVG, "ДОНАТ"))

        h_btn_lyt.addWidget(self.btn_promo); h_btn_lyt.addWidget(self.btn_donate)
        bottom_lyt.addLayout(h_btn_lyt); root.addLayout(bottom_lyt)
        self._update_style()

    def _create_icon_lbl(self, svg_str, text):
        w = QWidget(); w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(6)
        svg = QSvgWidget(); svg.setFixedSize(18, 18); svg.load(QByteArray(svg_str.format(color="#888888").encode()))
        lbl = QLabel(text); lbl.setStyleSheet("color: #888888; font-size: 13px; font-weight: 800; background: transparent;")
        l.addWidget(svg); l.addWidget(lbl)
        return w

    def _draw_logo(self): self.logo.load(QByteArray(LOGO_SVG.format(c1=self.c_cur[0].name(), c2=self.c_cur[1].name(), c3=self.c_cur[2].name()).encode()))

    def _update_style(self):
        btn_tpl = "QPushButton {{ background: {bg}; color: {tc}; border-radius: 18px; font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }} QPushButton:hover {{ background: {hbg}; }} QPushButton:pressed {{ background: {pbg}; }} QPushButton:disabled {{ background: #333333; color: #888888; }}"
        if self._is_processing: styles = ("#333333", "#888888", "#333333", "#333333")
        elif self._is_connected: styles = ("#10B981", "#FFFFFF", "#059669", "#047857")
        else: styles = ("#121214", "#A0A0A0", "#1A1A1D", "#0A0A0C")
        self.btn_main.setStyleSheet(btn_tpl.format(bg=styles[0], tc=styles[1], hbg=styles[2], pbg=styles[3]))
        self.btn_update.setStyleSheet(btn_tpl.format(bg="#1BA1E3", tc="#FFFFFF", hbg="#147EAF", pbg="#0F6085"))
        self.btn_donate.setStyleSheet(btn_tpl.format(bg="#121214", tc="#888888", hbg="#1A1A1D", pbg="#0A0A0C"))
        self.btn_promo.setStyleSheet(btn_tpl.format(bg="#121214", tc="#888888", hbg="#1A1A1D", pbg="#0A0A0C"))

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self); self.tray.setIcon(self._app_icon)
        self.menu = QMenu(); self.menu.setStyleSheet("QMenu { background: #0A0A0C; color: #A0A0A0; border: 1px solid #1A1A1D; } QMenu::item:selected { background: #1A1A1D; color: #FFF; }")
        self.show_act = QAction("Открыть", self); self.show_act.triggered.connect(self._show_me)
        self.toggle_act = QAction("Подключиться", self); self.toggle_act.triggered.connect(self._handle_main_btn)
        self.timer_act = QAction("Время: 00:00:00", self); self.timer_act.setEnabled(False); self.timer_act.setVisible(False)
        self.exit_act = QAction("Выход", self); self.exit_act.triggered.connect(QApplication.quit)
        for act in [self.show_act, self.toggle_act, self.timer_act]: self.menu.addAction(act)
        self.menu.addSeparator(); self.menu.addAction(self.exit_act)
        self.tray.setContextMenu(self.menu); self.tray.activated.connect(lambda r: self._show_me() if r in (2,3) else None); self.tray.show()

    def handle_second_instance(self): self._show_me()
    def _show_me(self): self.showNormal(); self.activateWindow(); self.raise_()

    def _init_state(self):
        if check_installation():
            self._is_connected = True
            try: self._connect_timestamp = os.path.getmtime(HOSTS_PATH)
            except: self._connect_timestamp = time.time()
            self._set_ui_connected()
        else:
            self._set_ui_disconnected()

    def _check_status_loop(self):
        if self._is_processing: return
        actual_state = check_installation()
        if actual_state != self._is_connected:
            self._is_connected = actual_state
            self._connect_timestamp = os.path.getmtime(HOSTS_PATH) if actual_state else 0
            self._set_ui_connected() if actual_state else self._set_ui_disconnected()

    def _handle_main_btn(self):
        if self._is_processing: return
        self._is_processing = True
        self._toggle_ui_lock(True)
        
        if self._is_connected:
            self.lbl_stat.setText("ОТКЛЮЧЕНИЕ..."); self.btn_main.setText("ОТКЛЮЧЕНИЕ...")
            self.worker = HostsWorker("uninstall")
        else:
            self.lbl_stat.setText("ПОДКЛЮЧЕНИЕ..."); self.btn_main.setText("ПОДКЛЮЧЕНИЕ...")
            self.worker = HostsWorker("install")
            
        self.lbl_stat.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;")
        self._anim_logo_to(AppConfig.GRADIENT_CONN)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _handle_update_btn(self):
        if self._is_processing: return
        self._is_processing = True
        self._toggle_ui_lock(True)
        self.btn_update.setText("ОБНОВЛЕНИЕ..."); self.lbl_stat.setText("ОБНОВЛЕНИЕ БАЗЫ...")
        self.lbl_stat.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;")
        self._anim_logo_to(AppConfig.GRADIENT_CONN)
        self.worker = HostsWorker("update")
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _toggle_ui_lock(self, locked):
        self.btn_main.setEnabled(not locked); self.btn_update.setEnabled(not locked); self.toggle_act.setEnabled(not locked)
        if locked: self._anim_opac(False); self.timer_act.setVisible(False)
        self._update_style()

    def _on_worker_finished(self, success, msg):
        self._is_processing = False
        self._toggle_ui_lock(False)
        self.btn_update.setText("ОБНОВИТЬ БАЗУ")
        
        if success:
            if msg in ("install", "update"):
                self._is_connected = True
                self._connect_timestamp = time.time()
                self._set_ui_connected()
            else:
                self._is_connected = False
                self._set_ui_disconnected()
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить действие:\n{msg}")
            self._check_status_loop()

    def _set_ui_connected(self):
        self.btn_main.setText("ОТКЛЮЧИТЬСЯ"); self.lbl_stat.setText("ПОДКЛЮЧЕНО"); self.toggle_act.setText("Отключиться")
        self.btn_update.setVisible(True); self.lbl_stat.setStyleSheet("color: #10B981; font-size: 14px; font-weight: 700; margin-top: 15px;")
        if not self._is_processing: self.timer_act.setVisible(True); self._anim_opac(True)
        self._anim_logo_to(AppConfig.GRADIENT_ON); self._update_style(); self._update_timer_label()

    def _set_ui_disconnected(self):
        self.btn_main.setText("ПОДКЛЮЧИТЬСЯ"); self.lbl_stat.setText("ОТКЛЮЧЕНО"); self.toggle_act.setText("Подключиться")
        self.btn_update.setVisible(False); self.lbl_stat.setStyleSheet("color: #666; font-size: 14px; font-weight: 700; margin-top: 15px;")
        self.timer_act.setVisible(False); self._anim_opac(False)
        self._anim_logo_to(AppConfig.GRADIENT_OFF); self._update_style()

    def _update_timer_label(self):
        if not self._is_connected or self._is_processing: return
        diff = max(0, int(time.time() - self._connect_timestamp))
        t_str = f"{diff // 3600:02d}:{(diff % 3600) // 60:02d}:{diff % 60:02d}"
        self.lbl_time.setText(t_str); self.timer_act.setText(f"Время: {t_str}")

    def _anim_logo_to(self, e_grad):
        self.a_col = QVariantAnimation(self)
        self.a_col.setDuration(400); self.a_col.setStartValue(0.0); self.a_col.setEndValue(1.0)
        s_grad = [QColor(c) for c in self.c_cur]
        def step(v):
            for i in range(3): self.c_cur[i] = QColor(int(s_grad[i].red() + (e_grad[i].red() - s_grad[i].red()) * v), int(s_grad[i].green() + (e_grad[i].green() - s_grad[i].green()) * v), int(s_grad[i].blue() + (e_grad[i].blue() - s_grad[i].blue()) * v))
            self._draw_logo()
        self.a_col.valueChanged.connect(step); self.a_col.start()

    def _anim_opac(self, show):
        self.a_op = QVariantAnimation(self)
        self.a_op.setDuration(250); self.a_op.setStartValue(float(self.lbl_time.palette().color(self.lbl_time.foregroundRole()).alpha()))
        self.a_op.setEndValue(255.0 if show else 0.0)
        self.a_op.valueChanged.connect(lambda a: self.lbl_time.setStyleSheet(f"color: rgba(255, 255, 255, {max(0, min(255, int(a)))}); font-size: 32px; font-weight: 300;"))
        self.a_op.start()

    def closeEvent(self, e): e.ignore(); self.hide()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.pos().y() <= 60: self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if getattr(self, "_drag_pos", None): self.move(e.globalPosition().toPoint() - self._drag_pos)
    def mouseReleaseEvent(self, e): self._drag_pos = None

def main():
    if sys.platform == "win32" and not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return 0

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    if sys.platform == "win32":
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("geminivpn.golden.alpha")
        except: pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    instance = SingleInstance(AppConfig.INSTANCE_LOCK_KEY)
    if instance.is_running:
        sock = QLocalSocket(); sock.connectToServer(AppConfig.INSTANCE_LOCK_KEY)
        if sock.waitForConnected(500): sock.write(b"show"); sock.waitForBytesWritten(500)
        return 0

    icon_file = get_resource_path("icon.ico")
    app_icon = QIcon(icon_file) if os.path.exists(icon_file) else app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon)
    app.setWindowIcon(app_icon)

    window = GeminiVPN(app_icon)
    instance.show_requested.connect(window.handle_second_instance)
    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())