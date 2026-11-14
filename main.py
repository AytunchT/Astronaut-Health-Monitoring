import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Astronaut Health Monitor")

uyku = st.number_input("How many hours did you sleep", 0, 24, 7)
nabiz = st.number_input("What is your pulse?", 30, 200, 70)
ruh_hali = st.slider("Spiritual mood (1-10)", 1, 10, 5)

if st.button("Save"):
    st.write(f"Saved as: {uyku} hours of sleep, {nabiz} pulse, {ruh_hali} mood")