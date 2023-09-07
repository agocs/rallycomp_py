import curses
import sys

def main(argv):
  # BEGIN ncurses startup/initialization...
  # Initialize the curses object.
  stdscr = curses.initscr()

  # Do not echo keys back to the client.
  curses.noecho()

  # Non-blocking or cbreak mode... do not wait for Enter key to be pressed.
  curses.cbreak()

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
    # stdscr.addstr(1, 1, "Hello World!")
    # stdscr.refresh()


    # Coordinates start from top left, in the format of y, x.
    headerWindow = curses.newwin(3, curses.COLS-1, 1, 1)
    headerWindow.bkgd(' ', curses.color_pair(1))
    headerWindow.box()
    headerWindow.addstr(1, 1, "Rally Computer", curses.color_pair(1))
    headerWindow.refresh()

    # Pace
    paceWin = curses.newwin(5, curses.COLS-1, 4, 1)
    paceWin.bkgd(' ', curses.color_pair(1))
    paceWin.box()
    pace_width = paceWin.getmaxyx()[1]
    minus10 = int(pace_width * .2)
    minus5 = int(pace_width * .3)
    minus1 = int(pace_width * .4)
    zero = int(pace_width * .5)
    plus1 = int(pace_width * .6)
    plus5 = int(pace_width * .7)
    plus10 = int(pace_width * .8)
    paceWin.addstr(1, minus10, "-10", curses.color_pair(1))
    paceWin.addstr(1, minus5, "-5", curses.color_pair(1))
    paceWin.addstr(1, minus1, "-1", curses.color_pair(1))
    paceWin.addstr(1, zero, "0", curses.color_pair(1))
    paceWin.addstr(1, plus1, "1", curses.color_pair(1))
    paceWin.addstr(1, plus5, "5", curses.color_pair(1))
    paceWin.addstr(1, plus10, "10", curses.color_pair(1))

    shaded_area = "█" * (plus1 - minus1)
    paceWin.addstr(2, minus1+1, shaded_area, curses.color_pair(1))
    paceWin.addstr(2, zero-1, "|", curses.color_pair(1) )
    paceWin.addstr(3, 1, "Speed up!", curses.color_pair(1))
    paceWin.addstr(3, pace_width-11, "Slow down!", curses.color_pair(1))
    paceWin.refresh()

    # Odometer
    odometerWindow = curses.newwin(5, 20, 9, 1)
    odometerWindow.bkgd(' ', curses.color_pair(1))
    odometerWindow.box()
    odometerWindow.addstr(1, 1, "Odometer", curses.color_pair(1) | curses.A_BOLD)
    odometerWindow.addstr(2, 2, "miles:", curses.color_pair(1))
    odometerWindow.addstr(2, odometerWindow.getmaxyx()[1]-8, "000.000", curses.color_pair(1))
    odometerWindow.addstr(3, 2, "calib.: 1.0", curses.color_pair(1))
    odometerWindow.refresh()

    # Current Instruction
    currWin = curses.newwin(8, 30, 14, 1)
    currWin.bkgd(' ', curses.color_pair(1))
    currWin.box()
    currWin.addstr(1, 1, "Current Instruction", curses.color_pair(1) | curses.A_BOLD)
    currWin.addstr(2, 2, "time remaining:", curses.color_pair(1))
    currWin.addstr(2, currWin.getmaxyx()[1]-9, "00:00:00", curses.color_pair(1))
    currWin.addstr(3, 2, "dist remaining", curses.color_pair(1))
    currWin.addstr(3, currWin.getmaxyx()[1]-8, "000.000", curses.color_pair(1))
    currWin.addstr(4, 2, "CAST:", curses.color_pair(1))
    currWin.addstr(4, currWin.getmaxyx()[1]-6, "00.00", curses.color_pair(1))
    currWin.addstr(5, 2, "offset:", curses.color_pair(1))
    currWin.addstr(5, currWin.getmaxyx()[1]-7, "-00.10", curses.color_pair(1))
    currWin.addstr(6, currWin.getmaxyx()[1]-10, "Speed up!", curses.color_pair(1))
    currWin.refresh()

    # Next Instruction
    nextWin = curses.newwin(8, 30, 14, 31)
    nextWin.bkgd(' ', curses.color_pair(1))
    nextWin.box()
    nextWin.addstr(1, 1, "Next Instruction", curses.color_pair(1) | curses.A_BOLD)
    nextWin.addstr(2, 2, "actual [t]ime:", curses.color_pair(1))
    nextWin.addstr(2, nextWin.getmaxyx()[1]-9, "00:00:00", curses.color_pair(1))
    nextWin.addstr(3, 2, "[d]istance:", curses.color_pair(1))
    nextWin.addstr(3, nextWin.getmaxyx()[1]-8, "000.000", curses.color_pair(1))
    nextWin.addstr(4, 2, "[C]AST:", curses.color_pair(1))
    nextWin.addstr(4, nextWin.getmaxyx()[1]-6, "00.00", curses.color_pair(1))
    nextWin.refresh()

    # Actually draws the text above to the positions specified.

    # Grabs a value from the keyboard without Enter having to be pressed (see cbreak above)
    stdscr.getch()
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
   print ("Got error(s) [" + caughtExceptions + "]")

if __name__ == "__main__":
  curses.wrapper(main)
