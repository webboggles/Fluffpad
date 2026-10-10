"""Shared emulator state. Imported by the hardware mocks and by run_emu."""

# Raised by the runner's update hook. BaseException so `except Exception` in a
# game loop does not swallow the stop.
class EmuStop(BaseException):
    pass


virtual_us = 0
buttons = set()
led = (0, 0, 0)
tone_log = []  # (virtual_time_us, pin_id, freq_hz, duty_u16)
frames = 0
frame_us = 23000
cpu_hz = 150_000_000
backlight = 1.0
on_frame = None


def reset():
    global virtual_us, led, frames, frame_us, cpu_hz, backlight, on_frame
    virtual_us = 0
    buttons.clear()
    led = (0, 0, 0)
    tone_log.clear()
    frames = 0
    frame_us = 23000
    cpu_hz = 150_000_000
    backlight = 1.0
    on_frame = None


def log_tone(pin_id, freq, duty):
    tone_log.append((virtual_us, pin_id, int(freq), int(duty)))
