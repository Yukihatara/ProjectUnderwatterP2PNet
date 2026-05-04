import os
from pathlib import Path
import socket
import threading
import keyboard
import time
from pathlib import Path

import json

from parser import process_all_data, split_data_to_packages, reconstruct_all_data, reconstruct_data


# files_bin = [f for f in Path('Packages/00001').iterdir() if f.is_file() and f.suffix == '.bin']
# print(files_bin)

# === Сокет ===

node1_port = 5001
node2_port = 5002

# Создание сокета 1 для абонента 1
sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock1.bind(('', node1_port))
sock1.settimeout(1.0)
# sock1.setblocking(False)

# Создание сокета 2 для абонента 2
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock2.bind(('', node2_port))
sock2.settimeout(1.0)
# sock2.setblocking(False)

def UpdatePackets():
    Data_path = Path(r'C:\Users\user\MainProject\Data')
    Packeges_path = Path(r'C:\Users\user\MainProject\Packeges')
        
    while True:
        result = process_all_data(data_dir='Data', packages_dir='Packages', package_size=60)
        if any(Packeges_path.iterdir()):
            print("There are contents in the Packeges folder")
        else:
            print("There are not contents in the Packeges folder")
        
        send()
        time.sleep(5) # Raise to 15-30

def send():
    
    my_packages_path = Path(r"C:\Users\user\MainProject\Packeges")
    try:
        package_folders = [d for d in my_packages_path.iterdir() if d.is_dir()]        
        if not package_folders:
            print("There aren't packages")
            return
        
        for folder in package_folders:
            
            
        with open(Path('Packages/00001/00012.bin'), 'rb') as f:
            data = f.read()
        
        sock1.sendto(data, ('127.0.0.1', node2_port)) # node1 -> node2
        time.sleep(3)
    except Exception as e:
        print(f"Ошибка отправки в {node2_port}: {e}")
        time.sleep(3)

def recieve():
    while True:
        try:
            data, addr = sock2.recvfrom(4096) # msg is byte
            # msg = data.decode('utf-8')
            
            print(f"Получено сообщение от {addr}:\n{data}")
            
        except socket.timeout:
            continue
        except ConnectionResetError as cre:  # ← СПЕЦИФИЧЕСКОЕ ИСКЛЮЧЕНИЕ ПЕРВЫМ
            print(f"Подключение к несуществующему узлу <{cre}>")
            import traceback
            traceback.print_exc()
            continue
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON: {e}")
            continue
        except Exception as e:  # ← ОБЩЕЕ ИСКЛЮЧЕНИЕ ПОСЛЕДНИМ
            print(f"Ошибка приема: {type(e).__name__}: {e}")
            continue


# threading.Thread(target=send, daemon=True).start()        
threading.Thread(target=recieve, daemon=True).start()

while True:
    time.sleep(1)

