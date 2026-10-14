"""Ghi phép đo trong một khoảng thời gian; Ctrl+C để dừng sớm."""
import csv
import time
from datetime import datetime
import serial

PORT = "COM3"
BAUDRATE = 9600
DURATION_SECONDS = 30
INTERVAL_SECONDS = 1.0
OUTPUT_FILE = "du_lieu_theo_thoi_gian.csv"


def read_measurement(device):
    device.write(b"READ?\r")
    device.flush()
    return device.read_until(b"\r").decode("ascii", errors="replace").strip()


with serial.Serial(PORT, BAUDRATE, timeout=1, write_timeout=1,
                   bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE, xonxoff=False,
                   rtscts=False, dsrdtr=False) as device:
    time.sleep(2)
    device.reset_input_buffer()
    device.write(b"CONF:VOLT:DC\r")
    device.flush()
    time.sleep(0.1)

    start = time.monotonic()
    next_sample = start
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as output:
        writer = csv.writer(output)
        writer.writerow(["timestamp", "elapsed_seconds", "command", "value"])
        try:
            while time.monotonic() - start < DURATION_SECONDS:
                value = read_measurement(device)
                elapsed = round(time.monotonic() - start, 2)
                timestamp = datetime.now().isoformat(timespec="milliseconds")
                writer.writerow([timestamp, elapsed, "READ?", value])
                output.flush()
                print(elapsed, value if value else "TIMEOUT")
                next_sample += INTERVAL_SECONDS
                time.sleep(max(0, next_sample - time.monotonic()))
        except KeyboardInterrupt:
            print("Đã dừng theo yêu cầu.")

print("Đã lưu dữ liệu vào", OUTPUT_FILE)
