#include "DigiKeyboard.h"

#define PROGRAM_SIZE /*program_size*/
const PROGMEM uint8_t program[PROGRAM_SIZE] = {
    /*program_array*/
};

uint16_t keystroke_delay = 0;
uint16_t remaining_loops = 0;
uint16_t program_counter = 0;

uint8_t infinite_loop = 0;

uint8_t read(uint16_t offset) {
    return pgm_read_byte_near(program + offset);
}

void setup()
{
    keystroke_delay = read(program_counter++) << 8 | read(program_counter++);
    remaining_loops = read(program_counter++) << 8 | read(program_counter++);
    if (remaining_loops == 0)
    {
        infinite_loop = 1;
        remaining_loops = 1;
    }
    pinMode(0, OUTPUT); // LED on Model B
    pinMode(1, OUTPUT); // LED on Model A
    // We need to wait a bit before sending the program, otherwise the
    // host may not be ready to receive it.
    DigiKeyboard.sendKeyStroke(0);
    DigiKeyboard.delay(1000); 
}

void loop()
{
    if (remaining_loops > 0 || infinite_loop)
    {
        DigiKeyboard.sendKeyStroke(0);
        program_counter = 4; // first 4 bytes are delay and loop
        while (program_counter < PROGRAM_SIZE)
        {
            digitalWrite(0, HIGH);
            digitalWrite(1, HIGH);
            uint8_t mod = read(program_counter++);
            uint8_t scancode = read(program_counter++);
            if (scancode != 0)
            {
                DigiKeyboard.sendKeyStroke(scancode, mod);
            }
            else if (mod != 0)
            {
                uint16_t delay = mod | read(program_counter++);
                DigiKeyboard.delay(delay);
            }
            else
            {
                break;
            }            
            digitalWrite(0, LOW);
            digitalWrite(1, LOW);
            DigiKeyboard.delay(keystroke_delay);
        }
        remaining_loops -= !infinite_loop;
    }
}