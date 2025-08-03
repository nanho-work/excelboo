from PyQt6.QtWidgets import QSplashScreen, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QFont

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setFixedSize(600, 300)
        self.setStyleSheet("background-color: #e6f5e6;")  # 연한 연녹색
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # 텍스트 라벨
        self.label = QLabel("민원 관리 툴", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(0, 0, 600, 300)
        self.label.setFont(QFont("맑은 고딕", 20, QFont.Weight.Bold))
        self.label.setStyleSheet("color: #222;")

        # 로고 라벨
        self.logo = QLabel(self)
        self.logo.setPixmap(QPixmap("assets/logo.png").scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        self.logo.move(20, 20)
        self.logo.setStyleSheet("background: transparent;")

        # 푸터 라벨
        self.footer = QLabel("제작: LaonCode", self)
        self.footer.setStyleSheet("color: #555; font-size: 10pt; background: transparent;")
        self.footer.adjustSize()
        footer_x = self.width() - self.footer.width() - 20
        footer_y = self.height() - self.footer.height() - 15
        self.footer.move(footer_x, footer_y)

        # 투명도 애니메이션
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(1200)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def fade_out(self, callback):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(callback)
        self.animation.start()