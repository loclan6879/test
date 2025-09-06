#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate video previews for EverLiving
Tạo lại các file preview GIF cho video
"""

import os
import sys
from moviepy.editor import VideoFileClip
import warnings
warnings.filterwarnings('ignore')

def generate_video_preview(video_path, output_path, duration=3, width=300, fps=8):
    """
    Tạo preview GIF từ video
    Args:
        video_path: Đường dẫn video gốc
        output_path: Đường dẫn output GIF
        duration: Thời lượng preview (giây)
        width: Chiều rộng GIF
        fps: Frame per second
    """
    try:
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        
        # Load video
        clip = VideoFileClip(video_path)
        
        # Lấy preview từ giây thứ 1 (bỏ qua frame đầu có thể đen)
        start_time = min(1.0, clip.duration * 0.1)  # Bắt đầu từ 10% video hoặc 1s
        end_time = min(start_time + duration, clip.duration)
        
        if end_time <= start_time:
            end_time = min(clip.duration, start_time + 1)  # Ít nhất 1 giây
        
        # Tạo subclip
        preview_clip = clip.subclip(start_time, end_time)
        
        # Resize để tối ưu size
        preview_clip = preview_clip.resize(width=width)
        
        # Tạo GIF
        preview_clip.write_gif(output_path, fps=fps, verbose=False, logger=None)
        
        # Cleanup
        clip.close()
        preview_clip.close()
        
        # Kiểm tra file size
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Created: {os.path.basename(output_path)} ({file_size:,} bytes)")
            return True
        else:
            print(f"❌ Failed to create: {os.path.basename(output_path)}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(video_path)}: {e}")
        return False

def regenerate_all_previews():
    """
    Tạo lại tất cả preview cho user1
    """
    username = "user1"
    videos_dir = f"storage/{username}/videos"
    previews_dir = f"storage/{username}/videos/previews"
    # No longer need static previews directory - serve directly from E drive
    
    # Tạo thư mục nếu chưa có
    os.makedirs(previews_dir, exist_ok=True)
    
    if not os.path.exists(videos_dir):
        print(f"❌ Videos directory not found: {videos_dir}")
        return
    
    # Lấy danh sách video
    video_extensions = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv')
    video_files = [f for f in os.listdir(videos_dir) if f.lower().endswith(video_extensions)]
    
    if not video_files:
        print(f"❌ No video files found in {videos_dir}")
        return
    
    print(f"🎯 Found {len(video_files)} video files")
    print(f"📁 Output directory: {previews_dir}")
    print(f"📁 Static directory: {static_previews_dir}")
    print("=" * 60)
    
    success_count = 0
    
    for video_file in video_files:
        video_path = os.path.join(videos_dir, video_file)
        
        # Tạo tên preview
        preview_name = f"upload_preview_{video_file.rsplit('.', 1)[0]}.gif"
        preview_path = os.path.join(previews_dir, preview_name)
        static_preview_path = os.path.join(static_previews_dir, preview_name)
        
        # Generate preview
        if generate_video_preview(video_path, preview_path):
            # Copy to static folder
            try:
                import shutil
                shutil.copy2(preview_path, static_preview_path)
                print(f"📋 Copied to static: {preview_name}")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to copy to static: {e}")
        
        print("-" * 40)
    
    print(f"🎉 Completed! Generated {success_count}/{len(video_files)} previews")

if __name__ == "__main__":
    print("🚀 EverLiving Video Preview Generator")
    print("=" * 60)
    regenerate_all_previews()
