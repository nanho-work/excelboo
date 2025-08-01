# utils/pdf_exporter.py
import sys
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.table import Table
from PyQt6.QtWidgets import QTableWidget

def export_table_to_pdf(table: QTableWidget, file_path: str, title: str, orientation: str = 'portrait', font_size: int = 12):
    font_prop = font_manager.FontProperties(
        family='Malgun Gothic' if sys.platform == 'win32' else 'AppleGothic',
        size=font_size
    )

    def wrap_text(text, max_length=15):
        return text  # 줄바꿈 제거 (필요시 수정 가능)

    with PdfPages(file_path) as pdf:
        if orientation == 'landscape':
            fig, ax = plt.subplots(figsize=(11.69, 8.27))  # A4 landscape
        else:
            fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 portrait
        fig.suptitle(title, fontproperties=font_prop, fontsize=14, y=0.98)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
        ax.axis('off')

        headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        rows = []
        for row in range(table.rowCount()):
            row_data = [table.item(row, col).text() if table.item(row, col) else "" for col in range(table.columnCount())]
            rows.append(row_data)

        table_data = [headers] + rows
        row_count = len(table_data)
        height_unit = font_size / 600  # constant row height per cell line
        row_heights = [height_unit * max(cell.count("\n") + 1 for cell in row) for row in table_data]
        unified_row_heights = [height_unit * max(cell.count("\n") + 1 for cell in row) for row in table_data]
        avg_cell_height = sum(row_heights) / row_count
        total_table_height = avg_cell_height * row_count
        bbox_top = 0.9
        bbox_bottom = 0.1
        available_height = bbox_top - bbox_bottom
        height_ratio = min(total_table_height, available_height)
        adjusted_bbox = [0.01, bbox_top - height_ratio, 0.98, height_ratio]

        tab = Table(ax, bbox=adjusted_bbox)
        col_count = table.columnCount()
        col_lengths = [max(len(str(table_data[row][col])) for row in range(len(table_data))) for col in range(col_count)]
        total_length = sum(col_lengths)
        col_widths = [length / total_length for length in col_lengths]

        for i, row in enumerate(table_data):
            for j, cell in enumerate(row):
                wrapped_cell = wrap_text(cell, max_length=12)
                cell_height = unified_row_heights[i]
                cell_obj = tab.add_cell(
                    i, j, col_widths[j], cell_height, text=wrapped_cell, loc='center',
                    facecolor='#cccccc' if i == 0 else 'white'
                )
                cell_obj.get_text().set_fontproperties(font_prop)
                # Set font size explicitly once per cell
                cell_obj.get_text().set_fontsize(font_size)
                cell_obj.set_height(cell_height)

        ax.add_table(tab)
        pdf.savefig(fig)
        plt.close(fig)