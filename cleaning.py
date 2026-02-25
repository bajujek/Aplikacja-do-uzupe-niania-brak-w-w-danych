import pandas as pd

def clean_column(series):
    # Usuń spacje z początku i końca
    series = series.astype(str).str.strip()

    # Zamień znane puste i błędne wartości na NaN
    series = series.replace(
        to_replace=[r'^\s*$', 'nan', 'NaN', 'null', 'None', '<NA>'],
        value=pd.NA,
        regex=True
    )
    return series

def remove_rows_with_missing(df, columns=None):
    if columns is not None:
        return df.dropna(subset=columns)
    else:
        return df.dropna()

