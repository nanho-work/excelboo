import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.table import Table
from PyQt6.QtWidgets import QTableWidget

def export_table_to_pdf(table: QTableWidget, file_path: str, title: str, orientation: str = 'portrait', font_size: int = 12, highlight_bold_rows: bool = False):
    try:
        TITLE_FONT_SIZE = 14  # 타이틀용 폰트 크기 (고정)
        import sys
        font_prop = font_manager.FontProperties(
            family='Malgun Gothic' if sys.platform == 'win32' else 'AppleGothic',
            size=font_size
        )

        with PdfPages(file_path) as pdf:  # 페이지를 위한 PDF 파일 저장 시작
            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]  # 테이블의 헤더 추출
            rows = []
            for row in range(table.rowCount()):
                row_data = [table.item(row, col).text() if table.item(row, col) else "" for col in range(table.columnCount())]
                rows.append(row_data)  # 테이블의 모든 데이터 행 추출

            table_data = [headers] + rows  # headers 포함된 상태로 테이블 전체 데이터 구성
            col_count = table.columnCount()
            col_lengths = [max(len(str(table_data[row][col])) for row in range(len(table_data))) for col in range(col_count)]  # 열별 최대 텍스트 길이 계산
            total_length = sum(col_lengths)
            col_widths = [length / total_length for length in col_lengths]  # 열 너비 비율 계산

            # Calculate how many rows fit per page
            global_prev_value = None

            current_row = 0
            page_num = 1
            while current_row < len(table_data):  # 페이지 반복 출력
                if orientation == 'landscape':
                    fig, ax = plt.subplots(figsize=(11.69, 8.27))  # A4 가로/세로 크기 지정
                else:
                    fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 가로/세로 크기 지정

                fig.suptitle(f"{title} (p.{page_num})", fontproperties=font_prop, fontsize=TITLE_FONT_SIZE, y=0.98)  # 타이틀 설정
                fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.04)  # 여백 조정 (왼쪽, 오른쪽, 상단, 하단)
                ax.axis('off')  # 축 숨김 처리

                # Calculate how many rows fit on this page based on actual heights
                rows_per_page = 30 - 1  # 헤더 포함으로 실제 데이터 행 수는 29
                end_row = min(current_row + rows_per_page, len(table_data))  # 고정된 행 수만큼 출력

                page_rows = []
                for i in range(current_row, end_row):
                    row = table_data[i]
                    original_first_col = row[0]

                    if original_first_col and global_prev_value == original_first_col:
                        row = [""] + row[1:]
                    elif original_first_col:
                        global_prev_value = original_first_col

                    if i == current_row and row[0] == "" and global_prev_value:
                        row[0] = global_prev_value

                    page_rows.append(row)

                # 첫 페이지인 경우 (헤더 이미 포함됨)에는 중복 방지
                if current_row == 0:
                    page_rows = [headers] + page_rows[1:]
                else:
                    page_rows = [headers] + page_rows

                # 빈 행 추가: 총 행 수가 30 + 헤더 1개 = 31이 되도록 유지
                while len(page_rows) < rows_per_page + 1:
                    page_rows.append([""] * col_count)

                adjusted_bbox = [0.01, 0.02, 0.98, 0.96]

                tab = Table(ax, bbox=adjusted_bbox)  # 테이블 생성
                from PyQt6.QtCore import Qt
                for i, row in enumerate(page_rows):
                    for j, cell in enumerate(row):
                        alignment = Qt.AlignmentFlag.AlignCenter  # 기본값
                        if i > 0 and table.item(current_row + i - 1, j):  # 데이터 행이고, 셀이 존재한다면
                            alignment = table.item(current_row + i - 1, j).textAlignment()

                        if alignment & Qt.AlignmentFlag.AlignLeft:
                            cell_loc = 'left'
                        elif alignment & Qt.AlignmentFlag.AlignRight:
                            cell_loc = 'right'
                        else:
                            cell_loc = 'center'  # 기본값

                        cell_height = (adjusted_bbox[3] - adjusted_bbox[1]) / len(page_rows)
                        cell_obj = tab.add_cell(
                            i, j, col_widths[j], cell_height, text=cell, loc=cell_loc,
                            facecolor='#e0f0ff' if i == 0 else 'white'  # 헤더는 회색, 나머지는 흰색 배경
                        )
                        cell_obj.PAD = 0.1
                        cell_obj.get_text().set_fontproperties(font_prop)  # 셀 텍스트 설정 및 폰트 속성 적용
                        cell_obj.get_text().set_fontsize(font_size)  # 셀 내부 폰트 크기 (기본값 12)
                        if highlight_bold_rows and i > 0:
                            qt_row_index = current_row + i - 1  # Adjust for header
                            if 0 <= qt_row_index < table.rowCount():  # Ensure valid index
                                first_item = table.item(qt_row_index, 0)
                                if first_item and ">>" in first_item.text():
                                    cell_obj.get_text().set_weight("bold")
                                else:
                                    cell_obj.get_text().set_weight("normal")
                            else:
                                cell_obj.get_text().set_weight("normal")
                        else:
                            cell_obj.get_text().set_weight("normal")
                        cell_obj.set_height(cell_height)  # 셀 높이 지정

                        # 빈 행이면 테두리 투명 처리
                        if all(c == "" for c in row):
                            cell_obj.set_edgecolor((1, 1, 1, 0))  # 테두리 투명
                            cell_obj.set_facecolor("white")      # 배경은 흰색 유지

                ax.add_table(tab)  # 테이블 추가
                pdf.savefig(fig)  # PDF 저장 및 다음 페이지로
                plt.close(fig)
                current_row = end_row
                page_num += 1
    except Exception as e:
        print("[PDF EXPORT ERROR]", str(e))  # 예외 발생 시 출력