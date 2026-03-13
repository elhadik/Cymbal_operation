const video = document.getElementById('video-feed');
const placeholder = document.getElementById('placeholder');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const statusText = document.getElementById('status-text');
const connectionDot = document.getElementById('connection-dot');

let ws = null;
let localStream = null;
let mediaRecorder = null;
let audioContext = null;
let audioQueue = [];
let isPlaying = false;
let frameInterval = null;
let speechRecognition = null;
let recentModelTexts = [];

// UI Elements
const transcriptBox = document.getElementById('transcript-box');

let lastSpeaker = null;
let currentContentNode = null;
let lastAudioPlayTime = 0;
let isScanning = false;
let currentAudioSource = null;

function appendTranscript(text, role, forceNew = false, isContinuation = false) {
    if (!text || text.trim() === '') return;
    
    // If the speaker is the same as the last message AND we aren't forcing a new bubble, append or replace
    if (!forceNew && lastSpeaker === role && currentContentNode) {
        if (isContinuation) {
            // It's the full string being yielded again
            currentContentNode.innerText = text.trim();
        } else {
            // It's a new incremental chunk
            currentContentNode.innerText += " " + text.trim();
        }
        transcriptBox.scrollTop = transcriptBox.scrollHeight;
        return;
    }

    // Otherwise, create a new bubble.
    lastSpeaker = role;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const title = document.createElement('div');
    title.className = 'message-title';
    title.innerText = role === 'user' ? 'You' : 'Assistant';
    
    currentContentNode = document.createElement('span');
    currentContentNode.className = 'message-text';
    currentContentNode.innerText = text.trim();
    
    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-content';
    contentWrapper.appendChild(currentContentNode);
    
    msgDiv.appendChild(title);
    msgDiv.appendChild(contentWrapper);
    transcriptBox.appendChild(msgDiv);
    transcriptBox.scrollTop = transcriptBox.scrollHeight;
}

let typingIndicatorEl = null;

function showTypingIndicator() {
    if (typingIndicatorEl) return;
    typingIndicatorEl = document.createElement('div');
    typingIndicatorEl.className = 'typing-indicator';
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        typingIndicatorEl.appendChild(dot);
    }
    transcriptBox.appendChild(typingIndicatorEl);
    transcriptBox.scrollTop = transcriptBox.scrollHeight;
}

function hideTypingIndicator() {
    if (typingIndicatorEl) {
        typingIndicatorEl.remove();
        typingIndicatorEl = null;
    }
}

// Audio Playback functionality
async function playNextAudio() {
    if (isPlaying || audioQueue.length === 0 || isScanning) return;
    isPlaying = true;

    try {
        const item = audioQueue.shift();

        if (item.type === 'signal' && item.name === 'barcode') {
            console.log("Playing sequenced barcode animation...");
            const scannerLine = document.getElementById('scanner-line');
            if (scannerLine) {
                isScanning = true;
                scannerLine.classList.add('active');
                
                // CRITICAL: We wait exactly 1.5 seconds for the scan animation to visually complete.
                // This MUST match the `animation: scan 1.5s` CSS exactly to perform a single clean pass.
                setTimeout(() => {
                    scannerLine.classList.remove('active');
                    isScanning = false;
                    isPlaying = false;
                    
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'scan_completed' }));
                    }

                    playNextAudio();
                }, 1500);
            } else {
                isPlaying = false;
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'scan_completed' }));
                }

                playNextAudio();
            }
            return;
            return;
        }

        if (item.type === 'signal' && item.name === 'show_widget') {
            console.log("Playing sequenced widget display...");
            const panel = document.getElementById('fulfillment-panel');
            panel.style.display = 'flex';
        
            // Show Insulin First
            panel.innerHTML = `
                <div class="fulfillment-widget">
                    <div class="widget-image">
                        Medicine Image Placeholder
                    </div>
                    <div class="widget-details">
                        <h3 class="widget-title">Insulin</h3>
                        <p class="widget-meta">
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Aisle 2 • Refrigerated
                        </p>
                    </div>
                    <button class="widget-btn" onclick="showCreonWidget()">Added to order package</button>
                </div>
            `;
            
            window.showCreonWidget = function() {
                panel.innerHTML = `
                    <div class="fulfillment-widget fade-in">
                        <div class="widget-image">
                            Medicine Image Placeholder
                        </div>
                        <div class="widget-details">
                            <h3 class="widget-title">Creon</h3>
                            <p class="widget-meta">
                                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                Aisle 4 • Room Temperature
                            </p>
                        </div>
                        <button class="widget-btn" onclick="finishChecklist()">Added to order package</button>
                    </div>
                `;
            };
            
            window.finishChecklist = function() {
                panel.innerHTML = `
                    <div class="fade-in" style="color: #22c55e; display: flex; flex-direction: column; align-items: center; gap: 1rem;">
                        <svg width="64" height="64" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <h2>Order Package Complete</h2>
                    </div>
                `;
                
                setTimeout(() => {
                    panel.style.display = 'none';
                    window._checklistPending = false; // Reset for future interactions
                }, 3000);
                
                // Send confirmation message back to Gemini silently so it concludes the flow
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        clientContent: {
                            turns: [{
                                parts: [{text: "User clicked: Added both items to package"}]
                            }]
                        }
                    }));
                }
            };
            
            isPlaying = false;
            // Instantly move to next item
            setTimeout(playNextAudio, 0);
            return;
        }
        
        if (item.type === 'text') {
            appendTranscript(item.text, item.role, item.forceNew, item.isContinuation);
            isPlaying = false;
            // Instantly move to next item
            setTimeout(playNextAudio, 0);
            return;
        }

        const audioData = item.data;
        
        // Convert base64 to array buffer
        const binaryString = window.atob(audioData);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        // Initialize AudioContext if needed
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000 // Gemini Live API outputs audio at 24000Hz
            });
        }

        // The Gemini API returns raw PCM16 data, we need to convert to Float32Audio
        const pcm16Data = new Int16Array(bytes.buffer);
        const float32Data = new Float32Array(pcm16Data.length);
        for (let i = 0; i < pcm16Data.length; i++) {
            float32Data[i] = pcm16Data[i] / 32768.0; // Normalize 16-bit PCM to [-1, 1]
        }

        const audioBuffer = audioContext.createBuffer(1, float32Data.length, 24000);
        audioBuffer.getChannelData(0).set(float32Data);

        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);

        currentAudioSource = source;

        source.onended = () => {
            currentAudioSource = null;
            isPlaying = false;
            lastAudioPlayTime = Date.now();
            if (audioQueue.length === 0 && speechRecognition) {
                // Agent finished speaking entirely. Restart mic recognition.
                try { speechRecognition.start(); } catch(e) {}
            }
            playNextAudio();
        };

        source.start(0);
    } catch (e) {
        console.error("Error playing audio/signal:", e);
        isPlaying = false;
        playNextAudio();
    }
}

// Start Stream functionality
startBtn.addEventListener('click', async () => {
    try {
        // Request Camera & Mic
        try {
            localStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 15 }
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    channelCount: 1,
                    sampleRate: 16000
                }
            });

            video.srcObject = localStream;
            placeholder.style.display = 'none';
        } catch (mediaError) {
            console.warn("Camera/Mic not found or denied, proceeding with connection anyway:", mediaError);
            statusText.textContent = `Warning: ${mediaError.name}. Connecting anyway...`;
        }

        // Connect to WebSocket regardless of media devices
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        ws.onopen = () => {
            statusText.textContent = "Connected to Cymbal Agent";
            connectionDot.classList.add('active');
            startBtn.disabled = true;
            stopBtn.disabled = false;

            if (typeof localStream !== 'undefined' && localStream) {
                // Start sending video frames (1 per second to save bandwidth for Live API)
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.width = 1280;
                canvas.height = 720;

                frameInterval = setInterval(() => {
                    // Do NOT send video frames if the agent is blocked on tool execution/scanning
                    if (isScanning || window._muteAgentUntilWidget) return;

                    if (ws.readyState === WebSocket.OPEN && video.readyState === video.HAVE_ENOUGH_DATA) {
                        context.drawImage(video, 0, 0, canvas.width, canvas.height);
                        // Use higher quality JPEG (0.8 instead of 0.5) so Gemini can actually read barcodes
                        const imageData = canvas.toDataURL('image/jpeg', 0.8);
                        ws.send(JSON.stringify({
                            type: 'image',
                            data: imageData
                        }));
                    }
                }, 1000);

                // Delay sending the first audio chunks slightly to ensure Gemini's 
                // backend connection is fully initialized and listening.
                setTimeout(() => {
                    if (ws.readyState !== WebSocket.OPEN) return;
                    
                    const source = new (window.AudioContext || window.webkitAudioContext)({
                        sampleRate: 16000
                    }).createMediaStreamSource(localStream);
                    
                    const processor = source.context.createScriptProcessor(4096, 1, 1);
                    source.connect(processor);
                    processor.connect(source.context.destination);
                    
                    processor.onaudioprocess = (e) => {
                        if (ws.readyState !== WebSocket.OPEN) return;
                        
                        // Mute microphone output to Gemini while the agent is speaking or thinking/executing tools
                        // We include a 500ms grace period after audio finishes
                        if (isPlaying || audioQueue.length > 0 || (Date.now() - lastAudioPlayTime < 500) || isScanning || window._muteAgentUntilWidget) {
                            return; 
                        }
                        
                        const inputData = e.inputBuffer.getChannelData(0);
                        // Convert Float32 to Int16
                        const pcm16Data = new Int16Array(inputData.length);
                        for (let i = 0; i < inputData.length; i++) {
                            const s = Math.max(-1, Math.min(1, inputData[i]));
                            pcm16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }
                        
                        // Convert to Base64
                        const bytes = new Uint8Array(pcm16Data.buffer);
                        let binary = '';
                        for (let i = 0; i < bytes.byteLength; i++) {
                            binary += String.fromCharCode(bytes[i]);
                        }
                        const base64Audio = window.btoa(binary);
                        
                        ws.send(JSON.stringify({
                            realtimeInput: {
                                mediaChunks: [{
                                    mimeType: "audio/pcm;rate=16000",
                                    data: base64Audio
                                }]
                            }
                        }));
                    };
                    
                    window._audioProcessor = processor;
                    window._audioSource = source;
                }, 1000); // Wait 1 second before capturing audio to ensure Gemini is ready
            }
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            
            // Check for explicit UI signals sent from the backend proxy
            if (msg.type === 'barcode_detected') {
                console.log("Barcode detected by Gemini agent (tool call)! Queuing scanner animation at the FRONT.");

                // Instantly stop current filler playback
                if (isPlaying && currentAudioSource) {
                    currentAudioSource.onended = null;
                    try { currentAudioSource.stop(); } catch(e) {}
                    currentAudioSource = null;
                }
                
                // Nuke all pending filler audio ("Let me scan that for you...")
                audioQueue = [];
                isPlaying = false;
                
                // Keep the agent fully muted from this point forward until the order is successfully parsed.
                // This guarantees the agent cannot say "Scan completed! Now fetching details..." and ruin the sync.
                window._muteAgentUntilWidget = true;
                
                // Add the barcode signal directly and begin the sequenced execution
                audioQueue.push({ type: 'signal', name: 'barcode' });
                playNextAudio();
                return;
            } else if (msg.type === 'order_parsed') {
                console.log("Order parsed details:", msg.medicine, msg.aisle);
                
                // We MUST NOT unmute the agent instantly! The `serverContent` wrapper containing the 
                // caller filler text is right behind this packet. Defer the unmute until it is processed.
                window._unmuteAfterNextServerContent = true;
                
                if (!window._checklistPending) {
                    window._checklistPending = true;
                    console.log("Starting interactive fulfillment checklist after audio...");
                    
                    // Mark that the UI is expecting the 'turn_complete' signal to drop the widget into the audio queue
                    window._pendingWidgetDrop = true;
                }
                return;
            } else if (msg.type === 'pathfinder_map') {
                console.log("Received pathfinder map data:", msg.distance);
                const mapData = msg;
                
                // The user specifically requested the map widget be placed inside the "text box" (transcriptBox)
                // and not on the side panel, and they want the actual map restored.
                const transcriptBox = document.getElementById('transcript-box');
                const widgetBubble = document.createElement('div');
                widgetBubble.className = 'message model fade-in';
                widgetBubble.style.width = '100%';
                widgetBubble.style.maxWidth = '100%';
                
                widgetBubble.innerHTML = `
                    <div class="message-title">Cymbal Ordering System</div>
                    <div class="message-content">
                        <h4 style="margin-top: 0;">Order Delivery Route</h4>
                        <iframe width="100%" height="250" style="border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 1rem;" loading="lazy" src="https://www.google.com/maps/embed/v1/directions?key=${mapData.api_key}&origin=Cymbal&destination=Hackensack+Meridian+Health+Palisades+Medical+Center"></iframe>
                        <div style="font-weight: bold; margin-bottom: 1rem; color: #1e293b; display: flex; align-items: center; gap: 8px;">
                            <span>🚗</span> <span>Distance: ${mapData.distance}</span>
                        </div>
                        <button id="map-confirm-btn" onclick="window.acknowledgeMap(this)" style="width: 100%; padding: 0.75rem; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                            Confirm Delivery Route
                        </button>
                    </div>
                `;
                
                // Immediately append it so it is visible in the chat log
                transcriptBox.appendChild(widgetBubble);
                transcriptBox.scrollTop = transcriptBox.scrollHeight;
                
                window.acknowledgeMap = function(btnElement) {
                    btnElement.disabled = true;
                    btnElement.innerText = "✓ Route Confirmed";
                    btnElement.style.background = "#22c55e";
                    
                    // Send confirmation message back to Gemini silently so it concludes the order
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            clientContent: {
                                turns: [{
                                    parts: [{text: "User clicked: Confirm Delivery Route. Please conclude the order now."}]
                                }]
                            }
                        }));
                    }
                };
                
                return;
            }

            // Handle ADK transcribed/forwarded model content
            if (msg.serverContent) {
                if (msg.serverContent.modelTurn) {
                    const parts = msg.serverContent.modelTurn.parts;
                const isPartial = msg.serverContent.modelTurn.isPartial;

                for (const part of parts) {
                    if (part.text) {
                        hideTypingIndicator();
                        
                        // Completely drop text generated while the scanner is physically active 
                        // or if the barcode signal is queued, to enforce absolute silence/no-text.
                        if (isScanning || audioQueue.some(q => q.type === 'signal' && q.name === 'barcode') || window._muteAgentUntilWidget) {
                            console.log("Dropping filler text during scan block/transition:", part.text);
                            continue;
                        }

                        console.log("WS Received TEXT (isPartial=" + isPartial + "):", part.text);
                        
                        const newText = part.text.trim();
                        
                        let isContinuation = false;
                        if (lastSpeaker === 'model' && currentContentNode) {
                            const currentText = currentContentNode.innerText.trim();
                            const prefixLen = Math.min(10, currentText.length);
                            if (prefixLen === 0) {
                                isContinuation = true;
                            } else {
                                const prefix = currentText.substring(0, prefixLen);
                                isContinuation = newText.startsWith(prefix);
                            }
                        }

                        // Do NOT render text immediately. Add it to the playback queue so it
                        // appears strictly in the order it was received, perfectly in sync with signals/audio.
                        audioQueue.push({
                            type: 'text',
                            text: part.text,
                            role: 'model',
                            forceNew: !isContinuation && (lastSpeaker !== 'model'), // force new if not continuation and not same speaker
                            isContinuation: isContinuation
                        });
                        
                        // Keep track of recent model texts for echo cancellation
                        recentModelTexts.push(part.text.toLowerCase().trim());
                        if (recentModelTexts.length > 5) {
                            recentModelTexts.shift();
                        }
                        
                        // Trigger playback queue in case there's no audio following
                        playNextAudio();
                    } else if (part.inlineData && part.inlineData.mimeType.startsWith("audio/")) {
                        hideTypingIndicator();
                        
                        // Completely drop audio mapped to the filler text that arrives during the block.
                        if (isScanning || audioQueue.some(q => q.type === 'signal' && q.name === 'barcode') || window._muteAgentUntilWidget) {
                            console.log("Dropping trailing audio chunk during barcode block/transition");
                            continue;
                        }
                        
                        // Abort transcription immediately when agent audio arrives to prevent echo
                        if (!isPlaying && audioQueue.length === 0 && speechRecognition) {
                            try { speechRecognition.abort(); } catch(e) {}
                        }
                        
                        audioQueue.push({ type: 'audio', data: part.inlineData.data });
                        playNextAudio();
                    }
                }
                } // Close msg.serverContent.modelTurn block
                
                if (window._unmuteAfterNextServerContent) {
                    window._muteAgentUntilWidget = false;
                    window._unmuteAfterNextServerContent = false;
                    console.log("Agent unmuted safely after dropping tool transitional filler.");
                }

                if (msg.serverContent.turnComplete) {
                    // The ADK agent finished its response
                    lastSpeaker = null;
                    
                    if (window._pendingWidgetDrop) {
                        console.log("Turn completed, enqueueing widget display...");
                        window._pendingWidgetDrop = false;
                        audioQueue.push({ type: 'signal', name: 'show_widget' });
                        playNextAudio();
                    }
                }
            }
        };

        // Initialize SpeechRecognition for User Transcripts
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            console.log("Initializing SpeechRecognition...");
            speechRecognition = new SpeechRecognition();
            speechRecognition.continuous = true;
            speechRecognition.interimResults = false;
            
            speechRecognition.onstart = () => console.log("SpeechRecognition started.");
            speechRecognition.onend = () => {
                console.log("SpeechRecognition ended.");
                // Only automatically restart if we aren't currently playing agent audio
                if (ws && ws.readyState === WebSocket.OPEN && speechRecognition && !isPlaying && audioQueue.length === 0) {
                    console.log("Restarting SpeechRecognition...");
                    try {
                        speechRecognition.start();
                    } catch (e) {
                        // Ignore already started errors
                    }
                }
            };
            speechRecognition.onerror = (e) => {
                console.error("SpeechRecognition error:", e.error);
                if (e.error === 'no-speech' || e.error === 'network' || e.error === 'audio-capture') {
                    // These errors also cause it to end, let the onend handler restart it
                }
            };
            
            speechRecognition.onresult = (event) => {
                // Prevent the mic from transcribing the computer's own speaker output
                if (isPlaying || (Date.now() - lastAudioPlayTime < 500)) {
                    console.log("Ignoring speech input: Model is currently speaking or just finished.");
                    return;
                }

                const transcript = event.results[event.results.length - 1][0].transcript;
                const lowerTranscript = transcript.toLowerCase().trim();
                console.log("SpeechRecognition result:", transcript);
                
                // Text-based echo cancellation
                const isEcho = recentModelTexts.some(modelText => {
                    // Check if the transcript is a substring of the model text or vice versa.
                    return lowerTranscript.length > 5 && (modelText.includes(lowerTranscript) || lowerTranscript.includes(modelText));
                });
                
                if (isEcho) {
                    console.log("Ignoring echoed transcript:", transcript);
                    return;
                }

                // Each non-interim speech result from the user is a distinct utterance.
                appendTranscript(transcript.trim(), 'user', true);
                showTypingIndicator();
            };
            
            try {
                speechRecognition.start();
            } catch (e) {
                console.error("Failed to start SpeechRecognition:", e);
            }
        } else {
            console.warn("SpeechRecognition API not supported in this browser.");
        }

        ws.onclose = () => {
            handleDisconnect();
        };

        ws.onerror = (e) => {
            console.error("WebSocket Error:", e);
            statusText.textContent = "Connection Error";
        };

    } catch (err) {
        console.error("Error accessing media devices.", err);
        statusText.textContent = "Camera/Mic Error";
    }
});

function handleDisconnect() {
    if (frameInterval) clearInterval(frameInterval);
    if (window._audioProcessor) {
        window._audioProcessor.disconnect();
        window._audioSource.disconnect();
    }
    
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    video.srcObject = null;
    placeholder.style.display = 'flex';
    
    if (speechRecognition) {
        speechRecognition.stop();
        speechRecognition = null;
    }
    
    statusText.textContent = "Disconnected";
    connectionDot.classList.remove('active');
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    audioQueue = [];
    isPlaying = false;
}

stopBtn.addEventListener('click', () => {
    if (ws) ws.close();
    handleDisconnect();
});
