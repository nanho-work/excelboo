# 하나카드 사고건

# 하나카드 사고건

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
import pandas as pd

class HanacardIncidentView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("하나카드 사고건")
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.load_button = QPushButton("하나카드 사고건 엑셀 불러오기")
        self.load_button.clicked.connect(self.load_excel)
        layout.addWidget(self.load_button)

    def load_excel(self):
        try:
            df = pd.read_excel("웨이업_RM리스트_2025년_보고.xlsx", sheet_name="하나카드 사고건")
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(df.columns)

            for i in range(len(df)):
                for j, col in enumerate(df.columns):
                    val = str(df.iloc[i, j])
                    self.table.setItem(i, j, QTableWidgetItem(val))
        except Exception as e:
            print("엑셀 불러오기 실패:", e)