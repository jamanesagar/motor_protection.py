import time

# ANSI color codes
RED = '\033[31m'    # Red color
GREEN = '\033[32m'  # Green color
BLUE = '\033[34m'   # Blue color
YELLOW = '\033[33m' # Yellow color
CYAN = '\033[36m'   # Cyan color
ORANGE = '\033[93m' # Orange color
ENDC = '\033[0m'    # Reset color to default

# Initial settings (these won't change unless the correct password is provided)
initial_relay_setting_current = 1.0  # Example initial value
initial_time_multiplier_setting = 1.0  # Example initial value

# Current settings (these will be modified during normal operation)
relay_setting_current = initial_relay_setting_current
time_multiplier_setting = initial_time_multiplier_setting

def classify_fault(Ia, Ib, Ic, I_s):
    # Simple example to classify faults based on current values
    if Ia > 5 * I_s or Ib > 5 * I_s or Ic > 5 * I_s:
        return 'short circuit'
    elif (Ia <= 0.75 * I_s and Ib <= 0.75 * I_s) or (Ia <= 0.75 * I_s and Ic <= 0.75 * I_s) or (Ib <= 0.75 * I_s and Ic <= 0.75 * I_s):
        return 'prime mover got decoupled'
    elif Ia > 1.5 * I_s or Ib > 1.5 * I_s or Ic > 1.5 * I_s:
        return 'overcurrent'
    elif Ia > 1.2 * I_s or Ib > 1.2 * I_s or Ic > 1.2 * I_s:
        return 'overload'
    else:
        return 'no fault'

def standard_inverse_trip_time_three_phase(Ia, Ib, Ic, I_s, TMS):
    k = 0.14
    n = 0.02

    # Check for missing phases
    missing_phases = []
    if Ia == 0:
        missing_phases.append('R')
    if Ib == 0:
        missing_phases.append('Y')
    if Ic == 0:
        missing_phases.append('B')

    if len(missing_phases) == 1:
        fault_type = f"{missing_phases[0]} phase missing"
    elif len(missing_phases) == 2:
        fault_type = f"{missing_phases[0]} and {missing_phases[1]} phases missing"
    elif len(missing_phases) == 3:
        fault_type = "All phases missing"
    else:
        fault_type = classify_fault(Ia, Ib, Ic, I_s)

    # Special conditions for tripping times
    if fault_type == 'prime mover got decoupled':
        return 5, fault_type
    elif fault_type in ["R and Y phases missing", "R and B phases missing", "Y and B phases missing", "All phases missing"]:
        return 2, fault_type

    # Find the highest phase current
    I = max(Ia, Ib, Ic)

    if fault_type == 'no fault':
        return float('inf'), 'no fault'

    T = (k * TMS) / ((I / I_s) ** n - 1)
    return T, fault_type

# Function to reset relay with password confirmation
def reset_relay_with_confirmation():
    reset_password = "password123"  # Replace with your actual password

    while True:
        user_password = input(f"{ORANGE}Enter reset password: {ENDC}")
        if user_password == reset_password:
            return True
        else:
            print("Incorrect password. Access denied.")
            return False

# Function to change relay settings with password protection
def change_relay_settings_with_password():
    set_password = "admin123"  # Replace with your actual password

    while True:
        user_password = input("Enter admin password to change relay settings: ")
        if user_password == set_password:
            global relay_setting_current, time_multiplier_setting
            relay_setting_current = float(input("Enter new current relay setting: "))
            time_multiplier_setting = float(input("Enter new time multiplier setting: "))
            print("Settings updated successfully.")
            return
        else:
            print("Incorrect password. Access denied.")

# Function for continuous monitoring with automatic trip and latch
def continuous_monitoring():
    relay_latched = False
    settings_changed = False

    while True:
        if not relay_latched:
            fault_current_a = float(input(f"{BLUE}Enter R phase current: {RED}"))
            fault_current_b = float(input(f"{BLUE}Enter Y phase current: {RED}"))
            fault_current_c = float(input(f"{BLUE}Enter B phase current: {RED}"))

            # Display current settings only when settings are changed
            if settings_changed:
                print(f"Current relay setting: {relay_setting_current}")
                print(f"Current time multiplier setting: {time_multiplier_setting}")

            # Use current settings for calculation
            trip_time, fault_type = standard_inverse_trip_time_three_phase(fault_current_a, fault_current_b, fault_current_c, relay_setting_current, time_multiplier_setting)

            if trip_time != float('inf'):
                print(f"{GREEN}Trip command generated for {RED}{fault_type}{GREEN}! Waiting for {trip_time:.2f} seconds before latching the relay.{ENDC}")
                time.sleep(trip_time)  # Simulate delay
                relay_latched = True
                print(f"{YELLOW}Relay latched.{ENDC}")

        # Check if relay needs resetting
        if relay_latched:
            if reset_relay_with_confirmation():
                print(f"{YELLOW}Relay has been reset.{ENDC}")
                settings_changed = False  # Reset settings change flag
                relay_latched = False
                change_settings = input(f"{CYAN}Do you want to change relay settings? (yes/no): {ENDC}").strip().lower()
                if change_settings == 'yes':
                    change_relay_settings_with_password()
                    settings_changed = True  # Mark settings as changed to avoid repeated prompts

        # Ask for setting change only when relay is latched and settings have not been changed
        if relay_latched and not settings_changed:
            change_settings = input(f"{CYAN}Do you want to change relay settings? (yes/no): {ENDC}").strip().lower()
            if change_settings == 'yes':
                change_relay_settings_with_password()
                settings_changed = True  # Mark settings as changed to avoid repeated prompts

# Main program starts continuous monitoring
if __name__ == "__main__":
    continuous_monitoring()
