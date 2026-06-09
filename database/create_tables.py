from database.connection import connect, get_table_columns, using_mysql


def _schema_usuarios():
    if using_mysql():
        return """
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            login VARCHAR(120) UNIQUE NOT NULL,
            senha VARCHAR(255) NOT NULL,
            nivel VARCHAR(50),
            foto VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    return """
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        login TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT,
        foto TEXT
    )
    """


def _schema_itens():
    if using_mysql():
        return """
        CREATE TABLE IF NOT EXISTS itens (
            id_item INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            foto VARCHAR(255),
            caixa VARCHAR(120),
            localizacao VARCHAR(120),
            quantidade INT,
            quantidade_minima INT,
            quantidade_operacional INT DEFAULT 0,
            em_uso INT DEFAULT 0,
            em_manutencao INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    return """
    CREATE TABLE IF NOT EXISTS itens (
        id_item INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        foto TEXT,
        caixa TEXT,
        localizacao TEXT,
        quantidade INTEGER,
        quantidade_minima INTEGER,
        quantidade_operacional INTEGER DEFAULT 0,
        em_uso INTEGER DEFAULT 0,
        em_manutencao INTEGER DEFAULT 0
    )
    """


def _schema_movimentacoes():
    if using_mysql():
        return """
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id_movimentacao INT AUTO_INCREMENT PRIMARY KEY,
            id_item INT,
            id_usuario INT,
            tipo VARCHAR(20),
            quantidade INT,
            observacao TEXT,
            data DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(id_item) REFERENCES itens(id_item) ON DELETE CASCADE,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    return """
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
    """


def _definicoes_colunas_operacionais():
    tipo_inteiro = "INT" if using_mysql() else "INTEGER"
    return [
        ("quantidade_operacional", f"{tipo_inteiro} DEFAULT 0"),
        ("em_uso", f"{tipo_inteiro} DEFAULT 0"),
        ("em_manutencao", f"{tipo_inteiro} DEFAULT 0"),
    ]


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(_schema_usuarios())
    cursor.execute(_schema_itens())
    cursor.execute(_schema_movimentacoes())
    conn.commit()
    conn.close()

    colunas = {coluna.lower() for coluna in get_table_columns("itens")}
    conn = connect()
    cursor = conn.cursor()

    for nome_coluna, definicao in _definicoes_colunas_operacionais():
        if nome_coluna.lower() not in colunas:
            cursor.execute(f"ALTER TABLE itens ADD COLUMN {nome_coluna} {definicao}")
            print(f"Coluna '{nome_coluna}' adicionada com sucesso.")

    conn.commit()
    conn.close()
    print("Tabelas criadas/atualizadas com sucesso.")


if __name__ == "__main__":
    create_tables()
