import math
import pyperclip
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, QDialog, QSizePolicy, QApplication,
                             QPushButton, QScrollArea, QLineEdit, QHBoxLayout, QFrame, QGridLayout, QStackedWidget)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPainterPath, QPen, QFont
from PySide6.QtCore import QSize
import styles

import os
from PySide6.QtGui import QIcon


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

        msg = QLabel("УДАЛИТЬ ЭТУ ЗАПИСЬ?")
        msg.setStyleSheet("font-weight: 800; font-size: 16px; color: #22241E; border: none;")
        msg.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(msg)

        btns = QHBoxLayout()
        self.no_btn = QPushButton("ОТМЕНА")
        self.no_btn.setStyleSheet("QPushButton { background: #F2F2F7; color: #22241E; border-radius: 12px; padding: 12px; font-weight: 700; border: none; } QPushButton:hover { background: #E5E5E7; }")
        self.yes_btn = QPushButton("УДАЛИТЬ")
        self.yes_btn.setStyleSheet("QPushButton { background: #FF3B30; color: white; border-radius: 12px; padding: 12px; font-weight: 700; border: none; } QPushButton:hover { background: #D32F2F; }")
        
        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)
        btns.addWidget(self.no_btn); btns.addWidget(self.yes_btn)
        f_layout.addLayout(btns)
        layout.addWidget(self.frame)


class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(8)
        self.value = 0.0

    def set_value(self, val):
        self.value = max(0.0, min(1.0, val))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        
        p.setBrush(QColor("#E5E5EA"))
        p.drawRoundedRect(self.rect(), 4, 4)
        
        if self.value > 0:
            p.setBrush(QColor("#34C759"))
            bar_width = self.width() * self.value
            p.drawRoundedRect(0, 0, bar_width, self.height(), 4, 4)


class BarChart(QWidget):
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
        self.hovered_idx = idx if 0 <= idx < 7 else -1
        self.update()

    def leaveEvent(self, event):
        self.hovered_idx = -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h, m = self.width(), self.height(), 30
        max_val = max(self.data) if max(self.data) > 0 else 1
        cw, ch = w - m*2, h - m*2
        bw, gap = (cw / 7) * 0.6, (cw / 7) * 0.4
        
        for i, val in enumerate(self.data):
            bh = (val / max_val) * ch
            bx = m + i * (bw + gap) + gap/2
            by = h - m - bh
            color = QColor("#FFCC00") if i == self.hovered_idx or i == 6 else QColor("#E5E5E7")
            p.setBrush(color); p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(bx, by, bw, bh), 5, 5)
            p.setPen(QColor("#8E8E93"))
            p.drawText(QRectF(bx - gap/2, h - 20, bw + gap, 20), Qt.AlignCenter, self.days[i])
            if i == self.hovered_idx:
                p.setPen(QColor("#22241E"))
                p.drawText(QRectF(bx - 20, by - 25, bw + 40, 20), Qt.AlignCenter, str(int(val)))


class NavButton(QPushButton):
    def __init__(self, text, icon_path):
        super().__init__()
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet("""
            QPushButton { 
                background-color: transparent; border: none; border-radius: 8px; 
                text-align: left; padding-left: 45px; color: #1D1D1F; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.05); }
            QPushButton:checked { background-color: #007AFF; color: white; }
        """)

        self.setIcon(QIcon(icon_path))
        self.setText(text)


class ModelCard(QFrame):
    def __init__(self, m_data, main_win):
        super().__init__()
        self.m_data = m_data
        self.main_win = main_win
        self.setStyleSheet("QFrame { background: white; border: 1px solid #E5E5E7; border-radius: 18px; }")
        
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        
        # Header: Имя и Вес
        h = QHBoxLayout()
        name_lbl = QLabel(self.m_data['name'])
        name_lbl.setStyleSheet("font-weight: 900; font-size: 16px; color: #22241E; border: none; background: transparent;")
        
        size_lbl = QLabel(self.m_data['size'])
        size_lbl.setStyleSheet("color: #8E8E93; font-size: 10px; font-weight: 700; border: none; background: transparent;")
        
        h.addWidget(name_lbl); h.addStretch(); h.addWidget(size_lbl)
        l.addLayout(h)
        
        desc = QLabel(self.m_data['desc'])
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8E8E93; font-size: 12px; border: none; background: transparent; margin-top: 5px;")
        l.addWidget(desc)
        
        l.addSpacing(10)
        l.addWidget(self.create_stat_bar("СКОРОСТЬ", self.m_data['speed']))
        l.addWidget(self.create_stat_bar("ТОЧНОСТЬ", self.m_data['acc']))
        l.addSpacing(10)
        
        self.btn = QPushButton()
        self.btn.setFixedHeight(35)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.on_btn_clicked)
        self.update_btn_state()
        l.addWidget(self.btn)

    def update_btn_state(self):
        is_active = (self.main_win.model_name == self.m_data['path'])
        
        engine_loaded = False
        if hasattr(self.main_win, 'engine') and getattr(self.main_win, 'engine', None):
            engine_loaded = self.main_win.engine.model_loaded
        
        if not self.m_data['downloaded']:
            self.btn.setText(f"СКАЧАТЬ ({self.m_data['size']})")
            self.btn.setEnabled(True)
            self.btn.setStyleSheet("QPushButton { background: #007AFF; color: white; border-radius: 10px; font-weight: 800; border: none; }")
        elif is_active and engine_loaded:
            self.btn.setText("ИСПОЛЬЗУЕТСЯ")
            self.btn.setEnabled(False)
            self.btn.setStyleSheet("QPushButton { background: #F2F2F7; color: #8E8E93; border-radius: 10px; border: none; }")
        else:
            self.btn.setText("ВЫБРАТЬ")
            self.btn.setEnabled(True)
            self.btn.setStyleSheet("QPushButton { background: #22241E; color: white; border-radius: 10px; font-weight: 800; border: none; }")

    def on_btn_clicked(self):
        if not self.m_data['downloaded']:
            self.main_win.engine.download_model(self.m_data['id'], self.m_data['repo'])
            self.btn.setText("СКАЧИВАНИЕ...")
            self.btn.setEnabled(False)
        else:
            self.btn.setText("ЗАПУСКАЕТСЯ...")
            self.btn.setStyleSheet("QPushButton { background: #F0FF00; color: #22241E; border-radius: 10px; font-weight: 900; border: none; }")
            
            QTimer.singleShot(300, self.actually_switch_model)

    def actually_switch_model(self):
        self.main_win.engine.unload()
        new_path = self.m_data['path']
        self.main_win.model_name = new_path
        self.main_win.db.set_active_model(new_path)
        self.main_win.sys_model_lbl.setText(self.m_data['name'].upper())
        self.main_win.engine.load_model(new_path)
        QTimer.singleShot(500, self.main_win.refresh_models)


    def create_stat_bar(self, label, value):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        txt = QLabel(f"{label}")
        txt.setStyleSheet("font-size: 9px; font-weight: 800; color: #8E8E93; border: none;")
        bar = ProgressBar()
        bar.setFixedHeight(6)
        bar.set_value(value / 100.0)
        l.addWidget(txt); l.addWidget(bar)
        return w


# --- КАРТОЧКА ИСТОРИИ ---
class HistoryItem(QFrame):
    def __init__(self, text, dt, audio_len, proc_len, main_win):
        super().__init__()
        self.setObjectName("Card")
        self.full_text = text
        self.dt = dt
        self.main_win = main_win
        self.is_expanded = False
        
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        self.setStyleSheet("QFrame#Card { background-color: #FFFFFF; border: 1px solid #E5E5E7; border-radius: 16px; }")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(12)

        # --- 1. HEADER ---
        header = QHBoxLayout()
        try:
            d_p, t_p = str(dt).split(' ')
            time_lbl = QLabel(t_p[:5])
            time_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #1D1D1F; border: none; background: transparent;")
            date_lbl = QLabel(d_p)
            date_lbl.setStyleSheet("font-size: 11px; color: #8E8E93; font-weight: 600; border: none; background: transparent; margin-left: 5px;")
            header.addWidget(time_lbl); header.addWidget(date_lbl)
        except:
            lbl = QLabel(str(dt))
            lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #1D1D1F; border: none; background: transparent;")
            header.addWidget(lbl)
        
        header.addStretch()
        
        self.del_btn = QPushButton()
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/icon_delete.png")
        if os.path.exists(icon_path):
            self.del_btn.setIcon(QIcon(icon_path))
            self.del_btn.setIconSize(QSize(16, 16))
        else:
            self.del_btn.setText("✕") 
            
        self.del_btn.setStyleSheet("""
            QPushButton { background: #FFF0F0; border: none; border-radius: 10px; color: #FF3B30; font-weight: 900; } 
            QPushButton:hover { background: #FF3B30; color: white; }
        """)
        self.del_btn.clicked.connect(lambda: self.main_win.delete_requested(self.full_text, self.dt))
        header.addWidget(self.del_btn)
        self.main_layout.addLayout(header)

        meta_h = QHBoxLayout()
        meta_h.setSpacing(8)
        x_factor = int(audio_len / proc_len) if proc_len > 0 else 0
        tags_css = "font-size: 10px; font-weight: 800; padding: 0px 10px; border-radius: 8px; border: none;"
        
        dur_tag = QLabel(f"● {audio_len:.1f}s")
        dur_tag.setStyleSheet(f"color: #007AFF; background: #E5F1FF; {tags_css}")
        proc_tag = QLabel(f"→ {proc_len:.1f}s")
        proc_tag.setStyleSheet(f"color: #FF9500; background: #FFF4E5; {tags_css}")
        eff_tag = QLabel(f"x{x_factor}")
        eff_tag.setStyleSheet(f"color: #34C759; background: #E8F5E9; {tags_css}")
        
        for tag in [dur_tag, proc_tag, eff_tag]:
            tag.setFixedHeight(24)
            tag.setAlignment(Qt.AlignCenter)
            meta_h.addWidget(tag)
            
        meta_h.addStretch()
        self.main_layout.addLayout(meta_h)

        self.text_mask = QScrollArea()
        self.text_mask.setFrameShape(QFrame.NoFrame)
        self.text_mask.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_mask.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_mask.setWidgetResizable(True)
        self.text_mask.setStyleSheet("QScrollArea { background-color: #FFFFFF; border: none; }")
        
        self.BASE_HEIGHT = 45
        self.text_mask.setMinimumHeight(self.BASE_HEIGHT)
        self.text_mask.setMaximumHeight(self.BASE_HEIGHT)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #FFFFFF;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_lbl = QLabel(text)
        self.content_lbl.setWordWrap(True)
        self.content_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.content_lbl.setCursor(Qt.IBeamCursor)
        self.content_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.content_lbl.setStyleSheet("font-size: 14px; line-height: 1.5; color: #1D1D1F; border: none; background: #FFFFFF;")
        
        self.scroll_layout.addWidget(self.content_lbl)
        self.scroll_layout.addStretch()
        self.text_mask.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.text_mask)

        footer = QHBoxLayout()
        footer.setSpacing(10)
        self.copy_btn = QPushButton("КОПИРОВАТЬ")
        self.expand_btn = QPushButton("РАЗВЕРНУТЬ")
        
        self.btn_style = "QPushButton { background: #F2F2F7; color: #007AFF; border-radius: 10px; padding: 8px 16px; font-size: 11px; font-weight: 800; border: none; } QPushButton:hover { background: #E5E5E7; }"
        self.copy_btn.setStyleSheet(self.btn_style)
        self.expand_btn.setStyleSheet(self.btn_style)
        
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        
        self.copy_btn.clicked.connect(self.copy_it)
        self.expand_btn.clicked.connect(self.toggle_animation)
        
        footer.addWidget(self.copy_btn)
        footer.addWidget(self.expand_btn)
        footer.addStretch()
        self.main_layout.addLayout(footer)

        self.expand_btn.hide()
        QTimer.singleShot(10, self.check_text_length)

    def check_text_length(self):
        if self.content_lbl.sizeHint().height() > self.BASE_HEIGHT:
            self.expand_btn.show()

    def toggle_animation(self):
        self.is_expanded = not self.is_expanded
        
        target_height = min(self.content_lbl.sizeHint().height() + 5, 400)
        
        self.anim_max = QPropertyAnimation(self.text_mask, b"maximumHeight")
        self.anim_min = QPropertyAnimation(self.text_mask, b"minimumHeight")
        
        for anim in [self.anim_max, self.anim_min]:
            anim.setDuration(250) # Плавные 250мс
            anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        if self.is_expanded:
            self.anim_max.setStartValue(self.BASE_HEIGHT)
            self.anim_max.setEndValue(target_height)
            self.anim_min.setStartValue(self.BASE_HEIGHT)
            self.anim_min.setEndValue(target_height)
            self.expand_btn.setText("СВЕРНУТЬ")
        else:
            self.text_mask.verticalScrollBar().setValue(0) 
            self.anim_max.setStartValue(self.text_mask.height())
            self.anim_max.setEndValue(self.BASE_HEIGHT)
            self.anim_min.setStartValue(self.text_mask.height())
            self.anim_min.setEndValue(self.BASE_HEIGHT)
            self.expand_btn.setText("РАЗВЕРНУТЬ")
            
        self.anim_max.start()
        self.anim_min.start()

    def copy_it(self):
        pyperclip.copy(self.full_text)
        self.copy_btn.setText("✓ СКОПИРОВАНО")
        self.copy_btn.setStyleSheet("QPushButton { background: #34C759; color: white; border-radius: 10px; padding: 8px 16px; font-size: 11px; font-weight: 800; border: none; }")
        QTimer.singleShot(1500, self.reset_copy_btn)

    def reset_copy_btn(self):
        self.copy_btn.setText("КОПИРОВАТЬ")
        self.copy_btn.setStyleSheet(self.btn_style)


# --- ГЛАВНОЕ ОКНО ---
class MainWindow(QMainWindow):
    def __init__(self, db, model_name):
        super().__init__()
        self.db, self.model_name = db, model_name
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.BASE_DIR, "assets/icon_idle.png")
        self.icon_bord = os.path.join(self.BASE_DIR, "assets/icon_bord.png")
        self.icon_history = os.path.join(self.BASE_DIR, "assets/icon_history.png")
        self.icon_models = os.path.join(self.BASE_DIR, "assets/icon_models.png")
        self.icon_settings = os.path.join(self.BASE_DIR, "assets/icon_settings.png")
        
        self.setWindowTitle("Голосок")
        self.resize(1000, 700)
        self.setStyleSheet("QMainWindow { background: #FBFBFD; }")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.root_layout = QHBoxLayout(self.central)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # --- САЙДБАР ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("QFrame { background-color: #F2F2F7; border: none; border-right: 1px solid #E5E5E7; }")
        self.side_l = QVBoxLayout(self.sidebar)
        self.side_l.setContentsMargins(12, 40, 12, 20)
        self.side_l.setSpacing(4)

        # --- ЛОГОТИП ---
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(15, 10, 10, 25)
        logo_icon = QLabel()
        logo_icon.setPixmap(QIcon(self.icon_path).pixmap(24, 24))
        logo_icon.setStyleSheet("background: transparent; border: none;")
        logo_text = QLabel("ГОЛОСОК")
        logo_text.setStyleSheet("font-size: 18px; font-weight: 900; color: #22241E; border: none;")
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        self.side_l.addLayout(logo_layout)

        self.btn_dash = NavButton("Борд", self.icon_bord)
        self.btn_hist = NavButton("История", self.icon_history)
        self.btn_mods = NavButton("Модели", self.icon_models)
        self.btn_sett = NavButton("Настройки", self.icon_settings)
        
        self.nav_group = [self.btn_dash, self.btn_hist, self.btn_mods, self.btn_sett]
        for i, btn in enumerate(self.nav_group):
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            self.side_l.addWidget(btn)

        self.side_l.addStretch()
        
        self.model_status_box = QFrame()
        self.model_status_box.setFixedHeight(80)
        self.model_status_box.setStyleSheet("""
            QFrame { 
                background: white; border: 1px solid #E5E5E7; 
                border-radius: 12px; margin: 5px;
            }
            QLabel { border: none; background: transparent; }
        """)
        footer_l = QVBoxLayout(self.model_status_box)
        footer_l.setContentsMargins(10, 8, 10, 8)
        footer_l.setSpacing(2)

        h_status = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #FF3B30; font-size: 14px;")
        self.model_name_lbl = QLabel(self.model_name.split('/')[-1].upper())
        self.model_name_lbl.setStyleSheet("font-size: 9px; font-weight: 800; color: #22241E;")
        self.model_name_lbl.setWordWrap(True)
        
        h_status.addWidget(self.status_dot)
        h_status.addWidget(self.model_name_lbl)
        h_status.addStretch()
        footer_l.addLayout(h_status)

        # Прогресс-бар
        self.load_progress = ProgressBar() 
        self.load_progress.setFixedHeight(4)
        self.load_progress.hide() 
        footer_l.addWidget(self.load_progress)

        self.ram_lbl = QLabel("RAM: -- MB")
        self.ram_lbl.setStyleSheet("font-size: 9px; color: #8E8E93; font-weight: 600;")
        footer_l.addWidget(self.ram_lbl)

        self.side_l.addWidget(self.model_status_box)

        # --- СТЕК КОНТЕНТА ---
        self.stack = QStackedWidget()
        self.stack.addWidget(self.setup_dash())
        self.stack.addWidget(self.setup_hist())
        self.stack.addWidget(self.setup_models())
        self.stack.addWidget(self.setup_settings())

        self.root_layout.addWidget(self.sidebar)
        self.root_layout.addWidget(self.stack)

        self.switch_page(0)
        self.refresh()
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh)
    
    def on_search_text_changed(self):
        self.search_timer.start(300)

    def actually_do_search(self):
        self.refresh()
    
    def refresh_models(self):
        while self.models_grid.count():
            item = self.models_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        models = self.db.get_models()
        for i, m_data in enumerate(models):
            card = ModelCard(m_data, self)
            self.models_grid.addWidget(card, i // 2, i % 2)
    
    def update_engine_status(self, status, progress):
        # Достаем главный объект приложения
        main_app = QApplication.instance()
        
        if status == "loading":
            self.status_dot.setStyleSheet("color: #FF9500; font-size: 14px;")
            self.model_name_lbl.setText("ЗАПУСКАЮСЬ...")
            self.load_progress.show()
            self.load_progress.set_value(progress / 100.0)
            if hasattr(main_app, 'set_app_icon'):
                main_app.set_app_icon('off')
                
        elif status == "ready":
            self.status_dot.setStyleSheet("color: #34C759; font-size: 14px;")
            self.model_name_lbl.setText(self.model_name.split('/')[-1].upper())
            self.load_progress.hide()
            if hasattr(main_app, 'set_app_icon'):
                main_app.set_app_icon('idle')
            self.refresh_models()
            
        elif status == "unloaded" or status == "error":
            self.status_dot.setStyleSheet("color: #FF3B30; font-size: 14px;")
            self.model_name_lbl.setText("ВЫКЛЮЧЕН" if status == "unloaded" else "ОШИБКА")
            self.load_progress.hide()
            if hasattr(main_app, 'set_app_icon'):
                main_app.set_app_icon('off')

    def switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_group):
            btn.setChecked(i == idx)

    def add_stat(self, grid, label, value, r, c, rs, cs, is_main=False):
        container = QFrame()
        bg = "#22241E" if is_main else "white"
        color = "#FFF" if is_main else "#22241E"
        container.setStyleSheet(f"background: {bg}; border-radius: 20px; border: 1px solid #E5E5E7;")
        l = QVBoxLayout(container)
        l.setContentsMargins(20, 20, 20, 20)
        v = QLabel(value); v.setStyleSheet(f"font-size: {'42px' if is_main else '26px'}; font-weight: 200; color: {color}; border:none;")
        t = QLabel(label); t.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {'#AAA' if is_main else '#8E8E93'}; letter-spacing: 1px; border:none;")
        l.addWidget(v); l.addWidget(t)
        grid.addWidget(container, r, c, rs, cs)
        return v

    def setup_dash(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(35, 35, 35, 35); l.setSpacing(25)
        
        h = QHBoxLayout()
        sys_lbl = QLabel("ИСПОЛЬЗУЕТСЯ")
        sys_lbl.setStyleSheet("font-size: 9px; font-weight: 800; color: #8E8E93;")
        h.addWidget(sys_lbl)
        
        self.sys_model_lbl = QLabel(self.model_name.split('/')[-1].upper())
        self.sys_model_lbl.setStyleSheet("background: #E5E5E7; color: #22241E; padding: 4px 10px; border-radius: 6px; font-size: 9px; font-weight: 800;")
        h.addWidget(self.sys_model_lbl)
        h.addStretch()
        l.addLayout(h)
        
        grid = QGridLayout(); grid.setSpacing(12)
        self.m_hours = self.add_stat(grid, "ЧАСОВ ЖИЗНИ СЭКОНОМЛЕНО", "0.0", 0, 0, 1, 3, is_main=True)
        self.m_speed = self.add_stat(grid, "МОЩНОСТЬ ИИ", "0.0x", 1, 0, 1, 1)
        self.m_streak = self.add_stat(grid, "ДНЕЙ ПОДРЯД", "0", 1, 1, 1, 1)
        self.m_wpm = self.add_stat(grid, "WPM (ТЕМП)", "0", 1, 2, 1, 1)
        self.m_audio = self.add_stat(grid, "НАГОВОРИЛИ (МИН)", "0.0", 2, 0, 1, 1)
        self.m_count = self.add_stat(grid, "ВСЕГО ЗАМЕТОК", "0", 2, 1, 1, 1)
        self.m_avg = self.add_stat(grid, "СРЕДНЯЯ ДЛИНА (ЗН)", "0", 2, 2, 1, 1)
        
        l.addLayout(grid)
        l.addWidget(QLabel("НЕДЕЛЬНЫЙ ТРЕНД", styleSheet="font-size: 10px; font-weight: 800; color: #8E8E93;"))
        self.bar_chart = BarChart(); l.addWidget(self.bar_chart)
        
        manifest = QFrame()
        manifest.setFixedHeight(45); manifest.setStyleSheet("background: #22241E; border-radius: 12px;")
        ml = QHBoxLayout(manifest); ml.setContentsMargins(15, 0, 15, 0)
        mt = QLabel("ГОЛОСОК ™2026"); mt.setStyleSheet("color: #F0FF00; font-weight: 900; font-size: 10px;")
        ma = QLabel("Design by Kozak"); ma.setStyleSheet("color: #8E8E93; font-size: 9px; font-weight: 700;")
        ml.addWidget(mt); ml.addStretch(); ml.addWidget(ma)
        l.addWidget(manifest)

        l.addStretch(); return page

    def setup_hist(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(25, 35, 25, 20)
        page.setStyleSheet("background: white;")
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск по мыслям...")
        self.search_bar.setStyleSheet("background: #FFFFFF; color: #22241E; border: none; border-radius: 12px; padding: 12px; font-size: 14px;")
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(300))
        
        l.addWidget(self.search_bar)
        
        self.scroll = QScrollArea(); 
        self.scroll.setWidgetResizable(True); 
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.scroll.setStyleSheet("""
            QScrollArea { 
                background: transparent; 
                border: none; 
            }
            QScrollBar:vertical { 
                border: none; 
                background: transparent; 
                width: 8px; 
                margin: 0px; 
            }
            QScrollBar::handle:vertical { 
                background: rgba(0, 0, 0, 0.15); 
                border-radius: 4px; 
                min-height: 30px; 
            }
            QScrollBar::handle:vertical:hover { 
                background: rgba(0, 0, 0, 0.3); 
            }
            /* ТОТАЛЬНОЕ УНИЧТОЖЕНИЕ МАКОВСКИХ РАМОК И ФОНА СКРОЛЛА */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { 
                border: none; 
                background: none; 
            }
        """)
        self.scroll.viewport().setStyleSheet("background: #FBFBFD;") 
        
        self.scroll_content = QWidget(); self.hist_layout = QVBoxLayout(self.scroll_content)
        self.hist_layout.setAlignment(Qt.AlignTop); self.hist_layout.setSpacing(15)
        self.scroll.setWidget(self.scroll_content); l.addWidget(self.scroll)
        return page
    
    def setup_models(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(35, 40, 35, 35)
        
        title = QLabel("ДОСТУПНЫЕ МОДЕЛИ")
        title.setStyleSheet("font-weight: 800; font-size: 18px; color: #22241E; margin-bottom: 20px;")
        l.addWidget(title)
        
        self.models_grid_widget = QWidget()
        self.models_grid = QGridLayout(self.models_grid_widget)
        self.models_grid.setSpacing(15)
        
        models = self.db.get_models()
        for i, m_data in enumerate(models):
            card = ModelCard(m_data, self)
            self.models_grid.addWidget(card, i // 2, i % 2)
            
        l.addWidget(self.models_grid_widget)
        l.addStretch()
        return page

    def setup_settings(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.setContentsMargins(35, 40, 35, 35)
        l.setSpacing(15)
        
        l.addWidget(QLabel("НАСТРОЙКИ СИСТЕМЫ", styleSheet="font-weight: 800; font-size: 18px; color: #22241E; margin-bottom: 20px;"))
        
        # Тумблеры
        l.addWidget(self.create_setting_row("Запускать при старте системы", True))
        l.addWidget(self.create_setting_row("Уведомления о вставке текста", True))
        l.addWidget(self.create_setting_row("Автоматическое удаление через 30 дней", False))
        
        l.addStretch()
        return page

    def create_setting_row(self, text, checked):
        row = QFrame()
        row.setStyleSheet("background: #F2F2F7; border-radius: 12px; padding: 15px;")
        rl = QHBoxLayout(row)
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: 600; color: #1D1D1F; border: none;")
        toggle = QPushButton("ВКЛ" if checked else "ВЫКЛ")
        toggle.setFixedSize(50, 26)
        toggle.setStyleSheet(f"background: {'#34C759' if checked else '#D1D1D6'}; color: white; border-radius: 13px; font-size: 9px; font-weight: 900;")
        rl.addWidget(lbl); rl.addStretch(); rl.addWidget(toggle)
        return row

    def refresh(self):
        s = self.db.get_stats()
        
        self.m_hours.setText(str(s["hours"]))
        self.m_speed.setText(f"{s['speed_factor']}x")
        self.m_streak.setText(str(s["streak"]))
        self.m_wpm.setText(str(s["wpm"]))
        self.m_audio.setText(str(s["total_audio_min"]))
        self.m_count.setText(str(s["count"]))
        self.m_avg.setText(str(s["avg_len"]))
        self.bar_chart.set_data(self.db.get_weekly_activity())
        
        while self.hist_layout.count():
            item = self.hist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                pass

        query = self.search_bar.text()
        data = self.db.search(query) if query else self.db.get_all_full()
        
        # Заглушка или данные
        if not data:
            empty_lbl = QLabel("НИЧЕГО НЕ НАЙДЕНО")
            empty_lbl.setStyleSheet("color: #8E8E93; font-size: 14px; font-weight: 800; margin-top: 50px;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.hist_layout.addWidget(empty_lbl)
        else:
            for text, dt, al, pl in data:
                self.hist_layout.addWidget(HistoryItem(text, dt, al, pl, self))
        
        self.hist_layout.addStretch(1)
            
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / 1024 / 1024
            self.ram_lbl.setText(f"RAM: {int(mem_mb)} MB")
        except: pass

    def delete_requested(self, text, dt):
        from ui import ConfirmDialog
        if ConfirmDialog(self).exec():
            self.db.delete_entry(dt); self.refresh()
