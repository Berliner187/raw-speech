import math
import pyperclip
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, QDialog, QSizePolicy,
                             QPushButton, QScrollArea, QLineEdit, QHBoxLayout, QFrame, QGridLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPainterPath, QPen, QFont
import styles


class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setStyleSheet("background: white; border: 1px solid #E5E5E7; border-radius: 20px;")
        f_layout = QVBoxLayout(self.frame)
        f_layout.setContentsMargins(30, 30, 30, 30)
        f_layout.setSpacing(20)

        msg = QLabel("Удалить эту запись?")
        msg.setStyleSheet("font-weight: 800; font-size: 16px; color: #000; border: none;")
        msg.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(msg)

        btns = QHBoxLayout()
        self.no_btn = QPushButton("Отмена")
        self.no_btn.setStyleSheet("QPushButton { background: #F2F2F7; color: #000; border-radius: 12px; padding: 12px; font-weight: 700; border: none; } QPushButton:hover { background: #E5E5E7; }")
        self.yes_btn = QPushButton("Удалить")
        self.yes_btn.setStyleSheet("QPushButton { background: #FF3B30; color: white; border-radius: 12px; padding: 12px; font-weight: 700; border: none; } QPushButton:hover { background: #D32F2F; }")
        
        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)
        btns.addWidget(self.no_btn)
        btns.addWidget(self.yes_btn)
        f_layout.addLayout(btns)
        layout.addWidget(self.frame)


class BarChart(QWidget):
    """ Гистограмма с ховером """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(160)
        self.data = [0] * 7
        self.days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
        self.hovered_idx = -1
        self.setMouseTracking(True) 

    def set_data(self, data):
        self.data = data
        self.update()

    def mouseMoveEvent(self, event):
        w = self.width() - 40
        step = w / 7
        idx = int((event.x() - 20) // step)
        if 0 <= idx < 7:
            if self.hovered_idx != idx:
                self.hovered_idx = idx
                self.update()
        else:
            self.hovered_idx = -1
            self.update()

    def leaveEvent(self, event):
        self.hovered_idx = -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        m = 30 # Отступы
        max_val = max(self.data) if max(self.data) > 0 else 1
        
        chart_w = w - m*2
        chart_h = h - m*2
        bar_w = (chart_w / 7) * 0.6
        gap = (chart_w / 7) * 0.4
        
        for i, val in enumerate(self.data):
            bh = (val / max_val) * chart_h
            bx = m + i * (bar_w + gap) + gap/2
            by = h - m - bh
            
            rect = QRectF(bx, by, bar_w, bh)
            
            color = QColor("#FFCC00") if i == self.hovered_idx or i == 6 else QColor("#E5E5E7")
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(rect, 5, 5)
            
            p.setPen(QColor("#8E8E93"))
            p.setFont(QFont("SF Pro Display", 9, QFont.Bold))
            p.drawText(QRectF(bx - gap/2, h - 20, bar_w + gap, 20), Qt.AlignCenter, self.days[i])
            
            if i == self.hovered_idx:
                p.setPen(QColor("#000"))
                p.drawText(QRectF(bx - 20, by - 20, bar_w + 40, 20), Qt.AlignCenter, str(int(val)))


class LinearChart(QWidget):
    """
        ГРАФИК ТРЕНДА
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(130)
        self.data = [0] * 7

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self.data or max(self.data) == 0:
            p.setPen(QColor("#D1D1D6"))
            p.drawLine(20, h/2, w-20, h/2)
            return

        max_val = max(self.data)
        step = (w - 40) / (len(self.data) - 1)
        path = QPainterPath()
        
        for i, val in enumerate(self.data):
            x = 20 + i * step
            y = h - (val / max_val * (h - 40)) - 20
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)

        fill = QPainterPath(path)
        fill.lineTo(w-20, h)
        fill.lineTo(20, h)
        p.setBrush(QColor(0, 122, 255, 15))
        p.setPen(Qt.NoPen)
        p.drawPath(fill)

        p.setPen(QPen(QColor("#007AFF"), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)


class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(12)
        self.value = 0.0

    def set_value(self, val):
        self.value = max(0.01, min(1.0, val))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        p.setBrush(QColor("#F2F2F7"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 6, 6)
        
        p.setBrush(QColor("#34C759"))
        p.drawRoundedRect(0, 0, self.width() * self.value, self.height(), 6, 6)


class HistoryItem(QFrame):
    def __init__(self, text, dt, main_win):
        super().__init__()
        self.setObjectName("Card")
        self.full_text = text
        self.dt = dt
        self.main_win = main_win
        self.is_collapsed = True
        
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        self.setMinimumWidth(10)
        self.setStyleSheet("QFrame#Card { background: #FFFFFF; border: 1px solid #E5E5E7; border-radius: 18px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        date_lbl = QLabel(dt)
        date_lbl.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: 700; border: none;")
        
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(22, 22)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("QPushButton { color: #FF3B30; border: none; font-weight: 900; background: transparent; } QPushButton:hover { background: #FFE5E5; border-radius: 11px; }")
        del_btn.clicked.connect(lambda: self.main_win.delete_requested(self.full_text, self.dt))
        
        header.addWidget(date_lbl)
        header.addStretch()
        header.addWidget(del_btn)
        layout.addLayout(header)

        # Content
        self.content_lbl = QLabel(text)
        self.content_lbl.setWordWrap(True)
        self.content_lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        self.content_lbl.setMinimumWidth(10)
        self.content_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.content_lbl.setStyleSheet("color: #1D1D1F; font-size: 14px; line-height: 1.5; border: none;")
        self.content_lbl.setMaximumHeight(60) 
        layout.addWidget(self.content_lbl)

        # Footer
        footer = QHBoxLayout()
        self.copy_btn = QPushButton("КОПИРОВАТЬ")
        self.expand_btn = QPushButton("РАЗВЕРНУТЬ")
        btn_style = "QPushButton { background: #F2F2F7; color: #007AFF; border-radius: 10px; padding: 8px 16px; font-size: 11px; font-weight: 800; border: none; } QPushButton:hover { background: #E5E5E7; }"
        self.copy_btn.setStyleSheet(btn_style)
        self.expand_btn.setStyleSheet(btn_style)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_text)
        self.expand_btn.clicked.connect(self.toggle_expand)
        
        footer.addWidget(self.copy_btn)
        footer.addStretch()
        footer.addWidget(self.expand_btn)
        layout.addLayout(footer)

    def toggle_expand(self):
        if self.is_collapsed:
            self.content_lbl.setMaximumHeight(10000)
            self.expand_btn.setText("СВЕРНУТЬ")
        else:
            self.content_lbl.setMaximumHeight(60)
            self.expand_btn.setText("РАЗВЕРНУТЬ")
        self.is_collapsed = not self.is_collapsed

    def copy_text(self):
        pyperclip.copy(self.full_text)
        orig = self.copy_btn.text()
        self.copy_btn.setText("✓ ГОТОВО")
        self.copy_btn.setStyleSheet("QPushButton { background: #34C759; color: white; border-radius: 10px; padding: 8px 16px; font-size: 11px; font-weight: 800; border: none; }")
        QTimer.singleShot(1000, lambda: self.reset_copy_btn(orig))

    def reset_copy_btn(self, text):
        self.copy_btn.setText(text)
        self.copy_btn.setStyleSheet("QPushButton { background: #F2F2F7; color: #007AFF; border-radius: 10px; padding: 8px 16px; font-size: 11px; font-weight: 800; border: none; } QPushButton:hover { background: #E5E5E7; }")


class MainWindow(QMainWindow):
    def __init__(self, db, model_name):
        super().__init__()
        self.setWindowFlags(
            Qt.Window | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint | 
            Qt.WindowSystemMenuHint | 
            Qt.WindowMinMaxButtonsHint | 
            Qt.WindowCloseButtonHint
        )
        
        self.setUnifiedTitleAndToolBarOnMac(True)
        
        self.db = db
        self.model_name = model_name
        self.setWindowTitle("Голосок")
        self.resize(440, 800)
        self.setStyleSheet(styles.QSS)

        self.central = QWidget()
        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Nav
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(25, 20, 25, 10)
        self.btn_dash = QPushButton("БОРД", objectName="NavBtn")
        self.btn_hist = QPushButton("ИСТОРИЯ", objectName="NavBtn")
        self.btn_dash.clicked.connect(lambda: self.switch_page(0))
        self.btn_hist.clicked.connect(lambda: self.switch_page(1))
        nav_layout.addWidget(self.btn_dash)
        nav_layout.addWidget(self.btn_hist)
        self.main_layout.addLayout(nav_layout)

        self.container = QWidget()
        self.clayout = QVBoxLayout(self.container)
        self.clayout.setContentsMargins(0,0,0,0)

        self.page_dash = self.setup_dash()
        self.page_hist = self.setup_hist()
        
        self.clayout.addWidget(self.page_dash)
        self.clayout.addWidget(self.page_hist)
        self.main_layout.addWidget(self.container)

        self.setCentralWidget(self.central)
        self.switch_page(0)
        self.refresh()

    def switch_page(self, idx):
        self.page_dash.setVisible(idx == 0)
        self.page_hist.setVisible(idx == 1)
        self.btn_dash.setStyleSheet("border-bottom: 2px solid #007AFF; color: #000;" if idx == 0 else "color: #8E8E93;")
        self.btn_hist.setStyleSheet("border-bottom: 2px solid #007AFF; color: #000;" if idx == 1 else "color: #8E8E93;")

    def add_stat(self, grid, label, value, r, c, rs, cs, is_main=False):
        container = QFrame()
        bg = "#000" if is_main else "#F2F2F7"
        color = "#FFF" if is_main else "#000"
        container.setStyleSheet(f"background: {bg}; border-radius: 20px;")
        l = QVBoxLayout(container)
        l.setContentsMargins(12, 12, 12, 12)
        
        v = QLabel(value)
        v.setStyleSheet(f"font-size: {'32px' if is_main else '24px'}; font-weight: 200; color: {color}; border:none;")
        txt = QLabel(label)
        txt.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {'#AAA' if is_main else '#8E8E93'}; letter-spacing: 1px;")
        
        l.addWidget(v, alignment=Qt.AlignLeft)
        l.addWidget(txt, alignment=Qt.AlignLeft)
        grid.addWidget(container, r, c, rs, cs)
        return v

    def setup_dash(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(25, 15, 25, 25)
        l.setSpacing(20)

        # 1. СИСТЕМА
        h = QHBoxLayout()
        h.addWidget(QLabel("АНАЛИТИКА ГОЛОСКА", styleSheet="font-size: 10px; font-weight: 800; color: #8E8E93; letter-spacing: 1px;"))
        h.addStretch()
        m_lbl = QLabel(self.model_name.split('/')[-1].upper())
        m_lbl.setStyleSheet("background: #F2F2F7; color: #555; padding: 4px 10px; border-radius: 6px; font-size: 9px; font-weight: 800;")
        h.addWidget(m_lbl)
        l.addLayout(h)

        # 2. HERO BENTO GRID
        grid = QGridLayout()
        grid.setSpacing(12)
        self.m_hours = self.add_stat(grid, "ЧАСОВ СЭКОНОМЛЕНО", "0.0", 0, 0, 1, 3, is_main=True)
        self.m_speed = self.add_stat(grid, "МОЩНОСТЬ", "0.0x", 1, 0, 1, 1)
        self.m_audio = self.add_stat(grid, "НАГОВОРИЛИ", "0.0 мин", 1, 1, 1, 1)
        self.m_words = self.add_stat(grid, "СЛОВ", "0", 1, 2, 1, 1)
        self.m_count = self.add_stat(grid, "ВСЕГО ЗАМЕТОК", "0", 2, 0, 1, 1)
        self.m_avg   = self.add_stat(grid, "СР. ДЛИНА", "0 зн", 2, 1, 1, 1)
        self.m_intens = self.add_stat(grid, "ЗАМЕТОК В ДЕНЬ", "0.0", 2, 2, 1, 1)
        l.addLayout(grid)

        # 3. ГРАФИК АКТИВНОСТИ 
        chart_box = QFrame()
        chart_box.setStyleSheet("background: #FFFFFF; border: 1px solid #E5E5E7; border-radius: 20px;")
        cl = QVBoxLayout(chart_box)
        cl.setContentsMargins(15, 15, 15, 15)
        
        chart_header = QLabel("НЕДЕЛЬНАЯ АКТИВНОСТЬ (символы)")
        chart_header.setStyleSheet("font-size: 10px; font-weight: 800; color: #8E8E93; margin-bottom: 5px;")
        cl.addWidget(chart_header)
        
        self.bar_chart = BarChart()
        cl.addWidget(self.bar_chart)
        l.addWidget(chart_box)

        # 4. ДОПОЛНИТЕЛЬНАЯ МЕТРИКА: ЭФФЕКТИВНОСТЬ ДВИЖКА
        self.efficiency_box = QFrame()
        self.efficiency_box.setStyleSheet("background: #000; border-radius: 15px; padding: 15px;")
        el = QHBoxLayout(self.efficiency_box)
        etxt = QLabel("Ваш Мак обрабатывает речь умнее, чем вы думаете.")
        etxt.setStyleSheet("color: #F0FF00; font-weight: 800; font-size: 9px;")
        el.addWidget(etxt)
        l.addWidget(self.efficiency_box)

        l.addStretch()

        # 5. МАНИФЕСТ
        manifest = QFrame()
        manifest.setFixedHeight(45); manifest.setStyleSheet("background: #000; border-radius: 12px;")
        ml = QHBoxLayout(manifest); ml.setContentsMargins(15, 0, 15, 0)
        mt = QLabel("ГОЛОСОК ™2026"); mt.setStyleSheet("color: #F0FF00; font-weight: 900; font-size: 10px;")
        ma = QLabel("Design by Kozak"); ma.setStyleSheet("color: #8E8E93; font-size: 9px; font-weight: 700;")
        ml.addWidget(mt); ml.addStretch(); ml.addWidget(ma)
        l.addWidget(manifest)

        scroll.setWidget(content)
        return scroll

    def setup_hist(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(20, 10, 20, 15)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск по мыслям...")
        self.search_bar.setStyleSheet("QLineEdit { background: #F2F2F7; border: none; border-radius: 12px; padding: 12px 16px; font-size: 14px; color: #000; }")
        self.search_bar.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_bar)
        l.addWidget(search_container)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; }
            QScrollBar::handle:vertical { background: #D1D1D6; border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.hist_layout = QVBoxLayout(self.scroll_content)
        self.hist_layout.setAlignment(Qt.AlignTop)
        self.hist_layout.setContentsMargins(20, 0, 20, 30)
        self.hist_layout.setSpacing(15)
        
        self.scroll.setWidget(self.scroll_content)
        l.addWidget(self.scroll)
        return page

    def refresh(self):
        stats = self.db.get_stats()
        
        self.m_hours.setText(str(stats["hours"]))
        self.m_speed.setText(f"{stats['speed_factor']}x")
        self.m_audio.setText(str(stats["total_audio_min"]))
        self.m_words.setText(str(stats["words"]))
        self.m_count.setText(str(stats["count"]))
        self.m_avg.setText(str(stats["avg_len"]))
        self.m_intens.setText(str(stats["intensity"]))

        weekly_data = self.db.get_weekly_activity()
        self.bar_chart.set_data(weekly_data)

        while self.hist_layout.count():
            item = self.hist_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        query = self.search_bar.text()
        data = self.db.search(query) if query else self.db.get_all()
        for text, dt in data:
            self.hist_layout.addWidget(HistoryItem(text, dt, self))

    def delete_requested(self, text, dt):
        dialog = ConfirmDialog(self)
        if dialog.exec():
            self.db.delete_entry(dt)
            self.refresh()
