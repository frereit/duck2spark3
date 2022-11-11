import argparse
import os
import sys
import tempfile

import duckscript


def two_byte_type(x):
    x = int(x)
    if x < 0 or x > 0xffff:
        raise argparse.ArgumentTypeError("must be between 0 and 65535")
    return x


def compile_and_upload(program):
    with open("rubberducky.tmpl.ino", "r") as f:
        template = f.read()
    template = template.replace("/*program_size*/", str(len(program))).replace(
        "/*program_array*/", ", ".join(["0x{:02x}".format(x) for x in program]))
    # write to temp directory
    with tempfile.TemporaryDirectory() as tempdir:
        with open(os.path.join(tempdir, os.path.basename(tempdir) + ".ino"), "w") as f:
            f.write(template)
        os.system(
            "arduino-cli compile --upload --verify --fqbn digistump:avr:digispark-tiny {}".format(tempdir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input', type=argparse.FileType(
        'r', encoding="utf-8"), help="Input Ducky Script")
    parser.add_argument('layout_file', type=argparse.FileType('r', encoding="utf-8"),
                        help="Keyboard layout file, downloaded from https://kbdlayout.info/ (XML for processing)")
    # int arguments between 0 and 65535
    parser.add_argument("--keystroke-delay", type=two_byte_type,
                        default=300, help="Delay between keystrokes in milliseconds")
    parser.add_argument("--loop", type=two_byte_type, default=1,
                        help="Number of times to loop the script. 0 means infinite loop")
    args = parser.parse_args()
    converter = duckscript.DuckyScript2HIDConverter(args.layout_file.read())
    program = converter.convert(args.input.read())

    program = bytes([args.keystroke_delay >> 8, args.keystroke_delay & 0xff,
                     args.loop >> 8, args.loop & 0xff]) + program
    if len(program) > 3096:
        print("Program may be too large to fit on the ATTiny85.")
        if input("Try anyway? (y/n)") != "y":
            sys.exit(1)
    with open("test.bin", "wb") as f:
        f.write(program)
    compile_and_upload(program)
