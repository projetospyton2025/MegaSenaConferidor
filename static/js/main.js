// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const numeros = document.querySelectorAll('.numero');
    const limparBtn = document.getElementById('limpar');
    const sugestaoBtn = document.getElementById('sugestao');
    const conferirBtn = document.getElementById('conferir');
    const incluirBtn = document.getElementById('incluir');
    const listaJogos = document.getElementById('lista-jogos');
    const overlay = document.getElementById('overlay');
    const numerosSelecionados = new Set();
    const jogosIncluidos = [];

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

        const jogoItem = document.createElement('div');
        jogoItem.className = 'jogo-item';
        
        const jogoNumeros = document.createElement('div');
        jogoNumeros.className = 'jogo-numeros';
        
        numerosArray.forEach(num => {
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
            const index = jogosIncluidos.findIndex(jogo => 
                JSON.stringify(jogo) === JSON.stringify(numerosArray)
            );
            if (index !== -1) {
                jogosIncluidos.splice(index, 1);
            }
        };

        jogoItem.appendChild(jogoNumeros);
        jogoItem.appendChild(btnRemover);
        listaJogos.appendChild(jogoItem);

        limparBtn.click();
    });

    // Botão Conferir
// Substitua apenas a parte do evento do botão conferir

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
        console.log('Resposta recebida:', data);  // Log para debug

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
 // # Atualização no JavaScript para exibir os resultados
function atualizarResultados(resultados) {
    const detalhesDiv = document.getElementById('detalhes-resultados');
    detalhesDiv.innerHTML = '';

    // Adiciona o resumo geral
    const resumoDiv = document.createElement('div');
    resumoDiv.className = 'resumo-geral';
    resumoDiv.innerHTML = `
        <div class="resumo-header">
            <h3>Resumo dos Resultados</h3>
        </div>
        <div class="resumo-cards">
            <div class="resumo-card">
                <h4>Quadras</h4>
                <div class="resumo-numero">${resultados.resumo.quatro}</div>
            </div>
            <div class="resumo-card">
                <h4>Quinas</h4>
                <div class="resumo-numero">${resultados.resumo.cinco}</div>
            </div>
            <div class="resumo-card">
                <h4>Senas</h4>
                <div class="resumo-numero">${resultados.resumo.seis}</div>
            </div>
        </div>
    `;
    detalhesDiv.appendChild(resumoDiv);

    // Adiciona cada resultado individual
    resultados.acertos.forEach(resultado => {
        const resultadoDiv = document.createElement('div');
        resultadoDiv.className = 'resultado-card';
        
        resultadoDiv.innerHTML = `
            <div class="resultado-header">
                <div class="concurso-info">
                    <h3>Concurso ${resultado.concurso}</h3>
                    <p>${resultado.data} - ${resultado.local}</p>
                </div>
                <div class="premio-badge">
                    ${resultado.acertos} Acertos
                </div>
            </div>
            
            <div class="numeros-container">
                <div class="numeros-grupo">
                    <h4>Números Sorteados</h4>
                    <div class="numeros-bolas">
                        ${resultado.numeros_sorteados
                            .map(n => `
                                <div class="bola">
                                    ${String(n).padStart(2, '0')}
                                </div>
                            `).join('')}
                    </div>
                </div>
                
                <div class="numeros-grupo">
                    <h4>Seu Jogo</h4>
                    <div class="numeros-bolas">
                        ${resultado.seus_numeros
                            .map(n => `
                                <div class="bola ${resultado.numeros_sorteados.includes(n) ? 'acertou' : ''}">
                                    ${String(n).padStart(2, '0')}
                                </div>
                            `).join('')}
                    </div>
                </div>
            </div>
            
            ${resultado.premio > 0 ? `
                <div class="premio-info">
                    <strong>Prêmio:</strong> R$ ${resultado.premio.toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}
                </div>
            ` : ''}
        `;
        
        detalhesDiv.appendChild(resultadoDiv);
    });
}

		} catch (error) {
			console.error('Erro detalhado:', error);
			alert(`Erro ao conferir jogos: ${error.message}`);
		} finally {
			overlay.style.display = 'none';
		}
	});

});

