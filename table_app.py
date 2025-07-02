import pandas as pd
import numpy as np
import streamlit as st
import io

input_file = r"Основная таблица.csv"
table = pd.read_csv(input_file)
table = table.drop(columns=['Unnamed: 0'])

st.title("Фильтр по МНН и классификациям")
buffer = io.BytesIO()

# фильтр
mnn_selection = st.multiselect("Выберите МНН", sorted(table['Molecule'].unique()))
class1_selection = st.multiselect("Выберите New Form Classification Lev 1", sorted(table['New Form Classification Lev 1'].unique()))
class2_selection = st.multiselect("Выберите New Form Classification Lev 2", sorted(table['New Form Classification Lev 2'].unique()))
class3_selection = st.multiselect("Выберите New Form Classification Lev 3", sorted(table['New Form Classification Lev 3'].unique()))
ephmra1_selection = st.multiselect("Выберите EphMRA1", sorted(table['EphMRA1'].unique()))
ephmra2_selection = st.multiselect("Выберите EphMRA2", sorted(table['EphMRA2'].unique()))
ephmra3_selection = st.multiselect("Выберите EphMRA3", sorted(table['EphMRA3'].unique()))
atc1_selection = st.multiselect("Выберите ATC1", sorted(table['ATC1'].dropna().astype(str).unique()))
atc2_selection = st.multiselect("Выберите ATC2", sorted(table['ATC2'].dropna().astype(str).unique()))
atc3_selection = st.multiselect("Выберите ATC3", sorted(table['ATC3'].dropna().astype(str).unique()))

# собираем таблицу и выводим
if mnn_selection:
    st.subheader("Результат по выбранным МНН")
    table["CAGR 5Y, руб"] = table["CAGR 5Y, руб"].astype(float).map('{:.1%}'.format)
    table["CAGR 5Y, уп"] = table["CAGR 5Y, уп"].astype(float).map('{:.1%}'.format)
    st.dataframe(table[table['Molecule'].isin(mnn_selection)].reset_index(drop=True))

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        table[table['Molecule'].isin(mnn_selection)].reset_index(drop=True).to_excel(writer, sheet_name='Sheet1', index=False)
        writer.close()

        download = st.download_button(
            label="Download as Excel",
            data=buffer,
            file_name='Сводная таблица.xlsx',
            #mime='application/vnd.ms-excel'
        )
    #sdfsdf
elif class1_selection or class2_selection or class3_selection or ephmra1_selection or ephmra2_selection or ephmra3_selection:
    df = table.copy()
    if class1_selection:
        df = df[df['New Form Classification Lev 1'].isin(class1_selection)]
    if class2_selection:
        df = df[df['New Form Classification Lev 2'].isin(class2_selection)]
    if class3_selection:
        df = df[df['New Form Classification Lev 3'].isin(class3_selection)]
    if ephmra1_selection:
        df = df[df['EphMRA1'].isin(ephmra1_selection)]
    if ephmra2_selection:
        df = df[df['EphMRA2'].isin(ephmra2_selection)]
    if ephmra3_selection:
        df = df[df['EphMRA3'].isin(ephmra3_selection)]
    if atc1_selection:
        df = df[df['ATC1'].isin(atc1_selection)]
    if atc2_selection:
        df = df[df['ATC2'].isin(atc2_selection)]
    if atc3_selection:
        df = df[df['ATC3'].isin(atc3_selection)]
    
    group_cols = []
    if class1_selection:
        group_cols.append('New Form Classification Lev 1')
    if class2_selection:
        group_cols.append('New Form Classification Lev 2')
    if class3_selection:
        group_cols.append('New Form Classification Lev 3')
    if ephmra1_selection:
        group_cols.append('EphMRA1')
    if ephmra2_selection:
        group_cols.append('EphMRA2')    
    if ephmra3_selection:
        group_cols.append('EphMRA3')
    if atc1_selection:
        group_cols.append('ATC1')
    if atc2_selection:
        group_cols.append('ATC2')
    if atc3_selection:
        group_cols.append('ATC3')

    
    agg_df = df.groupby(group_cols)[[
        'Кол-во игроков (МНН+NFC)',
        'Сумма 23, М Руб',
        'Сумма 24, М Руб'
    ]].sum().reset_index()
    agg_df['Прирост 24, М руб'] = agg_df['Сумма 24, М Руб'] - agg_df['Сумма 23, М Руб']

    
    # Группируем кагр по руб
    base = df.groupby(group_cols)["Сумма 19, М Руб"].sum().reset_index(name="base_19")
    future = df.groupby(group_cols)["Сумма 24, М Руб"].sum().reset_index(name="future_24")
    cagr_df = pd.merge(base, future, on=group_cols, how="outer")

    # считаем CAGR по руб
    agg_df["CAGR 5Y, руб"] = np.where(
        (cagr_df["base_19"] > 0) & (cagr_df["future_24"] >= 0),
        round((cagr_df["future_24"] / cagr_df["base_19"]) ** (1/4) - 1, 2),
        np.nan
    )
    
    agg_sum_23up = df.groupby(group_cols)['Сумма 23, тыс уп'].sum().reset_index()
    agg_df = pd.merge(agg_df, agg_sum_23up, on=group_cols, how='left') 
    
    agg_sum_24up = df.groupby(group_cols)['Сумма 24, тыс уп'].sum().reset_index()
    agg_df = pd.merge(agg_df, agg_sum_24up, on=group_cols, how='left')
    
    agg_df['Прирост 24, тыс уп'] = agg_df['Сумма 24, тыс уп'] - agg_df['Сумма 23, тыс уп']

    # Группируем кагр по уп
    baseu = df.groupby(group_cols)["Сумма 19, тыс уп"].sum().reset_index(name="base_19")
    futureu = df.groupby(group_cols)["Сумма 24, тыс уп"].sum().reset_index(name="future_24")
    cagru_df = pd.merge(baseu, futureu, on=group_cols, how="outer")

    #считаем CAGR по уп
    agg_df["CAGR 5Y, уп"] = np.where(
        (cagru_df["base_19"] > 0) & (cagru_df["future_24"] >= 0), 
        round((cagru_df["future_24"] / cagru_df["base_19"]) ** (1/4) - 1, 2),
        np.nan
    )

    agg_df["CAGR 5Y, руб"] = agg_df["CAGR 5Y, руб"].astype(float).map('{:.1%}'.format)
    agg_df["CAGR 5Y, уп"] = agg_df["CAGR 5Y, уп"].astype(float).map('{:.1%}'.format)
    
    st.subheader("Сводная таблица")
    st.dataframe(agg_df)
 
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        agg_df.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.close()

        download = st.download_button(
            label="Download as Excel",
            data=buffer,
            file_name='Сводная таблица.xlsx',
            #mime='application/vnd.ms-excel'
        )
    
else:
    st.warning("Выбери МНН или классификацию")
