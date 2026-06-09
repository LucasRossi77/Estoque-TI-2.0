from database.connection import connect


def listar_itens():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM itens")
    itens = cursor.fetchall()
    conn.close()
    return itens


def adicionar_item(nome, caixa, localizacao, quantidade, quantidade_minima, foto):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO itens (nome, caixa, localizacao, quantidade, quantidade_minima, foto)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, caixa, localizacao, quantidade, quantidade_minima, foto))
    conn.commit()
    conn.close()


def atualizar_quantidade(item_id, nova_quantidade):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE itens
        SET quantidade = ?
        WHERE id_item = ?
    """, (nova_quantidade, item_id))
    conn.commit()
    conn.close()


def buscar_item_por_id(item_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM itens WHERE id_item = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return dict(item) if item else None


def atualizar_item(id_item, nome, caixa, localizacao, quantidade_minima, quantidade, foto):
    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE itens
            SET nome = ?,
                caixa = ?,
                localizacao = ?,
                quantidade_minima = ?,
                quantidade = ?,
                foto = ?
            WHERE id_item = ?
        """, (nome, caixa, localizacao, quantidade_minima, quantidade, foto, id_item))
        conn.commit()
    except Exception as exc:
        print(f"Erro ao atualizar item no banco: {exc}")
        raise
    finally:
        conn.close()


def excluir_item(item_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM itens WHERE id_item = ?", (item_id,))
    conn.commit()
    conn.close()
