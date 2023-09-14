import curses
import curses.textpad
import datetime
import sys
import time
import traceback
from rallycomp import Instruction, OdometerMode, RallyComputer
import math
from dateutil import parser


def atan_position(width: int, position: int) -> int:
    cursor_multiple = math.atan(position / 4) / 1.2
    cursor_offset = int(width / 2 * cursor_multiple)
    return int(width / 2) + cursor_offset


def update_instruction(
    instruction: Instruction, command: str, value: str, tz: datetime.timezone
):
    if command == "c":
        instruction.set_speed(float(value))
    elif command == "d":
        instruction.set_distance(float(value))
    elif command == "t":
        iTime = parser.parse(value, fuzzy=True, ignoretz=True).replace(tzinfo=tz)
        instruction.set_time(iTime)
    elif command == "p":
        instruction.speed = 0
        # TODO: pause
    else:
        raise Exception("Unknown command: " + command)


def activate_window(win):
    win.bkgd(" ", curses.color_pair(2))
    win.refresh()


def deactivate_window(win):
    win.bkgd(" ", curses.color_pair(1))
    win.refresh()


def main(argv):
    # BEGIN ncurses startup/initialization...
    # Initialize the curses object.
    stdscr = curses.initscr()

    # Do not echo keys back to the client.
    curses.noecho()

    # Non-blocking or cbreak mode... do not wait for Enter key to be pressed.
    curses.cbreak()
    stdscr.nodelay(1)

    # Turn off blinking cursor
    curses.curs_set(False)

    # Enable color if we can...
    if curses.has_colors():
        curses.start_color()

    # Optional - Enable the keypad. This also decodes multi-byte key sequences
    # stdscr.keypad(True)

    # END ncurses startup/initialdization...
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED)
    caughtExceptions = ""
    try:
        initialized = False

        rcomp = RallyComputer()

        current_instruction = Instruction(distance_km=0, speed_kmh=0, dummy=True)
        rcomp.start_instruction(current_instruction)
        rcomp.odo.mode = OdometerMode.PARK

        next_instrucion = Instruction()

        commandStr = ""
        errorStr = ""

        while True:
            # Header
            localtime = rcomp.odo.lastFix.timestamp.astimezone(
                rcomp.config.get_timezone()
            )
            time_string = localtime.strftime("%H:%M:%S.%f")[:-3]
            headerWindow = curses.newwin(3, curses.COLS - 1, 1, 1)
            headerWindow.bkgd(" ", curses.color_pair(1))
            headerWindow.box()
            if initialized:
                headerWindow.addstr(1, 1, "Rally Computer", curses.color_pair(1))
            else:
                headerWindow.addstr(1, 1, "Initializing...", curses.color_pair(1))
            headerWindow.addstr(
                1,
                int(headerWindow.getmaxyx()[1] / 2) - 6,
                time_string,
                curses.color_pair(1),
            )
            headerWindow.refresh()

            # Pace
            pace = rcomp.cast.get_offset()
            paceWin = curses.newwin(5, curses.COLS - 1, 4, 1)
            paceColor = curses.color_pair(2)
            if pace > 0.5:
                paceColor = curses.color_pair(4)  # red
            elif pace < -0.5:
                paceColor = curses.color_pair(3)  # yellow
            else:
                paceColor = curses.color_pair(2)  # green
            paceWin.bkgd(" ", paceColor)
            paceWin.box()
            pace_width = paceWin.getmaxyx()[1]
            minus10 = atan_position(pace_width, -10)
            minus5 = atan_position(pace_width, -5)
            minus1 = atan_position(pace_width, -1)
            zero = atan_position(pace_width, 0)
            plus1 = atan_position(pace_width, 1) - 2
            plus5 = atan_position(pace_width, 5) - 2
            plus10 = atan_position(pace_width, 10) - 3
            paceWin.addstr(1, minus10, "-10", paceColor)
            paceWin.addstr(1, minus5, "-5", paceColor)
            paceWin.addstr(1, minus1, "-1", paceColor)
            paceWin.addstr(1, zero, "0", paceColor)
            paceWin.addstr(1, plus1, "1", paceColor)
            paceWin.addstr(1, plus5, "5", paceColor)
            paceWin.addstr(1, plus10, "10", paceColor)

            shaded_area = "_" * (plus1 - minus1)
            paceWin.addstr(2, minus1 + 1, shaded_area, paceColor)

            cursor_position = atan_position(pace_width, rcomp.cast.get_offset())
            if cursor_position < 1:
                cursor_position = 1
            if cursor_position > (pace_width - 2):
                cursor_position = pace_width - 2
            paceWin.addstr(2, cursor_position, "█", paceColor)

            paceWin.addstr(3, 1, "Speed up!", paceColor)
            paceWin.addstr(3, pace_width - 11, "Slow down!", paceColor)
            paceWin.refresh()

            # Odometer

            odo_string = "{:3.3f}".format(rcomp.odo.get_accumulated_distance() / 1000)
            odo_mode_string = rcomp.odo.mode.name
            odometerWindow = curses.newwin(5, 20, 9, 1)
            odometerWindow.bkgd(" ", curses.color_pair(1))
            odometerWindow.box()
            odometerWindow.addstr(
                1, 1, "[O]dometer", curses.color_pair(1) | curses.A_BOLD
            )
            odometerWindow.addstr(2, 2, "km:", curses.color_pair(1))
            odometerWindow.addstr(
                2, odometerWindow.getmaxyx()[1] - 8, odo_string, curses.color_pair(1)
            )
            odometerWindow.addstr(3, 2, "Mode:", curses.color_pair(1))
            odometerWindow.addstr(
                3,
                odometerWindow.getmaxyx()[1] - (len(odo_mode_string) + 1),
                odo_mode_string,
                curses.color_pair(1),
            )
            odometerWindow.refresh()

            # Speedometer
            speed_str = "{:2.5f}".format(rcomp.odo.get_last_speed())
            speedWin = curses.newwin(5, 20, 9, 21)
            speedWin.bkgd(" ", curses.color_pair(1))
            speedWin.box()
            speedWin.addstr(1, 1, "Speedometer", curses.color_pair(1) | curses.A_BOLD)
            speedWin.addstr(2, 2, "km/h:", curses.color_pair(1))
            speedWin.addstr(
                2, speedWin.getmaxyx()[1] - 9, speed_str, curses.color_pair(1)
            )
            speedWin.refresh()

            # Current Instruction
            cast_str = "{:2.2f}".format(rcomp.cast.average)
            offset_str = "{:2.2f}".format(rcomp.cast.get_offset())
            time_remaining_str = str(rcomp.current_instruction.get_time_remaining())
            if len(time_remaining_str) > 11:
                time_remaining_str = time_remaining_str[:11]
            dist_remaining_str = "{:3.3f}".format(
                rcomp.current_instruction.get_distance_remaining() / 1000
            )
            currWin = curses.newwin(9, 30, 14, 1)
            currWin.bkgd(" ", curses.color_pair(1))
            currWin.box()
            currWin.addstr(
                1, 1, "Current Instruction", curses.color_pair(1) | curses.A_BOLD
            )
            currWin.addstr(2, 2, "time remaining:", curses.color_pair(1))
            currWin.addstr(
                2,
                currWin.getmaxyx()[1] - len(time_remaining_str) - 1,
                time_remaining_str,
                curses.color_pair(1),
            )
            currWin.addstr(3, 2, "dist remaining", curses.color_pair(1))
            currWin.addstr(
                3,
                currWin.getmaxyx()[1] - len(dist_remaining_str) - 1,
                dist_remaining_str,
                curses.color_pair(1),
            )
            currWin.addstr(4, 2, "CAST:", curses.color_pair(1))
            currWin.addstr(4, currWin.getmaxyx()[1] - 6, cast_str, curses.color_pair(1))
            currWin.addstr(5, 2, "offset:", curses.color_pair(1))
            currWin.addstr(
                5, currWin.getmaxyx()[1] - 7, offset_str, curses.color_pair(1)
            )
            if rcomp.cast.get_offset() > 0.5:
                currWin.addstr(
                    6, currWin.getmaxyx()[1] - 10, "Slow down", curses.color_pair(1)
                )
            elif rcomp.cast.get_offset() < -0.5:
                currWin.addstr(
                    6, currWin.getmaxyx()[1] - 10, "Speed up!", curses.color_pair(1)
                )
            else:
                currWin.addstr(
                    6,
                    int(currWin.getmaxyx()[1]) - 10,
                    "Right On!",
                    curses.color_pair(1),
                )
            currWin.refresh()

            # Next Instruction
            nextActTime = next_instrucion.get_time().strftime("%H:%M:%S")
            nextActDist = "{:3.3f}".format(next_instrucion.get_distance())
            nextActCast = "{:2.2f}".format(next_instrucion.get_speed())
            nextWin = curses.newwin(8, 30, 14, 31)
            nextWin.bkgd(" ", curses.color_pair(1))
            nextWin.box()
            nextWin.addstr(
                1, 1, "Next Instruction", curses.color_pair(1) | curses.A_BOLD
            )
            nextWin.addstr(2, 2, "actual [t]ime:", curses.color_pair(1))
            nextWin.addstr(
                2, nextWin.getmaxyx()[1] - 9, nextActTime, curses.color_pair(1)
            )
            nextWin.addstr(3, 2, "[d]istance:", curses.color_pair(1))
            nextWin.addstr(
                3, nextWin.getmaxyx()[1] - 8, nextActDist, curses.color_pair(1)
            )
            nextWin.addstr(4, 2, "[C]AST:", curses.color_pair(1))
            nextWin.addstr(
                4, nextWin.getmaxyx()[1] - 6, nextActCast, curses.color_pair(1)
            )
            nextWin.refresh()

            # Command
            commandTitlewin = curses.newwin(3, 30, 24, 1)
            commandTitlewin.bkgd(" ", curses.color_pair(1))
            commandTitlewin.box()
            commandTitlewin.refresh()

            commandWin = curses.newwin(1, 30, 27, 1)
            commandWin.bkgd(" ", curses.color_pair(1))
            commandBox = curses.textpad.Textbox(commandWin)
            commandWin.refresh()

            # Errors
            errorWin = curses.newwin(5, 20, 24, 31)
            errorWin.bkgd(" ", curses.color_pair(1))
            errorWin.box()
            errorWin.addstr(1, 1, "Errors", curses.color_pair(1) | curses.A_BOLD)
            errorWin.addstr(2, 1, errorStr, curses.color_pair(1))
            errorWin.refresh()

            rcomp.try_update()
            time.sleep(0.05)
            initialized = True

            # Command Keys
            commandKeys = {
                "c": ("CAST", update_instruction),
                "d": ("Distance", update_instruction),
                "t": ("Time", update_instruction),
                "p": ("Pause", update_instruction),
            }

            # Grabs a value from the keyboard without Enter having to be pressed (see cbreak above)
            key = stdscr.getch()
            if key == ord("q"):
                break
            if key > 0 and chr(key) in commandKeys.keys():
                errorStr = ""
                commandName = commandKeys[chr(key)][0]
                commandFunction = commandKeys[chr(key)][1]
                commandTitlewin.clear()
                activate_window(commandTitlewin)
                commandTitlewin.box()
                commandTitlewin.addstr(1, 1, commandName, curses.color_pair(2))
                commandTitlewin.refresh()

                commandWin.clear()
                activate_window(commandWin)
                commandBox.edit()
                text = commandBox.gather()
                try:
                    commandFunction(
                        next_instrucion, chr(key), text, rcomp.config.get_timezone()
                    )
                except Exception as err:
                    errorStr = str(err)
                text = ""
                commandWin.clear()
                deactivate_window(commandWin)
                commandTitlewin.clear()
                deactivate_window(commandTitlewin)
            if key == ord(" "):
                errorStr = ""
                if next_instrucion.verify():
                    if current_instruction.dummy:
                        rcomp.odo.reset()
                    current_instruction = next_instrucion
                    rcomp.start_instruction(current_instruction)
                    next_instrucion = Instruction(
                        speed_kmh=current_instruction.get_speed()
                    )
                else:
                    errorStr = "Instruction is not valid!"
            if key == ord("o"):
                errorStr = ""
                commandTitlewin.clear()
                activate_window(commandTitlewin)
                commandTitlewin.box()
                commandTitlewin.addstr(
                    1, 1, "Odometer [D][R][P][C][Z]", curses.color_pair(2)
                )
                commandTitlewin.refresh()

                commandWin.clear()
                activate_window(commandWin)
                commandBox.edit()
                text = commandBox.gather()
                if text.lower().startswith("d"):
                    rcomp.odo.mode = OdometerMode.DRIVE
                elif text.lower().startswith("r"):
                    rcomp.odo.mode = OdometerMode.REVERSE
                elif text.lower().startswith("p"):
                    rcomp.odo.mode = OdometerMode.PARK
                elif text.lower().startswith("c"):
                    commandTitlewin.clear()
                    activate_window(commandTitlewin)
                    commandTitlewin.box()
                    commandTitlewin.addstr(
                        1, 1, "Enter expected odometer", curses.color_pair(2)
                    )
                    commandTitlewin.refresh()

                    commandWin.clear()
                    activate_window(commandWin)
                    commandBox.edit()
                    text = commandBox.gather()
                    try:
                        expected_distance = float(text)
                        rcomp.odo.calibrate(expected_distance)
                        rcomp.config.set_calibration(rcomp.odo.calibration)
                        errorStr = "Cal: {}".format(rcomp.odo.calibration)
                    except Exception as err:
                        errorStr = str(err)
                elif text.lower().startswith("z"):
                    rcomp.odo.distanceAccumulator = 0
                else:
                    errorStr = "Unknown mode! [D][R][P][C][Z]"

    except Exception as err:
        # Just printing from here will not work, as the program is still set to
        # use ncurses.
        # print ("Some error [" + str(err) + "] occurred.")
        caughtExceptions = str(err)
        caughtExceptions += str(traceback.format_exc())

    # BEGIN ncurses shutdown/deinitialization...
    # Turn off cbreak mode...
    curses.nocbreak()

    # Turn echo back on.
    curses.echo()

    # Restore cursor blinking.
    curses.curs_set(True)

    # Turn off the keypad...
    # stdscr.keypad(False)

    # Restore Terminal to original state.
    curses.endwin()

    # END ncurses shutdown/deinitialization...

    # Display Errors if any happened:
    if "" != caughtExceptions:
        print("Got error(s) [" + caughtExceptions + "]")


if __name__ == "__main__":
    curses.wrapper(main)
