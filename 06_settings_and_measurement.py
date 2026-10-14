"""Ví dụ theo trình tự: cài đặt → đọc lại cài đặt → đo → hỏi lỗi."""
import time
import serial

PORT = "COM3"       # Đổi theo máy
BAUDRATE = 9600      # Thông số học phần


def send_command(device, command):
    device.write((command.strip() + "\r").encode("ascii"))
    device.flush()
    if "?" not in command:
        print(f"> {command}  [đã gửi lệnh cài đặt]")
        return None
    reply = device.read_until(b"\r").decode("ascii", errors="replace").strip()
    print(f"> {command}\n< {reply or '(timeout)'}")
    return reply


with serial.Serial(PORT, BAUDRATE, timeout=1, write_timeout=1,
                   bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE, xonxoff=False,
                   rtscts=False, dsrdtr=False) as device:
    time.sleep(2)  # Chờ Uno khởi động sau khi mở COM.
    device.reset_input_buffer()

    send_command(device, "*IDN?")
    send_command(device, "*RST")
    send_command(device, "CONF:VOLT:DC")
    send_command(device, "CONF?")
    send_command(device, "SENS:FUNC?")

    # Thử range cố định, rồi bật lại autorange.
    send_command(device, "SENS:VOLT:DC:RANG 1")
    send_command(device, "SENS:VOLT:DC:RANG?")
    send_command(device, "SENS:VOLT:DC:RANG:AUTO?")
    send_command(device, "SENS:VOLT:DC:RANG:AUTO ON")
    send_command(device, "SENS:VOLT:DC:RANG:AUTO?")

    send_command(device, "SENS:VOLT:DC:NPLC 2")
    send_command(device, "SENS:VOLT:DC:NPLC?")
    send_command(device, "READ?")
    send_command(device, "FETC?")
    send_command(device, "SYST:ERR?")
