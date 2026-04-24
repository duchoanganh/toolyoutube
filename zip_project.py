import os
import zipfile

def zip_project():
    output_filename = "TubeAuto-Ultimate-SourceCode.zip"
    exclude_dirs = {'venv', '__pycache__', 'CapCut_Export_Folder', '.pytest_cache', '.git'}
    exclude_exts = {'.pyc', '.zip', '.mp4'}
    
    print(f"Đang đóng gói mã nguồn thành {output_filename}...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, ".")
                zipf.write(file_path, arcname)

    print(f"Hoàn tất! File được lưu tại: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    zip_project()
