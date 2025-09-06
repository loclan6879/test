@echo off
echo 🔍 Checking updated system...
echo ================================

echo 📊 NVIDIA Driver Check:
nvidia-smi

echo.
echo 🛠️ CUDA Toolkit Check:
nvcc --version

echo.
echo 🎬 GPU Encoding Test:
ffmpeg -f lavfi -i testsrc=duration=2:size=320x240:rate=1 -c:v h264_nvenc -preset fast -f null -

echo.
echo ✅ If no errors above, GPU acceleration is ready!
echo Run: python test_system.py
pause
