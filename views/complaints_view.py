from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QHBoxLayout
from PyQt6.QtWidgets import QLineEdit, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
import pandas as pd
import os
from dialogs.sheet_select_dialog import SheetSelectDialog
from styles.button_styles import modern_default_button_style
from styles.scrollbar_styles import modern_scrollbar_style
from styles.search_box_styles import modern_search_box_style

class ComplaintsView(QWidget):
    data_loaded = pyqtSignal(pd.DataFrame)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(modern_scrollbar_style)
        self.setWindowTitle("전체민원")
        layout = QVBoxLayout(self)

        self.last_dir = ""

        self.table = QTableWidget()

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        self.load_button = QPushButton("전체민원 엑셀 불러오기")
        self.load_button.setStyleSheet(modern_default_button_style)
        self.load_button.clicked.connect(self.load_excel)
        button_layout.addWidget(self.load_button)

        self.save_button = QPushButton("수정된 내용 엑셀로 저장")
        self.save_button.setStyleSheet(modern_default_button_style)
        self.save_button.clicked.connect(self.save_to_excel)
        button_layout.addWidget(self.save_button)

        self.add_row_button = QPushButton("행 추가")
        self.add_row_button.setStyleSheet(modern_default_button_style)
        self.add_row_button.clicked.connect(self.add_row)
        button_layout.addWidget(self.add_row_button)

        # Add the horizontal button layout before the search box
        layout.addLayout(button_layout)

        self.search_box = QLineEdit()
        self.search_box.setStyleSheet(modern_search_box_style)
        self.search_box.setPlaceholderText("검색어를 입력하세요...")
        self.search_box.textChanged.connect(self.search_data)
        layout.addWidget(self.search_box)
        layout.addWidget(self.table)

    def load_excel(self):
        try:
            dialog = QFileDialog(self)
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            file, _ = dialog.getOpenFileName(self, "엑셀 파일 선택", self.last_dir, "Excel Files (*.xlsx)")
            if file:
                self.last_dir = os.path.dirname(file)
                excel_file = pd.ExcelFile(file)
                sheet_names = excel_file.sheet_names

                # 시트 선택 다이얼로그
                QApplication.setStyle("Fusion")
                dialog = SheetSelectDialog(sheet_names, is_dark_mode=False, parent=self)
                if dialog.exec():
                    sheet = dialog.get_selected_sheet()
                    df = pd.read_excel(file, sheet_name=sheet, dtype=str).fillna("")
                    # ✅ 컬럼명 공백 및 줄바꿈 제거
                    df.columns = df.columns.str.strip().str.replace("\n", "").str.replace("\r", "")

                    # ✅ 날짜 컬럼을 datetime으로 변환하고 NaT는 공백 처리
                    date_cols = ["접수일", "처리기한", "처리완료일", "취소일자", "입금일자"]
                    for col in date_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
                            df[col] = df[col].fillna("")

                    # ✅ 금액 컬럼을 float으로 변환
                    money_cols = ["승인금액", "입금금액"]
                    for col in money_cols:
                        if col in df.columns:
                            df[col] = (
                                df[col]
                                .astype(str)
                                .str.replace(",", "", regex=False)
                                .str.replace("₩", "", regex=False)
                                .str.strip()
                                .replace("", "0")
                                .astype(float)
                            )

                    self.original_df = df.copy()
                    self.table.setRowCount(len(df))
                    self.table.setColumnCount(len(df.columns))
                    self.table.setHorizontalHeaderLabels(df.columns)

                    self.table.setSortingEnabled(False)

                    for i in range(len(df)):
                        for j, col in enumerate(df.columns):
                            val = df.iloc[i, j]
                            if col in ["승인금액", "입금금액"]:
                                try:
                                    val = f"{int(float(val)):,}"
                                except:
                                    val = str(val)
                            else:
                                val = str(val)
                            item = QTableWidgetItem(val)
                            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                            if col in ["승인금액", "입금금액"]:
                                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            else:
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.table.setItem(i, j, item)

                    self.table.setSortingEnabled(True)
                    self.data_loaded.emit(df)
        except Exception as e:
            print("엑셀 불러오기 실패:", e)

    def save_to_excel(self):
        try:
            rows = self.table.rowCount()
            cols = self.table.columnCount()
            headers = [self.table.horizontalHeaderItem(j).text() for j in range(cols)]

            data = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    item = self.table.item(i, j)
                    row.append(item.text() if item else "")
                data.append(row)

            df = pd.DataFrame(data, columns=headers)

            dialog = QFileDialog(self)
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            file, _ = dialog.getSaveFileName(self, "엑셀로 저장", self.last_dir, "Excel Files (*.xlsx)")
            if file:
                self.last_dir = os.path.dirname(file)
                df.to_excel(file, index=False)
        except Exception as e:
            print("엑셀 저장 실패:", e)
    def add_row(self):
        self.table.setSortingEnabled(False)
        current_rows = self.table.rowCount()
        self.table.insertRow(current_rows)
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(current_rows, col, item)
        self.table.setSortingEnabled(True)

    def search_data(self, text):
        if not hasattr(self, 'original_df'):
            return

        filtered_df = self.original_df[self.original_df.apply(
            lambda row: text.lower() in ''.join(row.astype(str)).lower(), axis=1
        )]

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(filtered_df))
        self.table.setColumnCount(len(filtered_df.columns))
        self.table.setHorizontalHeaderLabels(filtered_df.columns)

        for i in range(len(filtered_df)):
            for j, col in enumerate(filtered_df.columns):
                val = filtered_df.iloc[i, j]
                if col in ["승인금액", "입금금액"]:
                    try:
                        val = f"{int(float(val)):,}"
                    except:
                        val = str(val)
                else:
                    val = str(val)
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                if col in ["승인금액", "입금금액"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Reset background to default
                item.setBackground(Qt.GlobalColor.white)
                if text.lower() in val.lower() and text.strip() != "":
                    item.setBackground(Qt.GlobalColor.yellow)
                self.table.setItem(i, j, item)
        self.table.setSortingEnabled(True)