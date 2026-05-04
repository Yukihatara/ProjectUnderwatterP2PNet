from Parser import *

_data_dir = 'Data'
_packages_dir = 'Packages'
_package_size = 60

print("=== РЕЖИМ РАЗБИЕНИЯ ===")
process_all_data(_data_dir, _packages_dir, _package_size)
    
# from pathlib import Path

# package_file = Path('Packages/00001/00012.bin')
# print(f"package_file: {package_file}")

# output_path = Path('Packages/00001/blablabla.txt')

# with open(output_path, 'wb') as op:
#     with open(package_file, 'rb') as pkg:
#         op.write(pkg.read())
        
