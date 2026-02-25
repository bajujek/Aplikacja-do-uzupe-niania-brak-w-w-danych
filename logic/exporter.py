import pandas as pd
from tkinter import filedialog, messagebox

def export_dataframe(df):
    """Eksportuje DataFrame do pliku CSV lub Excel z oknem dialogowym zapisu."""
    if df is None or df.empty:
        messagebox.showwarning("Brak danych", "Najpierw wczytaj plik.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
    if not file_path:
        return
    try:
        if file_path.endswith(".csv"):
            df.to_csv(file_path, index=False)
        else:
            df.to_excel(file_path, index=False)
        messagebox.showinfo("Sukces", "Dane zostały wyeksportowane.")
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się wyeksportować danych:\n{e}")
