import os
import time

# Получаем путь к папке, где находится текущий скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
filename = 'example.txt'
filepath = os.path.join(script_dir, filename)

print(f'Скрипт находится в: {script_dir}')
print(f'Файл будет создан по пути: {filepath}')

if os.path.exists(filepath):
    with open(filepath, 'w') as file:
        print(f'Файл {filename} очищен')
else:
    with open(filepath, 'w') as file:
        
        print(f'Файл {filename} создан в папке со скриптом')
        pass # Очистка или перезапись
        
        
with open(filepath, 'a', encoding='utf-8') as file:
    while True:
        file.write('Добавил информацию')
        time.sleep(10)
    