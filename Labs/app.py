"""Run: python -m streamlit run Labs/app.py"""
import json
import pandas as pd
import streamlit as st
from pipeline import process_csv

st.set_page_config(page_title="Химера: проверка библиотеки",layout="wide")
st.title("Химера: проверка молекулярной библиотеки")
st.write("Загрузите CSV с id и smiles. Исходные записи сохраняются; PAINS — предупреждение для разбора.")
st.caption("Политика: teaching-parent-v1, нейтрализация parent, без канонизации таутомеров. Закупки и активность не определяются.")
upload=st.file_uploader("CSV UTF-8, не более 1 МБ",type=["csv"])
if upload:
    data=upload.getvalue()
    if len(data)>1_000_000:
        st.error("Для учебной версии допустим файл до 1 МБ.")
    else:
        try:
            rows,passport=process_csv(data,max_rows=500)
            if len(rows)>500:
                st.error("Для учебной версии допустимо до 500 структур.")
            else:
                frame=pd.DataFrame(rows)
                st.json(passport)
                if rows:
                    st.dataframe(frame,width="stretch")
                    st.write(frame["status"].value_counts().to_dict())
                    st.download_button("Полный CSV",frame.to_csv(index=False).encode("utf-8-sig"),"chimera.csv")
                st.download_button("Отчёт с паспортом",json.dumps({"passport":passport,"rows":rows},ensure_ascii=False,indent=2),"chimera.json")
        except (ValueError,UnicodeDecodeError) as error:
            st.error(str(error))
