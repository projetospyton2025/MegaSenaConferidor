# MegaSenaConferidor.ps1
# Script para criar e configurar a estrutura do projeto MegaSenaConferidor

#No entanto, se você quiser que o script funcione de forma mais dinâmica 
#(ou seja, rodar no diretório onde o script está localizado, sem precisar modificar manualmente o caminho), 
#você pode usar a variável $PSScriptRoot, que aponta para o diretório onde o script está sendo executado:

# Diretório do projeto será o local do script
 $projectDir = Join-Path -Path $PSScriptRoot -ChildPath "MegaSenaConferidor"


# a macro sempre rodará nesse caminho específico, independentemente de onde você esteja rodando o script.
# a macro *.ps1 tem que estar no diretorio que for rodada (mas aqui ele ativa o ambiente virtual.. não vira)
# Diretório do projeto
# $projectDir = "H:\Meu Drive\ProjetosPython\Loterias\Conferidores\MegaSenaConferidor"


# Definir o diretório do projeto (Isto faz criar uma pasta com este nome)
# $projectDir = Join-Path -Path $PSScriptRoot -ChildPath "MegaSenaConferidor"

# Criar a estrutura de diretórios
Write-Host "Criando a estrutura de diretórios do projeto..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $projectDir -Force
New-Item -ItemType Directory -Path "$projectDir\static\css" -Force
New-Item -ItemType Directory -Path "$projectDir\static\js" -Force
New-Item -ItemType Directory -Path "$projectDir\templates" -Force

# Criar os arquivos principais
Write-Host "Criando arquivos iniciais do projeto..." -ForegroundColor Cyan
New-Item -ItemType File -Path "$projectDir\requirements.txt" -Force
New-Item -ItemType File -Path "$projectDir\setup.ps1" -Force
New-Item -ItemType File -Path "$projectDir\app.py" -Force
New-Item -ItemType File -Path "$projectDir\static\css\style.css" -Force
New-Item -ItemType File -Path "$projectDir\static\js\main.js" -Force
New-Item -ItemType File -Path "$projectDir\templates\index.html" -Force

# Criando o ambiente virtual
Write-Host "Criando o ambiente virtual..." -ForegroundColor Cyan
python -m venv "$projectDir\venv"

# Verificando se o ambiente virtual foi criado
if (-Not (Test-Path "$projectDir\venv")) {
    Write-Host "Falha ao criar o ambiente virtual. Verifique se o Python está instalado e configurado corretamente." -ForegroundColor Red
    exit
}

Write-Host "Ambiente virtual criado com sucesso." -ForegroundColor Green

# Carregando o perfil do PowerShell
if (Test-Path $PROFILE) {
    Write-Host "Carregando o perfil do PowerShell..." -ForegroundColor Green
    . $PROFILE
} else {
    Write-Host "O arquivo de perfil do PowerShell não foi encontrado." -ForegroundColor Yellow
}

# Ativando o ambiente virtual diretamente
$activateScript = Join-Path "$projectDir\venv\Scripts" "Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Ativando o ambiente virtual..." -ForegroundColor Green
    . $activateScript
} else {
    Write-Host "O script de ativação do ambiente virtual não foi encontrado." -ForegroundColor Red
    exit
}

# Informando o usuário para preencher o arquivo requirements.txt
Write-Host "O ambiente está pronto para configurar as dependências." -ForegroundColor Cyan
Write-Host "Edite o arquivo requirements.txt em: $projectDir\requirements.txt e insira as dependências necessárias." -ForegroundColor Yellow
Write-Host "Pressione qualquer tecla para continuar a instalação quando terminar de editar o arquivo requirements.txt..." -ForegroundColor Cyan
Pause

# Instalando as dependências do requirements.txt
if (Test-Path "$projectDir\requirements.txt") {
    Write-Host "Instalando dependências do requirements.txt..." -ForegroundColor Cyan
    pip install -r "$projectDir\requirements.txt"
    Write-Host "Dependências instaladas com sucesso." -ForegroundColor Green
    Write-Host "Insira os conteúdos nos arquivos gerados e comece a desenvolver seu projeto!" -ForegroundColor Cyan
} else {
    Write-Host "O arquivo requirements.txt não foi encontrado, ou está vazio." -ForegroundColor Red
}
