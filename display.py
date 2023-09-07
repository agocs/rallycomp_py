import curses
import sys
from rallycomp import RallyComputer
import math


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
    caughtExceptions = ""
    try:
        initialized = False

        rcomp = RallyComputer()

        while True:
            # Header
            time_string = rcomp.odo.lastFix.timestamp.strftime("%H:%M:%S.%f")[:-3]
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
            paceWin = curses.newwin(5, curses.COLS - 1, 4, 1)
            paceWin.bkgd(" ", curses.color_pair(1))
            paceWin.box()
            pace_width = paceWin.getmaxyx()[1]
            minus10 = int(pace_width * 0.2)
            minus5 = int(pace_width * 0.3)
            minus1 = int(pace_width * 0.4)
            zero = int(pace_width * 0.5)
            plus1 = int(pace_width * 0.6)
            plus5 = int(pace_width * 0.7)
            plus10 = int(pace_width * 0.8)
            paceWin.addstr(1, minus10, "-10", curses.color_pair(1))
            paceWin.addstr(1, minus5, "-5", curses.color_pair(1))
            paceWin.addstr(1, minus1, "-1", curses.color_pair(1))
            paceWin.addstr(1, zero, "0", curses.color_pair(1))
            paceWin.addstr(1, plus1, "1", curses.color_pair(1))
            paceWin.addstr(1, plus5, "5", curses.color_pair(1))
            paceWin.addstr(1, plus10, "10", curses.color_pair(1))

            shaded_area = "█" * (plus1 - minus1)
            paceWin.addstr(2, minus1 + 1, shaded_area, curses.color_pair(1))

            # TODO: verify this math
            cursor_multiple = math.atan(rcomp.cast.get_offset()) / 2
            cursor_offset = int(pace_width / 2 * cursor_multiple)
            cursor_position = int(pace_width / 2) + cursor_offset

            # TODO: figure out position of this cursor
            paceWin.addstr(2, cursor_position, "|", curses.color_pair(1))

            paceWin.addstr(3, 1, "Speed up!", curses.color_pair(1))
            paceWin.addstr(3, pace_width - 11, "Slow down!", curses.color_pair(1))
            paceWin.refresh()

            # Odometer

            odo_string = "{:3.3f}".format(rcomp.odo.distanceAccumulator / 1000)

            odometerWindow = curses.newwin(5, 20, 9, 1)
            odometerWindow.bkgd(" ", curses.color_pair(1))
            odometerWindow.box()
            odometerWindow.addstr(
                1, 1, "Odometer", curses.color_pair(1) | curses.A_BOLD
            )
            odometerWindow.addstr(2, 2, "km:", curses.color_pair(1))
            odometerWindow.addstr(
                2, odometerWindow.getmaxyx()[1] - 8, odo_string, curses.color_pair(1)
            )
            odometerWindow.addstr(3, 2, "calib.: 1.0", curses.color_pair(1))
            odometerWindow.refresh()

            # Speedometer
            speed_str = "{:2.5f}".format(rcomp.odo.lastFix.speed)
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

            currWin = curses.newwin(9, 30, 14, 1)
            currWin.bkgd(" ", curses.color_pair(1))
            currWin.box()
            currWin.addstr(
                1, 1, "Current Instruction", curses.color_pair(1) | curses.A_BOLD
            )
            currWin.addstr(2, 2, "time remaining:", curses.color_pair(1))
            currWin.addstr(
                2, currWin.getmaxyx()[1] - 9, "00:00:00", curses.color_pair(1)
            )
            currWin.addstr(3, 2, "dist remaining", curses.color_pair(1))
            currWin.addstr(
                3, currWin.getmaxyx()[1] - 8, "000.000", curses.color_pair(1)
            )
            currWin.addstr(4, 2, "CAST:", curses.color_pair(1))
            currWin.addstr(4, currWin.getmaxyx()[1] - 6, cast_str, curses.color_pair(1))
            currWin.addstr(5, 2, "offset:", curses.color_pair(1))
            currWin.addstr(
                5, currWin.getmaxyx()[1] - 7, offset_str, curses.color_pair(1)
            )
            if rcomp.cast.get_offset() > 0:
                currWin.addstr(
                    6, currWin.getmaxyx()[1] - 10, "Slow down", curses.color_pair(1)
                )
            elif rcomp.cast.get_offset() < 0:
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
            nextWin = curses.newwin(8, 30, 14, 31)
            nextWin.bkgd(" ", curses.color_pair(1))
            nextWin.box()
            nextWin.addstr(
                1, 1, "Next Instruction", curses.color_pair(1) | curses.A_BOLD
            )
            nextWin.addstr(2, 2, "actual [t]ime:", curses.color_pair(1))
            nextWin.addstr(
                2, nextWin.getmaxyx()[1] - 9, "00:00:00", curses.color_pair(1)
            )
            nextWin.addstr(3, 2, "[d]istance:", curses.color_pair(1))
            nextWin.addstr(
                3, nextWin.getmaxyx()[1] - 8, "000.000", curses.color_pair(1)
            )
            nextWin.addstr(4, 2, "[C]AST:", curses.color_pair(1))
            nextWin.addstr(4, nextWin.getmaxyx()[1] - 6, "00.00", curses.color_pair(1))
            nextWin.refresh()

            rcomp.update()
            initialized = True

            # Grabs a value from the keyboard without Enter having to be pressed (see cbreak above)
            key = stdscr.getch()
            if key == ord("q"):
                break
    except Exception as err:
        # Just printing from here will not work, as the program is still set to
        # use ncurses.
        # print ("Some error [" + str(err) + "] occurred.")
        caughtExceptions = str(err)

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
