from database.connection import connect
from datetime import datetime

def registrar_movimentacao(item_id, tipo, quantidade, usuario_id=None, observacao=""):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO movimentacoes
        (id_item, tipo, quantidade, id_usuario, observacao, data) -- <-- CORREÇÃO
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        item_id,
        tipo,
        quantidade,
        usuario_id,
        observacao,
        datetime.now()
    ))
    conn.commit()
    conn.close()

def listar_historico():
    conn = connect()
    cursor = conn.cursor()
    # O JOIN busca o nome do item e o nome do usuário que fez a ação
    cursor.execute("""
        SELECT 
            m.data, 
            i.nome as item_nome, 
            m.tipo, 
            m.quantidade, 
            u.nome as usuario_nome, 
            m.observacao
        FROM movimentacoes m
        JOIN itens i ON m.id_item = i.id_item
        LEFT JOIN usuarios u ON m.id_usuario = u.id_usuario
        ORDER BY m.data DESC
    """)
    historico = cursor.fetchall()
    conn.close()
    return historico