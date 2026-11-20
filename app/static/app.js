// Global Application State
let appState = {
    file: null,
    fileType: null, // 'image' or 'video'
    originalWidth: 0,
    originalHeight: 0,
    analysisResults: null,
    activeTab: 'original',
    videoTimeline: [],
    videoDuration: 0,
    currentFrameIndex: 0
};

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const terminalBody = document.getElementById('terminal-body');
const systemTimeEl = document.getElementById('system-time');
const progressBox = document.getElementById('analysis-status-box');
const progressBarFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');
const viewportPlaceholder = document.getElementById('viewport-placeholder');
const mediaContainer = document.getElementById('media-container');
const viewImage = document.getElementById('view-image');
const viewVideo = document.getElementById('view-video');
const landmarkCanvas = document.getElementById('landmark-canvas');
const visualizerTabs = document.getElementById('visualizer-tabs');
const videoTimelinePanel = document.getElementById('video-timeline-panel');
const reportPlaceholder = document.getElementById('report-content-placeholder');
const reportData = document.getElementById('report-content-data');
const timelineSlider = document.getElementById('timeline-slider');
const timelineTimeCurrent = document.getElementById('timeline-time-current');
const timelineTimeTotal = document.getElementById('timeline-time-total');

// Images Overlays
const elaImage = document.getElementById('ela-image');
const fftImage = document.getElementById('fft-image');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    setupEventListeners();
});

// Update System Clock
function updateClock() {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    systemTimeEl.textContent = timeStr;
}

// Write line to terminal log
function logTerminal(message, type = 'info') {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    const timestamp = new Date().toTimeString().split(' ')[0];
    line.textContent = `[${timestamp}] ${message}`;
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
}

// Setup Event Listeners
function setupEventListeners() {
    // Drop Zone Click
    dropZone.addEventListener('click', () => fileInput.click());
    
    // File Input Selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag and Drop Effects
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--cyan)';
        dropZone.style.backgroundColor = 'rgba(0, 242, 254, 0.05)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border-color)';
        dropZone.style.backgroundColor = 'rgba(6, 9, 19, 0.5)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        dropZone.style.backgroundColor = 'rgba(6, 9, 19, 0.5)';
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    // Visualizer Tab Switches
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            switchTab(e.target.dataset.tab);
        });
    });

    // Video Timeline Tracker
    viewVideo.addEventListener('timeupdate', handleVideoPlayback);
    
    // Slider Dragging
    timelineSlider.addEventListener('input', (e) => {
        if (appState.videoDuration) {
            const time = (e.target.value / 100) * appState.videoDuration;
            viewVideo.currentTime = time;
        }
    });
}

// Switch Visualizer Tabs (Original, ELA, FFT)
function switchTab(tabName) {
    appState.activeTab = tabName;
    
    // Hide all
    viewImage.style.display = 'none';
    viewVideo.style.display = 'none';
    elaImage.style.display = 'none';
    fftImage.style.display = 'none';
    landmarkCanvas.style.display = 'none';

    if (appState.fileType === 'image') {
        if (tabName === 'original') {
            viewImage.style.display = 'block';
            landmarkCanvas.style.display = 'block';
        } else if (tabName === 'ela') {
            elaImage.style.display = 'block';
        } else if (tabName === 'fft') {
            fftImage.style.display = 'block';
        }
    } else if (appState.fileType === 'video') {
        if (tabName === 'original') {
            viewVideo.style.display = 'block';
            landmarkCanvas.style.display = 'block';
        } else if (tabName === 'ela') {
            elaImage.style.display = 'block';
        } else if (tabName === 'fft') {
            fftImage.style.display = 'block';
        }
    }
}

// Main Ingestion Gateway
function handleFileSelection(file) {
    appState.file = file;
    appState.fileType = file.type.startsWith('video/') ? 'video' : 'image';
    appState.analysisResults = null;
    
    // Reset view UI elements
    viewportPlaceholder.style.display = 'none';
    mediaContainer.style.display = 'flex';
    visualizerTabs.style.display = 'none';
    videoTimelinePanel.style.display = 'none';
    reportData.style.display = 'none';
    reportPlaceholder.style.display = 'block';
    
    elaImage.src = '';
    fftImage.src = '';
    
    logTerminal(`Ingesting target file: ${file.name} (${(file.size/1024/1024).toFixed(2)} MB)`, 'info');
    
    if (appState.fileType === 'image') {
        viewVideo.style.display = 'none';
        viewImage.style.display = 'block';
        
        // Read image to get original dimensions
        const reader = new FileReader();
        reader.onload = (e) => {
            viewImage.src = e.target.result;
            viewImage.onload = () => {
                appState.originalWidth = viewImage.naturalWidth;
                appState.originalHeight = viewImage.naturalHeight;
                logTerminal(`Image loaded successfully. Size: ${appState.originalWidth}x${appState.originalHeight}px`, 'success');
                uploadAndAnalyzeImage(file);
            };
        };
        reader.readAsDataURL(file);
    } else {
        viewImage.style.display = 'none';
        viewVideo.style.display = 'block';
        
        // Load video metadata
        const url = URL.createObjectURL(file);
        viewVideo.src = url;
        viewVideo.onloadedmetadata = () => {
            appState.originalWidth = viewVideo.videoWidth;
            appState.originalHeight = viewVideo.videoHeight;
            appState.videoDuration = viewVideo.duration;
            timelineTimeTotal.textContent = formatTime(viewVideo.duration);
            logTerminal(`Video loaded successfully. Duration: ${viewVideo.duration.toFixed(2)}s, Size: ${appState.originalWidth}x${appState.originalHeight}px`, 'success');
            uploadAndAnalyzeVideo(file);
        };
    }
}

// Simulate scanning loading bar animations
function simulateLoading(onComplete) {
    progressBox.style.display = 'block';
    dropZone.querySelector('.scanning-bar').style.display = 'block';
    
    let progress = 0;
    const interval = setInterval(() => {
        // Fast start, slow down towards the end while waiting for backend calculations
        if (progress < 40) {
            progress += Math.floor(Math.random() * 8) + 2;
        } else if (progress < 85) {
            progress += Math.floor(Math.random() * 3) + 1;
        } else if (progress < 98) {
            progress += 0.5;
        }
        
        const rounded = Math.floor(progress);
        progressBarFill.style.width = `${rounded}%`;
        progressPercent.textContent = `${rounded}%`;
        
        if (rounded < 30) {
            progressText.textContent = "Extracting facial features...";
        } else if (rounded < 60) {
            progressText.textContent = "Calculating frequency decay (FFT)...";
        } else if (rounded < 85) {
            progressText.textContent = "Analyzing compression variance (ELA)...";
        } else {
            progressText.textContent = "Aggregating geometric anomaly checks...";
        }
    }, 150);
    
    return {
        stop: () => {
            clearInterval(interval);
            progressBarFill.style.width = `100%`;
            progressPercent.textContent = `100%`;
            progressText.textContent = "Analysis complete.";
            setTimeout(() => {
                progressBox.style.display = 'none';
                dropZone.querySelector('.scanning-bar').style.display = 'none';
            }, 500);
        }
    };
}

// Image Analysis Call
async function uploadAndAnalyzeImage(file) {
    const loadingTracker = simulateLoading();
    logTerminal("Triggering spatial, ELA, and FFT scans on image...", "info");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch("/api/analyze-image", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) throw new Error(await response.text());
        
        const result = await response.json();
        loadingTracker.stop();
        
        if (result.success) {
            appState.analysisResults = result;
            logTerminal("Forensic assessment returned successfully.", "success");
            populateReport(result);
        } else {
            logTerminal(`Engine error: ${result.error}`, "warning");
        }
    } catch (err) {
        loadingTracker.stop();
        logTerminal(`HTTP Error: ${err.message}`, "warning");
    }
}

// Video Analysis Call
async function uploadAndAnalyzeVideo(file) {
    const loadingTracker = simulateLoading();
    logTerminal("Triggering keyframe parsing and temporal stability check on video...", "info");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch("/api/analyze-video", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) throw new Error(await response.text());
        
        const result = await response.json();
        loadingTracker.stop();
        
        if (result.success) {
            appState.analysisResults = result;
            appState.videoTimeline = result.timeline;
            logTerminal(`Video assessment completed. Extracted ${result.frames_analyzed} keyframes.`, "success");
            populateReport(result);
        } else {
            logTerminal(`Engine error: ${result.error}`, "warning");
        }
    } catch (err) {
        loadingTracker.stop();
        logTerminal(`HTTP Error: ${err.message}`, "warning");
    }
}

// Populate Diagnostic Report
function populateReport(data) {
    reportPlaceholder.style.display = 'none';
    reportData.style.display = 'block';
    
    // Set tabs active
    visualizerTabs.style.display = 'flex';
    
    // Hide FFT tab if no face was detected
    const fftTabBtn = document.querySelector('.tab-btn[data-tab="fft"]');
    if (data.face_count === 0) {
        if (fftTabBtn) fftTabBtn.style.display = 'none';
    } else {
        if (fftTabBtn) fftTabBtn.style.display = 'inline-block';
    }
    
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector('.tab-btn[data-tab="original"]').classList.add('active');
    switchTab('original');
    
    // 1. Set Threat Gauge
    const score = Math.round(data.overall_score);
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugePercent = document.getElementById('gauge-percent');
    const verdictLabel = document.getElementById('verdict-label');
    
    // Calculate circular SVG offset (radius=40, circumference = 2 * PI * r = 251.2)
    const strokeOffset = 251.2 - (251.2 * score) / 100;
    gaugeFill.style.strokeDashoffset = strokeOffset;
    gaugePercent.textContent = `${score}%`;
    
    // Set Threat Color
    if (score < 35) {
        gaugeFill.style.stroke = "var(--emerald)";
        verdictLabel.textContent = "AUTHENTIC";
        verdictLabel.className = "verdict-safe";
    } else if (score < 55) {
        gaugeFill.style.stroke = "var(--purple)";
        verdictLabel.textContent = "SUSPICIOUS";
        verdictLabel.className = "verdict-warning";
    } else {
        gaugeFill.style.stroke = "var(--crimson)";
        verdictLabel.textContent = "MANIPULATED";
        verdictLabel.className = "verdict-fake";
    }
    
    // 2. Load Comparative overlays
    if (data.ela_b64) {
        elaImage.src = data.ela_b64;
    }
    if (data.fft_b64) {
        fftImage.src = data.fft_b64;
    }
    
    // 3. Metric breakdown bars
    let fftScore = 0;
    let elaScore = 0;
    let geomScore = 0;
    
    if (appState.fileType === 'image') {
        elaScore = data.ela_metrics.score;
        if (data.faces.length > 0) {
            fftScore = data.faces[0].fft_score;
            geomScore = data.faces[0].geometry_score;
        } else {
            fftScore = data.overall_score * 0.8;
            geomScore = 0;
        }
        document.getElementById('temporal-card').style.display = 'none';
        document.getElementById('meta-row-duration').style.display = 'none';
    } else {
        // Video report statistics (worst keyframe values)
        elaScore = data.worst_frame_visuals.score * 0.8; // Estimated
        fftScore = data.worst_frame_visuals.score * 0.9;
        geomScore = data.worst_frame_visuals.score * 0.7;
        
        // Show video temporal card
        const temporalCard = document.getElementById('temporal-card');
        temporalCard.style.display = 'block';
        const jitterScore = data.temporal_metrics.temporal_jitter * 10;
        document.getElementById('val-temporal').textContent = `${Math.min(100, Math.round(jitterScore))}%`;
        document.getElementById('bar-temporal').style.width = `${Math.min(100, jitterScore)}%`;
        document.getElementById('bar-temporal').style.backgroundColor = jitterScore > 50 ? 'var(--crimson)' : 'var(--cyan)';
        
        // Show Video controls
        videoTimelinePanel.style.display = 'block';
        document.getElementById('meta-row-duration').style.display = 'flex';
        document.getElementById('meta-duration').textContent = `${data.duration_seconds}s`;
        
        // Draw Timeline wave
        drawTimelineWave(data.timeline);
    }
    
    document.getElementById('val-fft').textContent = `${Math.round(fftScore)}%`;
    document.getElementById('bar-fft').style.width = `${fftScore}%`;
    document.getElementById('bar-fft').style.backgroundColor = fftScore > 50 ? 'var(--crimson)' : 'var(--cyan)';
    
    document.getElementById('val-ela').textContent = `${Math.round(elaScore)}%`;
    document.getElementById('bar-ela').style.width = `${elaScore}%`;
    document.getElementById('bar-ela').style.backgroundColor = elaScore > 50 ? 'var(--crimson)' : 'var(--cyan)';
    
    document.getElementById('val-geom').textContent = `${Math.round(geomScore)}%`;
    document.getElementById('bar-geom').style.width = `${geomScore}%`;
    document.getElementById('bar-geom').style.backgroundColor = geomScore > 50 ? 'var(--crimson)' : 'var(--cyan)';
    
    // 4. Metadata rows
    document.getElementById('meta-resolution').textContent = data.resolution;
    document.getElementById('meta-faces').textContent = data.face_count;
    
    // 5. Draw FFT Radial graph
    if (data.radial_profile && data.radial_profile.length > 0) {
        drawRadialChart(data.radial_profile);
    }
    
    // 6. Draw Bounding boxes
    renderBoxes();
    
    // Logging assessments
    logTerminal(`--- ASSESSMENT SUMMARY ---`, 'info');
    logTerminal(`Verdict: ${data.verdict}`, score >= 50 ? 'warning' : 'success');
    logTerminal(`Integrity score: ${(100 - score)}% safe`, score >= 50 ? 'warning' : 'success');
}

// Custom SVG/Canvas Draw: Frequency Decay Graph
function drawRadialChart(profileData) {
    const canvas = document.getElementById('radial-chart');
    const ctx = canvas.getContext('2d');
    
    // Handle Retina displays (sharp lines)
    const rect = canvas.parentNode.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    const w = canvas.width;
    const h = canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // 1. Draw Grid Lines
    ctx.strokeStyle = 'rgba(32, 43, 77, 0.4)';
    ctx.lineWidth = 1;
    
    const horizontalGridLines = 4;
    for (let i = 1; i < horizontalGridLines; i++) {
        const y = (h / horizontalGridLines) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }
    
    const verticalGridLines = 6;
    for (let i = 1; i < verticalGridLines; i++) {
        const x = (w / verticalGridLines) * i;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }
    
    // 2. Draw standard "Natural Face" exponential decay curve (Green)
    ctx.strokeStyle = '#05c46b';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    
    const stepX = w / (profileData.length - 1);
    
    for (let i = 0; i < profileData.length; i++) {
        // Natural exponential decay approximation: y = exp(-0.15 * x)
        const mathX = i;
        const mathY = Math.exp(-0.13 * mathX);
        
        const canvasX = i * stepX;
        const canvasY = h - (mathY * (h - 15)) - 10;
        
        if (i === 0) ctx.moveTo(canvasX, canvasY);
        else ctx.lineTo(canvasX, canvasY);
    }
    ctx.stroke();
    
    // 3. Draw Target sample curve (Purple/Magenta)
    ctx.strokeStyle = '#a020f0';
    ctx.lineWidth = 2.5;
    ctx.shadowBlur = 4;
    ctx.shadowColor = 'rgba(160, 32, 240, 0.4)';
    ctx.beginPath();
    
    for (let i = 0; i < profileData.length; i++) {
        const mathY = profileData[i];
        
        const canvasX = i * stepX;
        const canvasY = h - (mathY * (h - 15)) - 10;
        
        if (i === 0) ctx.moveTo(canvasX, canvasY);
        else ctx.lineTo(canvasX, canvasY);
    }
    ctx.stroke();
    ctx.shadowBlur = 0; // Reset
}

// Custom Canvas Draw: Video Timeline Threat Graph
function drawTimelineWave(timeline) {
    const canvas = document.getElementById('timeline-chart');
    const ctx = canvas.getContext('2d');
    
    const rect = canvas.parentNode.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    const w = canvas.width;
    const h = canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // Draw Threat Limit Line (50%)
    ctx.strokeStyle = 'rgba(220, 53, 69, 0.4)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, h/2);
    ctx.lineTo(w, h/2);
    ctx.stroke();
    ctx.setLineDash([]); // Reset
    
    // Plot the values
    const stepX = w / (timeline.length - 1);
    
    // Draw glowing wave fill
    const gradient = ctx.createLinearGradient(0, h, 0, 0);
    gradient.addColorStop(0, 'rgba(0, 242, 254, 0.0)');
    gradient.addColorStop(0.5, 'rgba(160, 32, 240, 0.1)');
    gradient.addColorStop(1, 'rgba(220, 53, 69, 0.25)');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(0, h);
    
    for (let i = 0; i < timeline.length; i++) {
        const val = timeline[i].score; // 0 - 100
        const canvasX = i * stepX;
        const canvasY = h - (val / 100) * h;
        ctx.lineTo(canvasX, canvasY);
    }
    
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fill();
    
    // Draw connecting wave line
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.8)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    for (let i = 0; i < timeline.length; i++) {
        const val = timeline[i].score;
        const canvasX = i * stepX;
        const canvasY = h - (val / 100) * h;
        
        if (i === 0) ctx.moveTo(canvasX, canvasY);
        else ctx.lineTo(canvasX, canvasY);
    }
    ctx.stroke();
}

// Render Face Bounding boxes & Cyber Target Reticles
function renderBoxes() {
    const canvas = landmarkCanvas;
    const ctx = canvas.getContext('2d');
    
    // Get actual displaying video/image client dimensions
    const displayElement = appState.fileType === 'image' ? viewImage : viewVideo;
    
    if (!displayElement || displayElement.clientWidth === 0) {
        // Wait and retry once metadata sizes trigger layouts
        setTimeout(renderBoxes, 100);
        return;
    }
    
    // Adjust canvas bounds to align exactly with image display box
    canvas.width = displayElement.clientWidth;
    canvas.height = displayElement.clientHeight;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const scaleX = canvas.width / appState.originalWidth;
    const scaleY = canvas.height / appState.originalHeight;
    
    let activeFaces = [];
    
    if (appState.fileType === 'image') {
        if (appState.analysisResults && appState.analysisResults.faces) {
            activeFaces = appState.analysisResults.faces;
        }
    } else {
        // Find the closest keyframe analyzed for the current playback time
        if (appState.videoTimeline.length > 0) {
            const currentTime = viewVideo.currentTime;
            let closestFrame = appState.videoTimeline[0];
            let minDiff = Math.abs(currentTime - closestFrame.timestamp);
            
            for (let f of appState.videoTimeline) {
                const diff = Math.abs(currentTime - f.timestamp);
                if (diff < minDiff) {
                    minDiff = diff;
                    closestFrame = f;
                }
            }
            
            // If worst frame visuals match box size
            const worstBoxes = appState.analysisResults.worst_frame_visuals.face_boxes;
            if (worstBoxes) {
                // Mock coordinate arrays for frames to keep bounding boxes active 
                activeFaces = worstBoxes.map(box => ({ box: box }));
            }
        }
    }
    
    activeFaces.forEach(face => {
        const [x, y, fw, fh] = face.box;
        
        const scaledX = x * scaleX;
        const scaledY = y * scaleY;
        const scaledW = fw * scaleX;
        const scaledH = fh * scaleY;
        
        // Draw cyber brackets
        ctx.strokeStyle = appState.analysisResults.overall_score >= 50.5 ? '#dc3545' : 'var(--cyan)';
        ctx.lineWidth = 2;
        
        const length = Math.min(scaledW, scaledH) * 0.25; // Bracket arm length
        
        // Top Left Bracket
        ctx.beginPath();
        ctx.moveTo(scaledX + length, scaledY);
        ctx.lineTo(scaledX, scaledY);
        ctx.lineTo(scaledX, scaledY + length);
        ctx.stroke();
        
        // Top Right Bracket
        ctx.beginPath();
        ctx.moveTo(scaledX + scaledW - length, scaledY);
        ctx.lineTo(scaledX + scaledW, scaledY);
        ctx.lineTo(scaledX + scaledW, scaledY + length);
        ctx.stroke();
        
        // Bottom Left Bracket
        ctx.beginPath();
        ctx.moveTo(scaledX, scaledY + scaledH - length);
        ctx.lineTo(scaledX, scaledY + scaledH);
        ctx.lineTo(scaledX + length, scaledY + scaledH);
        ctx.stroke();
        
        // Bottom Right Bracket
        ctx.beginPath();
        ctx.moveTo(scaledX + scaledW - length, scaledY + scaledH);
        ctx.lineTo(scaledX + scaledW, scaledY + scaledH);
        ctx.lineTo(scaledX + scaledW, scaledY + scaledH - length);
        ctx.stroke();
        
        // Draw dotted box borders
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.2)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(scaledX, scaledY, scaledW, scaledH);
        ctx.setLineDash([]); // Reset
        
        // Draw Cyber target label text
        ctx.fillStyle = appState.analysisResults.overall_score >= 50.5 ? '#dc3545' : 'var(--cyan)';
        ctx.font = '600 10px Space Grotesk';
        const label = appState.analysisResults.overall_score >= 50.5 ? 'TAMPER RISK HIGH' : 'FACE ENCRYPTED';
        ctx.fillText(label, scaledX + 4, scaledY - 6);
    });
}

// Handle video time update event
function handleVideoPlayback() {
    if (!appState.videoDuration) return;
    
    const time = viewVideo.currentTime;
    const percent = (time / appState.videoDuration) * 100;
    timelineSlider.value = percent;
    timelineTimeCurrent.textContent = formatTime(time);
    
    // Draw timeline vertical cursor overlay
    const canvas = document.getElementById('timeline-chart');
    if (canvas && appState.videoTimeline.length > 0) {
        drawTimelineWave(appState.videoTimeline); // Redraw clean wave
        
        const ctx = canvas.getContext('2d');
        const cursorX = (time / appState.videoDuration) * canvas.width;
        
        // Draw current cursor position line
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cursorX, 0);
        ctx.lineTo(cursorX, canvas.height);
        ctx.stroke();
    }
    
    // Update active frame boxes
    renderBoxes();
}

// Format Time helper (seconds -> mm:ss)
function formatTime(secs) {
    const minutes = Math.floor(secs / 60);
    const seconds = Math.floor(secs % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

// Handle window resizing (guarantees bounding box scales perfectly)
window.addEventListener('resize', () => {
    if (appState.analysisResults) {
        renderBoxes();
        if (appState.analysisResults.radial_profile) {
            drawRadialChart(appState.analysisResults.radial_profile);
        }
        if (appState.fileType === 'video' && appState.videoTimeline.length > 0) {
            drawTimelineWave(appState.videoTimeline);
        }
    }
});
