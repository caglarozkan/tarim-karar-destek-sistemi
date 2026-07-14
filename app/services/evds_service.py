import os
import pandas as pd
from dotenv import load_dotenv
from evds import evdsAPI

load_dotenv()


class EVDSService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("EVDS_API_KEY")

        if not self.api_key:
            raise ValueError("EVDS_API_KEY bulunamadı. .env dosyasına ekle.")

        self.client = evdsAPI(self.api_key)

    def get_series(self, series_codes, start_date, end_date):
        if isinstance(series_codes, str):
            series_codes = [series_codes]

        df = self.client.get_data(
            series_codes,
            startdate=start_date,
            enddate=end_date
        )

        if df is None or df.empty:
            return pd.DataFrame()

        return self._clean_evds_dataframe(df)

    def get_seasonal_average(self, series_codes, start_date, end_date):
        df = self.get_series(series_codes, start_date, end_date)

        if df.empty:
            return df

        df["year"] = df["date"].dt.year

        season_map = {
            12: "Winter",
            1: "Winter",
            2: "Winter",
            3: "Spring",
            4: "Spring",
            5: "Spring",
            6: "Summer",
            7: "Summer",
            8: "Summer",
            9: "Fall",
            10: "Fall",
            11: "Fall",
        }

        season_order = ["Winter", "Spring", "Summer", "Fall"]

        df["season"] = df["date"].dt.month.map(season_map)

        value_columns = [
            col for col in df.columns
            if col not in ["date", "year", "season"]
        ]

        seasonal_df = (
            df.groupby(["year", "season"], as_index=False)[value_columns]
            .mean()
        )

        seasonal_df["season"] = pd.Categorical(
            seasonal_df["season"],
            categories=season_order,
            ordered=True
        )

        seasonal_df = seasonal_df.sort_values(["year", "season"]).reset_index(drop=True)

        return seasonal_df

    def save_seasonal_inflation_csv(
        self,
        output_path="data/processed/data_files/seasonal_inflation.csv",
        series_code="TP.FG.J0"
    ):
        seasonal_df = self.get_seasonal_average(
            series_codes=series_code,
            start_date="01-01-2013",
            end_date="31-12-2026"
        )

        if seasonal_df.empty:
            print("EVDS verisi boş döndü.")
            return seasonal_df

        value_columns = [
            col for col in seasonal_df.columns
            if col not in ["year", "season"]
        ]

        if len(value_columns) != 1:
            raise ValueError("Tek bir enflasyon serisi bekleniyordu.")

        seasonal_df = seasonal_df.rename(
            columns={value_columns[0]: "inflation_index"}
        )

        seasonal_df["annual_inflation_pct"] = (
            seasonal_df
            .groupby("season", observed=True)["inflation_index"]
            .pct_change() * 100.
        ).round(2)

        seasonal_df = seasonal_df[
            (seasonal_df["year"] >= 2014) &
            (seasonal_df["year"] <= 2026)
        ].reset_index(drop=True)

        self._save_csv(seasonal_df, output_path)

        return seasonal_df

    @staticmethod
    def _clean_evds_dataframe(df):
        df = df.copy()

        if "Tarih" in df.columns:
            df = df.rename(columns={"Tarih": "date"})
        elif "DATE" in df.columns:
            df = df.rename(columns={"DATE": "date"})
        elif "Date" in df.columns:
            df = df.rename(columns={"Date": "date"})
        else:
            df = df.rename(columns={df.columns[0]: "date"})

        df["date"] = df["date"].apply(EVDSService.parse_evds_date)

        for col in df.columns:
            if col == "date":
                continue

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
            )

            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["date"]).reset_index(drop=True)

        return df

    @staticmethod
    def parse_evds_date(value):
        if pd.isna(value):
            return pd.NaT

        value = str(value).strip()

        formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m-%Y",
            "%Y-%m",
            "%m/%Y",
            "%Y/%m",
        ]

        for fmt in formats:
            try:
                return pd.to_datetime(value, format=fmt)
            except ValueError:
                pass

        return pd.to_datetime(value, errors="coerce", dayfirst=True)

    @staticmethod
    def _save_csv(df, output_path):
        folder = os.path.dirname(output_path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"CSV kaydedildi: {output_path}")


if __name__ == "__main__":
    evds_service = EVDSService()

    seasonal_inflation = evds_service.save_seasonal_inflation_csv(
        output_path="data/processed/data_files/seasonal_inflation.csv",
        series_code="TP.FG.J0"
    )

    print(seasonal_inflation.head(20))
    print(seasonal_inflation.tail(20))