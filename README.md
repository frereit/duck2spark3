## Usage

Download the desired layout.xml file from https://kbdlayout.info/. You will need the "XML for processing" file.
Install [arduino-cli](https://arduino.github.io/arduino-cli/0.28/). You probably want to install the entire Arduino IDE as well.
Install the digispark library as described in the [digispark library installation tutorial](https://digistump.com/wiki/digispark/tutorials/connecting).

Now, flash your duckscript using flash.py:
```bsh
$ python3 flash.py myscript.duck layout.xml
```
You will receive a lot of warnings about missing scancodes. This is to be expected and simply tells you that not all keys are supported, such as media keys.
When asked to plug in the digispark, do so. The script will be flashed to the device and the device will be reset.
Be careful, the script will be executed immediately after the device is reset.

## Troubleshooting

Good luck.

## ToDo

- [ ] Add support for missing DuckyScript commands
- [ ] Reduce size of Keyboard Library so that there is more space for the script

## Technical details

This is mostly just to remind myself how to do this, but I'll try to make it useful for others.

### How the arduino processes the program

Each instruction consists of at least two bytes.

Parsing works as follows:
1. Read and increment the instruction pointer twice, reading to `keystroke_delay_high` and `keystroke_delay_low`.
2. Read and increment the instruction pointer twice, reading to `loop_count_high` and `loop_count_low`.
3. Compute `keystroke_delay` and `loop_count` from the bytes read in steps 1-3, e.g. `keystroke_delay = keystroke_delay_high << 8 | keystroke_delay_low`.
4. Read and increment instruction pointer as `mod`.
5. Read and increment instruction pointer as `scancode`.
6. If `scancode` is non-zero, then send the keypress for `scancode` with modifiers `mod`. Continue to step 4.
7. Otherwise, if `mod` is non-zero, read and increment instruction pointer as `delay_low` and delay for `mod << 8 | delay_low` milliseconds. Continue to step 4.
8. Otherwise, if `loop_count` is non-zero, decrement `loop_count`, reset the instruction pointer to 4, and continue to step 4.