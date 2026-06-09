# MySQL

Por padrao o sistema continua usando `database.db` com SQLite.

Para testar com MySQL, instale a dependencia e defina as variaveis de ambiente antes de iniciar o app.
Se o `venv` nao estiver ativado, use `.\venv\Scripts\pip.exe` e `.\venv\Scripts\python.exe`
no lugar de `pip` e `python`.

```powershell
pip install PyMySQL
$env:DB_BACKEND = "mysql"
$env:MYSQL_HOST = "localhost"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = 'sua_senha'
$env:MYSQL_DATABASE = "estoque"
python main.py
```

No PowerShell, use aspas simples na senha se ela tiver caracteres como `$`, por exemplo:

```powershell
$env:MYSQL_PASSWORD = 'TI@Mu$eu%'
```

Se quiser que o sistema tente criar o banco automaticamente quando ele ainda nao existir:

```powershell
$env:MYSQL_AUTO_CREATE_DATABASE = "1"
```

Para copiar os dados atuais do SQLite para o MySQL configurado:

```powershell
python -m database.migrate_sqlite_to_mysql
```

O migrador usa `INSERT IGNORE`, entao registros que ja existirem no MySQL nao sao duplicados.
