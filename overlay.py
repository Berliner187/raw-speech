import math
from PySide6.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPainterPath, QPen
import objc
from AppKit import NSWindow, NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorStationary, NSWindowCollectionBehaviorIgnoresCycle

class CenterOverlay(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus |
            Qt.ToolTip |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        screen = QApplication.primaryScreen().geometry()
        self.island_w, self.island_h = 220, 40
        self.y_offset = 45 
        self.setGeometry((screen.width() - self.island_w) // 2, self.y_offset, self.island_w, self.island_h)

        # Состояния
        self.state = 'hidden'
        self.rms, self.smooth_rms, self.phase = 0.0, 0.0, 0.0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)

        # Тень
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

    def showEvent(self, event):
        """Вызывается, когда окно показывается. Идеальное время для нативного хака."""
        super().showEvent(event)
        try:
            ptr = self.winId()
            view = objc.objc_object(c_void_p=ptr)
            ns_window = view.window()
            if ns_window:
                behavior = (NSWindowCollectionBehaviorCanJoinAllSpaces | 
                           NSWindowCollectionBehaviorStationary | 
                           NSWindowCollectionBehaviorIgnoresCycle)
                ns_window.setCollectionBehavior_(behavior)
                ns_window.setLevel_(20)
        except Exception as e:
            print(f"Space Hack Error: {e}")

    def set_recording(self):
        self.state = 'recording'
        self.timer.start(16)
        self.show()

    def set_processing(self):
        self.state = 'processing'
        self.smooth_rms = 0.0
        self.timer.start(16)
        self.show()

    def hide_overlay(self):
        self.state = 'hidden'
        self.timer.stop()
        self.hide()

    def set_rms(self, rms): self.rms = rms

    def update_animation(self):
        if self.state != 'hidden':
            self.smooth_rms += (self.rms - self.smooth_rms) * 0.15
            self.phase += 0.2
            self.update()
    
    def draw_wave(self, p, cx, cy, amplitude, speed_mult, frequency, opacity, stroke_w):
        path = QPainterPath()
        w_wave = self.width() - 30
        start_x = cx - w_wave / 2
        points = 80
        final_amp = min(14.0, amplitude * 450) 
        p.setPen(QPen(QColor(255, 255, 255, opacity), stroke_w, Qt.SolidLine, Qt.RoundCap))
        
        for i in range(points + 1):
            x = start_x + (i / points) * w_wave
            dist = abs(i / points - 0.5) * 2
            envelope = math.cos(dist * math.pi / 2) ** 2
            y_off = math.sin(i * frequency + self.phase * speed_mult) * final_amp * envelope
            if i == 0: path.moveTo(x, cy + y_off)
            else: path.lineTo(x, cy + y_off)
        p.drawPath(path)

    def paintEvent(self, event):
        if self.state == 'hidden': return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        p.setBrush(QColor(0, 0, 0, 245))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 20, 20)

        if self.state == 'recording':
            self.draw_wave(p, cx, cy, self.smooth_rms * 0.5, 1.0, 0.2, 100, 1)
            self.draw_wave(p, cx, cy, self.smooth_rms * 0.8, 1.5, 0.4, 180, 2)
            self.draw_wave(p, cx, cy, self.smooth_rms * 1.0, 2.2, 0.6, 255, 1.5)

        elif self.state == 'processing':
            p.setBrush(QColor(255, 255, 255))
            for i in range(3):
                off = math.sin(self.phase * 2.5 + i * 0.8) * 4
                radius = 3 + (off + 4) / 4
                dot_x = cx + (i - 1) * 15 
                p.drawEllipse(QPointF(dot_x, cy), radius, radius)