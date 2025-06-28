#!/usr/bin/python3
"""
A modular, class-based script for reading and processing joystick input on the STEAM DECK

This script defines a `Joystick` class that encapsulates SDL initialization,
event polling, and state management. It provides a clean API with specific
"getter" methods for different parts of the controller, making it highly
reusable for other developers.
"""

import sys
import os
import sdl2
from rich.live import Live
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel

# --- Configuration Constants ---
# Note: These are common values for a Steam Deck. Adjust for your controller.
JOYSTICK_INDEX = 0          # The joystick to use (0 is the first one found)
NUM_AXES_TO_TRACK = 6       # Number of axes to monitor (Steam Deck has 6)
NUM_BUTTONS_TO_TRACK = 20   # Number of buttons to monitor (covers back buttons)
REFRESH_RATE_HZ = 60        # Target refresh rate for the display
REFRESH_DELAY_SEC = int(1 / REFRESH_RATE_HZ) # Calculate delay in seconds

class Joystick:
    """A class to manage and read data from an SDL2 joystick."""

    def __init__(self, index=JOYSTICK_INDEX, num_axes=NUM_AXES_TO_TRACK, num_buttons=NUM_BUTTONS_TO_TRACK):
        """
        Initializes the Joystick, including SDL and the physical device.

        Args:
            index (int): The system index of the joystick to open (0 is the first).
            num_axes (int): The number of axes to track.
            num_buttons (int): The number of buttons to track.
        """
        self._joystick = None
        self._initialize_sdl()
        self._open_joystick(index)

        # Master state dictionaries that hold the real-time data
        self.axis_values = {i: 0 for i in range(num_axes)}
        self.button_values = {i: 0 for i in range(num_buttons)}

    def _initialize_sdl(self):
        """Initializes the SDL joystick subsystem."""
        if sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK) < 0:
            raise RuntimeError(f"SDL Init Error: {sdl2.SDL_GetError().decode()}")

    def _open_joystick(self, index):
        """Opens the physical joystick device."""
        if sdl2.SDL_NumJoysticks() < 1:
            raise RuntimeError("No joystick found. Please connect a controller.")

        self._joystick = sdl2.SDL_JoystickOpen(index)
        if not self._joystick:
            raise RuntimeError(f"Failed to open joystick {index}: {sdl2.SDL_GetError().decode()}")

        sdl2.SDL_JoystickEventState(sdl2.SDL_ENABLE)
        print(f"Opened: {sdl2.SDL_JoystickName(self._joystick).decode()}")

    def update(self):
        """
        This is the core polling method. It must be called once per frame.
        It processes all pending SDL events and updates the internal state.

        Returns:
            bool: False if a quit event was received, True otherwise.
        """
        event = sdl2.SDL_Event()
        # Process pending SDL events and stores them in event
        while sdl2.SDL_PollEvent(event) != 0:
            # joystick and triggers
            if event.type == sdl2.SDL_JOYAXISMOTION:
                if event.jaxis.axis in self.axis_values:
                    self.axis_values[event.jaxis.axis] = event.jaxis.value
            # D-pad and buttons
            elif event.type in (sdl2.SDL_JOYBUTTONDOWN, sdl2.SDL_JOYBUTTONUP):
                if event.jbutton.button in self.button_values:
                    self.button_values[event.jbutton.button] = event.jbutton.state
            # Check for Quit event
            elif event.type == sdl2.SDL_QUIT:
                # If the window is closed, we should exit gracefully.
                return False
        return True

    # --- Getter Methods for Developers ---

    @property
    def dpad_state(self):
        """
        Returns the state of the D-Pad as a dictionary.

        Note:
            On the Steam Deck, the D-Pad registers as individual buttons.
            This method maps buttons 11, 12, 13, and 14 to D-Pad directions.

        Returns:
            dict: The state of the D-Pad. Example:
                ```
                {
                    "Up (11)": 0,
                    "Down (12)": 1,
                    "Left (13)": 0,
                    "Right (14)": 0
                }
                ```
        """
        dpad_dict = {
            "Up": self.button_values.get(11, 0),
            "Down": self.button_values.get(12, 0),
            "Left": self.button_values.get(13, 0),
            "Right": self.button_values.get(14, 0),
        }
        return dpad_dict

    @property
    def face_buttons(self):
        """
        Returns the state of the four primary face buttons (A, B, X, Y).

        Returns:
            dict: The state of the face buttons. Example:
                ```
                {
                    "A (0)": 1,
                    "B (1)": 0,
                    "X (2)": 0,
                    "Y (3)": 0
                }
                ```
        """
        face_buttons_dict = {
            "A": self.button_values.get(0, 0),
            "B": self.button_values.get(1, 0),
            "X": self.button_values.get(2, 0),
            "Y": self.button_values.get(3, 0),
        }
        return face_buttons_dict

    @property
    def shoulder_state(self):
        """
        Returns the state of the shoulder bumpers (L1/R1) and triggers (L2/R2).

        Returns:
            dict: A dictionary containing the state of the shoulder controls.
                  The bumpers are buttons, and the triggers are analog axes.
                  Example:
                  ```
                  {
                      "L1 (9)": 1,
                      "R1 (10)": 0,
                      "L2 Axis (4)": -32768,
                      "R2 Axis (5)": 21530
                  }
                  ```
        """
        shoulder_dict = {
            "L1": self.button_values.get(9, 0),
            "R1": self.button_values.get(10, 0),
            "L2 Axis": self.axis_values.get(4, 0),
            "R2 Axis": self.axis_values.get(5, 0),
        }
        return shoulder_dict

    @property
    def joystick_state(self):
        """
        Returns the state of both joysticks, including their axes and click-buttons.

        Returns:
            dict: A dictionary containing the state of the joysticks.
                  Example:
                  ```
                  {
                      "L-Stick X (0)": 12040,
                      "L-Stick Y (1)": -256,
                      "R-Stick X (2)": -32768,
                      "R-Stick Y (3)": 32767,
                      "L3 Click (7)": 0,
                      "R3 Click (8)": 1
                  }
                  ```
        """
        joystick_dict = {
            "LX": self.axis_values.get(0, 0),
            "LY": self.axis_values.get(1, 0),
            "RX": self.axis_values.get(2, 0),
            "RY": self.axis_values.get(3, 0),
            "L3": self.button_values.get(7, 0),
            "R3": self.button_values.get(8, 0),
        }
        return joystick_dict

    @property
    def back_buttons(self):
        """
        Returns the state of the back grip buttons (L4, R4, L5, R5).

        Returns:
            dict: A dictionary containing the state of the back buttons.
                  Example:
                  ```
                  {
                      "L4 (17)": 0,
                      "R4 (16)": 1,
                      "L5 (19)": 0,
                      "R5 (18)": 0
                  }
                  ```
        """
        back_buttons_dict = {
            "L4": self.button_values.get(17, 0),
            "R4": self.button_values.get(16, 0),
            "L5": self.button_values.get(19, 0),
            "R5": self.button_values.get(18, 0),
        }
        return back_buttons_dict

    @property
    def full_state(self):
        """
        Returns a complete snapshot of all tracked axes and buttons.

        Returns:
            dict: A dictionary containing two keys, 'axes' and 'buttons',
                  whose values are dictionaries of the raw states.
                  Example:
                  ```
                  {
                      "axes": {0: -256, 1: 12040, ...},
                      "buttons": {0: 1, 1: 0, ...}
                  }
                  ```
        """
        full_state_dict = {
            "axes": self.axis_values.copy(),
            "buttons": self.button_values.copy(),
        }
        return full_state_dict

    def close(self):
        """Closes the joystick and quits SDL."""
        if self._joystick:
            sdl2.SDL_JoystickClose(self._joystick)
            self._joystick = None
        sdl2.SDL_Quit()
        print("Joystick closed and SDL resources released.")

def generate_dashboard_layout(joystick):
    """
    Generates a rich layout object to be displayed by Live.
    This function NO LONGER prints to the screen. It just builds the layout.
    """
    def create_table(data_dict, title):
        table = Table(title=title, expand=True, show_header=False, border_style="dim")
        table.add_column("Item", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right")
        for item, value in data_dict.items():
            if isinstance(value, int) and value in (0, 1):
                state = "[bold green]Pressed[/]" if value else "[red]Off[/]"
                table.add_row(item, state)
            else:
                color = "green" if value > 1000 else "red" if value < -1000 else "white"
                table.add_row(item, f"[{color}]{value:+6d}[/]")
        return Panel(table, title=f"[bold cyan]{title}[/]", border_style="cyan")

    # --- Use the properties to create each panel ---
    face_button_panel = create_table(joystick.face_buttons, "Face Buttons")
    dpad_panel = create_table(joystick.dpad_state, "D-Pad")
    shoulder_panel = create_table(joystick.shoulder_state, "Shoulders")
    joystick_panel = create_table(joystick.joystick_state, "Joysticks")
    back_button_panel = create_table(joystick.back_buttons, "Back Grips")
    
    left_column = Columns([face_button_panel, dpad_panel])
    right_column = Columns([shoulder_panel, back_button_panel])
    
    return Columns([left_column, joystick_panel, right_column])

def main():
    """Main execution function."""
    joystick = None
    try:
        # Create an instance of our new Joystick class
        joystick = Joystick()

        with Live(generate_dashboard_layout(joystick), screen=True, vertical_overflow="visible") as live:
            # Main application loop
            while True:
                # 1. Update the joystick state by polling events
                joystick.update()

                # 2. Display the data using our modular functions
                live.update(generate_dashboard_layout(joystick))

                # 3. Wait a moment
                sdl2.SDL_Delay(REFRESH_DELAY_SEC)

    except (RuntimeError, KeyboardInterrupt) as e:
        print(f"ERROR: {e}")
    finally:
        if joystick:
            joystick.close()

if __name__ == "__main__":
    main()