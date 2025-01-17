// Declare jogosIncluidos como variável global
const jogosIncluidos = [];

// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    const numeros = document.querySelectorAll('.numero');
    const limparBtn = document.getElementById('limpar');
    const sugestaoBtn = document.getElementById('sugestao');
    const conferirBtn = document.getElementById('conferir');
    const incluirBtn = document.getElementById('incluir');
    const listaJogos = document.getElementById('lista-jogos');
    const overlay = document.getElementById('overlay');
    const numerosSelecionados = new Set();

    // Funcionalidade de seleção de números
    numeros.forEach(numero => {
        numero.addEventListener('click', () => {
            const num = parseInt(numero.dataset.numero);
            if (numero.classList.contains('selecionado')) {
                numero.classList.remove('selecionado');
                numerosSelecionados.delete(num);
            } else if (numerosSelecionados.size < 6) {
                numero.classList.add('selecionado');
                numerosSelecionados.add(num);
            }
        });
    });

    // Botão Limpar
    limparBtn.addEventListener('click', () => {
        numeros.forEach(numero => numero.classList.remove('selecionado'));
        numerosSelecionados.clear();
    });

    // Botão Sugestão
    sugestaoBtn.addEventListener('click', async () => {
        const response = await fetch('/gerar_numeros');
        const data = await response.json();
        
        limparBtn.click();
        data.numeros.forEach(num => {
            const numero = document.querySelector(`[data-numero="${num}"]`);
            numero.classList.add('selecionado');
            numerosSelecionados.add(num);
        });
    });

    // Botão Incluir
    incluirBtn.addEventListener('click', () => {
        if (numerosSelecionados.size !== 6) {
            alert('Selecione 6 números antes de incluir o jogo!');
            return;
        }

        const numerosArray = Array.from(numerosSelecionados).sort((a, b) => a - b);
        jogosIncluidos.push(numerosArray);

        adicionarJogoNaLista(numerosArray);
        limparBtn.click();
    });

    // Botão Conferir
    conferirBtn.addEventListener('click', async () => {
        if (jogosIncluidos.length === 0) {
            alert('Inclua pelo menos um jogo antes de conferir!');
            return;
        }

        const inicio = document.getElementById('inicio').value;
        const fim = document.getElementById('fim').value;

        if (!inicio || !fim || parseInt(inicio) > parseInt(fim)) {
            alert('Verifique os números dos concursos!');
            return;
        }

        overlay.style.display = 'flex';
        document.querySelector('.progress-text').textContent = 'Conferindo jogos...';

        try {
            console.log('Enviando dados:', {
                inicio: parseInt(inicio),
                fim: parseInt(fim),
                jogos: jogosIncluidos
            });

            const response = await fetch('/conferir', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inicio: parseInt(inicio),
                    fim: parseInt(fim),
                    jogos: jogosIncluidos
                })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            if (data.message) {
                alert(data.message);
                return;
            }

            // Atualizar contagens
            document.getElementById('quatro-acertos').textContent = data.resumo.quatro;
            document.getElementById('cinco-acertos').textContent = data.resumo.cinco;
            document.getElementById('seis-acertos').textContent = data.resumo.seis;

            // Atualizar detalhes
            const detalhesDiv = document.getElementById('detalhes-resultados');
            detalhesDiv.innerHTML = '';

            if (data.acertos && data.acertos.length > 0) {
                data.acertos.forEach(resultado => {
                    const resultadoDiv = document.createElement('div');
                    resultadoDiv.className = 'resultado-item';
                    resultadoDiv.innerHTML = `
                        <div class="resultado-header">
                            <h3>Concurso ${resultado.concurso} - ${resultado.data}</h3>
                            <p>${resultado.local || ''}</p>
                        </div>
                        <div class="resultado-numeros">
                            <div class="numeros-sorteados">
                                <h4>Números Sorteados:</h4>
                                <div class="numeros-lista">
                                    ${resultado.numeros_sorteados
                                        .sort((a, b) => a - b)
                                        .map(n => `<span class="numero-sorteado">${String(n).padStart(2, '0')}</span>`)
                                        .join(' ')}
                                </div>
                            </div>
                            <div class="seu-jogo">
                                <h4>Seu Jogo:</h4>
                                <div class="numeros-lista">
                                    ${resultado.seus_numeros
                                        .sort((a, b) => a - b)
                                        .map(n => `<span class="numero-jogado ${resultado.numeros_sorteados.includes(n) ? 'acerto' : ''}">${String(n).padStart(2, '0')}</span>`)
                                        .join(' ')}
                                </div>
                            </div>
                            <div class="resultado-info">
                                <p class="acertos-info">Acertos: <strong>${resultado.acertos}</strong></p>
                                ${resultado.premio > 0 ? 
                                    `<p class="premio-info">Prêmio: <strong>R$ ${resultado.premio.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong></p>` 
                                    : ''}
                            </div>
                        </div>
                    `;
                    detalhesDiv.appendChild(resultadoDiv);
                });
            } else {
                detalhesDiv.innerHTML = '<p class="sem-resultados">Nenhum prêmio encontrado para os jogos conferidos.</p>';
            }

        } catch (error) {
            console.error('Erro detalhado:', error);
            alert(`Erro ao conferir jogos: ${error.message}`);
        } finally {
            overlay.style.display = 'none';
        }
    });
});

function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    // Eventos da zona de drop
    dropZone.onclick = () => fileInput.click();

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight);
    });

    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    dropZone.classList.add('dragover');
}

function unhighlight() {
    dropZone.classList.remove('dragover');
}

async function handleDrop(e) {
    const file = e.dataTransfer.files[0];
    await processFile(file);
}

async function handleFileSelect(e) {
    const file = e.target.files[0];
    await processFile(file);
}

async function processFile(file) {
    if (!file) return;

    // Mostra um indicador de processamento
    const dropZone = document.getElementById('drop-zone');
    dropZone.classList.add('processing');
    
    try {
        const formData = new FormData();
        formData.append('file', file);

        // Faz o upload e processamento do arquivo
        const response = await fetch('/processar_arquivo', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }

        if (data.jogos && data.jogos.length > 0) {
            // Remove jogos duplicados antes de adicionar
            const jogosAtuais = new Set(jogosIncluidos.map(j => JSON.stringify(j)));
            
            data.jogos.forEach(jogo => {
                const jogoStr = JSON.stringify(jogo);
                if (!jogosAtuais.has(jogoStr)) {
                    jogosIncluidos.push(jogo);
                    adicionarJogoNaLista(jogo);
                    jogosAtuais.add(jogoStr);
                }
            });
            
            alert(`${data.jogos.length} jogos importados com sucesso!`);
        } else {
            alert('Nenhum jogo válido encontrado no arquivo');
        }

    } catch (error) {
        console.error('Erro:', error);
        alert(`Erro ao processar arquivo: ${error.message}`);
    } finally {
        // Remove o indicador de processamento
        dropZone.classList.remove('processing');
    }
}

function adicionarJogoNaLista(jogo) {
    const jogoItem = document.createElement('div');
    jogoItem.className = 'jogo-item';
    
    const jogoNumeros = document.createElement('div');
    jogoNumeros.className = 'jogo-numeros';
    
    jogo.forEach(num => {
        const numeroSpan = document.createElement('span');
        numeroSpan.className = 'jogo-numero';
        numeroSpan.textContent = String(num).padStart(2, '0');
        jogoNumeros.appendChild(numeroSpan);
    });

    const btnRemover = document.createElement('button');
    btnRemover.className = 'btn-remover';
    btnRemover.textContent = 'Remover';
    btnRemover.onclick = () => {
        jogoItem.remove();
        const index = jogosIncluidos.findIndex(j => 
            JSON.stringify(j) === JSON.stringify(jogo)
        );
        if (index !== -1) {
            jogosIncluidos.splice(index, 1);
        }
    };

    jogoItem.appendChild(jogoNumeros);
    jogoItem.appendChild(btnRemover);
    document.getElementById('lista-jogos').appendChild(jogoItem);
}