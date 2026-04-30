# viewer.py
import os
from PIL import Image
from pathlib import Path
import matplotlib.pyplot as plt

def view_packages_info(packages_dir):
    """Просмотр информации о созданных пакетах"""
    
    packages_path = Path(packages_dir)
    
    if not packages_path.exists():
        print(f"Папка {packages_dir} не существует!")
        return
    
    print(f"Анализ пакетов в: {packages_dir}")
    print("="*50)
    
    total_packages = 0
    package_sizes = {}
    
    for subdir in packages_path.iterdir():
        if subdir.is_dir():
            packages = list(subdir.glob("*.png"))
            print(f"\nИзображение: {subdir.name}")
            print(f"Пакетов: {len(packages)}")
            
            for package in packages:
                img = Image.open(package)
                size = img.size
                if size not in package_sizes:
                    package_sizes[size] = 0
                package_sizes[size] += 1
                total_packages += 1
    
    print("\n" + "="*50)
    print(f"Всего пакетов: {total_packages}")
    print("\nРаспределение по размерам:")
    for size, count in sorted(package_sizes.items()):
        print(f"  {size[0]}x{size[1]} пикселей: {count} пакетов")

if __name__ == "__main__":
    view_packages_info("Packages")