# 🌍 Long-Term Climate Analysis: Madrid (ERA5)

Projekt analizuje zmiany klimatyczne w regionie Madrytu na przestrzeni 31 lat (1994–2024). Wykorzystuje zrównoleglony potok przetwarzania danych (ETL) do transformacji surowych plików GRIB z systemu **Copernicus ERA5** na zoptymalizowane pliki analityczne.

## 🚀 Technical Performance & Optimization

Projekt demonstruje podejście **Data Engineering**, mające na celu optymalizację pracy z dużymi zbiorami danych:

*   **Parallel Data Pipeline:** Wykorzystano `concurrent.futures.ProcessPoolExecutor` do obejścia ograniczeń **GIL (Global Interpreter Lock)**. Skrypt automatycznie rozdziela zadania na wiele rdzeni procesora.
    *   **Benchmark:** Na procesorze **i7-13gen (16 wątków)** czas przetwarzania 31 lat spadł z **~120 min do ~ 11.35  min** (przyspieszenie 1.5 x).
*   **Memory Management:** Dane są przetwarzane w "paczkach" rocznych, co pozwala na stabilną pracę przy 32GB RAM bez ryzyka przepełnienia pamięci przy operacjach na `xarray`.
*   **Storage Optimization:** Konwersja z formatu GRIB do **Parquet** (kompresja Snappy). Format kolumnowy pozwala na błyskawiczne wczytywanie wybranych zmiennych podczas fazy EDA.

---

## 🛠️ Setup & Installation

Aby uruchomić projekt lokalnie i odtworzyć środowisko analityczne, wykonaj poniższe kroki:

1. **Sklonuj repozytorium:**
   ```bash
   git clone https://github.com/TwojUser/Long_Term_Climate_Analysis_Madrid_ERA5.git
   cd Long_Term_Climate_Analysis_Madrid_ERA5
   ```

2. **Utwórz i aktywuj środowisko wirtualne:**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # Linux/MacOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Zainstaluj zależności:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

> **⚠️ Ważna uwaga (Windows):** Do poprawnego działania biblioteki `cfgrib` wymagany jest silnik **eccodes**. Jeśli po instalacji wystąpi błąd `ecCodes library not found`, najprostszym rozwiązaniem jest instalacja przez Condę (`conda install -c conda-forge eccodes`) lub pobranie binariów ze strony ECMWF.


---

## 📂 Data Access & Benchmark

Ze względu na duży rozmiar danych klimatycznych, surowe pliki GRIB nie są przechowywane bezpośrednio w repozytorium GitHub. Aby umożliwić pełną replikowalność projektu, udostępniam dane w mojej chmurze.

### 🔗 Linki do pobrania:
- [**Pobierz surowe pliki GRIB (Raw Data)**](LINK_DO_FOLDERU_RAW) – *Wymagane do przetestowania skryptu ETL.*
- [**Pobierz przetworzone pliki Parquet (Clean Data)**](LINK_DO_FOLDERU_CLEAN) – *Zalecane do natychmiastowego rozpoczęcia analizy EDA.*

### 🛠️ Instrukcja przygotowania danych:
Aby skrypty i notebooki działały poprawnie, umieść pobrane pliki w następujących ścieżkach:

1.  **Dane Surowe (GRIB):** Wypakuj pliki `.grib` do folderu:  
    `raw_data/DaneMadryt/`
2.  **Dane Przetworzone (Parquet):** Pliki `.parquet` umieść w folderze:  
    `clean_data/`

---

## ⚡ Performance Challenge (Benchmark)

Głównym osiągnięciem technicznym projektu jest optymalizacja potoku przetwarzania danych. 

*   **Standardowe przetwarzanie (Single-thread):** ok. 120 minuty.
*   **Moja optymalizacja (Multiprocessing):** ok. **11.35 minut**.

**Chcesz sprawdzić to na własnej maszynie?**
1. Pobierz surowe dane do folderu `raw_data/DaneMadryt/`.
2. Aktywuj środowisko wirtualne (`.venv`).
3. Uruchom skrypt: `python src/data_processing.py`.
4. Skrypt automatycznie wykryje Twoje wątki procesora i przeprowadzi równoległą agregację 31 lat danych.

---

# 📊 Kompleksowy Słownik Kolumn (Processed Data)

Każdy wiersz w pliku wynikowym reprezentuje **12-godzinny interwał** (agregacja nocna 00:00 lub dzienna 12:00) dla konkretnej lokalizacji.

### 📍 Lokalizacja i Czas
| Nazwa kolumny | Opis | Jednostka |
| :--- | :--- | :--- |
| `latitude` | Szerokość geograficzna (zaokrąglona do 0.02 dla spójności). | stopnie [°] |
| `longitude` | Długość geograficzna (zaokrąglona do 0.02). | stopnie [°] |
| `date` | Data kalendarzowa pomiaru. | RRRR-MM-DD |
| `hour` | Godzina rozpoczęcia interwału (0 lub 12). | [h] |

### 🌡️ Temperatura i Wilgotność (Konwersja z Kelvinów na °C)
| Nazwa kolumny | Opis | Statystyka interwału |
| :--- | :--- | :--- |
| `t2m_mean` | Średnia temperatura powietrza na 2m. | Średnia (12h) |
| `t2m_max` | Maksymalna odnotowana temperatura powietrza. | Max (12h) |
| `t2m_min` | Minimalna odnotowana temperatura powietrza. | Min (12h) |
| `d2m_mean` | Średnia temperatura punktu rosy (wskaźnik wilgotności). | Średnia (12h) |
| `skt_mean` | Średnia temperatura powierzchni gruntu (Skin Temperature). | Średnia (12h) |

### 💧 Hydrologia i Gleba (Konwersja z metrów na mm)
| Nazwa kolumny | Opis | Interpretacja |
| :--- | :--- | :--- |
| `tp_sum` | Suma całkowitego opadu (deszcz + śnieg). | Suma (12h) |
| `e_sum` | Suma ewaporacji (odparowywania wody). | Wartości ujemne = utrata wody |
| `soil_moisture`| Wilgotność gleby w warstwie powierzchniowej (0-7cm). | $[m^3/m^3]$ |
| `water_balance`| Bilans wodny (`tp_sum` + `e_sum`). | Wynik > 0 to zysk wody |

### 🍃 Roślinność i Energia
| Nazwa kolumny | Opis | Interpretacja |
| :--- | :--- | :--- |
| `lai_total` | Całkowity Leaf Area Index (suma `lai_hv` + `lai_lv`). | Gęstość ulistnienia |
| `tcc_mean` | Średnie zachmurzenie nieba. | 0 (czyste) do 1 (pełne) |
| `ssrd_sum` | Suma promieniowania słonecznego docierającego do powierzchni. | $[J/m^2]$ |

### 🌬️ Atmosfera i Wiatr
| Nazwa kolumny | Opis | Uwagi |
| :--- | :--- | :--- |
| `sp_mean` | Średnie ciśnienie powierzchniowe. | [Pa] |
| `blh_mean` | Średnia wysokość warstwy granicznej atmosfery. | Dynamika pionowa powietrza |

Data source: Copernicus Climate Change Service (C3S), ERA5 reanalysis.
© European Centre for Medium-Range Weather Forecasts (ECMWF).
Data is redistributed under the Copernicus open data policy.
---

## 📈 Plan Analizy (EDA)

Po przetworzeniu danych, projekt przechodzi do fazy **Exploratory Data Analysis**, która obejmuje:

1.  **Analiza Trendów:** Czy średnia temperatura Madrytu w ostatnich 10 latach rośnie szybciej niż w poprzednich dekadach?
2.  **Badanie Ekstremów:** Analiza częstotliwości występowania dni z `t2m_max > 35°C`.
3.  **Bilans Wodny:** Korelacja między ujemnym `water_balance` a spadkiem `lai_total` (reakcja roślin na suszę).
4.  **Multikoliniowość (VIF):** Sprawdzenie współzależności między `skt_mean` a `t2m_mean` w celu poprawnego doboru zmiennych do przyszłych modeli ML.

---

## 📁 Project Structure
```text
├── DIR/
│   └── CONSTS.py          # Ścieżki do plików GRIB i Parquet
├── src/
│   └── data_processing.py # Skrypt ETL (Multiprocessing)
├── notebooks/
│   └── 01_eda.ipynb       # Wizualizacje i statystyki
├── clean_data/
│   └──  era5_data_1994.parquet       # Gotowe pliki .parquet 
├── raw_data     
│   └── DaneMadryt/era5_data_1994,grub    # Surowe pliki .grib 
└── README.md
```

---

📊 Exploratory Data Analysis (EDA)

Po przetworzeniu danych ERA5 do postaci zoptymalizowanych plików Parquet,
projekt przechodzi do fazy eksploracyjnej analizy danych (EDA),
której celem jest ilościowa i wizualna ocena zmian klimatu
w regionie Madrytu w latach 1994–2024.

Analiza EDA została przeprowadzona w notebooku:

notebooks/01_eda.ipynb


### Cele EDA

```markdown
Celem analizy jest odpowiedź na następujące pytania badawcze:

• Czy obserwowany jest długoterminowy trend wzrostowy temperatury powietrza?
• Jak zmienia się częstość występowania ekstremalnych upałów?
• Czy występują zmiany w bilansie wodnym i wilgotności gleby?
• Jak reaguje roślinność (LAI) na warunki suche i gorące?
• Które zmienne są silnie współzależne i mogą powodować multikoliniowość
  w przyszłych modelach predykcyjnych?
```

### Zakres analiz

```markdown
Notebook EDA obejmuje m.in.:

• agregację czasową (roczną i sezonową),
• analizę trendów i anomalii względem okresu referencyjnego,
• analizę ekstremów klimatycznych (np. dni z t2m_max > 35°C),
• analizę korelacji i współzależności między zmiennymi,
• diagnostykę statystyczną (VIF, rozkłady, zmienność),
• krytyczną ocenę jakości i ograniczeń danych ERA5.
```

### Reprodukowalność

```markdown
Notebook 01_eda.ipynb może być uruchomiony bezpośrednio
na podstawie plików Parquet dostępnych w folderze clean_data/,
bez konieczności ponownego przetwarzania danych GRIB.
```

Pełna analiza statystyczna oraz opis metodologii znajdują się w pliku:
[Link do raportu PDF]([AnalizaKlimatu.pdf))

---






