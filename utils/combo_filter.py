from PyQt6.QtWidgets import QComboBox
import pandas as pd

def combo_fillter(df: pd.DataFrame, year_combo: QComboBox, month_combo: QComboBox, day_combo: QComboBox = None, date_column: str = "접수일", on_change_callback=None) -> pd.DataFrame:
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df = df.dropna(subset=[date_column])
    df["접수년"] = df[date_column].dt.year
    df["월"] = df[date_column].dt.month
    df["월일"] = df[date_column].dt.strftime("%m-%d")
    df["일"] = df["월일"].str.slice(start=3).astype(int)

    year_combo.blockSignals(True)
    month_combo.blockSignals(True)
    if day_combo:
        day_combo.blockSignals(True)

    year_combo.clear()
    month_combo.clear()
    if day_combo:
        day_combo.clear()

    years = sorted(df["접수년"].unique())
    if not years:
        return df

    year_combo.addItems([str(y) for y in years])
    latest_year = years[-1]
    year_combo.setCurrentText(str(latest_year))

    months = sorted(df[df["접수년"] == latest_year]["월"].unique())
    if months:
        month_combo.addItems([str(m) for m in months])
        latest_month = months[-1]
        month_combo.setCurrentText(str(latest_month))

        if day_combo:
            days = sorted(
                df[
                    (df["접수년"] == latest_year) &
                    (df["월"] == latest_month)
                ]["월일"].str.slice(start=3).astype(int).unique()
            )
            print(f"📌 days generated: {days}")
            day_combo.addItems([str(d) for d in days])
            if days:
                day_combo.setCurrentText(str(days[-1]))

    year_combo.blockSignals(False)
    month_combo.blockSignals(False)
    if day_combo:
        day_combo.blockSignals(False)

    if on_change_callback:
        year_combo.currentIndexChanged.connect(on_change_callback)
        month_combo.currentIndexChanged.connect(on_change_callback)
        if day_combo:
            day_combo.currentIndexChanged.connect(on_change_callback)

    # ✅ 연도/월 변경 시 day 콤보 동적 갱신 추가
    if day_combo:
        year_combo.currentIndexChanged.connect(lambda: update_day_combo(df, year_combo, month_combo, day_combo))
        month_combo.currentIndexChanged.connect(lambda: update_day_combo(df, year_combo, month_combo, day_combo))

    return df

def update_day_combo(df: pd.DataFrame, year_combo: QComboBox, month_combo: QComboBox, day_combo: QComboBox, date_column: str = "접수일"):
    selected_year = year_combo.currentText()
    selected_month = month_combo.currentText()

    if not selected_year or not selected_month:
        return

    selected_year = int(selected_year)
    selected_month = int(selected_month)

    days = sorted(
        df[
            (df["접수년"] == selected_year) & 
            (df["월"] == selected_month)
        ]["월일"].str.slice(start=3).astype(int).unique()
    )
    print(f"📌 update_day_combo() days: {days}")

    day_combo.blockSignals(True)
    day_combo.clear()
    day_combo.addItems([str(d) for d in days])
    if days:
        day_combo.setCurrentText(str(days[-1]))
    day_combo.blockSignals(False)