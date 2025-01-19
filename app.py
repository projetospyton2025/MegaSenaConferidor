# app.py
# Valores que podem ser alterados... 

""" MAIN.JS
// Adicione esta validação
    const intervalo = fim - inicio;
    if (intervalo > 100) { //Conferência de no máximo 100 por vez
        const confirmacao = confirm('Para melhor desempenho, recomendamos conferir no máximo 100 concursos por vez. Deseja continuar mesmo assim?');
        if (!confirmacao) {
            return;
        }
    }

   // Adicione esta validação
    const intervalo = fim - inicio;
    if (intervalo > 3000) { //Conferência de no máximo 3000 por vez 

// APP.PY
# Ordena as estatísticas de jogos
        jogos_stats_ordenados = sorted(
            [{'numeros': stats['numeros'], 
              'total': stats['total'], 
              'distribuicao': stats['distribuicao']} 
             for stats in jogos_stats.values()],
            key=lambda x: x['total'],
            reverse=True
        )[:10]  # Retorna apenas os 10 mais frequentes
"""

from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import os
import random  # Adicione esta linha
import aiohttp
import asyncio
import redis
import json





# Configuração do Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
CACHE_EXPIRATION = 60 * 60 * 24  # 24 horas em segundos

# Funções auxiliares para o cache
def get_cached_result(concurso):
    """Tenta obter resultado do cache"""
    try:
        cached = redis_client.get(f"megasena:{concurso}")
        if cached:
            return json.loads(cached)
    except:
        print(f"Erro ao buscar cache para concurso {concurso}")
    return None

def set_cached_result(concurso, data):
    """Armazena resultado no cache"""
    try:
        redis_client.setex(
            f"megasena:{concurso}",
            CACHE_EXPIRATION,
            json.dumps(data)
        )
    except:
        print(f"Erro ao armazenar cache para concurso {concurso}")


app = Flask(__name__)


def atualizar_estatisticas_jogo(stats, jogo, acertos):
    """Atualiza as estatísticas de um jogo"""
    jogo_key = tuple(sorted(jogo))
    if jogo_key not in stats:
        stats[jogo_key] = {
            'total': 0,
            'distribuicao': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            'numeros': list(jogo_key)
        }
    stats[jogo_key]['total'] += 1
    stats[jogo_key]['distribuicao'][acertos] += 1
    return stats

API_BASE_URL = "https://loteriascaixa-api.herokuapp.com/api"

def get_latest_result():
    try:
        response = requests.get(f"{API_BASE_URL}/megasena/latest")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Erro ao buscar último resultado: {str(e)}")
        return None

@app.route('/')
def index():
    latest = get_latest_result()
    ultimo_concurso = latest['concurso'] if latest else 2680
    return render_template('index.html', ultimo_concurso=ultimo_concurso)

@app.route('/gerar_numeros')
def gerar_numeros():
    numeros = random.sample(range(1, 61), 6)
    return jsonify({'numeros': sorted(numeros)})






@app.route('/conferir', methods=['POST'])
def conferir():
    try:
        data = request.get_json()
        inicio = int(data['inicio'])
        fim = int(data['fim'])
        jogos = data['jogos']

        print(f"\nIniciando conferência de {len(jogos)} jogos")
        print(f"Período: concurso {inicio} até {fim}")

        resultados = {
            'acertos': [],
            'resumo': {
                'quatro': 0,
                'cinco': 0,
                'seis': 0
            }
        }

        jogos_stats = {}

        for concurso in range(inicio, fim + 1):
            try:
                # Tenta buscar do cache primeiro
                resultado = get_cached_result(concurso)
                
                # Se não está no cache, busca da API
                if not resultado:
                    print(f"Cache miss para concurso {concurso}")
                    response = requests.get(f"{API_BASE_URL}/megasena/{concurso}", timeout=5)
                    
                    if response.status_code != 200:
                        print(f"Erro ao buscar concurso {concurso}: Status {response.status_code}")
                        continue

                    try:
                        resultado = response.json()
                        # Armazena no cache
                        set_cached_result(concurso, resultado)
                    except ValueError:
                        print(f"Resposta inválida do servidor para concurso {concurso}")
                        continue
                else:
                    print(f"Cache hit para concurso {concurso}")

                dezenas = [int(d) for d in resultado['dezenas']]
                print(f"Dezenas sorteadas: {dezenas}")

                # Resto do código permanece igual...
                for idx, jogo in enumerate(jogos):
                    print(f"\nJogo {idx + 1}: {jogo}")
                    acertos = len(set(jogo) & set(dezenas))
                    print(f"Acertos encontrados: {acertos}")

                    if acertos > 0:
                        jogos_stats = atualizar_estatisticas_jogo(jogos_stats, jogo, acertos)

                    if acertos >= 4:
                        premio = 0
                        for premiacao in resultado['premiacoes']:
                            if ((acertos == 6 and premiacao['descricao'] == '6 acertos') or
                                (acertos == 5 and premiacao['descricao'] == '5 acertos') or
                                (acertos == 4 and premiacao['descricao'] == '4 acertos')):
                                premio = premiacao['valorPremio']
                                break

                        if acertos == 4:
                            resultados['resumo']['quatro'] += 1
                        elif acertos == 5:
                            resultados['resumo']['cinco'] += 1
                        elif acertos == 6:
                            resultados['resumo']['seis'] += 1

                        resultados['acertos'].append({
                            'concurso': resultado['concurso'],
                            'data': resultado['data'],
                            'local': resultado.get('local', ''),
                            'numeros_sorteados': dezenas,
                            'seus_numeros': jogo,
                            'acertos': acertos,
                            'premio': premio
                        })

            except Exception as e:
                print(f"Erro ao processar concurso {concurso}: {str(e)}")
                continue

        # O resto do código permanece igual...
        jogos_stats_ordenados = sorted(
            [{'numeros': stats['numeros'], 
              'total': stats['total'], 
              'distribuicao': stats['distribuicao']} 
             for stats in jogos_stats.values()],
            key=lambda x: x['total'],
            reverse=True
        )[:10]

        if not resultados['acertos']:
            return jsonify({
                'message': 'Nenhum prêmio encontrado nos concursos verificados',
                'resumo': resultados['resumo'],
                'jogos_stats': jogos_stats_ordenados
            }), 200

        return jsonify({
            'acertos': resultados['acertos'],
            'resumo': resultados['resumo'],
            'jogos_stats': jogos_stats_ordenados
        })

    except Exception as e:
        print(f"Erro geral: {str(e)}")
        return jsonify({'error': str(e)}), 500



# Adicione esta função ao seu app.py
@app.route('/processar_arquivo', methods=['POST'])
def processar_arquivo():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    try:
        # Lê o conteúdo do arquivo
        content = file.read()
        jogos = []
        
        # Tenta processar como texto primeiro
        try:
            # Decodifica o conteúdo como texto
            text_content = content.decode('utf-8')
            lines = text_content.strip().split('\n')
            
            for line in lines:
                # Remove espaços extras e divide os números
                numbers = [int(n) for n in line.strip().split() if n.strip().isdigit()]
                
                # Valida os números
                if (len(numbers) == 6 and 
                    all(1 <= n <= 60 for n in numbers) and 
                    len(set(numbers)) == 6):
                    jogos.append(sorted(numbers))
                    
        except Exception as e:
            print(f"Erro ao processar como texto: {str(e)}")
            
            # Se falhou como texto, tenta processar como Excel
            try:
                # Converte o conteúdo para DataFrame
                df = pd.read_excel(content)
                
                for _, row in df.iterrows():
                    # Pega os primeiros 6 valores numéricos da linha
                    numbers = [int(n) for n in row.values[:6] if isinstance(n, (int, float)) and 1 <= n <= 60]
                    
                    if len(numbers) == 6 and len(set(numbers)) == 6:
                        jogos.append(sorted(numbers))
                        
            except Exception as excel_error:
                print(f"Erro ao processar como Excel: {str(excel_error)}")
                
        if not jogos:
            return jsonify({'error': 'Nenhum jogo válido encontrado no arquivo'}), 400
            
        return jsonify({'jogos': jogos})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500




"""
if __name__ == '__main__':
     app.run(debug=True)
"""


     # Agora a parte de configuração da porta
if __name__ == '__main__':
     port = int(os.environ.get("PORT", 5000))  # Obtém a porta do ambiente ou usa 5000 como padrão
     app.run(host="0.0.0.0", port=port)  # Inicia o servidor Flask na porta correta



