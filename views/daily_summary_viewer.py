# daily_summary_viewer.py
import os
import pandas as pd
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties
from matplotlib import font_manager

font_path = os.path.abspath("fonts/NanumGothic.ttf")
font_manager.fontManager.addfont(font_path)
font_prop = FontProperties(fname=font_path)
nanum_font = font_prop.get_name()
matplotlib.rcParams['font.family'] = nanum_font
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['pdf.fonttype'] = 42  # Ensure TrueType fonts are embedded in PDFs


class DailySummaryViewer(QDialog):
    def __init__(self, full_df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("일자별 요약 및 시각화")
        self.resize(800, 600)

        self.df = full_df.copy()
        self.df["접수일"] = pd.to_datetime(self.df["접수일"], errors="coerce").dt.date

        self.layout = QVBoxLayout()
        self.date_selector = QComboBox()
        self.date_selector.addItems(sorted({str(d) for d in self.df["접수일"].dropna().unique()}))
        self.date_selector.currentIndexChanged.connect(self.update_view)

        self.label = QLabel("날짜를 선택하세요")
        self.table = QTableWidget()

        # matplotlib 그래프 영역 설정
        self.figure, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.date_selector)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.canvas)

        self.print_button = QPushButton("프린터 출력")
        self.print_button.clicked.connect(self.handle_print)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)

        self.update_view()

    def update_view(self):
        selected_date = self.date_selector.currentText()
        if not selected_date:
            return

        filtered = self.df[self.df["접수일"].astype(str) == selected_date]
        filtered = filtered.fillna("")
        # Ensure 'TID명' column is one-dimensional and string-typed
        filtered["TID명"] = filtered["TID명"].apply(
            lambda x: x[0] if isinstance(x, (list, tuple)) and len(x) > 0 else ("" if pd.isna(x) else str(x))
        )
        filtered["TID명"] = filtered["TID명"].astype(str)
        print("TID명 column ndim:", filtered["TID명"].ndim)
        print("TID명 column type sample:", type(filtered["TID명"].iloc[0]))
        # ✅ groupby().agg()로 집계
        filtered["기한내처리여부"] = filtered["처리상태"].str.lower() == "y"
        grouped = (
            filtered.groupby(["가맹점명", "TID명"])
            .agg(
                민원건수=("TID명", "count"),
                기한내처리건수=("기한내처리여부", "sum")
            )
            .reset_index()
        )

        # ✅ 처리율 및 비중 계산
        grouped["처리율"] = ((grouped["기한내처리건수"] / grouped["민원건수"]) * 100).round(1).astype(str) + "%"
        total_complaints_day = grouped["민원건수"].sum()
        grouped["민원비중(%)"] = grouped["민원건수"].apply(
            lambda x: f"{(x / total_complaints_day * 100):.1f}%" if total_complaints_day else "0.0%"
        )

        # 테이블에 데이터 표시
        self.table.setRowCount(len(grouped))
        self.table.setColumnCount(len(grouped.columns))
        self.table.setHorizontalHeaderLabels(grouped.columns)

        prev_store = None
        for i, row in grouped.iterrows():
            for j, val in enumerate(row):
                # Replace duplicate "가맹점명" values with empty string except first occurrence
                if j == 0:
                    if val == prev_store:
                        display_val = ""
                    else:
                        display_val = val
                        prev_store = val
                else:
                    display_val = val
                item = QTableWidgetItem(str(display_val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, j, item)

        # 합계 행 추가
        total_rows = len(grouped)
        self.table.insertRow(total_rows)
        self.table.setSpan(total_rows, 0, 1, 2)
        sum_item = QTableWidgetItem("합계")
        sum_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        sum_item.setFlags(sum_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(total_rows, 0, sum_item)

        total_complaints = grouped["민원건수"].sum()
        total_processed = grouped["기한내처리건수"].sum()
        total_rate = f"{(total_processed / total_complaints * 100):.1f}%" if total_complaints else "0.0%"

        self.table.setItem(total_rows, 2, QTableWidgetItem(str(total_complaints)))
        self.table.setItem(total_rows, 3, QTableWidgetItem(str(total_processed)))
        self.table.setItem(total_rows, 4, QTableWidgetItem(total_rate))
        self.table.setItem(total_rows, 5, QTableWidgetItem("100.0%"))
        item = self.table.item(total_rows, 5)
        if item:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)

        for col in [2, 3, 4]:
            item = self.table.item(total_rows, col)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)

        # 열 너비 자동 조정
        self.table.resizeColumnsToContents()

        # 글꼴 크기에 따라 행 높이 자동 조정
        font = self.table.font()
        font.setPointSize(16)
        self.table.setFont(font)

        metrics = self.table.fontMetrics()
        row_height = metrics.height() + 20  # Add padding

        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, row_height)

        # 바 차트 표시
        self.ax.clear()
        self.ax.bar(grouped["TID명"], grouped["민원건수"], label="민원건수")
        self.ax.set_title(f"{selected_date} 민원 건수", fontproperties=font_prop)
        self.ax.set_xlabel("TID명", fontproperties=font_prop)
        self.ax.set_ylabel("건수", fontproperties=font_prop)
        self.ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

    def handle_print(self):
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.table import Table

        def wrap_text(text, max_length=15):
            if len(text) <= max_length:
                return text
            return "\n".join([text[i:i+max_length] for i in range(0, len(text), max_length)])

        file_path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        with PdfPages(file_path) as pdf:
            # ✅ 첫 번째 페이지: 표 출력 (도표 제외)
            fig, ax = plt.subplots(figsize=(8.27, 11.69))
            fig.suptitle(f"{self.date_selector.currentText()} 일일민원보고", fontproperties=font_prop, fontsize=28, y=0.98)
            fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # ✅ A4 여백 설정 (5%)
            ax.axis('off')

            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            rows = []
            for row in range(self.table.rowCount()):
                row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
                rows.append(row_data)

            table_data = [headers] + rows

            # Dynamic bbox calculation for table height
            row_count = len(table_data)
            font_size = 14
            height_unit = font_size / 600

            def count_lines(cell):
                return wrap_text(cell, 12).count("\n") + 1

            row_heights = [height_unit * max(count_lines(cell) for cell in row) for row in table_data]
            avg_cell_height = sum(row_heights) / row_count
            total_table_height = avg_cell_height * row_count

            bbox_top = 0.9
            bbox_bottom = 0.1
            available_height = bbox_top - bbox_bottom
            height_ratio = min(total_table_height, available_height)
            adjusted_bbox = [0.1, bbox_top - height_ratio, 0.8, height_ratio]

            tab = Table(ax, bbox=adjusted_bbox)

            # ✅ 표 데이터 생성 및 셀 폰트 적용
            # font_size = 14  # 줄였을 경우
            col_widths = [0.15, 0.3, 0.1, 0.1, 0.1, 0.1]
            # cell_width = 1.0 / n_cols
            # cell_height = max(0.03, min(0.2, 0.9 / n_rows))
            num_lines = max(cell.count("\n") + 1 for row in table_data for cell in row)
            cell_height = min(0.03 * num_lines, 0.2)

            for i, row in enumerate(table_data):
                for j, cell in enumerate(row):
                    wrapped_cell = wrap_text(cell, max_length=12)
                    height_unit = font_size / 600  # 예: 14/600 ≈ 0.023
                    cell_height = height_unit * (wrapped_cell.count("\n") + 1)
                    cell_obj = tab.add_cell(
                        i, j, col_widths[j], cell_height, text=wrapped_cell, loc='center',
                        facecolor='#cccccc' if i == 0 else 'white'
                    )
                    # ✅ 셀 폰트 및 크기 적용
                    cell_obj.get_text().set_fontproperties(font_prop)
                    cell_obj.get_text().set_fontsize(font_size)
                    cell_obj.set_height(cell_height)

            ax.add_table(tab)
            # ✅ 표 전체 크기 맞춤 조정
           
            pdf.savefig(fig)
            plt.close(fig)

            # ✅ 두 번째 페이지: 도넛 차트 출력 (좌측에 TID명 리스트, 우측에 도넛 차트)
            fig2 = plt.figure(figsize=(8.27, 11.69))

            selected_date = self.date_selector.currentText()
            filtered = self.df[self.df["접수일"].astype(str) == selected_date]
            grouped = filtered.groupby("TID명").size()

            labels = grouped.index.tolist()
            sizes = grouped.values

            # 좌측 텍스트 박스 영역 (TID 리스트)
            ax_text = fig2.add_axes([0.05, 0.1, 0.4, 0.8])  # left half
            ax_text.axis('off')
            text_str = "\n".join(labels)
            ax_text.text(0, 1, text_str, va='top', ha='left', fontsize=14, fontproperties=font_prop)

            # 우측 도넛 차트
            ax_donut = fig2.add_axes([0.55, 0.3, 0.4, 0.4])  # right half
            wedges, texts, autotexts = ax_donut.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                textprops={'fontsize': 10, 'fontproperties': font_prop},
                wedgeprops=dict(width=0.4)
            )
            ax_donut.set_title(f"{selected_date} 민원 비중", fontproperties=font_prop)

            pdf.savefig(fig2)
            plt.close(fig2)