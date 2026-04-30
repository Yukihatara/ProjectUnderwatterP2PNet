import subprocess
import time
import os
import sys

def launch_all():
    print("=" * 60)
    print("ЗАПУСК СИМУЛЯЦИИ СЕТИ С ВИЗУАЛИЗАЦИЕЙ")
    print("=" * 60)
    
    # 1. Запускаем визуализатор
    print("\n[1/2] Запуск визуализатора...")
    visualizer_process = subprocess.Popen(
        [sys.executable, "network_visualizer.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    time.sleep(2)
    
    # 2. Запускаем узлы
    print("\n[2/2] Запуск узлов сети...")
    
    nodes = [
        {"id": "A", "pos": "0,100,0", "packets": "1-10", "sink": False},
        {"id": "B", "pos": "50,120,0", "packets": "5-10", "sink": False},
        {"id": "C", "pos": "50,80,0", "packets": "4-7", "sink": False},
        {"id": "D", "pos": "50,40,0", "packets": "1-5", "sink": False},
        {"id": "E", "pos": "100,100,0", "packets": "", "sink": True}
    ]
    
    node_processes = []
    for node in nodes:
        cmd = [
            sys.executable, "node_visualized.py",  # Используем модифицированную версию
            "--id", node["id"],
            "--pos", node["pos"]
        ]
        
        if node.get("packets"):
            cmd.extend(["--packets", node["packets"]])
        if node.get("sink"):
            cmd.append("--sink")
        
        # Запускаем в новом окне
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        node_processes.append(process)
        time.sleep(1.5)
    
    print(f"\n✅ Запущено {len(nodes)} узлов и визуализатор")
    print("\n" + "=" * 60)
    print("ВИЗУАЛИЗАТОР ЗАПУЩЕН")
    print("- Зеленые кружки: пакеты есть")
    print("- Красные кружки: пакетов нет")
    print("- Черная рамка: сток (узел E)")
    print("- Синие линии: возможные связи")
    print("- Красные линии: активная передача")
    print("\nКнопки управления:")
    print("- 'Следующая симуляция' - показать другой сценарий")
    print("- 'Обновить' - обновить отображение")
    print("- 'Сбросить' - вернуться к началу")
    print("=" * 60)
    
    return visualizer_process, node_processes

if __name__ == "__main__":
    visualizer, nodes = launch_all()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nЗавершение работы...")
        # Завершаем все процессы
        for node in nodes:
            node.terminate()
        visualizer.terminate()
        print("Все процессы завершены")