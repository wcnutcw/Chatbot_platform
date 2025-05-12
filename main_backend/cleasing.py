def cleansing(df_combined):
        df_combined.dropna(inplace=True)
        df_combined.drop_duplicates(inplace=True)
        df_combined.reset_index(drop=True, inplace=True)
        return df_combined