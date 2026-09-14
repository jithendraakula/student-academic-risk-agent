const EVENT_NAME = "academic-case-work-updated";
const STORAGE_KEY = "academic-case-work-updated-at";

export function notifyCaseWorkUpdated() {
  window.dispatchEvent(new CustomEvent(EVENT_NAME));
  try { localStorage.setItem(STORAGE_KEY, String(Date.now())); } catch { /* non-blocking */ }
}

export function subscribeToCaseWorkUpdates(onUpdate: () => void) {
  const handler = () => onUpdate();
  const storageHandler = (event: StorageEvent) => { if (event.key === STORAGE_KEY) onUpdate(); };
  window.addEventListener(EVENT_NAME, handler);
  window.addEventListener("storage", storageHandler);
  return () => {
    window.removeEventListener(EVENT_NAME, handler);
    window.removeEventListener("storage", storageHandler);
  };
}

export function subscribeToLiveCaseWorkUpdates(onUpdate: () => void) {
  let stopped = false;
  const controller = new AbortController();
  const token = sessionStorage.getItem("agent14_token");
  const base = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");

  const run = async () => {
    try {
      const response = await fetch(`${base}/interventions/events`, {
        headers: token ? { Authorization: `Bearer ${token}`, Accept: "text/event-stream" } : { Accept: "text/event-stream" },
        signal: controller.signal,
      });
      if (!response.ok || !response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (!stopped) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";
        for (const block of blocks) if (block.includes("event: case-work")) onUpdate();
      }
    } catch { /* polling/event fallback remains active */ }
  };
  void run();
  const stop = () => { stopped = true; controller.abort(); };
  return stop;
}
