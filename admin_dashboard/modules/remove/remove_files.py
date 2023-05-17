"""
@created at 2023.05.17
@author OKS in Aimdat Team
"""
import os
import shutil

def remove_files(file_path, folder=False):
    """
    사용한 파일 제거
    """
    if folder:
        try:
            shutil.rmtree(file_path)
        except OSError:
            pass
    else:
        try:
            os.remove(file_path)
        except OSError:
            pass