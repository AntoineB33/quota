from tracker_core import run_tracker

# Weekdays: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
CONFIG = {
    'START_WEEKDAY': 1,
    'START_HOUR': 10,
    'START_MINUTE': 7,
    'START_SECOND': 0,
    
    'END_WEEKDAY': 1,
    'END_HOUR': 10,
    'END_MINUTE': 7,
    'END_SECOND': 0,
}

if __name__ == "__main__":
    run_tracker("Gemini", CONFIG)