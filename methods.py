import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer, KNNImputer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder

def _detect_decimal_places(series):
    """Zwraca średnią liczbę miejsc po przecinku w niepustych wartościach serii."""
    floats = series.dropna().astype(float)
    if floats.empty:
        return 4  # domyślnie 4, jeśli brak danych
    decimal_counts = floats.apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
    avg_decimals = int(round(decimal_counts.mean()))
    return max(0, avg_decimals)

def fillna_mean(series):
    """Uzupełnia braki średnią, zaokrąglając do średniej liczby miejsc po przecinku w kolumnie."""
    if pd.api.types.is_numeric_dtype(series):
        decimals = _detect_decimal_places(series)
        mean_val = round(series.mean(), decimals)
        return series.fillna(mean_val).round(decimals)
    return series

def fillna_median(series):
    """Uzupełnia braki medianą, zaokrąglając do średniej liczby miejsc po przecinku w kolumnie."""
    if pd.api.types.is_numeric_dtype(series):
        decimals = _detect_decimal_places(series)
        median_val = round(series.median(), decimals)
        return series.fillna(median_val).round(decimals)
    return series

def fillna_value(series, value):
    """Uzupełnia braki podaną wartością (zaokrągla jeśli liczba)."""
    if pd.api.types.is_numeric_dtype(series):
        decimals = _detect_decimal_places(series)
        try:
            value = round(float(value), decimals)
        except Exception:
            value = 0
        return series.fillna(value).round(decimals)
    return series.fillna(value)

def fillna_group_mean(df, target_col, group_cols):
    """Uzupełnia braki w kolumnie numerycznej średnią wyliczoną w grupach wskazanych kolumn (jednej lub wielu)."""
    # Normalizuj listę kolumn grupujących
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    group_cols = [c for c in group_cols if c in df.columns and c != target_col]
    if target_col not in df.columns or not group_cols:
        return df[target_col]
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        return df[target_col]
    decimals = _detect_decimal_places(df[target_col])
    base = df[df[target_col].notna()]
    if base.empty:
        return df[target_col]
    grouped = base.groupby(group_cols)[target_col].mean().round(decimals)
    filled = df[target_col].copy()
    mask = filled.isna()

    # Buduj klucze zgodnie z liczbą kolumn grupujących
    if len(group_cols) == 1:
        key_series = df[group_cols[0]]
        filled.loc[mask] = key_series[mask].map(grouped)
    else:
        key_series = df[group_cols].apply(lambda row: tuple(row.values), axis=1)
        key_map = grouped
        filled.loc[mask] = key_series[mask].map(key_map)

    if filled.isna().any():
        overall = round(df[target_col].mean(), decimals)
        filled = filled.fillna(overall)
    return filled.round(decimals)

def fillna_regression(df, target_col):
    """
    Uzupełnia braki w kolumnie target_col na podstawie regresji liniowej z pozostałych kolumn numerycznych.
    """
    if target_col not in df.columns:
        return df[target_col]
    num_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col, errors='ignore')
    if len(num_cols) == 0:
        return df[target_col]
    notnull = df[target_col].notnull() & df[num_cols].notnull().all(axis=1)
    nulls = df[target_col].isnull() & df[num_cols].notnull().all(axis=1)
    if notnull.sum() == 0 or nulls.sum() == 0:
        return df[target_col]
    X_train = df.loc[notnull, num_cols]
    y_train = df.loc[notnull, target_col]
    X_pred = df.loc[nulls, num_cols]
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_pred)
    decimals = _detect_decimal_places(df[target_col])
    filled = df[target_col].copy()
    filled.loc[nulls] = np.round(y_pred, decimals)
    return filled

def fillna_mice(df, target_col):
    """
    Uzupełnia braki w kolumnie target_col za pomocą MICE (IterativeImputer).
    """
    if target_col not in df.columns:
        return df[target_col]
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) < 2:
        return df[target_col]
    imputer = IterativeImputer(max_iter=10, random_state=0)
    imputed = imputer.fit_transform(df[num_cols])
    imputed_df = pd.DataFrame(imputed, columns=num_cols, index=df.index)
    decimals = _detect_decimal_places(df[target_col])
    filled = df[target_col].copy()
    mask = df[target_col].isnull()
    filled[mask] = np.round(imputed_df.loc[mask, target_col], decimals)
    return filled

def fillna_unknown(series):
    """Uzupełnia braki tekstowe wartością 'Unknown'."""
    return series.fillna('Unknown')

def fillna_mode(series):
    """Uzupełnia braki najczęściej występującą wartością tekstową."""
    if series.dropna().empty:
        return series
    mode_val = series.mode().iloc[0]
    return series.fillna(mode_val)

def fillna_knn_categorical(df, target_col, n_neighbors=5):
    """
    Uzupełnia braki w kolumnie kategorycznej target_col za pomocą KNN (na podstawie pozostałych cech).
    Pomija wiersze z brakami w cechach predykcyjnych.
    """
    if target_col not in df.columns:
        return df[target_col]
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    encoders = {}
    temp = df[cat_cols].copy()
    for col in cat_cols:
        enc = LabelEncoder()
        notnull_mask = temp[col].notnull()
        temp.loc[notnull_mask, col] = enc.fit_transform(temp.loc[notnull_mask, col].astype(str))
        temp.loc[~notnull_mask, col] = np.nan
        encoders[col] = enc
    mask = df[target_col].notnull()
    # Użyj tylko wierszy bez braków w cechach predykcyjnych
    X_train = temp[mask].drop(columns=[target_col])
    y_train = temp[mask][target_col].astype(float)
    valid_train = X_train.notnull().all(axis=1)
    X_train = X_train[valid_train]
    y_train = y_train[valid_train]
    X_pred = temp[~mask].drop(columns=[target_col])
    valid_pred = X_pred.notnull().all(axis=1)
    X_pred = X_pred[valid_pred]
    if X_pred.empty or X_train.empty:
        return df[target_col]
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    knn.fit(X_train, y_train)
    y_pred = knn.predict(X_pred)
    enc = encoders[target_col]
    y_pred = y_pred.astype(int)
    filled = df[target_col].copy()
    # Uzupełnij tylko te wiersze, które mają komplet cech predykcyjnych
    idx_pred = X_pred.index
    filled.loc[idx_pred] = enc.inverse_transform(y_pred)
    return filled

def fillna_logreg_categorical(df, target_col):
    """
    Uzupełnia braki w kolumnie kategorycznej target_col za pomocą regresji logistycznej (klasyfikacji).
    """
    if target_col not in df.columns:
        return df[target_col]
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    # Użyj osobnego LabelEncoder dla każdej kolumny
    encoders = {}
    temp = df[cat_cols].copy()
    for col in cat_cols:
        enc = LabelEncoder()
        notnull_mask = temp[col].notnull()
        temp.loc[notnull_mask, col] = enc.fit_transform(temp.loc[notnull_mask, col].astype(str))
        temp.loc[~notnull_mask, col] = np.nan
        encoders[col] = enc
    mask = df[target_col].notnull()
    X_train = temp[mask].drop(columns=[target_col])
    y_train = temp[mask][target_col].astype(float)
    valid_train = X_train.notnull().all(axis=1)
    X_train = X_train[valid_train]
    y_train = y_train[valid_train]
    X_pred = temp[~mask].drop(columns=[target_col])
    valid_pred = X_pred.notnull().all(axis=1)
    X_pred = X_pred[valid_pred]
    if X_pred.empty or X_train.empty:
        return df[target_col]
    clf = LogisticRegression(max_iter=200)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_pred)
    enc = encoders[target_col]
    y_pred = y_pred.astype(int)
    filled = df[target_col].copy()
    idx_pred = X_pred.index
    filled.loc[idx_pred] = enc.inverse_transform(y_pred)
    return filled

def fillna_group_mode(df, target_col, group_cols):
    """Uzupełnia braki w kolumnie kategorycznej modą obliczoną w grupach (jednej lub wielu kolumn)."""
    if target_col not in df.columns:
        return df[target_col]
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    group_cols = [c for c in group_cols if c in df.columns and c != target_col]
    if not group_cols:
        return df[target_col]
    base = df[df[target_col].notna()]
    if base.empty:
        return df[target_col]

    # Wylicz modę dla każdej grupy; jeśli wiele mod, wybierz pierwszą z mode()
    grouped_mode = base.groupby(group_cols)[target_col].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA)

    filled = df[target_col].copy()
    mask = filled.isna()
    if len(group_cols) == 1:
        key_series = df[group_cols[0]]
        filled.loc[mask] = key_series[mask].map(grouped_mode)
    else:
        key_series = df[group_cols].apply(lambda row: tuple(row.values), axis=1)
        filled.loc[mask] = key_series[mask].map(grouped_mode)

    # Fallback: global moda
    if filled.isna().any():
        global_mode = df[target_col].mode()
        if not global_mode.empty:
            filled = filled.fillna(global_mode.iloc[0])
    return filled
