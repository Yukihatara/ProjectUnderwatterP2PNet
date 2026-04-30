# node_fixed.py
import argparse
import socket
import threading
import time
import json
import math
from typing import Set, Dict, Any, List, Tuple
import random

import queue
import os
from datetime import datetime

# === ФИКСИРОВАННЫЕ ПОРТЫ ===
PORT_MAP = {
    'A': 5001,
    'B': 5002, 
    'C': 5003,
    'D': 5004,
    'E': 5005
}
MAX_NODE = 5
MAX_RANGE = 80
MAX_PACKETS = list(range(1,11))

# === Аргументы ===
parser = argparse.ArgumentParser()
parser.add_argument("--id", required=True)   # required - обязательные значения 
parser.add_argument("--pos", required=True, help="x,y например 0,10 или -10,-5") # help Комментрарии внутри кода
parser.add_argument("--packets", type=str, default="")  # Тип преобразованных данных str. Если не задан аргумент - default
parser.add_argument("--sink", action="store_true")  # Укаание на булевые значения. Если не указан аргумент - false
args = parser.parse_args()


"""Знаний расположения всех узлов сети, енобходимое для того,, чтобы реализовать
ненаправленное излучение. В оптимальных алгоритма и протоколов MAC использоваться не будет""" 
positions = {
    'A': tuple(map(float, '0,100,0'.split(','))),       #B
    'B': tuple(map(float, '50,120,0'.split(','))), #A        #E
    'C': tuple(map(float, '50,80,0'.split(','))),       #C
    'D': tuple(map(float, '50,40,0'.split(','))),      
    'E': tuple(map(float, '100,100,0'.split(','))),     #D
}
table_round = {
    'A': {'B': positions['B'], 'C': positions['C'], 'D': positions['D']},
    'B': {'A': positions['A'], 'C': positions['C'], 'E': positions['E']},
    'C': {'A': positions['A'], 'B': positions['B'], 'D': positions['D'], 'E': positions['E']},
    'D': {'A': positions['A'], 'C': positions['C'], 'E': positions['E']},
    'E': {'B': positions['B'], 'C': positions['C'], 'D': positions['D']},
}
"""------------------------------------------------------------------------------------"""

dstrb_packets = {
    'A': sorted(set(range(1,11))),
    'B': sorted(set(range(5,11))),
    'C': sorted(set(range(4,8))),
    'D': sorted(set(range(1,6))),
    'E': sorted(set([])),
    }

is_sink_value = {
    'A': False,
    'B': False,
    'C': False,
    'D': False,
    'E': True,
    } 

stok = 'E'

cond = None # cond = 'Listening', cond = 'Sending', 

def parse_packets(s: str) -> Set[int]:
    if not s: return set()
    if '-' in s:
        a, b = map(int, s.split('-'))
        return set(range(a, b+1))
    return set(map(int, s.split(',')))

# === Данные узла ===
node_id = args.id
position = tuple(map(float, args.pos.split(',')))

packets_value = ['Каждый',' ','Охотник',' ','желает',' ','знать',',',' ','где']
packets = {}
for i in sorted(parse_packets(args.packets)):
    packets[i] = packets_value[i-1]    

# neibors = {name: position}

is_sink = args.sink

"""Априорная информация, которую неободимо собирать в процессе функционирования всей сети,
используя служеюные сообщения. Для упрощения, known_network известе с самого начала"""
# known_network: Dict[str, Dict[str, Any]] = {}

network_status = {}

network_status[node_id] = {
    'packets': list(packets.keys()),
    'position': position,
    'neibors': {},    # neibors = {node's_id: {'position': (), 'packets_id': [...]}}
    }


# DestinationStorage = {} 

node_ports = PORT_MAP.copy()


if node_id == 'A': 
    temp_data = {'fullset': [1,2,3,4,5,6,7,8,9,10]}
else:
    temp_data = {}
# Имитация полученного знания о существовании изображения в сети
# if node_id == 'E': temp_data = {'fullset': [1,2,3,4,5,6,7,8,9,10]}

# === Сокет ===
my_port = PORT_MAP[node_id]  # ← ФИКСИРОВАННЫЙ порт
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', my_port))
sock.settimeout(1.0)

print(f"\n=== Узел {node_id} запущен ===")
print(f"Порт: {my_port}") ### Для моделирования
print(f"Позиция: {position}") ### Для моделирования
print(f"Известные порты: {node_ports}") ### Для моделирования
print(f"Пакеты: {sorted(packets)}")
if is_sink: print("СТАТУС: Я — СТОК")
print("=" * 30)

# ОЧИСТКА БУФЕРА: читаем все старые данные
print(f"[{node_id}] Очищаю буфер сокета...")
sock.setblocking(False)
cleared = 0
while True:
    try:
        data, addr = sock.recvfrom(4096)
        cleared += 1
        print(f"[{node_id}] Очищен старый пакет ({len(data)} байт) от {addr}")
    except (socket.error, BlockingIOError):
        break
sock.setblocking(True)
print(f"[{node_id}] Очищено {cleared} старых пакетов")

# === Утилиты ===

# Настройка логирования
log_file = 'logs.txt'
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)

# Очередь для логов (буфер)
log_queue = queue.Queue()
log_thread_running = True

def log_writer():
    """Отдельный поток для записи логов в файл"""
    while log_thread_running:
        try:
            # Пытаемся получить сообщение из очереди с таймаутом 0.5 сек
            log_entry = log_queue.get(timeout=0.5)
            
            # Открываем файл каждый раз для записи (чтобы избежать блокировок)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
                f.flush()  # Принудительная запись на диск
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[{node_id}] Ошибка записи лога: {e}")

def log_event(node_id, operation, target, details=None):
    """
    Добавляет событие в очередь логов
    Формат: время | node_id | операция | отправитель/получатели | уточнение
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # ЧЧ:ММ:СС.ммм
    target_str = str(target) if target else "ALL"
    details_str = str(details) if details else "None"
    
    log_message = f"{timestamp} | {node_id} | {operation} | {target_str} | {details_str}"
    log_queue.put(log_message)

def calculate_propagation_delay(target_position, position=position):
    """Вычисляем задержку распространения сигнала"""
    dx = position[0] - target_position[0]
    dy = position[1] - target_position[1]
    dz = position[2] - target_position[2]
    dist = math.sqrt(dx**2 + dy**2 + dz**2)
    
    base_delay = dist/1500  # Чистая задержка по скорости звука
    noise = abs(random.gauss(0, 0.05))
    prop_delay = base_delay + noise
    
    return max(prop_delay, 0.001), dist   # Минимально-возможная задержка

def send_to(target_id, data, purpose_nodes, Route, msg_type):
  
    if msg_type == 'Hello':
        # Формируем сообщение
        msg = {
            'type': msg_type, # На практике предполагаю, что тип сообщения можно сократить
            'sender': node_id,
            'position': position,
            'packets_id': list(packets),
            'time': time.time(), # Планируется удаление
            }
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, None)    

    if msg_type == 'Known_Fullset':
        # Формируем сообщение
        msg = {
            'type': msg_type,
            'sender': node_id,
            'data': data,
            'time': time.time(),
            }
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, None)
  
    if msg_type == 'Retrans_Fullset':
        # Формируем сообщение
        msg = {
            'type': msg_type,
            'sender': node_id,
            'recievers': purpose_nodes,
            'data': data,
            'time': time.time(),
            }
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, None)

    if msg_type == 'Request':
        # Формируем сообщение
        msg = {
            'type': msg_type,
            'sender': node_id,
            'data': data,
            'route': Route,
            'time': time.time(),
            }    
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, f"{data.get('need_packets')}")
        
    if msg_type == 'Retrans_Request':
        # Формируем сообщение
        msg = {
            'type': msg_type, # На практике предполагаю, что тип сообщения можно сократить
            'sender': node_id,
            'recievers': purpose_nodes,
            'data': data,
            'time': time.time(), # Планируется удаление
            }
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, None)      
        
    if msg_type == 'Packets':
        # Формируем сообщение
        msg = {
            'type': msg_type,
            'sender': node_id,
            'recievers': purpose_nodes,
            'data': data,
            'route': Route,
            'time': time.time(),
            }
        # Костыль, чтобы не слать два сообщения (все в одном)
        if isinstance(data, list):
            msg['data'] = data[0]
            msg['data1'] = data[1]
            
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, f"{list(data)}")

    if msg_type == 'Packets2Retrans':
        # Формируем сообщение
        msg = {
            'type': msg_type,
            'sender': node_id,
            'recievers': purpose_nodes,
            'data': data,
            'time': time.time(),
            }
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, f"{list(data)}")
            
    if msg_type == 'Request_info':
        # Формируем сообщение
        msg = {
            'type': msg_type,
            'sender': node_id,
            'time': time.time(),
            }
        log_event(node_id, f"Отправка {msg_type}", purpose_nodes, None)
        
    # Трансформируем сообщение в нужный формат
    msg_json = json.dumps(msg).encode()
        
    # Отправляем сообщение
    try:
        # Добавляем задержку распространения сигна (иммитация задежки)
        prorp_delay, _ = calculate_propagation_delay(positions[target_id])
        time.sleep(prorp_delay + 0.05)
        
        # ОТПРАВКА
        sock.sendto(msg_json, ('127.0.0.1', node_ports[target_id]))
        print(f"[{node_id}]: Отправил {msg['type']} -> {target_id}")
    except Exception as e:
        print(f"[{node_id}]: Ошибка отправки в {target_id}: {e}")   

def send_in(msg_type=None, data=None, purpose_nodes=None, Route=None):
    """
    Функция, которая отправляет сообщения всем в радиусе.
    Иммитация ненаправленного излучения (сообщение содержит метку получателя) 
    
      - data: передаваемые данные (пакеты)    
        
      - target: сосед, которому отправляется сообзение,
        
      - purpose_nodes: кому назначено это сообщение.
        
    """
    # Запускаем отдельные процессы для отправки сообщений всем соседям в радиусе
    print("") # Структура вывода
    for target in table_round[node_id].keys():
        threading.Thread(target=send_to, args=(target, data, purpose_nodes, Route, msg_type,), daemon=True).start()
    
def process_request_packets(msg, mode=None):
# def process_request_packets(msg, mode): # mode: SndPck or RtrPck
    need_packets = set(msg.get('data').get('need_packets')) # list() -> set()
    
    back_node = msg.get('data').get('back_node')
    
    # Сохраняем полученную инфомрацию в переменную
    local_stok = msg.get('sender')
    neibors_cluster = msg.get('data').get('neibors') # neibors = {node's_id: {'position': (), 'packets_id': [...]}}
    
    # Проверяем наличие need_packets у соседей
    around_packets = set() # Сумма пакетов у всех соседей в радиусе
    for node in neibors_cluster:
        around_packets.update(set(neibors_cluster[node]['packets_id']))
    
    busy_storage = {} # {'node_id': num}
    
    local_need = need_packets - around_packets
    if local_need != need_packets: # Если "==", кластер не содержит запрошенных пакетов для отправки
        
        if local_need == set():
            print(f"\t- {list(neibors_cluster)} Среди соседей есть все пакеты")
        else:
            print(f"\t- Среди соседей {list(neibors_cluster)} не хватает {local_need} пакетов")
        
        # Поиск уникальных пакетов
        NodeAndUniqPck, all_unique_packets = find_unique_packets(neibors_cluster.copy())
        print(f"\t- Уникальные пакеты среди соседей:\n{' '*(4*2-1)}>{all_unique_packets}\n  - {NodeAndUniqPck}")
        
        # Некоторые уникальные пакеты не пересекаются с need_packets - отфильтруем
        for key, value in NodeAndUniqPck.items():
            NodeAndUniqPck[key] = value & need_packets

        # Создаем переменную, в которой будут узлы и пакеты, которые они отправят
        send_storage = NodeAndUniqPck.copy()

        for key, value in NodeAndUniqPck.items():
            busy_storage[key] = len(value)
            
        # Находим оставшиеся пакеты
        remaining_packets = need_packets - all_unique_packets

        # ------------------------------------------------------------------------------------------------------------------#
        # Уникальные пакеnы не покрывают запрос полностью - есть оставшиеся пакеты
        remaining_packets = need_packets - all_unique_packets # Находим оставшиеся пакеты
        
        if remaining_packets != set():
            for pck in remaining_packets:
                nodeMinValue = []
                minValue = min(busy_storage.values())
                for key, value in busy_storage.items():
                    if value == minValue:
                        nodeMinValue.append(key)
                                 
                if len(nodeMinValue) > 1: # Any nodes with same busy
                    arrDist = {}

                    for n in nodeMinValue:
                        if n == node_id:
                            _ , dist = calculate_propagation_delay(network_status[node_id]['neibors'][local_stok]['position'])
                            arrDist.update({n: dist})
                        else:
                            _ , dist = calculate_propagation_delay(network_status[node_id]['neibors'][local_stok]['position'],
                                                                   neibors_cluster[n]['position'])
                            arrDist.update({n: dist})

                    minDist = min(arrDist.values())
                    
                    for n, value in arrDist.items():
                        if value == minDist:
                            nodeMinValue[0] = n
                            
                busy_storage[nodeMinValue[0]] += 1
                send_storage[nodeMinValue[0]].update(set([pck]))
        # ------------------------------------------------------------------------------------------------------------------#
        # Создаем шаблон сообщения для отправки
        msg_to_send = {} # Пустоее сообщение
        if node_id in send_storage: # Проверка на наличии пакетов для отправки
            for i in list(send_storage[node_id]):
                msg_to_send[i] = packets[i] # {packet_idx: value}
            
            R = msg.get('route')
            recs = R.copy()[-1]
            recs_target = list(set(recs)&set(neibors_cluster))
            
            info_target = {} # Для того, чтобы познакомить узлы друг с другом, если они не знакомы
            for n in recs_target:
                info_target[n] = neibors_cluster[n]
            
            if len(R) < 2:
                # Отправляем всем узлам назад (по запросу) пакеты, чтобы они могли распределить нагрузку
                send_in(msg_type='Packets', data=msg_to_send, purpose_nodes=recs_target, Route=R.pop())
            else:            
                extend_msg_to_send = [msg_to_send, info_target, ]
                # Если пакеты отправляются для ретрансляции, необходимо дополнительно передать информацию о соседях
                send_in(msg_type='Packets', data=extend_msg_to_send, purpose_nodes=recs_target, Route=R.pop())
            
    elif local_need != set() and mode == 'CanRtr': # Есть пакеты, которых не хватает кластеру
        print("\t- Необходимо отправить запрос недостающих пакетов дальше")
        
        retrans_msg = {'neibors': neibors_cluster,
                       'need_packets': list(local_need),
                       'back_node': msg.get('data').get('back_node'),}
        
        retranslation(retrans_msg, 'Request')
                
def retranslation(msg, mode):
    print("\nЗапускаю алгоритм ретрансляции")
    sender = msg.get('sender')
    neibors_cluster = msg.get('data').get('neibors')
    whom_to_send = {}
    back_node = msg.get('data').get('back_node') 
    
    # Собираю всех своих соседей, которые не принадлежат моему кластеру и не являются отправителем
    for neibor in network_status[node_id]['neibors']:
        if neibor != sender and neibor not in neibors_cluster and neibor not in back_node:
            whom_to_send[neibor] = network_status[node_id]['neibors'][neibor]
     
    who_to_send_mt = {} # mt - my_target: кто может отправлять моим таргетам?
    
    # Ищем всех, кто связан с whom_to_send из neibors_sender, используя координаты
    for node1 in whom_to_send:
        who_to_send_mt[node1] = {}
        for node2 in neibors_cluster:
            _, dist = calculate_propagation_delay(whom_to_send[node1]['position'],neibors_cluster[node2]['position'] )
            if dist < 79:
                who_to_send_mt[node1].update({dist: node2})
    
    for node in who_to_send_mt:
        source_and_target = {who_to_send_mt[node][min(list(who_to_send_mt[node]))]: node}
    
    if node_id in source_and_target:   
        if mode == 'Fullset':
            msg_to_send_retranslation = {'neibors': whom_to_send,
                                         'fullset': msg.get('data').get('fullset'),
                                         'back_node': list(neibors_cluster),}
            
            someNodes = list()
            for node in source_and_target[node_id]:  
                someNodes.append(node)
            
            print(f"Ретранслирую {mode} в {someNodes}")
            send_in(msg_type='Retrans_Fullset', data=msg_to_send_retranslation, purpose_nodes=node)
        
        elif mode == 'Request':
            
            msg_to_send_retranslation = {'neibors': whom_to_send,
                                         'need_packets': neibors_cluster, # local_need pcks
                                         'back_node': list(neibors_cluster),}
            
            someNodes = list()
            for node in source_and_target[node_id]:    
                someNodes.append(node)
                
            R = msg.get('route')
            R.append(list(neibors_cluster))
            
            print(f"Ретранслирую {mode} в {someNodes}")
            send_in(msg_type='Request', data=msg_to_send_retranslation, purpose_nodes=node, Route=R)
    
    else:
        print(f"Я не учавствую в ретрансляции {mode}")
        
def receive_from():
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            
            msg = json.loads(data.decode())
            
            sender = msg.get('sender')
            
            if msg.get('type') == 'Hello':
                print(f"\nПолучил {msg.get('type')} от {sender}")
                
                log_event(node_id, f"Получил {msg.get('type')}", sender, None)
                
                # Обновляем информацию о своих соседях
                network_status[node_id]['neibors'].update({sender: {'position': msg.get('position'), 'packets_id': msg.get('packets_id')}})

            if msg.get('type') == 'Known_Fullset':
                
                """
                data = {'neibors': network_status[node_id]['neibors'],
                        'fullset': temp_data['fullset'],
                        'back_node': []}
                
                """

                print(f"\nПолучил {msg.get('type')} от {sender}")

                log_event(node_id, f"Получил {msg.get('type')}", sender, None)

                # Запускаем алгоритм ретрансляции
                retranslation(msg, 'Fullset')
            
            if msg.get('type') == 'Retrans_Fullset':
                
                """
                msg_to_send_retranslation = {'neibors': whom_to_send,
                                             'fullset': fullset,
                                             'back_node': list(neibors_cluster),}
                
                """
                
                print(f"\nПолучил {msg.get('type')} от {sender}")
                
                log_event(node_id, f"Получил {msg.get('type')}", sender, None)
                
                recievers = msg.get('recievers')
                
                if not sender or sender == node_id or node_id not in recievers :
                # if not sender or sender == node_id:
                    continue
                
                if is_sink:
                    temp_data.update( {'fullset': msg.get('data').get('fullset')} )
                    continue
                
                # Продолжаю ретранслировать мета-данные
                retranslation(msg, 'Fullset')                
            
            if msg.get('type') == 'Request':
                print(f"\nПолучил {msg.get('type')} от {sender}: {list(msg.get('data').get('need_packets'))}")
                
                log_event(node_id, f"Получил {msg.get('type')}", sender, f"Получил {msg.get('data').get('need_packets')}")
                
                """
                msg_request_packets = {
                    'neibors': network_status[node_id]['neibors'],
                    'need_packets': list(need_packets),
                    'back_node':[],
                    }
                """
                
                # Запускаем алгоритм поиска необходимых пакетов для отправки
                process_request_packets(msg, 'CanRtr')
                # process_request_packets(msg, 'SndPck')

            if msg.get('type') == 'Retrans_Request':
                print(f"\nПолучил {msg.get('type')} от {sender}")
                
                """
                msg_to_send_retranslation = {'neibors': whom_to_send,
                                             'need_packets': msg.get('data').get('need_packets'),
                                             'back_node': list(neibors_cluster),}
                """
                
                log_event(node_id, f"Получил {msg.get('type')}", sender, f"Получил {msg.get('data').get('need_packets')}")
                
                process_request_packets(msg, mode = 'RtrPck')
                
            if msg.get('type') == 'Packets':
                
                msg['data'] = {int(k): v for k, v in msg['data'].items()}
                
                log_event(node_id, f"Получил {msg.get('type')}", sender, f"Получил {list(msg.get('data'))}")
                
                recievers = msg.get('recievers')
                
                # Если в сообщении нет отправилея
                # Если отправил сам себе
                # Если получателем являюсь не я
                
                if not sender or sender == node_id or node_id not in recievers:
                # if not sender or sender == node_id:
                    continue
                
                new_packets = msg.get('data')
                print(f"\nПолучил PACKETS от {sender}: {list(new_packets.keys())}")
                
                # Обновляем свои пакеты
                packets.update(new_packets)
                network_status[node_id]['packets'] = sorted(set(packets.keys())) 
                
                print(f"[{node_id}] Обновил свои пакеты в network_status:\n  - {network_status[node_id]['packets']}")
                print(f"Содержимое пакетов:\n  - ({(''.join(list(dict(sorted(packets.items())).values())))})")
                
                if 'data1' in msg:
                    Neibors.get('data1')
                    
                
                
                
            if msg.get('type') == 'Packets2Retrans':
                
                msg['data'] = {int(k): v for k, v in msg['data'].items()}
                recievers = msg.get('recievers')
                
                if not sender or sender == node_id or node_id not in recievers:
                # if not sender or sender == node_id:
                    continue
            
                print(f"\nПолучил {msg.get('type')} от {sender}")
                log_event(node_id, f"Получил {msg.get('type')}", sender, f"Получил {list(msg.get('data'))}")
                
            if msg.get('type') == 'Request_Info':
                print(f"\nПолучил {msg.get('type')} от {sender}")
                
                # Добавляю соседа, поскольку я его слышу
                if sender not in network_status[node_id]['neibors']:
                    network_status[node_id]['neibors'].extend(list(sender))
                
                # Отправляю информацию по запросу
                send_in(msg_type='INFO', data=network_status[node_id], purpose_node=sender)
                
            if msg.get('type') == 'Info':
                
                recievers = msg.get('recievers')
                
                if not sender or sender == node_id or node_id not in recievers:
                # if not sender or sender == node_id:
                    continue
                print(f"\nПолучил {msg.get('type')} от {sender}\n")
                
                # Добавляю у себя соседа, поскольку я получил ответ
                if sender not in network_status[node_id]['neibors']:
                    network_status[node_id]['neibors'].extend(list(sender))
                network_status[sender] = msg.get('data')
         
        except socket.timeout:
            continue
        except ConnectionResetError as cre:  # ← СПЕЦИФИЧЕСКОЕ ИСКЛЮЧЕНИЕ ПЕРВЫМ
            print(f"[{node_id}] Подключение к несуществующему узлу <{cre}>")
            import traceback
            traceback.print_exc()
            continue
        except json.JSONDecodeError as e:
            print(f"[{node_id}] Ошибка декодирования JSON: {e}")
            continue
        except Exception as e:  # ← ОБЩЕЕ ИСКЛЮЧЕНИЕ ПОСЛЕДНИМ
            print(f"[{node_id}] Ошибка приема: {type(e).__name__}: {e}")
            continue

def find_unique_packets(neibors):
    """
    Найти уникальные пакеты у каждого узла в списке.
    
    Уникальный пакет = есть ТОЛЬКО у этого узла, нет у других.
    
    Args:
        nodes_around_target: список ID узлов (например, ['B', 'C', 'D'])
    
    Returns:
        dict: {node_id: [уникальные_пакеты_этого_узла]}
    """
    
    # result = {
    #     'A' = set([1,2,5]),
    # }
    # set(sorted(all_unique_packets))
    
    result = {}
    
    # 1. Собираем пакеты всех узлов
    all_packets = {}
    all_unique_packets = set()
    for n_id in neibors:
        all_packets[n_id] = set(neibors[n_id]['packets_id'])
    
    # 2. Для каждого узла находим уникальные пакеты
    for n_id, n_packets in all_packets.items():
        # Собираем пакеты ВСЕХ остальных узлов
        other_packets = set()
        for other_id, other_packets_set in all_packets.items():
            if other_id != n_id:
                other_packets.update(other_packets_set)
        
        # Уникальные = есть у этого узла, но нет у других
        unique_packets = n_packets - other_packets
        result[n_id] = set(sorted(list(unique_packets)))  # Сортируем для удобства
        
        all_unique_packets.update(unique_packets)
    
    return result, set(sorted(all_unique_packets))
    
def MainLoop():    
    time.sleep(10)
    warmup = 0
    print("\n ===Прогреваю сеть===")
    
    while True:
        if warmup < 2:
            send_in(msg_type='Hello',)
            time.sleep(0.05) # Для последовательного вывода в консоль необходимо УБРАТЬ!
            
            # Вывод информаии о соседях
            print("Мои сосдеди:")
            for key, value in network_status[node_id]['neibors'].items():
                print(f"| - [{key}]:\n |{'-'*5}>position: {value['position']}\n |{'-'*5}>packets_id: {value['packets_id']}")
            warmup += 1
            time.sleep(11)      
        else:
            print("\n ===Сеть прогрета===\n")
            break
        
    time.sleep(11)
    if node_id == 'A' and temp_data != {}:
        print("Я источник с полным набором данных")
    
        # Формируем посылку
        msg_to_send_info = {'neibors': network_status[node_id]['neibors'],
                            'fullset': temp_data['fullset'],
                            'back_node': [],}
        send_in(msg_type='Known_Fullset', data=msg_to_send_info,) # Отправляем сообщение всем в радиусе
                  
    while True:        
        if is_sink and temp_data != {}: # Пришла информация о существоании в сети некоторого изображения (индексы его пакетов)
            need_packets = set(temp_data['fullset']) - set(packets)
            if need_packets != set() and network_status[node_id]['neibors'] != {}:        
                msg_request_packets = {
                    'neibors': network_status[node_id]['neibors'],
                    'need_packets': list(need_packets),
                    'back_node':[node_id],
                    }
                
                send_in(msg_type='Request', data=msg_request_packets, Route=list(node_id))
            
        time.sleep(10)

# === Запуск ===

# Запускаем поток для записи логов
logging_thread = threading.Thread(target=log_writer, daemon=True)
logging_thread.start()

threading.Thread(target=MainLoop, daemon=True).start()
threading.Thread(target=receive_from, daemon=True).start()

try:
    while True: 
        time.sleep(1)
except KeyboardInterrupt:
    print(f"\n[{node_id}] Выключаюсь...")