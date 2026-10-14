"""Gửi từng lệnh SCPI đến Keithley Model 2000."""
import argparse
import time
import serial


def send_command(connection, command):
    """Gửi một lệnh; chỉ đọc khi lệnh là truy vấn có dấu hỏi."""
    connection.write((command.strip() + "\r").encode("ascii"))
    connection.flush()
    if "?" not in command:
        print("Đã gửi (lệnh cấu hình thường không trả dữ liệu).")
        return None

    answer = connection.read_until(b"\r").decode("ascii", errors="replace").strip()
    if not answer:
        print("Hết thời gian chờ: thiết bị chưa gửi phản hồi.")
        return None
    print("Phản hồi:", answer)
    return answer


def main():
    parser = argparse.ArgumentParser(description="Terminal SCPI tối giản")
    parser.add_argument("--port", default="COM3", help="Ví dụ: COM3")
    parser.add_argument("--baud", type=int, default=9600)
    args = parser.parse_args()

    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            write_timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        ) as connection:
            # Arduino Uno có thể reset khi cổng COM vừa mở.
            time.sleep(2)
            connection.reset_input_buffer()
            print(f"Đã mở {args.port} ở {args.baud} baud. Gõ exit để thoát.")
            while True:
                command = input("SCPI> ").strip()
                if command.lower() in {"exit", "quit"}:
                    break
                if command:
                    send_command(connection, command)
    except serial.SerialException as error:
        print("Không mở được cổng serial:", error)
        print("Kiểm tra đúng COM, tốc độ baud và đóng Hercules/Arduino Serial Monitor.")


if __name__ == "__main__":
    main()
