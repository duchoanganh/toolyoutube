from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import requests
import time
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
from moviepy.editor import ImageClip, VideoFileClip
import zipfile
import shutil
import json
import sys
import subprocess

app = Flask(__name__)
CORS(app) # Cho phép Backend nhận request từ Frontend

OUTPUT_FILENAME = "CapCut_Export.zip"
TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)

def download_file(url, prefix):
    try:
        if not url.startswith("http"):
            return None
        
        ext = ".jpg" if ("photo" in url or "image" in url or "picsum" in url) else ".mp4"
        filename = os.path.join(TEMP_DIR, f"{prefix}{ext}")
        
        # Nếu đã tải rồi thì tái sử dụng
        if os.path.exists(filename):
            pass 
            
        print(f"  Downloading: {url}...")
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return filename
    except Exception as e:
        print(f"  Error download {url}: {e}")
        return None

@app.route('/api/render', methods=['POST'])
def render_video():
    data = request.json
    print("========================================")
    print("      NHẬN DỰ ÁN TỪ TUBE-AUTO STUDIO    ")
    
    scenes = data.get('scenes', [])
    sources = data.get('selectedSources', {})
    total_scenes = data.get('totalScenes')
    
    print(f"Tổng số cảnh: {total_scenes}")
    print("\n   ĐANG XUẤT TÀI NGUYÊN CHO CAPCUT...")
    
    export_dir = "CapCut_Export_Folder"
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir)
    
    def format_time(seconds):
        ms = int((seconds % 1) * 1000)
        s = int(seconds)
        m = s // 60
        h = m // 60
        return f"{h:02d}:{m%60:02d}:{s%60:02d},{ms:03d}"
        
    file_counter = 1
    srt_content = ""
    current_time = 0.0
    
    for scene in scenes:
        sid = str(scene['id'])
        duration = float(scene['duration'])
        text = scene.get('text', f'Cảnh {sid}')
        
        # Build SRT block
        srt_content += f"{file_counter}\n"
        srt_content += f"{format_time(current_time)} --> {format_time(current_time + duration)}\n"
        srt_content += f"{text}\n\n"
        
        current_time += duration
        
        src_info = sources.get(sid)
        if not src_info:
            print(f" - Cảnh {sid}: Bị bỏ trống.")
            file_counter += 1
            continue
            
        url = src_info['src']
        media_type = src_info['type']
        
        local_path = download_file(url, f"temp_scene_{sid}_{int(time.time())}")
        
        if local_path:
            ext = ".jpg" if local_path.endswith(".jpg") else ".mp4"
            new_filename = f"{file_counter:02d}.mp4"
            new_path = os.path.join(export_dir, new_filename)
            
            try:
                print(f"   -> Đang đồng bộ thời lượng {duration}s cho {new_filename}...")
                if ext == ".jpg":
                    clip = ImageClip(local_path).set_duration(duration)
                    clip = clip.resize(newsize=(1280, 720))
                    clip.write_videofile(new_path, fps=24, codec="libx264", preset="ultrafast", audio=False, verbose=False, logger=None)
                    clip.close()
                else:
                    clip = VideoFileClip(local_path)
                    if clip.duration < duration:
                        clip = clip.loop(duration=duration)
                    else:
                        clip = clip.subclip(0, duration)
                    clip = clip.resize(newsize=(1280, 720)).without_audio()
                    clip.write_videofile(new_path, fps=24, codec="libx264", preset="ultrafast", audio=False, verbose=False, logger=None)
                    clip.close()
                print(f" - Đã đồng bộ thành công {new_filename}")
            except Exception as e:
                print(f" [LỖI] Không thể xử lý Cảnh {sid}: {e}")
                
        file_counter += 1
        
    # Ghi file SRT phụ đề
    with open(os.path.join(export_dir, "PhuDe_Chuan_CapCut.srt"), "w", encoding="utf-8") as f:
        f.write(srt_content)
            
    # Tạo thêm file hướng dẫn cho CapCut
    with open(os.path.join(export_dir, "Huong_Dan_CapCut.txt"), "w", encoding="utf-8") as f:
        f.write("HƯỚNG DẪN ĐƯA VÀO CAPCUT:\n")
        f.write("1. Mở CapCut PC/Mobile.\n")
        f.write("2. Kéo toàn bộ các file media trong thư mục này vào phần Local Media của CapCut.\n")
        f.write("3. Chọn tất cả các file (từ 01 đến hết) và kéo xuống Timeline cùng 1 lúc.\n")
        f.write("4. Kéo file PhuDe_Chuan_CapCut.srt vào Timeline để có phụ đề khớp chuẩn 100% thời gian!\n")

    # Zip thư mục lại
    print("\n   [RENDER] Đang nén thành file ZIP...")
    with zipfile.ZipFile(OUTPUT_FILENAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)
                
    print("   [OK] Đã xuất thành công gói tài nguyên CapCut!")
        
    return jsonify({
        "status": "success",
        "message": "Kết nối thành công. Đã xuất nén ZIP cho CapCut!",
        "video_url": "http://127.0.0.1:5000/api/download",
    })

@app.route('/api/download', methods=['GET'])
def download_video():
    if os.path.exists(OUTPUT_FILENAME):
        return send_file(OUTPUT_FILENAME, as_attachment=True, download_name="CapCut_Assets.zip", mimetype="application/zip")
    return "Lỗi: Không tìm thấy render.", 404

@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    target_dir = os.path.abspath("CapCut_Export_Folder")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    try:
        if sys.platform == 'win32':
            os.startfile(target_dir)
        elif sys.platform == 'darwin':
            subprocess.call(["open", target_dir])
        else:
            subprocess.call(["xdg-open", target_dir])
        return jsonify({"status": "success", "message": "Đã mở thư mục"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("   Bắt đầu Backend MoviePy API Render Engine ở port 5000...")
    app.run(host='127.0.0.1', port=5000)
