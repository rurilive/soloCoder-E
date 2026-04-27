class ConferenceManager {
    constructor(roomCode, userId, username, isHost) {
        this.roomCode = roomCode;
        this.userId = userId;
        this.username = username;
        this.isHost = isHost;
        
        this.ws = null;
        this.localStream = null;
        this.screenStream = null;
        this.peerConnections = new Map();
        this.remoteStreams = new Map();
        this.participants = new Map();
        
        this.audioMuted = false;
        this.videoMuted = false;
        this.screenSharing = false;
        this.recording = false;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.recordingStartTime = null;
        
        this.iceServers = [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
        ];
    }
    
    async init() {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            this.renderLocalVideo();
        } catch (err) {
            console.error('Failed to get media devices:', err);
            this.renderPlaceholderVideo(this.userId, this.username, true);
        }
        
        await this.connectWebSocket();
    }
    
    async connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/conference/ws/${this.roomCode}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            await this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket closed');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    async handleMessage(data) {
        const { type, ...payload } = data;
        
        switch (type) {
            case 'room_joined':
                await this.handleRoomJoined(payload);
                break;
            case 'participant_joined':
                await this.handleParticipantJoined(payload);
                break;
            case 'participant_left':
                this.handleParticipantLeft(payload);
                break;
            case 'offer':
                await this.handleOffer(payload);
                break;
            case 'answer':
                await this.handleAnswer(payload);
                break;
            case 'ice_candidate':
                await this.handleICECandidate(payload);
                break;
            case 'chat_message':
                this.handleChatMessage(payload);
                break;
            case 'audio_muted':
                this.handleAudioMuted(payload);
                break;
            case 'video_muted':
                this.handleVideoMuted(payload);
                break;
            case 'screen_share_start':
                this.handleScreenShareStart(payload);
                break;
            case 'screen_share_stop':
                this.handleScreenShareStop(payload);
                break;
            case 'recording_started':
                this.handleRecordingStarted(payload);
                break;
            case 'recording_stopped':
                this.handleRecordingStopped(payload);
                break;
        }
    }
    
    async handleRoomJoined(payload) {
        const { participants, is_host } = payload;
        
        for (const p of participants) {
            if (p.user_id !== this.userId) {
                this.participants.set(p.user_id, p);
            }
        }
        
        this.updateParticipantList();
        this.updateVideoGrid();
        
        for (const p of participants) {
            if (p.user_id !== this.userId) {
                await this.createPeerConnection(p.user_id, true);
            }
        }
    }
    
    async handleParticipantJoined(payload) {
        const { user_id, username, participants } = payload;
        
        if (user_id === this.userId) return;
        
        console.log('Participant joined:', username);
        this.participants.set(user_id, { user_id, username });
        this.updateParticipantList();
        
        await this.createPeerConnection(user_id, false);
    }
    
    handleParticipantLeft(payload) {
        const { user_id, username } = payload;
        
        console.log('Participant left:', username);
        
        const pc = this.peerConnections.get(user_id);
        if (pc) {
            pc.close();
            this.peerConnections.delete(user_id);
        }
        
        this.remoteStreams.delete(user_id);
        this.participants.delete(user_id);
        
        this.updateParticipantList();
        this.updateVideoGrid();
    }
    
    async createPeerConnection(targetUserId, isInitiator) {
        if (this.peerConnections.has(targetUserId)) {
            return this.peerConnections.get(targetUserId);
        }
        
        const pc = new RTCPeerConnection({
            iceServers: this.iceServers
        });
        
        this.peerConnections.set(targetUserId, pc);
        
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                pc.addTrack(track, this.localStream);
            });
        }
        
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendMessage({
                    type: 'ice_candidate',
                    target_user_id: targetUserId,
                    candidate: event.candidate
                });
            }
        };
        
        pc.ontrack = (event) => {
            const [stream] = event.streams;
            this.remoteStreams.set(targetUserId, stream);
            this.renderRemoteVideo(targetUserId, stream);
        };
        
        pc.onconnectionstatechange = () => {
            console.log('Connection state:', pc.connectionState);
            if (pc.connectionState === 'connected') {
                this.updateVideoGrid();
            }
        };
        
        if (isInitiator) {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            
            this.sendMessage({
                type: 'offer',
                target_user_id: targetUserId,
                offer: pc.localDescription
            });
        }
        
        return pc;
    }
    
    async handleOffer(payload) {
        const { from_user_id, offer } = payload;
        
        let pc = this.peerConnections.get(from_user_id);
        if (!pc) {
            pc = await this.createPeerConnection(from_user_id, false);
        }
        
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        this.sendMessage({
            type: 'answer',
            target_user_id: from_user_id,
            answer: pc.localDescription
        });
    }
    
    async handleAnswer(payload) {
        const { from_user_id, answer } = payload;
        
        const pc = this.peerConnections.get(from_user_id);
        if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
        }
    }
    
    async handleICECandidate(payload) {
        const { from_user_id, candidate } = payload;
        
        const pc = this.peerConnections.get(from_user_id);
        if (pc && candidate) {
            await pc.addIceCandidate(new RTCIceCandidate(candidate));
        }
    }
    
    sendMessage(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    renderLocalVideo() {
        const grid = document.getElementById('videoGrid');
        let container = document.getElementById(`video-${this.userId}`);
        
        if (!container) {
            container = document.createElement('div');
            container.id = `video-${this.userId}`;
            container.className = 'video-container';
            grid.appendChild(container);
        }
        
        container.innerHTML = `
            <video autoplay playsinline muted style="transform: scaleX(-1);"></video>
            <div class="video-label">${this.username} (我)</div>
            <div class="video-controls">
                <button class="video-control-btn audio-status" title="音频">🔊</button>
                <button class="video-control-btn video-status" title="视频">📹</button>
            </div>
        `;
        
        const video = container.querySelector('video');
        video.srcObject = this.localStream;
        
        this.updateVideoGrid();
    }
    
    renderPlaceholderVideo(userId, username, isLocal = false) {
        const grid = document.getElementById('videoGrid');
        let container = document.getElementById(`video-${userId}`);
        
        if (!container) {
            container = document.createElement('div');
            container.id = `video-${userId}`;
            container.className = 'video-container';
            grid.appendChild(container);
        }
        
        container.innerHTML = `
            <div class="no-video-placeholder">
                <div class="no-video-icon">👤</div>
                <div>${username}${isLocal ? ' (我)' : ''}</div>
            </div>
            <div class="video-label">${username}${isLocal ? ' (我)' : ''}</div>
        `;
        
        this.updateVideoGrid();
    }
    
    renderRemoteVideo(userId, stream) {
        const participant = this.participants.get(userId);
        const username = participant ? participant.username : `用户 ${userId}`;
        
        const grid = document.getElementById('videoGrid');
        let container = document.getElementById(`video-${userId}`);
        
        if (!container) {
            container = document.createElement('div');
            container.id = `video-${userId}`;
            container.className = 'video-container';
            grid.appendChild(container);
        }
        
        container.innerHTML = `
            <video autoplay playsinline></video>
            <div class="video-label">${username}</div>
            <div class="video-controls">
                <button class="video-control-btn audio-status" title="音频">🔊</button>
                <button class="video-control-btn video-status" title="视频">📹</button>
            </div>
        `;
        
        const video = container.querySelector('video');
        video.srcObject = stream;
        
        this.updateVideoGrid();
    }
    
    updateVideoGrid() {
        const grid = document.getElementById('videoGrid');
        const participantCount = this.participants.size + 1;
        
        grid.className = 'video-grid';
        if (participantCount === 1) {
            grid.classList.add('participants-1');
        } else if (participantCount === 2) {
            grid.classList.add('participants-2');
        } else if (participantCount <= 4) {
            grid.classList.add('participants-4');
        } else {
            grid.classList.add('participants-more');
        }
    }
    
    updateParticipantList() {
        const list = document.getElementById('participantList');
        list.innerHTML = '';
        
        list.innerHTML += `
            <div class="participant-item" data-user-id="${this.userId}">
                <div class="participant-avatar">${this.username[0].toUpperCase()}</div>
                <div class="participant-info">
                    <div class="participant-name">
                        ${this.username}
                        ${this.isHost ? '<span class="participant-badge">房主</span>' : ''}
                    </div>
                    <div class="participant-status">
                        ${this.audioMuted ? '🔇 静音' : '🔊 音频'}
                        ${this.videoMuted ? ' | 📷 视频关闭' : ' | 📹 视频开启'}
                    </div>
                </div>
            </div>
        `;
        
        this.participants.forEach((p, userId) => {
            list.innerHTML += `
                <div class="participant-item" data-user-id="${userId}">
                    <div class="participant-avatar">${p.username[0].toUpperCase()}</div>
                    <div class="participant-info">
                        <div class="participant-name">${p.username}</div>
                        <div class="participant-status">
                            ${p.audio_muted ? '🔇 静音' : '🔊 音频'}
                            ${p.video_muted ? ' | 📷 视频关闭' : ' | 📹 视频开启'}
                            ${p.screen_sharing ? ' | 🖥️ 共享中' : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        const tabs = document.querySelectorAll('.sidebar-tab');
        tabs[1].textContent = `参与者 (${this.participants.size + 1})`;
    }
    
    handleChatMessage(payload) {
        const { user_id, username, message, timestamp } = payload;
        const isOwn = user_id === this.userId;
        
        this.addChatMessage(username, message, isOwn);
    }
    
    addChatMessage(username, message, isOwn) {
        const chatMessages = document.getElementById('chatMessages');
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${isOwn ? 'own' : 'other'}`;
        msgDiv.innerHTML = `
            <div class="chat-sender">${username}</div>
            <div>${message}</div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    handleAudioMuted(payload) {
        const { user_id, muted } = payload;
        
        if (user_id === this.userId) {
            this.audioMuted = muted;
        } else {
            const p = this.participants.get(user_id);
            if (p) {
                p.audio_muted = muted;
            }
        }
        
        this.updateParticipantList();
    }
    
    handleVideoMuted(payload) {
        const { user_id, muted } = payload;
        
        if (user_id === this.userId) {
            this.videoMuted = muted;
        } else {
            const p = this.participants.get(user_id);
            if (p) {
                p.video_muted = muted;
            }
        }
        
        this.updateParticipantList();
    }
    
    handleScreenShareStart(payload) {
        const { user_id, username } = payload;
        
        if (user_id === this.userId) {
            this.screenSharing = true;
        } else {
            const p = this.participants.get(user_id);
            if (p) {
                p.screen_sharing = true;
            }
        }
        
        this.updateParticipantList();
    }
    
    handleScreenShareStop(payload) {
        const { user_id } = payload;
        
        if (user_id === this.userId) {
            this.screenSharing = false;
        } else {
            const p = this.participants.get(user_id);
            if (p) {
                p.screen_sharing = false;
            }
        }
        
        this.updateParticipantList();
    }
    
    handleRecordingStarted(payload) {
        this.recording = true;
        const btn = document.getElementById('recordBtn');
        if (btn) {
            btn.classList.add('active');
            btn.title = '停止录制';
        }
    }
    
    handleRecordingStopped(payload) {
        this.recording = false;
        const btn = document.getElementById('recordBtn');
        if (btn) {
            btn.classList.remove('active');
            btn.title = '录制';
        }
    }
    
    toggleAudio() {
        this.audioMuted = !this.audioMuted;
        
        if (this.localStream) {
            this.localStream.getAudioTracks().forEach(track => {
                track.enabled = !this.audioMuted;
            });
        }
        
        this.sendMessage({
            type: 'mute_audio',
            muted: this.audioMuted
        });
        
        const btn = document.getElementById('audioBtn');
        if (this.audioMuted) {
            btn.classList.add('muted');
            btn.textContent = '🔇';
        } else {
            btn.classList.remove('muted');
            btn.textContent = '🎤';
        }
    }
    
    toggleVideo() {
        this.videoMuted = !this.videoMuted;
        
        if (this.localStream) {
            this.localStream.getVideoTracks().forEach(track => {
                track.enabled = !this.videoMuted;
            });
        }
        
        this.sendMessage({
            type: 'mute_video',
            muted: this.videoMuted
        });
        
        const btn = document.getElementById('videoBtn');
        if (this.videoMuted) {
            btn.classList.add('muted');
            btn.textContent = '📷';
        } else {
            btn.classList.remove('muted');
            btn.textContent = '📹';
        }
    }
    
    async toggleScreenShare() {
        if (this.screenSharing) {
            await this.stopScreenShare();
        } else {
            await this.startScreenShare();
        }
    }
    
    async startScreenShare() {
        try {
            this.screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: true
            });
            
            this.peerConnections.forEach((pc, userId) => {
                if (this.screenStream) {
                    this.screenStream.getTracks().forEach(track => {
                        pc.addTrack(track, this.screenStream);
                    });
                }
            });
            
            this.screenSharing = true;
            this.sendMessage({
                type: 'screen_share_start'
            });
            
            const btn = document.getElementById('screenBtn');
            btn.classList.add('active');
            
            this.screenStream.getVideoTracks()[0].onended = () => {
                this.stopScreenShare();
            };
            
        } catch (err) {
            console.error('Failed to start screen share:', err);
        }
    }
    
    async stopScreenShare() {
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
            this.screenStream = null;
        }
        
        this.screenSharing = false;
        this.sendMessage({
            type: 'screen_share_stop'
        });
        
        const btn = document.getElementById('screenBtn');
        btn.classList.remove('active');
    }
    
    async toggleRecording() {
        if (this.recording) {
            await this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        if (!this.localStream) {
            alert('需要先开启摄像头和麦克风');
            return;
        }
        
        this.sendMessage({
            type: 'start_recording'
        });
        
        this.recording = true;
        this.recordingStartTime = Date.now();
        this.recordedChunks = [];
        
        try {
            const stream = new MediaStream();
            
            const audioContext = new AudioContext();
            const destination = audioContext.createMediaStreamDestination();
            
            if (this.localStream.getAudioTracks().length > 0) {
                const source = audioContext.createMediaStreamSource(this.localStream);
                source.connect(destination);
            }
            
            if (destination.stream.getAudioTracks().length > 0) {
                stream.addTrack(destination.stream.getAudioTracks()[0]);
            }
            
            if (this.localStream.getVideoTracks().length > 0) {
                stream.addTrack(this.localStream.getVideoTracks()[0]);
            }
            
            const mimeTypes = [
                'video/webm;codecs=vp9,opus',
                'video/webm;codecs=vp8,opus',
                'video/webm',
                'video/mp4',
            ];
            
            let selectedMimeType = '';
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    break;
                }
            }
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: selectedMimeType || 'video/webm'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                await this.saveRecording();
            };
            
            this.mediaRecorder.start(1000);
            
        } catch (err) {
            console.error('Failed to start recording:', err);
            alert('录制功能不可用: ' + err.message);
            this.recording = false;
        }
    }
    
    async stopRecording() {
        this.sendMessage({
            type: 'stop_recording'
        });
        
        this.recording = false;
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
    }
    
    async saveRecording() {
        if (this.recordedChunks.length === 0) return;
        
        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        const duration = Math.floor((Date.now() - this.recordingStartTime) / 1000);
        
        const formData = new FormData();
        formData.append('file', blob, `recording_${this.roomCode}.webm`);
        formData.append('room_code', this.roomCode);
        formData.append('duration', duration.toString());
        
        try {
            const response = await fetch('/recording/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                alert('录制已保存！可以在"我的录制"中查看。');
            } else {
                alert('保存录制失败');
            }
        } catch (err) {
            console.error('Failed to upload recording:', err);
            alert('上传录制失败: ' + err.message);
        }
    }
    
    sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.sendMessage({
            type: 'chat_message',
            message: message
        });
        
        input.value = '';
    }
    
    leaveRoom() {
        if (this.recording) {
            this.stopRecording();
        }
        
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        
        this.peerConnections.forEach(pc => pc.close());
        
        if (this.ws) {
            this.ws.close();
        }
        
        window.location.href = '/conference/';
    }
}

let conferenceManager = null;

async function initConference() {
    if (typeof currentUser === 'undefined' || !currentUser) {
        window.location.href = '/auth/login';
        return;
    }
    
    const isHost = roomConfig && roomConfig.host_id === currentUser.user_id;
    
    conferenceManager = new ConferenceManager(
        roomConfig.room_code,
        currentUser.user_id,
        currentUser.display_name || currentUser.username,
        isHost
    );
    
    await conferenceManager.init();
}

function toggleAudio() {
    if (conferenceManager) conferenceManager.toggleAudio();
}

function toggleVideo() {
    if (conferenceManager) conferenceManager.toggleVideo();
}

function toggleScreenShare() {
    if (conferenceManager) conferenceManager.toggleScreenShare();
}

function toggleRecording() {
    if (conferenceManager) conferenceManager.toggleRecording();
}

function sendChatMessage() {
    if (conferenceManager) conferenceManager.sendChatMessage();
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function leaveRoom() {
    if (conferenceManager) conferenceManager.leaveRoom();
}

function switchTab(tab) {
    document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    
    document.querySelector(`.sidebar-tab[onclick="switchTab('${tab}')"]`).classList.add('active');
    document.getElementById(`${tab}Panel`).classList.add('active');
}

function copyRoomCode(code) {
    navigator.clipboard.writeText(code).then(() => {
        alert('房间码已复制: ' + code);
    }).catch(() => {
        prompt('复制房间码:', code);
    });
}

function stopScreenShareView() {
    document.getElementById('screenShareContainer').classList.remove('active');
}

document.addEventListener('DOMContentLoaded', initConference);
