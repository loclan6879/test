// Mixed Media Viewer - Unified viewer for images and videos with navigation
let currentMixedMediaIndex = 0;
let currentMixedMediaList = [];

function openMixedMediaViewer(mediaPath, title, mediaType, mediaList = [], index = 0) {
    currentMixedMediaList = mediaList;
    currentMixedMediaIndex = index;
    
    const modal = document.createElement('div');
    modal.id = 'mixedMediaModal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: rgba(0,0,0,0.9); z-index: 10000; display: flex; 
        align-items: center; justify-content: center; cursor: pointer;
    `;
    
    updateMixedMediaModal(modal);
    
    // Close modal when clicking outside
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeMixedMediaModal();
        }
    };
    
    // Add keyboard navigation
    document.addEventListener('keydown', handleMixedMediaKeyPress);
    
    document.body.appendChild(modal);
}

function updateMixedMediaModal(modal) {
    const currentMedia = currentMixedMediaList[currentMixedMediaIndex];
    const isVideo = currentMedia.type === 'video';
    
    modal.innerHTML = `
        <div class="media-container" style="max-width: 90%; max-height: 90%; position: relative;" onclick="event.stopPropagation();">
            <!-- Close button -->
            <div class="close-btn" style="position: absolute; top: -40px; right: 0; color: white; font-size: 30px; cursor: pointer; z-index: 10001;" onclick="closeMixedMediaModal()">&times;</div>
            
            <!-- Navigation buttons -->
            ${currentMixedMediaList.length > 1 ? `
                <div class="nav-btn nav-prev" style="position: absolute; left: -60px; top: 50%; transform: translateY(-50%); color: white; font-size: 40px; cursor: pointer; z-index: 10001; background: rgba(0,0,0,0.5); border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;" onclick="navigateMixedMedia(-1)">
                    &lt;
                </div>
                <div class="nav-btn nav-next" style="position: absolute; right: -60px; top: 50%; transform: translateY(-50%); color: white; font-size: 40px; cursor: pointer; z-index: 10001; background: rgba(0,0,0,0.5); border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;" onclick="navigateMixedMedia(1)">
                    &gt;
                </div>
            ` : ''}
            
            <!-- Media title -->
            <div class="media-title" style="color: white; text-align: center; margin-bottom: 10px; font-size: 18px; font-weight: 500;">${currentMedia.title}</div>
            
            <!-- Media content -->
            ${isVideo ? `
                <video id="currentMixedVideo" controls autoplay style="max-width: 100%; max-height: 85vh; border-radius: 8px;">
                    <source src="${currentMedia.path}" type="video/mp4">
                    <source src="${currentMedia.path}" type="video/webm">
                    <source src="${currentMedia.path}" type="video/ogg">
                    Trình duyệt không hỗ trợ video.
                </video>
            ` : `
                <img src="${currentMedia.path}" alt="${currentMedia.title}" 
                     style="max-width: 100%; max-height: 85vh; object-fit: contain; display: block; margin: 0 auto; border-radius: 8px;">
            `}
            
            <!-- Media counter -->
            ${currentMixedMediaList.length > 1 ? `
                <div class="media-counter" style="color: white; text-align: center; margin-top: 10px; font-size: 14px;">
                    ${currentMixedMediaIndex + 1} / ${currentMixedMediaList.length} (${isVideo ? 'Video' : 'Hình ảnh'})
                </div>
            ` : ''}
        </div>
    `;
}

function closeMixedMediaModal() {
    const modal = document.getElementById('mixedMediaModal');
    if (modal) {
        // Stop video if playing
        const video = modal.querySelector('video');
        if (video) {
            video.pause();
            video.currentTime = 0;
        }
        
        // Remove keyboard event listener
        document.removeEventListener('keydown', handleMixedMediaKeyPress);
        
        // Remove modal
        document.body.removeChild(modal);
        
        // Reset variables
        currentMixedMediaList = [];
        currentMixedMediaIndex = 0;
    }
}

function navigateMixedMedia(direction) {
    if (currentMixedMediaList.length <= 1) return;
    
    // Stop current video if playing
    const currentVideo = document.getElementById('currentMixedVideo');
    if (currentVideo) {
        currentVideo.pause();
        currentVideo.currentTime = 0;
    }
    
    currentMixedMediaIndex += direction;
    
    // Loop around
    if (currentMixedMediaIndex < 0) {
        currentMixedMediaIndex = currentMixedMediaList.length - 1;
    } else if (currentMixedMediaIndex >= currentMixedMediaList.length) {
        currentMixedMediaIndex = 0;
    }
    
    // Update modal content
    const modal = document.getElementById('mixedMediaModal');
    if (modal) {
        updateMixedMediaModal(modal);
    }
}

function handleMixedMediaKeyPress(e) {
    switch(e.key) {
        case 'Escape':
            closeMixedMediaModal();
            break;
        case 'ArrowLeft':
            navigateMixedMedia(-1);
            break;
        case 'ArrowRight':
            navigateMixedMedia(1);
            break;
    }
}
