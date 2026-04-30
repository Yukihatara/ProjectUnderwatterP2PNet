import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import socket
import math
from collections import defaultdict, deque
import random
from datetime import datetime

class NetworkVisualizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Симулятор сети - Визуализация передачи пакетов в реальном времени")
        self.root.geometry("1600x900")
        
        # Данные сети
        self.nodes = ['A', 'B', 'C', 'D', 'E']
        self.positions = {
            'A': (200, 200),
            'B': (400, 100),
            'C': (400, 300),
            'D': (400, 500),
            'E': (600, 300)
        }
        
        # Состояние узлов
        self.node_packets = {node: set() for node in self.nodes}
        self.max_packets = 10
        
        # Очередь событий и история
        self.event_queue = deque()
        self.active_transmissions = []
        self.transmission_history = deque(maxlen=20)
        
        # Подсветка недавно полученных пакетов (3 секунды)
        self.packet_highlights = {node: {} for node in self.nodes}  # {node: {packet_id: expire_time}}
        
        # Состояния узлов
        self.node_states = {node: {
            'mode': 'idle',
            'activity': 0,
        } for node in self.nodes}
        
        # Цвета
        self.colors = {
            'have': '#90EE90',
            'missing': '#FFB6C1',
            'beacon': '#FFD700',
            'request': '#FFA500',
            'transmission': '#FF4500',
            'warmup': '#FFFF00',
            'sink': '#000000',
            'connection': '#4169E1',
            'active_connection': '#FF0000',
            'idle': '#D3D3D3'
        }
        
        self.setup_ui()
        self.reset_simulation()           # начальное состояние
        self.start_realtime_monitoring()
        self.animate_realtime()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Холст
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=0, column=0, padx=10)
        
        self.canvas = tk.Canvas(canvas_frame, width=900, height=600, bg='white')
        self.canvas.grid(row=0, column=0)
        
        # Правая панель
        info_frame = ttk.Frame(main_frame, width=500)
        info_frame.grid(row=0, column=1, padx=10, sticky=(tk.N, tk.S))
        
        # Управление
        control_frame = ttk.LabelFrame(info_frame, text="Управление", padding="10")
        control_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame, text="▶ Запустить симуляцию", 
                  command=self.start_simulation).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="⏸ Пауза", 
                  command=self.pause_simulation).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="🔄 Сброс", 
                  command=self.reset_simulation).grid(row=0, column=2, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Статус: Готов", foreground="blue")
        self.status_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        # Таблица пакетов
        packets_frame = ttk.LabelFrame(info_frame, text="Состояние пакетов", padding="10")
        packets_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        columns = ('Узел', 'Режим') + tuple(f'Пакет {i}' for i in range(1, 11))
        self.packet_tree = ttk.Treeview(packets_frame, columns=columns, height=6, show='headings')
        
        self.packet_tree.column('Узел', width=50)
        self.packet_tree.column('Режим', width=90)
        for i in range(1, 11):
            self.packet_tree.column(f'Пакет {i}', width=45)
            self.packet_tree.heading(f'Пакет {i}', text=str(i))
        
        self.packet_tree.heading('Узел', text='Узел')
        self.packet_tree.heading('Режим', text='Режим')
        
        for node in self.nodes:
            self.packet_tree.insert('', 'end', iid=node, values=[node, '● idle'] + ['']*10)
        
        self.packet_tree.grid(row=0, column=0, pady=5)
        
        # Статистика
        stats_frame = ttk.LabelFrame(info_frame, text="Статистика и транзакции", padding="10")
        stats_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))
        
        header_frame = ttk.Frame(stats_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(header_frame, text="Время", font=('Arial', 9, 'bold'), width=8).grid(row=0, column=0)
        ttk.Label(header_frame, text="Тип", font=('Arial', 9, 'bold'), width=8).grid(row=0, column=1)
        ttk.Label(header_frame, text="От", font=('Arial', 9, 'bold'), width=6).grid(row=0, column=2)
        ttk.Label(header_frame, text="К", font=('Arial', 9, 'bold'), width=6).grid(row=0, column=3)
        ttk.Label(header_frame, text="Пакеты", font=('Arial', 9, 'bold'), width=20).grid(row=0, column=4)
        
        self.stats_text = tk.Text(stats_frame, width=60, height=15, font=('Courier', 9))
        self.stats_text.grid(row=1, column=0)
        
        # Легенда
        legend_frame = ttk.LabelFrame(info_frame, text="Легенда", padding="10")
        legend_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        
        legend_items = [
            (self.colors['have'], "✅ Есть пакет"),
            (self.colors['missing'], "❌ Нет пакета"),
            (self.colors['transmission'], "🔴 Только что получен"),
            (self.colors['beacon'], "📡 Beacon"),
            (self.colors['request'], "🔍 Запрос"),
            (self.colors['warmup'], "⚡ Прогрев"),
            ("black", "⭕ Сток E"),
        ]
        
        for i, (color, text) in enumerate(legend_items):
            frame = ttk.Frame(legend_frame)
            frame.grid(row=i//3, column=i%3, sticky=tk.W, pady=2, padx=10)
            if color == "black":
                c = tk.Canvas(frame, width=20, height=20, bg='white')
                c.grid(row=0, column=0)
                c.create_oval(5, 5, 15, 15, fill='black')
            else:
                c = tk.Canvas(frame, width=20, height=20, bg=color)
                c.grid(row=0, column=0)
            ttk.Label(frame, text=text).grid(row=0, column=1, padx=5)
    
    def draw_network(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, 900, 600, fill='#F0F0F0')
        
        self.draw_connections()
        for node, (x, y) in self.positions.items():
            self.draw_node(node, x, y)
    
    def draw_node(self, node, x, y):
        state = self.node_states[node]
        mode = state['mode']
        
        if mode == 'warmup':
            fill_color = self.colors['warmup']
        elif mode == 'beacon':
            fill_color = self.colors['beacon']
        elif mode == 'request':
            fill_color = self.colors['request']
        elif mode == 'transmit':
            fill_color = self.colors['transmission']
        else:
            fill_color = self.colors['idle']
        
        # Пульсация
        if state['activity'] > 0:
            pulse = state['activity'] * 1.5
            self.canvas.create_oval(x-25-pulse, y-25-pulse, x+25+pulse, y+25+pulse,
                                   outline=fill_color, width=3, dash=(3,3))
        
        # Сам узел
        outline = 'black' if node == 'E' else 'gray'
        width = 4 if node == 'E' else 2
        self.canvas.create_oval(x-20, y-20, x+20, y+20, 
                               fill=fill_color, outline=outline, width=width)
        
        self.canvas.create_text(x, y-30, text=node, font=('Arial', 14, 'bold'))
        
        mode_text = {'warmup': '🔥', 'beacon': '📡', 'request': '🔍', 
                     'transmit': '📤', 'idle': '●'}.get(mode, '●')
        self.canvas.create_text(x, y+30, text=mode_text, font=('Arial', 12))
        
        self.draw_packets(x, y, self.node_packets.get(node, set()), node)
    
    def draw_connections(self):
        connections = [
            ('A', 'B'), ('A', 'C'), ('A', 'D'),
            ('B', 'C'), ('B', 'E'),
            ('C', 'B'), ('C', 'D'), ('C', 'E'),
            ('D', 'C'), ('D', 'E'),
            ('E', 'B'), ('E', 'C'), ('E', 'D')
        ]
        
        for n1, n2 in connections:
            if n1 in self.positions and n2 in self.positions:
                x1, y1 = self.positions[n1]
                x2, y2 = self.positions[n2]
                
                is_active = any((t['from'] == n1 and t['to'] == n2) for t in self.active_transmissions)
                
                color = self.colors['active_connection'] if is_active else self.colors['connection']
                width = 3 if is_active else 1
                dash = () if is_active else (4, 2)
                
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, dash=dash)
                
                if is_active:
                    for trans in self.active_transmissions:
                        if trans['from'] == n1 and trans['to'] == n2:
                            self.animate_packet_transfer(trans, x1, y1, x2, y2)
                            break
    
    def animate_packet_transfer(self, trans, x1, y1, x2, y2):
        elapsed = time.time() - trans['start_time']
        duration = trans.get('duration', 1.5)
        if elapsed > duration:
            return
            
        progress = elapsed / duration
        x = x1 + (x2 - x1) * progress
        y = y1 + (y2 - y1) * progress
        
        color = self.colors.get(trans.get('type', 'PACKETS').lower(), self.colors['transmission'])
        
        self.canvas.create_oval(x-9, y-9, x+9, y+9, fill=color, outline='black', width=2)
        self.canvas.create_text(x, y, text="P", font=('Arial', 9, 'bold'), fill='white')
    
    def draw_packets(self, x, y, packets, node):
        radius = 45
        size = 15
        
        now = time.time()
        for i in range(1, self.max_packets + 1):
            angle = (i - 1) * (360 / self.max_packets)
            rad = math.radians(angle)
            px = x + radius * math.cos(rad)
            py = y + radius * math.sin(rad)
            
            if i in packets:
                # Подсветка недавно полученного
                highlight = (i in self.packet_highlights[node] and 
                            now < self.packet_highlights[node][i])
                color = self.colors['transmission'] if highlight else self.colors['have']
            else:
                color = self.colors['missing']
            
            self.canvas.create_oval(px-size/2, py-size/2, px+size/2, py+size/2,
                                   fill=color, outline='black', width=1)
            self.canvas.create_text(px, py, text=str(i), font=('Arial', 8, 'bold'))
    
    def update_packet_table(self):
        now = time.time()
        for node in self.nodes:
            values = [node]
            
            mode = self.node_states[node]['mode']
            mode_str = {
                'warmup': '🔥 прогрев',
                'beacon': '📡 beacon',
                'request': '🔍 запрос',
                'transmit': '📤 передача',
                'idle': '● ожидание'
            }.get(mode, '● idle')
            values.append(mode_str)
            
            packets = self.node_packets.get(node, set())
            for i in range(1, 11):
                if i in packets:
                    recently = (i in self.packet_highlights[node] and 
                               now < self.packet_highlights[node].get(i, 0))
                    values.append('🟢' if recently else '✓')
                else:
                    values.append('✗')
            
            self.packet_tree.item(node, values=values)
    
    def update_stats(self):
        self.stats_text.delete(1.0, tk.END)
        total = sum(len(p) for p in self.node_packets.values())
        sink = len(self.node_packets.get('E', set()))
        
        text = f"{'='*55}\n"
        text += f"📊 СТАТИСТИКА {datetime.now().strftime('%H:%M:%S')}\n"
        text += f"{'='*55}\n"
        text += f"📦 Всего пакетов в сети: {total}/50\n"
        text += f"🎯 У стока E: {sink}/10  ({sink*10}%)\n\n"
        text += f"📋 ПОСЛЕДНИЕ ТРАНЗАКЦИИ\n"
        text += f"{'-'*55}\n"
        text += f"{'Время':<9} {'Тип':<9} {'От':<4} {'→':<2} {'К':<4} Пакеты\n"
        
        for t in list(self.transmission_history)[-7:]:
            ts = t.get('time', '')[-8:]
            typ = t.get('type', '')[0:8]
            fr = t.get('from', '')
            to = t.get('to', '')
            pkts = str(t.get('packets', ''))[:18]
            text += f"{ts:<9} {typ:<9} {fr:<4} → {to:<4} {pkts}\n"
        
        self.stats_text.insert(1.0, text)
    
    def add_event(self, event_type, from_node, to_node, packets=None):
        event = {
            'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'type': event_type,
            'from': from_node,
            'to': to_node,
            'packets': packets or []
        }
        
        self.transmission_history.append(event)
        
        # Активная передача (анимация)
        duration = random.uniform(1.2, 2.3)
        self.active_transmissions.append({
            **event,
            'start_time': time.time(),
            'duration': duration
        })
        
        # Обновление состояния узлов
        mode_from = 'transmit' if event_type == 'PACKETS' else event_type.lower()
        self.node_states[from_node]['mode'] = mode_from
        self.node_states[from_node]['activity'] = 25
        self.node_states[to_node]['activity'] = 12
        
        # Добавление пакетов + подсветка
        if event_type == 'PACKETS' and packets:
            current = self.node_packets.get(to_node, set())
            self.node_packets[to_node] = current | set(packets)
            
            now = time.time()
            for p in packets:
                self.packet_highlights[to_node][p] = now + 3.0   # подсветка 3 секунды
    
    # ====================== СИМУЛЯЦИЯ ======================
    def simulate_warmup(self):
        for node in self.nodes:
            self.node_states[node]['mode'] = 'warmup'
            self.node_states[node]['activity'] = 30
            for target in self.nodes:
                if target != node:
                    self.add_event('BEACON', node, target)
                    time.sleep(0.15)
            time.sleep(0.4)
    
    def simulate_requests(self):
        for target in ['B', 'C', 'D']:
            self.add_event('REQUEST', 'E', target, [1,2,3,4,5,6,7,8,9,10])
            time.sleep(0.7)
    
    def simulate_transmissions(self):
        self.add_event('PACKETS', 'B', 'E', [5,6,7,8,9,10])
        time.sleep(1.0)
        self.add_event('PACKETS', 'C', 'E', [4,5,6,7])
        time.sleep(1.0)
        self.add_event('PACKETS', 'D', 'E', [1,2,3,4,5])
        time.sleep(1.0)
        self.add_event('PACKETS', 'A', 'C', [1,2,3])
        time.sleep(0.8)
        self.add_event('PACKETS', 'A', 'B', [4,8,9,10])
    
    def start_simulation(self):
        self.status_label.config(text="Статус: Симуляция запущена", foreground="green")
        threading.Thread(target=self.run_simulation, daemon=True).start()
    
    def run_simulation(self):
        self.reset_simulation()
        time.sleep(0.8)
        
        self.status_label.config(text="Фаза 1 — Прогрев (BEACON)")
        self.simulate_warmup()
        time.sleep(1.5)
        
        self.status_label.config(text="Фаза 2 — Запросы (REQUEST)")
        self.simulate_requests()
        time.sleep(1.5)
        
        self.status_label.config(text="Фаза 3 — Передача пакетов")
        self.simulate_transmissions()
        
        self.status_label.config(text="Симуляция завершена ✓", foreground="blue")
    
    def pause_simulation(self):
        self.status_label.config(text="Статус: Пауза", foreground="orange")
    
    def reset_simulation(self):
        self.node_packets = {
            'A': {1,2,3,4,5,6,7,8,9,10},
            'B': {5,6,7,8,9,10},
            'C': {4,5,6,7},
            'D': {1,2,3,4,5},
            'E': set()
        }
        self.active_transmissions.clear()
        self.transmission_history.clear()
        self.packet_highlights = {node: {} for node in self.nodes}
        
        for node in self.nodes:
            self.node_states[node] = {'mode': 'idle', 'activity': 0}
        
        self.status_label.config(text="Статус: Сброшено", foreground="blue")
    
    def animate_realtime(self):
        now = time.time()
        
        # 1. Удаляем завершившиеся передачи
        self.active_transmissions = [
            t for t in self.active_transmissions 
            if now - t['start_time'] < t.get('duration', 1.0)
        ]
        
        # 2. Уменьшаем активность узлов
        for node in self.nodes:
            if self.node_states[node]['activity'] > 0:
                self.node_states[node]['activity'] -= 1
                if self.node_states[node]['activity'] == 0:
                    self.node_states[node]['mode'] = 'idle'
        
        # 3. Очищаем устаревшую подсветку пакетов
        for node in self.nodes:
            expired = [p for p, exp in self.packet_highlights[node].items() if now > exp]
            for p in expired:
                del self.packet_highlights[node][p]
        
        # 4. Рисуем всё
        self.draw_network()
        self.update_packet_table()
        self.update_stats()
        
        self.root.after(16, self.animate_realtime)   # ~60 FPS
    
    def start_realtime_monitoring(self):
        self.monitor_thread = threading.Thread(target=self.monitor_network, daemon=True)
        self.monitor_thread.start()
    
    def monitor_network(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 6000))
        sock.settimeout(0.1)
        
        while True:
            try:
                data, _ = sock.recvfrom(4096)
                msg = json.loads(data.decode())
                
                if 'transmission' in msg:
                    t = msg['transmission']
                    self.add_event(
                        t.get('type', 'PACKETS'),
                        t['from'],
                        t['to'],
                        t.get('packets')
                    )
                elif 'packets' in msg and 'node_id' in msg:
                    self.node_packets[msg['node_id']] = set(msg['packets'])
            except socket.timeout:
                continue
            except Exception:
                continue   # не падаем
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    visualizer = NetworkVisualizer()
    visualizer.run()