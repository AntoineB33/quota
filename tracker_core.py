import datetime

# ==========================================
# DEFAULT CONFIGURATION
# ==========================================
DEFAULT_CONFIG = {
    'START_WEEKDAY': 0,  # 0 = Monday
    'START_HOUR': 0,
    'START_MINUTE': 0,
    'START_SECOND': 0,
    
    # Sleep schedule defaults
    'SLEEP_START': '22:15',
    'SLEEP_END': '08:20',

    # Number of times the quota resets during the tracked period (must be >= 1)
    'QUOTA_CYCLES': 1
}

def get_active_seconds(start_dt, end_dt, sleep_start_str, sleep_end_str):
    """
    Calculates total active seconds between start_dt and end_dt, 
    excluding daily periods between sleep_start and sleep_end.
    """
    if not sleep_start_str or not sleep_end_str or start_dt >= end_dt:
        return max(0.0, (end_dt - start_dt).total_seconds())
    
    sleep_start_h, sleep_start_m = map(int, sleep_start_str.split(':'))
    sleep_end_h, sleep_end_m = map(int, sleep_end_str.split(':'))
    
    # True if the sleep period goes over midnight (e.g., 22:15 to 08:20)
    sleep_spans_midnight = (sleep_start_h > sleep_end_h) or (
        sleep_start_h == sleep_end_h and sleep_start_m > sleep_end_m)
    
    total_active = 0.0
    current = start_dt
    
    # Evaluate day-by-day to cleanly handle sleep overlap
    while current < end_dt:
        next_day = (current + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        chunk_end = min(end_dt, next_day)
        today_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        
        sleep_intervals = []
        if sleep_spans_midnight:
            # Sleep period split by midnight boundary
            sleep_intervals.append((
                today_start, 
                today_start.replace(hour=sleep_end_h, minute=sleep_end_m)
            ))
            sleep_intervals.append((
                today_start.replace(hour=sleep_start_h, minute=sleep_start_m), 
                today_start + datetime.timedelta(days=1)
            ))
        else:
            # Single sleep block in the same day
            sleep_intervals.append((
                today_start.replace(hour=sleep_start_h, minute=sleep_start_m),
                today_start.replace(hour=sleep_end_h, minute=sleep_end_m)
            ))
            
        sleep_time_in_chunk = 0.0
        for s_start, s_end in sleep_intervals:
            overlap_start = max(current, s_start)
            overlap_end = min(chunk_end, s_end)
            if overlap_start < overlap_end:
                sleep_time_in_chunk += (overlap_end - overlap_start).total_seconds()
        
        total_active += (chunk_end - current).total_seconds() - sleep_time_in_chunk
        current = chunk_end
        
    return total_active


def calculate_period_progression(
    start_weekday, start_hour, start_minute=0, start_second=0,
    end_weekday=None, end_hour=None, end_minute=None, end_second=None,
    reference_time=None, quota_cycles=1, sleep_start=None, sleep_end=None
):
    """
    Calculates the active time progression percentage between a specific start 
    and end time within a weekly cycle, omitting sleep hours.
    """
    # Apply default values for end time if not explicitly provided
    if end_weekday is None: end_weekday = start_weekday
    if end_hour is None: end_hour = start_hour
    if end_minute is None: end_minute = start_minute
    if end_second is None: end_second = start_second

    now = reference_time if reference_time else datetime.datetime.now().astimezone()

    # 1. Find the most recent start time
    current_day_start = now.replace(
        hour=start_hour, minute=start_minute, second=start_second, microsecond=0
    )
    days_since_start = (now.weekday() - start_weekday) % 7
    start_time = current_day_start - datetime.timedelta(days=days_since_start)

    if now < start_time and days_since_start == 0:
        start_time -= datetime.timedelta(days=7)

    # 2. Find the corresponding end time
    end_time = start_time.replace(
        hour=end_hour, minute=end_minute, second=end_second, microsecond=0
    )
    
    days_to_end = (end_weekday - start_weekday) % 7
    end_time += datetime.timedelta(days=days_to_end)

    # If start and end are exactly the same, it creates a full 7-day period
    if end_time <= start_time:
        end_time += datetime.timedelta(days=7)

    # 3. Calculate ACTIVE elapsed time and total ACTIVE duration
    total_duration = get_active_seconds(start_time, end_time, sleep_start, sleep_end)
    calc_end_time = min(now, end_time)
    elapsed_time = get_active_seconds(start_time, calc_end_time, sleep_start, sleep_end)

    # 4. Calculate percentage based on the number of quota cycles
    if elapsed_time >= total_duration or total_duration <= 0:
        percentage = 100.0 if now >= end_time else 0.0
        is_active = False
    else:
        # Divide the active period into sub-cycles based on QUOTA_CYCLES
        cycle_duration = total_duration / max(1, quota_cycles)
        elapsed_in_current_cycle = elapsed_time % cycle_duration
        percentage = (elapsed_in_current_cycle / cycle_duration) * 100
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

    # Fallback missing END constants to START constants
    for suffix in ['WEEKDAY', 'HOUR', 'MINUTE', 'SECOND']:
        end_key = f'END_{suffix}'
        start_key = f'START_{suffix}'
        if end_key not in config:
            config[end_key] = config[start_key]

    times_to_evaluate = None

    while True:
        if times_to_evaluate is None:
            now = datetime.datetime.now().astimezone()
            
            # Calculate next sleep start time
            sleep_start_str = config.get('SLEEP_START', '22:15')
            sleep_start_h, sleep_start_m = map(int, sleep_start_str.split(':'))
            
            today_sleep_start = now.replace(
                hour=sleep_start_h, minute=sleep_start_m, second=0, microsecond=0
            )
            
            if today_sleep_start <= now:
                next_sleep_start = today_sleep_start + datetime.timedelta(days=1)
            else:
                next_sleep_start = today_sleep_start
                
            current_batch = [now, next_sleep_start]
        else:
            current_batch = times_to_evaluate

        for eval_time in current_batch:
            progression_pct, start, end, is_active = calculate_period_progression(
                config['START_WEEKDAY'], config['START_HOUR'], config['START_MINUTE'], config['START_SECOND'],
                config['END_WEEKDAY'], config['END_HOUR'], config['END_MINUTE'], config['END_SECOND'],
                eval_time, config.get('QUOTA_CYCLES', 1), config.get('SLEEP_START'), config.get('SLEEP_END')
            )
            
            if eval_time == current_batch[0] and times_to_evaluate is None:
                label = "Current Time"
            elif times_to_evaluate is None:
                label = "Next Sleep Start"
            else:
                label = "Evaluated Time"

            status = "ACTIVE" if is_active else "COMPLETED/WAITING"

            print(f"\n{name} Tracker")
            print("=" * 55)
            print(f"Cycle Start : {start.strftime('%A, %Y-%m-%d %H:%M:%S')}")
            print(f"Cycle End   : {end.strftime('%A, %Y-%m-%d %H:%M:%S')}")
            print(f"Sleep Time  : {config.get('SLEEP_START', 'N/A')} to {config.get('SLEEP_END', 'N/A')}")
            print(f"{label.ljust(16)}: {eval_time.strftime('%A, %Y-%m-%d %H:%M:%S')}")
            print("-" * 55)
            print(f"Progression : {progression_pct:.4f}% ({status})")
            print("=" * 55)

        print("\nOptions:")
        print("  - Press [Enter] for a normal run (current time & next sleep start)")
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