const API_URL = "http://127.0.0.1:8000";
const CLASS_ID = "BEC405A";

// Get token from localStorage
const token = localStorage.getItem("token");
if(!token) window.location.href = "/login";  // redirect if not logged in

async function fetchStudents() {
  const token = localStorage.getItem("token");
  const response = await fetch("/students", {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
  const data = await response.json();
  // render students...
}


async function loadStudents() {
    const response = await fetch(`${API_URL}/students`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await response.json();
    const list = document.getElementById("students-list");
    list.innerHTML = "";
    data.students.forEach(student => {
        const li = document.createElement("li");
        li.textContent = `${student.name} (RFID: ${student.rfid_tag})`;
        list.appendChild(li);
    });
}

async function updateDashboard() {
    const verifyRes = await fetch(`${API_URL}/verify/${CLASS_ID}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    const verifyData = await verifyRes.json();
    const result = document.getElementById("verification-result");

    if(verifyData.status === "green") {
        result.textContent = `✅ Class Verified! RFID: ${verifyData.rfid_count}, Headcount: ${verifyData.headcount}`;
        result.style.color = "green";
    } else if(verifyData.status === "red") {
        result.textContent = `❌ Mismatch! RFID: ${verifyData.rfid_count}, Headcount: ${verifyData.headcount}`;
        result.style.color = "red";
    } else {
        result.textContent = verifyData.status;
        result.style.color = "black";
    }

    const headcountRes = await fetch(`${API_URL}/headcounts/${CLASS_ID}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    const headcounts = await headcountRes.json();
    const list = document.getElementById("headcount-list");
    list.innerHTML = "";
    headcounts.forEach(hc => {
        const li = document.createElement("li");
        li.textContent = `${hc.count} at ${new Date(hc.timestamp).toLocaleTimeString()}`;
        list.appendChild(li);
    });
}

setInterval(() => {
    loadStudents();
    updateDashboard();
}, 5000);

window.onload = () => {
    loadStudents();
    updateDashboard();
};
