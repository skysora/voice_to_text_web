
import zipfile
import os
from web.module.emotion import *


def add_folder_to_zip(zipf, folder_path, base_folder):
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(file_path, base_folder)
            zipf.write(file_path, arcname=relative_path)