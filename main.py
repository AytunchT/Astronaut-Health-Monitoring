import os
import streamlit as st
import pandas as pd
from datetime import datetime
 
file = "File.csv" # creates file.csv

st.title("Astronaut Health Monitor")

sleep = st.number_input("How many hours did you sleep", 0, 24, 7)
heartBeat = st.number_input("What is your Heart Beat?", 30, 200, 70)
mood = st.slider("Mood (1-10)", 1, 10, 5)

if st.button("Save"):
    st.write(f"Saved as: {sleep} hours of sleep, {heartBeat} pulse, {mood} mood")
    # Creates new dictionary table in panda
    new = pd.DataFrame ([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Sleep": sleep,
        "Heart Beat": heartBeat,
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

if "fileShow" not in st.session_state:
    st.session_state.fileShow = False #table is closed

if os.path.exists(file):
    #if button is clicked, show the table
    if st.button("Saved Files"):
        st.session_state.fileShow = not st.session_state.fileShow #open the table

    #if the table is opened, read the csv file
    if st.session_state.fileShow:
        st.dataframe(pd.read_csv(file)) #dataframe reads file and shows the table in the screen



if "tipsShow" not in st.session_state:
    st.session_state.tipsShow = False

if os.path.exists(file):
    data = pd.read_csv(file)
    
    if st.button("Tips"):
        st.session_state.tipsShow = not st.session_state.tipsShow

    if st.session_state.tipsShow:
        last = data.iloc[-1] #gets the last input.
        tips = []
        critical = False

        #For normal situations
        if data["Sleep"].mean() < 8: #.mean() calculates average // if sleep in file's average is below 8, add "Sleep More"
            tips.append("Sleep More")
        if data["Mood"].mean() < 5:
            tips.append("Try to relax and talk to someone")
        
        #For deadly situations
        if last["Heart Beat"] < 40 or last["Heart Beat"] > 150:
            st.error("CRITICAL: DEADLY HEART BEAT, SEEK HELP IMMEDIATLY")
        if data["Sleep"].mean() <= 3:
            st.error("CRITICAL: DEADLY SLEEPING SCHEDULE, SLEEP MORE")
            critical = True
        
        if tips and not critical: #if tips is not empty and critical = 
            for tip in tips:
                st.warning(tip)
        elif not critical:
            st.success("Everything looks good!")