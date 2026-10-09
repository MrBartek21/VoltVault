const tableBody = document.querySelector("#data-table tbody");
const ws = new WebSocket(`ws://${window.location.host}/ws`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    tableBody.innerHTML = "";
    for (const key in data) {
        const row = document.createElement("tr");
        const keyCell = document.createElement("td");
        const valueCell = document.createElement("td");
        keyCell.textContent = key;
        valueCell.textContent = data[key];
        row.appendChild(keyCell);
        row.appendChild(valueCell);
        tableBody.appendChild(row);
    }
};
