# Inicia o sistema usando MySQL.
# Ajuste MYSQL_USER e MYSQL_PASSWORD conforme sua instalacao local.

$env:DB_BACKEND = "mysql"
$env:MYSQL_HOST = "localhost"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = 'TI@Mu$eu%'
$env:MYSQL_DATABASE = "estoque"
$env:MYSQL_AUTO_CREATE_DATABASE = "1"

Set-Location $PSScriptRoot
& ".\venv\Scripts\python.exe" main.py
