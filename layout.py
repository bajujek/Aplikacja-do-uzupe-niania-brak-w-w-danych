import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from logic.file_loader import load_file
from logic.cleaning import clean_column, remove_rows_with_missing
from logic.visualizations import show_missing_heatmap, show_value_counts
from logic.methods import fillna_mean, fillna_median, fillna_group_mean, fillna_group_mode
from logic.exporter import export_dataframe
import pandas as pd

class ExcelViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Uzupełnianie braków w danych")
        self.root.geometry("1000x700")
        self.df = None

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#e9ecef")
        self.style.configure("TLabel", background="#e9ecef", font=("Helvetica", 11))
        self.style.configure("TButton", font=("Helvetica", 11, "bold"), padding=8, background="#4078c0", foreground="#fff")
        self.style.map("TButton", background=[("active", "#305080")], foreground=[("active", "#fff")])
        self.style.configure("TCombobox", padding=8, font=("Helvetica", 11), fieldbackground="#fff", background="#fff")
        self.style.map("TCombobox",
            fieldbackground=[("readonly", "#fff")],
            background=[("readonly", "#fff")],
            selectbackground=[("readonly", "#fff")],
            selectforeground=[("readonly", "#222")]
        )
        self.root.configure(bg="#e9ecef")

        self.main_frame = ttk.Frame(root, padding=0, style="TFrame")
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.configure(style="TFrame")

        # Górna belka z tytułem i przyciskiem zamknij
        self.header_frame = tk.Frame(self.main_frame, bg="#4078c0", height=50)
        self.header_frame.pack(side="top", fill="x")
        self.header_frame.pack_propagate(False)
        self.title_label = tk.Label(self.header_frame, text="Uzupełnianie braków w danych", bg="#4078c0", fg="#fff", font=("Helvetica", 16, "bold"))
        self.title_label.pack(side="top", pady=8)
        self.close_button = tk.Button(self.header_frame, text="✖", bg="#4078c0", fg="#fff", font=("Helvetica", 12, "bold"), borderwidth=0, command=self.root.destroy, activebackground="#305080", activeforeground="#fff")
        self.close_button.place(relx=1.0, x=-10, y=10, anchor="ne")

        # Strona startowa
        self.start_frame = ttk.Frame(self.main_frame, padding=32, style="TFrame")
        self.start_frame.pack(fill="both", expand=True)
        self.welcome_label = ttk.Label(self.start_frame, text="Witaj w aplikacji do uzupełniania braków w danych!", style="TLabel", font=("Helvetica", 14, "bold"))
        self.welcome_label.pack(pady=40)
        self.start_load_button = ttk.Button(self.start_frame, text="Wczytaj dane", style="TButton", command=self.load_file)
        self.start_load_button.pack(pady=20)

    # Główny widok (ukryty na starcie)
        self.top_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.visual_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.text_area = tk.Text(self.main_frame, wrap=tk.WORD, font=("Consolas", 11), width=100, height=30, bg="#f8fafd", fg="#222", relief=tk.FLAT, borderwidth=2, highlightbackground="#4078c0", highlightcolor="#4078c0")

    # Pozostałe elementy głównego widoku
        self.load_button = ttk.Button(self.top_frame, text="Wczytaj plik", style="TButton", command=self.load_file)
        self.column_label = ttk.Label(self.top_frame, text="Wybierz kolumnę:", style="TLabel")
        self.column_combobox = ttk.Combobox(self.top_frame, state="readonly", width=60, style="TCombobox")
        self.column_combobox.bind("<<ComboboxSelected>>", self.display_column)
        self.fillna_button = ttk.Button(self.top_frame, text="Uzupełnij dane", style="TButton", command=self.open_fillna_dialog)
        self.heatmap_button = ttk.Button(self.visual_frame, text="Pokaż mapę ciepła braków", style="TButton", command=self.show_missing_heatmap)
        self.barplot_button = ttk.Button(self.visual_frame, text="Pokaż histogram wartości", style="TButton", command=self.show_value_counts)
        # Przycisk Zapisz z menu rozwijanym (tworzony tylko raz)
        self.save_menu_button = ttk.Menubutton(self.visual_frame, text="Zapisz ▼", style="TButton")
        self.save_menu = tk.Menu(self.save_menu_button, tearoff=0)
        self.save_menu.add_command(label="Zapisz jako", command=self.save_as_dialog)
        self.save_menu.add_command(label="Podział na próbkę treningową, walidacyjną oraz testową", command=self.prepare_ai_data)
        self.save_menu.add_command(label="Zapisz (nadpisz plik)", command=self.save_data)
        self.save_menu_button['menu'] = self.save_menu
    def show_main_view(self):
        # Ukryj stronę startową
        self.start_frame.pack_forget()
        # Ukryj widoki, jeśli były już pokazane
        self.top_frame.pack_forget()
        self.visual_frame.pack_forget()
        self.text_area.pack_forget()
    # Tylko pakowanie przycisku (nie tworzymy go ponownie)
        self.save_menu_button.pack(side="right", padx=8, pady=4)
        self.top_frame.pack(side="top", fill="x", pady=16)
        self.load_button.config(text="Wczytaj inny plik")
        self.load_button.pack(side="left", padx=8, pady=4)
        self.column_label.pack(side="left", padx=8)
        self.column_combobox.pack(side="left", padx=8)
        self.fillna_button.pack(side="left", padx=8, pady=4)

        self.visual_frame.pack(side="top", fill="x", pady=8)
        self.heatmap_button.pack(side="left", padx=8, pady=4)
        self.barplot_button.pack(side="left", padx=8, pady=4)
        self.save_menu_button.pack(side="right", padx=8, pady=4)
        self.text_area.pack(fill="both", expand=True, pady=16, padx=8)
        # Po wczytaniu pliku automatycznie wyświetl dane z pierwszej kolumny

        if self.df is not None and len(self.df.columns) > 0:
            col_with_types = [f"{col} ({self.df[col].dtype})" for col in self.df.columns]
            self.column_combobox['values'] = col_with_types
            self.column_combobox.set(col_with_types[0])
            self.display_column()

    def prepare_ai_data(self):
        self.save_menu_button.pack(side="right", padx=8, pady=4)
        if self.df is None:
            messagebox.showwarning("Brak danych", "Najpierw wczytaj plik.")
            return
        # Sprawdź czy są braki w całym DataFrame
        missing_total = self.df.isna().sum().sum()
        if missing_total > 0:
            missing_cols = [col for col in self.df.columns if self.df[col].isna().sum() > 0]
            msg = "Brakujące dane w kolumnach: " + ", ".join(missing_cols)
            messagebox.showwarning("Brakujące dane", msg)
            return
        # Okno do wpisania procentów podziału
        split_dialog = tk.Toplevel(self.root)
        split_dialog.title("Podział na próbki: trening/ walidacja/ test")
        split_dialog.configure(bg="#fff")
        tk.Label(split_dialog, text="Podaj procentowy podział danych (trening / walidacja / test):", bg="#fff").pack(pady=10)
        frame = tk.Frame(split_dialog, bg="#fff")
        frame.pack(pady=10)
        tk.Label(frame, text="Treningowe [%]", bg="#fff").grid(row=0, column=0, padx=5)
        train_entry = tk.Entry(frame, width=5)
        train_entry.grid(row=0, column=1, padx=5)
        train_entry.insert(0, "70")
        tk.Label(frame, text="Walidacyjne [%]", bg="#fff").grid(row=0, column=2, padx=5)
        val_entry = tk.Entry(frame, width=5)
        val_entry.grid(row=0, column=3, padx=5)
        val_entry.insert(0, "15")
        tk.Label(frame, text="Testowe [%]", bg="#fff").grid(row=0, column=4, padx=5)
        test_entry = tk.Entry(frame, width=5)
        test_entry.grid(row=0, column=5, padx=5)
        test_entry.insert(0, "15")
        def do_split_and_export():
            try:
                train_pct = float(train_entry.get())
                val_pct = float(val_entry.get())
                test_pct = float(test_entry.get())
                total = train_pct + val_pct + test_pct
                if abs(total - 100) > 0.1:
                    messagebox.showerror("Błąd podziału", "Suma procentów musi wynosić 100%.")
                    return
                # Podział danych
                df_shuffled = self.df.sample(frac=1, random_state=42).reset_index(drop=True)
                n = len(df_shuffled)
                train_end = int(n * train_pct / 100)
                val_end = train_end + int(n * val_pct / 100)
                df_train = df_shuffled.iloc[:train_end]
                df_val = df_shuffled.iloc[train_end:val_end]
                df_test = df_shuffled.iloc[val_end:]
                # Zapytaj o ścieżki zapisu
                train_path = filedialog.asksaveasfilename(defaultextension=".csv", title="Zapisz dane treningowe", initialfile="Dane treningowe.csv", filetypes=[("CSV files", "*.csv")])
                if not train_path:
                    return
                val_path = filedialog.asksaveasfilename(defaultextension=".csv", title="Zapisz dane walidacyjne", initialfile="Dane walidacyjne.csv", filetypes=[("CSV files", "*.csv")])
                if not val_path:
                    return
                test_path = filedialog.asksaveasfilename(defaultextension=".csv", title="Zapisz dane testowe", initialfile="Dane testowe.csv", filetypes=[("CSV files", "*.csv")])
                if not test_path:
                    return
                # Eksport plików
                df_train.to_csv(train_path, index=False)
                df_val.to_csv(val_path, index=False)
                df_test.to_csv(test_path, index=False)
                messagebox.showinfo("Sukces", f"Dane zostały podzielone i wyeksportowane jako:\n'{train_path}', '{val_path}', '{test_path}'")
                split_dialog.destroy()
            except Exception as e:
                messagebox.showerror("Błąd", f"Wystąpił błąd podczas podziału danych:\n{e}")
        ttk.Button(split_dialog, text="Podziel i eksportuj", command=do_split_and_export).pack(pady=10)
        ttk.Button(split_dialog, text="Anuluj", command=split_dialog.destroy).pack(pady=5)

    def load_file(self):
        file_types = [("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls")]
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if not file_path:
            return
        self.loaded_file_path = file_path  # zapisz ścieżkę do pliku
        try:
            self.df = load_file(file_path)
            if self.df is None or len(self.df.columns) == 0:
                messagebox.showerror("Błąd", "Plik nie zawiera danych lub nagłówków.")
                return
            col_with_types = [f"{col} ({self.df[col].dtype})" for col in self.df.columns]
            self.show_main_view()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać pliku:\n{e}")

    def save_as_dialog(self):
        if self.df is None:
            messagebox.showwarning("Brak danych", "Najpierw wczytaj plik.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls")], title="Zapisz jako")
        if not file_path:
            return
        try:
            if file_path.endswith(".csv"):
                self.df.to_csv(file_path, index=False)
            else:
                self.df.to_excel(file_path, index=False)
            messagebox.showinfo("Sukces", f"Dane zostały zapisane do pliku: {file_path}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać danych:\n{e}")

    def display_column(self, event=None):
        selected_item = self.column_combobox.get()
        if not selected_item or self.df is None:
            return

        column_name = selected_item.split(" (")[0]
        self.text_area.delete("1.0", tk.END)

        try:
            column_data = self.df[column_name].copy()
            column_data = clean_column(column_data)

            # Sprawdź, czy dane da się zrzutować na float
            converted_data = column_data.dropna()
            try:
                converted_data = converted_data.astype(float)
                data_type = "float"
            except:
                data_type = "object"

            total = len(column_data)
            missing = column_data.isna().sum()
            percent_missing = (missing / total) * 100

            self.text_area.insert(tk.END, f"📊 Profil kolumny '{column_name}':\n")
            self.text_area.insert(tk.END, f"- Typ danych: {data_type}\n")
            self.text_area.insert(tk.END, f"- Liczba rekordów: {total}\n")
            self.text_area.insert(tk.END, f"- Liczba braków: {missing} ({percent_missing:.2f}%)\n\n")
            self.text_area.insert(tk.END, column_data.to_string(index=False))
        except Exception as e:
            self.text_area.insert(tk.END, f"Błąd odczytu danych:\n{e}")

    def show_missing_heatmap(self):
        if self.df is None:
            messagebox.showwarning("Brak danych", "Najpierw wczytaj plik.")
            return
        show_missing_heatmap(self.df)

    def show_value_counts(self):
        selected_item = self.column_combobox.get()
        if not selected_item or self.df is None:
            messagebox.showwarning("Brak kolumny", "Wybierz kolumnę.")
            return
        column_name = selected_item.split(" (")[0]
        show_value_counts(self.df[column_name])

    def open_fillna_dialog(self):
        selected_item = self.column_combobox.get()
        if not selected_item or self.df is None:
            messagebox.showwarning("Brak kolumny", "Wybierz kolumnę.")
            return
        column_name = selected_item.split(" (")[0]
        dtype = self.df[column_name].dtype
        missing_count = self.df[column_name].isna().sum()
        if missing_count == 0:
            messagebox.showinfo("Brak brakujących danych", f"Kolumna '{column_name}' nie zawiera brakujących danych do uzupełnienia.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.configure(bg="#fff")
        dialog.title(f"Uzupełnianie braków: {column_name}")
        tk.Label(dialog, text="Wybierz sposób uzupełnienia braków:", bg="#fff").pack(pady=10)
        method_var = tk.StringVar(value="mean" if dtype == "float64" else "value")
        radio_methods = []
        if dtype == "float64":
            radio_methods = [
                ("Uzupełnij średnią", "mean"),
                ("Uzupełnij średnią z grupy", "group_mean"),
                ("Uzupełnij medianą", "median"),
                ("Uzupełnij wartością domyślną", "value"),
                ("Uzupełnij metodą regresji", "regression"),
                ("Uzupełnij metodą MICE", "mice"),
            ]
        elif dtype == "object":
            radio_methods = [
                ("Uzupełnij wartością domyślną", "value"),
                ("Uzupełnij najczęstszą wartością", "mode"),
                ("Uzupełnij najczęstszą wartością z grupy", "group_mode"),
                ("Uzupełnij metodą KNN (kategorie)", "knn_cat"),
                ("Uzupełnij klasyfikatorem (regresja logist.)", "logreg_cat"),
            ]
        for text, value in radio_methods:
            tk.Radiobutton(dialog, text=text, variable=method_var, value=value, bg="#fff", anchor="w").pack(fill="x", padx=10)
        # Dodaj opcję usuwania wierszy z brakami
        tk.Radiobutton(dialog, text="Usuń wiersze z brakami", variable=method_var, value="remove_rows", bg="#fff", anchor="w").pack(fill="x", padx=10)
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Zastosuj", command=lambda: self.apply_fillna(dialog, column_name, method_var.get())).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Anuluj", command=dialog.destroy).pack(side="left", padx=5)

    def apply_fillna(self, dialog, column_name, method):
        dtype = self.df[column_name].dtype
        if method == "mean":
            self.df[column_name] = fillna_mean(self.df[column_name])
            info = f"metodą: {method}."
        elif method == "median":
            self.df[column_name] = fillna_median(self.df[column_name])
            info = f"metodą: {method}."
        elif method == "group_mean":
            self.ask_fillna_group_mean(dialog, column_name)
            return
        elif method == "value":
            self.ask_fillna_value(dialog, column_name)
            return
        elif method == "regression":
            from logic.methods import fillna_regression
            self.df[column_name] = fillna_regression(self.df, column_name)
            info = f"metodą: {method}."
        elif method == "mice":
            from logic.methods import fillna_mice
            self.df[column_name] = fillna_mice(self.df, column_name)
            info = f"metodą: {method}."
        elif method == "unknown" and dtype == "object":
            from logic.methods import fillna_unknown
            self.df[column_name] = fillna_unknown(self.df[column_name])
            info = "wartością: 'Unknown'."
        elif method == "mode" and dtype == "object":
            from logic.methods import fillna_mode
            mode_val = self.df[column_name].mode().iloc[0] if not self.df[column_name].mode().empty else ''
            self.df[column_name] = fillna_mode(self.df[column_name])
            info = f"najczęstszą wartością: '{mode_val}'."
        elif method == "group_mode" and dtype == "object":
            self.ask_fillna_group_mode(dialog, column_name)
            return
        elif method == "knn_cat" and dtype == "object":
            from logic.methods import fillna_knn_categorical
            self.df[column_name] = fillna_knn_categorical(self.df, column_name)
            info = "KNN dla danych kategorycznych."
        elif method == "logreg_cat" and dtype == "object":
            from logic.methods import fillna_logreg_categorical
            self.df[column_name] = fillna_logreg_categorical(self.df, column_name)
            info = "regresją logistyczną/klasyfikatorem."
        elif method == "remove_rows":
            # Usuń wiersze z brakami w wybranej kolumnie
            self.df = remove_rows_with_missing(self.df, columns=[column_name])
            info = "usunięciem wierszy z brakami."
        else:
            messagebox.showinfo("Informacja", f"Wybrano nieobsługiwaną metodę: {method}.")
            dialog.destroy()
            return
        messagebox.showinfo("Informacja", f"Braki w kolumnie '{column_name}' zostały uzupełnione {info}")
        dialog.destroy()
        self.display_column()

    def ask_fillna_value(self, dialog, column_name):
        dialog.withdraw()
        dtype = self.df[column_name].dtype
        if dtype == "object":
            answer = messagebox.askquestion("Wartość domyślna", "Czy uzupełnić wartością domyślną ('Unknown')?")
            if answer == 'yes':
                value = 'Unknown'
            else:
                value = tk.simpledialog.askstring("Wpisz wartość", "Podaj wartość do uzupełnienia:")
                if value is None:
                    dialog.deiconify()
                    return
        else:
            answer = messagebox.askquestion("Wartość domyślna", "Czy uzupełnić wartością domyślną (0)?")
            if answer == 'yes':
                value = 0
            else:
                value = tk.simpledialog.askstring("Wpisz wartość", "Podaj wartość do uzupełnienia:")
                if value is None:
                    dialog.deiconify()
                    return
        from logic.methods import fillna_value
        self.df[column_name] = fillna_value(self.df[column_name], value)
        messagebox.showinfo("Informacja", f"Braki w kolumnie '{column_name}' zostały uzupełnione wartością: {value}.")
        dialog.destroy()
        self.display_column()

    def ask_fillna_group_mean(self, dialog, column_name):
        dialog.withdraw()
        group_cols = [c for c in self.df.columns if c != column_name]
        if not group_cols:
            messagebox.showwarning("Brak kolumn", "Brak kolumn do grupowania.")
            dialog.deiconify()
            return
        group_dialog = tk.Toplevel(self.root)
        group_dialog.title("Wybierz kolumny grupujące")
        group_dialog.configure(bg="#fff")
        tk.Label(group_dialog, text="Wybierz kolumny do grupowania (Ctrl/Shift dla wielu):", bg="#fff").pack(padx=10, pady=6)
        listbox = tk.Listbox(group_dialog, selectmode=tk.MULTIPLE, exportselection=False, height=min(10, len(group_cols)), width=40)
        for col in group_cols:
            listbox.insert(tk.END, col)
        listbox.pack(padx=10, pady=6, fill="both", expand=True)

        def apply_group_mean():
            selections = listbox.curselection()
            if not selections:
                messagebox.showwarning("Brak wyboru", "Wybierz co najmniej jedną kolumnę do grupowania.")
                return
            chosen = [group_cols[i] for i in selections]
            self.df[column_name] = fillna_group_mean(self.df, column_name, chosen)
            msg = "', '".join(chosen)
            messagebox.showinfo("Informacja", f"Braki w kolumnie '{column_name}' zostały uzupełnione średnią w grupach kolumn: '{msg}'.")
            group_dialog.destroy()
            dialog.destroy()
            self.display_column()

        btn_frame = ttk.Frame(group_dialog)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Zastosuj", command=apply_group_mean).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Anuluj", command=lambda: (group_dialog.destroy(), dialog.deiconify())).pack(side="left", padx=5)

    def ask_fillna_group_mode(self, dialog, column_name):
        dialog.withdraw()
        group_cols = [c for c in self.df.columns if c != column_name]
        if not group_cols:
            messagebox.showwarning("Brak kolumn", "Brak kolumn do grupowania.")
            dialog.deiconify()
            return
        group_dialog = tk.Toplevel(self.root)
        group_dialog.title("Wybierz kolumny grupujące")
        group_dialog.configure(bg="#fff")
        tk.Label(group_dialog, text="Wybierz kolumny do grupowania (Ctrl/Shift dla wielu):", bg="#fff").pack(padx=10, pady=6)
        listbox = tk.Listbox(group_dialog, selectmode=tk.MULTIPLE, exportselection=False, height=min(10, len(group_cols)), width=40)
        for col in group_cols:
            listbox.insert(tk.END, col)
        listbox.pack(padx=10, pady=6, fill="both", expand=True)

        def apply_group_mode():
            selections = listbox.curselection()
            if not selections:
                messagebox.showwarning("Brak wyboru", "Wybierz co najmniej jedną kolumnę do grupowania.")
                return
            chosen = [group_cols[i] for i in selections]
            self.df[column_name] = fillna_group_mode(self.df, column_name, chosen)
            msg = "', '".join(chosen)
            messagebox.showinfo("Informacja", f"Braki w kolumnie '{column_name}' zostały uzupełnione najczęstszą wartością w grupach kolumn: '{msg}'.")
            group_dialog.destroy()
            dialog.destroy()
            self.display_column()

        btn_frame = ttk.Frame(group_dialog)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Zastosuj", command=apply_group_mode).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Anuluj", command=lambda: (group_dialog.destroy(), dialog.deiconify())).pack(side="left", padx=5)

    def save_data(self):
        if self.df is None or not hasattr(self, 'loaded_file_path') or not self.loaded_file_path:
            messagebox.showwarning("Brak pliku", "Najpierw wczytaj plik.")
            return
        try:
            if self.loaded_file_path.endswith(".csv"):
                self.df.to_csv(self.loaded_file_path, index=False)
            else:
                self.df.to_excel(self.loaded_file_path, index=False)
            messagebox.showinfo("Sukces", "Dane zostały zapisane do oryginalnego pliku.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać danych:\n{e}")

def main():
    root = tk.Tk()
    app = ExcelViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()