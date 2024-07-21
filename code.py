import usb_hid
import time
import board
import busio
import storage
import usb_hid_map as usb

from adafruit_hid.keyboard import Keyboard


# 100Hz poll UART and Main Loop
timeout_sec = 0.01
max_buffer_size = 2048

# Initialize keyboard and serial
kbd = Keyboard(usb_hid.devices)
uart = busio.UART(tx=board.GP4, rx=board.GP5, timeout=timeout_sec, receiver_buffer_size=max_buffer_size)


def send(this_input):
    for item in this_input:
        if type(item) is list:
            kbd.send(*item)
        else:
            kbd.send(item)


def press(this_input):
    for item in this_input:
        kbd.press(item)
    kbd.release_all()


def consume(data):
    command = data[:1][0]
    this_input = data[1:]
    # debug keycodes: send(usb.get_sequence(r'\x' + r'\x'.join(f'{b:02x}' for b in a)))
    if 0x0 == command:
        # emergency reset button if boot.py gets messed up
        storage.erase_filesystem()
    elif 0x1 == command:
        send(usb.get_sequence(bytearray(this_input, 'ascii').decode()))
    elif 0x2 == command:
        press(usb.get_press(bytearray(this_input, 'ascii').decode()))
    elif 0x3 == command:
        if kbd.led_on(Keyboard.LED_CAPS_LOCK):
            uart.write(bytes(f"ONN", "ascii"))
        else:
            uart.write(bytes(f"OFF", "ascii"))
    else:
        send(usb.get_sequence('NO_COM'))


buf = bytearray(max_buffer_size)

while True:
    if uart.in_waiting > 0 and uart.readinto(buf) > 0:
        consume(buf)
        buf = bytearray(max_buffer_size)
    else:
        time.sleep(timeout_sec)
