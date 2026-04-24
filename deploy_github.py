import os
import subprocess
import sys

def run_command(command):
    print(f"⏳ Đang chạy: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        # Ignore error if it's just "remote origin already exists" or "nothing to commit"
        if "already exists" in result.stderr or "nothing to commit" in result.stdout:
            return True
        print(f"❌ LỖI: {result.stderr}")
        return False
    else:
        print(f"✅ OK")
        return True

def deploy_to_github():
    print("==================================================")
    print("🚀 TUBEAUTO ULTIMATE - GITHUB DEPLOYMENT TOOL")
    print("==================================================")
    repo_url = "https://github.com/duchoanganh/toolyoutube.git"
    
    # Kiểm tra Git
    print("Kiểm tra Git trên hệ thống...")
    if subprocess.run("git --version", shell=True, capture_output=True).returncode != 0:
        print("❌ THẤT BẠI: Máy tính của bạn chưa cài đặt Git hoặc Git chưa có trong biến môi trường PATH.")
        print("👉 Hướng dẫn: ")
        print("   1. Tải Git tại: https://git-scm.com/downloads")
        print("   2. Cài đặt (nhấn Next liên tục)")
        print("   3. Mở lại terminal và chạy lại file này.")
        print("--------------------------------------------------")
        print("💡 CÁCH THỦ CÔNG: Bạn cũng có thể vào thẳng link https://github.com/duchoanganh/toolyoutube")
        print("   và chọn 'Add file' -> 'Upload files' rồi kéo thả các file Code vào nhé!")
        sys.exit(1)

    commands = [
        "git init",
        "git add .",
        'git commit -m "🚀 Bản phát hành đầu tiên: TubeAuto Ultimate AI Studio"',
        "git branch -M main",
        f"git remote add origin {repo_url}",
        f"git remote set-url origin {repo_url}", # Chắc chắn trỏ đúng repo
        "git push -u origin main -f"
    ]

    for cmd in commands:
        if not run_command(cmd):
            print("\n❌ Quá trình push code lên Github đã dừng lại do lỗi bên trên.")
            print("👉 Vui lòng đảm bảo bạn đã đăng nhập tài khoản Github trên máy tính.")
            sys.exit(1)

    print("\n🎉 XUẤT SẮC! Toàn bộ mã nguồn đã được tải lên: " + repo_url)
    print("Mọi người giờ đây có thể tải về và sử dụng hệ thống của bạn!")

if __name__ == "__main__":
    deploy_to_github()
