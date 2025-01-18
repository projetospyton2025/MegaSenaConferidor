// Variáveis globais
const jogosIncluidos = [];
const jogosSelecionados = new Set();

// Função para atualizar o contador e mensagem
function atualizarContadorJogos() {
    const quantidade = jogosIncluidos.length;
    const contadorElement = document.getElementById('contador-jogos');
    if (contadorElement) {
        contadorElement.textContent = quantidade;
    }

    // Atualiza o título com singular/plural
    const tituloJogos = document.querySelector('.jogos-incluidos h3');
    if (tituloJogos) {
        tituloJogos.textContent = `Jogos Incluídos (${quantidade} ${quantidade === 1 ? 'jogo' : 'jogos'})`;
    }
}

// Função para formatar mensagens de jogos
function formatarMensagemJogos(quantidade, acao) {
    if (acao === 'incluir') {
        return `${quantidade} jogo${quantidade === 1 ? ' foi incluído' : 's foram incluídos'} com sucesso!`;
    } else if (acao === 'remover') {
        return `${quantidade} jogo${quantidade === 1 ? ' foi removido' : 's foram removidos'} com sucesso!`;
    }
    return '';
}

// Função principal - Inicialização do documento
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

    // Adiciona eventos para os novos botões
    document.getElementById('btn-limpar-todos').addEventListener('click', limparTodosJogos);
    document.getElementById('btn-remover-selecionados').addEventListener('click', removerJogosSelecionados);

    // Inicializa o contador
    atualizarContadorJogos();

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
        atualizarContadorJogos();
        alert('1 jogo foi incluído com sucesso!');
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

            if (confirm('Deseja limpar os jogos conferidos?')) {
                limparTodosJogos();
            }

        } catch (error) {
            console.error('Erro detalhado:', error);
            alert(`Erro ao conferir jogos: ${error.message}`);
        } finally {
            overlay.style.display = 'none';
        }
    });
});

// Funções de Drag and Drop
function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    dropZone.onclick = () => fileInput.click();

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
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

    const dropZone = document.getElementById('drop-zone');
    dropZone.classList.add('processing');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/processar_arquivo', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        if (data.jogos && data.jogos.length > 0) {
            const jogosAtuais = new Set(jogosIncluidos.map(j => JSON.stringify(j)));
            let jogosNovos = 0;

            data.jogos.forEach(jogo => {
                const jogoStr = JSON.stringify(jogo);
                if (!jogosAtuais.has(jogoStr)) {
                    jogosIncluidos.push(jogo);
                    adicionarJogoNaLista(jogo);
                    jogosAtuais.add(jogoStr);
                    jogosNovos++;
                }
            });

            atualizarContadorJogos();
            alert(formatarMensagemJogos(jogosNovos, 'incluir'));

        } else {
            alert('Nenhum jogo válido encontrado no arquivo');
        }

    } catch (error) {
        console.error('Erro:', error);
        alert(`Erro ao processar arquivo: ${error.message}`);
    } finally {
        dropZone.classList.remove('processing');
    }
}

// Função para adicionar jogo na lista
function adicionarJogoNaLista(jogo) {
    const jogoItem = document.createElement('div');
    jogoItem.className = 'jogo-item';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'jogo-checkbox';
    checkbox.onclick = (e) => {
        const jogoStr = JSON.stringify(jogo);
        if (e.target.checked) {
            jogosSelecionados.add(jogoStr);
            jogoItem.classList.add('selecionado');
        } else {
            jogosSelecionados.delete(jogoStr);
            jogoItem.classList.remove('selecionado');
        }
        atualizarBotoesSeleção();
    };

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
    btnRemover.onclick = () => removerJogo(jogo, jogoItem);

    jogoItem.appendChild(checkbox);
    jogoItem.appendChild(jogoNumeros);
    jogoItem.appendChild(btnRemover);
    document.getElementById('lista-jogos').appendChild(jogoItem);
}

// Função para remover jogo
function removerJogo(jogo, jogoItem) {
    const index = jogosIncluidos.findIndex(j =>
        JSON.stringify(j) === JSON.stringify(jogo)
    );
    if (index !== -1) {
        jogosIncluidos.splice(index, 1);
        jogosSelecionados.delete(JSON.stringify(jogo));
        jogoItem.remove();
        atualizarBotoesSeleção();
        atualizarContadorJogos();
        alert(formatarMensagemJogos(1, 'remover'));
    }
}

// Função para limpar todos os jogos
function limparTodosJogos() {
    const quantidadeAtual = jogosIncluidos.length;
    if (quantidadeAtual === 0) {
        alert('Não há jogos para remover');
        return;
    }

    if (confirm('Tem certeza que deseja remover todos os jogos?')) {
        jogosIncluidos.length = 0;
        jogosSelecionados.clear();
        document.getElementById('lista-jogos').innerHTML = '';
        atualizarBotoesSeleção();
        atualizarContadorJogos();
        alert(formatarMensagemJogos(quantidadeAtual, 'remover'));
    }
}

// Função para remover jogos selecionados
function removerJogosSelecionados() {
    if (jogosSelecionados.size === 0) {
        alert('Selecione pelo menos um jogo para remover');
        return;
    }

    const quantidadeRemover = jogosSelecionados.size;
    if (confirm(`Deseja remover ${quantidadeRemover} jogo${quantidadeRemover === 1 ? '' : 's'} selecionado${quantidadeRemover === 1 ? '' : 's'}?`)) {
        jogosSelecionados.forEach(jogoStr => {
            const jogo = JSON.parse(jogoStr);
            const index = jogosIncluidos.findIndex(j =>
                JSON.stringify(j) === jogoStr
            );
            if (index !== -1) {
                jogosIncluidos.splice(index,jogosIncluidos.splice(index, 1));
            }
        });

        document.querySelectorAll('.jogo-checkbox:checked').forEach(checkbox => {
            checkbox.closest('.jogo-item').remove();
        });

        jogosSelecionados.clear();
        atualizarBotoesSeleção();
        atualizarContadorJogos();
        alert(formatarMensagemJogos(quantidadeRemover, 'remover'));
    }
}

// Função para atualizar botões de seleção
function atualizarBotoesSeleção() {
    const removerSelecionadosBtn = document.getElementById('btn-remover-selecionados');
    if (removerSelecionadosBtn) {
        removerSelecionadosBtn.disabled = jogosSelecionados.size === 0;
    }
}