from tracker_core import run_tracker

# Weekdays: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
CONFIG = {
    'START_WEEKDAY': 2,  # Wednesday
    'START_HOUR': 6,
    'START_MINUTE': 0,
    'START_SECOND': 0,

    'QUOTA_CYCLES': 1
}

if __name__ == "__main__":
    run_tracker("Claude", CONFIG)