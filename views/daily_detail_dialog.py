# views/daily_detail_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt

class DailyDetailDialog(QDialog):
    def __init__(self, df, date, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{date} 상세 민원 내역")
        self.resize(1000, 600)

        layout = QVBoxLayout()
        label = QLabel(f"{date} 접수 민원 상세")
        table = QTableWidget()
        df = df.copy()
        df = df.fillna("")
        df = df[df.astype(str).apply(lambda x: ''.join(x).strip(), axis=1) != '']  # remove fully blank rows
        df = df.reset_index(drop=True)
        df.columns = df.columns.str.strip()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns)

        for i, row in df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, j, item)

        layout.addWidget(label)
        layout.addWidget(table)
        self.setLayout(layout)