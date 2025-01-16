# setup.ps1
$projectDir = $PSScriptRoot

# Criando o ambiente virtual
Write-Host "Criando o ambiente virtual..." -ForegroundColor Cyan
python -m venv "$projectDir\venv"

# Verificando se o ambiente virtual foi criado
if (-Not (Test-Path "$projectDir\venv")) {
    Write-Host "Falha ao criar o ambiente virtual. Verifique se o Python esta instalado e configurado corretamente." -ForegroundColor Red
    exit
}

Write-Host "Ambiente virtual criado com sucesso." -ForegroundColor Green

# Carregando o perfil do PowerShell
if (Test-Path $PROFILE) {
    Write-Host "Carregando o perfil do PowerShell..." -ForegroundColor Green
    . $PROFILE
} else {
    Write-Host "O arquivo de perfil do PowerShell nao foi encontrado." -ForegroundColor Yellow
}

# Ativando o ambiente virtual diretamente
$activateScript = Join-Path "$projectDir\venv\Scripts" "Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Ativando o ambiente virtual..." -ForegroundColor Green
    . $activateScript
} else {
    Write-Host "O script de ativacao do ambiente virtual não foi encontrado." -ForegroundColor Red
    exit
}

# Criando estrutura de diretórios
New-Item -ItemType Directory -Force -Path "$projectDir\static\css"
New-Item -ItemType Directory -Force -Path "$projectDir\static\js"
New-Item -ItemType Directory -Force -Path "$projectDir\templates"

# Instalando as dependências do requirements.txt
if (Test-Path "$projectDir\requirements.txt") {
    Write-Host "Instalando dependencias do requirements.txt..." -ForegroundColor Cyan
    pip install -r "$projectDir\requirements.txt"
    Write-Host "Dependencias instaladas com sucesso." -ForegroundColor Green
} else {
    Write-Host "O arquivo requirements.txt nao foi encontrado." -ForegroundColor Red
}