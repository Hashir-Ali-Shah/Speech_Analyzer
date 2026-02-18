/* ═══════════════════════════════════════════════════════════════
   SpeakBetter Local — Frontend Application
   SPA with sidebar navigation, view switching, recording,
   API communication, rendering, session history.
   ═══════════════════════════════════════════════════════════════ */

(() => {
  "use strict";

  // ─── Configuration ────────────────────────────────────────
  const API_BASE = "";
  const MAX_RECORDING_SECONDS = 120;
  const MIN_RECORDING_SECONDS = 30;

  const FILLER_WORDS = new Set(["uh", "um", "like", "basically", "actually"]);

  // ─── State ────────────────────────────────────────────────
  const state = {
    currentTopic: null,
    isRecording: false,
    recordingTime: 0,
    audioBlob: null,
    isAnalyzing: false,
    analysisResult: null,
    activeView: "record",
    sessions: [],
  };

  let mediaRecorder = null;
  let audioChunks = [];
  let timerInterval = null;
  let audioContext = null;
  let analyserNode = null;
  let visualizerRAF = null;

  // ─── DOM References ───────────────────────────────────────
  const $ = (id) => document.getElementById(id);

  const dom = {
    // Nav
    navItems: document.querySelectorAll(".nav-item"),
    views: document.querySelectorAll(".view"),

    // Record view
    generateTopicBtn: $("generateTopicBtn"),
    topicDisplay: $("topicDisplay"),
    recordBtn: $("recordBtn"),
    stopBtn: $("stopBtn"),
    timerText: $("timerText"),
    timerLabel: $("timerLabel"),
    visualizerContainer: $("visualizerContainer"),
    visualizerCanvas: $("visualizerCanvas"),
    visualizerLabel: $("visualizerLabel"),
    playbackContainer: $("playbackContainer"),
    audioPlayback: $("audioPlayback"),
    analyzeBtn: $("analyzeBtn"),

    // Results view
    resultsContent: $("resultsContent"),
    noResults: $("noResults"),
    transcriptContent: $("transcriptContent"),
    copyTranscriptBtn: $("copyTranscriptBtn"),
    copyBtnText: $("copyBtnText"),
    fillerBreakdown: $("fillerBreakdown"),
    fillerBreakdownContent: $("fillerBreakdownContent"),

    // Coach view
    coachContent: $("coachContent"),
    noCoachData: $("noCoachData"),
    llmContextArea: $("llmContextArea"),
    copyLLMBtn: $("copyLLMBtn"),
    copyLLMText: $("copyLLMText"),

    // History view
    historyList: $("historyList"),
    clearHistoryBtn: $("clearHistoryBtn"),

    // Model
    modelSelect: $("modelSelect"),

    // Analysis progress (inline)
    analysisProgress: $("analysisProgress"),
    analysisProgressText: $("analysisProgressText"),
  };

  // ─── View Navigation ──────────────────────────────────────
  function switchView(viewName) {
    state.activeView = viewName;

    dom.views.forEach((v) => v.classList.remove("active"));
    dom.navItems.forEach((n) => n.classList.remove("active"));

    const targetView = $(
      "view" + viewName.charAt(0).toUpperCase() + viewName.slice(1),
    );
    if (targetView) targetView.classList.add("active");

    const targetNav = document.querySelector(
      `.nav-item[data-view="${viewName}"]`,
    );
    if (targetNav) targetNav.classList.add("active");
  }

  dom.navItems.forEach((item) => {
    item.addEventListener("click", () => {
      switchView(item.dataset.view);
    });
  });

  // ─── Event Bindings ───────────────────────────────────────
  dom.generateTopicBtn.addEventListener("click", fetchTopic);
  dom.recordBtn.addEventListener("click", toggleRecording);
  dom.stopBtn.addEventListener("click", stopRecording);
  dom.analyzeBtn.addEventListener("click", analyzeAudio);
  dom.copyTranscriptBtn.addEventListener("click", copyTranscript);
  dom.copyLLMBtn.addEventListener("click", copyLLMContext);
  dom.clearHistoryBtn.addEventListener("click", clearHistory);

  // ─── Topic ────────────────────────────────────────────────
  async function fetchTopic() {
    try {
      dom.generateTopicBtn.disabled = true;
      const res = await fetch(`${API_BASE}/api/topic`);
      if (!res.ok) throw new Error("Failed to fetch topic");
      const data = await res.json();
      state.currentTopic = data;
      renderTopic(data);
    } catch (err) {
      console.error("Topic fetch error:", err);
      dom.topicDisplay.innerHTML = `<p class="topic-placeholder" style="color:var(--danger)">Failed to load topic.</p>`;
    } finally {
      dom.generateTopicBtn.disabled = false;
    }
  }

  function renderTopic(data) {
    dom.topicDisplay.innerHTML = `
      <div>
        <span class="topic-category">${escapeHtml(data.category)}</span>
        <p class="topic-text">${escapeHtml(data.topic)}</p>
      </div>
    `;
  }

  // ─── Recording ────────────────────────────────────────────
  async function toggleRecording() {
    if (state.isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "";

      mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
        state.audioBlob = blob;
        stream.getTracks().forEach((t) => t.stop());
        stopVisualizer();
        onRecordingComplete(blob);
      };

      mediaRecorder.start(250);
      state.isRecording = true;
      state.recordingTime = 0;
      state.audioBlob = null;

      dom.recordBtn.classList.add("recording");
      dom.stopBtn.classList.remove("hidden");
      dom.playbackContainer.classList.add("hidden");
      dom.analyzeBtn.classList.add("hidden");
      dom.timerLabel.textContent = "Recording...";

      startVisualizer(stream);

      timerInterval = setInterval(() => {
        state.recordingTime++;
        dom.timerText.textContent = formatTime(state.recordingTime);

        if (state.recordingTime >= MAX_RECORDING_SECONDS) {
          stopRecording();
        }
      }, 1000);
    } catch (err) {
      console.error("Microphone access error:", err);
      dom.timerLabel.textContent = "Microphone access denied";
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    clearInterval(timerInterval);
    state.isRecording = false;

    dom.recordBtn.classList.remove("recording");
    dom.stopBtn.classList.add("hidden");
    dom.timerLabel.textContent = "Recording complete";
  }

  // ─── Audio Visualizer ─────────────────────────────────────
  function startVisualizer(stream) {
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 256;
      analyserNode.smoothingTimeConstant = 0.7;

      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyserNode);

      dom.visualizerContainer.classList.remove("hidden");

      const canvas = dom.visualizerCanvas;
      const ctx = canvas.getContext("2d");
      const bufferLength = analyserNode.frequencyBinCount;
      const frequencyData = new Uint8Array(bufferLength);

      function drawBars() {
        analyserNode.getByteFrequencyData(frequencyData);
        const { width, height } = canvas;

        ctx.clearRect(0, 0, width, height);

        const barCount = 48;
        const barWidth = (width / barCount) * 0.65;
        const gap = width / barCount;

        for (let i = 0; i < barCount; i++) {
          const dataIndex = Math.floor((i / barCount) * bufferLength);
          const value = frequencyData[dataIndex] / 255;
          const barHeight = Math.max(2, value * height * 0.9);

          const x = i * gap + (gap - barWidth) / 2;
          const y = height - barHeight;
          const radius = barWidth / 2;

          const hue = 230 + value * 20;
          ctx.fillStyle = `hsla(${hue}, 70%, ${50 + value * 20}%, ${0.5 + value * 0.5})`;

          ctx.beginPath();
          ctx.moveTo(x + radius, y);
          ctx.arcTo(x + barWidth, y, x + barWidth, y + radius, radius);
          ctx.lineTo(x + barWidth, height);
          ctx.lineTo(x, height);
          ctx.lineTo(x, y + radius);
          ctx.arcTo(x, y, x + radius, y, radius);
          ctx.fill();
        }

        const totalEnergy = frequencyData.reduce((a, b) => a + b, 0);
        dom.visualizerLabel.textContent =
          totalEnergy < 100 ? "No input detected" : "Input Level";

        visualizerRAF = requestAnimationFrame(drawBars);
      }

      drawBars();
    } catch (err) {
      console.error("Visualizer error:", err);
    }
  }

  function stopVisualizer() {
    if (visualizerRAF) {
      cancelAnimationFrame(visualizerRAF);
      visualizerRAF = null;
    }
    if (audioContext) {
      audioContext.close().catch(() => {});
      audioContext = null;
    }
    dom.visualizerContainer.classList.add("hidden");
  }

  function onRecordingComplete(blob) {
    const url = URL.createObjectURL(blob);
    dom.audioPlayback.src = url;
    dom.playbackContainer.classList.remove("hidden");

    if (state.recordingTime >= MIN_RECORDING_SECONDS) {
      dom.analyzeBtn.classList.remove("hidden");
    } else {
      dom.analyzeBtn.classList.remove("hidden");
      dom.timerLabel.textContent = `Recording: ${state.recordingTime}s (min ${MIN_RECORDING_SECONDS}s recommended)`;
    }
  }

  // ─── Analysis ─────────────────────────────────────────────
  async function analyzeAudio() {
    if (!state.audioBlob || state.isAnalyzing) return;

    state.isAnalyzing = true;
    dom.analysisProgress.classList.remove("hidden");
    dom.analysisProgressText.textContent = "Transcribing speech...";
    dom.analyzeBtn.classList.add("hidden");

    try {
      const formData = new FormData();
      formData.append("audio", state.audioBlob, "recording.webm");

      setTimeout(() => {
        if (state.isAnalyzing) {
          dom.analysisProgressText.textContent = "Computing metrics...";
        }
      }, 3000);

      const selectedModel = dom.modelSelect ? dom.modelSelect.value : "base";
      const res = await fetch(
        `${API_BASE}/api/analyze?model=${selectedModel}`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Analysis failed");
      }

      const data = await res.json();
      state.analysisResult = data;

      saveSession(data);
      renderResults(data);

      // Auto-switch to results view
      switchView("results");
    } catch (err) {
      console.error("Analysis error:", err);
      dom.analysisProgressText.textContent = `Error: ${err.message}`;
      setTimeout(() => {
        dom.analysisProgress.classList.add("hidden");
      }, 2500);
    } finally {
      state.isAnalyzing = false;
      dom.analyzeBtn.classList.remove("hidden");
      dom.analysisProgress.classList.add("hidden");
    }
  }

  // ─── Render Results ───────────────────────────────────────
  function renderResults(data) {
    const { transcript, metrics, duration_seconds } = data;

    // Show results content, hide empty state
    dom.noResults.classList.add("hidden");
    dom.resultsContent.classList.remove("hidden");

    // Show coach content, hide empty state
    dom.noCoachData.classList.add("hidden");
    dom.coachContent.classList.remove("hidden");

    renderTranscript(transcript, metrics);

    // Core metrics
    setMetric("metricWPM", metrics.words_per_minute);
    setMetric("metricWordCount", metrics.word_count);
    setMetric("metricDuration", duration_seconds);
    setMetric("metricFillerCount", metrics.filler_count);
    setMetric("metricFillerDensity", metrics.filler_density);
    setMetric("metricTopFiller", metrics.most_common_filler);
    setMetric("metricRepetitions", metrics.repetition_count);
    setMetric("metricLongestPause", metrics.longest_pause_seconds);
    setMetric("metricPauseCount", metrics.pause_count_over_1s);
    setMetric("metricAvgSentence", metrics.avg_sentence_length);
    setMetric("metricLongestSentence", metrics.longest_sentence_length);
    setMetric("metricShortestSentence", metrics.shortest_sentence_length);

    // New metrics
    setMetric("metricSentenceCount", metrics.sentence_count);
    setMetric("metricVocabDiversity", metrics.vocabulary_diversity);
    setMetric("metricUniqueWords", metrics.unique_word_count);
    setMetric("metricAvgWordLength", metrics.avg_word_length);
    setMetric("metricArticulationRate", metrics.articulation_rate);
    setMetric("metricSpeakingRatio", metrics.speaking_time_ratio);

    renderFillerBreakdown(metrics.filler_details || {});
    generateLLMContext(data);
  }

  function renderTranscript(transcript, metrics) {
    const repeatedWords = new Set();
    if (metrics.repeated_words) {
      metrics.repeated_words.forEach((r) =>
        repeatedWords.add(r.word.toLowerCase()),
      );
    }

    const words = transcript.split(/\s+/);
    let html = "";

    for (const word of words) {
      const clean = word.replace(/[^a-zA-Z']/g, "").toLowerCase();

      if (FILLER_WORDS.has(clean)) {
        html += `<span class="filler-highlight">${escapeHtml(word)}</span> `;
      } else if (repeatedWords.has(clean)) {
        html += `<span class="repeat-highlight">${escapeHtml(word)}</span> `;
      } else {
        html += escapeHtml(word) + " ";
      }
    }

    dom.transcriptContent.innerHTML = html;
  }

  function renderFillerBreakdown(fillerDetails) {
    if (!fillerDetails || Object.keys(fillerDetails).length === 0) {
      dom.fillerBreakdown.classList.add("hidden");
      return;
    }

    dom.fillerBreakdown.classList.remove("hidden");
    const sorted = Object.entries(fillerDetails).sort((a, b) => b[1] - a[1]);

    dom.fillerBreakdownContent.innerHTML = sorted
      .map(
        ([filler, count]) =>
          `<span class="breakdown-chip">${escapeHtml(filler)} <span class="chip-count">×${count}</span></span>`,
      )
      .join("");
  }

  function setMetric(id, value) {
    const el = $(id);
    if (el) el.textContent = value ?? "—";
  }

  // ─── LLM Context ─────────────────────────────────────────
  function generateLLMContext(data) {
    const { transcript, metrics, duration_seconds } = data;
    const topic = state.currentTopic;

    const lines = [];
    lines.push("=== SPEECH ANALYSIS REPORT ===");
    lines.push(
      "Analyze my speech below and provide specific, actionable improvement advice.",
    );
    lines.push("");

    if (topic) {
      lines.push(`TOPIC: ${topic.topic}`);
      lines.push(`CATEGORY: ${topic.category}`);
      lines.push("");
    }

    lines.push("--- TRANSCRIPT ---");
    lines.push(transcript);
    lines.push("");

    lines.push("--- PERFORMANCE METRICS ---");
    lines.push("");
    lines.push("Core:");
    lines.push(`  Words per Minute: ${metrics.words_per_minute}`);
    lines.push(`  Total Words: ${metrics.word_count}`);
    lines.push(`  Duration: ${duration_seconds}s`);
    lines.push(`  Sentence Count: ${metrics.sentence_count ?? "N/A"}`);
    lines.push(`  Avg Sentence Length: ${metrics.avg_sentence_length} words`);
    lines.push(`  Longest Sentence: ${metrics.longest_sentence_length} words`);
    lines.push(
      `  Shortest Sentence: ${metrics.shortest_sentence_length} words`,
    );
    lines.push("");

    lines.push("Fillers:");
    lines.push(`  Total Filler Words: ${metrics.filler_count}`);
    lines.push(`  Filler Density: ${metrics.filler_density} per 100 words`);
    lines.push(`  Most Common Filler: ${metrics.most_common_filler}`);
    if (
      metrics.filler_details &&
      Object.keys(metrics.filler_details).length > 0
    ) {
      const breakdown = Object.entries(metrics.filler_details)
        .sort((a, b) => b[1] - a[1])
        .map(([f, c]) => `${f} (×${c})`)
        .join(", ");
      lines.push(`  Breakdown: ${breakdown}`);
    }
    lines.push("");

    lines.push("Repetitions:");
    lines.push(`  Total Repetitions: ${metrics.repetition_count}`);
    if (metrics.repeated_words && metrics.repeated_words.length > 0) {
      const rw = metrics.repeated_words
        .map((r) => `"${r.word}" (×${r.count})`)
        .join(", ");
      lines.push(`  Repeated Words: ${rw}`);
    }
    lines.push("");

    lines.push("Pauses:");
    lines.push(`  Longest Pause: ${metrics.longest_pause_seconds}s`);
    lines.push(`  Avg Pause Duration: ${metrics.avg_pause_duration}s`);
    lines.push(`  Pauses > 1 second: ${metrics.pause_count_over_1s}`);
    lines.push("");

    lines.push("Vocabulary:");
    lines.push(
      `  Vocabulary Diversity: ${metrics.vocabulary_diversity ?? "N/A"} (unique/total words)`,
    );
    lines.push(`  Unique Words: ${metrics.unique_word_count ?? "N/A"}`);
    lines.push(
      `  Avg Word Length: ${metrics.avg_word_length ?? "N/A"} characters`,
    );
    lines.push("");

    lines.push("Pacing:");
    lines.push(
      `  Articulation Rate: ${metrics.articulation_rate ?? "N/A"} WPM (excluding pauses)`,
    );
    lines.push(
      `  Speaking Time Ratio: ${metrics.speaking_time_ratio ?? "N/A"}% (speech vs silence)`,
    );
    lines.push("");

    lines.push("--- INSTRUCTIONS FOR AI ---");
    lines.push("Based on the transcript and metrics above, please:");
    lines.push("1. Identify my top 3 speaking weaknesses.");
    lines.push("2. Provide specific exercises to improve each weakness.");
    lines.push("3. Comment on my sentence structure and vocabulary usage.");
    lines.push(
      "4. Rate my overall fluency on a scale of 1-10 with justification.",
    );
    lines.push("5. Suggest what to focus on in my next practice session.");

    dom.llmContextArea.value = lines.join("\n");
  }

  async function copyLLMContext() {
    const text = dom.llmContextArea.value;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      dom.copyLLMText.textContent = "Copied!";
      setTimeout(() => {
        dom.copyLLMText.textContent = "Copy to Clipboard";
      }, 2000);
    } catch {
      dom.llmContextArea.select();
      document.execCommand("copy");
      dom.copyLLMText.textContent = "Copied!";
      setTimeout(() => {
        dom.copyLLMText.textContent = "Copy to Clipboard";
      }, 2000);
    }
  }

  // ─── Copy Transcript ──────────────────────────────────────
  async function copyTranscript() {
    if (!state.analysisResult) return;
    try {
      await navigator.clipboard.writeText(state.analysisResult.transcript);
      dom.copyBtnText.textContent = "Copied!";
      setTimeout(() => {
        dom.copyBtnText.textContent = "Copy";
      }, 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = state.analysisResult.transcript;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      dom.copyBtnText.textContent = "Copied!";
      setTimeout(() => {
        dom.copyBtnText.textContent = "Copy";
      }, 2000);
    }
  }

  async function loadSessionsFromAPI() {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`);
      if (res.ok) {
        state.sessions = await res.json();
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
      state.sessions = [];
    }
    renderHistory();
  }

  async function persistSessions() {
    try {
      await fetch(`${API_BASE}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.sessions),
      });
    } catch (err) {
      console.error("Failed to save sessions:", err);
    }
  }

  function saveSession(data) {
    const session = {
      id: Date.now(),
      date: new Date().toISOString(),
      topic: state.currentTopic,
      transcript: data.transcript,
      duration_seconds: data.duration_seconds,
      metrics: data.metrics,
    };
    state.sessions.unshift(session);
    if (state.sessions.length > 50)
      state.sessions = state.sessions.slice(0, 50);
    persistSessions();
    renderHistory();
  }

  function renderHistory() {
    if (state.sessions.length === 0) {
      dom.historyList.innerHTML = `
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <p>No sessions yet. Record and analyze your speech to see history.</p>
        </div>`;
      dom.clearHistoryBtn.classList.add("hidden");
      return;
    }

    dom.clearHistoryBtn.classList.remove("hidden");

    dom.historyList.innerHTML = state.sessions
      .map(
        (s) => `
        <div class="history-item" data-id="${s.id}">
          <div class="history-item-date">${formatDate(s.date)}</div>
          <div class="history-item-topic">${s.topic ? escapeHtml(s.topic.topic) : truncateWords(s.transcript, 4)}</div>
          <div class="history-item-stats">
            <span class="history-item-stat">${s.metrics.words_per_minute} WPM</span>
            <span class="history-item-stat">${s.metrics.filler_count} fillers</span>
            <span class="history-item-stat">${s.duration_seconds}s</span>
          </div>
        </div>`,
      )
      .join("");

    // Click to load session
    dom.historyList.querySelectorAll(".history-item").forEach((el) => {
      el.addEventListener("click", () => {
        const id = parseInt(el.dataset.id);
        const session = state.sessions.find((s) => s.id === id);
        if (session) {
          state.analysisResult = session;
          if (session.topic) {
            state.currentTopic = session.topic;
            renderTopic(session.topic);
          }
          renderResults(session);
          switchView("results");
        }
      });
    });
  }

  async function clearHistory() {
    if (confirm("Clear all session history?")) {
      state.sessions = [];
      try {
        await fetch(`${API_BASE}/api/sessions`, { method: "DELETE" });
      } catch (err) {
        console.error("Failed to clear sessions:", err);
      }
      renderHistory();
    }
  }

  // ─── Utilities ────────────────────────────────────────────
  function formatTime(seconds) {
    const m = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  }

  function formatDate(isoString) {
    const d = new Date(isoString);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function truncateWords(text, count) {
    if (!text) return "Untitled session";
    const words = text.trim().split(/\s+/);
    const slice = words.slice(0, count).join(" ");
    return escapeHtml(words.length > count ? slice + "..." : slice);
  }

  // ─── Init ─────────────────────────────────────────────────
  loadSessionsFromAPI();
})();
