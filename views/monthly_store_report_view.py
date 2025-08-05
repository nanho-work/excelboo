import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout, QComboBox, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from utils.pdf_exporter import export_table_to_pdf



class MonthlyStoreReportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_df = None
        self.setWindowTitle("월별 가맹점 종합리포트")
        self.resize(1200, 800)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        filter_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.month_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("월 선택"))
        filter_layout.addWidget(self.month_combo)
        # PDF 저장 버튼 추가
        self.export_button = QPushButton("PDF 저장")
        self.export_button.clicked.connect(self.export_pdf)
        filter_layout.addWidget(self.export_button)
        self.layout.addLayout(filter_layout)

        label = QLabel("2025년 7월 가맹점 종합 리포트")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(label)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

    def set_full_data(self, df):
        self.full_df = df.copy()
        self.full_df["접수일"] = pd.to_datetime(self.full_df["접수일"], errors="coerce")
        self.full_df["월"] = self.full_df["접수일"].dt.to_period("M")
        months = sorted(self.full_df["월"].astype(str).unique())
        self.month_combo.clear()
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(len(months) - 1)  # 최신 월 선택
        self.load_data()

    def load_data(self):
        if self.full_df is None:
            return

        selected_month = self.month_combo.currentText()
        if not selected_month:
            return

        df = self.full_df[self.full_df["월"].astype(str) == selected_month].copy()

        # 날짜 전처리 및 필터링
        df["접수일"] = pd.to_datetime(df["접수일"], errors="coerce")
        # 필터 제거 (테스트용) → 전체 데이터를 그대로 사용
        filtered_df = df

        # 숫자 컬럼 처리
        filtered_df["입금금액"] = filtered_df["입금금액"].fillna(0).astype(int)
        filtered_df["승인금액"] = filtered_df["승인금액"].fillna(0)
        filtered_df["할부"] = pd.to_numeric(filtered_df["할부"], errors="coerce").fillna(0)

        민원발생건수 = filtered_df.groupby(['가맹점명', 'TID명']).size().reset_index(name='민원발생건수')
        전체민원수 = filtered_df.shape[0]
        민원발생건수['비중(%)'] = (민원발생건수['민원발생건수'] / 전체민원수 * 100).round(1)

        처리완료_df = filtered_df[filtered_df['처리상태'] == 'Y']
        민원처리건수 = 처리완료_df.groupby(['가맹점명', 'TID명']).size().reset_index(name='민원처리건수')

        결과 = 민원발생건수.merge(민원처리건수, on=['가맹점명', 'TID명'], how='left')
        결과['민원처리건수'] = 결과['민원처리건수'].fillna(0).astype(int)
        결과['회신율(%)'] = ((결과['민원처리건수'] / 결과['민원발생건수']) * 100).round(1)

        거래액 = filtered_df.groupby(['가맹점명', 'TID명'])['승인금액'].sum().reset_index(name='거래액')
        거래액["거래액"] = 거래액["거래액"].fillna(0).astype(int)
        # '취소여부'가 '취소완료'인 경우만 필터링
        취소완료_df = filtered_df[filtered_df['취소여부'] == '취소완료']

        # 취소완료된 건의 입금금액만 합산
        취소금액 = 취소완료_df.groupby(['가맹점명', 'TID명'])['입금금액'].sum().reset_index(name='취소금액')
        미수금_df = filtered_df[filtered_df['입금여부'] == '미입금']
        미수금 = 미수금_df.groupby(['가맹점명', 'TID명'])['입금금액'].sum().reset_index(name='미수금')

        결과 = 결과.merge(거래액, on=['가맹점명', 'TID명'], how='left')
        결과 = 결과.merge(취소금액, on=['가맹점명', 'TID명'], how='left')
        결과 = 결과.merge(미수금, on=['가맹점명', 'TID명'], how='left')
        결과[['취소금액', '미수금']] = 결과[['취소금액', '미수금']].fillna(0).astype(int)
        결과['취소비율(%)'] = ((결과['취소금액'] / 결과['거래액']) * 100).round(1)
        결과['미수비율(%)'] = ((결과['미수금'] / 결과['거래액']) * 100).round(1)

        거래건수 = filtered_df.groupby(['가맹점명', 'TID명']).size().reset_index(name='거래건수')
        결과 = 결과.merge(거래건수, on=['가맹점명', 'TID명'], how='left')
        결과['평균객단가'] = (결과['거래액'] / 결과['거래건수']).round(0).fillna(0).astype(int)

        평균할부 = filtered_df.groupby(['가맹점명', 'TID명'])['할부'].mean().reset_index(name='평균할부')
        결과 = 결과.merge(평균할부, on=['가맹점명', 'TID명'], how='left')
        결과['평균할부'] = 결과['평균할부'].fillna(0).round(1)

        결과 = 결과.fillna("")

        # Insert subtotal rows per store
        subtotals = []
        for store, group in 결과.groupby('가맹점명'):
            subtotal = {
                "가맹점명": f"{store} >>",
                "TID명": "소계",
                "민원발생건수": group["민원발생건수"].sum(),
                "비중(%)": round(group["민원발생건수"].sum() / 전체민원수 * 100, 1) if 전체민원수 else 0,
                "민원처리건수": group["민원처리건수"].sum(),
                "회신율(%)": round(group["민원처리건수"].sum() / group["민원발생건수"].sum() * 100, 1) if group["민원발생건수"].sum() else 0,
                "거래액": group["거래액"].sum(),
                "취소금액": group["취소금액"].sum(),
                "미수금": group["미수금"].sum(),
                "취소비율(%)": round(group["취소금액"].sum() / group["거래액"].sum() * 100, 1) if group["거래액"].sum() else 0,
                "미수비율(%)": round(group["미수금"].sum() / group["거래액"].sum() * 100, 1) if group["거래액"].sum() else 0,
                "거래건수": group["거래건수"].sum(),
                "평균객단가": int(round(group["거래액"].sum() / group["거래건수"].sum(), 0)) if group["거래건수"].sum() else 0,
                "평균할부": round(group["평균할부"].mean(), 1)
            }
            subtotal["__row_type"] = "subtotal"
            insert_index = 결과[결과["가맹점명"] == store].index.max() + 1
            subtotals.append((insert_index, subtotal))

        # Insert subtotal rows back into 결과 DataFrame
        offset = 0
        for idx, subtotal_row in subtotals:
            결과 = pd.concat([
                결과.iloc[:idx + offset],
                pd.DataFrame([subtotal_row]),
                결과.iloc[idx + offset:]
            ]).reset_index(drop=True)
            offset += 1

        # 합계 행 추가
        total_민원처리건수 = 결과["민원처리건수"].sum()
        total_민원발생건수 = 결과["민원발생건수"].sum()
        total_전체민원수 = 전체민원수
        total_거래액 = 결과["거래액"].sum()
        total_취소금액 = 결과["취소금액"].sum()
        total_미수금 = 결과["미수금"].sum()

        total_row = {
            "가맹점명": "합계",
            "TID명": "",
            "민원발생건수": total_민원발생건수,
            "비중(%)": round((total_민원발생건수 / total_전체민원수) * 100, 1) if total_전체민원수 else "",
            "민원처리건수": total_민원처리건수,
            "회신율(%)": round((total_민원처리건수 / total_민원발생건수) * 100, 1) if total_민원발생건수 else "",
            "거래액": total_거래액,
            "취소금액": total_취소금액,
            "미수금": total_미수금,
            "취소비율(%)": round((total_취소금액 / total_거래액) * 100, 1) if total_거래액 else "",
            "미수비율(%)": round((total_미수금 / total_거래액) * 100, 1) if total_거래액 else "",
            "거래건수": 결과["거래건수"].sum(),
            "평균객단가": int(round(total_거래액 / 결과["거래건수"].sum(), 0)) if 결과["거래건수"].sum() else "",
            "평균할부": round(결과["평균할부"].mean(), 1) if not 결과["평균할부"].isna().all() else ""
        }
        total_row["__row_type"] = "total"
        결과.loc[len(결과)] = total_row

        # 중복 가맹점명 제거: 동일 가맹점명의 첫 번째 행만 값 표시
        결과['__first_flag'] = ~결과.duplicated(subset=['가맹점명'])
        결과.loc[~결과['__first_flag'], '가맹점명'] = ""
        결과.drop(columns=['__first_flag'], inplace=True)

        unique_stores = 결과['가맹점명'].nunique()
        store_summary_label = QLabel(f"총 가맹점 수: {unique_stores}")
        store_summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(store_summary_label)

        header = [
            "가맹점명", "TID명", "민원발생건수", "비중(%)", "민원처리건수", "회신율(%)", "거래액", "취소금액",
            "미수금", "취소비율(%)", "미수비율(%)", "거래건수", "평균객단가", "평균할부"
        ]
        self.table.setColumnCount(len(header))
        self.table.setRowCount(len(결과))
        self.table.setHorizontalHeaderLabels(header)

        for row_idx, row_data in 결과.iterrows():
            for col_idx, col_name in enumerate(header):
                value = row_data[col_name]

                if col_name in ["거래액", "취소금액", "미수금", "평균객단가"]:
                    display_value = f"{int(float(value)):,}"
                else:
                    display_value = str(value)

                item = QTableWidgetItem(display_value)
                if row_data.get("__row_type") in ["subtotal", "total"]:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if col_name in ["거래액", "취소금액", "미수금", "평균객단가"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

    def export_pdf(self):
        try:
            if self.table.rowCount() == 0:
                print("❌ 출력할 데이터가 없습니다.")
                return

            save_path, _ = QFileDialog.getSaveFileName(self, "PDF 저장", "", "PDF Files (*.pdf)")
            if not save_path:
                return

            # Replace the existing PDF export logic with the new call including orientation and font_size
            selected_month = self.month_combo.currentText()
            title = f"{selected_month} 가맹점 종합리포트"
            export_table_to_pdf(self.table, save_path, title, orientation="landscape", font_size=12)

            print(f"✅ PDF 저장 완료: {save_path}")
        except Exception as e:
            print(f"❌ PDF 저장 중 오류 발생: {e}")