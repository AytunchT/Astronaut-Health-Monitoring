import io
import math
import os
import struct
import wave

import streamlit as st
import pandas as pd

st.set_page_config(initial_sidebar_state="collapsed")

file = "File.csv"            # daily records (one row per day)
missionFile = "Mission.csv"  # mission info (so F5 doesn't lose it)

radiation = {
    "Moon": 1.3,
    "Mars": 0.67,
}

# average distance from Earth in km (Mars changes a lot, this is the average)
distance = {
    "Moon": 384_400,
    "Mars": 225_000_000,
}

# "maintain weight" counts as OK if consumed and burnt are this close (kcal)
calorieTolerance = 100


# ---------- SOUND ----------
RATE = 22050  # samples per second


# a single beep: frequency (Hz), length (sec), volume (0-1), "sine" is soft, "square" is harsh
def tone(freq, seconds, volume=0.4, shape="sine"):
    n = int(RATE * seconds)
    samples = []
    for i in range(n):
        value = math.sin(2 * math.pi * freq * i / RATE)
        if shape == "square":
            value = 1 if value >= 0 else -1
        fade = 1 - i / n  # fades out so there is no "pop" at the end
        samples.append(volume * fade * value)
    return samples


def silence(seconds):
    return [0] * int(RATE * seconds)


# turns a list of numbers into a wav file (bytes) that st.audio can play
def toWav(samples):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        data = b"".join(
            struct.pack("<h", int(max(-1, min(1, s)) * 32767)) for s in samples
        )
        w.writeframes(data)
    return buffer.getvalue()


# the sound effects. cache_data = built once, not on every run
@st.cache_data
def makeSound(name, variant):
    if name == "click":
        s = tone(800, 0.06, 0.3)
    elif name == "save":
        s = tone(523, 0.12) + tone(659, 0.12) + tone(784, 0.25)
    elif name == "warning":
        s = tone(440, 0.15) + silence(0.08) + tone(440, 0.15)
    else:  # critical: alarm
        s = (tone(900, 0.2, 0.5, "square") + tone(600, 0.2, 0.5, "square")) * 3
    # variant makes the file a tiny bit different, so the browser plays
    # the same sound again when it comes twice in a row
    return toWav(s + silence(0.001 * variant))


# background music: a soft looping chord (8 sec, loops without a gap)
@st.cache_data
def makeMusic(variant):
    samples = []
    for i in range(RATE * 8):
        t = i / RATE
        chord = sum(math.sin(2 * math.pi * f * t) for f in (110, 165, 220, 330)) / 4
        chord *= 0.6 + 0.4 * math.sin(2 * math.pi * 0.25 * t)  # slow volume wave
        samples.append((0.25 - 0.001 * variant) * chord)  # variant: tiny change, different file
    return toWav(samples)


# if two sounds are queued in the same run, the more important one plays
priority = {"click": 1, "save": 2, "warning": 3, "critical": 4}


def queueSound(name):
    if name == "warning":  # normal warnings are silent
        return
    current = st.session_state.get("sound")
    if current is None or priority[name] >= priority[current]:
        st.session_state.sound = name


# plays the queued sound (if any), then clears it
def playQueuedSound():
    if "sound" in st.session_state:
        name = st.session_state.sound
        del st.session_state.sound
        st.session_state.soundCount = st.session_state.get("soundCount", 0) + 1
        st.audio(
            makeSound(name, st.session_state.soundCount % 2),
            format="audio/wav",
            autoplay=True,
        )


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

# sound switch and background music live in the sidebar
# counts the runs: the first run is the page load, the next ones come from clicks
st.session_state.runs = st.session_state.get("runs", 0) + 1

musicOn = st.sidebar.toggle("Background music", value=True)
if musicOn:
    st.sidebar.audio(
        makeMusic(0 if st.session_state.runs == 1 else 1),
        format="audio/wav",
        loop=True,
        autoplay=True,
    )

# hides the sound effect players, only the sidebar one stays visible
st.markdown(
    """
    <style>
    audio { display: none; }
    [data-testid="stSidebar"] audio { display: block; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        queueSound("critical")
    elif isRisky:
        st.warning("Radiation limit is high, are you certain you want to participate in this mission?")
        queueSound("warning")

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
        queueSound("save")
        st.rerun()

    playQueuedSound()
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

# ---------- MISSION INFO (click the title to open/close) ----------
with st.expander("Mission info"):
    remaining = max(m["Days"] - st.session_state.day, 0)  # mission days - current day
    c1, c2, c3 = st.columns(3)
    c1.metric("Mission", m["Location"])
    c2.metric("Remaining time", f"{remaining} days")
    c3.metric("Distance from Earth", f"{distance[m['Location']]:,} km")

st.subheader(f"Day {st.session_state.day}")

# ---------- PHASE 1: LIVE CHECKS (not saved, only instant tips) ----------
if st.session_state.phase == "live":
    st.write("Pick a check:")

    tools = {
        "heart": "Heart Beat",
        "dizzy": "Dizziness",
        "comfort": "Habitat Comfort",
        "calories": "Calories",
    }

    # one button per check, the open one disappears
    cols = st.columns(len(tools))
    for col, (key, label) in zip(cols, tools.items()):
        if key != st.session_state.tool:
            if col.button(label):
                st.session_state.tool = key  # opens this check, closes the other one
                queueSound("click")
                st.rerun()

    tool = st.session_state.tool

    if tool == "heart":
        heartBeat = st.number_input("What is your Heart Beat?", 30, 200, 70)
        if heartBeat < 40 or heartBeat > 150:
            st.error("CRITICAL: DEADLY HEART BEAT, SEEK HELP IMMEDIATLY")
            queueSound("critical")
        else:
            st.success("Heart beat is normal")

    elif tool == "dizzy":
        dizzy = st.checkbox("Feeling dizzy or lightheaded?")  # gravity changes
        if dizzy:
            st.warning("Sit or lie down, rest and drink water")
            queueSound("warning")
        else:
            st.success("No problem")

    elif tool == "comfort":
        comfort = st.slider("Habitat comfort (1-10)", 1, 10, 5)  # temperature, noise, light, crowding
        if comfort < 4:
            st.warning("Habitat conditions are poor: check temperature, noise and lighting")
            queueSound("warning")
        else:
            st.success("Habitat conditions are fine")

    elif tool == "calories":
        goal = st.radio(
            "What is your goal?",
            ["Gain weight", "Lose weight", "Maintain weight"],
            horizontal=True,
        )
        consumed = st.number_input("Calories consumed", 0, 10000, 2000)
        burnt = st.number_input("Calories burnt", 0, 10000, 2000)
        diff = consumed - burnt  # positive = ate more than burnt

        st.write(f"Difference: {diff:+} kcal")

        # instant tips, nothing is saved
        if goal == "Gain weight":  # bulk: consumed > burnt
            if consumed > burnt:
                st.success("Good, you are in a calorie surplus")
            else:
                st.warning("Eat more or exercise less")
                queueSound("warning")

        elif goal == "Lose weight":  # deficit: consumed < burnt
            if consumed < burnt:
                st.success("Good, you are in a calorie deficit")
            else:
                st.warning("Eat less or exercise more")
                queueSound("warning")

        else:  # maintain: consumed is about equal to burnt
            if abs(diff) <= calorieTolerance:
                st.success("Good, your calories are balanced")
            elif diff > 0:
                st.warning("You ate more than you burnt: eat less or exercise more")
                queueSound("warning")
            else:
                st.warning("You burnt more than you ate: eat more or exercise less")
                queueSound("warning")

    st.divider()
    if st.button("End Day"):
        st.session_state.tool = None
        st.session_state.phase = "daily"
        queueSound("click")
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
        })
        st.session_state.phase = "saved"
        queueSound("save")
        st.rerun()

# ---------- PHASE 3: DAY SAVED ----------
else:
    st.success(f"Day {st.session_state.day} saved!")
    if st.button("Next Day"):
        st.session_state.day += 1
        st.session_state.phase = "live"
        queueSound("click")
        st.rerun()

# ---------- SAVED FILES ----------
if "fileShow" not in st.session_state:
    st.session_state.fileShow = False

if os.path.exists(file):
    if st.button("Saved Files"):
        st.session_state.fileShow = not st.session_state.fileShow
        queueSound("click")

    if st.session_state.fileShow:
        st.dataframe(pd.read_csv(file))

# ---------- TIPS (based on daily records) ----------
if "tipsShow" not in st.session_state:
    st.session_state.tipsShow = False

if os.path.exists(file):
    tipsClicked = st.button("Tips")  # True only in the run where it was just clicked
    if tipsClicked:
        st.session_state.tipsShow = not st.session_state.tipsShow
        queueSound("click")

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

        # sound only when Tips was just opened, so it doesn't repeat on every click
        if tipsClicked:
            if critical:
                queueSound("critical")
            elif tips:
                queueSound("warning")

# plays the sound that was queued during this run (keep this at the very end)
playQueuedSound()