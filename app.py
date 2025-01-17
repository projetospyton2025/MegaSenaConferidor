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






if __name__ == '__main__':
    app.run(debug=True)