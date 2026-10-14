"""Bài thực hành: chủ động tạo lỗi rồi đọc từng lỗi trong error queue."""
import time
import serial

PORT = "COM3"
BAUDRATE = 9600


def send(device, command):
    device.write((command + "\r").encode("ascii"))
    device.flush()
    if "?" not in command:
        print(">", command, "[đã gửi]")
        return None
    answer = device.read_until(b"\r").decode("ascii", errors="replace").strip()
    print(">", command, "\n<", answer or "(timeout)")
    return answer


with serial.Serial(PORT, BAUDRATE, timeout=1, write_timeout=1,
                   bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE, xonxoff=False,
                   rtscts=False, dsrdtr=False) as device:
    time.sleep(2)
    device.reset_input_buffer()

    send(device, "*CLS")
    send(device, "CONF:NOT_A_FUNCTION")       # Header không hỗ trợ
    send(device, "SENS:VOLT:DC:RANG")         # Thiếu tham số
    send(device, "SENS:VOLT:DC:NPLC abc")    # Sai kiểu dữ liệu
    send(device, "SENS:VOLT:DC:RANG 5")      # Giá trị ngoài tập range bài tập

    # Mỗi lần đọc lấy một lỗi cũ nhất ra khỏi hàng đợi.
    for _ in range(5):
        send(device, "SYST:ERR?")

    send(device, "*CLS")
    send(device, "SYST:ERR?")
