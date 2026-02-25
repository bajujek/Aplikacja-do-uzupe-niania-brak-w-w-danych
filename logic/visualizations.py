import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import tkinter.messagebox as msg
import numpy as np

def show_missing_heatmap(df):
    plt.figure(figsize=(12, 6))
    # Oblicz procent braków dla każdej kolumny
    percent_missing = df.isnull().mean() * 100
    # Oblicz liczbę braków dla każdej kolumny
    missing_count = df.isnull().sum()

    sns.heatmap(df.isnull(), cbar=False, cmap="YlOrRd", yticklabels=False)
    
    plt.title("Mapa ciepła braków danych")
    # Domyślne etykiety kolumn
    plt.xticks(ticks=range(len(df.columns)), labels=df.columns, rotation=45, ha='right', fontsize=10)
    # Dodaj informację o procentach i liczbie braków pod każdą kolumną
    ax = plt.gca()
    ylim = ax.get_ylim()
    for i, col in enumerate(df.columns):
        percent = percent_missing[i]
        count = missing_count[i]
        percent_str = f"{percent:.0f}%" if percent >= 1 else ("<1%" if percent > 0 else "0%")
        label = f"{percent_str} - {count}"
        ax.text(i, ylim[0] - 0.5, label, ha='center', va='top', color='black', fontsize=10, fontweight='bold', rotation=0)
    plt.tight_layout()
    plt.show()

def show_value_counts(series):
    series = series.astype(str).str.strip()
    series = series.replace(
        to_replace=[r'^\s*$', 'nan', 'NaN', 'null', 'None', '<NA>'],
        value=pd.NA,
        regex=True
    )

    null_count = series.isna().sum()
    cleaned = series.dropna()
    numeric = pd.to_numeric(cleaned, errors="coerce").dropna()
    is_numeric = numeric.notna().sum() > 0

    if is_numeric and numeric.nunique() > 20:
        try:
            binned = pd.cut(numeric, bins=19)
            counts = binned.value_counts(sort=False).sort_index()
            
            avg = numeric.mean()
            labels = []

            # Dynamiczne zaokrąglenie
            if avg > 100:
                n = int(np.floor(np.log10(avg)))  # znajdź n takie że 10^n < avg <= 10^(n+1)
                rounding = 10**(n - 1)

                for interval in counts.index:
                    left = int(np.floor(interval.left / rounding) * rounding)
                    right = int(np.ceil(interval.right / rounding) * rounding) - 1
                    labels.append(f"{left}–{right}")
            else:
                for interval in counts.index:
                    left = int(round(interval.left)) + 1
                    right = int(round(interval.right))
                    labels.append(f"{left}–{right}")

            if null_count > 0:
                counts = pd.concat([counts, pd.Series([null_count], index=["Brak danych"])])
                labels.append("Brak danych")

        except Exception as e:
            msg.showerror("Błąd", f"Nie udało się stworzyć przedziałów:\n{e}")
            return
    else:
        counts = cleaned.value_counts()
        if null_count > 0:
            counts = pd.concat([counts, pd.Series({'Brak danych': null_count})])
        labels = counts.index.astype(str)

    if is_numeric:
        # Dla typów numerycznych pionowe słupki
        plt.figure(figsize=(max(10, len(counts) * 0.5), 5))
        ax = sns.barplot(x=labels, y=counts.values, width=0.8)
        plt.title("Histogram wartości")
        plt.ylabel("Liczba wystąpień")
        plt.xlabel("Wartość")
        plt.xticks(rotation=45)
        for i, v in enumerate(counts.values):
            ax.text(i, v + max(counts.values)*0.01, str(v), ha='center', va='bottom', fontsize=10, fontweight='bold')
    else:
        # Dla nienumerycznych poziome słupki
        plt.figure(figsize=(8, max(6, len(counts) * 0.4)))
        ax = sns.barplot(y=labels, x=counts.values, width=0.8, orient='h')
        plt.title("Histogram wartości")
        plt.xlabel("Liczba wystąpień")
        plt.ylabel("Wartość")
        for i, v in enumerate(counts.values):
            ax.text(v + max(counts.values)*0.01, i, str(v), ha='left', va='center', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.show()
