const API = "http://127.0.0.1:8000";

window.onload = carregar;

// ---------------- LISTAR ----------------
async function carregar() {
    const res = await fetch(`${API}/pessoas`);
    const data = await res.json();

    const tabela = document.getElementById("tabela");
    tabela.innerHTML = "";

    data.forEach(p => {
        tabela.innerHTML += `
        <tr>
            <td>${p.nome}</td>
            <td>${p.documento}</td>
            <td>${p.tipo}</td>
            <td>${p.status}</td>
            <td>
                <button onclick="entrada('${p.documento}')">Entrada</button>
                <button onclick="saida('${p.documento}')">Saída</button>
                <button onclick="remover('${p.documento}')">Remover</button>
            </td>
        </tr>
        `;
    });
}

// ---------------- CADASTRAR ----------------
async function cadastrar() {
    const nome = document.getElementById("nome").value;
    const documento = document.getElementById("documento").value;
    const tipo = document.getElementById("tipo").value;

    await fetch(`${API}/pessoas`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ nome, documento, tipo })
    });

    carregar();
}

// ---------------- ENTRADA ----------------
async function entrada(documento) {
    await fetch(`${API}/entrada`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            documento,
            porteiro: "web"
        })
    });

    carregar();
}

// ---------------- SAÍDA ----------------
async function saida(documento) {
    await fetch(`${API}/saida`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            documento,
            porteiro: "web"
        })
    });

    carregar();
}

// ---------------- REMOVER ----------------
async function remover(documento) {
    await fetch(`${API}/pessoas/${documento}`, {
        method: "DELETE"
    });

    carregar();
}