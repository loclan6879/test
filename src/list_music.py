import os

# Liệt kê nhạc
MUSIC_FOLDER = "./music"
music_files = [f for f in os.listdir(MUSIC_FOLDER) 
               if f.endswith(('.mp3', '.wav', '.aac', '.m4a', '.flac'))]

print("🎵 DANH SÁCH NHẠC CÓ SẴN:")
print("=" * 40)
for i, music in enumerate(music_files, 1):
    print(f"{i}. {music}")

print(f"\nTổng cộng: {len(music_files)} file nhạc")
print("\nĐể chọn nhạc khác, sửa dòng sau trong bot.py:")
print("selected_music = music_files[0]  # Đổi số 0 thành số khác")
