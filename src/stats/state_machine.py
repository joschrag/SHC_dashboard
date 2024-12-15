from .read_data import D_Types, read_memory


class StateMachine:
    def __init__(self):
        self.previous_state = None  # Tracks the last state

    def update_state(self, process_name: str) -> str:
        # Read current conditions
        is_year_zero = read_memory(process_name, 0x24BA938, D_Types.INT) == 0
        in_game = not is_year_zero and read_memory(process_name, 0x1311607, D_Types.STRING) != "shc_back.tgx"

        # Determine the next state
        if is_year_zero:
            current_state = "lobby"
        elif in_game:
            current_state = "game"
        else:
            current_state = "stats"

        # Ensure "stats" can only follow "game"
        if current_state == "stats" and self.previous_state != "game":
            current_state = "lobby"  # Default to lobby or another appropriate state

        # Update the previous state tracker
        self.previous_state = current_state

        return current_state
