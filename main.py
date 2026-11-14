import os
import streamlit as st
import pandas as pd
from datetime import datetime
 
file = "File.csv" # creates file.csv

st.title("Astronaut Health Monitor")

sleep = st.number_input("How many hours did you sleep", 0, 24, 7)
heartBeat = st.number_input("What is your pulse?", 30, 200, 70)
mood = st.slider("Spiritual mood (1-10)", 1, 10, 5)

if st.button("Save"):
    st.write(f"Saved as: {sleep} hours of sleep, {heartBeat} pulse, {mood} mood")
    # Creates new dictionary table in panda
    new = pd.DataFrame ([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Sleep": sleep,
        "Hearth Beat": heartBeat,
        "Mood": mood
    }])


    if os.path.exists(file): #cheks is there a csv file
        old = pd.read_csv(file) #reads old csv file
        table = pd.concat([old, new], ignore_index = True) #merge the new file and old file 
        #igone_index=True deletes the old indexes and creates new indexes.
    else:
        table = new # if there is no old file, creates a new one

    table.to_csv(file, index=False) #writes table file in csv
    #index=False stops to create index in csv file.
    st.success("Saved")

if "show" not in st.session_state:
    st.session_state.show = False #table is closed

if os.path.exists(file):
    #if button is clicked, show the table
    if st.button("Saved Files"):
        st.session_state.show = not st.session_state.show #open the table

    #if the table is opened, read the csv file
    if st.session_state.show:
        st.dataframe(pd.read_csv(file)) #dataframe reads file and shows the table in the screen