from widgets.base_report_widget import BaseReportWidget
from utils.combo_filter import combo_fillter
from PyQt6.QtWidgets import QTableWidgetItem, QFileDialog
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt
import pandas as pd
from .monthly_pie_dialog import MonthlyPieDialog
from .monthly_store_report_view import MonthlyStoreReportView

class MonthlyStatusView(BaseReportWidget):
    def __init__(self, parent=None, pdf_button_label="PDF 저장"):
        super().__init__(
            title_text="",
            parent=parent,
            pdf_button_label=pdf_button_label,
            on_combo_change=self.load_data,
            on_pdf_click=self.export_pdf
        )
        self.day_combo.hide()


    def set_full_data(self, df):
        if df is None or df.empty:
            return

        self.full_df = combo_fillter(
            df.copy(),
            self.year_combo,
            self.month_combo,
            day_combo=self.day_combo,  # 생략 가능
            on_change_callback=lambda *_: self.load_data()
        )
        self.load_data()
        
        
    def export_pdf(self):
        try:
            if self.table.rowCount() == 0:
                print("❌ 출력할 데이터가 없습니다.")
                return

            save_path, _ = QFileDialog.getSaveFileName(self, "PDF 저장", "", "PDF Files (*.pdf)")
            if not save_path:
                return

            selected_month = self.month_combo.currentText()
            title = f"{selected_month} 월 단위 민원 리포트"
            from utils.pdf_exporter import export_table_to_pdf
            export_table_to_pdf(self.table, save_path, title, orientation="landscape", font_size=12)

            print(f"✅ PDF 저장 완료: {save_path}")
        except Exception as e:
            print(f"❌ PDF 저장 중 오류 발생: {e}")

    def load_data(self):
        print("📌 load_data() 호출됨")
        if self.full_df is None:
            return

        year = self.year_combo.currentText()
        month = self.month_combo.currentText()
        if not year or not month:
            return

        selected_year = int(year)
        selected_month = int(month)
        pre_year = selected_year if selected_month > 1 else selected_year - 1
        pre_month = selected_month - 1 if selected_month > 1 else 12

        self.label.setText(f"{selected_year}년 {selected_month}월 단위 민원 리포트")

        # ✅ 전체 카드사 목록 확보 (선택월에 없더라도 포함)
        all_card_companies = self.full_df["카드사"].astype(str).str.strip().unique()
        all_merchants = self.full_df["가맹점명"].astype(str).str.strip().unique()

        # ✅ 필터링된 월별 데이터
        df = self.full_df[
            (self.full_df["접수년"].isin([selected_year, pre_year])) &
            (self.full_df["월"].isin([selected_month, pre_month]))
        ].copy()

        df["카드사"] = df["카드사"].astype(str).str.strip()
        df["가맹점명"] = df["가맹점명"].astype(str).str.strip()

        grouped = df.groupby(["가맹점명", "카드사", "접수년", "월"]).size().reset_index(name="민원건수")
        pivot = grouped.pivot_table(
            index=["가맹점명", "카드사"],
            columns=["접수년", "월"],
            values="민원건수",
            fill_value=0
        ).sort_index(axis=1).reset_index()

        result_df = pd.DataFrame({"가맹점명": all_merchants})

        for card in all_card_companies:
            card_df = pivot[pivot["카드사"] == card]

            pre_counts = card_df.set_index("가맹점명").get((pre_year, pre_month), pd.Series(dtype=int))
            cur_counts = card_df.set_index("가맹점명").get((selected_year, selected_month), pd.Series(dtype=int))

            pre_counts = pre_counts.reindex(all_merchants, fill_value=0)
            cur_counts = cur_counts.reindex(all_merchants, fill_value=0)

            rate_display = []
            for i in range(len(pre_counts)):
                pre = pre_counts.iloc[i]
                cur = cur_counts.iloc[i]
                if pre == 0:
                    rate_display.append("신규" if cur > 0 else "0.0%")
                else:
                    diff_rate = ((cur - pre) / pre) * 100
                    rate_display.append(f"{diff_rate:.1f}%")

            result_df[f"{card}_전월"] = pre_counts.values
            result_df[f"{card}_당월"] = cur_counts.values
            result_df[f"{card}_증감률"] = rate_display


        df = result_df
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setAlternatingRowColors(True)

        for row_idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()