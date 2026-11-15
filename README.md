# Astronaut Health Monitoring

NASA Space Apps Challenge: Health Monitoring Software.

Aim: A health tracker for astronauts on long missions (Moon / Mars). It logs daily records, checks live vitals and gives instant tips and critical warnings.

## Features
- Mission setup with radiation dose check
- Live checks: heart beat, dizziness, habitat comfort, calories
- Daily record (sleep, mood, workload, exercise) saved to CSV
- Tips based on the last days
- Sound effects and background music

## Libraries
- streamlit
- pandas

## Install

Mac:
```
python3 -m pip install streamlit pandas
```

Windows:
```
python -m pip install streamlit pandas
```

## Run

Mac:
```
python3 -m streamlit run main.py
```

Windows:
```
python -m streamlit run main.py
```

Do not use the VS Code Run button, use the terminal command.

## Live demo
https://astronaut-health-monitoring-8if5x6reubl6drvahzb336.streamlit.app