# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import subprocess
import glob
import time

# Force UTF-8 encoding for stdout
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
# Set environment variable for proper encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'



from moviepy.editor import *
import random
import numpy as np
import datetime
import cv2
from PIL import Image
import warnings
import subprocess
import time
import tempfile
import urllib.parse
from pathlib import Path
import glob
warnings.filterwarnings('ignore')

# ================= AUDIO DOWNLOAD FUNCTIONS =================
def download_audio_from_url(url, output_folder=None):
    """
    Download audio từ YouTube, SoundCloud, Spotify URLs
    Args:
        url: URL của nhạc
        output_folder: Thư mục lưu file (mặc định là temp)
    Returns:
        Đường dẫn file audio đã download hoặc None nếu lỗi
    """
    try:
        if not output_folder:
            output_folder = tempfile.gettempdir()
        
        # Tạo tên file output dựa trên timestamp
        import time
        timestamp = int(time.time())
        output_template = os.path.join(output_folder, f"downloaded_audio_{timestamp}.%(ext)s")
        
        print(f"🎵 Downloading audio from: {url}")
        print(f"📁 Output folder: {output_folder}")
        
        # Cấu hình yt-dlp command (dùng python -m yt_dlp để chắc chắn chạy được)
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "--output", output_template,
            "--no-playlist",  # Chỉ download 1 video/track
            "--quiet",        # Giảm output verbose
            url
        ]
        print(f"🔧 Running command: {' '.join(cmd)}")
        # Chạy yt-dlp qua python module
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Tìm file đã download
            mp3_file = os.path.join(output_folder, f"downloaded_audio_{timestamp}.mp3")
            if os.path.exists(mp3_file):
                print(f"✅ Downloaded successfully: {mp3_file}")
                return mp3_file
            else:
                # Tìm file với pattern khác
                pattern = os.path.join(output_folder, f"downloaded_audio_{timestamp}.*")
                files = glob.glob(pattern)
                if files:
                    downloaded_file = files[0]
                    print(f"✅ Downloaded successfully: {downloaded_file}")
                    return downloaded_file
                else:
                    print(f"❌ Download completed but file not found")
                    return None
        else:
            print(f"❌ yt-dlp error: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ Download timeout after 120 seconds")
        return None
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return None

def is_supported_music_url(url):
    """
    Kiểm tra xem URL có được hỗ trợ không
    """
    supported_domains = [
        'youtube.com', 'youtu.be', 'm.youtube.com',
        'soundcloud.com', 'on.soundcloud.com',
        'spotify.com', 'open.spotify.com',
        'bandcamp.com'
    ]
    
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        
        # Loại bỏ www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return any(supported_domain in domain for supported_domain in supported_domains)
    except:
        return False

# ================= TIMER & LOGGING SYSTEM =================
class VideoTimer:
    """Hệ thống timing cho video processing"""
    def __init__(self):
        self.start_time = None
        self.phase_times = {}
        self.current_phase = None
        
    def start(self, operation="Video Processing"):
        """Bắt đầu đếm thời gian"""
        self.start_time = time.time()
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n⏰ [{current_time}] 🚀 BẮT ĐẦU: {operation}")
        print("="*60)
        
    def phase_start(self, phase_name):
        """Bắt đầu một phase mới"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        phase_start_time = time.time()
        
        if self.current_phase:
            # Kết thúc phase trước
            elapsed = phase_start_time - self.phase_times[self.current_phase]
            print(f"⏱️  [{current_time}] ✅ Hoàn thành: {self.current_phase} ({elapsed:.1f}s)")
            
        self.current_phase = phase_name
        self.phase_times[phase_name] = phase_start_time
        print(f"⏱️  [{current_time}] 🔄 Bắt đầu: {phase_name}")
        
    def phase_update(self, message):
        """Cập nhật tiến trình trong phase"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if self.current_phase:
            elapsed = time.time() - self.phase_times[self.current_phase]
            print(f"   [{current_time}] 📝 {message} (+{elapsed:.1f}s)")
        else:
            print(f"   [{current_time}] 📝 {message}")
            
    def finish(self):
        """Kết thúc và báo cáo tổng thời gian"""
        end_time = time.time()
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        if self.current_phase:
            # Kết thúc phase cuối
            elapsed = end_time - self.phase_times[self.current_phase]
            print(f"⏱️  [{current_time}] ✅ Hoàn thành: {self.current_phase} ({elapsed:.1f}s)")
            
        total_time = end_time - self.start_time
        minutes = int(total_time // 60)
        seconds = total_time % 60
        
        print("="*60)
        print(f"🎉 [{current_time}] ✅ HOÀN THÀNH VIDEO!")
        print(f"⏰ TỔNG THỜI GIAN: {minutes}:{seconds:05.2f} ({total_time:.1f} giây)")
        print("="*60)
        
        return total_time

# Khởi tạo timer global
video_timer = VideoTimer()

# ================= GPU DETECTION & SETUP =================
def check_gpu_availability():
    """Kiểm tra GPU NVIDIA có sẵn và CUDA support"""
    try:
        # Kiểm tra nvidia-smi command
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Kiểm tra FFmpeg có hỗ trợ h264_nvenc không
            ffmpeg_result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=10)
            if 'h264_nvenc' in ffmpeg_result.stdout:
                return True, "NVIDIA GPU detected with h264_nvenc support"
            else:
                return False, "NVIDIA GPU detected but h264_nvenc not available in FFmpeg"
        else:
            return False, "NVIDIA GPU not detected"
    except Exception as e:
        return False, f"GPU check failed: {str(e)}"

def log_gpu_status():
    """Log GPU status và khuyến nghị với performance optimization"""
    gpu_available, gpu_message = check_gpu_availability()
    if gpu_available:
        log(f"🚀 GPU Status: {gpu_message}")
        log("💡 GPU acceleration ENABLED - render sẽ nhanh hơn 5-10x")
        
        # Optimization tips
        try:
            # Get GPU memory info
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,memory.used,memory.free', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                memory_info = result.stdout.strip().split(', ')
                total_mem = int(memory_info[0])
                used_mem = int(memory_info[1])
                free_mem = int(memory_info[2])
                
                log(f"📊 GPU Memory: {free_mem}MB free / {total_mem}MB total")
                
                if free_mem > 3000:  # > 3GB free
                    log("🔥 Excellent GPU memory - Maximum performance mode enabled")
                elif free_mem > 1000:  # > 1GB free
                    log("✅ Good GPU memory - High performance mode enabled")
                else:
                    log("⚠️ Limited GPU memory - Standard performance mode")
                    
        except:
            log("📊 GPU Memory check failed - using default settings")
            
        return True
    else:
        log(f"⚠️ GPU Status: {gpu_message}")
        log("💡 GPU acceleration DISABLED - sử dụng CPU encoding")
        return False

def log_cpu_status():
    """Log CPU status và performance optimization cho 44 cores"""
    import multiprocessing
    try:
        import psutil
    except ImportError:
        log("⚠️ psutil not available - using basic CPU info")
        psutil = None
    
    try:
        cpu_count = multiprocessing.cpu_count()
        
        if psutil:
            memory_gb = round(psutil.virtual_memory().total / (1024**3))
            memory_available_gb = round(psutil.virtual_memory().available / (1024**3))
            log(f"🚀 CPU Status: {cpu_count} cores detected, {memory_gb}GB total RAM")
            log(f"💾 Available RAM: {memory_available_gb}GB / {memory_gb}GB")
        else:
            log(f"🚀 CPU Status: {cpu_count} cores detected")
        
        log("💡 CPU acceleration ENABLED - tối ưu cho hiệu suất cao")
        log("⚡ Mode: MAXIMUM PERFORMANCE với multi-threading tối đa")
        
        if cpu_count >= 40:
            log("🔥 EXCELLENT CPU - 40+ cores detected! Maximum optimization enabled")
        elif cpu_count >= 20:
            log("✅ POWERFUL CPU - 20+ cores detected! High performance mode")
        elif cpu_count >= 8:
            log("👍 GOOD CPU - 8+ cores detected! Standard optimization")
        else:
            log("⚠️ LIMITED CPU - <8 cores detected! Basic optimization")
        
        if psutil:
            if memory_gb >= 64:
                log("🚀 MASSIVE RAM - 64GB+ detected! Maximum buffer sizes enabled")
            elif memory_gb >= 32:
                log("✅ PLENTY RAM - 32GB+ detected! Large buffer optimization")
            elif memory_gb >= 16:
                log("👍 GOOD RAM - 16GB+ detected! Standard buffers")
            else:
                log("⚠️ LIMITED RAM - <16GB detected! Conservative settings")
        
        log(f"🎯 Optimization: x264 preset '{CPU_PRESET}', CRF {CPU_CRF}, {THREADS} threads")
        log(f"📊 Target quality: Very High (CRF {CPU_CRF}), Bitrate: {CPU_BITRATE}")
        log("🚀 RENDERING MODE: CPU MAXIMUM PERFORMANCE (GPU disabled)")
        
    except Exception as e:
        log(f"⚠️ CPU status check failed: {str(e)}")
        log("💻 Using default CPU settings")

def optimize_gpu_settings():
    """Tối ưu GPU settings dựa trên hardware"""
    try:
        global GPU_EXTRA_PARAMS
        
        # Check GPU memory for optimization
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            free_mem = int(result.stdout.strip())
            
            if free_mem > 3000:  # > 3GB free - Maximum performance
                log("🔥 MAXIMUM GPU memory detected - Optimizing for speed")
                # Thay đổi surfaces và async_depth cho maximum performance
                for i, param in enumerate(GPU_EXTRA_PARAMS):
                    if param == "-surfaces":
                        GPU_EXTRA_PARAMS[i+1] = "64"  # Maximum surfaces
                    elif param == "-async_depth":
                        GPU_EXTRA_PARAMS[i+1] = "8"   # Maximum async depth
                        
            elif free_mem > 1500:  # > 1.5GB free - High performance  
                log("⚡ HIGH GPU memory detected - Balanced optimization")
                # Giữ nguyên settings hiện tại (32 surfaces, 4 async_depth)
                pass
            else:  # Limited memory - Conservative
                log("🔧 LIMITED GPU memory - Conservative settings")
                for i, param in enumerate(GPU_EXTRA_PARAMS):
                    if param == "-surfaces":
                        GPU_EXTRA_PARAMS[i+1] = "16"  # Conservative surfaces
                    elif param == "-async_depth":
                        GPU_EXTRA_PARAMS[i+1] = "2"   # Conservative async depth
                
        return True
    except Exception as e:
        log(f"⚠️ GPU optimization failed: {str(e)}")
        return False

# ================= CẤU HÌNH THAM SỐ =================
INPUT_FOLDER = "./photos"       # Thư mục chứa ảnh và video
OUTPUT_FOLDER = "."             # Thư mục đầu ra
OUTRO_FOLDER = "./outro"        # 🆕 Thư mục chứa video outro

# Tạo tên file output với timestamp (format: hhmm_ddmm.mp4)
timestamp = datetime.datetime.now().strftime("%H%M_%d%m")
OUTPUT_FILENAME = f"{timestamp}.mp4" # Tên file output với timestamp
OUTPUT_VIDEO = OUTPUT_FILENAME   # Tên file output (tương thích)
MUSIC_FOLDER = "./music"        # Thư mục chứa nhạc
TARGET_DURATION = 90            # Tổng thời lượng mong muốn (giây) - tổng video output
MIN_DURATION = 75               # Thời lượng tối thiểu (giây)
MAX_VIDEO_MATERIALS_DURATION = 52  # Tổng thời lượng tối đa cho video nguyên liệu (giây)

# 🆕 ORIENTATION SETTINGS
RESOLUTION_HORIZONTAL = (1280, 720)    # 16:9 720p ngang
RESOLUTION_VERTICAL = (720, 1280)      # 9:16 720p dọc (TikTok/Reel)
RESOLUTION_SQUARE = (720, 720)         # 1:1 720p vuông (Instagram Post)
RESOLUTION = RESOLUTION_HORIZONTAL     # Mặc định ngang (sẽ được update)

FPS = 30                        # Số khung hình/giây (30fps cho smooth)
CODEC = "libx264"               # Video codec
AUDIO_CODEC = "aac"             # Audio codec
THREADS = 44                    # Sử dụng tất cả 44 cores của CPU mạnh mẽ (cập nhật từ 22)

# 🚀 CPU ACCELERATION SETTINGS - OPTIMIZED FOR 44 CORES & 128GB RAM
GPU_ENABLED = False             # Tắt GPU acceleration - sử dụng CPU mạnh mẽ
GPU_CODEC = "h264_nvenc"        # NVIDIA hardware encoder (GTX 1660 support)

# ================= MANUAL SELECTION SETTINGS =================
IS_MANUAL_SELECTION = False     # Flag để biết user có tự chọn file không
MANUAL_SELECTED_FILES = []      # List các file user đã chọn
GPU_PRESET = "p4"               # Balanced preset (p4=medium speed, good quality)
GPU_MULTIPASS = "disabled"      # Tắt multi-pass để tăng tốc
GPU_CRF = 20                    # Quality: 20=good quality nhưng nhanh hơn (thay vì 16)
GPU_BITRATE = "6M"              # Bitrate hợp lý cho 720p (giảm từ 10M xuống 6M)
GPU_EXTRA_PARAMS = [
    "-c:v", "h264_nvenc",       # Video codec
    "-preset", "p4",            # Balanced preset (p4=medium speed, good quality)
    "-tune", "ll",              # Low latency tuning (nhanh hơn hq)
    "-profile:v", "main",       # Main profile (nhanh hơn high)
    "-pix_fmt", "yuv420p",      # Pixel format (Windows compatibility)
    "-level:v", "4.0",          # H.264 level standard (4.0 thay vì 4.1)
    "-rc:v", "vbr",             # Variable bitrate standard mode (nhanh hơn vbr_hq)
    "-cq:v", "20",              # Constant quality 20 (balanced speed/quality)
    "-b:v", "6M",               # Video bitrate hợp lý cho 720p
    "-maxrate:v", "8M",         # Max bitrate thấp hơn
    "-bufsize:v", "12M",        # Buffer size nhỏ hơn
    "-spatial_aq", "0",         # Tắt spatial AQ để tăng tốc
    "-temporal_aq", "0",        # Tắt temporal AQ để tăng tốc
    "-rc-lookahead", "8",       # Look-ahead frames thấp để tăng tốc (giảm từ 32 xuống 8)
    "-bf", "0",                 # Tắt B-frames
    "-surfaces", "32",          # GPU surfaces ít hơn để tăng tốc (giảm từ 64 xuống 32)
    "-async_depth", "4",        # Async processing depth để tăng tốc
    "-c:a", "aac",              # Audio codec
    "-b:a", "192k",             # Audio bitrate standard (giảm từ 256k xuống 192k)
    "-movflags", "+faststart"   # Optimize for web playback
]

# 💻 CPU OPTIMIZATION SETTINGS - MAXIMUM PERFORMANCE FOR 44 CORES
CPU_CODEC = "libx264"                   # CPU codec tối ưu
CPU_PRESET = "faster"                   # Preset nhanh cho CPU mạnh (faster thay vì medium)
CPU_CRF = 18                            # Quality cao cho CPU (18 thay vì 23 mặc định)
CPU_BITRATE = "12M"                     # Bitrate cao hơn GPU vì CPU có thể handle
CPU_EXTRA_PARAMS = [
    "-c:v", "libx264",                  # Video codec tối ưu CPU
    "-preset", "faster",                # Preset nhanh cho CPU mạnh (44 cores)
    "-crf", "18",                       # Quality cao (18 = very good quality)
    "-profile:v", "high",               # High profile for best quality
    "-level:v", "4.2",                  # Level cao cho high bitrate
    "-pix_fmt", "yuv420p",              # Standard pixel format
    "-x264-params", "threads=44:thread-input=1:thread-lookahead=8", # Maximize thread usage
    "-tune", "film",                    # Optimize for high-quality video content
    "-bf", "3",                         # B-frames for better compression
    "-refs", "5",                       # Reference frames for quality
    "-me_method", "umh",                # Motion estimation for quality
    "-subq", "8",                       # Subpixel motion quality
    "-partitions", "+parti8x8+parti4x4+partp8x8+partb8x8", # All partition types
    "-direct-pred", "3",                # Auto direct prediction
    "-weightb", "1",                    # Weighted B-frames
    "-mixed-refs", "1",                 # Mixed references
    "-8x8dct", "1",                     # 8x8 DCT transform
    "-fast-pskip", "1",                 # Fast P-frame skip
    "-aq-mode", "2",                    # Adaptive quantization mode 2
    "-aq-strength", "1.0",              # AQ strength
    "-psy-rd", "1.0:0.15",              # Psychovisual rate-distortion
    "-b:v", "12M",                      # High bitrate for quality
    "-maxrate:v", "15M",                # Maximum bitrate
    "-bufsize:v", "24M",                # Large buffer for 128GB RAM
    "-c:a", "aac",                      # Audio codec
    "-b:a", "256k",                     # High quality audio
    "-movflags", "+faststart"           # Optimize for web playback
]

MIN_MATERIALS = 15               # Số nguyên liệu tối thiểu để chọn (tăng từ 12 lên 15)
MAX_MATERIALS = 30              # Số nguyên liệu tối đa để chọn
MAX_VIDEOS = 5                  # Số video tối đa
MIN_VIDEOS = 1                  # Số video tối thiểu (nếu có)
VIDEO_CLIP_DURATION = 10        # Thời lượng mỗi clip video (giây) - sẽ được random 8-12s
VIDEO_CLIP_GAP = 1              # Khoảng trống giữa các clip video (giây)
MIN_VIDEO_CLIP_DURATION = 8     # Thời lượng clip video tối thiểu (giây) - tăng từ 5s lên 8s
MAX_VIDEO_CLIP_DURATION = 12    # Thời lượng clip video tối đa (giây)
MAX_IMAGE_DURATION = 5          # Thời lượng ảnh tối đa (giây)
AUDIO_FADEIN = 2.0              # Fade in cho nhạc (giây)
AUDIO_FADEOUT = 5.0             # Fade out cho nhạc (giây) - khớp với outro
AUDIO_FADE_DURATION = 2.0       # Thời lượng fade in/out cho nhạc (giây)
MAX_IMAGES_PER_FRAME = 5        # Số ảnh tối đa trong 1 khung ghép

# ================= HIỆU ỨNG CHUYỂN CẢNH =================
TRANSITION_PROBABILITY = 0.3    # 30% tỉ lệ có hiệu ứng chuyển cảnh
TRANSITION_MIN_DURATION = 1.0   # Thời lượng tối thiểu hiệu ứng chuyển cảnh (giây)
TRANSITION_MAX_DURATION = 2.5   # Thời lượng tối đa hiệu ứng chuyển cảnh (giây)
MAX_TOTAL_DURATION = 100         # Thời lượng tối đa cho video (tính cả transitions)

# ================= OUTRO SETTINGS =================
OUTRO_DURATION = 5.0            # Thời lượng outro: fade out (giây)
# LOGO_TEXT = "EverLiving"        # Text logo (disabled - ImageMagick error)
# LOGO_COLOR = "blue"             # Màu logo (disabled)
# LOGO_FONTSIZE = 80              # Kích thước font (disabled)
# ===================================================

# Danh sách 20 hiệu ứng chuyển cảnh (không xoay vòng)
TRANSITION_EFFECTS = [
    "fade",           # 1. Mờ dần
    "slide_left",     # 2. Trượt từ trái
    "slide_right",    # 3. Trượt từ phải  
    "slide_up",       # 4. Trượt từ trên
    "slide_down",     # 5. Trượt từ dưới
    "push_left",      # 6. Đẩy sang trái
    "push_right",     # 7. Đẩy sang phải
    "push_up",        # 8. Đẩy lên trên
    "push_down",      # 9. Đẩy xuống dưới
    "zoom_in",        # 10. Thu phóng vào
    "zoom_out",       # 11. Thu phóng ra
    "crossfade",      # 12. Chồng mờ

    # ===== 20 HIỆU ỨNG MỚI (ƯU TIÊN FADE) =====
    "fade_in_out",    # 21. Fade in + fade out kết hợp
    "soft_fade",      # 22. Fade mềm mại hơn
    "double_fade",    # 23. Fade 2 lớp
    "fade_zoom",      # 24. Fade + zoom nhẹ
    "fade_slide",     # 25. Fade + slide nhẹ
    "dissolve",       # 26. Hòa tan
    "soft_dissolve",  # 27. Hòa tan mềm
    "blur_fade",      # 28. Fade với blur
    "gentle_slide",   # 29. Slide mềm mại
    "smooth_push",    # 30. Push mượt mà
    "soft_wipe",      # 31. Wipe mềm
    "fade_wipe",      # 32. Wipe + fade
    "elastic_fade",   # 33. Fade với easing
    "bounce_fade",    # 34. Fade với bounce nhẹ
    "scale_fade",     # 35. Scale + fade
    "alpha_blend",    # 36. Alpha blending mượt
    "gradient_fade",  # 37. Fade với gradient
    "feather_fade",   # 38. Fade với feather edge
    "soft_zoom",      # 39. Zoom mềm mại
    "gentle_morph"    # 40. Morph nhẹ nhàng
]
# =====================================================

# ================= AI FACE DETECTION & SCORING =================
def check_file_readable(image_path):
    """
    Kiểm tra file có thể đọc được không
    """
    try:
        if not os.path.exists(image_path):
            return False, "File không tồn tại"
        
        if not os.path.isfile(image_path):
            return False, "Không phải file"
            
        # Thử đọc vài bytes đầu
        with open(image_path, 'rb') as f:
            header = f.read(10)
            if len(header) < 10:
                return False, "File rỗng hoặc bị hỏng"
                
        return True, "OK"
    except Exception as e:
        return False, f"Lỗi đọc file: {str(e)}"

def detect_faces_and_score(image_path):
    """
    🥇 SUPER AI Face Detection: MediaPipe + Haar Cascade hybrid approach
    Sử dụng AI mạnh nhất để detect chính xác khuôn mặt
    """
    try:
        # Đọc ảnh với xử lý encoding UTF-8
        with open(image_path, 'rb') as f:
            file_bytes = np.frombuffer(f.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
        if img is None:
            return 0, 0, "Không thể đọc ảnh (format không hỗ trợ)"
        
        img_height, img_width = img.shape[:2]
        img_area = img_height * img_width
        
        # Resize if too large để optimize processing
        original_scale = 1.0
        if max(img.shape[:2]) > 1200:
            scale = 1200 / max(img.shape[:2])
            new_width = int(img.shape[1] * scale)
            new_height = int(img.shape[0] * scale)
            img_resized = cv2.resize(img, (new_width, new_height))
            original_scale = 1 / scale
        else:
            img_resized = img.copy()
        
        all_detections = []
        
        # ========== METHOD 1: MediaPipe (Google's AI - Most Accurate) ==========
        try:
            import mediapipe as mp
            
            mp_face_detection = mp.solutions.face_detection
            
            # Test với cả 2 models của MediaPipe
            models = [
                (0, 0.6, 'mediapipe_short'),    # Short-range model
                (1, 0.6, 'mediapipe_full'),     # Full-range model
            ]
            
            for model_sel, min_conf, method_name in models:
                try:
                    with mp_face_detection.FaceDetection(
                        model_selection=model_sel, 
                        min_detection_confidence=min_conf
                    ) as face_detection:
                        # Convert BGR to RGB for MediaPipe
                        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
                        results_mp = face_detection.process(img_rgb)
                        
                        if results_mp.detections:
                            for detection in results_mp.detections:
                                # Get bounding box
                                bbox = detection.location_data.relative_bounding_box
                                h_res, w_res = img_resized.shape[:2]
                                
                                x = int(bbox.xmin * w_res * original_scale)
                                y = int(bbox.ymin * h_res * original_scale) 
                                w = int(bbox.width * w_res * original_scale)
                                h = int(bbox.height * h_res * original_scale)
                                
                                confidence = detection.score[0]
                                
                                # Basic validation
                                face_area = w * h
                                size_ratio = face_area / img_area
                                
                                if (0.001 <= size_ratio <= 0.5 and 
                                    w >= 20 and h >= 20 and
                                    x >= 0 and y >= 0 and
                                    x + w <= img_width and y + h <= img_height):
                                    
                                    detection_data = {
                                        'bbox': (x, y, w, h),
                                        'confidence': confidence,
                                        'method': method_name,
                                        'size_ratio': size_ratio,
                                        'ai_type': 'mediapipe'
                                    }
                                    
                                    all_detections.append(detection_data)
                except Exception:
                    continue
        except ImportError:
            pass
        except Exception:
            pass
        
        # ========== METHOD 2: Enhanced Haar Cascade (Backup) ==========
        try:
            gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
            
            # CLAHE enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            cascades = [
                ('haar_default', cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
                ('haar_alt', cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'),
                ('haar_alt2', cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'),
            ]
            
            for name, path in cascades:
                try:
                    cascade = cv2.CascadeClassifier(path)
                    if cascade.empty():
                        continue
                    
                    # Conservative parameters để giảm false positive
                    for img_type, test_img in [('normal', gray), ('enhanced', enhanced)]:
                        faces = cascade.detectMultiScale(
                            test_img,
                            scaleFactor=1.08,
                            minNeighbors=4,
                            minSize=(25, 25),
                            maxSize=(test_img.shape[1]//2, test_img.shape[0]//2)
                        )
                        
                        for face in faces:
                            x, y, w, h = face
                            
                            # Scale back to original
                            x_orig = int(x * original_scale)
                            y_orig = int(y * original_scale)
                            w_orig = int(w * original_scale)
                            h_orig = int(h * original_scale)
                            
                            face_area = w_orig * h_orig
                            size_ratio = face_area / img_area
                            
                            if (0.001 <= size_ratio <= 0.4 and
                                w_orig >= 20 and h_orig >= 20 and
                                x_orig >= 0 and y_orig >= 0 and
                                x_orig + w_orig <= img_width and y_orig + h_orig <= img_height):
                                
                                confidence = 0.7 if name == 'haar_default' else 0.6
                                
                                detection_data = {
                                    'bbox': (x_orig, y_orig, w_orig, h_orig),
                                    'confidence': confidence,
                                    'method': f"{name}_{img_type}",
                                    'size_ratio': size_ratio,
                                    'ai_type': 'haar'
                                }
                                
                                all_detections.append(detection_data)
                except Exception:
                    continue
        except Exception:
            pass
        
        # ========== SMART VALIDATION & FILTERING ==========
        validated_faces = []
        
        for detection in all_detections:
            x, y, w, h = detection['bbox']
            
            # Extract face region for advanced validation
            if (y + h <= img_height and x + w <= img_width and y >= 0 and x >= 0):
                face_region = img[y:y+h, x:x+w]
                
                if face_region.size > 400:  # Only validate larger faces
                    face_gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
                    
                    # 1. Texture Analysis
                    texture_var = np.var(face_gray)
                    
                    # 2. Edge Analysis
                    edges = cv2.Canny(face_gray, 30, 100)
                    edge_ratio = np.sum(edges > 0) / edges.size
                    
                    # 3. Gradient Analysis
                    sobelx = cv2.Sobel(face_gray, cv2.CV_64F, 1, 0, ksize=3)
                    sobely = cv2.Sobel(face_gray, cv2.CV_64F, 0, 1, ksize=3)
                    gradient_strength = np.mean(np.sqrt(sobelx**2 + sobely**2))
                    
                    # MediaPipe detections get more lenient validation (since they're more accurate)
                    if detection['ai_type'] == 'mediapipe':
                        # More lenient for MediaPipe
                        is_valid = (
                            texture_var > 50 and
                            edge_ratio > 0.02 and 
                            gradient_strength > 5
                        )
                    else:
                        # Stricter for Haar Cascade
                        is_valid = (
                            texture_var > 100 and
                            edge_ratio > 0.03 and
                            gradient_strength > 8
                        )
                    
                    if is_valid:
                        detection['validation_score'] = (texture_var/100 + edge_ratio*10 + gradient_strength/10) / 3
                        validated_faces.append(detection)
                else:
                    # Small faces - accept if from MediaPipe
                    if detection['ai_type'] == 'mediapipe':
                        validated_faces.append(detection)
        
        # ========== INTELLIGENT NMS (Non-Maximum Suppression) ==========
        if validated_faces:
            # Sort by AI type priority (MediaPipe > Haar) and confidence
            validated_faces.sort(
                key=lambda x: (1 if x['ai_type'] == 'mediapipe' else 0, x['confidence']), 
                reverse=True
            )
            
            final_faces = []
            for detection in validated_faces:
                x, y, w, h = detection['bbox']
                is_duplicate = False
                
                for existing in final_faces:
                    ex, ey, ew, eh = existing['bbox']
                    
                    # IoU calculation
                    overlap_x = max(0, min(x + w, ex + ew) - max(x, ex))
                    overlap_y = max(0, min(y + h, ey + eh) - max(y, ey))
                    overlap_area = overlap_x * overlap_y
                    
                    area1 = w * h
                    area2 = ew * eh
                    union_area = area1 + area2 - overlap_area
                    
                    if union_area > 0:
                        iou = overlap_area / union_area
                        
                        # Lower threshold for better faces
                        threshold = 0.2 if detection['ai_type'] == 'mediapipe' else 0.3
                        
                        if iou > threshold:
                            is_duplicate = True
                            # Keep MediaPipe detection over Haar if available
                            if (detection['ai_type'] == 'mediapipe' and 
                                existing['ai_type'] == 'haar'):
                                final_faces[final_faces.index(existing)] = detection
                            break
                
                if not is_duplicate:
                    final_faces.append(detection)
        else:
            final_faces = []
        
        # ========== SCORING ==========
        num_faces = len(final_faces)
        
        if num_faces == 0:
            return 0, 0, "❌ Không phát hiện khuôn mặt (super-AI detection)"
        
        # Advanced scoring
        if num_faces == 1:
            face = final_faces[0]
            base_score = 30
            
            # AI type bonus
            ai_bonus = 8 if face['ai_type'] == 'mediapipe' else 5
            
            # Confidence bonus
            conf_bonus = min(10, face['confidence'] * 10)
            
            # Size bonus
            size_bonus = min(7, face['size_ratio'] * 100)
            
            face_score = base_score + ai_bonus + conf_bonus + size_bonus
        else:
            # Multiple faces
            base_score = 35
            
            # AI type bonus
            mediapipe_count = sum(1 for f in final_faces if f['ai_type'] == 'mediapipe')
            ai_bonus = mediapipe_count * 3
            
            # Average confidence bonus
            avg_confidence = np.mean([f['confidence'] for f in final_faces])
            conf_bonus = min(8, avg_confidence * 8)
            
            # Multi-face bonus
            multi_bonus = min(12, (num_faces - 1) * 4)
            
            face_score = base_score + ai_bonus + conf_bonus + multi_bonus
        
        face_score = min(40, max(0, int(face_score)))
        
        # Detailed report
        ai_types = [f['ai_type'] for f in final_faces]
        mediapipe_count = ai_types.count('mediapipe')
        haar_count = ai_types.count('haar')
        avg_conf = np.mean([f['confidence'] for f in final_faces])
        
        ai_info = []
        if mediapipe_count > 0:
            ai_info.append(f"MediaPipe:{mediapipe_count}")
        if haar_count > 0:
            ai_info.append(f"Haar:{haar_count}")
        
        detail = f"✅ {num_faces} faces ({'+'.join(ai_info)}, conf:{avg_conf:.2f})"
        if num_faces > 1:
            detail += f" [+{min(12, (num_faces - 1) * 4)} multi-bonus]"
        
        return num_faces, face_score, detail
        
    except Exception as e:
        return 0, 0, f"Lỗi Super-AI detection: {str(e)[:50]}"
        
    except Exception as e:
        return 0, 0, f"Lỗi AI detection: {str(e)[:50]}"

def calculate_image_quality_score(image_path):
    """
    Tính điểm chất lượng ảnh (độ rõ, độ sáng, màu sắc)
    
    Returns:
        tuple: (điểm_chất_lượng, chi_tiết)
    """
    try:
        # Đọc ảnh với xử lý encoding UTF-8
        with open(image_path, 'rb') as f:
            file_bytes = np.frombuffer(f.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
        if img is None:
            return 0, "Không thể đọc ảnh (format không hỗ trợ)"
        
        # 1. Độ rõ (Sharpness) - 15 điểm
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(15, laplacian_var / 100)  # Normalize, max 15
        
        # 2. Độ sáng (Brightness) - 15 điểm  
        brightness = np.mean(gray)
        # Điểm cao nhất khi brightness trong khoảng 80-180
        if 80 <= brightness <= 180:
            brightness_score = 15
        else:
            brightness_score = max(0, 15 - abs(brightness - 130) / 10)
        
        # 3. Cân bằng màu sắc - 20 điểm
        # Tính độ lệch chuẩn của các kênh màu
        b, g, r = cv2.split(img)
        color_balance = 20 - min(20, np.std([np.mean(b), np.mean(g), np.mean(r)]) / 5)
        
        total_quality = sharpness_score + brightness_score + color_balance
        detail = f"Rõ:{sharpness_score:.1f} Sáng:{brightness_score:.1f} Màu:{color_balance:.1f}"
        
        return total_quality, detail
        
    except Exception as e:
        return 0, f"Lỗi quality: {str(e)}"

def get_image_resolution_score(image_path):
    """
    Kiểm tra độ phân giải ảnh và tính điểm
    
    Returns:
        tuple: (điểm_độ_phân_giải, width, height, is_acceptable, reason)
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
        
        target_w, target_h = RESOLUTION  # 1280x720
        
        # Kiểm tra ảnh có đạt độ phân giải tối thiểu không (ít nhất 80% của 720p)
        min_acceptable_w = target_w * 0.8  # 1024
        min_acceptable_h = target_h * 0.8  # 576
        is_acceptable = (width >= min_acceptable_w and height >= min_acceptable_h)
        
        # Tạo lý do chi tiết
        if not is_acceptable:
            reason = f"Độ phân giải {width}x{height} < tiêu chuẩn tối thiểu {min_acceptable_w:.0f}x{min_acceptable_h:.0f} (80% của 720p)"
        else:
            reason = f"Độ phân giải {width}x{height} đạt chuẩn"
        
        # Tính điểm độ phân giải (0-10 điểm)
        if width >= target_w and height >= target_h:
            resolution_score = 10  # 720p hoặc cao hơn
        elif width >= target_w * 0.8 and height >= target_h * 0.8:
            resolution_score = 7   # 80% 720p
        elif width >= target_w * 0.6 and height >= target_h * 0.6:
            resolution_score = 4   # 60% 720p
        else:
            resolution_score = 1   # Quá nhỏ
        
        return resolution_score, width, height, is_acceptable, reason
        
    except Exception as e:
        return 0, 0, 0, False, f"Lỗi đọc ảnh: {str(e)}"

def calculate_total_image_score(image_path):
    """
    Tính tổng điểm ảnh từ tất cả tiêu chí
    
    Returns:
        tuple: (tổng_điểm, chi_tiết, is_acceptable, rejection_reason)
    """
    try:
        # Kiểm tra file có đọc được không
        can_read, read_error = check_file_readable(image_path)
        if not can_read:
            return 0, f"File error: {read_error}", False, f"File không đọc được: {read_error}"
        
        # 1. Điểm khuôn mặt (0-40 điểm)
        num_faces, face_score, face_detail = detect_faces_and_score(image_path)
        
        # 2. Điểm chất lượng (0-50 điểm)
        quality_score, quality_detail = calculate_image_quality_score(image_path)
        
        # 3. Điểm độ phân giải (0-10 điểm)
        resolution_score, width, height, resolution_ok, resolution_reason = get_image_resolution_score(image_path)
        
        # Tổng điểm
        total_score = face_score + quality_score + resolution_score
        
        # Kiểm tra tiêu chí loại ảnh và tạo lý do chi tiết
        rejection_reasons = []
        
        if total_score < 40:
            rejection_reasons.append(f"Điểm thấp {total_score:.1f}/40")
            
        if not resolution_ok:
            rejection_reasons.append(resolution_reason)
        
        is_acceptable = (total_score >= 40 and resolution_ok)
        rejection_reason = "; ".join(rejection_reasons) if rejection_reasons else "Đạt tiêu chuẩn"
        
        detail = f"Face:{face_score}({face_detail}) Quality:{quality_score:.1f}({quality_detail}) Res:{resolution_score}({width}x{height})"
        
        return total_score, detail, is_acceptable, rejection_reason
        
    except Exception as e:
        return 0, f"Lỗi tính điểm: {str(e)}", False, f"Lỗi xử lý: {str(e)}"

# =====================================================

def log(message):
    """Ghi log với timestamp - Fixed Unicode for Windows"""
    import sys
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] {message}")
    except UnicodeEncodeError:
        # Fallback cho Windows PowerShell
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(f"[{timestamp}] {safe_message}")

def generate_preview_thumbnail(video_path, output_dir):
    """
    Generate a preview thumbnail/GIF for uploaded videos
    Args:
        video_path: Path to the video file
        output_dir: Directory to save the preview
    Returns:
        Dict with success status and preview filename
    """
    try:
        if not os.path.exists(video_path):
            return {'success': False, 'message': 'Video file not found'}
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate preview filename
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        preview_filename = f"upload_preview_{video_name}.gif"
        preview_path = os.path.join(output_dir, preview_filename)
        
        # Load video with MoviePy
        video = VideoFileClip(video_path)
        
        # Get video duration and select clips
        duration = video.duration
        
        if duration <= 3:
            # Short video - use entire video
            preview_clip = video
        else:
            # Longer video - create a preview from first 3 seconds
            preview_clip = video.subclip(0, min(3, duration))
        
        # Resize to reasonable size for preview (max 320px width)
        if preview_clip.w > 320:
            preview_clip = preview_clip.resize(width=320)
        
        # Write as GIF with optimized settings
        preview_clip.write_gif(
            preview_path,
            fps=8,  # Lower FPS for smaller file size
            opt='OptimizePlus',  # Optimize for size
            fuzz=1  # Slight quality reduction for smaller size
        )
        
        # Clean up
        preview_clip.close()
        video.close()
        
        log(f"✅ Generated video preview: {preview_filename}")
        
        return {
            'success': True,
            'preview_filename': preview_filename,
            'preview_path': preview_path
        }
        
    except Exception as e:
        log(f"❌ Error generating video preview: {str(e)}")
        return {
            'success': False,
            'message': f'Error generating preview: {str(e)}'
        }

def create_transition(clip1, clip2, transition_type, duration=1.0):
    """
    Tạo hiệu ứng chuyển cảnh giữa 2 clips
    
    Args:
        clip1: Clip đầu tiên
        clip2: Clip thứ hai  
        transition_type: Loại hiệu ứng (từ TRANSITION_EFFECTS)
        duration: Thời lượng hiệu ứng (giây)
    
    Returns:
        Composite clip với hiệu ứng chuyển cảnh
    """
    w, h = RESOLUTION
    
    # ===== HIỆU ỨNG GỐC =====
    if transition_type == "fade":
        clip1_fade = clip1.crossfadeout(duration)
        clip2_fade = clip2.crossfadein(duration)
        return concatenate_videoclips([clip1_fade, clip2_fade])
    
    elif transition_type == "slide_left":
        clip2_slide = clip2.set_position(lambda t: (-w + w*t/duration, 0) if t < duration else (0, 0))
        return CompositeVideoClip([clip1, clip2_slide], size=RESOLUTION)
        
    elif transition_type == "slide_right":
        clip2_slide = clip2.set_position(lambda t: (w - w*t/duration, 0) if t < duration else (0, 0))
        return CompositeVideoClip([clip1, clip2_slide], size=RESOLUTION)
        
    elif transition_type == "slide_up":
        clip2_slide = clip2.set_position(lambda t: (0, -h + h*t/duration) if t < duration else (0, 0))
        return CompositeVideoClip([clip1, clip2_slide], size=RESOLUTION)
        
    elif transition_type == "slide_down":
        clip2_slide = clip2.set_position(lambda t: (0, h - h*t/duration) if t < duration else (0, 0))
        return CompositeVideoClip([clip1, clip2_slide], size=RESOLUTION)
        
    elif transition_type == "zoom_in":
        clip2_zoom = clip2.resize(lambda t: 0.1 + 0.9*t/duration if t < duration else 1.0)
        clip2_zoom = clip2_zoom.set_position('center')
        return CompositeVideoClip([clip1, clip2_zoom], size=RESOLUTION)
        
    elif transition_type == "zoom_out":
        clip1_zoom = clip1.resize(lambda t: 1.0 + 2.0*t/duration if t < duration else 3.0)
        clip1_zoom = clip1_zoom.set_position('center')
        return CompositeVideoClip([clip1_zoom, clip2], size=RESOLUTION)
        
    elif transition_type == "crossfade":
        clip1_fade = clip1.fadeout(duration)
        clip2_fade = clip2.fadein(duration)
        return CompositeVideoClip([clip1_fade, clip2_fade], size=RESOLUTION)
    
    # ===== 20 HIỆU ỨNG MỚI (ƯU TIÊN FADE) =====
    elif transition_type == "fade_in_out":
        # Fade in + fade out kết hợp với thời gian dài hơn
        clip1_fade = clip1.fadeout(duration * 0.7)
        clip2_fade = clip2.fadein(duration * 0.7)
        return concatenate_videoclips([clip1_fade, clip2_fade])
        
    elif transition_type == "soft_fade":
        # Fade mềm mại hơn với alpha thấp
        clip1_soft = clip1.crossfadeout(duration * 1.2)
        clip2_soft = clip2.crossfadein(duration * 1.2)
        return concatenate_videoclips([clip1_soft, clip2_soft])
        
    elif transition_type == "double_fade":
        # Fade 2 lớp với opacity khác nhau
        clip1_fade1 = clip1.fadeout(duration * 0.6)
        clip1_fade2 = clip1.fadeout(duration * 0.8)
        clip2_fade = clip2.fadein(duration)
        return CompositeVideoClip([clip1_fade1, clip1_fade2, clip2_fade], size=RESOLUTION)
        
    elif transition_type == "fade_zoom":
        # Fade + zoom nhẹ
        clip1_fade = clip1.fadeout(duration).resize(lambda t: 1.0 + 0.1*t/duration)
        clip2_fade = clip2.fadein(duration).resize(lambda t: 0.9 + 0.1*t/duration)
        return concatenate_videoclips([clip1_fade, clip2_fade])
        
    elif transition_type == "fade_slide":
        # Fade + slide nhẹ
        clip1_fade = clip1.fadeout(duration).set_position(lambda t: (-w*0.1*t/duration, 0))
        clip2_fade = clip2.fadein(duration).set_position(lambda t: (w*0.1*(1-t/duration), 0) if t < duration else (0, 0))
        return CompositeVideoClip([clip1_fade, clip2_fade], size=RESOLUTION)
        
    elif transition_type == "dissolve":
        # Hòa tan với opacity gradient
        clip1_dissolve = clip1.set_opacity(lambda t: 1.0 - t/duration if t < duration else 0)
        clip2_dissolve = clip2.set_opacity(lambda t: t/duration if t < duration else 1)
        return CompositeVideoClip([clip1_dissolve, clip2_dissolve], size=RESOLUTION)
        
    elif transition_type == "soft_dissolve":
        # Hòa tan mềm với thời gian dài hơn
        longer_duration = duration * 1.5
        clip1_soft = clip1.set_opacity(lambda t: 1.0 - t/longer_duration if t < longer_duration else 0)
        clip2_soft = clip2.set_opacity(lambda t: t/longer_duration if t < longer_duration else 1)
        return CompositeVideoClip([clip1_soft, clip2_soft], size=RESOLUTION)
        
    elif transition_type == "blur_fade":
        # Fade với blur (giả lập bằng resize)
        clip1_blur = clip1.fadeout(duration).resize(lambda t: 1.0 - 0.1*t/duration)
        clip2_blur = clip2.fadein(duration).resize(lambda t: 0.9 + 0.1*t/duration)
        return concatenate_videoclips([clip1_blur, clip2_blur])
        
    elif transition_type == "gentle_slide":
        # Slide mềm mại với easing
        clip2_gentle = clip2.set_position(lambda t: (-w * (1 - (t/duration)**2), 0) if t < duration else (0, 0))
        return CompositeVideoClip([clip1, clip2_gentle], size=RESOLUTION)
        
    elif transition_type == "smooth_push":
        # Push mượt mà với easing
        clip1_push = clip1.set_position(lambda t: (-w * (t/duration)**2, 0) if t < duration else (-w, 0))
        clip2_push = clip2.set_position(lambda t: (w * (1 - (t/duration)**2), 0) if t < duration else (0, 0))
        return CompositeVideoClip([clip1_push, clip2_push], size=RESOLUTION)
    
    # ===== FALLBACK CHO CÁC HIỆU ỨNG KHÁC =====
    else:
        # Fallback: fade đơn giản cho tất cả hiệu ứng còn lại
        clip1_fade = clip1.crossfadeout(duration)
        clip2_fade = clip2.crossfadein(duration)
        return concatenate_videoclips([clip1_fade, clip2_fade])

def apply_transitions_to_clips(clips):
    """
    Áp dụng hiệu ứng chuyển cảnh ngẫu nhiên cho danh sách clips
    Logic mới: Duyệt từng clip, random 30% cho mỗi lần chuyển, ngưng khi gần 100s
    
    Args:
        clips: Danh sách các clips
        
    Returns:
        Danh sách clips đã được áp dụng transitions (tối đa 100s)
    """
    video_timer.phase_update(f"Áp dụng transitions cho {len(clips)} clips")
    if len(clips) <= 1:
        return clips

    log(f"Bước 4.5: Áp dụng hiệu ứng chuyển cảnh")
    log(f"Có {len(clips)} clips → {len(clips)-1} lần chuyển cảnh có thể")
    log(f"Tỉ lệ random: {TRANSITION_PROBABILITY*100:.0f}% mỗi lần chuyển")
    log(f"Giới hạn tối đa: {MAX_TOTAL_DURATION}s")
    
    # Tính tổng thời lượng hiện tại (chưa có transitions)
    current_total_duration = sum(clip.duration for clip in clips)
    log(f"Thời lượng hiện tại: {current_total_duration:.1f}s (chưa có hiệu ứng)")
    
    final_clips = [clips[0]]  # Clip đầu tiên luôn được thêm
    transitions_applied = 0
    total_transition_time = 0.0
    
    # Duyệt từng clip và áp dụng transition giữa các clips
    for i in range(1, len(clips)):
        curr_clip = clips[i]  # Định nghĩa curr_clip ở đầu loop
        
        # Random 30% cho mỗi lần chuyển từ clip (i-1) → clip i
        should_add_transition = random.random() < TRANSITION_PROBABILITY
        
        if should_add_transition:
            # Random duration cho transition
            transition_duration = random.uniform(TRANSITION_MIN_DURATION, TRANSITION_MAX_DURATION)
            
            # Kiểm tra xem thêm transition có vượt quá 100s không
            estimated_total = current_total_duration + total_transition_time + transition_duration
            
            if estimated_total <= MAX_TOTAL_DURATION:
                # Chọn random hiệu ứng
                transition_type = random.choice(TRANSITION_EFFECTS)
                transitions_applied += 1
                total_transition_time += transition_duration
                
                # Log chi tiết
                new_total = current_total_duration + total_transition_time
                log(f"Clip {i} → {i+1}: ✅ {transition_type} ({transition_duration:.1f}s) - Tổng: {new_total:.1f}s")
                
                try:
                    # Tạo transition giữa clip trước và clip hiện tại
                    prev_clip = clips[i-1]
                    curr_clip = clips[i]
                    
                    # Tạo overlap để làm transition
                    overlap_duration = min(transition_duration, 
                                         prev_clip.duration * 0.3, 
                                         curr_clip.duration * 0.3)
                    
                    if overlap_duration > 0.1:  # Chỉ làm transition nếu đủ thời gian
                        # Tạo transition và thêm vào
                        prev_end = prev_clip.subclip(max(0, prev_clip.duration - overlap_duration))
                        curr_start = curr_clip.subclip(0, min(curr_clip.duration, overlap_duration))
                        
                        # Tạo transition
                        transition_clip = create_transition(prev_end, curr_start, transition_type, overlap_duration)
                        
                        # Ghép: [clip trước - overlap] + [transition] + [clip sau - overlap]
                        if i == 1:  # Clip đầu tiên cần được cắt
                            prev_main = prev_clip.subclip(0, max(0, prev_clip.duration - overlap_duration))
                            final_clips[-1] = prev_main  # Thay thế clip đầu
                            
                        final_clips.append(transition_clip)
                        
                        curr_main = curr_clip.subclip(min(curr_clip.duration, overlap_duration))
                        if curr_main.duration > 0.1:
                            final_clips.append(curr_main)
                        else:
                            final_clips.append(curr_clip)
                            
                    else:
                        # Không đủ thời gian cho transition, thêm clip bình thường
                        final_clips.append(curr_clip)
                        log(f"    ⚠️ Không đủ thời gian cho transition, bỏ qua")
                        
                except Exception as e:
                    # Nếu có lỗi, thêm clip bình thường
                    final_clips.append(curr_clip)
                    log(f"    ❌ Lỗi tạo transition: {str(e)}, dùng clip gốc")
            else:
                # Thêm transition sẽ vượt quá 100s
                final_clips.append(curr_clip)
                final_total = current_total_duration + total_transition_time
                log(f"Clip {i} → {i+1}: ⚠️ Dừng (gần chạm 100s) - Tổng hiện tại: {final_total:.1f}s")
                
                # Log các clip còn lại sẽ không có transition
                for j in range(i+1, len(clips)):
                    log(f"Clip {j} → {j+1}: ❌ Không có hiệu ứng (giới hạn 100s)")
                break
        else:
            # Không có hiệu ứng, thêm clip bình thường
            final_clips.append(curr_clip)
            current_total = current_total_duration + total_transition_time
            log(f"Clip {i} → {i+1}: ❌ Không có hiệu ứng - Tổng: {current_total:.1f}s")
    
    # Thêm các clip còn lại nếu loop bị break
    if len(final_clips) < len(clips):
        for remaining_i in range(len(final_clips), len(clips)):
            final_clips.append(clips[remaining_i])
    
    # Log kết quả cuối cùng
    final_total_duration = sum(clip.duration for clip in final_clips)
    log(f"• KẾT QUẢ: {transitions_applied}/{len(clips)-1} transitions được áp dụng")
    log(f"• THỜI LƯỢNG CUỐI: {final_total_duration:.1f}s")
    
    return final_clips

def add_outro_video(main_clip, outro_filename):
    """
    🆕 Thêm outro video thay thế logo
    Args:
        main_clip: VideoClip chính
        outro_filename: Tên file outro video (từ orientation selection)
    Returns:
        VideoClip với outro video được thêm vào
    """
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    
    try:
        outro_path = os.path.join(OUTRO_FOLDER, outro_filename)
        
        if not os.path.exists(outro_path):
            log(f"⚠️ File outro không tồn tại: {outro_path}")
            return main_clip
            
        log(f"Thêm outro video: {outro_filename}")
        
        # Load outro video
        outro_clip = VideoFileClip(outro_path)
        
        # 🔧 QUAN TRỌNG: Loại bỏ audio từ outro video để tránh conflict
        outro_clip = outro_clip.without_audio()
        
        # Resize outro video để match resolution hiện tại
        outro_clip = outro_clip.resize(RESOLUTION)
        
        # Giới hạn outro video tối đa 5s
        if outro_clip.duration > 5:
            outro_clip = outro_clip.subclip(0, 5)
            log(f"   Cắt outro video xuống 5s")
        
        log(f"   Outro duration: {outro_clip.duration:.1f}s (no audio)")
        
        # Nối main clip + outro clip (outro không có audio)
        final_video = concatenate_videoclips([main_clip, outro_clip])
        
        log(f"✅ Outro video hoàn thành: {final_video.duration:.1f}s")
        log(f"   {main_clip.duration:.1f}s main + {outro_clip.duration:.1f}s outro")
        
        # Clean up outro clip để giải phóng memory
        try:
            outro_clip.close()
            del outro_clip
        except:
            pass
        
        return final_video
        
    except Exception as e:
        log(f"❌ Lỗi thêm outro video: {str(e)}")
        return main_clip


def add_outro_effect(main_clip):
    """
    Thêm outro effect: Overlap transition trong 5s cuối
    - 0 đến (duration-5)s: Video bình thường  
    - (duration-5)s đến duration: Video fade out + Logo fade in đồng thời
    - Tổng duration: KHÔNG ĐỔI
    
    Args:
        main_clip: Video clip chính
        
    Returns:
        Video clip với outro overlap transition (cùng duration)
    """
    try:
        log(f"Thêm outro overlap trong 5s cuối: video fade out + logo fade in")
        
        # 1. Chia video thành 2 phần
        transition_start = max(0, main_clip.duration - OUTRO_DURATION)
        
        part1 = main_clip.subclip(0, transition_start)  # Phần bình thường
        part2 = main_clip.subclip(transition_start)     # 5s cuối để fade out
        
        log(f"   Phần 1 (normal): 0-{transition_start:.1f}s")
        log(f"   Phần 2 (transition): {transition_start:.1f}-{main_clip.duration:.1f}s")
        
        # 2. Tìm và load logo
        from moviepy.editor import ColorClip, CompositeVideoClip, ImageClip, concatenate_videoclips
        
        logo_folder = "./logo"
        logo_files = [f for f in os.listdir(logo_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if logo_files:
            logo_path = os.path.join(logo_folder, logo_files[0])
            log(f"   Logo: {logo_files[0]} fade in trong 5s cuối")
            
            # 3. Tạo nền trắng fade in cho 5s cuối
            white_background = ColorClip(size=RESOLUTION, color=(255, 255, 255), duration=OUTRO_DURATION)
            white_background = white_background.fadein(OUTRO_DURATION)
            
            # 4. Tạo logo fade in cho 5s cuối
            logo_clip = ImageClip(logo_path, duration=OUTRO_DURATION, transparent=True)
            logo_width = RESOLUTION[0] // 3
            logo_clip = logo_clip.resize(width=logo_width).set_position('center')
            logo_clip = logo_clip.fadein(OUTRO_DURATION)
            
            # 5. Composite 5s cuối: Video fade out + Nền trắng fade in + Logo fade in
            transition_part = CompositeVideoClip([
                part2.fadeout(OUTRO_DURATION),  # Video 5s cuối fade out
                white_background,               # Nền trắng fade in
                logo_clip                      # Logo fade in
            ], size=RESOLUTION)
            
            # 6. Nối: Phần bình thường + Phần transition
            final_clip = concatenate_videoclips([part1, transition_part])
            
            log(f"✅ Outro overlap hoàn thành: {final_clip.duration:.1f}s")
            log(f"   {transition_start:.1f}s normal + {OUTRO_DURATION:.1f}s overlap = {final_clip.duration:.1f}s")
            
            return final_clip
        else:
            log("⚠️ Không tìm thấy logo, chỉ dùng fade-out")
            # Fallback: fade out 5s cuối
            part1 = main_clip.subclip(0, transition_start)
            part2 = main_clip.subclip(transition_start).fadeout(OUTRO_DURATION)
            return concatenate_videoclips([part1, part2])
        
    except Exception as e:
        log(f"❌ Lỗi tạo outro: {str(e)}, dùng video gốc")
        return main_clip

def list_music_files():
    """Liệt kê các file nhạc có sẵn"""
    if not os.path.exists(MUSIC_FOLDER):
        log(f"Thư mục nhạc không tồn tại: {MUSIC_FOLDER}")
        return []
    
    music_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.flac']
    music_files = [f for f in os.listdir(MUSIC_FOLDER) 
                   if os.path.splitext(f)[1].lower() in music_extensions]
    
    log(f"Tìm thấy {len(music_files)} file nhạc:")
    for i, music_file in enumerate(music_files, 1):
        log(f"  {i}. {music_file}")
    
    return music_files

def detect_main_subject(image_path_or_array):
    """
    AI detect chủ thể chính trong ảnh (faces, people, important objects)
    
    Returns:
        dict với thông tin vùng quan trọng: {
            'faces': [(x, y, w, h), ...],
            'main_region': (x, y, w, h),  # Vùng bao quanh tất cả subjects
            'crop_center': (cx, cy)       # Điểm trung tâm tối ưu để crop
        }
    """
    try:
        # Load ảnh
        if isinstance(image_path_or_array, str):
            img = cv2.imread(image_path_or_array)
        else:
            img = image_path_or_array
            
        if img is None:
            return None
            
        h, w = img.shape[:2]
        
        # 1. Face Detection với OpenCV (fallback nếu không có MediaPipe)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # 2. Nếu có MediaPipe, dùng để detect faces tốt hơn
        detected_faces = []
        try:
            import mediapipe as mp
            mp_face_detection = mp.solutions.face_detection
            
            with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb_img)
                
                if results.detections:
                    for detection in results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        x = int(bbox.xmin * w)
                        y = int(bbox.ymin * h)
                        face_w = int(bbox.width * w)
                        face_h = int(bbox.height * h)
                        detected_faces.append((x, y, face_w, face_h))
        except:
            # Fallback to OpenCV faces nếu MediaPipe không có
            detected_faces = [(x, y, w, h) for (x, y, w, h) in faces]
        
        # 3. Tính vùng quan trọng
        if detected_faces:
            # Có faces - tính bounding box bao quanh tất cả faces
            min_x = min([x for x, y, w, h in detected_faces])
            min_y = min([y for x, y, w, h in detected_faces])
            max_x = max([x + w for x, y, w, h in detected_faces])
            max_y = max([y + h for x, y, w, h in detected_faces])
            
            # Mở rộng vùng một chút để không crop quá sát
            margin_x = int((max_x - min_x) * 0.3)
            margin_y = int((max_y - min_y) * 0.3)
            
            main_x = max(0, min_x - margin_x)
            main_y = max(0, min_y - margin_y)
            main_w = min(w - main_x, max_x - min_x + 2 * margin_x)
            main_h = min(h - main_y, max_y - min_y + 2 * margin_y)
            
            crop_center_x = main_x + main_w // 2
            crop_center_y = main_y + main_h // 2
            
        else:
            # Không có faces - dùng center crop
            main_x, main_y = 0, 0
            main_w, main_h = w, h
            crop_center_x, crop_center_y = w // 2, h // 2
        
        return {
            'faces': detected_faces,
            'main_region': (main_x, main_y, main_w, main_h),
            'crop_center': (crop_center_x, crop_center_y),
            'image_size': (w, h)
        }
        
    except Exception as e:
        # Fallback: center crop
        return {
            'faces': [],
            'main_region': (0, 0, w if 'w' in locals() else 100, h if 'h' in locals() else 100),
            'crop_center': (w//2 if 'w' in locals() else 50, h//2 if 'h' in locals() else 50),
            'image_size': (w if 'w' in locals() else 100, h if 'h' in locals() else 100)
        }

def analyze_image_for_collage(image_path):
    """
    Phân tích ảnh để đưa ra crop strategy phù hợp cho collage
    
    Returns:
        dict: {
            'aspect_ratio': float,
            'is_portrait': bool, 
            'is_landscape': bool,
            'recommended_position': str,  # 'main', 'side', 'any'
            'crop_strategy': str,         # 'center', 'left_bias', 'right_bias'
            'priority_score': float       # Điểm ưu tiên cho main position
        }
    """
    try:
        # Get image dimensions
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        h, w = img.shape[:2]
        aspect_ratio = w / h
        
        # Analyze image characteristics
        is_portrait = aspect_ratio < 0.8   # Tỷ lệ < 4:5
        is_landscape = aspect_ratio > 1.25  # Tỷ lệ > 5:4
        is_square = 0.8 <= aspect_ratio <= 1.25
        
        # Calculate priority score for main position
        priority_score = 0.5  # Base score
        
        if is_portrait:
            priority_score += 0.3  # Portrait ưu tiên main position
        elif is_square:
            priority_score += 0.1  # Square cũng ok cho main
        
        # Face detection bonus (nếu có face thì ưu tiên main)
        try:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_face_detection = mp.solutions.face_detection
            
            with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.3) as face_detection:
                results = face_detection.process(rgb_img)
                if results.detections and len(results.detections) > 0:
                    priority_score += 0.2  # Có face = ưu tiên main
                    
        except Exception:
            pass  # Ignore face detection errors
        
        # Determine recommended position
        if priority_score > 0.7:
            recommended_position = 'main'
        elif priority_score < 0.4:
            recommended_position = 'side'
        else:
            recommended_position = 'any'
        
        # Determine crop strategy
        if is_landscape:
            # Landscape có thể có nhiều subjects → cần bias strategy
            crop_strategy = 'smart_bias'  # Sẽ test cả left và right bias
        else:
            # Portrait/square thường dùng center crop
            crop_strategy = 'center'
        
        return {
            'aspect_ratio': aspect_ratio,
            'is_portrait': is_portrait,
            'is_landscape': is_landscape,
            'is_square': is_square,
            'recommended_position': recommended_position,
            'crop_strategy': crop_strategy,
            'priority_score': priority_score,
            'dimensions': (w, h)
        }
        
    except Exception as e:
        log(f"    ⚠️ Lỗi analyze image {image_path}: {str(e)}")
        return None

def smart_resize_image_enhanced(img_clip, target_resolution=(1920, 1080), fill_mode='smart_crop', position_hint=None):
    """
    Enhanced smart resize với position-aware cropping
    
    Args:
        img_clip: ImageClip object
        target_resolution: tuple (width, height)
        fill_mode: 'smart_crop', 'center', 'left_bias', 'right_bias'
        position_hint: 'main', 'side' - hint về vị trí trong collage
    """
    target_w, target_h = target_resolution
    img_w, img_h = img_clip.w, img_clip.h
    
    if fill_mode == 'smart_crop':
        # Enhanced smart cropping với position awareness
        try:
            temp_array = img_clip.get_frame(0)
            bgr_array = cv2.cvtColor(temp_array, cv2.COLOR_RGB2BGR)
            
            # Detect subjects
            subject_info = detect_main_subject(bgr_array)
            
            if subject_info and subject_info['crop_center']:
                cx, cy = subject_info['crop_center']
                
                # Apply position-aware bias cho landscape images
                if img_w > img_h * 1.3:  # Landscape image
                    if position_hint == 'side' and len(subject_info['faces']) > 1:
                        # Side position với nhiều faces → bias để tránh cắt qua subjects
                        faces = subject_info['faces']
                        if len(faces) >= 2:
                            # Chọn face phù hợp với target aspect ratio
                            target_aspect = target_w / target_h
                            
                            if target_aspect < 0.8:  # Target is tall (side position)
                                # Chọn face ở edge để tránh cắt qua giữa
                                leftmost = min(faces, key=lambda f: f[0] + f[2]/2)
                                rightmost = max(faces, key=lambda f: f[0] + f[2]/2)
                                
                                left_center = leftmost[0] + leftmost[2]/2
                                right_center = rightmost[0] + rightmost[2]/2
                                
                                # Chọn bias strategy dựa trên target position
                                if right_center - left_center > img_w * 0.3:  # Faces cách xa nhau
                                    # Bias về left nếu có space
                                    if left_center > img_w * 0.3:
                                        cx = left_center
                                        log(f"    🎯 Applied LEFT bias for side position")
                                    else:
                                        cx = right_center  
                                        log(f"    🎯 Applied RIGHT bias for side position")
                
                crop_coords = smart_crop_calculation(img_w, img_h, target_w, target_h, (cx, cy))
                x1, y1, x2, y2 = crop_coords
                
                scale_w = target_w / img_w
                scale_h = target_h / img_h
                scale = max(scale_w, scale_h)
                
                resized_img = img_clip.resize(scale)
                final_clip = resized_img.crop(x1=x1*scale, y1=y1*scale, x2=x2*scale, y2=y2*scale)
                
                return final_clip
                
            else:
                # Fallback to smart bias for landscape without detected subjects
                if img_w > img_h * 1.3:  # Landscape
                    if position_hint == 'side':
                        # Side position → left bias thường tốt hơn
                        cx = img_w // 3
                        log(f"    🎯 Applied LEFT bias fallback for landscape in side position")
                    else:
                        cx = img_w // 2  # Center for main position
                else:
                    cx = img_w // 2
                    
                cy = img_h // 2
                crop_coords = smart_crop_calculation(img_w, img_h, target_w, target_h, (cx, cy))
                x1, y1, x2, y2 = crop_coords
                
                scale_w = target_w / img_w
                scale_h = target_h / img_h
                scale = max(scale_w, scale_h)
                
                resized_img = img_clip.resize(scale)
                final_clip = resized_img.crop(x1=x1*scale, y1=y1*scale, x2=x2*scale, y2=y2*scale)
                
                return final_clip
                
        except Exception as e:
            log(f"    ❌ Enhanced smart crop error: {str(e)}, fallback to center")
            
    # Fallback to original smart_resize_image
    return smart_resize_image(img_clip, target_resolution, 'smart_crop')

def smart_crop_calculation(source_w, source_h, target_w, target_h, crop_center=None):
    """
    Tính toán vùng crop thông minh
    
    Args:
        source_w, source_h: Kích thước ảnh gốc
        target_w, target_h: Kích thước đích
        crop_center: (cx, cy) điểm trung tâm ưu tiên, None = center crop
    
    Returns:
        (x1, y1, x2, y2): Tọa độ vùng crop
    """
    if crop_center is None:
        crop_center = (source_w // 2, source_h // 2)
    
    cx, cy = crop_center
    
    # Tính tỷ lệ scale cần thiết
    scale_w = target_w / source_w
    scale_h = target_h / source_h
    scale = max(scale_w, scale_h)  # Scale để fill đầy target
    
    # Kích thước sau khi scale
    scaled_w = int(source_w * scale)
    scaled_h = int(source_h * scale)
    
    # Tính vùng crop từ ảnh đã scale
    crop_w = target_w
    crop_h = target_h
    
    # Điều chỉnh center để crop không bị tràn
    crop_x = max(0, min(scaled_w - crop_w, int(cx * scale) - crop_w // 2))
    crop_y = max(0, min(scaled_h - crop_h, int(cy * scale) - crop_h // 2))
    
    # Convert về tọa độ ảnh gốc
    x1 = crop_x / scale
    y1 = crop_y / scale
    x2 = x1 + crop_w / scale
    y2 = y1 + crop_h / scale
    
    return (x1, y1, x2, y2)

def smart_resize_image(img_clip, target_resolution=(1920, 1080), fill_mode='smart_crop'):
    """
    Resize ảnh thông minh với AI-powered cropping
    
    Args:
        img_clip: ImageClip object
        target_resolution: tuple (width, height) - resolution đích
        fill_mode: 'letterbox', 'crop', 'stretch', 'smart_crop' (AI-powered)
    
    Returns:
        ImageClip đã được resize
    """
    target_w, target_h = target_resolution
    img_w, img_h = img_clip.w, img_clip.h
    
    if fill_mode == 'smart_crop':
        # AI Smart Cropping
        try:
            # Lấy frame đầu tiên của ImageClip để analyze
            temp_array = img_clip.get_frame(0)  # RGB array
            
            # Convert RGB to BGR cho OpenCV
            bgr_array = cv2.cvtColor(temp_array, cv2.COLOR_RGB2BGR)
            
            # Detect chủ thể chính
            subject_info = detect_main_subject(bgr_array)
            
            if subject_info and subject_info['crop_center']:
                # Có detect được subject - crop thông minh
                cx, cy = subject_info['crop_center']
                crop_coords = smart_crop_calculation(img_w, img_h, target_w, target_h, (cx, cy))
                x1, y1, x2, y2 = crop_coords
                
                # Scale để fill đầy target resolution
                scale_w = target_w / img_w
                scale_h = target_h / img_h
                scale = max(scale_w, scale_h)
                
                # Resize trước
                resized_img = img_clip.resize(scale)
                
                # Sau đó crop
                final_clip = resized_img.crop(
                    x1=x1*scale, y1=y1*scale, 
                    x2=x2*scale, y2=y2*scale
                )
                
                log(f"    🎯 Smart crop: detected {len(subject_info['faces'])} faces, center=({cx},{cy})")
                return final_clip
                
            else:
                # Fallback to center crop
                log(f"    ⚠️ Smart crop fallback: no subjects detected, using center crop")
                return smart_resize_image(img_clip, target_resolution, 'crop')
                
        except Exception as e:
            log(f"    ❌ Smart crop error: {str(e)}, fallback to center crop")
            return smart_resize_image(img_clip, target_resolution, 'crop')
    
    elif fill_mode == 'letterbox':
        # Giữ tỷ lệ gốc, thêm padding (nền đen) nếu cần
        # Scale để ảnh vừa với một chiều của khung hình
        scale_w = target_w / img_w
        scale_h = target_h / img_h
        scale = min(scale_w, scale_h)  # Chọn scale nhỏ hơn để không bị tràn
        
        # Resize ảnh
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        resized_img = img_clip.resize((new_w, new_h))
        
        # Tạo nền đen và đặt ảnh vào giữa
        black_bg = ColorClip(size=target_resolution, color=(0, 0, 0))
        final_clip = CompositeVideoClip([
            black_bg,
            resized_img.set_position('center')
        ], size=target_resolution)
        
        return final_clip
        
    elif fill_mode == 'crop':
        # Cắt ảnh để vừa khung hình (có thể mất một phần ảnh)
        scale_w = target_w / img_w
        scale_h = target_h / img_h
        scale = max(scale_w, scale_h)  # Chọn scale lớn hơn để fill đầy
        
        # Resize và crop
        resized_img = img_clip.resize(scale)
        
        # Crop về đúng kích thước
        return resized_img.crop(
            x_center=resized_img.w/2, 
            y_center=resized_img.h/2,
            width=target_w, 
            height=target_h
        )
        
    else:  # stretch
        # Kéo dãn ảnh để vừa khung hình (có thể bị biến dạng)
        return img_clip.resize(target_resolution)

def smart_resize_video(video_clip, target_resolution=(1920, 1080), target_fps=24, fill_mode='smart_crop'):
    """
    Resize video thông minh với AI-powered cropping
    
    Args:
        video_clip: VideoFileClip object
        target_resolution: tuple (width, height) - resolution đích
        target_fps: int - FPS đích cho smooth playback
        fill_mode: 'letterbox', 'crop', 'smart_crop' (AI-powered)
    
    Returns:
        VideoFileClip đã được resize mượt mà
    """
    target_w, target_h = target_resolution
    video_w, video_h = video_clip.w, video_clip.h
    
    # Đặt FPS trước để tránh giật
    if hasattr(video_clip, 'fps') and video_clip.fps:
        if video_clip.fps != target_fps:
            video_clip = video_clip.set_fps(target_fps)
    
    if fill_mode == 'smart_crop':
        # AI Smart Cropping cho video
        try:
            # Sample một vài frame để analyze
            sample_times = [0.1, 0.3, 0.5, 0.7, 0.9]  # 5 điểm thời gian
            sample_times = [t * video_clip.duration for t in sample_times if t * video_clip.duration < video_clip.duration]
            
            all_centers = []
            total_faces = 0
            
            for t in sample_times:
                try:
                    frame = video_clip.get_frame(t)  # RGB array
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    subject_info = detect_main_subject(bgr_frame)
                    if subject_info and subject_info['crop_center']:
                        all_centers.append(subject_info['crop_center'])
                        total_faces += len(subject_info['faces'])
                        
                except Exception as e:
                    continue
            
            if all_centers:
                # Tính trung bình weighted của tất cả centers
                avg_cx = sum([cx for cx, cy in all_centers]) // len(all_centers)
                avg_cy = sum([cy for cx, cy in all_centers]) // len(all_centers)
                
                # Smart crop với center đã tính toán
                scale_w = target_w / video_w
                scale_h = target_h / video_h
                scale = max(scale_w, scale_h)  # Scale để fill đầy
                
                # Resize trước
                resized_video = video_clip.resize(scale)
                
                # Tính toán crop region
                crop_coords = smart_crop_calculation(video_w, video_h, target_w, target_h, (avg_cx, avg_cy))
                x1, y1, x2, y2 = crop_coords
                
                # Crop video
                final_video = resized_video.crop(
                    x1=x1*scale, y1=y1*scale,
                    x2=x2*scale, y2=y2*scale
                )
                
                log(f"      🎯 Smart crop video: {total_faces} faces detected, center=({avg_cx},{avg_cy})")
                return final_video
                
            else:
                # Fallback to center crop
                log(f"      ⚠️ Smart crop video fallback: no subjects detected, using center crop")
                return smart_resize_video(video_clip, target_resolution, target_fps, 'crop')
                
        except Exception as e:
            log(f"      ❌ Smart crop video error: {str(e)}, fallback to center crop")
            return smart_resize_video(video_clip, target_resolution, target_fps, 'crop')
    
    elif fill_mode == 'letterbox':
        # Letterbox mode - giữ tỷ lệ, thêm padding
        scale_w = target_w / video_w
        scale_h = target_h / video_h
        scale = min(scale_w, scale_h)  # Letterbox để không bị biến dạng
        
        # Resize video với scaling mượt
        new_w = int(video_w * scale)
        new_h = int(video_h * scale)
        
        resized_video = video_clip.resize((new_w, new_h))
        
        # Tạo nền đen và đặt video vào giữa
        black_bg = ColorClip(size=target_resolution, color=(0, 0, 0))
        final_video = CompositeVideoClip([
            black_bg.set_duration(video_clip.duration),
            resized_video.set_position('center')
        ], size=target_resolution)
        
        return final_video
        
    elif fill_mode == 'crop':
        # Center crop mode
        scale_w = target_w / video_w
        scale_h = target_h / video_h
        scale = max(scale_w, scale_h)  # Scale để fill đầy
        
        # Resize và crop
        resized_video = video_clip.resize(scale)
        
        return resized_video.crop(
            x_center=resized_video.w/2,
            y_center=resized_video.h/2,
            width=target_w,
            height=target_h
        )
        
    else:  # stretch
        return video_clip.resize(target_resolution)
    resized_video = video_clip.resize((new_w, new_h))
    
    # Nếu video không fill đầy, thêm padding đen
    if new_w != target_w or new_h != target_h:
        # Tạo background đen
        black_bg = ColorClip(size=target_resolution, color=(0, 0, 0))
        
        # Composite video lên background
        final_video = CompositeVideoClip([
            black_bg.set_duration(resized_video.duration),
            resized_video.set_position('center')
        ], size=target_resolution)
        
        return final_video
    else:
        return resized_video

def create_image_collage(image_paths, duration=4.0):
    """Tạo collage từ nhiều ảnh với intelligent positioning và smart crop"""
    try:
        num_images = len(image_paths)
        log(f"    Tạo collage từ {num_images} ảnh với intelligent positioning")
        
        # Professional margin và spacing
        margin = max(10, min(RESOLUTION) // 100)  # Dynamic margin based on resolution
        spacing = margin // 2  # Spacing giữa các ảnh
        
        if num_images == 1:
            # Ảnh đơn - sử dụng smart resize để vừa khung hình
            img = ImageClip(image_paths[0])
            collage = smart_resize_image_enhanced(img, RESOLUTION, 'smart_crop')
            log(f"    ✅ Ảnh đơn với enhanced smart crop")
            
        else:
            # Phân tích từng ảnh để intelligent positioning
            image_analyses = []
            for i, img_path in enumerate(image_paths):
                analysis = analyze_image_for_collage(img_path)
                if analysis:
                    analysis['original_index'] = i
                    analysis['path'] = img_path
                    image_analyses.append(analysis)
                    log(f"    📊 Ảnh {i+1}: {analysis['dimensions'][0]}x{analysis['dimensions'][1]}, "
                        f"priority={analysis['priority_score']:.2f}, pos={analysis['recommended_position']}")
            
            # Sort ảnh theo priority score (cao nhất lên đầu cho main position)
            image_analyses.sort(key=lambda x: x['priority_score'], reverse=True)
            sorted_paths = [analysis['path'] for analysis in image_analyses]
            
            # Load images theo thứ tự đã sort
            images = []
            for img_path in sorted_paths:
                img = ImageClip(img_path)
                images.append(img)
            
            # Available space sau khi trừ margin
            available_w = RESOLUTION[0] - (2 * margin)
            available_h = RESOLUTION[1] - (2 * margin)
            
            if num_images == 2:
                # 2 ảnh - modern split layout với spacing
                cell_w = (available_w - spacing) // 2
                cell_h = available_h
                
                # Enhanced crop với position hints
                img1 = smart_resize_image_enhanced(images[0], (cell_w, cell_h), 'smart_crop', 'main').set_position((margin, margin))
                img2 = smart_resize_image_enhanced(images[1], (cell_w, cell_h), 'smart_crop', 'main').set_position((margin + cell_w + spacing, margin))
                
                collage = CompositeVideoClip([img1, img2], size=RESOLUTION)
                log(f"    ✅ Layout 2 ảnh với intelligent positioning")
                
            elif num_images == 3:
                # 3 ảnh - Featured + sidebar layout với intelligent positioning
                main_w = int(available_w * 0.65)  # 65% cho ảnh chính (tương tự test)
                side_w = available_w - main_w - spacing
                side_h = (available_h - spacing) // 2
                
                # Ảnh có priority cao nhất → main position (trái)
                # 2 ảnh còn lại → side positions (phải)
                img1 = smart_resize_image_enhanced(images[0], (main_w, available_h), 'smart_crop', 'main').set_position((margin, margin))
                img2 = smart_resize_image_enhanced(images[1], (side_w, side_h), 'smart_crop', 'side').set_position((margin + main_w + spacing, margin))
                img3 = smart_resize_image_enhanced(images[2], (side_w, side_h), 'smart_crop', 'side').set_position((margin + main_w + spacing, margin + side_h + spacing))
                
                collage = CompositeVideoClip([img1, img2, img3], size=RESOLUTION)
                log(f"    ✅ Layout 3 ảnh: Main={image_analyses[0]['priority_score']:.2f}, "
                    f"Side1={image_analyses[1]['priority_score']:.2f}, Side2={image_analyses[2]['priority_score']:.2f}")
                
            elif num_images == 4:
                # 4 ảnh - Perfect grid 2x2 với intelligent positioning
                cell_w = (available_w - spacing) // 2
                cell_h = (available_h - spacing) // 2
                
                positions = [
                    (margin, margin),  # Top-left (highest priority)
                    (margin + cell_w + spacing, margin),  # Top-right
                    (margin, margin + cell_h + spacing),  # Bottom-left
                    (margin + cell_w + spacing, margin + cell_h + spacing)  # Bottom-right
                ]
                
                clips = []
                for i, img in enumerate(images[:4]):
                    # First position gets priority hint as main
                    position_hint = 'main' if i == 0 else 'any'
                    clip = smart_resize_image_enhanced(img, (cell_w, cell_h), 'smart_crop', position_hint).set_position(positions[i])
                    clips.append(clip)
                
                collage = CompositeVideoClip(clips, size=RESOLUTION)
                log(f"    ✅ Grid 2x2 với ảnh priority cao nhất ở top-left")
                
            else:  # 4 ảnh - Grid 2x2 layout
                # Giới hạn tối đa 4 ảnh để tránh phức tạp
                images = images[:4]  # Chỉ lấy 4 ảnh tốt nhất (đã sorted theo priority)
                
                # Layout 2x2 grid
                cell_w = (available_w - spacing) // 2
                cell_h = (available_h - spacing) // 2
                
                positions = [
                    (margin, margin),  # Top-left
                    (margin + cell_w + spacing, margin),  # Top-right
                    (margin, margin + cell_h + spacing),  # Bottom-left
                    (margin + cell_w + spacing, margin + cell_h + spacing)  # Bottom-right
                ]
                
                clips = []
                for i in range(min(4, len(images))):
                    # Ảnh đầu tiên (priority cao nhất) dùng main hint, còn lại dùng side hint
                    hint = 'main' if i == 0 else 'side'
                    clip = smart_resize_image_enhanced(images[i], (cell_w, cell_h), 'smart_crop', hint).set_position(positions[i])
                    clips.append(clip)
                
                collage = CompositeVideoClip(clips, size=RESOLUTION)
                log(f"    ✅ Grid 2x2 với ảnh priority cao nhất ở top-left (tối đa 4 ảnh)")
            
            log(f"    ✅ Intelligent collage {num_images} ảnh với smart positioning và enhanced cropping")
        
        collage = collage.set_duration(duration)
        log(f"    ✅ Collage hoàn thành ({duration}s)")
        
        # 🔧 CLEANUP: Close all individual image clips để tránh memory leak
        try:
            for img in images:
                if hasattr(img, 'close'):
                    img.close()
            log(f"    🧹 Cleaned up {len(images)} image clips")
        except Exception as cleanup_error:
            log(f"    ⚠️ Cleanup warning: {str(cleanup_error)}")
        
        return collage
        
    except Exception as e:
        log(f"    ❌ Lỗi tạo collage: {str(e)}")
        # Fallback: chỉ dùng ảnh đầu tiên với smart resize
        try:
            img = ImageClip(image_paths[0])
            result = smart_resize_image(img, RESOLUTION, 'smart_crop').set_duration(duration)
            img.close()  # Clean up fallback image
            return result
        except Exception as fallback_error:
            log(f"    ❌ Fallback error: {str(fallback_error)}")
            return None

def _process_ai_scoring_and_replacement(preliminary_images, image_files, video_files, selected_videos, find_file_path_func):
    """Helper function for AI scoring and replacement logic (used in RANDOM selection)"""
    selected_images = []
    rejected_images = []
    available_backup_images = [img for img in image_files if img not in preliminary_images]
    
    for i, image_file in enumerate(preliminary_images):
        log(f"📸 Đánh giá ảnh {i+1}/{len(preliminary_images)}: {image_file}")
        
        current_image = image_file
        replacement_attempts = 0
        max_attempts = 3  # Tối đa thay thế 3 lần
        
        while replacement_attempts <= max_attempts:
            image_path = find_file_path_func(current_image)
            
            # AI chấm điểm
            total_score, detail, is_acceptable, rejection_reason = calculate_total_image_score(image_path)
            
            log(f"   Điểm: {total_score:.1f}/100 - {detail}")
            
            if is_acceptable:
                selected_images.append(current_image)
                log(f"   ✅ Chấp nhận: {rejection_reason}")
                break
            else:
                rejected_images.append((current_image, rejection_reason))
                log(f"   ❌ Từ chối: {rejection_reason}")
                replacement_attempts += 1
                
                # Tìm ảnh thay thế
                if replacement_attempts <= max_attempts and available_backup_images:
                    log(f"   🔄 Thử thay thế lần {replacement_attempts}/{max_attempts}")
                    current_image = random.choice(available_backup_images)
                    available_backup_images.remove(current_image)
                    log(f"   📸 Thử ảnh thay thế: {current_image}")
                else:
                    # Hết ảnh thay thế hoặc đã thử đủ 3 lần
                    if replacement_attempts > max_attempts:
                        log(f"   ⏰ Đã thử {max_attempts} lần, chấp nhận ảnh cuối")
                        selected_images.append(current_image)
                    else:
                        log(f"   📭 Hết ảnh backup, chấp nhận ảnh gốc")
                        selected_images.append(image_file)
                    break
    
    # Đảm bảo tối thiểu video nếu có
    if len(selected_videos) == 0 and len(video_files) > 0:
        log("Không có video nào được chọn, thêm 1 video tối thiểu")
        # Thay 1 ảnh bằng 1 video
        if selected_images:
            selected_images.pop()
        selected_videos.append(video_files[0])
    
    return selected_images, rejected_images

def select_random_materials(image_files, video_files, find_file_path_func, skip_ai_scoring=False):
    """Chọn nguyên liệu ngẫu nhiên với AI chấm điểm và lọc ảnh chất lượng thấp
    Args:
        skip_ai_scoring: Nếu True, bỏ qua AI scoring và dùng hết files (cho manual selection)
    """
    total_materials = len(image_files) + len(video_files)
    
    # ========== MANUAL SELECTION LOGIC ==========
    if skip_ai_scoring:
        global MANUAL_SELECTED_FILES
        log(f"✋ MANUAL SELECTION: User đã chọn {len(MANUAL_SELECTED_FILES)} file")
        
        # Phân loại file user đã chọn thành ảnh và video
        manual_images = []
        manual_videos = []
        
        for filename in MANUAL_SELECTED_FILES:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                if filename in image_files:
                    manual_images.append(filename)
                else:
                    log(f"⚠️ Ảnh không tìm thấy: {filename}")
            elif ext in ['.mp4', '.mov', '.avi']:
                if filename in video_files:
                    manual_videos.append(filename)
                else:
                    log(f"⚠️ Video không tìm thấy: {filename}")
            else:
                log(f"⚠️ File không hỗ trợ: {filename}")
        
        log(f"✅ MANUAL SELECTION KẾT QUẢ: {len(manual_images)} ảnh, {len(manual_videos)} video")
        log(f"📋 Danh sách ảnh: {manual_images[:5]}{'...' if len(manual_images) > 5 else ''}")
        log(f"📋 Danh sách video: {manual_videos[:3]}{'...' if len(manual_videos) > 3 else ''}")
        
        # Trả về ngay file user đã chọn, không qua AI scoring
        return manual_images, manual_videos
    
    # ========== RANDOM SELECTION LOGIC (CŨ) ==========
    
    # Bước 1: Logic chọn số lượng nguyên liệu cho random selection
    if not skip_ai_scoring:
        # RANDOM SELECTION: Logic chọn số lượng như cũ
        if total_materials < MIN_MATERIALS:
            # Nếu tổng kho < 15 → lấy hết
            num_materials = total_materials
            log(f"Tổng kho {total_materials} < {MIN_MATERIALS}, lấy hết")
        elif total_materials < 5:
            # Tối thiểu 5 nguyên liệu để tạo clip
            log(f"⚠️ Chỉ có {total_materials} nguyên liệu < 5, không đủ để tạo clip!")
            return [], []
        else:
            # Random 15-30 nguyên liệu
            num_materials = random.randint(MIN_MATERIALS, min(MAX_MATERIALS, total_materials))
            log(f"Random chọn {num_materials} nguyên liệu từ tổng {total_materials} nguyên liệu")
    else:
        # MANUAL SELECTION: Dùng hết tất cả files user đã chọn
        num_materials = total_materials
        log(f"✋ MANUAL SELECTION: Dùng hết {num_materials} nguyên liệu user đã chọn")
    
    # Bước 2: Tạo danh sách tất cả nguyên liệu
    all_materials = []
    for img in image_files:
        all_materials.append(('image', img))
    for vid in video_files:
        all_materials.append(('video', vid))
    
    # Bước 3: Random chọn nguyên liệu
    random.shuffle(all_materials)
    selected_materials = all_materials[:num_materials]
    
    # Bước 4: Tách ảnh và video
    preliminary_images = [item[1] for item in selected_materials if item[0] == 'image']
    selected_videos = [item[1] for item in selected_materials if item[0] == 'video']
    
    log(f"Chọn sơ bộ: {len(preliminary_images)} ảnh, {len(selected_videos)} video")
    
    # ============ AI CHẤM ĐIỂM VÀ LỌC ẢNH ============
    if skip_ai_scoring:
        # MANUAL SELECTION: Dùng hết tất cả ảnh user đã chọn, không cần AI scoring
        log("✋ MANUAL SELECTION: Bỏ qua AI chấm điểm, dùng hết tất cả ảnh user đã chọn")
        selected_images = preliminary_images
        rejected_images = []
        
        # Đảm bảo tối thiểu video nếu có (áp dụng cho cả manual và random)
        if len(selected_videos) == 0 and len(video_files) > 0:
            log("Không có video nào được chọn, thêm 1 video tối thiểu")
            # Thay 1 ảnh bằng 1 video (nếu có ảnh)
            if selected_images:
                selected_images.pop()
            selected_videos.append(video_files[0])
    else:
        # RANDOM SELECTION: Áp dụng AI scoring như cũ
        log("🤖 RANDOM SELECTION: Bắt đầu AI chấm điểm và lọc ảnh...")
        selected_images, rejected_images = _process_ai_scoring_and_replacement(
            preliminary_images, image_files, video_files, selected_videos, find_file_path_func
        )
    
    log(f"Kết quả cuối: {len(selected_images)} ảnh, {len(selected_videos)} video")
    return selected_images, selected_videos

def create_random_image_groups(image_files, max_images=None):
    """Tạo các nhóm ảnh ngẫu nhiên"""
    if max_images is None:
        max_images = len(image_files)
    
    # Giới hạn số ảnh nếu cần
    if len(image_files) > max_images:
        image_files = random.sample(image_files, max_images)
        log(f"Giới hạn {max_images} ảnh từ {len(image_files)} ảnh có sẵn")
    
    # Tạo các nhóm ngẫu nhiên
    groups = []
    remaining_images = image_files.copy()
    
    while remaining_images:
        # Chọn ngẫu nhiên số ảnh trong nhóm (1-5)
        max_in_group = min(MAX_IMAGES_PER_FRAME, len(remaining_images))
        group_size = random.randint(1, max_in_group)
        
        # Lấy ảnh cho nhóm này
        group = remaining_images[:group_size]
        remaining_images = remaining_images[group_size:]
        groups.append(group)
        
        log(f"Nhóm {len(groups)}: {group_size} ảnh")
    
    return groups

def select_music(auto_random=False):
    """Cho phép người dùng chọn nhạc hoặc chọn ngẫu nhiên"""
    music_files = list_music_files()
    
    if not music_files:
        log("Không có file nhạc nào!")
        return None
    
    if len(music_files) == 1:
        selected_music = music_files[0]
        log(f"Chỉ có 1 file nhạc, tự động chọn: {selected_music}")
        return os.path.join(MUSIC_FOLDER, selected_music)
    
    # Hiển thị danh sách nhạc
    log(f"Tìm thấy {len(music_files)} file nhạc:")
    for i, music_file in enumerate(music_files, 1):
        log(f"  {i}. {music_file}")
    
    # Nếu auto_random=True (từ web), tự động chọn ngẫu nhiên
    if auto_random:
        selected_music = random.choice(music_files)
        log(f"✅ Đã chọn ngẫu nhiên tự động: {selected_music}")
        return os.path.join(MUSIC_FOLDER, selected_music)
    
    # Hỏi người dùng chọn (chỉ khi chạy từ command line)
    print("\n[MUSIC] Chọn file nhạc:")
    print(f"  0. Chọn ngẫu nhiên")
    for i, music_file in enumerate(music_files, 1):
        print(f"  {i}. {music_file}")
    
    while True:
        try:
            choice = int(input(f"Nhập lựa chọn (0-{len(music_files)}): "))
            if choice == 0:
                # Chọn ngẫu nhiên
                selected_music = random.choice(music_files)
                log(f"✅ Đã chọn ngẫu nhiên: {selected_music}")
                return os.path.join(MUSIC_FOLDER, selected_music)
            elif 1 <= choice <= len(music_files):
                selected_music = music_files[choice - 1]
                log(f"✅ Đã chọn: {selected_music}")
                return os.path.join(MUSIC_FOLDER, selected_music)
            else:
                print(f"❌ Vui lòng nhập số từ 0 đến {len(music_files)}")
        except ValueError:
            print("❌ Vui lòng nhập một số hợp lệ")
        except KeyboardInterrupt:
            log("Hủy chọn nhạc, chọn ngẫu nhiên")
            selected_music = random.choice(music_files)
            log(f"✅ Đã chọn ngẫu nhiên: {selected_music}")
            return os.path.join(MUSIC_FOLDER, selected_music)



def create_memories_video(username=None, custom_music_path=None):
    # 🕐 BẮT ĐẦU TIMER CHO TOÀN BỘ QUY TRÌNH
    video_timer.start("Tạo Video Kỷ Niệm với GPU Acceleration")
    
    # Set OUTPUT_FOLDER to user's memories directory
    global OUTPUT_FOLDER
    original_output_folder = OUTPUT_FOLDER
    if username:
        memories_folder = os.path.join('E:', 'EverLiving_UserData', username, 'memories')
        os.makedirs(memories_folder, exist_ok=True)
        OUTPUT_FOLDER = memories_folder
        log(f"✅ Output set to memories folder: {OUTPUT_FOLDER}")
    
    log("Bắt đầu tạo video kỷ niệm với logic mới")
    log(f"Thư mục ảnh/video: {INPUT_FOLDER}")
    log(f"Chọn ngẫu nhiên {MIN_MATERIALS}-{MAX_MATERIALS} nguyên liệu")
    log(f"Thời lượng mục tiêu: {MIN_DURATION}-{TARGET_DURATION}s")
    log(f"Custom music: {custom_music_path if custom_music_path else 'Không có'}")
    
    # BƯỚC 0: Kiểm tra và cấu hình CPU MAXIMUM PERFORMANCE
    video_timer.phase_start("Kiểm tra và tối ưu CPU")
    log("Bước 0: Cấu hình CPU maximum performance (44 cores + 128GB RAM)")
    global GPU_ENABLED
    
    # Log CPU status và optimization info
    log_cpu_status()
    video_timer.phase_update("CPU 44 cores được tối ưu hóa")
    
    if GPU_ENABLED:
        # GPU vẫn có thể được check nhưng sẽ không dùng vì ta đã tắt
        gpu_ok = log_gpu_status()
        if gpu_ok:
            log("🚀 GPU khả dụng nhưng đã DISABLED để dùng CPU mạnh hơn")
        GPU_ENABLED = False  # Force disable GPU để dùng CPU
        video_timer.phase_update("GPU disabled, sử dụng CPU maximum performance")
    else:
        log("💻 CPU MAXIMUM PERFORMANCE MODE - 44 cores + 128GB RAM")

    # BƯỚC 1: Chọn nhạc trước khi xử lý
    log("Bước 1: Chọn nhạc nền")
    selected_music = None
    
    if custom_music_path:
        # Kiểm tra nếu là URL
        if custom_music_path.startswith(('http://', 'https://')):
            if is_supported_music_url(custom_music_path):
                log(f"🌐 Đang download nhạc từ URL: {custom_music_path}")
                # Tạo thư mục temp cho download
                temp_music_folder = os.path.join(tempfile.gettempdir(), 'everTrace_music')
                os.makedirs(temp_music_folder, exist_ok=True)
                
                # Download audio
                downloaded_path = download_audio_from_url(custom_music_path, temp_music_folder)
                if downloaded_path and os.path.exists(downloaded_path):
                    selected_music = downloaded_path
                    log(f"✅ Download thành công: {os.path.basename(selected_music)}")
                else:
                    log(f"❌ Không thể download nhạc từ URL")
                    selected_music = select_music(auto_random=True)  # Fallback to random
            else:
                log(f"❌ URL không được hỗ trợ: {custom_music_path}")
                selected_music = select_music(auto_random=True)  # Fallback to random
        elif os.path.exists(custom_music_path):
            selected_music = custom_music_path
            log(f"🎵 Sử dụng nhạc local: {os.path.basename(selected_music)}")
        else:
            log(f"❌ File nhạc không tồn tại: {custom_music_path}")
            selected_music = select_music(auto_random=True)  # Fallback to random
    else:
        selected_music = select_music(auto_random=True)
        log(f"🎲 Chọn nhạc ngẫu nhiên: {os.path.basename(selected_music) if selected_music else 'Không có'}")
        
    if selected_music and os.path.exists(selected_music):
        try:
            music_audio = AudioFileClip(selected_music)
            music_duration = music_audio.duration
            log(f"✅ Đã chọn nhạc: {os.path.basename(selected_music)}")
            log(f"   Thời lượng nhạc: {music_duration:.1f}s")
            music_audio.close()
            del music_audio
        except Exception as e:
            log(f"❌ Lỗi đọc file nhạc: {str(e)}")
            selected_music = None
            music_duration = TARGET_DURATION
    else:
        log("⚠️ Không sử dụng nhạc nền")
        selected_music = None
        music_duration = TARGET_DURATION

    # 🆕 BƯỚC 0.5: Xác định outro file dựa trên resolution đã chọn
    log("Bước 0.5: Xác định outro video")
    if RESOLUTION == RESOLUTION_VERTICAL:
        outro_filename = "outro doc.mp4"
        log(f"✅ Chọn outro dọc cho {RESOLUTION}")
    elif RESOLUTION == RESOLUTION_SQUARE:
        outro_filename = "outro ngang.mp4"  # Có thể tạo outro vuông riêng sau
        log(f"✅ Chọn outro vuông cho {RESOLUTION}")
    else:
        outro_filename = "outro ngang.mp4"
        log(f"✅ Chọn outro ngang cho {RESOLUTION}")

    # Lấy danh sách file (scan subfolders)
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.avi']
    files = []
    
    # Scan root folder
    if os.path.exists(INPUT_FOLDER):
        for f in os.listdir(INPUT_FOLDER):
            if os.path.splitext(f)[1].lower() in valid_extensions:
                files.append(f)
    
    # Scan images subfolder
    images_folder = os.path.join(INPUT_FOLDER, 'images')
    if os.path.exists(images_folder):
        for f in os.listdir(images_folder):
            if os.path.splitext(f)[1].lower() in valid_extensions:
                files.append(f)
    
    # Scan videos subfolder  
    videos_folder = os.path.join(INPUT_FOLDER, 'videos')
    if os.path.exists(videos_folder):
        for f in os.listdir(videos_folder):
            if os.path.splitext(f)[1].lower() in valid_extensions:
                files.append(f)
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log(f"🔍 DEBUG [{timestamp}]: Total files found: {len(files)} in {INPUT_FOLDER} (including subfolders)")
    print(f"🔍 DEBUG [{timestamp}]: create_memories_video scanning files...")
    print(f"🔍 DEBUG [{timestamp}]: Root folder exists: {os.path.exists(INPUT_FOLDER)}")
    print(f"🔍 DEBUG [{timestamp}]: Images folder exists: {os.path.exists(os.path.join(INPUT_FOLDER, 'images'))}")
    print(f"🔍 DEBUG [{timestamp}]: Videos folder exists: {os.path.exists(os.path.join(INPUT_FOLDER, 'videos'))}")
    print(f"🔍 DEBUG [{timestamp}]: Files list: {files[:10] if files else 'No files found'}")
    
    # Create helper function to find file path in subfolders
    def find_file_path_in_create_memories(filename):
        """Find the full path of a file in INPUT_FOLDER or its subfolders"""
        # Try root folder first
        root_path = os.path.join(INPUT_FOLDER, filename)
        if os.path.exists(root_path):
            return root_path
        
        # Try images subfolder
        images_path = os.path.join(INPUT_FOLDER, 'images', filename)
        if os.path.exists(images_path):
            return images_path
        
        # Try videos subfolder
        videos_path = os.path.join(INPUT_FOLDER, 'videos', filename)
        if os.path.exists(videos_path):
            return videos_path
        
        # If not found anywhere, return original path for error handling
        return root_path
    
    # Store as global for other functions to use
    global find_file_path_in_memories
    find_file_path_in_memories = find_file_path_in_create_memories
    
    if not files:
        raise Exception("Không tìm thấy file hợp lệ trong thư mục!")

    # Phân loại ảnh và video
    image_files = [f for f in files if os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp']]
    video_files = [f for f in files if os.path.splitext(f)[1].lower() in ['.mp4', '.mov', '.avi']]

    log(f"Kho nguyên liệu: {len(image_files)} ảnh, {len(video_files)} video")

    # Create helper function to find file path in subfolders
    def find_file_path_func(filename):
        """Find the full path of a file in INPUT_FOLDER or its subfolders"""
        # Try root folder first
        root_path = os.path.join(INPUT_FOLDER, filename)
        if os.path.exists(root_path):
            return root_path
        
        # Try images subfolder
        images_path = os.path.join(INPUT_FOLDER, 'images', filename)
        if os.path.exists(images_path):
            return images_path
        
        # Try videos subfolder
        videos_path = os.path.join(INPUT_FOLDER, 'videos', filename)
        if os.path.exists(videos_path):
            return videos_path
        
        # If not found anywhere, return root path (for error handling)
        return root_path

    # BƯỚC 1: Chọn nguyên liệu
    video_timer.phase_start("Chọn nguyên liệu và AI xử lý")
    
    # Kiểm tra xem có phải manual selection không
    global IS_MANUAL_SELECTION
    skip_ai_scoring = IS_MANUAL_SELECTION
    
    if skip_ai_scoring:
        log("✋ MANUAL SELECTION: Bắt đầu với file đã chọn từ user")
    else:
        log("🎲 RANDOM SELECTION: Bắt đầu chọn nguyên liệu ngẫu nhiên")
    
    selected_images, selected_videos = select_random_materials(image_files, video_files, find_file_path_func, skip_ai_scoring=skip_ai_scoring)
    video_timer.phase_update(f"Đã chọn {len(selected_images)} ảnh và {len(selected_videos)} video")

    clips = []
    total_duration = 0

    # BƯỚC 2: Tính toán thời gian và xử lý video
    video_timer.phase_start("Tính toán thời gian và processing")
    log("Bước 2: Xử lý video và tính toán thời gian")
    
    video_clips = []
    estimated_video_duration = 0
    video_data = []  # Lưu thông tin video để xử lý 2 bước
    original_video_clips = []  # Lưu original clips để cleanup sau cùng
    
    # BƯỚC 1: Xử lý cơ bản - 1 clip mỗi video
    video_timer.phase_start("Xử lý video và AI smart cropping")
    log("BƯỚC 1: Xử lý cơ bản (1 clip/video)")
    for i, video_file in enumerate(selected_videos):
        video_path = find_file_path_func(video_file)
        log(f"  Video {i+1}: {video_file}")
        
        try:
            video_clip = VideoFileClip(video_path)
            original_duration = video_clip.duration
            original_fps = getattr(video_clip, 'fps', 24)
            log(f"    Thời lượng gốc: {original_duration:.1f}s, FPS: {original_fps}")
            
            if original_duration >= 5.0:  # Video >= 5s mới xử lý
                # Lưu thông tin video để xử lý bước 2 (giữ reference đến clip)
                video_data.append({
                    'file': video_file,
                    'path': video_path,
                    'clip': video_clip,  # Giữ reference để tránh lỗi get_frame
                    'duration': original_duration,
                    'used_segments': []  # Track các đoạn đã cắt
                })
                
                # Lưu clip để cleanup sau cùng
                original_video_clips.append(video_clip)
                if original_duration > MAX_VIDEO_CLIP_DURATION:
                    # Video dài: Cắt 1 clip random 8-12s
                    clip_duration = random.uniform(MIN_VIDEO_CLIP_DURATION, MAX_VIDEO_CLIP_DURATION)
                    max_start = original_duration - clip_duration
                    start_time = random.uniform(0, max_start)
                    end_time = min(start_time + clip_duration, original_duration)
                    
                    # Cắt clip
                    sub_clip = video_clip.subclip(start_time, end_time)
                    sub_clip = smart_resize_video(sub_clip, RESOLUTION, FPS)
                    
                    video_clips.append(sub_clip)
                    estimated_video_duration += (end_time - start_time)
                    
                    # Lưu segment đã dùng
                    video_data[-1]['used_segments'].append((start_time, end_time))
                    
                    log(f"    Clip {i+1}.1: {start_time:.1f}s-{end_time:.1f}s ({end_time-start_time:.1f}s)")
                else:
                    # Video ngắn: Dùng nguyên
                    sub_clip = smart_resize_video(video_clip, RESOLUTION, FPS)
                    video_clips.append(sub_clip)
                    estimated_video_duration += original_duration
                    
                    # Đánh dấu toàn bộ video đã dùng
                    video_data[-1]['used_segments'].append((0, original_duration))
                    
                    log(f"    Clip {i+1}.1: Dùng nguyên ({original_duration:.1f}s)")
            else:
                log(f"    ❌ Video quá ngắn ({original_duration:.1f}s < 5s), bỏ qua")
                # Cleanup ngay video không dùng được
                original_video_clips.append(video_clip)
                
        except Exception as e:
            log(f"    ❌ Lỗi xử lý video: {str(e)}")
            # Cleanup clip nếu có lỗi và đã tạo
            try:
                if 'video_clip' in locals() and video_clip is not None:
                    original_video_clips.append(video_clip)  # Vẫn add để cleanup
            except:
                pass
    
    log(f"Tổng Bước 1: {estimated_video_duration:.1f}s (< {MAX_VIDEO_MATERIALS_DURATION}s)")
    
    # Đếm số video thực tế được xử lý sau Bước 1
    processed_videos = len([v for v in video_data if len(v['used_segments']) > 0])
    
    # BƯỚC 2: Tối ưu hóa - Cắt thêm nếu còn dư thời gian
    if estimated_video_duration < MAX_VIDEO_MATERIALS_DURATION - MIN_VIDEO_CLIP_DURATION:
        remaining_time = MAX_VIDEO_MATERIALS_DURATION - estimated_video_duration
        log(f"BƯỚC 2: Tối ưu hóa (còn dư {remaining_time:.1f}s)")
        
        clip_counter_per_video = {}  # Track số clip cho mỗi video
        
        # Duyệt các video để cắt thêm
        for video_info in video_data:
            if estimated_video_duration >= MAX_VIDEO_MATERIALS_DURATION - MIN_VIDEO_CLIP_DURATION:
                break
            
            # 🔧 SỬ DỤNG: Dùng clip đã load thay vì reload
            video_clip = video_info['clip']  # Dùng clip đã có
            original_duration = video_info['duration']
            used_segments = video_info['used_segments']
            video_name = video_info['file']
            
            # Tìm vùng chưa sử dụng
            available_segments = []
            current_pos = 0
            
            # Sắp xếp used_segments theo thời gian
            used_segments.sort(key=lambda x: x[0])
            
            for start, end in used_segments:
                if current_pos < start - VIDEO_CLIP_GAP:
                    available_segments.append((current_pos, start - VIDEO_CLIP_GAP))
                current_pos = max(current_pos, end + VIDEO_CLIP_GAP)
            
            # Thêm phần cuối nếu có
            if current_pos < original_duration:
                available_segments.append((current_pos, original_duration))
            
            # Cắt thêm từ các segment available
            for avail_start, avail_end in available_segments:
                if estimated_video_duration >= MAX_VIDEO_MATERIALS_DURATION - MIN_VIDEO_CLIP_DURATION:
                    break
                    
                avail_duration = avail_end - avail_start
                if avail_duration >= MIN_VIDEO_CLIP_DURATION:
                    # Random clip duration
                    clip_duration = min(
                        random.uniform(MIN_VIDEO_CLIP_DURATION, MAX_VIDEO_CLIP_DURATION),
                        avail_duration
                    )
                    
                    # Kiểm tra xem thêm clip này có vượt quá không
                    if estimated_video_duration + clip_duration <= MAX_VIDEO_MATERIALS_DURATION:
                        # Random start position trong available segment
                        max_start = avail_end - clip_duration
                        start_time = random.uniform(avail_start, max_start)
                        end_time = min(start_time + clip_duration, avail_end)
                        
                        # Cắt clip bổ sung
                        sub_clip = video_clip.subclip(start_time, end_time)
                        sub_clip = smart_resize_video(sub_clip, RESOLUTION, FPS)
                        
                        video_clips.append(sub_clip)
                        estimated_video_duration += (end_time - start_time)
                        
                        # Cập nhật used_segments
                        video_info['used_segments'].append((start_time, end_time))
                        
                        video_index = video_data.index(video_info) + 1
                        if video_index not in clip_counter_per_video:
                            clip_counter_per_video[video_index] = 2  # Bắt đầu từ .2
                        
                        clip_number = clip_counter_per_video[video_index]
                        log(f"  + Video {video_index}: Clip {video_index}.{clip_number} ({start_time:.1f}s-{end_time:.1f}s) = {end_time-start_time:.1f}s → Tổng: {estimated_video_duration:.1f}s")
                        
                        clip_counter_per_video[video_index] += 1
                    else:
                        log(f"  + Video {video_data.index(video_info) + 1}: Clip sẽ vượt {MAX_VIDEO_MATERIALS_DURATION}s, bỏ qua")
                        break
        
        log(f"Tổng cuối: {estimated_video_duration:.1f}s từ {len(video_clips)} clips")
        
        # Cập nhật số video thực tế được xử lý (có thể thay đổi sau Bước 2)
        processed_videos = len([v for v in video_data if len(v['used_segments']) > 0])
        log(f"• KẾT QUẢ: {len(video_clips)} clips từ {processed_videos} video nguyên liệu")
        log(f"• THỜI LƯỢNG VIDEO: {estimated_video_duration:.1f}s/{MAX_VIDEO_MATERIALS_DURATION}s")
    else:
        # Nếu không có BƯỚC 2, vẫn cần log kết quả
        log(f"• KẾT QUẢ: {len(video_clips)} clips từ {processed_videos} video nguyên liệu")
        log(f"• THỜI LƯỢNG VIDEO: {estimated_video_duration:.1f}s/{MAX_VIDEO_MATERIALS_DURATION}s")
    
    # Đếm số video bị loại bỏ và bù nguyên liệu
    removed_videos_count = len(selected_videos) - processed_videos
    
    if removed_videos_count > 0:
        log(f"💡 Bị loại {removed_videos_count} video, random bù thêm nguyên liệu")
        
        # Tạo danh sách nguyên liệu dự phòng (chưa chọn)
        unused_materials = []
        for img in image_files:
            if img not in selected_images:
                unused_materials.append(('image', img))
        for vid in video_files:
            if vid not in selected_videos:
                unused_materials.append(('video', vid))
        
        # Random bù nguyên liệu
        if unused_materials:
            random.shuffle(unused_materials)
            backup_materials = unused_materials[:removed_videos_count]
            
            for material_type, material_file in backup_materials:
                if material_type == 'image':
                    selected_images.append(material_file)
                    log(f"   + Bù thêm ảnh: {material_file}")
                else:
                    # Thêm video vào danh sách để xử lý lại
                    selected_videos.append(material_file)
                    log(f"   + Bù thêm video: {material_file}")

    log(f"Tổng thời lượng video: {estimated_video_duration:.1f}s từ {len(video_clips)} clip (Max: {MAX_VIDEO_MATERIALS_DURATION}s)")
    
    # BƯỚC 3: Xử lý ảnh với logic đúng
    video_timer.phase_start("Xử lý ảnh với AI face detection")
    log("Bước 3: Xử lý ảnh")
    
    remaining_time = TARGET_DURATION - estimated_video_duration
    remaining_time = max(13, min(remaining_time, 44))  # Giới hạn 13-44s cho ảnh (khôi phục giá trị gốc)
    
    log(f"Thời gian còn lại cho ảnh: {remaining_time:.1f}s ({len(selected_images)} ảnh)")
    
    if selected_images:
        # Tính thời lượng mỗi ảnh nếu làm đơn
        time_per_single_image = remaining_time / len(selected_images)
        
        # Kiểm tra xem có thể làm ảnh đơn không (3-5s/ảnh)
        if 3.0 <= time_per_single_image <= 5.0:
            # Đủ thời gian, làm ảnh đơn
            log(f"Đủ thời gian ({time_per_single_image:.1f}s/ảnh), tạo ảnh đơn")
            
            for i, image_file in enumerate(selected_images):
                image_path = find_file_path_func(image_file)
                single_clip = create_image_collage([image_path], time_per_single_image)
                
                clips.append(single_clip)
                total_duration += time_per_single_image
                
                log(f"  => Ảnh đơn {i+1}: {image_file} ({time_per_single_image:.1f}s)")
        
        else:
            # Cần ghép ảnh để đạt 3-5s/clip
            log(f"Cần ghép ảnh (thời gian/ảnh đơn: {time_per_single_image:.1f}s)")
            
            if time_per_single_image < 3.0:
                # Thuật toán Random Grouping với Random Duration (3-5s)
                log(f"Thuật toán random grouping (< 3s/ảnh):")
                
                remaining_images = selected_images.copy()  # Copy để không ảnh hướng gốc
                collage_clips = []
                clip_durations = []
                total_used_time = 0
                iteration = 1
                
                # BƯỚC 1-3: Ba clip đầu tiên BẮT BUỘC chỉ 1 ảnh
                first_clips = 0
                while len(remaining_images) > 0 and first_clips < 3:  # 3 clip đầu
                    # Random thời gian cho clip (3-5s)
                    clip_duration = random.uniform(3.0, 5.0)
                    
                    # Chọn random 1 ảnh duy nhất
                    selected_image = random.choice(remaining_images)
                    remaining_images.remove(selected_image)
                    total_used_time += clip_duration
                    
                    # Log clip
                    log(f"   ⭐ Clip {iteration} (BẮT BUỘC 1 ảnh): ({clip_duration:.2f}s) {os.path.basename(selected_image)}")
                    log(f"   → Còn lại: {len(remaining_images)} ảnh, {remaining_time - total_used_time:.1f}s")
                    
                    # Lưu clip
                    collage_clips.append([selected_image])
                    clip_durations.append(clip_duration)
                    iteration += 1
                    first_clips += 1
                
                # BƯỚC 4+: Các clip sau random 1-4 ảnh (thay vì 2-5)
                while len(remaining_images) > 0:
                    remaining_time_left = remaining_time - total_used_time
                    
                    # Random thời gian (3-5s)
                    clip_duration = random.uniform(3.0, min(5.0, remaining_time_left))
                    
                    # Random số ảnh (1-4) thay vì (2-5)
                    max_group_size = min(4, len(remaining_images))
                    min_group_size = min(1, len(remaining_images))
                    group_size = random.randint(min_group_size, max_group_size)
                    
                    # Random chọn ảnh
                    selected_for_group = random.sample(remaining_images, group_size)
                    
                    # Log
                    log(f"   🎲 Clip {iteration} (RANDOM 1-4): {group_size} ảnh ({clip_duration:.2f}s) {[os.path.basename(img) for img in selected_for_group]}")
                    
                    # Lưu clip
                    collage_clips.append(selected_for_group)
                    clip_durations.append(clip_duration)
                    total_used_time += clip_duration
                    
                    # Loại bỏ ảnh đã chọn
                    for img in selected_for_group:
                        remaining_images.remove(img)
                    
                    log(f"   → Còn lại: {len(remaining_images)} ảnh, {remaining_time - total_used_time:.1f}s")
                    iteration += 1
                    
                    # Kiểm tra thời gian - nếu gần hết thì dừng
                    if remaining_time - total_used_time < 2.0:
                        if len(remaining_images) > 0:
                            # Fallback: lấy hết ảnh còn lại với thời gian còn lại
                            fallback_duration = remaining_time - total_used_time
                            log(f"   → Fallback: Lấy hết {len(remaining_images)} ảnh còn lại ({fallback_duration:.2f}s)")
                            log(f"   🔚 Clip {iteration} (FALLBACK): {len(remaining_images)} ảnh ({fallback_duration:.2f}s) {[os.path.basename(img) for img in remaining_images]}")
                            
                            collage_clips.append(remaining_images.copy())
                            clip_durations.append(fallback_duration)
                            remaining_images.clear()
                        break
                
                # BƯỚC 3: Clip 4 trở đi dùng logic kiểm tra ngược
                while len(remaining_images) > 0:
                    remaining_time_left = remaining_time - total_used_time
                    
                    # Random thời gian cho clip tiếp theo (3-5s)
                    if remaining_time_left <= 5.0:
                        clip_duration = remaining_time_left
                    else:
                        clip_duration = random.uniform(3.0, min(5.0, remaining_time_left))
                    
                    # Bắt đầu với số ảnh tối thiểu (2 ảnh) và tăng dần nếu cần
                    found_valid_group = False
                    for group_size in range(2, min(6, len(remaining_images) + 1)):  # 2-5 ảnh
                        
                        # Tính thời gian còn lại sau khi tạo clip này
                        images_after = len(remaining_images) - group_size
                        time_after = remaining_time_left - clip_duration
                        
                        # Kiểm tra: Ảnh còn lại có đủ thời gian không?
                        if images_after == 0:
                            # Clip cuối cùng, lấy hết ảnh còn lại
                            group_size = len(remaining_images)
                            found_valid_group = True
                            log(f"   → Clip cuối: {group_size} ảnh, dùng hết thời gian ({clip_duration:.2f}s)")
                            break
                        elif time_after / images_after >= 1.8:
                            # Ảnh còn lại đủ thời gian (≥1.8s/ảnh)
                            found_valid_group = True
                            log(f"   → Test {group_size} ảnh: OK ({images_after} ảnh còn lại, {time_after/images_after:.1f}s/ảnh)")
                            break
                        else:
                            # Không đủ thời gian, thử với nhóm lớn hơn
                            log(f"   → Test {group_size} ảnh: FAIL ({images_after} ảnh còn lại, {time_after/images_after:.1f}s/ảnh < 1.8s)")
                            continue
                    
                    # Nếu không tìm được group hợp lệ, lấy hết ảnh còn lại
                    if not found_valid_group:
                        group_size = len(remaining_images)
                        clip_duration = remaining_time_left
                        log(f"   → Fallback: Lấy hết {group_size} ảnh còn lại ({clip_duration:.2f}s)")
                    
                    # Random chọn ảnh (không theo thứ tự)
                    selected_for_group = random.sample(remaining_images, group_size)
                    
                    # Log iteration
                    log(f"   🔍 Clip {iteration} (CHECK): {group_size} ảnh ({clip_duration:.2f}s) {[os.path.basename(img) for img in selected_for_group]}")
                    
                    # Lưu clip và thời gian
                    collage_clips.append(selected_for_group)
                    clip_durations.append(clip_duration)
                    total_used_time += clip_duration
                    
                    # Loại bỏ ảnh đã chọn khỏi danh sách còn lại
                    for img in selected_for_group:
                        remaining_images.remove(img)
                    
                    iteration += 1
                    
                    # Debug: Kiểm tra ảnh còn lại
                    log(f"   → Còn lại: {len(remaining_images)} ảnh, {remaining_time_left - clip_duration:.1f}s")
                
                # Kiểm tra nếu còn ảnh chưa xử lý
                if len(remaining_images) > 0:
                    log(f"⚠️ CẢNH BÁO: Còn {len(remaining_images)} ảnh chưa xử lý!")
                    for img in remaining_images:
                        log(f"   - {os.path.basename(img)}")
                
                log(f"Tạo {len(collage_clips)} clips với tổng thời gian {total_used_time:.2f}s")
                
                # Tạo clips từ groups với thời gian tương ứng
                clips_with_duration = []
                for i, (group, duration) in enumerate(zip(collage_clips, clip_durations)):
                    group_paths = [find_file_path_func(img) for img in group]
                    collage_clip = create_image_collage(group_paths, duration)
                    clips_with_duration.append((collage_clip, duration, len(group)))
                    clips.append(collage_clip)
                    total_duration += duration
                
                # Bước 2: Xáo trộn thứ tự clips (Double Randomness)
                log(f"Xáo trộn thứ tự clips...")
                random.shuffle(clips_with_duration)
                
                # Cập nhật lại clips sau khi xáo trộn
                clips = clips[-len(clips_with_duration):]  # Xóa clips cũ
                clips.clear()
                for clip_info in clips_with_duration:
                    clips.append(clip_info[0])
                
                # Log kết quả sau xáo trộn
                for i, (clip, duration, group_size) in enumerate(clips_with_duration):
                    log(f"  => Clip ghép {i+1}: {group_size} ảnh ({duration:.2f}s) ✅")
                
                log(f"✅ Xử lý hết {len(selected_images)} ảnh, 2 lần random (duration + grouping + order)")
            
            else:
                # Thừa thời gian -> một số ảnh đơn + một số ghép
                # Ưu tiên ảnh đơn, ghép phần còn lại nếu cần
                single_count = int(remaining_time / 5.0)  # Ảnh đơn 5s
                single_count = min(single_count, len(selected_images))
                
                if single_count > 0:
                    remaining_images = selected_images[single_count:]
                    single_time = 5.0
                    remaining_after_singles = remaining_time - (single_count * single_time)
                    
                    # Tạo ảnh đơn
                    for i in range(single_count):
                        image_path = find_file_path_func(selected_images[i])
                        single_clip = create_image_collage([image_path], single_time)
                        clips.append(single_clip)
                        total_duration += single_time
                        log(f"  => Ảnh đơn {i+1}: {selected_images[i]} ({single_time:.1f}s)")
                    
                    # Ghép phần còn lại nếu có và đủ thời gian
                    if remaining_images and remaining_after_singles >= 1.8:
                        group_paths = [find_file_path_func(img) for img in remaining_images]
                        collage_clip = create_image_collage(group_paths, remaining_after_singles)
                        clips.append(collage_clip)
                        total_duration += remaining_after_singles
                        log(f"  => Nhóm ghép: {len(remaining_images)} ảnh ({remaining_after_singles:.1f}s)")

    # Tính tổng thời lượng thực tế (video + image)
    video_duration = sum(clip.duration for clip in video_clips)
    image_duration = sum(clip.duration for clip in clips)
    actual_total_duration = video_duration + image_duration
    
    # Log chi tiết từng phần
    log(f"📊 CHI TIẾT THỜI LƯỢNG:")
    log(f"   • Tổng thời lượng các clip ghép từ hình ảnh: {image_duration:.1f}s")
    log(f"   • Tổng thời lượng các video cắt ra: {video_duration:.1f}s ({len(video_clips)} video)")
    log(f"   • TỔNG CỘNG: {actual_total_duration:.1f}s")

    # BƯỚC 4: Xáo trộn và ghép video cuối cùng
    video_timer.phase_start("Ghép video và render GPU")
    log("Bước 4: Xáo trộn và tạo video cuối cùng")
    
    if not clips and not video_clips:
        raise Exception("Không có clip nào để tạo video!")
    
    # Merge tất cả clips (video + image) để xử lý chung
    all_clips = video_clips + clips
    
    # Xáo trộn tất cả clips để tạo sự ngẫu nhiên
    random.shuffle(all_clips)
    log(f"Đã xáo trộn {len(all_clips)} clips ({len(video_clips)} video + {len(clips)} image)")
    
    # Log thời lượng thực tế trước khi apply transitions
    total_duration_before_transitions = sum(clip.duration for clip in all_clips)
    log(f"Tổng thời lượng trước transitions: {total_duration_before_transitions:.1f}s")
    
    # Áp dụng hiệu ứng chuyển cảnh cho tất cả clips
    all_clips = apply_transitions_to_clips(all_clips)
    
    # Ghép tất cả clips lại
    final_clip = concatenate_videoclips(all_clips, method="compose")
    actual_final_duration = final_clip.duration
    log(f"Đã ghép video với transitions, thời lượng: {actual_final_duration:.1f}s")

    # 🆕 BƯỚC 5: Thêm outro video trước khi thêm nhạc
    log("Bước 5: Thêm outro video")
    final_clip = add_outro_video(final_clip, outro_filename)
    log(f"✅ Video sau outro: {final_clip.duration:.1f}s")

    # BƯỚC 5.5: Thêm nhạc nền để cover toàn bộ video (bao gồm outro)
    log("Bước 5.5: Thêm nhạc nền với fade effects (cover toàn bộ video + outro)")
    
    if selected_music and os.path.exists(selected_music):
        try:
            # Tải audio
            music_audio = AudioFileClip(selected_music)
            
            # Cắt audio cho phù hợp với video FINAL (bao gồm outro)
            if music_audio.duration > final_clip.duration:
                music_audio = music_audio.subclip(0, final_clip.duration)
            else:
                # Lặp lại nhạc nếu ngắn hơn video final (bao gồm outro)
                repeat_times = int(final_clip.duration / music_audio.duration) + 1
                music_clips = [music_audio] * repeat_times
                music_audio = concatenate_audioclips(music_clips).subclip(0, final_clip.duration)
            
            # Thêm fade in/out effects (fadeout sẽ sync với outro)
            music_audio = music_audio.audio_fadein(AUDIO_FADEIN).audio_fadeout(AUDIO_FADEOUT)
            
            # Áp dụng audio vào video
            final_clip = final_clip.set_audio(music_audio)
            
            log(f"✅ Đã thêm nhạc cover toàn bộ video: {os.path.basename(selected_music)}")
            log(f"   Video duration: {final_clip.duration:.1f}s (bao gồm outro)")
            log(f"   Fade in: {AUDIO_FADEIN}s, Fade out: {AUDIO_FADEOUT}s")
            
        except Exception as e:
            log(f"⚠️ Lỗi xử lý audio (tiếp tục không có nhạc): {str(e)}")
            # Tiếp tục xuất video không có nhạc nếu có lỗi
    else:
        log("🎵 Không có nhạc nền")

    # BƯỚC 6: Xuất video
    log("Bước 6: Xuất video cuối cùng")
    print(f"🔍 DEBUG: OUTPUT_FOLDER = {OUTPUT_FOLDER}", flush=True)
    print(f"🔍 DEBUG: OUTPUT_FILENAME = {OUTPUT_FILENAME}", flush=True)
    output_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILENAME)
    print(f"🔍 DEBUG: Final output_path = {output_path}", flush=True)
    
    try:
        # 🔧 Safety check: Đảm bảo final clip có audio hợp lệ
        if final_clip.audio is not None:
            log("Audio track được phát hiện, đang xuất video với âm thanh...")
        else:
            log("⚠️ Không có audio track, xuất video silent...")
            
        # Export với GPU acceleration cho tốc độ tối ưu
        if GPU_ENABLED:
            log("🚀 Xuất video với NVIDIA GPU acceleration (h264_nvenc)...")
            final_clip.write_videofile(
                output_path,
                fps=FPS,
                codec=GPU_CODEC,
                audio_codec=AUDIO_CODEC if final_clip.audio is not None else None,
                ffmpeg_params=GPU_EXTRA_PARAMS,
                logger=None,
                temp_audiofile="temp-audio.m4a",  # Tránh conflict audio
                remove_temp=True
            )
            log(f"✅ GPU Render hoàn thành! Video đã lưu: {output_path}")
            print(f"🔍 DEBUG: Video file created at: {output_path}", flush=True)
            print(f"🔍 DEBUG: File exists? {os.path.exists(output_path)}", flush=True)
            log(f"   GPU: NVIDIA GTX 1660 with CUDA acceleration")
            log(f"   Settings: {FPS}fps, {GPU_CODEC}, CRF {GPU_CRF}, preset {GPU_PRESET}")
        else:
            log("🚀 Xuất video với CPU MAXIMUM PERFORMANCE (44 cores + 128GB RAM)...")
            final_clip.write_videofile(
                output_path,
                fps=FPS,
                codec=CPU_CODEC,
                audio_codec=AUDIO_CODEC if final_clip.audio is not None else None,
                ffmpeg_params=CPU_EXTRA_PARAMS,
                threads=THREADS,
                logger=None,
                temp_audiofile="temp-audio.m4a",  # Tránh conflict audio
                remove_temp=True
            )
            log(f"✅ CPU MAXIMUM Render hoàn thành! Video đã lưu: {output_path}")
            log(f"   CPU: 44 cores @ maximum performance với 128GB RAM")
            log(f"   Settings: {FPS}fps, {CPU_CODEC}, CRF {CPU_CRF}, preset {CPU_PRESET}")
            log(f"   Bitrate: {CPU_BITRATE}, Quality: CRF {CPU_CRF} (very high quality)")
            
        log(f"   Thời lượng cuối cùng: {final_clip.duration:.1f}s")
        
    except Exception as e:
        log(f"❌ Lỗi xuất video: {str(e)}")
        raise
    finally:
        # 🛠️ PROPER CLEANUP để tránh lỗi Windows handle
        try:
            # Close tất cả clips để giải phóng resources
            if 'final_clip' in locals():
                final_clip.close()
            if 'all_clips' in locals():
                for clip in all_clips:
                    try:
                        clip.close()
                    except:
                        pass
            if 'video_clips' in locals():
                for clip in video_clips:
                    try:
                        clip.close()
                    except:
                        pass
            if 'clips' in locals():
                for clip in clips:
                    try:
                        clip.close()
                    except:
                        pass
            # 🆕 CLEANUP: Original video clips sau khi xuất xong
            if 'original_video_clips' in locals():
                for clip in original_video_clips:
                    try:
                        clip.close()
                    except:
                        pass
                log(f"🧹 Cleaned up {len(original_video_clips)} original video clips")
            if 'music_audio' in locals():
                try:
                    music_audio.close()
                except:
                    pass
            log("🧹 Đã cleanup resources thành công")
            
            # 🔧 FORCE GARBAGE COLLECTION để giải phóng memory
            import gc
            gc.collect()
            log("🗑️ Forced garbage collection completed")
            
        except Exception as cleanup_error:
            log(f"⚠️ Cleanup warning (không ảnh hưởng): {cleanup_error}")
            pass  # Không raise lỗi cleanup
    
    # 🏁 KẾT THÚC VÀ BÁO CÁO THỜI GIAN
    total_time = video_timer.finish()
    log(f"🎬 Video hoàn thành sau {total_time:.1f} giây với GPU acceleration!")
    
    # Restore original OUTPUT_FOLDER
    OUTPUT_FOLDER = original_output_folder
    
    # Return success result for app_simple.py
    return {
        'success': True,
        'message': 'Video kỷ niệm đã được tạo thành công!',
        'filename': os.path.basename(output_path) if 'output_path' in locals() else 'video.mp4',
        'video_path': output_path if 'output_path' in locals() else ''
    }


def create_video_from_images(user_folder, video_format, selected_files, username, music_path=None):
    """
    Tạo video từ ảnh đã chọn cho web app
    Args:
        user_folder: Thư mục chứa ảnh của user
        video_format: Định dạng video (horizontal/vertical/square)
        selected_files: List các file đã chọn
        username: Tên user
        music_path: Đường dẫn file nhạc (tùy chọn)
    Returns:
        Dict chứa kết quả tạo video
    """
    try:
        # Global declarations for manual selection handling
        global IS_MANUAL_SELECTION, MANUAL_SELECTED_FILES
        
        print(f"\n🚀 BẮT ĐẦU TẠO VIDEO CHO USER: {username}")
        print(f"📁 Thư mục: {user_folder}")
        print(f"📐 Định dạng: {video_format}")
        print(f"📋 Số file: {len(selected_files)}")
        print(f"🎵 Nhạc: {music_path if music_path else 'Không có'}")
        
        # Set global flag to indicate this is manual selection (user chose specific files)
        IS_MANUAL_SELECTION = True
        
        # Set global selected files for the memory creation process
        MANUAL_SELECTED_FILES = selected_files
        # Prepare user music folder (for backward compatibility if needed)
        user_music_folder = os.path.join(os.getcwd(), 'input', username, 'music')
        os.makedirs(user_music_folder, exist_ok=True)
        
        # If music_path is a URL, download to user music folder
        if music_path and isinstance(music_path, str) and music_path.startswith(('http://', 'https://')):
            print(f"🌐 Downloading custom music for user {username}...")
            downloaded_music = download_audio_from_url(music_path, user_music_folder)
            if downloaded_music:
                print(f"✅ Custom music downloaded: {downloaded_music}")
                music_path = downloaded_music
            else:
                print(f"❌ Failed to download custom music, fallback to no music.")
                music_path = None
        # If music_path is already a valid file path, use it directly
        elif music_path and os.path.exists(music_path):
            print(f"✅ Using existing music file: {music_path}")
        
        # Thiết lập folder input cho module
        global INPUT_FOLDER
        INPUT_FOLDER = user_folder
        
        # Thiết lập resolution theo format
        global RESOLUTION
        if video_format == 'vertical':
            RESOLUTION = RESOLUTION_VERTICAL
            print("📱 Chế độ dọc (9:16) - TikTok/Instagram Reels")
        elif video_format == 'square':
            RESOLUTION = RESOLUTION_SQUARE
            print("⬜ Chế độ vuông (1:1) - Instagram Post")
        else:
            RESOLUTION = RESOLUTION_HORIZONTAL
            print("📺 Chế độ ngang (16:9) - YouTube/TV")
        
        # Filter only selected files in the INPUT_FOLDER (scan subfolders)
        all_files = []
        supported_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.avi']
        
        # Scan root folder
        if os.path.exists(INPUT_FOLDER):
            for f in os.listdir(INPUT_FOLDER):
                if os.path.splitext(f)[1].lower() in supported_extensions:
                    all_files.append(f)
        
        # Scan images subfolder
        images_folder = os.path.join(INPUT_FOLDER, 'images')
        if os.path.exists(images_folder):
            for f in os.listdir(images_folder):
                if os.path.splitext(f)[1].lower() in supported_extensions:
                    all_files.append(f)
        
        # Scan videos subfolder  
        videos_folder = os.path.join(INPUT_FOLDER, 'videos')
        if os.path.exists(videos_folder):
            for f in os.listdir(videos_folder):
                if os.path.splitext(f)[1].lower() in supported_extensions:
                    all_files.append(f)
        
        # DEBUG: Log file info để tìm lỗi
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"🔍 DEBUG [{timestamp}]: INPUT_FOLDER = {INPUT_FOLDER}")
        print(f"🔍 DEBUG [{timestamp}]: Total files in folder: {len(all_files)}")
        print(f"🔍 DEBUG [{timestamp}]: Selected files count: {len(selected_files)}")
        print(f"🔍 DEBUG [{timestamp}]: First 5 all_files: {all_files[:5]}")
        print(f"🔍 DEBUG [{timestamp}]: First 5 selected_files: {selected_files[:5]}")
        
        available_files = [f for f in selected_files if f in all_files]
        
        print(f"🔍 DEBUG [{timestamp}]: Available files count: {len(available_files)}")
        print(f"🔍 DEBUG [{timestamp}]: Available files list: {available_files[:5]}")  # Show actual matches
        if not available_files and selected_files:
            print(f"🔍 DEBUG [{timestamp}]: Checking why files not found...")
            for sel_file in selected_files[:3]:  # Check first 3
                if sel_file in all_files:
                    print(f"✅ DEBUG [{timestamp}]: Found {sel_file}")
                else:
                    print(f"❌ DEBUG [{timestamp}]: Missing {sel_file}")
                    # Check if file exists with different case or characters
                    for all_file in all_files:
                        if sel_file.lower() == all_file.lower():
                            print(f"🔍 DEBUG [{timestamp}]: Case mismatch: '{sel_file}' vs '{all_file}'")
                        elif sel_file in all_file or all_file in sel_file:
                            print(f"🔍 DEBUG [{timestamp}]: Partial match: '{sel_file}' vs '{all_file}'")
        
        if not available_files:
            return {
                'success': False,
                'error': 'Không tìm thấy file nào hợp lệ trong danh sách đã chọn!',
                'error_code': 'NO_VALID_FILES',
                'debug_info': {
                    'input_folder': INPUT_FOLDER,
                    'total_files': len(all_files),
                    'selected_files': len(selected_files),
                    'available_files': len(available_files),
                    'first_selected': selected_files[:3] if selected_files else [],
                    'first_available': all_files[:3] if all_files else []
                }
            }
        
        print(f"✅ Tìm thấy {len(available_files)} file hợp lệ")
        
        # Create helper function to find file in subfolders
        def find_file_path(filename):
            """Find the full path of a file in INPUT_FOLDER or its subfolders"""
            # Try root folder first
            root_path = os.path.join(INPUT_FOLDER, filename)
            if os.path.exists(root_path):
                return root_path
            
            # Try images subfolder
            images_path = os.path.join(INPUT_FOLDER, 'images', filename)
            if os.path.exists(images_path):
                return images_path
            
            # Try videos subfolder
            videos_path = os.path.join(INPUT_FOLDER, 'videos', filename)
            if os.path.exists(videos_path):
                return videos_path
            
            # If not found anywhere, return original path for error handling
            return root_path
        
        # Store original INPUT_FOLDER as we'll need to override with subfolder logic
        global find_file_path_func
        find_file_path_func = find_file_path
        
        # Tạo thư mục memories cho user (đúng đường dẫn)
        output_folder = os.path.join('E:', 'EverLiving_UserData', username, 'memories')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
            print(f"📁 Tạo thư mục memories: {output_folder}")
        
        # Set OUTPUT_FOLDER cho module
        global OUTPUT_FOLDER
        original_output_folder = OUTPUT_FOLDER
        OUTPUT_FOLDER = output_folder
        print(f"📁 Đặt output folder: {OUTPUT_FOLDER}")
        print(f"📁 Original output folder: {original_output_folder}")
        
        # Temporarily backup original files list and set selected files
        original_files_backup = None
        try:
            # Save current state
            image_files = [f for f in available_files if os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp']]
            video_files = [f for f in available_files if os.path.splitext(f)[1].lower() in ['.mp4', '.mov', '.avi']]
            
            if not image_files and not video_files:
                return {
                    'success': False,
                    'error': 'Không có file ảnh hoặc video hợp lệ!',
                    'error_code': 'NO_MEDIA_FILES'
                }
            
            print(f"📊 Phân loại: {len(image_files)} ảnh, {len(video_files)} video")
            
            # Call the main video creation function with music
            start_time = time.time()
            create_memories_video(custom_music_path=music_path)
            processing_time = time.time() - start_time
            
            # Find the created video file (most recent .mp4 in output folder)
            video_files_in_folder = [f for f in os.listdir(output_folder) if f.endswith('.mp4')]
            
            if not video_files_in_folder:
                # Restore original output folder
                OUTPUT_FOLDER = original_output_folder
                return {
                    'success': False,
                    'error': f'Video đã được xử lý nhưng không tìm thấy file output trong {output_folder}!',
                    'error_code': 'OUTPUT_NOT_FOUND'
                }
            
            # Get the most recent video file
            video_files_with_time = [(f, os.path.getmtime(os.path.join(output_folder, f))) for f in video_files_in_folder]
            video_files_with_time.sort(key=lambda x: x[1], reverse=True)
            latest_video = video_files_with_time[0][0]
            video_path = os.path.join(output_folder, latest_video)
            
            # Restore original output folder
            OUTPUT_FOLDER = original_output_folder
            
            print(f"✅ Video tạo thành công: {latest_video}")
            print(f"📁 Lưu trong: {output_folder}")
            print(f"⏱️ Thời gian xử lý: {processing_time:.1f}s")
            
            # No temp cleanup needed, music is saved in user folder
            
            # Reset manual selection flags for next run
            IS_MANUAL_SELECTION = False
            MANUAL_SELECTED_FILES = []
            
            return {
                'success': True,
                'video_path': video_path,
                'filename': latest_video,
                'processing_time': processing_time,
                'frames_processed': len(available_files),
                'resolution': f"{RESOLUTION[0]}x{RESOLUTION[1]}",
                'format': video_format
            }
            
        except Exception as creation_error:
            # Restore original output folder
            OUTPUT_FOLDER = original_output_folder
            
            # Reset manual selection flags for next run
            IS_MANUAL_SELECTION = False
            MANUAL_SELECTED_FILES = []
            
            print(f"❌ Lỗi trong quá trình tạo video: {str(creation_error)}")
            return {
                'success': False,
                'error': f'Lỗi tạo video: {str(creation_error)}',
                'error_code': 'CREATION_ERROR',
                'error_details': str(creation_error)
            }
            
    except Exception as e:
        # Restore original output folder if it was set
        try:
            if 'original_output_folder' in locals():
                OUTPUT_FOLDER = original_output_folder
        except:
            pass
        print(f"❌ LỖI NGHIÊM TRỌNG trong create_video_from_images: {str(e)}")
        return {
            'success': False,
            'error': f'Lỗi hệ thống: {str(e)}',
            'error_code': 'SYSTEM_ERROR',
            'error_details': str(e)
        }


def set_user_folder(folder_path):
    """Thiết lập thư mục user cho video processor"""
    global INPUT_FOLDER
    INPUT_FOLDER = folder_path
    print(f"📁 Đã thiết lập thư mục user: {folder_path}")


if __name__ == "__main__":
    try:
        log("=" * 60)
        log("KHỞI ĐỘNG CHƯƠNG TRÌNH TẠO VIDEO KỶ NIỆM VỚI LOGIC MỚI")
        log("=" * 60)
        
        # ===== CHỌN ORIENTATION =====
        print("\n🎬 CHỌN ĐỊNH DẠNG VIDEO:")
        print("1. 📺 Ngang (16:9) - 1280x720 - YouTube/TV")
        print("2. 📱 Dọc (9:16) - 720x1280 - TikTok/Instagram Reels")
        print("3. ⬜ Vuông (1:1) - 720x720 - Instagram Post")
        
        while True:
            choice = input("\nNhập lựa chọn (1/2/3): ").strip()
            if choice == "1":
                globals()['RESOLUTION'] = RESOLUTION_HORIZONTAL
                orientation = "NGANG (16:9)"
                break
            elif choice == "2":
                globals()['RESOLUTION'] = RESOLUTION_VERTICAL
                orientation = "DỌC (9:16)"
                break
            elif choice == "3":
                globals()['RESOLUTION'] = RESOLUTION_SQUARE
                orientation = "VUÔNG (1:1)"
                break
            else:
                print("❌ Lựa chọn không hợp lệ. Vui lòng nhập 1, 2 hoặc 3.")
        
        log(f"✅ Đã chọn định dạng: {orientation} - {RESOLUTION[0]}x{RESOLUTION[1]}")
        
        create_memories_video()
    except Exception as e:
        log(f"❌ LỖI CHƯƠNG TRÌNH: {str(e)}")
        raise