import sys
import psutil
import wmi
import math
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import QThread, pyqtSignal

class Systeminfo_Thread(QThread):
    info_updated = pyqtSignal(str)  # 시스템 정보 업데이트 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        # WMI 인스턴스는 한 번만 생성합니다.
        self.getinfofromWMI = 1
        self.running = True

    def run(self):
        if self.getinfofromWMI == 1:
            self.wmi_instance = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            self.getinfofromWMI = 0

        while self.running:
            sensors = self.wmi_instance.Sensor()
            try:
                info = self.get_system_info(sensors)
                self.info_updated.emit(info)
            except Exception as e:
                print(f"Error in SystemInfoThread: {e}")
            QThread.msleep(1000)

    def stop(self):
        self.running = False

    def get_system_info(self, sensors):
        """Libre Hardware Monitor 데이터를 기반으로 시스템 정보를 가져옵니다."""
        try:
            cpu_usage = cpu_clock = cpu_temp = "N/A"
            ram_usage = ram_used = ram_total = "N/A"
            gpu_usage = gpu_mem_used = gpu_mem_total = gpu_clock = gpu_temp = "N/A"
            cpu_power = gpu_power = "N/A"

            for sensor in sensors:
                # 디버깅: 센서 정보 출력 (조건문이 제대로 동작하는지 확인)
                # print(f"Sensor: {sensor.Name}, Type: {sensor.SensorType}, Value: {sensor.Value}")
                if sensor.SensorType == "Load" and "CPU Total" == sensor.Name:
                    cpu_usage = round(sensor.Value, 1)
                if sensor.SensorType == "Clock" and "Core #1" == sensor.Name:
                    cpu_clock = round(sensor.Value)
                if sensor.SensorType == "Temperature" and "Core (Tctl/Tdie)" == sensor.Name:
                    cpu_temp = round(sensor.Value, 1)
                if sensor.SensorType == "Load" and "GPU Core" == sensor.Name:
                    gpu_usage = round(sensor.Value, 1)
                if sensor.SensorType == "Temperature" and "GPU Core" == sensor.Name:
                    gpu_temp = round(sensor.Value, 1)
                if sensor.SensorType == "Data" and "Memory Used" == sensor.Name:
                    ram_used = round(sensor.Value, 1)
                if sensor.SensorType == "Data" and "Memory Available" == sensor.Name:
                    ram_available = round(sensor.Value, 1)
                if sensor.SensorType == "SmallData" and "GPU Memory Used" == sensor.Name:
                    gpu_mem_used = round(sensor.Value / 1024, 1)
                if sensor.SensorType == "SmallData" and "GPU Memory Total" == sensor.Name:
                    gpu_mem_total = round(sensor.Value / 1024, 1)
                if sensor.SensorType == "Clock" and "GPU Core" == sensor.Name:
                    gpu_clock = round(sensor.Value)
                if sensor.SensorType == "Power" and "Package" == sensor.Name:
                    cpu_power = round(sensor.Value, 1)
                if sensor.SensorType == "Power" and "GPU Package" == sensor.Name:
                    gpu_power = round(sensor.Value, 1)

            ram_total = round(ram_used + ram_available, 1)

            if isinstance(ram_used, (int, float)) and isinstance(ram_total, (int, float)) and ram_total != 0:
                ram_usage = round((ram_used / ram_total) * 100, 1)
            else:
                ram_usage = "N/A"

            if isinstance(gpu_mem_used, (int, float)) and isinstance(gpu_mem_total, (int, float)) and gpu_mem_total != 0:
                gpu_mem_usage = round((gpu_mem_used / gpu_mem_total) * 100, 1)
            else:
                gpu_mem_usage = "N/A"

            if isinstance(cpu_power, (int, float)) and isinstance(gpu_power, (int, float)):
                total_power = round((cpu_power + gpu_power) * 1.2, 1)
            else:
                total_power = "N/A"

            # 네트워크 사용량 계산
            net_io = psutil.net_io_counters(pernic=False)
            if hasattr(self, 'last_net_sent') and hasattr(self, 'last_net_recv'):
                net_sent_speed = round((net_io.bytes_sent - self.last_net_sent) / (1024 ** 2), 1)
                net_recv_speed = round((net_io.bytes_recv - self.last_net_recv) / (1024 ** 2), 1)
            else:
                net_sent_speed = 0.0
                net_recv_speed = 0.0
            self.last_net_sent, self.last_net_recv = net_io.bytes_sent, net_io.bytes_recv

            return (f'CPU : {color_print(cpu_usage, "usage")} % | CPU Clock : {cpu_clock} MHz | CPU TEMP : {color_print(cpu_temp, "temp")}°C<br>'
                    f'GPU : {color_print(gpu_usage, "usage")}% | GPU Clock : {gpu_clock} MHz | GPU TEMP : {color_print(gpu_temp, "temp")}°C<br>'
                    f'RAM : {color_print(ram_usage, "mem")}% ({ram_used}GB / {ram_total}GB) | GPU Mem : {color_print(gpu_mem_usage, "mem")}% ({gpu_mem_used}GB / {gpu_mem_total}GB)<br>'
                    f'POWER : {color_print(total_power, "power")} W | Net : {net_sent_speed:.1f}MB/s ↑ {net_recv_speed:.1f}MB/s ↓')
        except Exception as ex:
            print(f"Error in get_system_info: {ex}")
            return "Error retrieving data from Libre Hardware Monitor"
        
class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()

        display_width = 900
        display_height = 135
        display_font = "Arial"
        display_font_size = 20
        display_background_rgba = "90, 90, 120, 200"
        display_hide_pos = 10

        self.show_height = display_hide_pos      # 보일 때의 위치
        self.hide_position = -display_height + display_hide_pos  # 숨길 때의 위치 (일부 보이게)

        # 창 스타일 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # UI 라벨 생성
        self.label = QLabel(self)
        self.label.setFont(QFont(display_font, display_font_size))
        self.label.setStyleSheet("font-size: " + str(display_font_size) +
                                 f"px; color: white; padding: 10px; border-radius: 15px; background-color: rgba({display_background_rgba});")
        self.label.setFixedWidth(display_width)
        self.label.setFixedHeight(display_height)
        self.label.setAlignment(Qt.AlignCenter)

        # 창 크기 및 위치 설정
        self.resize(display_width, display_height)
        self.move((QApplication.primaryScreen().geometry().width() - self.width()) // 2, self.hide_position)

        self.systeminfo_thread = Systeminfo_Thread()
        self.systeminfo_thread.info_updated.connect(self.update_info)
        self.systeminfo_thread.start()

        # 마우스 위치 확인 타이머
        self.mouse_timer = QTimer(self)
        self.mouse_timer.setInterval(16)
        self.mouse_timer.timeout.connect(self.check_mouse_position)
        self.mouse_timer.start()

    def check_mouse_position(self):
        """마우스 위치에 따라 창을 표시/숨깁니다."""
        cursor_pos = QCursor.pos()
        screen_rect = QApplication.primaryScreen().geometry()
        if (cursor_pos.y() <= self.y() + self.height() + 50) and (abs(cursor_pos.x() - screen_rect.width() // 2) <= self.width() // 2 + 50):
            self.move_window_smoothly(self.hide_position, self.show_height, self.y(), "down")
        else:
            self.move_window_smoothly(self.hide_position, self.show_height, self.y(), "up")

    def move_window_smoothly(self, up_y, down_y, current_y, mode):
        if mode == "up":
            self.target_y = up_y
            self.animation_progress = (down_y - current_y) / (down_y - up_y)
        elif mode == "down":
            self.target_y = down_y
            self.animation_progress = (current_y - up_y) / (down_y - up_y)
           
        if self.animation_progress >= 0.99:
            self.move((QApplication.primaryScreen().geometry().width() - self.width()) // 2, self.target_y)
            return
           
        eased_progress = 0.05 * (math.sin(self.animation_progress * math.pi) + 0.5)
        new_y = current_y + (self.target_y - current_y) * eased_progress

        if mode == "up":
            new_y = math.floor(new_y)
        elif mode == "down":
            new_y = math.ceil(new_y)
           
        self.move((QApplication.primaryScreen().geometry().width() - self.width()) // 2, round(new_y))

    def update_info(self, info_text):
        """정보를 UI에 업데이트합니다."""
        self.label.setText(info_text)

def color_print(value, type_str):
    """값에 따라 색상을 입힌 HTML 문자열 반환"""
    try:
        value = float(value)
        if (value < 40 and type_str == "usage") or (value < 50 and type_str == "mem") or (value < 50 and type_str == "temp") or (value < 100 and type_str == "power"):
            return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
        elif (value < 75 and type_str == "usage") or (value < 75 and type_str == "mem") or (value < 70 and type_str == "temp") or (value < 300 and type_str == "power"):
            return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
        else:
            return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
    except:
        return f"<span style='color:#FFFFFF'>{value}</span>"  # 에러 시 흰색 반환

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())
