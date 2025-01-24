#ESTOU COM ESTE ERRO ME AJUDE


from flask import Flask, render_template, request, jsonify, send_file
import requests
from datetime import datetime
import os
import random
import aiohttp
import asyncio
import redis
import json
import pandas as pd
import io

# Configuração do Redis - LOCALHOST
# redis_client = redis.Redis(host='localhost', port=6379, db=0)
# CACHE_EXPIRATION = 60 * 60 * 24  # 24 horas em segundos

import os
import redis

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    db=int(os.getenv('REDIS_DB', 0))
)



try:
    redis_client.ping()
    print("Conexão bem-sucedida ao Redis!")
except redis.ConnectionError as e:
    print(f"Erro ao conectar ao Redis: {e}")



# Funções auxiliares para o cache
def get_cached_result(concurso):
    try:
        cached = redis_client.get(f"megasena:{concurso}")
        if cached:
            return json.loads(cached)
    except:
        print(f"Erro ao buscar cache para concurso {concurso}")
    return None

def set_cached_result(concurso, data):
    try:
        redis_client.setex(f"megasena:{concurso}", CACHE_EXPIRATION, json.dumps(data))
    except:
        print(f"Erro ao armazenar cache para concurso {concurso}")

app = Flask(__name__)

def atualizar_estatisticas_jogo(stats, jogo, acertos):
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

        print(f"Iniciando conferência de {len(jogos)} jogos")
        print(f"Período: concurso {inicio} até {fim}")

        resultados = {
            'acertos': [],
            'resumo': {
                'quatro': 0,
                'cinco': 0,
                'seis': 0,
                'total_premios': 0
            }
        }

        jogos_stats = {}

        for concurso in range(inicio, fim + 1):
            try:
                resultado = get_cached_result(concurso)
                if not resultado:
                    response = requests.get(f"{API_BASE_URL}/megasena/{concurso}", timeout=5)
                    if response.status_code != 200:
                        continue
                    resultado = response.json()
                    set_cached_result(concurso, resultado)

                dezenas = [int(d) for d in resultado['dezenas']]

                for jogo in jogos:
                    acertos = len(set(jogo) & set(dezenas))
                    if acertos > 0:
                        jogos_stats = atualizar_estatisticas_jogo(jogos_stats, jogo, acertos)

                    if acertos >= 4:
                        premio = 0
                        for premiacao in resultado['premiacoes']:
                            if ((acertos == 6 and premiacao['descricao'] == '6 acertos') or
                                (acertos == 5 and premiacao['descricao'] == '5 acertos') or
                                (acertos == 4 and premiacao['descricao'] == '4 acertos')):
                                premio = premiacao['valorPremio']
                                resultados['resumo']['total_premios'] += premio
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
                continue

        resultados['resumo']['total_premios'] = round(resultados['resumo']['total_premios'], 2)
        jogos_stats_ordenados = sorted(
            [{'numeros': stats['numeros'], 
              'total': stats['total'], 
              'distribuicao': stats['distribuicao']} 
             for stats in jogos_stats.values()],
            key=lambda x: x['total'],
            reverse=True
        )[:10]

        return jsonify({
            'acertos': resultados['acertos'],
            'resumo': resultados['resumo'],
            'jogos_stats': jogos_stats_ordenados
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/processar_arquivo', methods=['POST'])
def processar_arquivo():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    try:
        jogos = []
        
        # Tenta processar como texto primeiro
        if file.filename.endswith('.txt'):
            try:
                content = file.read().decode('utf-8-sig')
                
                for line in content.strip().split('\n'):
                    try:
                        line = ''.join(c for c in line if c.isdigit() or c.isspace())
                        numbers = [int(n) for n in line.strip().split() if n.strip()]
                        
                        if (len(numbers) == 6 and 
                            all(1 <= n <= 60 for n in numbers) and 
                            len(set(numbers)) == 6):
                            jogos.append(sorted(numbers))
                    except (ValueError, TypeError):
                        continue
            except Exception as txt_error:
                print(f"Erro ao processar TXT: {str(txt_error)}")
                        
        # Se não é txt, tenta processar como Excel
        elif file.filename.endswith(('.xlsx', '.xls')):
            try:
                content = file.read()
                df = pd.read_excel(io.BytesIO(content))
                
                for _, row in df.iterrows():
                    numbers = []
                    for val in row.values[:6]:
                        try:
                            num = int(float(val))
                            if 1 <= num <= 60:
                                numbers.append(num)
                        except (ValueError, TypeError):
                            continue
                    
                    if len(numbers) == 6 and len(set(numbers)) == 6:
                        jogos.append(sorted(numbers))
            except Exception as excel_error:
                print(f"Erro ao processar Excel: {str(excel_error)}")
                
        else:
            return jsonify({
                'error': 'Formato de arquivo não suportado. Use .txt ou .xlsx'
            }), 400
            
        if not jogos:
            return jsonify({
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
            
        return jsonify({'jogos': jogos})
        
    except UnicodeDecodeError:
        return jsonify({
            'error': 'Erro ao ler o arquivo. Certifique-se que é um arquivo de texto válido.'
        }), 400
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        return jsonify({
            'error': 'Erro ao processar o arquivo. Verifique o formato e tente novamente.'
        }), 500
        

@app.route('/exportar/<tipo>/<formato>', methods=['POST'])
def exportar_dados(tipo, formato):
    try:
        data = request.json
        if tipo == 'resumo-acertos':
            return exportar_resumo_acertos(data, formato)
        elif tipo == 'jogos-premiados':
            return exportar_jogos_premiados(data, formato)
        elif tipo == 'jogos-sorteados':
            return exportar_jogos_sorteados(data, formato)
        else:
            return jsonify({'error': 'Tipo de exportação inválido'}), 400
    except Exception as e:
        print(f"Erro na exportação: {str(e)}")
        return jsonify({'error': str(e)}), 500

def exportar_resumo_acertos(data, formato):
    try:
        # Criação do DataFrame com os dados fornecidos
        df = pd.DataFrame({
            'Tipo': ['4 Acertos', '5 Acertos', '6 Acertos', 'Total de Prêmios'],
            'Quantidade': [
                data['resumo']['quatro'],
                data['resumo']['cinco'],
                data['resumo']['seis'],
                ''
            ],
            'Valor Total': [
                data['resumo'].get('valor_quatro', 0),
                data['resumo'].get('valor_cinco', 0),
                data['resumo'].get('valor_seis', 0),
                data['resumo'].get('total_premios', 0)
            ]
        })

        # Exportação para formato Excel
        if formato == 'xlsx':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Resumo de Acertos', index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='resumo_acertos.xlsx'
            )

        # Exportação para formato HTML
        elif formato == 'html':
            html_content = df.to_html(index=False, classes='table table-striped')
            html = f'''
            <html>
            <head>
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #008751; color: white; }}
                </style>
            </head>
            <body>
                <h2>Resumo de Acertos</h2>
                {html_content}
            </body>
            </html>
            '''
            return send_file(
                io.BytesIO(html.encode()),
                mimetype='text/html',
                as_attachment=True,
                download_name='resumo_acertos.html'
            )
        
        # Caso o formato não seja suportado
        else:
            raise ValueError(f"Formato '{formato}' não suportado. Use 'xlsx' ou 'html'.")

    except Exception as e:
        raise Exception(f"Erro ao exportar resumo: {str(e)}")

def exportar_jogos_premiados(data, formato):
    try:
        rows = []
        for resultado in data['acertos']:
            rows.append({
                'Concurso': resultado['concurso'],
                'Data': resultado['data'],
                'Local': resultado['local'],
                'Números Sorteados': ' '.join(str(n).zfill(2) for n in sorted(resultado['numeros_sorteados'])),
                'Seu Jogo': ' '.join(str(n).zfill(2) for n in sorted(resultado['seus_numeros'])),
                'Acertos': resultado['acertos'],
                'Prêmio': f"R$ {resultado['premio']:,.2f}",
                'Status': 'Premiado' if resultado['premio'] > 0 else 'Acumulado'
            })
        
        df = pd.DataFrame(rows)
        
        if formato == 'xlsx':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Jogos Premiados', index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='jogos_premiados.xlsx'
            )
        
        elif formato == 'html':
            html_content = df.to_html(index=False, classes='table table-striped')
            html = f'''
            <html>
            <head>
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #008751; color: white; }}
                </style>
            </head>
            <body>
                <h2>Jogos Premiados</h2>
                {html_content}
            </body>
            </html>
            '''
            return send_file(
                io.BytesIO(html.encode()),
                mimetype='text/html',
                as_attachment=True,
                download_name='jogos_premiados.html'
            )
    except Exception as e:
        raise Exception(f"Erro ao exportar jogos premiados: {str(e)}")
        
def exportar_jogos_sorteados(data, formato):
    try:
        rows = []
        for jogo in data['jogos_stats']:
            distribuicao = []
            for i in range(1, 7):
                if jogo['distribuicao'].get(i, 0) > 0:
                    distribuicao.append(f"{i} pontos: {jogo['distribuicao'][i]}")
            
            rows.append({
                'Jogo': ' '.join(str(n).zfill(2) for n in jogo['numeros']),
                'Total': jogo['total'],
                'Distribuição': ', '.join(distribuicao)
            })
        
        df = pd.DataFrame(rows)
        
        if formato == 'xlsx':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Jogos Mais Sorteados', index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='jogos_sorteados.xlsx'
            )
        
        elif formato == 'html':
            html_content = df.to_html(index=False, classes='table table-striped')
            html = f'''
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #008751; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    tr:hover {{ background-color: #ddd; }}
                </style>
            </head>
            <body>
                <h2>Jogos Mais Sorteados</h2>
                {html_content}
            </body>
            </html>
            '''
            return send_file(
                io.BytesIO(html.encode('utf-8')),
                mimetype='text/html',
                as_attachment=True,
                download_name='jogos_sorteados.html'
            )
    except Exception as e:
        raise Exception(f"Erro ao exportar jogos sorteados: {str(e)}")



def exportar_jogos_sorteados(data, formato):
    try:
        # Prepara as linhas de dados
        rows = []
        for jogo in data['jogos_stats']:
            distribuicao = []
            # Monta a distribuição de acertos (1 a 6 pontos)
            for i in range(1, 7):
                if jogo['distribuicao'].get(i, 0) > 0:
                    distribuicao.append(f"{i} pontos: {jogo['distribuicao'][i]}")
            
            # Adiciona cada jogo com suas estatísticas
            rows.append({
                'Jogo': ' '.join(str(n).zfill(2) for n in jogo['numeros']),
                'Total': jogo['total'],
                'Distribuição': ', '.join(distribuicao)
            })
        
        # Cria DataFrame com os dados
        df = pd.DataFrame(rows)
        
        # Exportação para Excel
        if formato == 'xlsx':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Jogos Mais Sorteados', index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='jogos_sorteados.xlsx'
            )
        
        # Exportação para HTML
        elif formato == 'html':
            html_content = df.to_html(index=False, classes='table table-striped')
            html = f'''
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #008751; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    tr:hover {{ background-color: #ddd; }}
                </style>
            </head>
            <body>
                <h2>Jogos Mais Sorteados</h2>
                {html_content}
            </body>
            </html>
            '''
            return send_file(
                io.BytesIO(html.encode('utf-8')),
                mimetype='text/html',
                as_attachment=True,
                download_name='jogos_sorteados.html'
            )
    except Exception as e:
        raise Exception(f"Erro ao exportar jogos sorteados: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


""" LOCALHOST
if __name__ == '__main__':
    app.run(debug=True)


# Agora a parte de configuração da porta
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Obtém a porta do ambiente ou usa 5000 como padrão
    app.run(host="0.0.0.0", port=port)  # Inicia o servidor Flask na porta correta

"""

#exportar_dados
#exportar_resumo_acertos
#exportar_jogos_premiados
#exportar_jogos_sorteados