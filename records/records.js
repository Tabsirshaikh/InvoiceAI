// ─────────────────────────────────────────────
// Auth guard — redirect to login if no token
// ─────────────────────────────────────────────

function getToken() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '../auth/auth.html';
        return null;
    }
    return token;
}

function authHeaders() {
    const token = getToken();
    if (!token) return null;
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Handle 401 globally — token expired or invalid
function handle401(response) {
    if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '../auth/auth.html';
        return true;
    }
    return false;
}

// ─────────────────────────────────────────────
// Build HTML table from records array
// ─────────────────────────────────────────────

let loadedRecords = [];

function buildTable(data) {
    loadedRecords = data;
    let html = `
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Client</th>
            <th>Quantity</th>
            <th>Price/pc</th>
            <th>Total</th>
        </tr>
    `;

    data.forEach(record => {
        html += `
        <tr>
            <td>${record.id}</td>
            <td>${record.client}</td>
            <td>${record.quantity}</td>
            <td>${record.ppc}</td>
            <td>${record.Total}</td>
        </tr>
        `;
    });

    html += '</table>';
    document.getElementById('table').innerHTML = html;
}

// ─────────────────────────────────────────────
// Load all records on page load
// ─────────────────────────────────────────────

async function loaddata() {
    const headers = authHeaders();
    if (!headers) return;

    try {
        const response = await fetch('http://127.0.0.1:8000/records', {
            headers: headers
        });

        if (handle401(response)) return;

        const data = await response.json();
        buildTable(data);

    } catch (err) {
        console.error(err);
        document.getElementById('table').textContent = 'Could not load records.';
    }
}

// ─────────────────────────────────────────────
// Sort / filter records
// ─────────────────────────────────────────────

async function sorting() {
    const headers = authHeaders();
    if (!headers) return;

    const order  = document.querySelector('#order').value;
    const filter = document.querySelector('#type').value;

    try {
        const response = await fetch('http://127.0.0.1:8000/filter', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ order, filter })
        });

        if (handle401(response)) return;

        const data = await response.json();
        buildTable(data);

    } catch (err) {
        console.error(err);
    }
}

// ─────────────────────────────────────────────
// Update an invoice
// ─────────────────────────────────────────────

const updateBtn = document.querySelector('#updateBtn');
const show      = document.querySelector('#show');
const idInput   = document.querySelector('#idselect');
const idError   = document.querySelector('#iderror');

async function updateInvoice(event) {
    event.preventDefault();

    const headers = authHeaders();
    if (!headers) return;

    const displayId = parseInt(idInput.value);
    if (isNaN(displayId)) {
        idError.textContent = 'Please enter a valid ID';
        return;
    }

    const record = loadedRecords.find(r => r.id === displayId);
    if (!record) {
        idError.textContent = 'Invoice ID not found';
        return;
    }

    const invoiceId = record.db_id;
    const quantity  = parseInt(document.querySelector('#quantity').value);
    const ppc       = parseInt(document.querySelector('#ppcs').value);

    document.querySelector('#total').textContent = quantity * ppc;

    const updateData = {
        name:     document.querySelector('#client').value  || null,
        product:  document.querySelector('#product').value || null,
        quantity: isNaN(quantity) ? null : quantity,
        ppc:      isNaN(ppc)      ? null : ppc
    };

    try {
        const response = await fetch(
            `http://127.0.0.1:8000/update/${invoiceId}`,
            {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(updateData)
            }
        );

        if (handle401(response)) return;

        const data = await response.json();

        if (!response.ok) {
            idError.textContent = data.detail;
            return;
        }

        idError.textContent = '';
        show.textContent = data.message;

        // Reload the table to reflect changes
        loaddata();

    } catch (err) {
        console.error(err);
        show.textContent = 'Error updating invoice.';
    }
}

// ─────────────────────────────────────────────
// ID input validation
// ─────────────────────────────────────────────

function validateId() {
    const value = idInput.value;

    if (value === '') {
        idError.textContent = '';
        return;
    }

    if (!/^\d+$/.test(value)) {
        idError.textContent = 'ID must contain only numbers';
    } else {
        idError.textContent = '';
    }
}

// ─────────────────────────────────────────────
// Event listeners
// ─────────────────────────────────────────────

const sortBtn = document.querySelector('#sortbutton');

idInput.addEventListener('input', validateId);
updateBtn.addEventListener('click', updateInvoice);
sortBtn.addEventListener('click', sorting);

// Load data immediately on page open
loaddata();