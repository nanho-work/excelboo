from PyQt6.QtWidgets import QDialog, QListWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class SheetSelectDialog(QDialog):
    def __init__(self, sheets, is_dark_mode=False, parent=None):
        super().__init__(parent)
        self.is_dark_mode = is_dark_mode
        self.selected_sheet = None

        self.setWindowTitle("시트 선택")
        self.resize(300, 400)

        self.list_widget = QListWidget()
        self.list_widget.addItems(sheets)
        self.list_widget.itemDoubleClicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.apply_list_widget_style()

    def apply_list_widget_style(self):
        if not self.is_dark_mode:
            self.list_widget.setStyleSheet("""
                QListWidget::item:hover {
                    background-color: #d1f2c4;
                    color: #000000;
                }
                QListWidget::item {
                    color: #000000;
                }
            """)
        else:
            self.list_widget.setStyleSheet("""
                QListWidget::item:hover {
                    background-color: #3a3a3a;
                    color: #ffffff;
                }
                QListWidget::item {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
            """)

    def get_selected_sheet(self):
        selected_item = self.list_widget.currentItem()
        return selected_item.text() if selected_item else None