# MySQL

Por padrao o sistema usa `database.db` (SQLite). Para usar MySQL, instale o **MySQL Server**
e inicie o app com `.\start-mysql.ps1` ou defina `DB_BACKEND=mysql`.

## Inicio rapido (Windows)

1. Instale e inicie o MySQL Server (porta 3306).
2. Instale as dependencias:

```powershell
.\venv\Scripts\pip.exe install -r requirements.txt
```

3. Ajuste a senha em `start-mysql.ps1` (variavel `MYSQL_PASSWORD`).
4. Crie as tabelas e migre os dados do SQLite, se necessario:

```powershell
.\start-mysql.ps1   # ou configure as variaveis abaixo manualmente

# Em outro terminal, com as mesmas variaveis MYSQL_*:
.\venv\Scripts\python.exe -m database.create_tables
.\venv\Scripts\python.exe -m database.migrate_sqlite_to_mysql
```

5. Inicie o app:

```powershell
.\start-mysql.ps1
```

## Variaveis de ambiente

```powershell
$env:DB_BACKEND = "mysql"
$env:MYSQL_HOST = "localhost"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = 'sua_senha'
$env:MYSQL_DATABASE = "estoque"
$env:MYSQL_AUTO_CREATE_DATABASE = "1"
.\venv\Scripts\python.exe main.py
```

No PowerShell, use aspas simples na senha se ela tiver caracteres como `$`, por exemplo:

```powershell
$env:MYSQL_PASSWORD = 'TI@Mu$eu%'
```

## Migrar dados do SQLite

Com as variaveis `MYSQL_*` configuradas:

```powershell
.\venv\Scripts\python.exe -m database.migrate_sqlite_to_mysql
```

O migrador usa `INSERT IGNORE`, entao registros que ja existirem no MySQL nao sao duplicados.

## Voltar ao SQLite (legado)

```powershell
$env:DB_BACKEND = "sqlite"
.\venv\Scripts\python.exe main.py
```

O arquivo `database.db` na raiz do projeto sera usado novamente.
