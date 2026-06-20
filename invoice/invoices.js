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
// DOM references
// ─────────────────────────────────────────────

const submitBtn    = document.querySelector('#submit');
const showMsg      = document.querySelector('#show');
const totalDisplay = document.querySelector('#total');
const clientInput  = document.querySelector('#client');
const inputError   = document.querySelector('#inputshow');
const qError       = document.querySelector('#qshow');
const pError       = document.querySelector('#pshow');
const quantityInput = document.querySelector('#quantity');
const ppcInput      = document.querySelector('#ppcs');

// ─────────────────────────────────────────────
// Submit invoice
// ─────────────────────────────────────────────

async function add() {
    const headers = authHeaders();
    if (!headers) return;

    const quantity = parseFloat(quantityInput.value) || 0;
    const pricepc  = parseFloat(ppcInput.value) || 0;

    const invoice = {
        name:     clientInput.value,
        product:  document.querySelector('#product').value,
        quantity: quantity,
        ppc:      pricepc,
        Total:    quantity * pricepc
    };

    try {
        const response = await fetch('http://127.0.0.1:8000/add', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(invoice)
        });

        if (handle401(response)) return;

        const data = await response.json();

        if (!response.ok) {
            showMsg.textContent = data.detail || 'Error submitting invoice.';
            return;
        }

        totalDisplay.textContent = invoice.Total;
        showMsg.textContent = data.message;

    } catch (err) {
        console.error(err);
        showMsg.textContent = 'Could not connect to the server.';
    }
}

// ─────────────────────────────────────────────
// Validation
// ─────────────────────────────────────────────

function Correct() {
    const name = clientInput.value;
    if (!/^\D*$/.test(name)) {
        inputError.textContent = "Name shouldn't have any numbers";
    } else {
        inputError.textContent = '';
    }

    const quantity = parseFloat(quantityInput.value);
    const ppc      = parseFloat(ppcInput.value);

    qError.textContent = quantityInput.value !== '' && quantity <= 0
        ? 'Quantity must be greater than 0'
        : '';

    pError.textContent = ppcInput.value !== '' && ppc <= 0
        ? 'Price must be greater than 0'
        : '';
}

// ─────────────────────────────────────────────
// Event listeners
// ─────────────────────────────────────────────

submitBtn.addEventListener('click', add);
clientInput.addEventListener('input', Correct);
quantityInput.addEventListener('input', Correct);
ppcInput.addEventListener('input', Correct);