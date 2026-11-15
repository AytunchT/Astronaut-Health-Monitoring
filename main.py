import os
import streamlit as st
import pandas as pd

file = "File.csv"            # daily records
missionFile = "Mission.csv"  # mission info (so F5 doesn't lose it)

radiation = {
    "Moon": 1.3,
    "Mars": 0.67,
}

# one-time message after rerun
if "missionMessage" in st.session_state:
    st.success(st.session_state.missionMessage)
    del st.session_state.missionMessage

st.title("Astronaut Health Monitor")

# load mission from file if it exists
if "mission" not in st.session_state and os.path.exists(missionFile):
    st.session_state.mission = pd.read_csv(missionFile).iloc[0].to_dict()

# ---------- MISSION SETUP ----------
if "mission" not in st.session_state:
    missionLocation = st.selectbox("Where is the mission?", options=("Moon", "Mars"))
    missionDays = st.number_input("Mission length (days)", 1, 1000, 30)
    radiationLimit = st.number_input("Radiation Limit (mSv)", 0, 600, 600)

    # calculate the dose live, before the button
    previewDose = radiation[missionLocation] * missionDays
    isCritical = previewDose > radiationLimit
    isRisky = previewDose > radiationLimit * 0.5 and not isCritical

    # warnings appear right under the radiation limit input
    if isCritical:
        st.error("CRITICAL: RADIATION LIMIT REACHED, YOU CAN'T PARTICIPATE IN THIS MISSION")
    elif isRisky:
        st.warning("Radiation limit is high, are you certain you want to participate in this mission?")

    # disabled=True makes the button unclickable when critical
    if st.button("Save Mission", disabled=isCritical):
        mission = {
            "Location": missionLocation,
            "Days": missionDays,
            "Radiation Limit": radiationLimit,
        }
        pd.DataFrame([mission]).to_csv(missionFile, index=False)
        st.session_state.mission = mission
        st.session_state.missionMessage = "Mission saved!"
        st.rerun()

    st.stop()  # stops here, nothing below runs until the mission is saved

# ---------- RADIATION ----------
m = st.session_state.mission
dose = radiation[m["Location"]] * m["Days"]
remainingRadiationLimit = m["Radiation Limit"] - dose

# risky missions can still be saved, so keep reminding after setup
if dose > m["Radiation Limit"] * 0.5:
    st.warning("Radiation limit is high")

# ---------- DAILY INPUT ----------
# day number continues from the last day in the file
if "day" not in st.session_state:
    if os.path.exists(file):
        st.session_state.day = int(pd.read_csv(file)["Day"].max()) + 1
    else:
        st.session_state.day = 1

if "saved" not in st.session_state:
    st.session_state.saved = False  # False = today's inputs are open

st.subheader(f"Day {st.session_state.day}")

if not st.session_state.saved:
    sleep = st.number_input("How many hours did you sleep", 0, 24, 7)
    mood = st.slider("Mood (1-10)", 1, 10, 5)
    workload = st.slider("Workload today (1-10)", 1, 10, 5)
    bedtime = st.time_input("Bedtime")
    talk = st.checkbox("Did you talk to someone today?")

    if st.button("Save"):
        new = pd.DataFrame([{
            "Day": st.session_state.day,
            "Sleep (hr)": sleep,
            "Talked": talk,
            "Mood": mood,
            "Workload": workload,
            "Bedtime": bedtime.strftime("%H:%M"),
            "Remaining Limit (mSv)": remainingRadiationLimit,
        }])

        if os.path.exists(file):
            table = pd.concat([pd.read_csv(file), new], ignore_index=True)
        else:
            table = new

        table.to_csv(file, index=False)
        st.session_state.saved = True
        st.rerun()
else:
    st.success(f"Day {st.session_state.day} saved!")
    if st.button("Next Day"):
        st.session_state.day += 1
        st.session_state.saved = False
        st.rerun()

# ---------- SAVED FILES ----------
if "fileShow" not in st.session_state:
    st.session_state.fileShow = False

if os.path.exists(file):
    if st.button("Saved Files"):
        st.session_state.fileShow = not st.session_state.fileShow

    if st.session_state.fileShow:
        st.dataframe(pd.read_csv(file))

# ---------- TIPS ----------
if "tipsShow" not in st.session_state:
    st.session_state.tipsShow = False

if os.path.exists(file):
    data = pd.read_csv(file)

    if st.button("Tips"):
        st.session_state.tipsShow = not st.session_state.tipsShow

    if st.session_state.tipsShow:
        tips = []
        critical = False

        if data["Sleep (hr)"].mean() < 8:
            tips.append("Sleep More")
        if data["Mood"].mean() < 5:
            tips.append("Try to relax and talk to someone")

        if data["Sleep (hr)"].mean() <= 3:
            st.error("CRITICAL: DEADLY SLEEPING SCHEDULE, SLEEP MORE")
            critical = True

        if tips and not critical:
            for tip in tips:
                st.warning(tip)
        elif not critical:
            st.success("Everything looks good!")