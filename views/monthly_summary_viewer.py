import pandas as pd
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QHeaderView
from PyQt6.QtCore import Qt, QMarginsF
from PyQt6.QtGui import QPainter, QPageLayout, QPageSize
import matplotlib.pyplot as plt


class MonthlySummaryViewer(QDialog):
    def __init__(self, full_df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("월별 요약 및 시각화")
        self.resize(800, 600)

        self.df = full_df.copy()
        self.df["접수일"] = pd.to_datetime(self.df["접수일"], errors="coerce")
        self.df = self.df.dropna(subset=["접수일"])
        self.df["월"] = self.df["접수일"].dt.to_period("M")

        self.layout = QVBoxLayout()
        self.label = QLabel("월별 요약 정보")
        self.table = QTableWidget()

        # --- Add month selector before generate_summary ---
        from PyQt6.QtWidgets import QComboBox, QHBoxLayout

        self.month_selector_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.available_months = sorted(self.df["월"].astype(str).unique())
        self.month_combo.addItems(self.available_months)
        self.month_combo.setCurrentIndex(len(self.available_months) - 1)
        self.month_combo.currentIndexChanged.connect(self.generate_summary)

        self.month_selector_layout.addWidget(QLabel("기준 월 선택:"))
        self.month_selector_layout.addWidget(self.month_combo)
        self.layout.insertLayout(0, self.month_selector_layout)
        # --- End month selector ---

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.table)

        self.print_button = QPushButton("PDF로 저장")
        self.print_button.clicked.connect(self.handle_print)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)

        self.generate_summary()

    def create_summary_table(self, curr_df, prev_df):
        df = pd.concat([prev_df, curr_df])

        prev_summary = prev_df.groupby(["가맹점명", "카드사"]).size().reset_index(name="전월")
        curr_summary = curr_df.groupby(["가맹점명", "카드사"]).size().reset_index(name="당월")

        merged = pd.merge(prev_summary, curr_summary, on=["가맹점명", "카드사"], how="outer").fillna(0)
        merged["전월"] = merged["전월"].astype(int)
        merged["당월"] = merged["당월"].astype(int)
        merged["증감률"] = ((merged["당월"] - merged["전월"]) / merged["전월"].replace(0, pd.NA)) * 100
        merged["증감률"] = merged["증감률"].round(1).fillna(0)

        all_cards = merged["카드사"].unique().tolist()
        reshaped = []
        for name, group in merged.groupby("가맹점명"):
            row = {"가맹점명": name}
            for card in all_cards:
                row[f"{card}_전월"] = 0
                row[f"{card}_당월"] = 0
                row[f"{card}_증감률"] = "0.0%"
            for _, r in group.iterrows():
                card = r["카드사"]
                row[f"{card}_전월"] = r["전월"]
                row[f"{card}_당월"] = r["당월"]
                arrow = "▲" if r["증감률"] > 0 else ("▼" if r["증감률"] < 0 else "")
                color = "🔴" if r["증감률"] > 0 else ("🔵" if r["증감률"] < 0 else "")
                row[f"{card}_증감률"] = f"{color} {abs(r['증감률'])}% {arrow}"
            reshaped.append(row)

        return pd.DataFrame(reshaped).fillna("")

    def populate_table(self, result_df):
        self.table.setRowCount(len(result_df))
        self.table.setColumnCount(len(result_df.columns))
        new_headers = []
        for col in result_df.columns:
            if "_" in col and not col.startswith("가맹점명"):
                parts = col.split("_")
                new_headers.append(f"{parts[0]}\n({parts[1]})")
            else:
                new_headers.append(col)
        self.table.setHorizontalHeaderLabels(new_headers)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        for i, row in result_df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        font = self.table.font()
        font.setPointSize(13)
        self.table.setFont(font)
        self.table.resizeColumnsToContents()

    def generate_summary(self):
        df = self.df.copy()
        curr_month_str = self.month_combo.currentText()
        self.curr_month_str = curr_month_str
        curr_month = pd.Period(curr_month_str, freq='M')
        all_months = sorted(df["월"].unique())
        curr_index = all_months.index(curr_month)
        if curr_index == 0:
            self.table.clearContents()
            self.table.setRowCount(0)
            return
        prev_month = all_months[curr_index - 1]
        curr_df = df[df["월"] == curr_month]
        prev_df = df[df["월"] == prev_month]
        result_df = self.create_summary_table(curr_df, prev_df)
        self.populate_table(result_df)

    def handle_print(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPageLayout, QPageSize
        from PyQt6.QtCore import QMarginsF, QRectF
        from PyQt6.QtGui import QFontMetrics

        file_path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "", "PDF Files (*.pdf)")
        if file_path and not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'
        if not file_path:
            return

        curr_month_str = getattr(self, 'curr_month_str', '선택된 월')

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        layout = QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Landscape, QMarginsF(10, 10, 10, 10))
        printer.setPageLayout(layout)

        painter = QPainter()
        if not painter.begin(printer):
            return

        page_rect = layout.paintRectPixels(printer.resolution())
        rows = self.table.rowCount()
        cols = self.table.columnCount()

        # Dynamically adjust font size to fit table within page width
        font = painter.font()
        for size in range(13, 5, -1):  # Try font sizes from 13 down to 6
            font.setPointSize(size)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            col_widths = []
            for col in range(cols):
                header_text = self.table.horizontalHeaderItem(col).text()
                max_width = metrics.horizontalAdvance(header_text)
                for row in range(rows):
                    cell_text = self.table.item(row, col).text()
                    max_width = max(max_width, metrics.horizontalAdvance(cell_text))
                col_widths.append(max_width + 10)
            total_width = sum(col_widths)
            if total_width <= page_rect.width():
                break  # Font size fits

        # Calculate height for each row
        row_heights = []
        for row in range(rows):
            max_height = 0
            for col in range(cols):
                text = self.table.item(row, col).text()
                max_height = max(max_height, metrics.height())
            row_heights.append(max_height + 6)

        # Calculate header height with padding
        header_line_counts = [
            self.table.horizontalHeaderItem(col).text().count('\n') + 1
            for col in range(cols)
        ]
        header_heights = [
            metrics.lineSpacing() * lines + 10
            for lines in header_line_counts
        ]
        header_height = max(header_heights)

        # Draw title
        title = f"월 단위 현황 ({curr_month_str})"
        title_font = font
        title_font.setPointSize(font.pointSize() + 2)
        painter.setFont(title_font)
        title_rect = QRectF(page_rect.left(), page_rect.top(), page_rect.width(), metrics.height() + 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title)
        y = title_rect.bottom() + 10  # Update y to be below title

        # Draw header
        x = page_rect.left()
        for col in range(cols):
            width = col_widths[col]
            header_text = self.table.horizontalHeaderItem(col).text()
            # line_count = header_text.count('\n') + 1  # removed
            height = header_height
            rect = QRectF(x, y, width, height)
            painter.drawRect(rect)
            text = header_text
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            x += width

        # y += header_height  # Removed to prevent double increment

        # Adjust y before drawing rows
        y += header_height

        # Draw table rows
        for row in range(rows):
            x = page_rect.left()
            for col in range(cols):
                width = col_widths[col]
                height = row_heights[row]
                rect = QRectF(x, y, width, height)
                painter.drawRect(rect)
                text = self.table.item(row, col).text()
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
                x += width
            y += row_heights[row]

        painter.end()
