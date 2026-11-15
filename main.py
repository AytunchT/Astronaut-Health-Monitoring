import os
import streamlit as st
import pandas as pd

file = "File.csv"            # daily records (one row per day)
missionFile = "Mission.csv"  # mission info (so F5 doesn't lose it)

radiation = {
    "Moon": 1.3,
    "Mars": 0.67,
}

muscleOptions = ["Biceps", "Triceps", "Back", "Chest", "Legs", "Shoulders"]


# a fresh log for a new day
def emptyLog():
    return {
        "Exercised": False,
        "Muscle Groups": "",
        "Calories Burnt": 0,
        "Calories Consumed": 0,
    }


# adds one row to the end of a csv file (creates the file if it doesn't exist)
def appendRow(path, row):
    new = pd.DataFrame([row])
    if os.path.exists(path):
        new = pd.concat([pd.read_csv(path), new], ignore_index=True)
    new.to_csv(path, index=False)


# one-time message after rerun
if "message" in st.session_state:
    st.success(st.session_state.message)
    del st.session_state.message

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
        st.session_state.message = "Mission saved!"
        st.rerun()

    st.stop()  # nothing below runs until the mission is saved

# ---------- RADIATION ----------
m = st.session_state.mission
dose = radiation[m["Location"]] * m["Days"]
remainingRadiationLimit = m["Radiation Limit"] - dose

if dose > m["Radiation Limit"] * 0.5:
    st.warning("Radiation limit is high")

# ---------- DAY / PHASE ----------
# day number continues from the last day in the file
if "day" not in st.session_state:
    if os.path.exists(file):
        st.session_state.day = int(pd.read_csv(file)["Day"].max()) + 1
    else:
        st.session_state.day = 1

# phase: "live" = live checks, "daily" = end of day form, "saved" = day saved
if "phase" not in st.session_state:
    st.session_state.phase = "live"

# which live check is open (None = all closed)
if "tool" not in st.session_state:
    st.session_state.tool = None

# exercise / calories collected during the day, saved with the daily record
if "log" not in st.session_state:
    st.session_state.log = emptyLog()

st.subheader(f"Day {st.session_state.day}")

# ---------- PHASE 1: LIVE CHECKS ----------
if st.session_state.phase == "live":
    st.write("Pick a check:")

    tools = {
        "heart": "Heart Beat",
        "dizzy": "Dizziness",
        "comfort": "Habitat Comfort",
        "burnt": "Calories Burnt",
        "consumed": "Calories Consumed",
    }

    # one button per check, the open one disappears
    cols = st.columns(len(tools))
    for col, (key, label) in zip(cols, tools.items()):
        if key != st.session_state.tool:
            if col.button(label):
                st.session_state.tool = key  # opens this check, closes the other one
                st.rerun()

    tool = st.session_state.tool

    if tool == "heart":
        heartBeat = st.number_input("What is your Heart Beat?", 30, 200, 70)
        if heartBeat < 40 or heartBeat > 150:
            st.error("CRITICAL: DEADLY HEART BEAT, SEEK HELP IMMEDIATLY")
        else:
            st.success("Heart beat is normal")

    elif tool == "dizzy":
        dizzy = st.checkbox("Feeling dizzy or lightheaded?")  # gravity changes
        if dizzy:
            st.warning("Sit or lie down, rest and drink water")
        else:
            st.success("No problem")

    elif tool == "comfort":
        comfort = st.slider("Habitat comfort (1-10)", 1, 10, 5)  # temperature, noise, light, crowding
        if comfort < 4:
            st.warning("Habitat conditions are poor: check temperature, noise and lighting")
        else:
            st.success("Habitat conditions are fine")

    elif tool == "burnt":
        exercised = st.radio("Did you exercise today?", ["No", "Yes"], horizontal=True)

        # if "No", nothing else happens
        if exercised == "Yes":
            muscles = st.multiselect("Which muscle groups did you work?", muscleOptions)
            burnt = st.number_input("Calories burnt", 0, 5000, 200)

            if st.button("Log exercise"):
                if not muscles:
                    st.warning("Pick at least one muscle group")
                else:
                    st.session_state.log["Exercised"] = True
                    st.session_state.log["Muscle Groups"] = ", ".join(muscles)
                    st.session_state.log["Calories Burnt"] = burnt
                    st.success("Exercise logged! It will be saved when you save the day.")

    elif tool == "consumed":
        consumed = st.number_input("Calories consumed", 0, 10000, 2000)

        if st.button("Log calories consumed"):
            st.session_state.log["Calories Consumed"] = consumed
            st.success("Calories logged! They will be saved when you save the day.")

    st.divider()
    if st.button("End Day"):
        st.session_state.tool = None
        st.session_state.phase = "daily"
        st.rerun()

# ---------- PHASE 2: DAILY RECORD ----------
elif st.session_state.phase == "daily":
    st.write("Fill in your daily record.")

    sleep = st.number_input("How many hours did you sleep", 0, 24, 7)
    talk = st.checkbox("Did you talk to someone today?")  # isolation
    mood = st.slider("Mood (1-10)", 1, 10, 5)
    workload = st.slider("Workload today (1-10)", 1, 10, 5)
    exercise = st.number_input("Exercise today (minutes)", 0, 300, 30)  # bone loss prevention
    bedtime = st.time_input("Bedtime")

    if st.button("Save"):
        appendRow(file, {
            "Day": st.session_state.day,
            "Sleep (hr)": sleep,
            "Talked": talk,
            "Mood": mood,
            "Workload": workload,
            "Exercise (min)": exercise,
            "Bedtime": bedtime.strftime("%H:%M"),
            "Remaining Limit (mSv)": remainingRadiationLimit,
            **st.session_state.log,  # Exercised, Muscle Groups, Calories Burnt, Calories Consumed
        })
        st.session_state.phase = "saved"
        st.rerun()

# ---------- PHASE 3: DAY SAVED ----------
else:
    st.success(f"Day {st.session_state.day} saved!")
    if st.button("Next Day"):
        st.session_state.day += 1
        st.session_state.phase = "live"
        st.session_state.log = emptyLog()  # new day starts fresh
        st.rerun()

# ---------- SAVED FILES ----------
if "fileShow" not in st.session_state:
    st.session_state.fileShow = False

if os.path.exists(file):
    if st.button("Saved Files"):
        st.session_state.fileShow = not st.session_state.fileShow

    if st.session_state.fileShow:
        st.dataframe(pd.read_csv(file))

# ---------- TIPS (based on daily records) ----------
if "tipsShow" not in st.session_state:
    st.session_state.tipsShow = False

if os.path.exists(file):
    if st.button("Tips"):
        st.session_state.tipsShow = not st.session_state.tipsShow

    if st.session_state.tipsShow:
        data = pd.read_csv(file)
        last = data.iloc[-1]    # most recent day
        recent = data.tail(3)   # last 3 days (or fewer if there are fewer days)
        tips = []
        critical = False

        # critical: looks at the last day
        if last["Sleep (hr)"] <= 3:
            st.error("CRITICAL: DEADLY SLEEPING SCHEDULE, SLEEP MORE")
            critical = True
        # trend: looks at the last 3 days
        elif recent["Sleep (hr)"].mean() < 8:
            tips.append("Sleep More")

        if recent["Mood"].mean() < 5:
            tips.append("Try to relax and talk to someone")
        if recent["Exercise (min)"].mean() < 30:
            tips.append("Exercise more: bones lose density without gravity")

        # combined: last day
        if last["Workload"] >= 8 and last["Sleep (hr)"] < 6:
            tips.append("High workload and low sleep together: take a break")

        # isolation: last 3 days
        if len(data) >= 3 and recent["Talked"].sum() == 0:
            tips.append("You haven't talked to anyone for 3 days: contact someone")

        if tips and not critical:
            for tip in tips:
                st.warning(tip)
        elif not critical:
            st.success("Everything looks good!")