import pandas as pd
from PyQt6.QtCore import Qt
from widgets.base_report_widget import BaseReportWidget
from utils.combo_filter import combo_fillter

class DailyStatusView(BaseReportWidget):
    def __init__(self, parent=None, pdf_button_label="PDF 파일 저장"):
        super().__init__(
            title_text="일 단위 민원 리포트",
            parent=parent,
            pdf_button_label=pdf_button_label,
            on_combo_change=self.load_data,
            on_pdf_click=self.export_pdf
        )

    def set_full_data(self, df):
        if df is None or df.empty:
            return

        df["접수일"] = pd.to_datetime(df["접수일"], errors="coerce")
        df = df.dropna(subset=["접수일"])
        df["접수년"] = df["접수일"].dt.year
        df["월"] = df["접수일"].dt.month
        df["월일"] = df["접수일"].dt.strftime("%m-%d")
        df["일"] = df["월일"].str.slice(start=3).astype(int)

        self.full_df = df

        # 콤보박스 수동 구성
        self.year_combo.blockSignals(True)
        self.month_combo.blockSignals(True)
        self.day_combo.blockSignals(True)

        self.year_combo.clear()
        self.month_combo.clear()
        self.day_combo.clear()

        years = sorted(df["접수년"].unique())
        if not years:
            return
        self.year_combo.addItems([str(y) for y in years])
        latest_year = years[-1]
        self.year_combo.setCurrentText(str(latest_year))

        months = sorted(df[df["접수년"] == latest_year]["월"].unique())
        self.month_combo.addItems([str(m) for m in months])
        latest_month = months[-1]
        self.month_combo.setCurrentText(str(latest_month))

        days = sorted(df[
            (df["접수년"] == latest_year) &
            (df["월"] == latest_month)
        ]["월일"].str.slice(start=3).astype(int).unique())
        self.day_combo.addItems([str(d) for d in days])
        self.day_combo.setCurrentText(str(days[-1]))

        print(f"✅ [셋업 확인] latest_year: {latest_year}")
        print(f"✅ [셋업 확인] latest_month: {latest_month}")
        print(f"✅ [셋업 확인] days: {days}")

        # 동적으로 연도/월 변경 시 일 콤보 업데이트
        from utils.combo_filter import update_day_combo
        self.year_combo.currentIndexChanged.connect(lambda: update_day_combo(self.full_df, self.year_combo, self.month_combo, self.day_combo))
        self.month_combo.currentIndexChanged.connect(lambda: update_day_combo(self.full_df, self.year_combo, self.month_combo, self.day_combo))

        self.year_combo.blockSignals(False)
        self.month_combo.blockSignals(False)
        self.day_combo.blockSignals(False)

        # 필터 변경 이벤트 연결
        self.year_combo.currentIndexChanged.connect(self.load_data)
        self.month_combo.currentIndexChanged.connect(self.load_data)
        self.day_combo.currentIndexChanged.connect(self.load_data)

    def export_pdf(self):
        try:
            if self.table.rowCount() == 0:
                print("❌ 출력할 데이터가 없습니다.")
                return

            from PyQt6.QtWidgets import QFileDialog
            from utils.pdf_exporter import export_table_to_pdf

            save_path, _ = QFileDialog.getSaveFileName(self, "PDF 저장", "", "PDF Files (*.pdf)")
            if not save_path:
                return

            selected_year = self.year_combo.currentText()
            selected_month = self.month_combo.currentText()
            selected_day = self.day_combo.currentText()
            title = f"{selected_year}년 {selected_month}월 {selected_day}일 단위 민원 리포트"
            export_table_to_pdf(self.table, save_path, title, orientation="portrait", font_size=12)
            print(f"✅ PDF 저장 완료: {save_path}")
        except Exception as e:
            print(f"❌ PDF 저장 중 오류 발생: {e}")

    def load_data(self):
        try:
            print("📌 load_data() 데일리 호출됨")  # 첫 줄에 넣어보세요
            if self.full_df is None:
                return

            year = self.year_combo.currentText()
            month = self.month_combo.currentText()
            day = self.day_combo.currentText()
            print(f"📌 year: '{year}', month: '{month}', day: '{day}'")
            if not year or not month or not day:
                print("❌ 필터값이 비어 있음. year/month/day 확인 필요")
                return

            selected_year = int(year)
            selected_month = int(month)
            selected_day = int(day)

            self.label.setText(f"{selected_year}년 {selected_month}월 가맹점 종합 리포트")

            self.full_df["접수일"] = pd.to_datetime(self.full_df["접수일"], errors="coerce")

            print("📌 [전처리 전] full_df 샘플:")
            print(self.full_df.head())
            print("📌 [전처리 전] full_df 컬럼:", self.full_df.columns.tolist())

            filtered_df = self.full_df[
                (self.full_df["접수년"] == selected_year) &
                (self.full_df["월"] == selected_month) &
                (self.full_df["월일"].str.slice(start=3).astype(int) == selected_day)
            ].copy()

            # 전처리
            filtered_df["입금금액"] = filtered_df["입금금액"].fillna(0).astype(int)
            filtered_df["승인금액"] = filtered_df["승인금액"].fillna(0)
            filtered_df["할부"] = pd.to_numeric(filtered_df["할부"], errors="coerce").fillna(0)

            grouped = filtered_df.groupby(["접수일", "가맹점명", "TID명"]).agg(
                민원건수=("TID명", "count"),
                기한내처리건수=("처리상태", lambda x: x.str.lower().eq("y").sum())
            ).reset_index()
            grouped["회신율"] = ((grouped["기한내처리건수"] / grouped["민원건수"]) * 100).round(1).astype(str) + "%"
            total_by_date = grouped.groupby("접수일")["민원건수"].transform("sum")
            grouped["날짜별민원비중"] = ((grouped["민원건수"] / total_by_date) * 100).round(1).astype(str) + "%"
            column_order = ["접수일", "가맹점명", "TID명", "날짜별민원비중", "민원건수", "기한내처리건수", "회신율"]
            grouped = grouped[column_order]

            self.table.clear()
            self.table.setColumnCount(len(grouped.columns))
            unique_merchants = grouped["가맹점명"].unique()
            from PyQt6.QtWidgets import QTableWidgetItem
            self.table.setRowCount(len(grouped))
            self.table.setHorizontalHeaderLabels(grouped.columns)
            self.table.verticalHeader().setDefaultSectionSize(30)
            self.table.setAlternatingRowColors(True)
            insert_offset = 0
            for idx, merchant in enumerate(unique_merchants):
                merchant_rows = grouped[grouped["가맹점명"] == merchant]
                for row_idx, (_, row) in enumerate(merchant_rows.iterrows()):
                    for j, val in enumerate(row):
                        if j in [0, 1] and row_idx > 0:
                            item = QTableWidgetItem("")  # Empty cell for duplicate 접수일, 가맹점명
                        else:
                            if j == 0 and isinstance(val, pd.Timestamp):
                                item = QTableWidgetItem(val.strftime("%Y-%m-%d"))
                            else:
                                item = QTableWidgetItem(str(val))
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                        if j == 0 or j == 1:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        elif "건수" in grouped.columns[j] or "율" in grouped.columns[j] or "비중" in grouped.columns[j]:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        else:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.table.setItem(insert_offset, j, item)
                    insert_offset += 1

            # ✅ 합계 행 추가
            summary_row = grouped[["민원건수", "기한내처리건수"]].sum()
            total_mw_count = summary_row["민원건수"]
            total_in_time = summary_row["기한내처리건수"]
            if total_mw_count > 0:
                reply_rate = f"{(total_in_time / total_mw_count * 100):.1f}%"
            else:
                reply_rate = "0.0%"

            summary_items = [
                QTableWidgetItem(""),  # 접수일
                QTableWidgetItem("합계"),  # 가맹점명
                QTableWidgetItem(""),  # TID명
                QTableWidgetItem(""),  # 날짜별민원비중 (합계에서는 제외)
                QTableWidgetItem(str(total_mw_count)),  # 민원건수
                QTableWidgetItem(str(total_in_time)),  # 기한내처리건수
                QTableWidgetItem(reply_rate)  # 회신율
            ]
            self.table.insertRow(insert_offset)
            for j, item in enumerate(summary_items):
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if j == 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                elif j in [4, 5]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(insert_offset, j, item)

            return  # Skip the existing rendering loop after this block

            # The following loop is now skipped; kept for reference but will not execute
            #for i, row in grouped.iterrows():
            #    for j, val in enumerate(row):
            #        if j == 0 and isinstance(val, pd.Timestamp):
            #            item = QTableWidgetItem(val.strftime("%Y-%m-%d"))
            #        else:
            #            item = QTableWidgetItem(str(val))
            #        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            #        if j == 0 or j == 1:
            #            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            #        elif "건수" in grouped.columns[j] or "율" in grouped.columns[j] or "비중" in grouped.columns[j]:
            #            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            #        else:
            #            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            #        self.table.setItem(i, j, item)

            self.table.resizeColumnsToContents()
        except Exception as e:
            print(f"❌ 데이터 로드 중 오류 발생: {e}")