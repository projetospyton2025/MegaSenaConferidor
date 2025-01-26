# processing.py
import asyncio
from typing import List, Dict
import aiohttp

async def process_concurso(session: aiohttp.ClientSession, 
                          concurso: int, 
                          jogos: List[List[int]]) -> Dict:
    try:
        async with session.get(f"{API_BASE_URL}/megasena/{concurso}") as response:
            if response.status != 200:
                return None
            
            resultado = await response.json()
            dezenas = [int(d) for d in resultado['dezenas']]
            
            resultados = {
                'acertos': [],
                'resumo': {'quatro': 0, 'cinco': 0, 'seis': 0, 'total_premios': 0}
            }
            
            for jogo in jogos:
                acertos = len(set(jogo) & set(dezenas))
                if acertos >= 4:
                    # Processar premiações
                    premio = calcular_premio(resultado, acertos)
                    resultados['resumo'][f'{acertos}'] += 1
                    resultados['resumo']['total_premios'] += premio
                    
                    resultados['acertos'].append({
                        'concurso': concurso,
                        'acertos': acertos,  
                        'premio': premio,
                        # ... outros campos
                    })
                    
            return resultados
            
    except Exception as e:
        logger.error(f"Erro processando concurso {concurso}: {e}")
        return None

async def process_batch(jogos: List[List[int]], 
                       inicio: int, 
                       fim: int) -> Dict:
    async with aiohttp.ClientSession() as session:
        tasks = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        for concurso in range(inicio, fim + 1):
            async with semaphore:
                task = asyncio.create_task(
                    process_concurso(session, concurso, jogos)
                )
                tasks.append(task)
                
        results = await asyncio.gather(*tasks)
        return combine_results(results)