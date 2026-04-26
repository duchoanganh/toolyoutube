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
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import send_from_directory

app = Flask(__name__)
CORS(app) # Cho phép Backend nhận request từ Frontend

# === CƠ SỞ DỮ LIỆU SQLITE NỘI BỘ ===
DATABASE = 'tubeauto.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                theme TEXT,
                status TEXT DEFAULT 'Bản nháp',
                script TEXT,
                scenes_data TEXT,
                selected_sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()
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
    
    images_dir = os.path.join(export_dir, "Images")
    videos_dir = os.path.join(export_dir, "Videos")
    os.makedirs(images_dir)
    os.makedirs(videos_dir)
    
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
            ext = ".jpg" if local_path.lower().endswith(".jpg") or local_path.lower().endswith(".png") or local_path.lower().endswith(".jpeg") else ".mp4"
            
            try:
                if ext == ".jpg":
                    new_filename = f"{file_counter:02d}_scene.jpg"
                    new_path = os.path.join(images_dir, new_filename)
                    shutil.copy(local_path, new_path)
                    print(f" - Đã chép file ảnh {new_filename} vào thư mục Images/")
                else:
                    new_filename = f"{file_counter:02d}_scene.mp4"
                    new_path = os.path.join(videos_dir, new_filename)
                    print(f"   -> Đang đồng bộ thời lượng {duration}s cho video {new_filename}...")
                    clip = VideoFileClip(local_path)
                    if clip.duration < duration:
                        clip = clip.loop(duration=duration)
                    else:
                        clip = clip.subclip(0, duration)
                    clip = clip.resize(newsize=(1280, 720)).without_audio()
                    clip.write_videofile(new_path, fps=24, codec="libx264", preset="ultrafast", audio=False, verbose=False, logger=None)
                    clip.close()
                    print(f" - Đã xuất thành công video {new_filename} vào thư mục Videos/")
            except Exception as e:
                print(f" [LỖI] Không thể xử lý Cảnh {sid}: {e}")
                # Fallback copy
                fallback_filename = f"{file_counter:02d}_scene{ext}"
                shutil.copy(local_path, os.path.join(export_dir, fallback_filename))
                
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

@app.route('/temp_media/<path:filename>')
def serve_temp_media(filename):
    return send_from_directory(TEMP_DIR, filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    if file:
        filename = secure_filename(f"upload_{int(time.time())}_{file.filename}")
        filepath = os.path.join(TEMP_DIR, filename)
        file.save(filepath)
        file_url = f"http://127.0.0.1:5000/temp_media/{filename}"
        return jsonify({"status": "success", "url": file_url})

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

# ==========================================
# DATABASE ENDPOINTS FOR PROJECTS
# ==========================================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    conn = get_db()
    projects = conn.execute('SELECT id, name, theme, status, created_at, updated_at FROM projects ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(p) for p in projects])

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    name = data.get('name', 'Dự án không tên')
    theme = data.get('theme', 'Chưa phân loại')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO projects (name, theme, script, scenes_data, selected_sources) VALUES (?, ?, ?, ?, ?)',
                   (name, theme, '', '[]', '{}'))
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return jsonify({"status": "success", "id": project_id, "name": name, "theme": theme})

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()
    if project:
        return jsonify(dict(project))
    return jsonify({"status": "error", "message": "Không tìm thấy dự án"}), 404

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.json
    script = data.get('script')
    scenes_data = data.get('scenes_data') # stringified JSON
    selected_sources = data.get('selected_sources') # stringified JSON
    status = data.get('status')
    
    # Chỉ update những trường được gửi lên
    update_fields = []
    params = []
    
    if script is not None:
        update_fields.append("script = ?")
        params.append(script)
    if scenes_data is not None:
        update_fields.append("scenes_data = ?")
        params.append(scenes_data)
    if selected_sources is not None:
        update_fields.append("selected_sources = ?")
        params.append(selected_sources)
    if status is not None:
        update_fields.append("status = ?")
        params.append(status)
        
    if not update_fields:
        return jsonify({"status": "success", "message": "Không có gì để update"})
        
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(project_id)
    
    query = f"UPDATE projects SET {', '.join(update_fields)} WHERE id = ?"
    
    conn = get_db()
    conn.execute(query, params)
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    print("   Bắt đầu Backend MoviePy API Render Engine ở port 5000...")
    app.run(host='127.0.0.1', port=5000)
