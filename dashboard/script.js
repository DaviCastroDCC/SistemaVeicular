const API_URL = "http://127.0.0.1:8000/leituras";
const IMG_URL = "http://127.0.0.1:8000/imagem/";

async function carregarLeituras() {
    const resposta = await fetch(API_URL);
    const dados = await resposta.json();

    const corpo = document.querySelector("#tabela tbody");
    corpo.innerHTML = "";

    dados.forEach(item => {
        const linha = document.createElement("tr");
        linha.innerHTML = `
            <td>${item.id}</td>
            <td>${item.placa}</td>
            <td>${new Date(item.data_hora).toLocaleString()}</td>
            <td><img src="${IMG_URL + item.id}" alt="Placa" onerror="this.src=''; this.alt='Sem imagem';"></td>
        `;
        corpo.appendChild(linha);
    });
}

carregarLeituras();
setInterval(carregarLeituras, 5000); // atualiza a cada 5 segundos
