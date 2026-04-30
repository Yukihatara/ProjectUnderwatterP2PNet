import json
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# --- Координаты узлов ---
# positions = {
#     'A': (0, 100, 0),
#     'B': (50, 120, 0),
#     'C': (50, 80, 0),
#     'D': (50, 40, 0),
#     'E': (100, 100, 0),
# }

positions = {
    'A': (0, 1200, 0),
    'B': (1000, 1603, 0),
    'C': (1000, 800, 0),
    'D': (1000, 1, 0),
    'E': (2000, 1200, 0),
}


# --- Связность ---
connections = {
    'A': ['B', 'C', 'D'],
    'B': ['A', 'C', 'E'],
    'C': ['A', 'B', 'D', 'E'],
    'D': ['A', 'C', 'E'],
    'E': ['B', 'C', 'D']
}

# --- Цвета сообщений ---
msg_colors = {
    'Known_Fullset': 'blue',
    'Request': 'orange',
    'Packets': 'green',
}

# --- Загрузка логов ---
def load_logs(path="logs.txt"):
    logs = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            log = json.loads(line.strip())
            log['time_start'] = datetime.fromisoformat(log['time_start'])
            log['time_end'] = log['time_start'] + timedelta(seconds=log['delay'])
            logs.append(log)
    return logs

logs = load_logs()

start_time = min(l['time_start'] for l in logs)
end_time = max(l['time_end'] for l in logs)

# --- Фигура ---
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# --- Рисуем узлы ---
def draw_nodes():
    for node, (x, y, z) in positions.items():
        ax.scatter(x, y, z, s=300, color='black')
        ax.text(x, y, z, node, fontsize=10, color='white', ha='center', va='center')

# --- Рисуем базовые связи ---
def draw_base_connections():
    for src, targets in connections.items():
        for dst in targets:
            if src < dst:  # чтобы не дублировать
                x = [positions[src][0], positions[dst][0]]
                y = [positions[src][1], positions[dst][1]]
                z = [positions[src][2], positions[dst][2]]
                ax.plot(x, y, z, color='black', linewidth=1)

# --- Рисуем стрелку передачи ---
def draw_arrow(src, dst, color):
    x1, y1, z1 = positions[src]
    x2, y2, z2 = positions[dst]

    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1

    ax.quiver(
        x1, y1, z1,
        dx, dy, dz,
        arrow_length_ratio=0.2,
        color=color,
        linewidth=2
    )

# --- Анимация ---
current_time = start_time

def update(frame):
    global current_time
    ax.clear()

    # фон темный для контраста
    ax.set_facecolor('white')

    draw_nodes()
    draw_base_connections()

    # активные передачи
    for log in logs:
        if log['time_start'] <= current_time <= log['time_end']:
            src = log['node']
            color = msg_colors.get(log['type'], 'red')

            for dst in log['targets']:
                draw_arrow(src, dst, color)

    # заголовок
    ax.set_title(f"Time: {current_time.strftime('%H:%M:%S.%f')[:-3]}")

    # границы
    # ax.set_xlim(0, 120)
    # ax.set_ylim(0, 140)
    # ax.set_zlim(0, 50)
    
    ax.set_xlim(-200, 2200)
    ax.set_ylim(-200, 2200)
    ax.set_zlim(-200, 2200)

    current_time += timedelta(milliseconds=100)
    if current_time > end_time:
        current_time = start_time

# --- Легенда ---
def draw_legend():
    for msg, color in msg_colors.items():
        ax.plot([], [], [], color=color, label=msg, linewidth=3)
    ax.legend(loc='upper left')

# --- Запуск ---
draw_legend()
ani = FuncAnimation(fig, update, interval=100)
plt.show()