document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-pomodoro]");
  if (!root) return;

  const form = root.querySelector("[data-settings]");
  const timeDisplay = root.querySelector("[data-time]");
  const phaseLabel = root.querySelector("[data-phase-label]");
  const roundLabel = root.querySelector("[data-round]");
  const status = root.querySelector("[data-status]");
  const startButton = root.querySelector('[data-action="start"]');
  const pauseButton = root.querySelector('[data-action="pause"]');
  const resetButton = root.querySelector('[data-action="reset"]');

  let state = "idle";
  let phase = "work";
  let focusCount = 0;
  let secondsLeft = readMinutes("work") * 60;
  let deadline = 0;
  let tickHandle = null;
  let audioContext = null;

  function readMinutes(name) {
    return Number(form.elements[name].value);
  }

  function formatTime(value) {
    const minutes = Math.floor(value / 60).toString().padStart(2, "0");
    const seconds = (value % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function paint() {
    timeDisplay.textContent = formatTime(Math.max(0, secondsLeft));
    const running = state === "running";
    startButton.disabled = running;
    pauseButton.disabled = !running;
    form.querySelectorAll("input").forEach((input) => { input.disabled = running; });
    startButton.innerHTML = state === "paused"
      ? 'Resume focus <span aria-hidden="true">▶</span>'
      : 'Start focus <span aria-hidden="true">▶</span>';

    if (state === "idle") {
      phaseLabel.textContent = "READY WHEN YOU ARE";
      roundLabel.textContent = "Make a little room for focus.";
    } else if (state === "paused") {
      phaseLabel.textContent = "PAUSED";
      roundLabel.textContent = phase === "work" ? `Focus interval ${focusCount + 1}` : "Break time";
    } else {
      phaseLabel.textContent = phase === "work" ? "FOCUS TIME" : phase === "long" ? "LONG BREAK" : "SHORT BREAK";
      roundLabel.textContent = phase === "work"
        ? `Focus interval ${focusCount + 1} · one thing at a time`
        : "Step away for a moment. You have earned it.";
    }
  }

  function chime() {
    if (!audioContext) return;
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(660, audioContext.currentTime);
    oscillator.frequency.setValueAtTime(880, audioContext.currentTime + 0.14);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.13, audioContext.currentTime + 0.025);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.5);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.52);
  }

  function phaseDuration() {
    if (phase === "work") return readMinutes("work") * 60;
    return (phase === "long" ? readMinutes("long") : readMinutes("short")) * 60;
  }

  function finishPhase() {
    chime();
    if (phase === "work") {
      focusCount += 1;
      phase = focusCount % readMinutes("rounds") === 0 ? "long" : "short";
      status.textContent = phase === "long" ? "Focus interval complete. Take a longer pause." : "Focus interval complete. Take a short pause.";
    } else {
      phase = "work";
      status.textContent = "Break complete. Ready for another focus interval?";
    }
    secondsLeft = phaseDuration();
    deadline += secondsLeft * 1000;
    paint();
  }

  function tick() {
    if (state !== "running") return;
    const now = Date.now();
    while (now >= deadline && state === "running") finishPhase();
    secondsLeft = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    paint();
  }

  async function start() {
    if (!form.reportValidity()) return;
    if (state === "idle") {
      phase = "work";
      secondsLeft = readMinutes("work") * 60;
      focusCount = 0;
    }
    if (!audioContext && (window.AudioContext || window.webkitAudioContext)) {
      const Context = window.AudioContext || window.webkitAudioContext;
      audioContext = new Context();
    }
    if (audioContext && audioContext.state === "suspended") await audioContext.resume();
    state = "running";
    deadline = Date.now() + secondsLeft * 1000;
    status.textContent = "Timer running in this browser tab.";
    clearInterval(tickHandle);
    tickHandle = window.setInterval(tick, 250);
    paint();
  }

  function pause() {
    if (state !== "running") return;
    secondsLeft = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    state = "paused";
    status.textContent = "Paused. Your place is saved in this tab.";
    clearInterval(tickHandle);
    paint();
  }

  function reset() {
    clearInterval(tickHandle);
    state = "idle";
    phase = "work";
    focusCount = 0;
    secondsLeft = readMinutes("work") * 60;
    deadline = 0;
    status.textContent = "Your timer runs in this browser tab.";
    paint();
  }

  form.addEventListener("change", () => {
    try {
      localStorage.setItem("zenara-pomodoro-settings", JSON.stringify(Object.fromEntries(new FormData(form))));
    } catch (_error) { /* Storage may be unavailable; the timer still works for this visit. */ }
    if (state === "idle") {
      secondsLeft = readMinutes("work") * 60;
      paint();
    }
  });
  try {
    const saved = JSON.parse(localStorage.getItem("zenara-pomodoro-settings") || "null");
    if (saved) Object.entries(saved).forEach(([name, value]) => {
      if (form.elements[name]) form.elements[name].value = value;
    });
  } catch (_error) { /* Ignore malformed or unavailable browser storage. */ }
  form.addEventListener("submit", (event) => event.preventDefault());
  secondsLeft = readMinutes("work") * 60;
  startButton.addEventListener("click", start);
  pauseButton.addEventListener("click", pause);
  resetButton.addEventListener("click", reset);
  paint();
});
