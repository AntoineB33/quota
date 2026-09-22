import datetime

# ==========================================
# DEFAULT CONFIGURATION
# ==========================================
DEFAULT_CONFIG = {
    'START_WEEKDAY': 0,  # 0 = Monday
    'START_HOUR': 0,
    'START_MINUTE': 0,
    'START_SECOND': 0,
    
    'END_WEEKDAY': 6,    # 6 = Sunday
    'END_HOUR': 23,
    'END_MINUTE': 59,
    'END_SECOND': 59,

    # Sleep schedule defaults
    'SLEEP_START': '22:15',
    'SLEEP_END': '08:20'
}

def calculate_period_progression(
    start_weekday, start_hour, start_minute=0, start_second=0,
    end_weekday=None, end_hour=None, end_minute=0, end_second=0,
    reference_time=None
):
    """
    Calculates the time progression percentage between a specific start 
    and end time within a weekly cycle.
    """
    now = reference_time if reference_time else datetime.datetime.now().astimezone()

    # 1. Find the most recent start time
    current_day_start = now.replace(
        hour=start_hour,
        minute=start_minute,
        second=start_second,
        microsecond=0
    )
    days_since_start = (now.weekday() - start_weekday) % 7
    start_time = current_day_start - datetime.timedelta(days=days_since_start)

    if now < start_time and days_since_start == 0:
        start_time -= datetime.timedelta(days=7)

    # 2. Find the corresponding end time
    if end_hour is None or end_weekday is None:
        raise ValueError("end_weekday and end_hour must be provided")

    end_time = start_time.replace(
        hour=end_hour,
        minute=end_minute,
        second=end_second,
        microsecond=0
    )
    
    days_to_end = (end_weekday - start_weekday) % 7
    end_time += datetime.timedelta(days=days_to_end)

    if end_time <= start_time:
        end_time += datetime.timedelta(days=7)

    # 3. Calculate elapsed time and total duration
    total_duration = (end_time - start_time).total_seconds()
    elapsed_time = (now - start_time).total_seconds()

    # 4. Calculate percentage and check if we are outside the active period
    if elapsed_time >= total_duration:
        percentage = 100.0
        is_active = False
    else:
        percentage = (elapsed_time / total_duration) * 100
        is_active = True

    return percentage, start_time, end_time, is_active


def run_tracker(name, custom_config=None):
    """
    Runs the interactive CLI loop for the given AI tracker config.
    """
    # Merge custom configuration over the defaults
    config = DEFAULT_CONFIG.copy()
    if custom_config:
        config.update(custom_config)

    times_to_evaluate = None

    while True:
        if times_to_evaluate is None:
            now = datetime.datetime.now().astimezone()
            tomorrow = now + datetime.timedelta(days=1)
            tomorrow_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            current_batch = [now, tomorrow_10am]
        else:
            current_batch = times_to_evaluate

        for eval_time in current_batch:
            progression_pct, start, end, is_active = calculate_period_progression(
                config['START_WEEKDAY'], config['START_HOUR'], config['START_MINUTE'], config['START_SECOND'],
                config['END_WEEKDAY'], config['END_HOUR'], config['END_MINUTE'], config['END_SECOND'],
                eval_time
            )
            
            label = "Current Time" if eval_time == current_batch[0] and times_to_evaluate is None else "Evaluated Time"
            status = "ACTIVE" if is_active else "COMPLETED/WAITING"

            print(f"\n{name} Tracker")
            print("=" * 55)
            print(f"Cycle Start : {start.strftime('%A, %Y-%m-%d %H:%M:%S')}")
            print(f"Cycle End   : {end.strftime('%A, %Y-%m-%d %H:%M:%S')}")
            print(f"Sleep Time  : {config['SLEEP_START']} to {config['SLEEP_END']}")
            print(f"{label.ljust(12)}: {eval_time.strftime('%A, %Y-%m-%d %H:%M:%S')}")
            print("-" * 55)
            print(f"Progression : {progression_pct:.4f}% ({status})")
            print("=" * 55)

        print("\nOptions:")
        print("  - Press [Enter] for a normal run (current time & 10h tomorrow)")
        print("  - Enter a specific time (YYYY-MM-DD HH:MM:SS)")
        print("  - Enter 'q' to quit")
        user_input = input(">> ").strip()
        
        if user_input.lower() in ['q', 'quit', 'exit']:
            print("Exiting...")
            break
        elif user_input == "":
            times_to_evaluate = None
        else:
            try:
                custom_time = datetime.datetime.strptime(
                    user_input, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
                times_to_evaluate = [custom_time]
            except ValueError:
                print(f"\n[!] Error: '{user_input}' does not match the expected format.")
                print("    Please use YYYY-MM-DD HH:MM:SS (e.g., 2026-07-25 14:30:00).")