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
import json
import hashlib
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
    except Exception:
        pass
    try:
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Критическая ошибка. Лог: {log_file}\n\n{error_msg[:500]}",
                "GeminiVPN Error",
                0x10,
            )
    except Exception:
        pass


sys.excepthook = global_exception_handler

try:
    from PyQt6.QtCore import (
        Qt,
        QTimer,
        QVariantAnimation,
        pyqtSignal,
        QByteArray,
        QThread,
        QUrl,
        QObject,
    )
    from PyQt6.QtGui import (
        QColor,
        QPainter,
        QPainterPath,
        QPen,
        QIcon,
        QAction,
        QDesktopServices,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QSystemTrayIcon,
        QMenu,
        QMessageBox,
        QLineEdit,
        QGraphicsBlurEffect,
    )
    from PyQt6.QtSvgWidgets import QSvgWidget
    from PyQt6.QtNetwork import QLocalServer, QLocalSocket
except ImportError as _imp_err:
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Не удалось импортировать PyQt6.\n{_imp_err}",
                "GeminiVPN Error",
                0x10,
            )
        except Exception:
            pass
    sys.exit(1)

HOSTS_PATH = (
    r"C:\Windows\System32\drivers\etc\hosts"
    if sys.platform == "win32"
    else "/etc/hosts"
)

DEFAULT_HOSTS = (
    "# Copyright (c) 1993-2009 Microsoft Corp.\n"
    "#\n"
    "# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.\n"
    "#\n"
    "# This file contains the mappings of IP addresses to host names. Each\n"
    "# entry should be kept on an individual line. The IP address should\n"
    "# be placed in the first column followed by the corresponding host name.\n"
    "# The IP address and the host name should be separated by at least one\n"
    "# space.\n"
    "#\n"
    "# Additionally, comments (such as these) may be inserted on individual\n"
    "# lines or following the machine name denoted by a '#' symbol.\n"
    "#\n"
    "# For example:\n"
    "#\n"
    "#      102.54.94.97     rhino.acme.com          # source server\n"
    "#       38.25.63.10     x.acme.com              # x client host\n"
    "\n"
    "# localhost name resolution is handled within DNS itself.\n"
    "#\t127.0.0.1       localhost\n"
    "#\t::1             localhost\n"
)

HOSTS_URL = "https://raw.githubusercontent.com/ImMALWARE/dns.malw.link/refs/heads/master/hosts"
ADD_HOSTS_URL = "https://raw.githubusercontent.com/AvenCores/Goida-AI-Unlocker/refs/heads/main/additional_hosts.py"
HOSTS_MARKER = "dns.malw.link"

LOGO_SVG = (
    '<svg viewBox="0 0 11 11" xmlns="http://www.w3.org/2000/svg">'
    "<defs>"
    '<linearGradient id="g" x1="1" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="{c1}"/>'
    '<stop offset="35%" stop-color="{c2}"/>'
    '<stop offset="67%" stop-color="{c3}"/>'
    "</linearGradient>"
    "</defs>"
    '<path fill="url(#g)" d="M9,1C7.488,1,5.4077,2.1459,4.0488,4H3'
    "C2.1988,4,1.8162,4.3675,1.5,5L1,6h1h1l1,1l1,1v1v1l1-0.5"
    " C6.6325,9.1838,7,8.8012,7,8V6.9512C8.8541,5.5923,10,3.512,10,2V1H9z"
    " M7.5,3C7.7761,3,8,3.2239,8,3.5S7.7761,4,7.5,4"
    ' S7,3.7761,7,3.5S7.2239,3,7.5,3z M2.75,7.25L2.5,7.5C2,8,2,9,2,9s0.9448,0.0552,1.5-0.5l0.25-0.25L2.75,7.25z"/>'
    "</svg>"
)

CTRL_SVG = (
    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
    '<path d="{path}" stroke="{color}" stroke-width="2.5" '
    'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    "</svg>"
)

HEART_SVG = (
    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 '
    "2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 "
    "16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 "
    '21.35z" fill="{color}"/>'
    "</svg>"
)

GIFT_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M5 12H19V17.8C19 18.9201 19 19.4802 18.782 19.908'
    "C18.5903 20.2843 18.2843 20.5903 17.908 20.782C17.4802 21 "
    "16.9201 21 15.8 21H8.2C7.07989 21 6.51984 21 6.09202 20.782"
    "C5.71569 20.5903 5.40973 20.2843 5.21799 19.908C5 19.4802 5 "
    "18.9201 5 17.8V12ZM4.6 12H19.4C19.9601 12 20.2401 12 20.454 "
    "11.891C20.6422 11.7951 20.7951 11.6422 20.891 11.454C21 "
    "11.2401 21 10.9601 21 10.4V8.6C21 8.03995 21 7.75992 20.891 "
    "7.54601C20.7951 7.35785 20.6422 7.20487 20.454 7.10899"
    "C20.2401 7 19.9601 7 19.4 7H4.6C4.03995 7 3.75992 7 3.54601 "
    "7.10899C3.35785 7.20487 3.20487 7.35785 3.10899 7.54601C3 "
    '7.75992 3 8.03995 3 8.6V10.4C3 10.9601 3 11.2401 3.10899 11.454'
    "C3.20487 11.6422 3.35785 11.7951 3.54601 11.891C3.75992 12 "
    '4.03995 12 4.6 12Z" fill="{color}"/>'
    '<path d="M12 7V20M12 7H8.46429C7.94332 7 7.4437 6.78929 '
    "7.07533 6.41421C6.70695 6.03914 6.5 5.53043 6.5 5C6.5 4.46957 "
    "6.70695 3.96086 7.07533 3.58579C7.4437 3.21071 7.94332 3 "
    "8.46429 3C11.2143 3 12 7 12 7ZM12 7H15.5357C16.0567 7 16.5563 "
    "6.78929 16.9247 6.41421C17.293 6.03914 17.5 5.53043 17.5 5"
    "C17.5 4.46957 17.293 3.96086 16.9247 3.58579C16.5563 3.21071 "
    '16.0567 3 15.5357 3C12.7857 3 12 7 12 7Z" stroke="{color}" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg>"
)

PROMO_WEBHOOK_URL = "https://formspree.io/f/xjgpezvd"
VERSION = "0.8.0-alpha"


class AppConfig:
    APP_NAME = "GeminiVPN"
    INSTANCE_LOCK_KEY = "geminivpn_instance_v8_alpha"
    WINDOW_WIDTH = 360
    WINDOW_HEIGHT = 600
    GRADIENT_OFF = [QColor("#9168C0"), QColor("#5684D1"), QColor("#1BA1E3")]
    GRADIENT_ON = [QColor("#10B981"), QColor("#059669"), QColor("#047857")]
    GRADIENT_CONN = [QColor("#F59E0B"), QColor("#D97706"), QColor("#B45309")]
    CACHE_DIR = (
        Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GeminiVPN_Cache"
    )
    CACHE_FILE = CACHE_DIR / "hosts_cache.txt"
    CACHE_HASH_FILE = CACHE_DIR / "hosts_cache.md5"
    CACHE_MAX_AGE = 3600
    REQUEST_COOLDOWN = 15


def get_resource_path(relative_path):
    try:
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        pass
    return os.path.join(os.path.abspath("."), relative_path)


def check_installation():
    try:
        if not os.path.exists(HOSTS_PATH):
            return False
        with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if HOSTS_MARKER not in content:
            return False
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 2 and not parts[0].startswith("#"):
                return True
        return False
    except Exception:
        return False


def safe_remove(path):
    for _attempt in range(3):
        try:
            if path and os.path.exists(path):
                os.chmod(path, 0o777)
                os.remove(path)
            return
        except Exception:
            time.sleep(0.1)


def file_hash(filepath):
    try:
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def cache_is_fresh():
    try:
        if not AppConfig.CACHE_FILE.exists():
            return False
        age = time.time() - AppConfig.CACHE_FILE.stat().st_mtime
        return age < AppConfig.CACHE_MAX_AGE
    except Exception:
        return False


def flush_dns_sync():
    try:
        if sys.platform == "win32":
            cf = subprocess.CREATE_NO_WINDOW
            subprocess.run(
                ["ipconfig", "/flushdns"], capture_output=True, timeout=15, creationflags=cf
            )
            subprocess.run(
                [
                    "powershell",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    "Clear-DnsClientCache",
                ],
                capture_output=True,
                timeout=10,
                creationflags=cf,
            )
            subprocess.run(
                ["ipconfig", "/release"], capture_output=True, timeout=20, creationflags=cf
            )
            subprocess.run(
                ["ipconfig", "/renew"], capture_output=True, timeout=30, creationflags=cf
            )
            subprocess.run(
                ["netsh", "winsock", "reset"], capture_output=True, timeout=15, creationflags=cf
            )
        else:
            subprocess.run(
                "resolvectl flush-caches 2>/dev/null || "
                "systemd-resolve --flush-caches 2>/dev/null || "
                "/etc/init.d/nscd restart 2>/dev/null || "
                "killall -HUP dnsmasq 2>/dev/null || true",
                shell=True,
                timeout=10,
                capture_output=True,
            )
    except Exception:
        pass


def verify_hosts_written(expected_content_has_marker):
    for _attempt in range(5):
        try:
            with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
                current = f.read()
            if expected_content_has_marker:
                if HOSTS_MARKER in current:
                    return True
            else:
                if HOSTS_MARKER not in current:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


class SingleInstance(QObject):
    show_requested = pyqtSignal()

    def __init__(self, key):
        super().__init__()
        self.key = key
        self.server = None
        self.is_running = False
        socket = QLocalSocket()
        socket.connectToServer(self.key)
        self.is_running = socket.waitForConnected(500)
        socket.disconnectFromServer()
        socket.deleteLater()
        if not self.is_running:
            QLocalServer.removeServer(self.key)
            self.server = QLocalServer(self)
            self.server.listen(self.key)
            self.server.newConnection.connect(self._handle_connection)

    def _handle_connection(self):
        try:
            client = self.server.nextPendingConnection()
            if client:
                client.waitForReadyRead(500)
                client.disconnectFromServer()
                client.deleteLater()
                self.show_requested.emit()
        except Exception:
            pass


class PromoWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, link):
        super().__init__()
        self.link = link

    def run(self):
        try:
            if not PROMO_WEBHOOK_URL:
                self.finished_signal.emit(False, "Webhook URL не настроен")
                return
            data = json.dumps({"video_link": self.link}).encode("utf-8")
            req = urllib.request.Request(
                PROMO_WEBHOOK_URL,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            )
            urllib.request.urlopen(req, timeout=10)
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class HostsWorker(QThread):
    finished_signal = pyqtSignal(bool, str)
    _last_network_request = 0
    _lock = threading.Lock()

    def __init__(self, action):
        super().__init__()
        self.action = action

    def run(self):
        try:
            AppConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            if self.action in ("install", "update"):
                self._install()
            else:
                self._uninstall()
        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def _download_hosts(self):
        req1 = urllib.request.Request(
            f"{HOSTS_URL}?t={int(time.time())}",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        content = urllib.request.urlopen(req1, timeout=20).read().decode("utf-8", errors="ignore")
        try:
            req2 = urllib.request.Request(
                f"{ADD_HOSTS_URL}?t={int(time.time())}",
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )
            add_raw = urllib.request.urlopen(req2, timeout=20).read().decode("utf-8", errors="ignore")
            if 'hosts_add = """' in add_raw:
                add_block = add_raw.split('hosts_add = """')[1].split('"""')[0].strip()
                if add_block:
                    content += f"\n{add_block}\n"
        except Exception:
            pass
        return content

    def _save_cache(self, content):
        try:
            tmp_cache = str(AppConfig.CACHE_FILE) + ".tmp"
            with open(tmp_cache, "w", encoding="utf-8") as f:
                f.write(content)
            if os.path.exists(str(AppConfig.CACHE_FILE)):
                safe_remove(str(AppConfig.CACHE_FILE))
            os.rename(tmp_cache, str(AppConfig.CACHE_FILE))
            digest = hashlib.md5(content.encode("utf-8")).hexdigest()
            with open(str(AppConfig.CACHE_HASH_FILE), "w", encoding="utf-8") as f:
                f.write(digest)
        except Exception:
            pass

    def _read_cache(self):
        with open(AppConfig.CACHE_FILE, "r", encoding="utf-8") as f:
            return f.read()

    def _apply_hosts(self, content_path):
        s_path = None
        bat_path = None
        alt_path = None
        try:
            if sys.platform == "win32":
                with open(content_path, "r", encoding="utf-8") as check_f:
                    check_data = check_f.read()
                if not check_data.strip():
                    raise Exception("Пустой файл для записи в hosts")
                hosts_dir = os.path.dirname(HOSTS_PATH)
                backup_path = os.path.join(hosts_dir, "hosts.geminivpn.bak")
                ps_lines = [
                    f"try {{ Copy-Item -LiteralPath '{HOSTS_PATH}' -Destination '{backup_path}' -Force -ErrorAction SilentlyContinue }} catch {{}}",
                    f"$srcContent = [System.IO.File]::ReadAllText('{content_path}', [System.Text.Encoding]::UTF8)",
                    f"[System.IO.File]::WriteAllText('{HOSTS_PATH}', $srcContent, (New-Object System.Text.UTF8Encoding $false))",
                    f"$written = [System.IO.File]::ReadAllText('{HOSTS_PATH}', [System.Text.Encoding]::UTF8)",
                    f"if ($written.Length -lt 10) {{ Copy-Item -LiteralPath '{backup_path}' -Destination '{HOSTS_PATH}' -Force; throw 'Write verification failed' }}",
                    "try { Clear-DnsClientCache } catch {}",
                    "ipconfig /flushdns | Out-Null",
                    "try { Register-DnsClient 2>$null } catch {}",
                ]
                ps_cmd = "\n".join(ps_lines)
                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ps1", encoding="utf-8") as pf:
                    pf.write(ps_cmd)
                    s_path = pf.name
                bat_content = (
                    "@echo off\n"
                    f'powershell -NoProfile -ExecutionPolicy Bypass -File "{s_path}"\n'
                    "exit /b %errorlevel%\n"
                )
                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".bat", encoding="utf-8") as bf:
                    bf.write(bat_content)
                    bat_path = bf.name
                cmd = [
                    "powershell",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    f"Start-Process cmd -Verb runAs -WindowStyle Hidden -ArgumentList '/c \"{bat_path}\"' -Wait",
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=45,
                )
                if result.returncode != 0:
                    alt_ps = (
                        f"Copy-Item -LiteralPath '{content_path}' -Destination '{HOSTS_PATH}' -Force; "
                        "ipconfig /flushdns | Out-Null"
                    )
                    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ps1", encoding="utf-8") as pf2:
                        pf2.write(alt_ps)
                        alt_path = pf2.name
                    cmd2 = [
                        "powershell",
                        "-WindowStyle",
                        "Hidden",
                        "-Command",
                        f"Start-Process powershell -Verb runAs -WindowStyle Hidden "
                        f"-ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{alt_path}\"' -Wait",
                    ]
                    subprocess.run(
                        cmd2,
                        check=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=45,
                    )
                time.sleep(0.5)
                flush_dns_sync()
            else:
                fc = (
                    "resolvectl flush-caches 2>/dev/null || "
                    "systemd-resolve --flush-caches 2>/dev/null || "
                    "/etc/init.d/nscd restart 2>/dev/null || "
                    "killall -HUP dnsmasq 2>/dev/null || true"
                )
                if os.geteuid() == 0:
                    shutil.copy2(content_path, HOSTS_PATH)
                    os.chmod(HOSTS_PATH, 0o644)
                    subprocess.run(fc, shell=True, timeout=10)
                else:
                    bc = f"cp '{content_path}' '{HOSTS_PATH}' && chmod 644 '{HOSTS_PATH}' && {fc}"
                    subprocess.run(["pkexec", "bash", "-c", bc], check=True, timeout=30)
        finally:
            if s_path:
                safe_remove(s_path)
            if bat_path:
                safe_remove(bat_path)
            if alt_path:
                safe_remove(alt_path)

    def _install(self):
        current_time = time.time()
        need_download = self.action == "update" or not cache_is_fresh()
        content = None

        if need_download:
            acquired = HostsWorker._lock.acquire(timeout=30)
            if acquired:
                try:
                    cooldown_ok = (
                        current_time - HostsWorker._last_network_request
                    ) >= AppConfig.REQUEST_COOLDOWN
                    if cooldown_ok:
                        HostsWorker._last_network_request = time.time()
                        content = self._download_hosts()
                        if content and content.strip() and HOSTS_MARKER in content:
                            self._save_cache(content)
                        else:
                            content = None
                except Exception:
                    content = None
                finally:
                    HostsWorker._lock.release()
            if content is None and AppConfig.CACHE_FILE.exists():
                try:
                    content = self._read_cache()
                except Exception:
                    content = None
            if content is None:
                self.finished_signal.emit(False, "Ошибка сети и кэш пуст.")
                return
        else:
            if AppConfig.CACHE_FILE.exists():
                try:
                    content = self._read_cache()
                except Exception:
                    content = None
            if content is None:
                self.finished_signal.emit(False, "Кэш отсутствует.")
                return

        if not content or not content.strip():
            self.finished_signal.emit(False, "Полученные данные пусты.")
            return

        if HOSTS_MARKER not in content:
            self.finished_signal.emit(False, "Данные повреждены — маркер отсутствует.")
            return

        t_fd, t_path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(t_fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)

            existing_hash = file_hash(HOSTS_PATH)
            new_hash = file_hash(t_path)
            if existing_hash and new_hash and existing_hash == new_hash:
                if check_installation():
                    self.finished_signal.emit(True, self.action)
                    return

            self._apply_hosts(t_path)

            if not verify_hosts_written(True):
                self._apply_hosts(t_path)
                if not verify_hosts_written(True):
                    self.finished_signal.emit(
                        False, "Не удалось записать в hosts после двух попыток."
                    )
                    return

            flush_dns_sync()
            self.finished_signal.emit(True, self.action)
        except subprocess.CalledProcessError:
            self.finished_signal.emit(False, "Операция отменена пользователем (UAC).")
        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, "Превышено время ожидания операции.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            safe_remove(t_path)

    def _uninstall(self):
        t_fd, t_path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(t_fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(DEFAULT_HOSTS)

            existing_hash = file_hash(HOSTS_PATH)
            new_hash = file_hash(t_path)
            if existing_hash and new_hash and existing_hash == new_hash:
                if not check_installation():
                    self.finished_signal.emit(True, "uninstall")
                    return

            self._apply_hosts(t_path)

            if not verify_hosts_written(False):
                self._apply_hosts(t_path)
                if not verify_hosts_written(False):
                    self.finished_signal.emit(
                        False, "Не удалось очистить hosts после двух попыток."
                    )
                    return

            flush_dns_sync()
            self.finished_signal.emit(True, "uninstall")
        except subprocess.CalledProcessError:
            self.finished_signal.emit(False, "Операция отменена пользователем (UAC).")
        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, "Превышено время ожидания операции.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            safe_remove(t_path)


class ControlBtn(QWidget):
    clicked = pyqtSignal()

    def __init__(self, path_d, normal_hex, hover_hex):
        super().__init__()
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path_d = path_d
        self.normal_hex = normal_hex
        self.hover_hex = hover_hex
        self._hovered = False
        self.setStyleSheet(
            "QWidget { border: 2px solid #1A1A1D; border-radius: 8px; background: transparent; } "
            "QWidget:hover { background: #1A1A1D; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.svg = QSvgWidget()
        self.svg.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.svg)
        self._render(self.normal_hex)

    def _render(self, color):
        try:
            data = CTRL_SVG.format(path=self.path_d, color=color)
            self.svg.load(QByteArray(data.encode()))
        except Exception:
            pass

    def enterEvent(self, e):
        self._hovered = True
        self._render(self.hover_hex)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._render(self.normal_hex)
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._hovered:
            self.clicked.emit()
        super().mouseReleaseEvent(e)


class PromoDialog(QWidget):
    closed_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 400)
        self.worker = None
        self._drag_pos = None
        self._build_ui()

    def hideEvent(self, e):
        self.closed_signal.emit()
        super().hideEvent(e)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 30)

        self.bar = QWidget()
        self.bar.setFixedHeight(60)
        bar_l = QHBoxLayout(self.bar)
        bar_l.setContentsMargins(25, 10, 20, 0)

        title = QLabel("БОНУС ЗА ПРОДВИЖЕНИЕ")
        title.setStyleSheet(
            "color: #1BA1E3; font-size: 10px; font-weight: 900; letter-spacing: 1px;"
        )

        close_btn = ControlBtn("M18 6L6 18M6 6l12 12", "#555555", "#FF4444")
        close_btn.clicked.connect(self.hide)

        bar_l.addWidget(title)
        bar_l.addStretch()
        bar_l.addWidget(close_btn)
        root.addWidget(self.bar)

        content_l = QVBoxLayout()
        content_l.setContentsMargins(25, 10, 25, 10)

        lbl_desc = QLabel("Помогите продвинуть наш проект,\nа мы отблагодарим вас наградой!")
        lbl_desc.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_l.addWidget(lbl_desc)

        lbl_terms = QLabel(
            "Опубликуйте короткое видео про GeminiVPN\n"
            "в TikTok или YouTube Shorts и прикрепите\n"
            "ссылку на публикацию ниже. После\n"
            "проверки вы получите вознаграждение."
        )
        lbl_terms.setStyleSheet("color: #888888; font-size: 12px; font-weight: 500;")
        lbl_terms.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_l.addWidget(lbl_terms)

        content_l.addStretch()

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Вставьте ссылку на видео...")
        self.input_url.setFixedHeight(50)
        self.input_url.setStyleSheet(
            "QLineEdit { background: #121214; color: #FFFFFF; border-radius: 12px; "
            "border: 2px solid #1A1A1D; padding: 0 15px; font-size: 13px; font-weight: 600; } "
            "QLineEdit:focus { border: 2px solid #1BA1E3; }"
        )
        content_l.addWidget(self.input_url)

        self.btn_send = QPushButton("ПРОВЕРИТЬ")
        self.btn_send.setFixedSize(310, 58)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_default_send_style()
        self.btn_send.clicked.connect(self._send_promo)
        content_l.addWidget(self.btn_send)

        root.addLayout(content_l)

    def _apply_default_send_style(self):
        self.btn_send.setStyleSheet(
            "QPushButton { background: #1BA1E3; color: #FFFFFF; border-radius: 18px; "
            "font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; } "
            "QPushButton:hover { background: #147EAF; } "
            "QPushButton:pressed { background: #0F6085; } "
            "QPushButton:disabled { background: #333333; color: #888888; }"
        )

    def paintEvent(self, e):
        p = QPainter()
        p.begin(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(
                1.0, 1.0, float(self.width() - 2), float(self.height() - 2), 30.0, 30.0
            )
            p.fillPath(path, QColor("#0A0A0C"))
            p.strokePath(path, QPen(QColor("#1A1A1D"), 2))
        finally:
            p.end()

    def _send_promo(self):
        link = self.input_url.text().strip()
        if not link:
            return
        self.btn_send.setEnabled(False)
        self.btn_send.setText("ОТПРАВКА...")
        self.worker = PromoWorker(link)
        self.worker.finished_signal.connect(self._on_sent)
        self.worker.start()

    def _on_sent(self, success, msg):
        self.btn_send.setEnabled(True)
        if success:
            self.btn_send.setText("УСПЕШНО ОТПРАВЛЕНО")
            self.btn_send.setStyleSheet(
                "QPushButton { background: #10B981; color: #FFFFFF; border-radius: 18px; "
                "font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }"
            )
            self.input_url.clear()
        else:
            self.btn_send.setText("ОШИБКА ОТПРАВКИ")
            self.btn_send.setStyleSheet(
                "QPushButton { background: #EF4444; color: #FFFFFF; border-radius: 18px; "
                "font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }"
            )
        QTimer.singleShot(3000, self._reset_btn)

    def _reset_btn(self):
        try:
            self.btn_send.setText("ПРОВЕРИТЬ")
            self._apply_default_send_style()
        except RuntimeError:
            pass

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.pos().y() <= 60:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)


class BgWidget(QWidget):
    def paintEvent(self, e):
        p = QPainter()
        p.begin(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(
                1.0, 1.0, float(self.width() - 2), float(self.height() - 2), 30.0, 30.0
            )
            p.fillPath(path, QColor("#0A0A0C"))
            p.strokePath(path, QPen(QColor("#1A1A1D"), 2))
        finally:
            p.end()


class GeminiVPN(QWidget):
    def __init__(self, app_icon):
        super().__init__()
        self._app_icon = app_icon
        self._is_connected = False
        self._is_processing = False
        self._drag_pos = None
        self._connect_timestamp = 0
        self.c_cur = [QColor(c) for c in AppConfig.GRADIENT_OFF]
        self.worker = None
        self.donate_url = "https://www.donationalerts.com/r/verloft"
        self.blur_effect = None
        self.blur_anim = None
        self.a_col = None
        self.a_op = None
        self._time_alpha = 0
        self._second_instance_handled = False
        self._promo_visible = False
        self._selfheal_counter = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)
        self.setWindowIcon(self._app_icon)

        self.bg_widget = BgWidget(self)
        self.bg_widget.setFixedSize(self.width(), self.height())
        self.bg_widget.move(0, 0)

        self.content_widget = QWidget(self.bg_widget)
        self.content_widget.setFixedSize(self.width(), self.height())
        self.content_widget.move(0, 0)

        self.block_overlay = QWidget(self.bg_widget)
        self.block_overlay.setFixedSize(self.width(), self.height())
        self.block_overlay.setStyleSheet("background: transparent;")
        self.block_overlay.hide()
        self.block_overlay.raise_()

        self.promo_win = PromoDialog()
        self.promo_win.closed_signal.connect(self._remove_blur)

        self._build_ui()
        self._setup_tray()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer_label)
        self.timer.start(1000)

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_status_loop)
        self.check_timer.start(3000)

        self.selfheal_timer = QTimer(self)
        self.selfheal_timer.timeout.connect(self._selfheal_check)
        self.selfheal_timer.start(10000)

        self._init_state()

        QTimer.singleShot(500, self._show_promo)

    def _selfheal_check(self):
        if self._is_processing:
            return
        try:
            if self._is_connected:
                if not check_installation():
                    self._selfheal_counter += 1
                    if self._selfheal_counter >= 2:
                        self._selfheal_counter = 0
                        self._is_connected = False
                        self._connect_timestamp = 0
                        self._set_ui_disconnected()
                else:
                    self._selfheal_counter = 0
            else:
                if check_installation():
                    self._is_connected = True
                    self._connect_timestamp = self._get_hosts_mtime()
                    self._set_ui_connected()
                self._selfheal_counter = 0
            if (
                self.btn_main.text()
                in ("ПОДКЛЮЧЕНИЕ...", "ОТКЛЮЧЕНИЕ...", "ОБНОВЛЕНИЕ...")
                and not self._is_processing
            ):
                actual = check_installation()
                if actual:
                    self._is_connected = True
                    self._set_ui_connected()
                else:
                    self._is_connected = False
                    self._set_ui_disconnected()
                self.btn_main.setEnabled(True)
                self.btn_update.setEnabled(True)
                self.toggle_act.setEnabled(True)
        except Exception:
            pass

    def _show_promo(self):
        if self._promo_visible:
            return
        self._promo_visible = True
        geom = self.frameGeometry()
        center_x = geom.left() + (geom.width() - self.promo_win.width()) // 2
        center_y = geom.top() + (geom.height() - self.promo_win.height()) // 2
        self.promo_win.move(center_x, center_y)
        self.block_overlay.show()
        self.block_overlay.raise_()
        self._stop_blur_anim()
        self.blur_effect = QGraphicsBlurEffect(self.content_widget)
        self.blur_effect.setBlurRadius(0.0)
        self.content_widget.setGraphicsEffect(self.blur_effect)
        self.blur_anim = QVariantAnimation(self)
        self.blur_anim.setDuration(250)
        self.blur_anim.setStartValue(0.0)
        self.blur_anim.setEndValue(15.0)
        self.blur_anim.valueChanged.connect(self._apply_blur_radius)
        self.blur_anim.start()
        self.promo_win.show()

    def _apply_blur_radius(self, value):
        try:
            if self.blur_effect is not None:
                self.blur_effect.setBlurRadius(float(value))
        except RuntimeError:
            pass

    def _stop_blur_anim(self):
        if self.blur_anim is not None:
            try:
                self.blur_anim.stop()
                self.blur_anim.deleteLater()
            except RuntimeError:
                pass
            self.blur_anim = None

    def _remove_blur(self):
        self._promo_visible = False
        self.block_overlay.hide()
        self._stop_blur_anim()
        if self.blur_effect is None:
            return
        self.blur_anim = QVariantAnimation(self)
        self.blur_anim.setDuration(250)
        try:
            self.blur_anim.setStartValue(self.blur_effect.blurRadius())
        except RuntimeError:
            self.blur_anim.setStartValue(15.0)
        self.blur_anim.setEndValue(0.0)
        self.blur_anim.valueChanged.connect(self._apply_blur_radius)
        self.blur_anim.finished.connect(self._finalize_remove_blur)
        self.blur_anim.start()

    def _finalize_remove_blur(self):
        try:
            if self.blur_effect is not None:
                self.blur_effect.setEnabled(False)
            self.content_widget.setGraphicsEffect(None)
        except RuntimeError:
            pass
        self.blur_effect = None
        self._stop_blur_anim()

    def _build_ui(self):
        root = QVBoxLayout(self.content_widget)
        root.setContentsMargins(0, 0, 0, 0)

        self.bar = QWidget()
        self.bar.setFixedHeight(60)
        bar_l = QHBoxLayout(self.bar)
        bar_l.setContentsMargins(25, 10, 20, 0)

        title = QLabel("GEMINIVPN")
        title.setStyleSheet(
            "color: #555; font-size: 10px; font-weight: 900; letter-spacing: 2px;"
        )

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
        self.lbl_stat.setFixedSize(250, 40)
        self.lbl_stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stat.setStyleSheet(
            "color: #666; font-size: 14px; font-weight: 700; margin-top: 15px;"
        )
        root.addWidget(self.lbl_stat, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setFixedSize(250, 45)
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet(
            "color: rgba(255, 255, 255, 0); font-size: 32px; font-weight: 300;"
        )
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

        h_btn_lyt = QHBoxLayout()
        h_btn_lyt.setContentsMargins(0, 0, 0, 0)
        h_btn_lyt.setSpacing(10)

        self.btn_promo = QPushButton()
        self.btn_promo.setFixedSize(150, 58)
        self.btn_promo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_promo.clicked.connect(self._show_promo)

        p_container = QWidget()
        p_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        p_lyt = QHBoxLayout(p_container)
        p_lyt.setContentsMargins(0, 0, 0, 0)
        p_lyt.setSpacing(6)

        p_svg = QSvgWidget()
        p_svg.setFixedSize(18, 18)
        p_svg.load(QByteArray(GIFT_SVG.format(color="#888888").encode()))
        p_svg.setStyleSheet("background: transparent; border: none;")

        p_lbl = QLabel("БОНУС")
        p_lbl.setStyleSheet(
            "color: #888888; font-size: 13px; font-weight: 800; background: transparent;"
        )

        p_lyt.addWidget(p_svg)
        p_lyt.addWidget(p_lbl)

        promo_main_lyt = QHBoxLayout(self.btn_promo)
        promo_main_lyt.setContentsMargins(0, 0, 0, 0)
        promo_main_lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        promo_main_lyt.addWidget(p_container)

        self.btn_donate = QPushButton()
        self.btn_donate.setFixedSize(150, 58)
        self.btn_donate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_donate.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self.donate_url))
        )

        d_container = QWidget()
        d_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        d_lyt = QHBoxLayout(d_container)
        d_lyt.setContentsMargins(0, 0, 0, 0)
        d_lyt.setSpacing(6)

        h_svg = QSvgWidget()
        h_svg.setFixedSize(18, 18)
        h_svg.load(QByteArray(HEART_SVG.format(color="#888888").encode()))
        h_svg.setStyleSheet("background: transparent; border: none;")

        d_lbl = QLabel("ДОНАТ")
        d_lbl.setStyleSheet(
            "color: #888888; font-size: 13px; font-weight: 800; background: transparent;"
        )

        d_lyt.addWidget(h_svg)
        d_lyt.addWidget(d_lbl)

        donate_main_lyt = QHBoxLayout(self.btn_donate)
        donate_main_lyt.setContentsMargins(0, 0, 0, 0)
        donate_main_lyt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donate_main_lyt.addWidget(d_container)

        h_btn_lyt.addWidget(self.btn_promo)
        h_btn_lyt.addWidget(self.btn_donate)

        bottom_lyt.addLayout(h_btn_lyt)
        root.addLayout(bottom_lyt)

        self._update_style()

    def _draw_logo(self):
        try:
            d = LOGO_SVG.format(
                c1=self.c_cur[0].name(), c2=self.c_cur[1].name(), c3=self.c_cur[2].name()
            )
            self.logo.load(QByteArray(d.encode()))
        except Exception:
            pass

    def _update_style(self):
        btn_tpl = (
            "QPushButton {{ background: {bg}; color: {tc}; border-radius: 18px; "
            "font-weight: 800; font-size: 13px; border: 2px solid #1A1A1D; }} "
            "QPushButton:hover {{ background: {hbg}; }} "
            "QPushButton:pressed {{ background: {pbg}; }} "
            "QPushButton:disabled {{ background: #333333; color: #888888; }}"
        )

        if self._is_processing:
            m_bg, m_tc, m_hbg, m_pbg = "#333333", "#888888", "#333333", "#333333"
        elif self._is_connected:
            m_bg, m_tc, m_hbg, m_pbg = "#10B981", "#FFFFFF", "#059669", "#047857"
        else:
            m_bg, m_tc, m_hbg, m_pbg = "#121214", "#A0A0A0", "#1A1A1D", "#0A0A0C"

        self.btn_main.setStyleSheet(btn_tpl.format(bg=m_bg, tc=m_tc, hbg=m_hbg, pbg=m_pbg))
        self.btn_update.setStyleSheet(
            btn_tpl.format(bg="#1BA1E3", tc="#FFFFFF", hbg="#147EAF", pbg="#0F6085")
        )
        self.btn_donate.setStyleSheet(
            btn_tpl.format(bg="#121214", tc="#888888", hbg="#1A1A1D", pbg="#0A0A0C")
        )
        self.btn_promo.setStyleSheet(
            btn_tpl.format(bg="#121214", tc="#888888", hbg="#1A1A1D", pbg="#0A0A0C")
        )

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self._app_icon)
        self.menu = QMenu()
        self.menu.setStyleSheet(
            "QMenu { background: #0A0A0C; color: #A0A0A0; border: 1px solid #1A1A1D; } "
            "QMenu::item:selected { background: #1A1A1D; color: #FFF; }"
        )

        self.show_act = QAction("Открыть", self)
        self.show_act.triggered.connect(self._show_me)

        self.toggle_act = QAction("Подключиться", self)
        self.toggle_act.triggered.connect(self._handle_main_btn)

        self.timer_act = QAction("Время: 00:00:00", self)
        self.timer_act.setEnabled(False)
        self.timer_act.setVisible(False)

        self.exit_act = QAction("Выход", self)
        self.exit_act.triggered.connect(self._safe_quit)

        self.menu.addAction(self.show_act)
        self.menu.addAction(self.toggle_act)
        self.menu.addAction(self.timer_act)
        self.menu.addSeparator()
        self.menu.addAction(self.exit_act)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _safe_quit(self):
        try:
            self.timer.stop()
            self.check_timer.stop()
            self.selfheal_timer.stop()
        except Exception:
            pass
        QApplication.quit()

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_me()

    def handle_second_instance(self):
        if self._second_instance_handled:
            self._show_me()
            return
        self._second_instance_handled = True
        self.show_act.setText("Закрыть")
        try:
            self.show_act.triggered.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.show_act.triggered.connect(self._safe_quit)
        self._show_me()

    def _show_me(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _init_state(self):
        if check_installation():
            self._is_connected = True
            self._connect_timestamp = self._get_hosts_mtime()
            self._set_ui_connected()
        else:
            self._is_connected = False
            self._connect_timestamp = 0
            self._set_ui_disconnected()

    def _get_hosts_mtime(self):
        try:
            return os.path.getmtime(HOSTS_PATH)
        except Exception:
            return 0

    def _check_status_loop(self):
        if self._is_processing:
            return
        try:
            st = check_installation()
            if st and not self._is_connected:
                self._is_connected = True
                self._connect_timestamp = self._get_hosts_mtime()
                self._set_ui_connected()
            elif not st and self._is_connected:
                self._is_connected = False
                self._connect_timestamp = 0
                self._set_ui_disconnected()
        except Exception:
            pass

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
            self.lbl_stat.setStyleSheet(
                "color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;"
            )
            self._anim_logo_to(AppConfig.GRADIENT_CONN)
            self.worker = HostsWorker("uninstall")
        else:
            self.btn_main.setText("ПОДКЛЮЧЕНИЕ...")
            self.lbl_stat.setText("ПОДКЛЮЧЕНИЕ...")
            self.lbl_stat.setStyleSheet(
                "color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;"
            )
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
        self.lbl_stat.setStyleSheet(
            "color: #F59E0B; font-size: 14px; font-weight: 700; margin-top: 15px;"
        )
        self._anim_logo_to(AppConfig.GRADIENT_CONN)

        self.worker = HostsWorker("update")
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self, success, msg):
        self._is_processing = False
        self.btn_main.setEnabled(True)
        self.btn_update.setEnabled(True)
        self.toggle_act.setEnabled(True)
        self.btn_update.setText("ОБНОВИТЬ БАЗУ")

        actual_state = check_installation()

        if success:
            if msg in ("install", "update"):
                if actual_state:
                    self._is_connected = True
                    self._connect_timestamp = time.time()
                    self._set_ui_connected()
                    flush_dns_sync()
                else:
                    self._is_connected = False
                    self._connect_timestamp = 0
                    self._set_ui_disconnected()
                    try:
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            "Запись в hosts прошла, но проверка не подтвердила изменения.\n"
                            "Попробуйте ещё раз.",
                        )
                    except Exception:
                        pass
            else:
                if not actual_state:
                    self._is_connected = False
                    self._connect_timestamp = 0
                    self._set_ui_disconnected()
                    flush_dns_sync()
                else:
                    self._is_connected = True
                    self._set_ui_connected()
                    try:
                        QMessageBox.warning(
                            self,
                            "Внимание",
                            "Отключение завершилось, но hosts всё ещё содержит записи.\n"
                            "Попробуйте ещё раз.",
                        )
                    except Exception:
                        pass
        else:
            try:
                QMessageBox.warning(self, "Информация", f"Статус операции: {msg}")
            except Exception:
                pass
            if actual_state:
                self._is_connected = True
                if self._connect_timestamp == 0:
                    self._connect_timestamp = self._get_hosts_mtime()
                self._set_ui_connected()
            else:
                self._is_connected = False
                self._connect_timestamp = 0
                self._set_ui_disconnected()

    def _set_ui_connected(self):
        self.btn_main.setText("ОТКЛЮЧИТЬСЯ")
        self.lbl_stat.setText("ПОДКЛЮЧЕНО")
        self.btn_update.setVisible(True)
        self.lbl_stat.setStyleSheet(
            "color: #10B981; font-size: 14px; font-weight: 700; margin-top: 15px;"
        )
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
        self.lbl_stat.setStyleSheet(
            "color: #666; font-size: 14px; font-weight: 700; margin-top: 15px;"
        )
        self.toggle_act.setText("Подключиться")
        self.timer_act.setVisible(False)
        self._anim_opac(False)
        self._anim_logo_to(AppConfig.GRADIENT_OFF)
        self._update_style()

    def _update_timer_label(self):
        if not self._is_connected or self._is_processing:
            return
        try:
            if self._connect_timestamp > 0:
                diff = max(0, int(time.time() - self._connect_timestamp))
            else:
                diff = 0
            t_str = f"{diff // 3600:02d}:{(diff % 3600) // 60:02d}:{diff % 60:02d}"
            self.lbl_time.setText(t_str)
            self.timer_act.setText(f"Время: {t_str}")
        except Exception:
            pass

    def _anim_logo_to(self, target_gradient):
        if self.a_col is not None:
            try:
                self.a_col.stop()
                self.a_col.deleteLater()
            except RuntimeError:
                pass
            self.a_col = None
        start_colors = [QColor(c) for c in self.c_cur]
        self.a_col = QVariantAnimation(self)
        self.a_col.setDuration(400)
        self.a_col.setStartValue(0.0)
        self.a_col.setEndValue(1.0)
        self.a_col.valueChanged.connect(
            lambda v, s=start_colors, e=target_gradient: self._step_logo(v, s, e)
        )
        self.a_col.start()

    def _step_logo(self, v, s, e):
        try:
            for i in range(3):
                r = max(0, min(255, int(s[i].red() + (e[i].red() - s[i].red()) * v)))
                g = max(0, min(255, int(s[i].green() + (e[i].green() - s[i].green()) * v)))
                b = max(0, min(255, int(s[i].blue() + (e[i].blue() - s[i].blue()) * v)))
                self.c_cur[i] = QColor(r, g, b)
            self._draw_logo()
        except Exception:
            pass

    def _anim_opac(self, show):
        if self.a_op is not None:
            try:
                self.a_op.stop()
                self.a_op.deleteLater()
            except RuntimeError:
                pass
            self.a_op = None
        self.a_op = QVariantAnimation(self)
        self.a_op.setDuration(250)
        self.a_op.setStartValue(float(self._time_alpha))
        self.a_op.setEndValue(255.0 if show else 0.0)
        self.a_op.valueChanged.connect(self._set_time_alpha)
        self.a_op.start()

    def _set_time_alpha(self, a):
        try:
            self._time_alpha = max(0, min(255, int(a)))
            self.lbl_time.setStyleSheet(
                f"color: rgba(255, 255, 255, {self._time_alpha}); font-size: 32px; font-weight: 300;"
            )
        except Exception:
            pass

    def closeEvent(self, e):
        e.ignore()
        self.hide()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.pos().y() <= 60:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)


def main():
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "geminivpn.v8.alpha"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    instance = SingleInstance(AppConfig.INSTANCE_LOCK_KEY)
    if instance.is_running:
        sock = QLocalSocket()
        sock.connectToServer(AppConfig.INSTANCE_LOCK_KEY)
        if sock.waitForConnected(500):
            sock.write(b"show")
            sock.waitForBytesWritten(500)
            sock.disconnectFromServer()
        sock.deleteLater()
        return 0

    icon_file = get_resource_path("icon.ico")
    if os.path.exists(icon_file):
        app_icon = QIcon(icon_file)
    else:
        app_icon = app.style().standardIcon(
            app.style().StandardPixmap.SP_ComputerIcon
        )

    app.setWindowIcon(app_icon)

    window = GeminiVPN(app_icon)
    instance.show_requested.connect(window.handle_second_instance)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
