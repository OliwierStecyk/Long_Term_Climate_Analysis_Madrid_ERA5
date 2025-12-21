from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import cfgrib
import seaborn as sns
import time
import os

from DIR.CONSTS import name_clean, name_raw



def get_clean_df(year, step_type):
    """

    Wczytanie danych grib, oraz

    :param year:
    :param step_type:
    :return:
    """

    ds = xr.open_dataset(f'{name_raw}{year}.grib',
                         engine='cfgrib',
                         backend_kwargs={'filter_by_keys': {'stepType': step_type}, 'indexpath': ''})
    df = ds.to_dataframe().reset_index()
    df['valid_time'] = df['time'] + df['step']

    # Lista śmieci do usunięcia
    cols_to_drop = ['time', 'step', 'number', 'surface', 'depthBelowLandLayer']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    df['latitude'] = df['latitude'].round(2)
    df['longitude'] = df['longitude'].round(2)
    return df


def process_one_year( year ):
    """
    Pełny proces ETL dla jednego roku.

    :param year:
    :return:

    """
    try:
        t1 = time.time()
        df_i = get_clean_df(year,'instant')
        df_a = get_clean_df(year,'accum')


        df_i_12h = df_i.groupby(['latitude', 'longitude', pd.Grouper(key='valid_time', freq='12h')]).agg({
            't2m': ['mean', 'max', 'min'],
            'd2m': 'mean',
            'skt': 'mean',
            'sp': 'mean',
            'blh': 'mean',
            'tcc': 'mean',
            'swvl1': 'mean',
            'lai_hv': 'mean',
            'lai_lv': 'mean',
            'u10': 'mean',
            'v10': 'mean'
        }).reset_index()


        df_i_12h.columns = [
            'latitude', 'longitude', 'time',
            't2m_mean', 't2m_max', 't2m_min',
            'd2m_mean', 'skt_mean', 'sp_mean', 'blh_mean',
            'tcc_mean', 'soil_moisture', 'lai_hv', 'lai_lv', 'u10', 'v10'
        ]

        df_a_12h = df_a.groupby(['latitude', 'longitude', pd.Grouper(key='valid_time', freq='12h')]).agg({
            'tp': 'sum',
            'e': 'sum',
            'ssrd': 'sum'
        }).reset_index()
        df_a_12h.columns = ['latitude', 'longitude', 'time', 'tp_sum', 'e_sum', 'ssrd_sum']

        ## Złączenie tabel
        df_final = pd.merge(df_i_12h, df_a_12h, on=['latitude', 'longitude', 'time'], how='inner')

        df_final['datetime'] = df_final['time']

        df_final['date'] = df_final['datetime'].dt.date
        df_final['hour'] = df_final['datetime'].dt.hour
        df_final['year'] = df_final['datetime'].dt.year
        df_final['month'] = df_final['datetime'].dt.month
        df_final['day'] = df_final['datetime'].dt.day
        df_final['dayofyear'] = df_final['datetime'].dt.dayofyear

        # pory roku: 1=zima, 2=wiosna, 3=lato, 4=jesień
        df_final['season'] = (df_final['month'] % 12 // 3 + 1).astype('int8')


        df_final['year'] = df_final['year'].astype('int16')
        df_final['month'] = df_final['month'].astype('int8')
        df_final['day'] = df_final['day'].astype('int8')
        df_final['hour'] = df_final['hour'].astype('int8')
        df_final['dayofyear'] = df_final['dayofyear'].astype('int16')


        df_final = df_final.drop(columns=['time', 'datetime'])



        ## Konwersja jednostek
        for col in ['t2m_mean', 't2m_max', 't2m_min', 'd2m_mean', 'skt_mean']:
            df_final[col] = df_final[col] - 273.15

        df_final['tp_sum'] *= 1000
        df_final['e_sum'] *= 1000

        df_final['lai_total'] = df_final['lai_hv'] + df_final['lai_lv']
        df_final = df_final.drop( columns = ['lai_hv','lai_lv'])

        df_final['ws_mean'] = np.sqrt(df_final['u10']**2 + df_final['v10']**2)
        df_final = df_final.drop( columns=['u10','v10'])



        df_final.to_parquet(f"{name_clean}{year}.parquet", engine='pyarrow', index=False)
        print(f"File processed : {year} in time = {time.time() - t1}")
    except Exception as e:
        print(f"Błąd w roku : {year}: {str(e)}")
        return 0



if __name__ == "__main__":
    time_all = time.time()
    print(1)
    num_workers = max(1, int(os.cpu_count() / 2) - 1)
    print(f"Uruchomienie przetwarzania równolegle na {num_workers } procesach ")

    years = list(range(1994, 2026))

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_one_year, years))

    total_duration = time.time() - time_all

    print(f"\n{'=' * 30}")
    print(f"CAŁKOWITY CZAS: {total_duration / 60:.2f} minut")
    print(f"{'=' * 30}")