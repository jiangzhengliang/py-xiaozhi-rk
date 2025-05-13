import serial
import threading
from src.iot.thing import Thing
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SerialDevice:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.read_thread = None
        self.read_callback = None
        self._running = False

    def open(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self._running = True
            logger.info(f"[SerialDevice] 打开串口: {self.port} 成功")

            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
        except serial.SerialException as e:
            logger.error(f"[SerialDevice] 串口打开失败: {e}")
        except Exception as e:
            logger.error(f"[SerialDevice] 串口打开时出现未知错误: {e}")

    def _read_loop(self):
        while self._running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line and self.read_callback:
                    self.read_callback(line)
            except Exception as e:
                logger.error(f"[SerialDevice] 串口读取错误: {e}")

    def set_read_callback(self, callback):
        self.read_callback = callback

    def send(self, data: str):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data.encode('utf-8'))
                logger.info(f"[SerialDevice] 发送: {data.strip()}")
            except Exception as e:
                logger.error(f"[SerialDevice] 发送失败: {e}")
        else:
            logger.error("[SerialDevice] 串口未打开，无法发送数据")

    def close(self):
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info(f"[SerialDevice] 串口 {self.port} 已关闭")


class SerialPort(Thing):
    def __init__(self, serial_dev: SerialDevice = None):
        super().__init__("SerialPort", "串口通信")

        self.serial_dev = serial_dev if serial_dev else SerialDevice()

        # 尝试打开串口
        try:
            self.serial_dev.open()
        except Exception as e:
            logger.error(f"[SerialPort] 串口初始化失败: {e}")

        logger.info(f"[SerialPort] 串口初始化完成")

        # 定义控制方法
        self.add_method("ForwardMovement", "前进", [],
                        lambda params: self.serial_dev.send("w\n"))
        self.add_method("StopMovement", "停止", [],
                        lambda params: self.serial_dev.send("q\n"))
        self.add_method("BackwardMovement", "后退", [],
                        lambda params: self.serial_dev.send("s\n"))
        self.add_method("DriveLookLeft", "左转", [],
                        lambda params: self.serial_dev.send("a\n"))
        self.add_method("DriveLookRight", "右转", [],
                        lambda params: self.serial_dev.send("d\n"))
        self.add_method("Dance", "跳舞", [],
                        lambda params: self.serial_dev.send("M1\n"))
        self.add_method("stopDance", "停止跳舞", [],
                        lambda params: self.serial_dev.send("M0\n"))
