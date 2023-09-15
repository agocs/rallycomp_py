# RallyComp_Py

## A Python Rally Computer

### Basic Layout

```
          Time

          Pace

Odometer        Speedometer

Current          Next
Instruction      Instruction

Command          Error

```

#### Time

Shows the latest GPS fix time rounded to a thousandth of a second. 
Usually your GPS receiver will only provide time in whole seconds or 1/10th of a second.

#### Pace

Indicates whether you are early or late.
The cursor will move between -10 and +10 seconds.
The window will be green if you are + or - 1 second of where you should be, yellow if you need to speed up, and red if you need to slow down.

#### Odometer

Displays the distance accumulated by your odometer. Press `o` to enter odometer commands.

- `o p [enter]`: puts your odometer in Park mode. The odometer will not accumulate more distance while parked.
- `o d [enter]`: puts your odometer in Drive mode. Odometer will accumulate distance while in drive.
- `o r [enter]`: puts your odometer in Reverse mode. Odometer will decumulate distance while in reverse.
- `o z [enter]`: Zeros your odometer.
- `o c [enter]`: puts you in Odometer Calibration mode. Enter the distance your odometer _should_ read, and it will calculate the calibration factor for you.

#### Speedometer

Displays the current speed as indicated by the GPS receiver.

#### Current Instruction

The current instruction. Indicates the time and distance remaining in the instruction, as well as the CAST and your pace.

#### Next Instruction

Allows you to enter the absolute time, absolute distance, and CAST for your next instruction.

- `t` allows you to enter the absolute time of the next instruction. Enter time in `hh:mm:ss` format, then press `[enter]`
- `d` allows you to enter the absolute distance of the next instruction. Enter it in `dd.dddd` format, then press `[enter]`.
- `c` allows you to enter the cast of the next instruction. Enter it in `dd.dddd` format, then press `[enter]`.  
- `p` allows you to enter a PAUSE instruction. Automatically sets CAST 0, distance 0, and time the indicated number of seconds after the end of the current instruction.

Press `[space]` to turn the next instruction into the current instruction.

### Odometer Check

The odometer check is an untimed transit of known distance that allows you to compare your odometer against the rallymaster's.
When you start the program, the odometer will be zeroed and in Park mode.
Drive up to the start line, then press `o d [enter]` to put the odometer in Drive mode.
Drive the length of the transit.
As you cross the finish line, press `o p [enter]` to Park the odometer again.

The odometer will display _approximately_ the distance indicated by the rallymaster.
To calibrate it, press `o c [enter]` to enter Calibration mode.
Then enter the correct distance and press `[enter]` again. The odometer will be calibrated. 
The calibration will be saved in `conf.yaml`.

### Driving a transit

- Reset the program.
- As you cross the start line, press `o d [enter]`.
- Drive the transit.

### Driving a regularity

- Reset the program.
- Enter the `c`AST and `d`istance of the first route instruction.
- Drive up to the start line. Cross the start line at your start time.
- As you cross the start line, press `[space]`.

Your odometer will automatically be put in Drive mode when you activate the first instruction.

The next instruction assumes it has the same CAST as the current instruction.
If this is the case, there is no need to re-enter the CAST. 
If you need to enter a new CAST, press `c`, enter the CAST in the command window, then press `[enter]`.

If you know the distance to the next route instruction, enter `d`, enter the _absolute_ distance, then press `[enter]`.

Absolute distance is the distance from the beginning of the regularity. I haven't implemented incremental distance yet.

#### PAUSE instructions

- Press `p` to enter a PAUSE. 
- Enter the number of seconds to pause. For example, if you see a PAUSE 10, enter `10` and then press `[enter]`.

The next instruction will get a distance of 0, and speed of 0, 
and an absolute time equal to the absolute time of the current instruction's absolute time + the indicated number of seconds.

Press `[space]` as you reach the stop sign or whatever (or, whenever your current instruction's time remaining reaches zero),
and then enter your next instruction while the driver is pausing.
