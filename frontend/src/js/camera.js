const CAMERA_PROXY = "http://localhost:8090";
const API_BASE_URL = "http://localhost:8000";

const img = document.getElementById("videoStream");
const checkButton = document.getElementById("checkButton");
const statusText = document.getElementById("statusText");
const statusEl = document.getElementById("status");

function setStatus(text, offline = false) {
  if (statusText) statusText.textContent = text;
  if (statusEl) statusEl.classList.toggle("offline", offline);
}

async function fetchSnapshotBlob() {
  const res = await fetch(`${CAMERA_PROXY}/snapshot`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Snapshot error: HTTP ${res.status}`);
  return await res.blob();
}

async function sendToQr(blob) {
  const fd = new FormData();
  fd.append("file", blob, "frame.jpg");

  const res = await fetch(`${API_BASE_URL}/identify/qr`, {
    method: "POST",
    body: fd,
  });

  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { detail: text }; }

  if (!res.ok) throw new Error(data.detail || `QR error HTTP ${res.status}`);
  return data;
}

checkButton.addEventListener("click", async () => {
  checkButton.disabled = true;
  const old = checkButton.textContent;
  checkButton.textContent = "Checking...";
  setStatus("Processing…", false);

  try {
    const blob = await fetchSnapshotBlob();
    const employee = await sendToQr(blob);

    alert(`Access granted: ${employee.first_name} ${employee.last_name}`);
    setStatus("Live", false);
  } catch (e) {
    console.error(e);
    alert("Error: " + e.message);
    setStatus("Error", true);
  } finally {
    checkButton.disabled = false;
    checkButton.textContent = old;
  }
});
