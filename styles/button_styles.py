# styles/button_styles.py

modern_default_button_style = """
    QPushButton {
        background-color: #1E90FF;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        border: none;
    }
    QPushButton:hover {
        background-color: #1C86EE;
    }
"""

modern_danger_button_style = """
    QPushButton {
        background-color: #FF4C4C;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        border: none;
    }
    QPushButton:hover {
        background-color: #E04343;
    }
"""

modern_outline_button_style = """
    QPushButton {
        background-color: transparent;
        color: #1E90FF;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        border: 2px solid #1E90FF;
    }
    QPushButton:hover {
        background-color: #E6F2FF;
    }
"""

selected_button_style = """
    QPushButton {
        background-color: #104E8B;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        border: 2px solid #1E90FF;
    }
    QPushButton:hover {
        background-color: #0F3E6D;
    }
"""

gradient_button_style = """
    QPushButton {
        background: qlineargradient(
            spread:pad,
            x1:1, y1:0,
            x2:0, y2:0,
            stop:0 #ffffff,
            stop:1 #bfdbfe
        );
        color: #1e3a8a;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        border: 1px solid #93c5fd;
    }
    QPushButton:hover {
        background: qlineargradient(
            spread:pad,
            x1:1, y1:0,
            x2:0, y2:0,
            stop:0 #e0f2fe,
            stop:1 #bfdbfe
        );
    }
"""