import sys
import os
import time
import pyperclip
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal
from pynput import keyboard
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle

from database import DB
from ui import MainWindow, ConfirmDialog
from engine import BoltEngine
from overlay import CenterOverlay

try:
    from Quartz import (CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap, 
                       CGEventSetFlags, kCGEventFlagMaskCommand)
    HAS_QUARTZ = True
except ImportError:
    HAS_QUARTZ = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(BASE_DIR, "models/whisper-medium-8bit")
HOTKEY = {keyboard.Key.alt, keyboard.Key.space}


class AppSignals(QObject):
    """ Мост для безопасной передачи команд 
        из фоновых потоков (клавиатура, нейросеть) в Главный поток UI 
    """
    start_rec = Signal()
    stop_rec = Signal()
    text_ready = Signal(str, float, float)


class BoltApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # 1. Инициализация системы сигналов
        self.signals = AppSignals()
        self.signals.start_rec.connect(self.ui_start_rec)
        self.signals.stop_rec.connect(self.ui_stop_rec)
        self.signals.text_ready.connect(self.ui_handle_text)
        
        # 2. БД и Окна
        self.db = DB()
        self.win = MainWindow(self.db, MODEL)
        self.overlay = CenterOverlay()
        
        # if self.db.is_first_launch(): # Реализуй проверку через COUNT(*) == 0
        #     intro = Onboarding(self.win)
        #     if intro.exec():
        #         print("Юзер согласился")

        # 3. Движок
        self.engine = BoltEngine(MODEL, self.signals.text_ready.emit, self.overlay.set_rms)
        
        # 4. Трей и иконки
        self.tray = QSystemTrayIcon(self)
        
        icon_idle_path = os.path.join(BASE_DIR, "assets/icon_tray.png")
        icon_rec_path = os.path.join(BASE_DIR, "assets/icon_tray_rec.png")
        
        if os.path.exists(icon_idle_path):
            self.icon_idle = QIcon(icon_idle_path)
            self.icon_rec = QIcon(icon_rec_path)
        else:
            self.icon_idle = self.style().standardIcon(QStyle.SP_ComputerIcon)
            self.icon_rec = self.style().standardIcon(QStyle.SP_MediaPlay)

        self.setWindowIcon(self.icon_idle)
        self.tray.setIcon(self.icon_idle)
        
        menu = QMenu()
        menu.addAction("Дашборд", self.win.show)
        menu.addAction("История", self.win.show)
        menu.addAction("Выход", self.quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

        # 5. Хоткеи
        self.kb_controller = keyboard.Controller()
        self.active_keys = set()
        self.shortcut_handled = False
        
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        self.active_keys.add(key)
        
        is_combo = all(k in self.active_keys for k in HOTKEY)
        
        if is_combo and not self.shortcut_handled:
            self.shortcut_handled = True
            
            if not self.engine.is_recording:
                self.signals.start_rec.emit()
            else:
                self.signals.stop_rec.emit()

    def on_release(self, key):
        if any(k in HOTKEY for k in[key]):
            self.shortcut_handled = False
        if key in self.active_keys:
            self.active_keys.remove(key)

    # --- ЭТИ ФУНКЦИИ РАБОТАЮТ СТРОГО В ГЛАВНОМ UI ПОТОКЕ ---
    def ui_start_rec(self):
        self.overlay.set_recording()
        os.system('afplay /System/Library/Sounds/Tink.aiff &')
        self.setWindowIcon(self.icon_rec)
        self.tray.setIcon(self.icon_rec)
        self.engine.start()

    def ui_stop_rec(self):
        os.system('afplay /System/Library/Sounds/Pop.aiff &')
        self.setWindowIcon(self.icon_idle)
        self.tray.setIcon(self.icon_idle)
        self.overlay.set_processing()
        self.engine.stop()

    def ui_handle_text(self, text, audio_len, proc_len):
        self.overlay.hide_overlay()
        QApplication.processEvents()
        
        if not text: 
            print("Пусто...")
            return
            
        self.db.add(text, audio_len, proc_len) 
        
        pyperclip.copy(text)
        
        time.sleep(0.1) 
        if HAS_QUARTZ:
            v_key = 0x09
            event_down = CGEventCreateKeyboardEvent(None, v_key, True)
            CGEventSetFlags(event_down, kCGEventFlagMaskCommand)
            event_up = CGEventCreateKeyboardEvent(None, v_key, False)
            CGEventSetFlags(event_up, kCGEventFlagMaskCommand)
            CGEventPost(kCGHIDEventTap, event_down)
            CGEventPost(kCGHIDEventTap, event_up)
        else:
            with self.kb_controller.pressed(keyboard.Key.cmd):
                self.kb_controller.tap('v')
            
        self.win.refresh()


if __name__ == "__main__":
    app = BoltApp(sys.argv)
    sys.exit(app.exec())
