import argparse

import keyboard


class DuckyScript2HIDConverter:
    def __init__(self, layout: str):
        """
        :param layout: keyboard layout to use, as a XML string. Download from https://kbdlayout.info/ (XML for processing)
        """
        self.textconverter = keyboard.Text2HIDConverter(layout)
        # This list needs to be expanded as necessary
        self.aliases = {
            "VK_ALT": "VK_LMENU",
            "VK_WINDOWS": "VK_LWIN",
            "VK_OPTION": "VK_LMENU",
            "VK_COMMAND": "VK_LWIN",
            "VK_ESC": "VK_ESCAPE",
            "VK_BACKSPACE": "VK_BACK",
        }

    def convert(self, script: str) -> bytes:
        """
        Implementation of some commands from https://github.com/dekuNukem/duckyPad/blob/master/duckyscript_info.md.
        Note that most commands are not implemented because they would increase the binary size or require a lot of
        additional code.
        :param script: ducky script to convert
        :return: HID bytes

        :raises ValueError: if the script contains syntax errors
        :raises NotImplementedError: if the script contains unsupported commands
        """

        instructions_as_bytes = []
        for line in script.splitlines():
            if line.startswith("REM"):
                continue
            elif line.startswith("DEFAULTDELAY"):
                # To implement this, if the scancode is zero,
                # the script would need to read the mod byte as a command
                # and interpret any following bytes as arguments
                # so that more than one (DELAY) metacommand can be implemented.
                # This will be referred to as "DuckAsm" in the following comments.
                raise NotImplementedError("DEFAULTDELAY is not implemented")
            elif line.startswith("DEFAULTCHARDELAY"):
                # To implement this, DuckAsm would need to be implemented.
                raise NotImplementedError(
                    "DEFAULTCHARDELAY is not implemented")
            elif line.startswith("DELAY"):
                if len(line.split()) != 2:
                    raise ValueError("DELAY requires one argument")
                try:
                    delay = int(line.split()[1])
                except ValueError:
                    raise ValueError("DELAY argument must be an integer")
                if delay < 0 or delay > 0xffff:
                    raise ValueError(
                        "DELAY argument must be between 0 and 65535")
                instructions_as_bytes.append(
                    bytes([delay >> 8, 0x00, delay & 0xff]))
            elif line.startswith("STRING"):
                if len(line.split(" ", maxsplit=1)) != 2:
                    raise ValueError("STRING requires an argument")
                text = line.split(" ", maxsplit=1)[1]
                instructions_as_bytes.append(self.textconverter.convert(text))
            elif line.startswith("STRINGLN"):
                if len(line.split(" ", maxsplit=1)) != 2:
                    raise ValueError("STRINGLN requires an argument")
                text = line.split(" ", maxsplit=1)[1]
                instructions_as_bytes.append(
                    self.textconverter.convert(text + b"\n"))
            elif line.startswith("REPEAT"):
                try:
                    repeat = int(line.split(" ", 1)[1])
                except ValueError:
                    raise ValueError(
                        "Invalid argument for REPEAT: {}".format(line))
                if len(instructions_as_bytes) == 0:
                    raise ValueError("REPEAT without any instructions")
                instructions_as_bytes += instructions_as_bytes[-1] * repeat
            else:
                # Treating as a key combination
                keys = ["VK_" + key for key in line.split()]
                non_mod_keys = []
                mod = 0
                for key in keys:
                    key = self.aliases.get(key, key)
                    if key in self.textconverter.VK_TO_MOD or key in self.textconverter.STATE_TO_VK:
                        if key in self.textconverter.VK_TO_MOD:
                            mod |= self.textconverter.VK_TO_MOD[key]
                        else:
                            mod |= self.textconverter.VK_TO_MOD[self.textconverter.STATE_TO_VK[key]]
                    else:
                        non_mod_keys.append(key)
                if len(non_mod_keys) == 0:
                    raise ValueError("No non-modifier keys in key combination")
                if len(non_mod_keys) > 1:
                    raise NotImplementedError(
                        "Multiple non-modifier keys in a combination are not implemented: %s", non_mod_keys)
                scancode = self.textconverter.scancodes[non_mod_keys[0]]
                if scancode not in keyboard.Text2HIDConverter.PS2_TO_HID:
                    raise NotImplementedError(
                        "Key %s is not implemented" % non_mod_keys[0])
                instructions_as_bytes.append(
                    bytes([mod, keyboard.Text2HIDConverter.PS2_TO_HID[scancode]]))
        return b"".join(instructions_as_bytes)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input', type=argparse.FileType(
        'r'), help="Input Ducky Script")
    parser.add_argument('output', type=argparse.FileType('wb'),
                        help="Binary output file for encoded script")
    parser.add_argument('layout_file', type=argparse.FileType('r', encoding="utf-8"),
                        help="Keyboard layout file, downloaded from https://kbdlayout.info/ (XML for processing)")
    args = parser.parse_args()
    converter = DuckyScript2HIDConverter(args.layout_file.read())
    args.output.write(converter.convert(args.input.read()))


if __name__ == '__main__':
    main()
