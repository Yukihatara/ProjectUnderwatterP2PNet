"""
должна быть функция send(), которая принимает на вход:
    
    data - данные,
    
    # Разберем ваш пример: '!BBHII'

    # '!' - сетевой порядок байт (big-endian)
    # 'B' - unsigned char (1 байт, число 0-255)
    # 'B' - unsigned char (1 байт)
    # 'H' - unsigned short (2 байта, число 0-65535)
    # 'I' - unsigned int (4 байта, число 0-4294967295)
    # 'I' - unsigned int (4 байта)
    
    # Итого: 1+1+2+4+4 = 12 байт

"""     
import os
from pathlib import Path
import socket
import threading
import time
from pathlib import Path

import struct

import json

from Parser import process_all_data, split_data_to_packages, reconstruct_all_data, reconstruct_data


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


"""
    Path(...).unlink() - удаляет объект Path из файловой системы
    Path(...).glob('*ext') - поиск всех фалов с заданным расширением (например .txt)
"""

def UpdatePackets():
    
    time.sleep(1) # Raise to 15-30 in practice
    Packeges_path = Path('Packages')
        
    while True:
        process_all_data(data_dir='Data', packages_dir='Packages', package_size=60)
        if any(Packeges_path.iterdir()):
            print("There are contents in the Packeges folder")
        else:
            print("There are not contents in the Packeges folder")
            time.sleep(5)
            return
        
        send() # After data collecting
        time.sleep(10) # Raise to 15-30 in practice


def send():
    my_packages_path = Path(r"C:\Users\user\MainProject\Packages")    
    try:
        package_folders = [d for d in my_packages_path.iterdir() if d.is_dir()]        
        if not package_folders:
            print("There aren't packages")
            return
        
        for folder in package_folders:
            """
            Тут необходимо для каждого исходника брать пакеты, заворчаивать их
            в обертку paiload, чтобы правильно отправлять данные с указанием,
            какой пакеты к чему относится
            """
            packages = sorted(folder.glob('*.bin'))
            num_packages = len(packages)
            
            for pkg_file in packages:
                with open(pkg_file, 'rb') as f:
                    data = f.read()
            
            # Добавим простой заголовок
            # [4 байта - номер пакета][данные]
            packet_num = int(pkg_file.stem) # идетификатор
            
            print(packet_num)
            
            headers = struct.pack('!II', packet_num, num_packages)
        
            data_to_send = headers + data
            # Отправка пакетов
            sock1.sendto(data_to_send, ('127.0.0.1', node2_port)) # node1 -> node2
            time.sleep(0.1)
            
        time.sleep(3)
    except Exception as e:
        print(f"Ошибка отправки в {node2_port}: {e}")
        time.sleep(3)

def recieve():
    while True:
        try:
            data, addr = sock2.recvfrom(4096) # msg is byte
            # msg = data.decode('utf-8')
            
            if len(data) > 4:
                packet_num = struct.unpack('!I', data[:4])[0]
                num_packages = struct.unpack('!I', data[4:8])[0]
                print(f"Get packet {packet_num}. All packets {num_packages}")
                
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
threading.Thread(target=UpdatePackets, daemon=True).start()


while True:
    time.sleep(1)

