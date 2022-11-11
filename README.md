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

Setup works as follows:
1. Initialize the program counter to 0.
2. Read and increment the instruction pointer twice, reading to `keystroke_delay_high` and `keystroke_delay_low`.
3. Read and increment the instruction pointer twice, reading to `loop_count_high` and `loop_count_low`.
4. Compute `keystroke_delay` and `loop_count` from the bytes read in steps 1-3, e.g. `keystroke_delay = keystroke_delay_high << 8 | keystroke_delay_low`.

The Loop works as follows:
1. Read and increment instruction pointer as `command`.
2. If `command < 0xE9`, then it is a HID usage id. Send the key with the given usage id.
3. If `command == 0xFF`, then it is a delay. Read and increment instruction pointer twice, reading `delay_high`, then `delay_low`. Wait `delay_high << 8 | delay_low` milliseconds.
4. If `command == 0xFE`, then it is a key with a modifier. Read and increment instruction pointer as `modifiers`. Read and increment instruction pointer as `key`. Send the key with the given modifiers and key.
5. Decrement `loop_count`. If `loop_count != 0`, then go to step 1.
