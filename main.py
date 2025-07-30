from PyQt6.QtWidgets import QApplication, QLabel, QWidget

app = QApplication([])
window = QWidget()
window.setWindowTitle("엑셀 대체 툴")
label = QLabel("엑셀 없이도 실행되는 툴입니다", parent=window)
label.move(50, 50)
window.resize(300, 200)
window.show()
app.exec()