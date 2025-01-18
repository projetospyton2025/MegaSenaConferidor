# MegaSenaConferidor

Este é um sistema web para conferência de jogos da Mega Sena. Suas principais funcionalidades são:

Seleção de Jogos:

Interface visual com 60 números (volante da Mega Sena)
Permite selecionar 6 números manualmente
Botão "Palpite" para gerar números aleatórios
Botão "Limpar" para limpar seleção


Importação de Jogos:

Área de "drag and drop" para arquivos
Aceita arquivos .txt e .xlsx
Permite carregar múltiplos jogos de uma vez
Mostra contador de jogos importados


Gerenciamento de Jogos:

Lista todos os jogos incluídos
Permite selecionar múltiplos jogos (checkbox)
Opção para remover jogos individualmente
Botão para remover jogos selecionados
Botão para limpar todos os jogos


Conferência de Resultados:

Define intervalo de concursos (inicial e final)
Checkbox "Somente premiados" para filtrar resultados
Verifica acertos de 4, 5 e 6 números
Mostra prêmios quando disponíveis


Exibição de Resultados:

Resumo com quantidade de quadras, quinas e senas
Lista detalhada de cada acerto encontrado
Mostra números sorteados vs números jogados
Destaque visual para números acertados


Backend (Flask):

API para consulta de resultados da Mega Sena
Processamento de arquivos
Cache de resultados para otimização
Conferência paralela usando threads


Interface Responsiva:

Design moderno e intuitivo
Animações e feedback visual
Indicadores de progresso
Mensagens de confirmação e erro



O sistema é projetado para facilitar a conferência de múltiplos jogos em vários concursos da Mega Sena, oferecendo uma interface amigável e recursos de otimização para melhor performance. Copy