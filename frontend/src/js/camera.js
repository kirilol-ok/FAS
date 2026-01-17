const CAMERA_PROXY = "http://localhost:8090";
const API_BASE_URL = "http://localhost:8000";

const img = document.getElementById("videoStream");
const checkButton = document.getElementById("checkButton");
const statusText = document.getElementById("statusText");
const statusEl = document.getElementById("status");
const overlay = document.getElementById("overlay"); // Pobierz element overlay


img.onload = () => {
    
    if (overlay) overlay.style.display = "none";
};

img.onerror = () => {
    if (overlay) overlay.style.display = "flex";
};

let isScanning = true; 

async function startAutoScan() {
    if (!isScanning) return;
    
    setStatus("Scanning...", false);

    try {
       
        const blob = await fetchSnapshotBlob();

        const fd = new FormData();
        fd.append("file", blob, "frame.jpg");

        const res = await fetch(`${API_BASE_URL}/identify/qr`, {
            method: "POST",
            body: fd,
        });

     
        if (res.ok) {
            
            const employee = await res.json();
            setStatus(`Witaj, ${employee.first_name}!`, false);
            document.body.style.backgroundColor = "#dcfce7"; 
            
           
            await new Promise(r => setTimeout(r, 3000));
            document.body.style.backgroundColor = "";
        } else {
            
            if (res.status === 403) {
                 setStatus("Odmowa dostępu!", true);
                 await new Promise(r => setTimeout(r, 2000));
            }
            
        }

    } catch (e) {
        console.error("Scan error loop:", e);
        
        await new Promise(r => setTimeout(r, 1000));
    }

    
    setTimeout(startAutoScan, 100); 
}


document.addEventListener("DOMContentLoaded", () => {
    
    if(checkButton) checkButton.style.display = 'none';
    
  
    startAutoScan();
});
