import sqlite3
from database.connection import connect

def autenticar_usuario(login, senha):
    conn = connect()
    cursor = conn.cursor()
    
    # Busca o usuário no banco
    cursor.execute("SELECT * FROM usuarios WHERE login = ? AND senha = ?", (login, senha))
    usuario = cursor.fetchone()
    
    conn.close()
    
    # Retorna os dados do usuário se encontrou, ou None se errou a senha
    return dict(usuario) if usuario else None

def criar_usuario_padrao():
    conn = connect()
    cursor = conn.cursor()
    
    # Verifica se a tabela está vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (nome, login, senha, nivel) 
            VALUES ('Administrador', 'admin', 'admin', 'admin')
        """)
        conn.commit()
        print("Usuário padrão criado: login 'admin', senha 'admin'")
        
    conn.close()

def registrar_usuario(nome, login, senha, nivel="usuario"):
    conn = connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, login, senha, nivel) 
            VALUES (?, ?, ?, ?)
        """, (nome, login, senha, nivel))
        conn.commit()
        sucesso = True
        mensagem = "Conta criada com sucesso!"
    except sqlite3.IntegrityError:
        sucesso = False
        mensagem = "Esse nome de usuário (login) já está em uso. Escolha outro."
    except Exception as e:
        sucesso = False
        mensagem = f"Erro ao criar usuário: {e}"
    finally:
        conn.close()
        
    return sucesso, mensagem

def obter_usuario_por_id(usuario_id):
    conn = connect()
    cursor = conn.cursor()
    # Adicionada a seleção da foto
    cursor.execute("SELECT nome, login, foto FROM usuarios WHERE id_usuario = ?", (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        return {"nome": usuario[0], "login": usuario[1], "foto": usuario[2]}
    return None

def atualizar_dados_usuario(usuario_id, nome, login, foto=None):
    conn = connect()
    cursor = conn.cursor()
    try:
        # Atualiza nome, login e foto
        cursor.execute("UPDATE usuarios SET nome = ?, login = ?, foto = ? WHERE id_usuario = ?", (nome, login, foto, usuario_id))
        conn.commit()
        sucesso = True
        mensagem = "Dados atualizados com sucesso!"
    except sqlite3.IntegrityError:
        sucesso = False
        mensagem = "Esse login já está em uso."
    except Exception as e:
        sucesso = False
        mensagem = f"Erro ao atualizar os dados: {e}"
    finally:
        conn.close()
        
    # Retorna a tupla esperada pela profile_window
    return sucesso, mensagem

def atualizar_senha_usuario(usuario_id, nova_senha):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha = ? WHERE id_usuario = ?", (nova_senha, usuario_id))
    conn.commit()
    conn.close()

def excluir_usuario_db(usuario_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id_usuario = ?", (usuario_id,))
    conn.commit()
    conn.close()