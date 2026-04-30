import os
from pathlib import Path

def split_data_to_packages(data_path, output_base_dir, package_size_bytes=1024):
    """
    Разбивает изображение на пакеты фиксированного размера (кроме последнего)
    
    Args:
        data_path: путь к данным WindowsPath('Data/Habr-Info.txt')
        output_base_dir: базовая папка для всех пакетов 'Packeges'
        package_size_bytes: размер пакета в байтах
    """
    
    # Создаем базовую папку
    Path(output_base_dir).mkdir(parents=True, exist_ok=True)
    
    # Получаем имя файла без расширения и создаем подпапку с номером
    # Для удобства используем порядковый номер, но можно и имя файла
    image_name = Path(data_path).stem # Извлекаем имя файла без расширения 
    
    # Создаем уникальную папку для этого изображения
    # Нумеруем папки последовательно: 00001, 00002, 00003...
    existing_folders = [d for d in Path(output_base_dir).iterdir() if d.is_dir()]
    next_number = len(existing_folders) + 1
    package_dir = Path(output_base_dir) / f"{next_number:05d}"  # 00001, 00002, etc.
    package_dir.mkdir(parents=True)
    
    # Сохраняем информацию о соответствии папки и исходного файла
    manifest_file = package_dir / "_manifest.txt"
    with open(manifest_file, 'w') as f:
        f.write(f"original_file: {Path(data_path).name}\n")
        f.write(f"original_path: {data_path}\n")
        f.write(f"package_size: {package_size_bytes}\n")
    
    # Читаем и разбиваем файл
    with open(data_path, 'rb') as f:
        package_number = 1
        total_bytes = 0
        
        while True:
            # Читаем пакет
            package_data = f.read(package_size_bytes)
            if not package_data:  # Конец файла
                break
            
            # Сохраняем пакет
            package_name = f"{package_number:05d}.bin"  # 00001.bin, 00002.bin, ...
            package_path = package_dir / package_name
            
            with open(package_path, 'wb') as pkg_file:
                pkg_file.write(package_data)
            
            package_size = len(package_data)
            total_bytes += package_size
            
            status = "полный" if package_size == package_size_bytes else "последний (меньше)"
            print(f"  Пакет {package_number:05d}: {package_size} байт - {status}")
            
            package_number += 1
    
    print(f"\n✓ Изображение '{Path(data_path).name}' разбито на {package_number-1} пакетов")
    print(f"  Папка: {package_dir}")
    print(f"  Общий размер: {total_bytes} байт\n")
    
    return package_dir, package_number - 1

def process_all_data(data_dir='Data', packages_dir='Packages', package_size=1024):
    """
    Обрабатывает все данные в папке
    """
    data_path = Path(data_dir) # 'Data'
    
    if not data_path.exists():
        print(f"Папка '{data_dir}' не найдена!")
        return
    
    # Получаем все изображения
    data_extensions = ['.txt', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    data = []
    for ext in data_extensions:
        data.extend(data_path.glob(f"*{ext}"))
        
        # Система регистронезависимая поэтому только .txt, с учетом .TXT автоматически
        # data.extend(data_path.glob(f"*{ext.upper()}")) 
        
    # data: [WindowsPath('Data/Habr-Info.txt'), ...] для всех файлов
    
    if not data:
        print(f"В папке '{data_dir}' нет данных!")
        return
    
    print(f"Найдено файлов: {len(data)}")
    print("="*60)
    
    for i, data_path in enumerate(data, 1):
        print(f"\n[{i}/{len(data)}] Обработка: {data_path.name}")
        split_data_to_packages(data_path, packages_dir, package_size)
    
    print("="*60)
    print(f"Готово! Все изображения разбиты на пакеты в папке '{packages_dir}'")

"""

def main():
    # import argparse
    
    # parser = argparse.ArgumentParser(description='Разбиение изображений на пакеты фиксированного размера')
    # parser.add_argument('--mode', '-m', choices=['split', 'reconstruct', 'both'], 
    #                    default='split', help='Режим работы')
    # parser.add_argument('--input', '-i', default='Images', 
    #                    help='Папка с исходными изображениями (для split)')
    # parser.add_argument('--output', '-o', default='Packages', 
    #                    help='Папка для пакетов/восстановления')
    # parser.add_argument('--size', '-s', type=int, default=1024, 
    #                    help='Размер пакета в байтах')
    # parser.add_argument('--package-folder', '-p', 
    #                    help='Конкретная папка с пакетами для восстановления')
    
    # args = parser.parse_args()
    
    # if args.mode in ['split', 'both']:
    #     print("=== РЕЖИМ РАЗБИЕНИЯ ===")
    #     process_all_images(args.input, args.output, args.size)
    
    # if args.mode in ['reconstruct', 'both']:
    #     print("\n=== РЕЖИМ ВОССТАНОВЛЕНИЯ ===")
    #     if args.package_folder:
    #         reconstruct_image(args.package_folder)
    #     else:
    #         reconstruct_all_images(args.output)      

    
    _data_dir = 'Data'
    _packages_dir = 'Packages'
    _package_size = 60
    
    print("=== РЕЖИМ РАЗБИЕНИЯ ===")
    process_all_data(_data_dir, _packages_dir, _package_size)
    

if __name__ == "__main__":
    main()
    
"""    

def reconstruct_data(package_dir, output_path=None):
    """
    Восстанавливает данные из пакетов
    
    Args:
        package_dir: папка с пакетами
        output_path: путь для сохранения восстановленного файла
    """
    package_dir = Path(package_dir)
    
    if not package_dir.exists():
        print(f"Папка {package_dir} не найдена!")
        return False
    
    # Читаем манифест
    manifest_file = package_dir / "_manifest.txt"
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            for line in f:
                if line.startswith('original_file:'):
                    original_name = line.split(':')[1].strip()
    
    # Получаем все пакеты в правильном порядке
    package_files = sorted(package_dir.glob("*.bin"))
    
    if not package_files:
        print(f"В папке {package_dir} нет пакетов!")
        return False
    
    # Определяем имя выходного файла
    if output_path is None:
        if manifest_file.exists():
            output_path = package_dir / f"restored_{original_name}"
        else:
            output_path = package_dir / "restored_data.jpg"
    
    # Восстанавливаем файл простой конкатенацией
    with open(output_path, 'wb') as output_file:
        for pkg_file in package_files:
            with open(pkg_file, 'rb') as pkg:
                output_file.write(pkg.read())
    
    print(f"✓ данных восстановлено восстановлено: {output_path}")
    print(f"  Количество пакетов: {len(package_files)}")
    print(f"  Размер: {output_path.stat().st_size} байт")
    
    return True

def reconstruct_all_data(packages_dir='Packages'):
    """
    Восстанавливает все данные из пакетов
    """
    packages_path = Path(packages_dir)
    
    if not packages_path.exists():
        print(f"Папка '{packages_dir}' не найдена!")
        return
    
    # Находим все папки с пакетами (игнорируем системные файлы)
    package_folders = [d for d in packages_path.iterdir() if d.is_dir()]
    
    if not package_folders:
        print(f"В папке '{packages_dir}' нет папок с пакетами!")
        return
    
    print(f"Найдено наборов пакетов: {len(package_folders)}")
    print("="*60)
    
    for folder in package_folders:
        print(f"\nВосстановление: {folder.name}")
        reconstruct_data(folder)
    
    print("="*60)
    print("Готово! Все изображения восстановлены")
    


"""
    
def main():
    # import argparse
    
    # parser = argparse.ArgumentParser(description='Разбиение изображений на пакеты фиксированного размера')
    # parser.add_argument('--mode', '-m', choices=['split', 'reconstruct', 'both'], 
    #                    default='split', help='Режим работы')
    # parser.add_argument('--input', '-i', default='Images', 
    #                    help='Папка с исходными изображениями (для split)')
    # parser.add_argument('--output', '-o', default='Packages', 
    #                    help='Папка для пакетов/восстановления')
    # parser.add_argument('--size', '-s', type=int, default=1024, 
    #                    help='Размер пакета в байтах')
    # parser.add_argument('--package-folder', '-p', 
    #                    help='Конкретная папка с пакетами для восстановления')
    
    # args = parser.parse_args()   
    
    # if args.mode in ['reconstruct', 'both']:
    #     print("\n=== РЕЖИМ ВОССТАНОВЛЕНИЯ ===")
    #     if args.package_folder:
    #         reconstruct_image(args.package_folder)
    #     else:
    #         reconstruct_all_images(args.output)

    _packages_dir = 'Packages'
    # _output_path = '...'
    
    reconstruct_all_data(_packages_dir)

if __name__ == "__main__":
    main()
    
"""