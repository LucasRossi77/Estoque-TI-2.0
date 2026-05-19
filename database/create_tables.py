from database.connection import connect

def create_tables():
    conn = connect()
    cursor = conn.cursor()

    # Tabela de Usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        login TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT,
        foto TEXT 
    )
    """)

    # Tabela de Itens (Atualizada com quantidade_operacional)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens (
        id_item INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        foto TEXT,
        caixa TEXT,
        localizacao TEXT,
        quantidade INTEGER,
        quantidade_minima INTEGER,
        quantidade_operacional INTEGER DEFAULT 0
    )
    """)

    # Lógica para atualizar bancos de dados já existentes
    # Isso evita que você tenha que apagar o arquivo .db para ver a mudança
    try:
        cursor.execute("ALTER TABLE itens ADD COLUMN quantidade_operacional INTEGER DEFAULT 0;")
        print("Coluna 'quantidade_operacional' adicionada com sucesso.")
    except:
        # Se a coluna já existir, o SQLite retornará um erro e o script apenas ignora
        pass

    # Tabela de Movimentações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
        id_item INTEGER,
        id_usuario INTEGER,
        tipo TEXT CHECK(tipo IN ('ENTRADA','SAIDA', 'TRANSFERENCIA')),
        quantidade INTEGER,
        observacao TEXT,
        data DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(id_item) REFERENCES itens(id_item),
        FOREIGN KEY(id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)

    conn.commit()
    conn.close()
    print("Tabelas criadas/atualizadas com sucesso.")

if __name__ == "__main__":
    create_tables()