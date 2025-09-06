import os

def list_and_select_music():
    """Liệt kê và cho phép chọn nhạc"""
    MUSIC_FOLDER = "./music"
    
    if not os.path.exists(MUSIC_FOLDER):
        print(f"Thư mục nhạc không tồn tại: {MUSIC_FOLDER}")
        return None
    
    music_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.flac']
    music_files = [f for f in os.listdir(MUSIC_FOLDER) 
                   if os.path.splitext(f)[1].lower() in music_extensions]
    
    if not music_files:
        print("Không có file nhạc nào!")
        return None
    
    print(f"\n📀 Danh sách nhạc có sẵn ({len(music_files)} file):")
    print("=" * 50)
    for i, music_file in enumerate(music_files, 1):
        print(f"  {i}. {music_file}")
    
    print("\n🎵 Hướng dẫn sử dụng:")
    print("- Sao chép tên file nhạc bạn muốn")
    print("- Dán vào biến SELECTED_MUSIC trong bot.py")
    print("- Hoặc thay đổi logic trong hàm select_music()")
    
    print(f"\n📁 Đường dẫn thư mục nhạc: {os.path.abspath(MUSIC_FOLDER)}")
    return music_files

if __name__ == "__main__":
    list_and_select_music()
