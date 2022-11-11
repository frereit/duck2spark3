import logging
from xml.etree import ElementTree as ET


class Text2HIDConverter:
    # According to https://www.usb.org/sites/default/files/hid1_11.pdf, p. 66
    VK_TO_MOD = {
        "VK_LCONTROL": 1 << 0,
        "VK_LSHIFT": 1 << 1,
        "VK_LMENU": 1 << 2,
        "VK_LWIN": 1 << 3,
        "VK_RCONTROL": 1 << 4,
        "VK_RSHIFT": 1 << 5,
        "VK_RMENU": 1 << 6,
        "VK_RWIN": 1 << 7,
    }

    STATE_TO_VK = {
        "VK_SHIFT": "VK_LSHIFT",
        "VK_CONTROL": "VK_LCONTROL",
        "VK_MENU": "VK_LMENU",
    }

    # https://download.microsoft.com/download/1/6/1/161ba512-40e2-4cc9-843a-923143f3456c/translate.pdf
    PS2_TO_HID = {255: 1, 252: 2, 30: 4, 48: 5, 46: 6, 32: 7, 18: 8, 33: 9, 34: 10, 35: 11, 23: 12, 36: 13, 37: 14, 38: 15, 50: 16, 49: 17, 24: 18, 25: 19, 16: 20, 19: 21, 31: 22, 20: 23, 22: 24, 47: 25, 17: 26, 45: 27, 21: 28, 44: 29, 2: 30, 3: 31, 4: 32, 5: 33, 6: 34, 7: 35, 8: 36, 9: 37, 10: 38, 11: 39, 28: 40, 1: 41, 14: 42, 15: 43, 57: 44, 12: 45, 13: 46, 26: 47, 27: 48, 43: 50, 39: 51, 40: 52, 41: 53, 51: 54, 52: 55, 53: 56,
                  58: 57, 59: 58, 60: 59, 61: 60, 62: 61, 63: 62, 64: 63, 65: 64, 66: 65, 67: 66, 68: 67, 87: 68, 88: 69, 70: 71, 69: 83, 55: 85, 74: 86, 78: 87, 79: 89, 80: 90, 81: 91, 75: 92, 76: 93, 77: 94, 71: 95, 72: 96, 73: 97, 82: 98, 83: 99, 86: 100, 89: 103, 93: 104, 94: 105, 95: 106, 126: 133, 115: 135, 112: 136, 125: 137, 121: 138, 123: 139, 92: 140, 242: 144, 241: 145, 120: 146, 119: 147, 118: 148, 29: 224, 42: 225, 56: 226, 54: 229}

    def __init__(self, xml_for_processing: str):
        """
        :param layout: keyboard layout to use, as a XML string. Download from https://kbdlayout.info/ (XML for processing)
        """
        self.layout, self.scancodes = Text2HIDConverter._parse_layout(
            xml_for_processing)

    @staticmethod
    def _parse_layout(xml_for_processing: str) -> tuple:
        text_to_hid_bytes = {}
        vk_to_sc = {}
        root = ET.fromstring(xml_for_processing)
        dead_keys = {}

        def with_string_to_mod(with_str):
            mod = 0
            if with_str:
                for vk in with_str.split():
                    if vk in Text2HIDConverter.STATE_TO_VK:
                        mod |= Text2HIDConverter.VK_TO_MOD[Text2HIDConverter.STATE_TO_VK[vk]]
                    else:
                        logging.warn("Unsupported modifier key %s", vk)
                        return -1
            return mod
        # First pass: Get the VK to SC mapping and the text to HID bytes mapping
        for physical_key in root.find("PhysicalKeys"):
            vk = physical_key.attrib['VK']
            sc = int(physical_key.attrib['SC'], 16)
            if sc > 255:
                logging.warn(
                    "Skipping scancode %x for virtual key %s", sc, vk)
                continue
            vk_to_sc[vk] = sc
            for result in physical_key:
                # if result has no child nodes
                if not result:
                    hid_sequence = b""
                    mod = with_string_to_mod(result.attrib.get("With"))
                    if mod < 0:
                        continue
                    scancode = vk_to_sc[physical_key.attrib["VK"]]
                    if scancode not in Text2HIDConverter.PS2_TO_HID:
                        logging.warn(
                            "Skipping scancode %x for virtual key %s, no HID Usage ID found.", vk_to_sc[vk], vk)
                        continue
                    hid = Text2HIDConverter.PS2_TO_HID[scancode]
                    hid_sequence += bytes([mod, hid])
                    if result.attrib.get("Text"):
                        text = result.attrib["Text"]
                    elif result.attrib.get("TextCodepoints"):
                        text = chr(int(result.attrib["TextCodepoints"], 16))
                    else:
                        print("No text for", result.attrib)
                    if text not in text_to_hid_bytes:
                        text_to_hid_bytes[text] = hid_sequence
                else:
                    dead_keys[vk] = dead_keys.get(vk, []) + [result]
        # Second pass: Get the text to HID bytes mapping for the dead keys
        for vk, results in dead_keys.items():
            for result in results:
                mod = with_string_to_mod(result.attrib.get("With"))
                if mod < 0:
                    continue
                for dead_key_result in result.find("DeadKeyTable"):
                    if vk_to_sc[vk] not in Text2HIDConverter.PS2_TO_HID:
                        logging.warn(
                            "Skipping scancode %x for virtual key %s, no HID Usage ID found.", vk_to_sc[vk], vk)
                        continue
                    hid = Text2HIDConverter.PS2_TO_HID[vk_to_sc[vk]]
                    hid_sequence = bytes(
                        [mod, hid]) + text_to_hid_bytes[dead_key_result.attrib["With"]]
                    if dead_key_result.attrib.get("Text"):
                        text = dead_key_result.attrib["Text"]
                    elif dead_key_result.attrib.get("TextCodepoints"):
                        text = chr(
                            int(dead_key_result.attrib["TextCodepoints"], 16))
                    else:
                        logging.warn("No text for", dead_key_result.attrib)
                        continue
                    if text not in text_to_hid_bytes:
                        text_to_hid_bytes[text] = hid_sequence
        return (text_to_hid_bytes, vk_to_sc)

    def convert(self, text: str) -> bytes:
        """
        Convert a string to a sequence of HID bytes

        Each keystroke is represented by 16 bytes: 
        8 bytes for the modifier keys and 8 bytes for the scancode.
        :param text: text to convert to HID bytes
        :return: bytes
        """
        result = b""
        curr_text = ""
        for char in text:
            if char in self.layout:
                result += self.layout[char]
                curr_text = ""
            else:
                curr_text += char
        if curr_text:
            logging.error("Could not convert text", curr_text)
            return b""
        return result
