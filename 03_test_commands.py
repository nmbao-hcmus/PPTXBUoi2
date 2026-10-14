"""Chạy một chuỗi kiểm tra cài đặt, đo và hàng đợi lỗi."""
import time
import serial

PORT = "COM3"       # Đổi thành cổng Arduino trên máy
BAUDRATE = 9600


def send(connection, command):
    print(f"\n> {command}")
    connection.write((command + "\r").encode("ascii"))
    connection.flush()
    if "?" in command:
        answer = connection.read_until(b"\r").decode("ascii", errors="replace").strip()
        print("<", answer if answer else "(không có phản hồi)")
        return answer
    print("(lệnh cấu hình; không chờ phản hồi)")
    return None


with serial.Serial(PORT, BAUDRATE, timeout=1, write_timeout=1,
                   xonxoff=False, rtscts=False) as device:
    time.sleep(2)
    device.reset_input_buffer()

    send(device, "*IDN?")
    send(device, "*RST")
    send(device, "CONF:VOLT:DC")
    send(device, "CONF?")
    send(device, "SENS:FUNC?")
    send(device, "SENS:VOLT:DC:RANG?")
    send(device, "SENS:VOLT:DC:RANG 1")
    send(device, "SENS:VOLT:DC:RANG?")
    send(device, "SENS:VOLT:DC:RANG:AUTO?")
    send(device, "SENS:VOLT:DC:NPLC 2")
    send(device, "SENS:VOLT:DC:NPLC?")
    send(device, "READ?")
    send(device, "FETC?")
    send(device, "SYST:ERR?")

    # Cố ý gửi giá trị không hợp lệ để kiểm tra error queue.
    send(device, "SENS:VOLT:DC:RANG 5")
    send(device, "SYST:ERR?")
    send(device, "*CLS")
    send(device, "SYST:ERR?")
