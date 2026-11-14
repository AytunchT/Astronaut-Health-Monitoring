import os
import streamlit as st
import pandas as pd
from datetime import datetime
 
file = "File.csv" # creates file.csv

if "missionMessage" in st.session_state:
    st.success(st.session_state.missionMessage)
    del st.session_state.missionMessage

if "saveMessage" in st.session_state:
    st.success(st.session_state.saveMessage)
    del st.session_state.saveMessage

st.title("Astronaut Health Monitor")

if "missionShow" not in st.session_state:
    st.session_state.missionShow = True

#gets mission location and mission days and saves it in a dictionary, when saved or created a file, won't show again
if not os.path.exists(file) and st.session_state.missionShow: 
    missionLocation = st.selectbox(
        "Where is the mission?",
        options=("Moon", "Mars")
    )
    missionDays = st.number_input("Mission length (days)", 1, 1000, 30)
    radiationLimit = st.number_input("Radiation Limit (mSv)", 0, 600, 600)
    st.session_state.mission = { #use this to create dictionary to save it in every run.
        "Location": missionLocation, 
        "Days": missionDays,
        "Radiation Limit": radiationLimit
        }

#radiation dictionary
radiation = { 
    "Moon": 1.3,
    "Mars": 0.67,
}

careerLimit = 600

#dose calculator
if "mission" in st.session_state:
    m = st.session_state.mission
    dose = radiation[m["Location"]] * m["Days"]

    if dose > m["Radiation Limit"]: # dose > 600
        st.error("CRITICAL: RADIATION LIMIT REACHED, YOU CAN'T PARTICIPATE IN THIS MISSION")
    elif dose > m["Radiation Limit"] * 0.5: # dose > 300
        st.warning("Radiation limit is high, are you certain you want to participate in this mission?")

    remainingRadiationLimit = m["Radiation Limit"] - dose

if "mainShow" not in st.session_state:
    st.session_state.mainShow = False

if st.session_state.missionShow:
    if st.button("Save Mission"):
        st.session_state.missionShow = False
        st.session_state.mainShow = True
        st.session_state.missionMessage = "Mission saved!"
        st.rerun()



if os.path.exists(file) or st.session_state.mainShow:
    sleep = st.number_input("How many hours did you sleep", 0, 24, 7)
    heartBeat = st.number_input("What is your Heart Beat?", 30, 200, 70)
    mood = st.slider("Mood (1-10)", 1, 10, 5)


if st.button("Save"):
    st.session_state.missionShow = False
    # Creates new dictionary table in panda
    new = pd.DataFrame ([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Sleep (hr)": sleep,
        "Heart Beat (BPM)": heartBeat,
        "Mood": mood,
        "Remaining Limit (mSv)": remainingRadiationLimit
    }])


    if os.path.exists(file): #cheks is there a csv file
        old = pd.read_csv(file) #reads old csv file
        table = pd.concat([old, new], ignore_index = True) #merge the new file and old file 
        #igone_index=True deletes the old indexes and creates new indexes.
    else:
        table = new # if there is no old file, creates a new one

    table.to_csv(file, index=False) #writes table file in csv
    #index=False stops to create index in csv file.
    st.session_state.saveMessage = "Saved!"
    st.rerun()

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
        if data["Sleep (hr)"].mean() < 8: #.mean() calculates average // if sleep in file's average is below 8, add "Sleep More"
            tips.append("Sleep More")
        if data["Mood"].mean() < 5:
            tips.append("Try to relax and talk to someone")
        
        #For deadly situations
        if last["Heart Beat (BPM)"] < 40 or last["Heart Beat (BPM)"] > 150:
            st.error("CRITICAL: DEADLY HEART BEAT, SEEK HELP IMMEDIATLY")
        if data["Sleep (hr)"].mean() <= 3:
            st.error("CRITICAL: DEADLY SLEEPING SCHEDULE, SLEEP MORE")
            critical = True
        
        if tips and not critical: #if tips is not empty and critical = 
            for tip in tips:
                st.warning(tip)
        elif not critical:
            st.success("Everything looks good!")