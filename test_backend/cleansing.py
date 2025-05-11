def data_cleansing(df):
  df.dropna(inplace=True)
  df.drop_duplicates(inplace=True)
  df.reset_index(drop=True, inplace=True)
  return df