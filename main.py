import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Astronot Sağlık Takibi")

uyku = st.number_input("Kaç saat uyudun?", 0, 24, 7)
nabiz = st.number_input("Nabzın kaç?", 30, 200, 70)
ruh_hali = st.slider("Ruh halin (1-10)", 1, 10, 5)

if st.button("Kaydet"):
    st.write(f"Kaydedildi: {uyku} saat uyku, {nabiz} nabız, {ruh_hali} ruh hali")