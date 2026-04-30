import os
from pathlib import Path

def reconstruct_data(package_dir, output_path=None):
    """
    Восстанавливает данные из пакетов
    
    Args:
        package_dir: папка с пакетами
        output_path: путь для сохранения восстановленного файла
    """
    package_dir = Path(package_dir)
    
    print(f"package_dir: {package_dir}")
    
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
            output_path = package_dir / "restored_data.txt"
    
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
    packages_path = Path(packages_dir) # Packeges
    
    print(f"packages_path: {packages_path}")
    
    if not packages_path.exists():
        print(f"Папка '{packages_dir}' не найдена!")
        return
    
    # Находим все папки с пакетами (игнорируем системные файлы)
    package_folders = [d for d in packages_path.iterdir() if d.is_dir()]
    
    print(f"package_folders: {package_folders}")
    
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
    
    
def main():
    _packages_dir = 'Packages'
    reconstruct_all_data(_packages_dir)

if __name__ == "__main__":
    main()