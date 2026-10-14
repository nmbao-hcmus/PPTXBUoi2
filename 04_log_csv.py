"""Đo lặp và lưu kết quả vào CSV bằng pyserial."""
import csv
import time
from datetime import datetime
import serial

PORT = "COM3"         # Đổi theo Device Manager
BAUDRATE = 9600
SO_LAN_DO = 10
KHOANG_CACH_GIAY = 1.0
TEN_FILE = "ket_qua_do.csv"


def query(connection, command):
    connection.write((command + "\r").encode("ascii"))
    connection.flush()
    return connection.read_until(b"\r").decode("ascii", errors="replace").strip()


with serial.Serial(PORT, BAUDRATE, timeout=1, write_timeout=1,
                   xonxoff=False, rtscts=False) as device:
    time.sleep(2)
    device.reset_input_buffer()
    device.write(b"CONF:VOLT:DC\r")
    device.flush()
    time.sleep(0.1)

    with open(TEN_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["thoi_gian", "chuc_nang", "gia_tri"])
        for index in range(SO_LAN_DO):
            value = query(device, "READ?")
            timestamp = datetime.now().isoformat(timespec="seconds")
            writer.writerow([timestamp, "VOLT:DC", value])
            file.flush()
            print(index + 1, timestamp, value)
            time.sleep(KHOANG_CACH_GIAY)

print(f"Đã lưu {SO_LAN_DO} lần đo vào {TEN_FILE}")
