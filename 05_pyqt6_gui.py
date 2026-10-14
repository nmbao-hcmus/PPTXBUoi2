"""GUI PyQt6 tối giản: chọn COM, kết nối, gửi lệnh và xem phản hồi."""
import sys
import time
import serial
from serial.tools import list_ports
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QComboBox,
    QLineEdit, QPlainTextEdit, QHBoxLayout, QVBoxLayout,
)


class SerialWorker(QObject):
    connected = pyqtSignal(str)
    disconnected = pyqtSignal()
    response_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.device = None

    @pyqtSlot(str, int)
    def open_port(self, port, baudrate):
        try:
            if self.device and self.device.is_open:
                self.device.close()
            self.device = serial.Serial(
                port=port, baudrate=baudrate,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=1, write_timeout=1,
                xonxoff=False, rtscts=False, dsrdtr=False,
            )
            time.sleep(2)  # Uno thường reset khi mở cổng USB-serial.
            self.device.reset_input_buffer()
            self.connected.emit(f"Đã kết nối {port} / {baudrate} baud")
        except (serial.SerialException, OSError) as exc:
            self.device = None
            self.error.emit(f"Không mở được cổng: {exc}")

    @pyqtSlot(str)
    def send_command(self, command):
        if not self.device or not self.device.is_open:
            self.error.emit("Chưa kết nối cổng serial.")
            return
        try:
            self.device.write((command.strip() + "\r").encode("ascii"))
            self.device.flush()
            if "?" in command:
                answer = self.device.read_until(b"\r").decode(
                    "ascii", errors="replace"
                ).strip()
                if answer:
                    self.response_ready.emit(f"> {command}\n< {answer}")
                else:
                    self.response_ready.emit(f"> {command}\n< (hết thời gian chờ)")
            else:
                self.response_ready.emit(
                    f"> {command}\n(đã gửi; lệnh cấu hình không trả dữ liệu)"
                )
        except (serial.SerialException, OSError, UnicodeEncodeError) as exc:
            self.error.emit(f"Lỗi truyền thông: {exc}")

    @pyqtSlot()
    def close_port(self):
        if self.device and self.device.is_open:
            self.device.close()
        self.device = None
        self.disconnected.emit()


class MainWindow(QWidget):
    request_open = pyqtSignal(str, int)
    request_send = pyqtSignal(str)
    request_close = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thực hành SCPI - Keithley Model 2000")
        self.resize(720, 520)

        self.port_box = QComboBox()
        self.baud_box = QComboBox()
        self.baud_box.addItems(["9600"])
        self.baud_box.setCurrentText("9600")
        self.refresh_button = QPushButton("Quét COM")
        self.connect_button = QPushButton("Kết nối")
        self.disconnect_button = QPushButton("Ngắt kết nối")
        self.disconnect_button.setEnabled(False)

        top = QHBoxLayout()
        top.addWidget(QLabel("Cổng:"))
        top.addWidget(self.port_box)
        top.addWidget(self.refresh_button)
        top.addWidget(QLabel("Baud:"))
        top.addWidget(self.baud_box)
        top.addWidget(self.connect_button)
        top.addWidget(self.disconnect_button)

        self.command_box = QLineEdit()
        self.command_box.setPlaceholderText("Ví dụ: *IDN? hoặc READ?")
        self.send_button = QPushButton("Gửi lệnh")
        command_row = QHBoxLayout()
        command_row.addWidget(self.command_box)
        command_row.addWidget(self.send_button)

        quick_row = QHBoxLayout()
        for title, command in [
            ("Nhận dạng", "*IDN?"),
            ("Cấu hình DCV", "CONF:VOLT:DC"),
            ("Đọc READ?", "READ?"),
            ("Đo DCV", "MEAS:VOLT:DC?"),
            ("Hàng đợi lỗi", "SYST:ERR?"),
        ]:
            button = QPushButton(title)
            button.clicked.connect(lambda checked=False, cmd=command: self.send(cmd))
            quick_row.addWidget(button)

        self.status = QLabel("Chưa kết nối")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(command_row)
        layout.addLayout(quick_row)
        layout.addWidget(self.status)
        layout.addWidget(self.log)

        self.thread = QThread(self)
        self.worker = SerialWorker()
        self.worker.moveToThread(self.thread)
        self.thread.start()
        self.request_open.connect(self.worker.open_port)
        self.request_send.connect(self.worker.send_command)
        self.request_close.connect(self.worker.close_port)
        self.worker.connected.connect(self.on_connected)
        self.worker.disconnected.connect(self.on_disconnected)
        self.worker.response_ready.connect(self.log.appendPlainText)
        self.worker.error.connect(self.show_error)

        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button.clicked.connect(self.request_close.emit)
        self.send_button.clicked.connect(self.send_from_box)
        self.command_box.returnPressed.connect(self.send_from_box)
        self.refresh_ports()

    def refresh_ports(self):
        current = self.port_box.currentText()
        self.port_box.clear()
        for port in list_ports.comports():
            self.port_box.addItem(port.device, port.description)
        old_index = self.port_box.findText(current)
        if old_index >= 0:
            self.port_box.setCurrentIndex(old_index)
        if self.port_box.count() == 0:
            self.port_box.addItem("Không có COM")

    def connect_device(self):
        port = self.port_box.currentText()
        if not port or port == "Không có COM":
            self.show_error("Chưa chọn được cổng COM.")
            return
        self.request_open.emit(port, int(self.baud_box.currentText()))

    def send(self, command):
        self.request_send.emit(command)

    def send_from_box(self):
        command = self.command_box.text().strip()
        if command:
            self.send(command)
            self.command_box.clear()

    def on_connected(self, message):
        self.status.setText(message)
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.log.appendPlainText(message)

    def on_disconnected(self):
        self.status.setText("Đã ngắt kết nối")
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

    def show_error(self, message):
        self.status.setText(message)
        self.log.appendPlainText("LỖI: " + message)

    def closeEvent(self, event):
        self.request_close.emit()
        self.thread.quit()
        self.thread.wait(1500)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
