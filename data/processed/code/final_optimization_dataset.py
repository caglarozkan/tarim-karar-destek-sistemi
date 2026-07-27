import pandas as pd

market = pd.read_csv("data/processed/data_files/final_risk_dataset.csv")
market=market.drop(columns=["fertilizer_price","diesel_price"])
final_df=market.drop_duplicates()
final_df.to_csv("data/processed/data_files/final_optimization.csv",index=False)