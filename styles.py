QSS = """
QMainWindow { 
    background-color: transparent; 
}

/* Навигация как в Центре Управления */
QWidget#NavBar {
    background: rgba(230, 230, 230, 150);
    border-radius: 12px;
}

QPushButton#NavBtn {
    background: transparent;
    border: none;
    color: #1D1D1F;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 8px;
}

QPushButton#NavBtn:checked {
    background: #FFFFFF;
}

/* Карточки-облака */
QFrame#Card {
    background: rgba(255, 255, 255, 180);
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 16px;
}

QLineEdit {
    background: rgba(200, 200, 200, 100);
    border-radius: 10px;
    padding: 10px;
    color: #000;
}

QScrollArea { border: none; background: transparent; }
QWidget#ScrollContent { background: transparent; }

QLabel { color: #1D1D1F; font-family: "SF Pro Display"; }
"""