# launch_all_windows_improved.py
import subprocess
import time
import os

nodes = [
    {"id": "A", "pos": "0,100,0", "packets": "1-10", "sink": False},
    {"id": "B", "pos": "50,120,0", "packets": "5-10", "sink": False},
    {"id": "C", "pos": "50,80,0", "packets": "4-7", "sink": False},
    {"id": "D", "pos": "50,40,0", "packets": "1-5", "sink": False},
    {"id": "E", "pos": "100,100,0", "packets": "", "sink": True}
]

print("Запуск 5 узлов в отдельных окнах...")
print("Закройте все окна для завершения работы.\n")

for node in nodes:
    # Собираем команду
    cmd_parts = ["python", "node8.py", 
                 "--id", node["id"], 
                 "--pos", node["pos"]]
    
    if node.get("packets"):
        cmd_parts.extend(["--packets", node["packets"]])
    if node.get("sink"):
        cmd_parts.append("--sink")
    
    # Запуск в новом окне cmd
    cmd_str = " ".join(cmd_parts)
    subprocess.Popen(f'start cmd /k "{cmd_str}"', shell=True)
    time.sleep(2)  # Увеличил задержку для стабильности

print("Все узлы запущены!")
print("Для завершения закройте окна терминалов вручную.")