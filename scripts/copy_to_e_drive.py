import shutil
import os

# Source và destination paths
source = r"F:\EverTrace\static\user_files"
destination = r"C:\EverLiving_Storage"

print(f"Copying from: {source}")
print(f"Copying to: {destination}")

try:
    # Tạo thư mục đích nếu chưa có
    os.makedirs(destination, exist_ok=True)
    
    # Copy từng item
    for item in os.listdir(source):
        source_path = os.path.join(source, item)
        dest_path = os.path.join(destination, item)
        
        if os.path.isdir(source_path):
            print(f"Copying directory: {item}")
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        else:
            print(f"Copying file: {item}")
            shutil.copy2(source_path, dest_path)
    
    print("✅ Copy completed successfully!")
    
    # Verify copied files
    print("\n📁 Contents of E drive:")
    for item in os.listdir(destination):
        print(f"  - {item}")
        
except Exception as e:
    print(f"❌ Error: {e}")
