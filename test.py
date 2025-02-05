import clr
import os
import time

clr.AddReference("LibreHardwareMonitorLib")

# Libre Hardware Monitor 모듈 가져오기
from LibreHardwareMonitor import Hardware

# Libre Hardware Monitor 초기화
computer = Hardware.Computer()
computer.IsCpuEnabled = True  # CPU 모니터링 활성화
computer.IsGpuEnabled = True  # GPU 모니터링 활성화
computer.IsMemoryEnabled = True  # RAM 모니터링 활성화
computer.IsMotherboardEnabled = True  # 메인보드 센서 활성화 (팬 속도, 전력 소비)
computer.Open()  # 센서 데이터 가져오기 시작

def get_sensor_data():
    """Libre Hardware Monitor를 통해 CPU, GPU, VRAM 등의 정보를 가져옴"""
    sensor_data = {}

    # 모든 하드웨어 장치 순회
    for hardware in computer.Hardware:
        hardware.Update()  # 최신 센서 데이터 업데이트
        for sensor in hardware.Sensors:
            if sensor.SensorType == Hardware.SensorType.Temperature:
                sensor_data[f"{hardware.Name} - {sensor.Name} Temp"] = f"{sensor.Value}°C"
            elif sensor.SensorType == Hardware.SensorType.Load:
                sensor_data[f"{hardware.Name} Load"] = f"{sensor.Value}%"
            elif sensor.SensorType == Hardware.SensorType.Clock:
                sensor_data[f"{hardware.Name} Clock"] = f"{sensor.Value} MHz"
            elif sensor.SensorType == Hardware.SensorType.Power:
                sensor_data[f"{hardware.Name} Power"] = f"{sensor.Value} W"
            elif sensor.SensorType == Hardware.SensorType.Fan:
                sensor_data[f"{hardware.Name} Fan Speed"] = f"{sensor.Value} RPM"
            elif sensor.SensorType == Hardware.SensorType.SmallData:
                if "Memory Used" in sensor.Name:
                    sensor_data[f"{hardware.Name} VRAM Used"] = f"{sensor.Value / 1024:.1f} GB"
                elif "Memory Total" in sensor.Name:
                    sensor_data[f"{hardware.Name} VRAM Total"] = f"{sensor.Value / 1024:.1f} GB"

    return sensor_data

# 5초마다 센서 데이터 출력
try:
    while True:
        sensor_data = get_sensor_data()
        os.system("cls" if os.name == "nt" else "clear")  # 콘솔 화면 지우기
        print("=== Libre Hardware Monitor Sensor Data ===")
        for key, value in sensor_data.items():
            print(f"{key}: {value}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n종료됨.")
    computer.Close()  # Libre Hardware Monitor 종료
