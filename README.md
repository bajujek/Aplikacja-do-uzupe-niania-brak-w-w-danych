# Uzupełnianie braków w danych (Missing Data Imputation App)

Aplikacja desktopowa w Pythonie (Tkinter) do wczytywania danych z CSV/XLSX, analizy braków oraz imputacji brakujących wartości wybranymi metodami.

## Funkcje
- Wczytywanie plików CSV (auto-detekcja separatora) oraz Excel (XLSX/XLS)  
- Profilowanie kolumn: typ, liczba rekordów, liczba i % braków  
- Wizualizacje:
  - mapa ciepła braków danych
  - histogram / liczności wartości
- Imputacja braków (w zależności od typu danych):
  - średnia, mediana, wartość stała
  - średnia / moda w grupach
  - regresja liniowa (dla numerycznych)
  - MICE (IterativeImputer)
  - KNN dla danych kategorycznych
  - regresja logistyczna/klasyfikator dla danych kategorycznych
  - usuwanie wierszy z brakami w wybranej kolumnie
- Zapis: “Zapisz jako…”, nadpisanie pliku, oraz podział danych na train/val/test.

## Wymagania
- Python 3.10+ (zalecane)
- Biblioteki: pandas, numpy, matplotlib, seaborn, scikit-learn

## Instalacja
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt