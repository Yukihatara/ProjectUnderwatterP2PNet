from pathlib import Path

import struct 
import json

import socket
import threading
import time

from Parser import process_all_data

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
    
    time.sleep(1) # Raise to 15-30 in practice
    Data_path = Path('Packages')
        
    while True:
        process_all_data(data_dir='Data', packages_dir='Packages', package_size=60)
        if any(Data_path.iterdir()):
            print("There are contents in the Data folder")
        else:
            print("There are not contents in the Data folder")
            time.sleep(5)
            return
        
        send() # After data collecting
        time.sleep(10) # Raise to 15-30 in practice

def send():
    my_packages_path = Path('Packages')    
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
        time.sleep(10)
    except Exception as e:
        print(f"Ошибка отправки в {node2_port}: {e}")
        time.sleep(3)

def recieve():
    reciver_id = 'E'
    node_env = Path('node_'+reciver_id)
    node_Packages = node_env / 'Packages'
    while True:
        try:
            # Get and processing r-data
            data, addr = sock2.recvfrom(4096) # msg is byte [headers][payload]
            if len(data) > 4:
                pkg_id = int(struct.unpack('!I', data[:4])[0])
                package_name = f"{pkg_id}.bin"
                package_path = node_Packages / package_name
                
                # Write r-data to folder as .bin file
                with open(package_path, 'wb') as pckg_p:
                    pckg_p.write(data[8:])
                    
                number_pkg = struct.unpack('!I', data[4:8])[0]
                print(f"Get packet {pkg_id}. All packets {number_pkg}")

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

