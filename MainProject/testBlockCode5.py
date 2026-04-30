import os
from pathlib import Path
import socket
import threading
import keyboard
import time
from pathlib import Path

import json


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

# def send():
#     data_to_send = 'Hello world'
#     time.sleep(1)
#     while True:
#         try:
            
#             print(data_to_send)
            
#             data_to_send_json = json.dumps({'data':data_to_send}).encode()
#             sock1.sendto(data_to_send_json, ('127.0.0.1', node2_port)) # node1 -> node2
#             time.sleep(3)
#         except Exception as e:
#             print(f"Ошибка отправки в {node2_port}: {e}")
#             time.sleep(3)
#             continue
                
# def recieve():
#     while True:
#         try:
#             data, addr = sock2.recvfrom(4096)
#             msg = json.loads(data.decode())
            
#             print(f"Получено сообщение от {addr}:\n{msg}")
            
#         except socket.timeout:
#             continue
#         except ConnectionResetError as cre:  # ← СПЕЦИФИЧЕСКОЕ ИСКЛЮЧЕНИЕ ПЕРВЫМ
#             print(f"Подключение к несуществующему узлу <{cre}>")
#             import traceback
#             traceback.print_exc()
#             continue
#         except json.JSONDecodeError as e:
#             print(f"Ошибка декодирования JSON: {e}")
#             continue
#         except Exception as e:  # ← ОБЩЕЕ ИСКЛЮЧЕНИЕ ПОСЛЕДНИМ
#             print(f"Ошибка приема: {type(e).__name__}: {e}")
#             continue


def send():
    data_to_send = 'Hello world'
    time.sleep(1)
    while True:
        try:
            with open(Path('Packages/00001/00012.bin'), 'rb') as f:
                data_to_send = f.read()
            
            sock1.sendto(data_to_send, ('127.0.0.1', node2_port)) # node1 -> node2
            time.sleep(3)
        except Exception as e:
            print(f"Ошибка отправки в {node2_port}: {e}")
            time.sleep(3)
            continue

def recieve():
    while True:
        try:
            data, addr = sock2.recvfrom(4096)
            msg = data.decode()
            
            print(f"Получено сообщение от {addr}:\n{msg}")
            
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

threading.Thread(target=send, daemon=True).start()        
threading.Thread(target=recieve, daemon=True).start()

while True:
    time.sleep(1)

