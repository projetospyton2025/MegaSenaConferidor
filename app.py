# app.py
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

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




# app.py - Apenas a parte que precisa mudar
@app.route('/conferir', methods=['POST'])
def conferir():
    try:
        data = request.get_json()
        inicio = int(data['inicio'])
        fim = int(data['fim'])
        jogos = data['jogos']

        print(f"\nIniciando conferência de {len(jogos)} jogos")
        print(f"Período: concurso {inicio} até {fim}")
        print(f"Jogos recebidos: {jogos}\n")

        resultados = {
            'acertos': [],
            'resumo': {
                'quatro': 0,
                'cinco': 0,
                'seis': 0
            }
        }

        # Verifica cada concurso
        for concurso in range(inicio, fim + 1):
            try:
                print(f"\nVerificando concurso {concurso}:")
                response = requests.get(f"{API_BASE_URL}/megasena/{concurso}", timeout=5)
                
                if response.status_code != 200:
                    print(f"Erro ao buscar concurso {concurso}: Status {response.status_code}")
                    continue

                resultado = response.json()
                dezenas = [int(d) for d in resultado['dezenas']]
                print(f"Dezenas sorteadas: {dezenas}")
                
                # Verifica cada jogo contra este concurso
                for idx, jogo in enumerate(jogos):
                    print(f"\nJogo {idx + 1}: {jogo}")
                    acertos = len(set(jogo) & set(dezenas))
                    print(f"Acertos encontrados: {acertos}")
                    
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
                        print(f"Prêmio encontrado! {acertos} acertos")

            except Exception as e:
                print(f"Erro ao processar concurso {concurso}: {str(e)}")
                continue

        print("\nResumo final:")
        print(f"Quadras: {resultados['resumo']['quatro']}")
        print(f"Quinas: {resultados['resumo']['cinco']}")
        print(f"Senas: {resultados['resumo']['seis']}")

        if not resultados['acertos']:
            return jsonify({
                'message': 'Nenhum prêmio encontrado nos concursos verificados',
                'resumo': resultados['resumo']
            }), 200

        return jsonify(resultados)

    except Exception as e:
        print(f"Erro geral: {str(e)}")
        return jsonify({'error': str(e)}), 500


#BOTÃO TESTE NO HTML EXCLUA SE NÃO QUISER MAIS.. 
"""
@app.route('/gerar_teste')
def gerar_teste():
    try:
        # Busca o último concurso
        response = requests.get(f"{API_BASE_URL}/megasena/latest")
        if response.status_code == 200:
            resultado = response.json()
            concurso = resultado['concurso']
            dezenas = [int(d) for d in resultado['dezenas']]
            
            # Cria um jogo com 4 números do último sorteio para garantir prêmio
            jogo_teste = dezenas[:4] + [58, 59]  # 4 números certos + 2 errados
            
            return jsonify({
                'concurso': concurso,
                'dezenas_sorteadas': dezenas,
                'jogo_teste': jogo_teste
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
"""


if __name__ == '__main__':
    app.run(debug=True)