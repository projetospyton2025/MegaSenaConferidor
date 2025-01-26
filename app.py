from flask import Flask, render_template, request, jsonify, send_file
from redis_config import redis_config
from datetime import datetime
from dotenv import load_dotenv
import logging
import random
import aiohttp
import asyncio
import json
import pandas as pd
import io
import os

async def fetch_with_retry(session, url, max_retries=3):
    timeout = aiohttp.ClientTimeout(total=30)
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)
    return None

async def process_concurso(session, concurso, jogos):
    try:
        cached = redis_config.get_cached_result(concurso)
        if cached:
            return cached
            
        resultado = await fetch_with_retry(session, f"{API_BASE_URL}/megasena/{concurso}")
        if resultado:
            redis_config.set_cached_result(concurso, resultado)
        return resultado
    except Exception as e:
        logger.error(f"Erro concurso {concurso}: {e}")
        return None



FLASK_RUN_TIMEOUT = 900  # 15 minutos
CHUNK_SIZE = 1000  # Reduzido de 5000 para 1000
CONCURSOS_PER_BATCH = 930  # Manter atual divisão de concursos
MAX_CONCURRENT_REQUESTS = 5  # Reduzido de 10 para 5

# Configuração de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Mega Sena Conferidor")

#ADICIONADO HOJE 26-01-2025
# Carregar variáveis do .env
load_dotenv()


app = Flask(__name__)

API_BASE_URL = "https://loteriascaixa-api.herokuapp.com/api"

async def get_latest_result():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/megasena/latest") as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        logger.error(f"Erro ao buscar último resultado: {str(e)}")
        return None

@app.route('/')
async def index():
    latest = await get_latest_result()
    ultimo_concurso = latest['concurso'] if latest else 2680
    return render_template('index.html', ultimo_concurso=ultimo_concurso)

@app.route('/gerar_numeros')
async def gerar_numeros():
    numeros = random.sample(range(1, 61), 6)
    return jsonify({'numeros': sorted(numeros)})

@app.route('/processar_arquivo', methods=['POST'])
def processar_arquivo():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    try:
        jogos = []
        logger.info(f"Processando arquivo: {file.filename}")
        
        if file.filename.endswith('.txt'):
            try:
                content = file.read().decode('utf-8-sig')
                for line in content.strip().split('\n'):
                    try:
                        line = ''.join(c for c in line if c.isdigit() or c.isspace())
                        numbers = [int(n) for n in line.strip().split()]
                        if len(numbers) == 6 and all(1 <= n <= 60 for n in numbers) and len(set(numbers)) == 6:
                            jogos.append(sorted(numbers))
                    except Exception as e:
                        logger.error(f"Erro na linha: {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"Erro no TXT: {str(e)}")
                
        elif file.filename.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(file)
                for _, row in df.iterrows():
                    numbers = []
                    for val in row.values[:6]:
                        try:
                            num = int(float(val))
                            if 1 <= num <= 60:
                                numbers.append(num)
                        except:
                            continue
                    if len(numbers) == 6 and len(set(numbers)) == 6:
                        jogos.append(sorted(numbers))
            except Exception as e:
                logger.error(f"Erro no Excel: {str(e)}")
        else:
            return jsonify({'error': 'Use .txt ou .xlsx'}), 400

        if not jogos:
            return jsonify({'error': 'Nenhum jogo válido encontrado'}), 400

        logger.info(f"Jogos processados: {len(jogos)}")
        return jsonify({'jogos': jogos})

    except Exception as e:
        logger.error(f"Erro geral: {str(e)}")
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500





@app.route('/conferir', methods=['POST'])
async def conferir():
    try:
        data = request.get_json()
        inicio = int(data.get('inicio', 1))
        fim = int(data.get('fim', 2680))
        jogos = data['jogos']

        resultados_finais = {
            'acertos': [],
            'resumo': {'quatro': 0, 'cinco': 0, 'seis': 0, 'total_premios': 0},
            'jogos_stats': {}  # Adicionado para estatísticas por jogo
        }

        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i in range(inicio, fim + 1, 930):
                fim_lote = min(i + 929, fim)
                
                semaphore = asyncio.Semaphore(5)
                for concurso in range(i, fim_lote + 1):
                    async with semaphore:
                        try:
                            cached = redis_config.get_cached_result(concurso)
                            if cached:
                                resultado = cached
                            else:
                                async with session.get(f"{API_BASE_URL}/megasena/{concurso}") as response:
                                    if response.status == 200:
                                        resultado = await response.json()
                                        redis_config.set_cached_result(concurso, resultado)
                                    else:
                                        continue

                            dezenas = [int(d) for d in resultado['dezenas']]
                            
                            # Atualiza estatísticas para cada jogo
                            for jogo in jogos:
                                resultados_finais['jogos_stats'] = atualizar_estatisticas_jogo(
                                    resultados_finais['jogos_stats'], 
                                    jogo, 
                                    dezenas
                                )
                                
                                # Processa premiações
                                acertos = len(set(jogo) & set(dezenas))
                                if acertos >= 4:
                                    premio = 0
                                    for premiacao in resultado['premiacoes']:
                                        if ((acertos == 6 and premiacao['descricao'] == '6 acertos') or
                                            (acertos == 5 and premiacao['descricao'] == '5 acertos') or
                                            (acertos == 4 and premiacao['descricao'] == '4 acertos')):
                                            premio = float(premiacao['valorPremio'])
                                            break

                                    resultados_finais['resumo'][f'{"quatro" if acertos == 4 else "cinco" if acertos == 5 else "seis"}'] += 1
                                    resultados_finais['resumo']['total_premios'] += premio

                                    resultados_finais['acertos'].append({
                                        'concurso': resultado['concurso'],
                                        'data': resultado['data'],
                                        'local': resultado.get('local', ''),
                                        'numeros_sorteados': dezenas,
                                        'seus_numeros': jogo,
                                        'acertos': acertos,
                                        'premio': premio
                                    })

                        except Exception as e:
                            logger.error(f"Erro no concurso {concurso}: {str(e)}")
                            continue

                await asyncio.sleep(1)

        # Processa e ordena as estatísticas finais
        jogos_stats_ordenados = sorted(
            [{'numeros': stats['numeros'], 
              'total': stats['total'], 
              'distribuicao': stats['distribuicao']} 
             for stats in resultados_finais['jogos_stats'].values()],
            key=lambda x: x['total'],
            reverse=True
        )[:10]

        resultados_finais['jogos_stats'] = jogos_stats_ordenados
        return jsonify(resultados_finais)

    except Exception as e:
        logger.error(f"Erro na conferência: {str(e)}")
        return jsonify({'error': str(e)}), 500





def atualizar_estatisticas_jogo(jogos_stats, jogo, dezenas):
    jogo_key = tuple(sorted(jogo))
    acertos = len(set(jogo) & set(dezenas))
    
    if jogo_key not in jogos_stats:
        jogos_stats[jogo_key] = {
            'numeros': list(jogo_key),
            'total': 0,
            'distribuicao': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        }
    
    jogos_stats[jogo_key]['total'] += 1
    jogos_stats[jogo_key]['distribuicao'][acertos] += 1

    return jogos_stats

# Funções auxiliares para adicionar em app.py:
def calcular_premio(resultado, acertos):
    for premiacao in resultado['premiacoes']:
        if ((acertos == 6 and premiacao['descricao'] == '6 acertos') or
            (acertos == 5 and premiacao['descricao'] == '5 acertos') or
            (acertos == 4 and premiacao['descricao'] == '4 acertos')):
            return premiacao['valorPremio']
    return 0

def atualizar_resumo(resultados, acertos, premio):
    if acertos == 4:
        resultados['resumo']['quatro'] += 1
    elif acertos == 5:
        resultados['resumo']['cinco'] += 1
    elif acertos == 6:
        resultados['resumo']['seis'] += 1
    resultados['resumo']['total_premios'] += premio

def registrar_acerto(resultados, resultado, jogo, acertos, premio):
    resultados['acertos'].append({
        'concurso': resultado['concurso'],
        'data': resultado['data'],
        'local': resultado.get('local', ''),
        'numeros_sorteados': resultado['dezenas'],
        'seus_numeros': jogo,
        'acertos': acertos,
        'premio': premio
    })

def processar_resultados_finais(resultados, jogos_stats):
    resultados['resumo']['total_premios'] = round(resultados['resumo']['total_premios'], 2)
    jogos_stats_ordenados = sorted(
        [{'numeros': stats['numeros'], 
          'total': stats['total'], 
          'distribuicao': stats['distribuicao']} 
         for stats in jogos_stats.values()],
        key=lambda x: x['total'],
        reverse=True
    )[:10]
    
    return {
        'acertos': resultados['acertos'],
        'resumo': resultados['resumo'],
        'jogos_stats': jogos_stats_ordenados
    }




# @app.route('/status')
# def get_status():
#     if not stats.start_time:
#         return jsonify({'status': 'idle'})
        
#     return jsonify({
#         'status': 'processing',
#         'processed_jogos': stats.processed_jogos,
#         'processed_concursos': stats.processed_concursos,
#         'errors': stats.errors,
#         'elapsed_time': time.time() - stats.start_time
#     })

"""
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
"""

# Agora a parte de configuração da porta
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Obtém a porta do ambiente ou usa 5000 como padrão
    app.run(host="0.0.0.0", port=port)  # Inicia o servidor Flask na porta correta

