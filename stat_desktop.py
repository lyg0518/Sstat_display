import sys
import math
import clr
import pythoncom
import keyboard
import time
import os, ctypes
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import QThread, pyqtSignal

pythoncom.CoInitialize()
        
class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()

        display_width = 900
        display_height = 180
        display_font = "Arial"
        display_font_size = 20
        display_background_rgba = "90, 90, 120, 200"
        display_hide_pos = 10

        self.show_height = display_hide_pos      # 보일 때의 위치
        self.hide_position = -display_height + display_hide_pos  # 숨길 때의 위치 (일부 보이게)
        self.always_show = False    # 상시로 창 표시 (기본값 False)

        # 스레드 초기화를 한 번만 수행
        self.systeminfo_thread = Systeminfo_Thread(self)  # self를 parent로 전달
        self.systeminfo_thread.daemon = True
        self.systeminfo_thread.info_updated.connect(self.update_info)
        self.systeminfo_thread.start()

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

        # 마우스 위치 확인 타이머
        self.mouse_timer = QTimer(self)
        self.mouse_timer.setInterval(16)
        self.mouse_timer.timeout.connect(self.check_mouse_position)
        self.mouse_timer.start()

        self.last_toggle_time = time.time()

        # 키보드 단축키 등록
        keyboard.add_hotkey('shift+q', self.close_application)
        keyboard.add_hotkey('shift+1', self.toggle_display_mode)

        app.aboutToQuit.connect(self.cleanup)

    def close_application(self):
        """프로그램 종료 함수"""
        print("단축키로 프로그램을 종료합니다...")
        self.cleanup()  # 리소스 정리
        app.quit()      # 애플리케이션 종료

    def cleanup(self):
        """프로그램 종료 시 실행되는 정리 함수"""
        print("프로그램 종료 중...")
        if self.systeminfo_thread:
            self.systeminfo_thread.stop()
            self.systeminfo_thread.wait()  # 스레드가 완전히 종료될 때까지 대기
        if self.mouse_timer:
            self.mouse_timer.stop()
        print("프로그램이 안전하게 종료되었습니다.")

    def toggle_display_mode(self):
        self.toggle_display_time = time.time()
        if(self.toggle_display_time - self.last_toggle_time > 0.1):
            self.last_toggle_time = self.toggle_display_time
            if self.always_show == True:
                self.always_show = False
            else:
                self.always_show = True

    def check_mouse_position(self):
        """마우스 위치에 따라 창을 표시/숨깁니다."""
        cursor_pos = QCursor.pos()
        screen_rect = QApplication.primaryScreen().geometry()
        if ((cursor_pos.y() <= self.y() + self.height() + 30) and (abs(cursor_pos.x() - screen_rect.width() // 2) <= self.width() // 2 + 30) or self.always_show == True):
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

class Systeminfo_Thread(QThread):
    info_updated = pyqtSignal(str)  # 시스템 정보 업데이트 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.isInit = 1
        self.running = True

    def run(self):
        if self.isInit == 1:
            try:
                clr.AddReference("LibreHardwareMonitorLib") 
                from LibreHardwareMonitor import Hardware # Libre Hardware Monitor 모듈 가져오기
                computer = Hardware.Computer() # Libre Hardware Monitor 초기화
                computer.IsCpuEnabled = True  # CPU 모니터링 활성화
                computer.IsGpuEnabled = True  # GPU 모니터링 활성화
                computer.IsMemoryEnabled = True  # RAM 모니터링 활성화
                computer.IsMotherboardEnabled = True  # 메인보드 센서 활성화 (팬 속도, 전력 소비)
                computer.IsNetworkEnabled = True
                computer.IsBatteryEnabled = True
                computer.Open()  # 센서 데이터 가져오기 시작
                self.isInit = 0
            except:
                self.running = False
                Systeminfo_Thread.quit()

            FILE_ATTRIBUTE_HIDDEN = 0x02
            for _ in range(20):
                if os.path.exists("Sstat_display.sys"):
                    break
                QThread.msleep(100)
            if os.path.exists("Sstat_display.sys"):
                # 파일을 숨김 속성으로 설정
                ret = ctypes.windll.kernel32.SetFileAttributesW("Sstat_display.sys", FILE_ATTRIBUTE_HIDDEN)
                if ret == 0:  # 실패한 경우
                    print("sys 파일 숨김 처리 실패")
                else:
                    print("sys 파일 숨김 처리 성공")
                    
        while self.running:
            try:
                info = self.get_system_info(computer)
                self.info_updated.emit(info)
            except Exception as e:
                print(f"Error in SystemInfoThread: {e}")
            QThread.msleep(1000)

    def stop(self):
        self.running = False

    def get_system_info(self, computer):
        """Libre Hardware Monitor 데이터를 기반으로 시스템 정보를 가져옵니다."""
        try:
            cpu_usage = cpu_clock = cpu_temp = "N/A"
            ram_usage = ram_used = ram_available = ram_total = "N/A"
            gpu_usage = gpu_mem_used = gpu_mem_total = gpu_clock = gpu_temp = "N/A"
            cpu_power = gpu_power = "N/A"
            net_upload = net_download = "N/A"
            battery = "N/A"

            for hardware in computer.Hardware:
                hardware.Update()  # 최신 센서 데이터 업데이트
                for sensor in hardware.Sensors:
                    if str(sensor.SensorType) == "Load" and "CPU Total" == sensor.Name:
                        cpu_usage = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Clock" and "Core #1" == sensor.Name:
                        cpu_clock = round(sensor.Value)
                    if str(sensor.SensorType) == "Temperature" and "Core (Tctl/Tdie)" == sensor.Name:
                        cpu_temp = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Load" and "GPU Core" == sensor.Name:
                        gpu_usage = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Temperature" and "GPU Core" == sensor.Name:
                        gpu_temp = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Data" and "Memory Used" == sensor.Name:
                        ram_used = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Data" and "Memory Available" == sensor.Name:
                        ram_available = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "SmallData" and "GPU Memory Used" == sensor.Name:
                        gpu_mem_used = round(sensor.Value / 1024, 1)
                    if str(sensor.SensorType) == "SmallData" and "GPU Memory Total" == sensor.Name:
                        gpu_mem_total = round(sensor.Value / 1024, 1)
                    if str(sensor.SensorType) == "Clock" and "GPU Core" == sensor.Name:
                        gpu_clock = round(sensor.Value)
                    if str(sensor.SensorType) == "Power" and "Package" == sensor.Name:
                        cpu_power = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Power" and "GPU Package" == sensor.Name:
                        gpu_power = round(sensor.Value, 1)
                    if str(sensor.SensorType) == "Throughput" and "Upload Speed" == sensor.Name and net_upload == "N/A":
                        if hardware.Name == "Wi-Fi" or hardware.Name == "이더넷":
                            net_upload = round(sensor.Value / 1024 ** 2, 1)
                    if str(sensor.SensorType) == "Throughput" and "Download Speed" == sensor.Name and net_download == "N/A":
                        if hardware.Name == "Wi-Fi" or hardware.Name == "이더넷":
                            net_download = round(sensor.Value / 1024 ** 2, 1)
                    if str(sensor.SensorType) == "Level" and "Charge Level" == sensor.Name:
                        battery = round(sensor.Value, 1)
                    #print(f"{hardware.Name} | {sensor.Name} = {sensor.Value}({type(sensor.Value)}) | {sensor.SensorType}")

            if isinstance(ram_used, (int, float)) and isinstance(ram_available, (int, float)):
                ram_total = round(ram_used + ram_available, 1)
                ram_usage = round((ram_used / ram_total) * 100, 1)
            else:
                ram_usage = "N/A"

            if isinstance(gpu_mem_used, (int, float)) and isinstance(gpu_mem_total, (int, float)):
                gpu_mem_usage = round((gpu_mem_used / gpu_mem_total) * 100, 1)
            else:
                gpu_mem_usage = "N/A"

            if self.parent.always_show == True:
                color_for_toggle_display_mode = "<span style='color:#AACCAA'>Shift+1 : Display mode (always)"
            else: color_for_toggle_display_mode = "<span style='color:#CCCCCC'>Shift+1 : Display mode (auto)"

            result_text = (
                f'CPU : {color_print(cpu_usage, 1)}% | Clock : {cpu_clock} MHz | TEMP : {color_print(cpu_temp, 2)}°C | POWER : {color_print(cpu_power, 4)}W<br>'
                f'GPU : {color_print(gpu_usage, 1)}% | Clock : {gpu_clock} MHz | TEMP : {color_print(gpu_temp, 2)}°C | POWER : {color_print(gpu_power, 4)}W<br>'
                f'RAM : {color_print(ram_usage, 3)}% ({ram_used} / {ram_total}) | '
                f'VRAM : {color_print(gpu_mem_usage, 3)}% ({gpu_mem_used} / {gpu_mem_total})<br>'
            )
            
            if battery != "N/A":
                result_text = result_text + f"Battery : {color_print(battery, 6)}% | "
            
            result_text = result_text + (
                f'Net : {color_print(net_upload, 5)}MB/s ↑ {color_print(net_download, 5)}MB/s ↓<br>'
                f'{color_for_toggle_display_mode} <span style="color:#CCCCCC">| Shift+q : Quit'
            )
            
            return result_text
        except Exception as ex:
            print(f"Error in get_system_info: {ex}")
            return "Error retrieving data from Libre Hardware Monitor"

def color_print(value, type):
    """값에 따라 색상을 입힌 HTML 문자열 반환"""
    try:
        value = float(value)
        if type == 1:       # core usage
            if value < 40:
                return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
            elif value < 80:
                return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
            else:
                return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
        elif type == 2:     # temp
            if value < 50:
                return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
            elif value < 75:
                return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
            else:
                return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
        elif type == 3:     # memory usage
            if value < 50:
                return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
            elif value < 80:
                return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
            else:
                return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
        elif type == 4:     # power
            if value < 50:
                return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
            elif value < 150:
                return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
            else:
                return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
        elif type == 5:     # network
            if value < 10:
                return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
            elif value < 25:
                return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
            else:
                return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
        elif type == 6:     # battery
            if value > 50:
                return f"<span style='color:#66FF66'>{value}</span>"  # 초록색
            elif value > 20:
                return f"<span style='color:#FFFF66'>{value}</span>"  # 노란색
            else:
                return f"<span style='color:#FF6666'>{value}</span>"  # 빨간색
    except:
        return f"<span style='color:#FFFFFF'>{value}</span>"  # 에러 시 흰색 반환


if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.daemon = True
    monitor.show()
    sys.exit(app.exec_())