import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QHBoxLayout, QFrame, QFileDialog, QGraphicsDropShadowEffect, QInputDialog
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QCursor, QPixmap, QColor, QPainter, QPainterPath
from services.usuario_service import (
    obter_usuario_por_id, atualizar_dados_usuario, 
    atualizar_senha_usuario, excluir_usuario_db, autenticar_usuario
)

class PerfilWidget(QWidget):
    def __init__(self, usuario_id, callback_logout):
        super().__init__()
        self.usuario_id = usuario_id
        self.callback_logout = callback_logout
        self.login_atual = "" 
        self.caminho_foto_atual = None
        self.caminho_foto_nova = None
        
        self.setStyleSheet("background-color: #F3EFE0;")

        layout_principal = QVBoxLayout(self)
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # ==========================================
        # CARD PRINCIPAL
        # ==========================================
        self.card = QFrame()
        self.card.setFixedWidth(750)
        self.card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #DCDCDC;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.card.setGraphicsEffect(shadow)
        
        layout_card = QVBoxLayout(self.card)
        layout_card.setContentsMargins(40, 40, 40, 30)

        # ==========================================
        # CONTEÚDO DIVIDIDO EM DUAS COLUNAS
        # ==========================================
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # --- COLUNA DA FOTO (ESQUERDA) ---
        layout_foto = QVBoxLayout()
        layout_foto.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout_foto.setSpacing(0) # Espaçamento zero para controle manual

        # Título agora centralizado em relação à foto
        titulo = QLabel("Meu Perfil")
        titulo.setStyleSheet("font-size: 32px; font-weight: bold; color: #1F2937; border: none; background: transparent;")
        layout_foto.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_foto.addSpacing(15) 
        
        self.tamanho_foto = 180 
        self.lbl_foto = QLabel()
        self.lbl_foto.setFixedSize(self.tamanho_foto, self.tamanho_foto)
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.estilo_foto_padrao = f"""
            QLabel {{
                background-color: #F8FAFC; 
                border-radius: {self.tamanho_foto // 2}px; 
                border: 3px solid #E2E8F0;
            }}
        """
        self.estilo_foto_edicao = f"""
            QLabel {{
                background-color: #F8FAFC;
                border-radius: {self.tamanho_foto // 2}px; 
                border: 4px solid #3B82F6;
            }}
        """
        self.lbl_foto.setStyleSheet(self.estilo_foto_padrao)

        self.btn_alterar_foto = QPushButton("Alterar Foto")
        self.btn_alterar_foto.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_alterar_foto.setStyleSheet("""
            QPushButton { 
                background: transparent; color: #3B82F6; 
                font-size: 14px; font-weight: bold; text-decoration: underline;
                border: none; padding: 0px; margin: 0px;
            }
            QPushButton:hover { color: #2953EB; }
        """)
        self.btn_alterar_foto.clicked.connect(self.selecionar_foto)

        layout_foto.addWidget(self.lbl_foto, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_foto.addSpacing(8) # Deixa o alterar foto coladinho na imagem
        layout_foto.addWidget(self.btn_alterar_foto, alignment=Qt.AlignmentFlag.AlignCenter)
        
        content_layout.addLayout(layout_foto)

        # --- COLUNA DE DADOS (DIREITA) ---
        layout_dados = QVBoxLayout()
        layout_dados.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_dados.setSpacing(0) # Zera para manter títulos colados aos inputs
        
        # Botão Editar Informações no topo direito
        header_direita = QHBoxLayout()
        header_direita.addStretch()
        
        self.btn_editar = QPushButton("Editar Informações")
        self.btn_editar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_editar.setMinimumHeight(40)
        self.btn_editar.setStyleSheet("""
            QPushButton { background-color: #334155; color: white; font-weight: bold; border-radius: 8px; padding: 8px 15px; border: none; font-size: 13px;}
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_editar.clicked.connect(lambda: self.alternar_modo_edicao(True))
        header_direita.addWidget(self.btn_editar)
        
        layout_dados.addLayout(header_direita)
        layout_dados.addSpacing(15)

        self.estilo_readonly = """
            QLineEdit {
                padding: 0px 5px 8px 0px; border: none; border-bottom: 2px solid #E5E7EB;
                background-color: transparent; font-size: 18px; color: #1F2937; font-weight: bold;
            }
        """
        self.estilo_edit = """
            QLineEdit {
                padding: 10px; border: 2px solid #3B82F6; border-radius: 6px;
                background-color: #FFFFFF; font-size: 16px; color: #1e293b; margin-top: 4px;
            }
        """

        lbl_nome = QLabel("NOME") 
        lbl_nome.setStyleSheet("font-size: 12px; font-weight: bold; color: #3B82F6; border: none; background: transparent;")
        self.input_nome = QLineEdit()
        self.input_nome.setReadOnly(True)
        self.input_nome.setStyleSheet(self.estilo_readonly)
        
        lbl_login = QLabel("USUÁRIO (LOGIN)")
        lbl_login.setStyleSheet("font-size: 12px; font-weight: bold; color: #3B82F6; border: none; background: transparent;")
        self.input_login = QLineEdit()
        self.input_login.setReadOnly(True)
        self.input_login.setStyleSheet(self.estilo_readonly)

    
        layout_dados.addWidget(lbl_nome)
        layout_dados.addSpacing(2)
        layout_dados.addWidget(self.input_nome)
        layout_dados.addSpacing(25) 
        layout_dados.addWidget(lbl_login)
        layout_dados.addSpacing(2)
        layout_dados.addWidget(self.input_login)
        layout_dados.addSpacing(30)

        # Botões de edição (Salvar/Cancelar)
        self.layout_botoes_edicao = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancelar.setMinimumHeight(40)
        self.btn_cancelar.setStyleSheet("QPushButton { background-color: #f14044; color: #ffffff; font-weight: bold; border-radius: 8px; border: 1px solid #DCDCDC; font-size: 13px;} QPushButton:hover { background-color: #E2E8F0; }")
        self.btn_cancelar.clicked.connect(self.cancelar_edicao)
        self.btn_cancelar.hide()

        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_salvar.setMinimumHeight(40)
        self.btn_salvar.setStyleSheet("QPushButton { background-color: #10B981; color: white; font-weight: bold; border-radius: 8px; border: none; font-size: 13px;} QPushButton:hover { background-color: #059669; }")
        self.btn_salvar.clicked.connect(self.salvar_perfil)
        self.btn_salvar.hide()

        self.layout_botoes_edicao.addWidget(self.btn_cancelar)
        self.layout_botoes_edicao.addWidget(self.btn_salvar)
        layout_dados.addLayout(self.layout_botoes_edicao)

        # Alterar senha posicionado abaixo
        self.btn_alterar_senha = QPushButton("Alterar Senha")
        self.btn_alterar_senha.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_alterar_senha.setMinimumHeight(40)
        self.btn_alterar_senha.setFixedWidth(160)
        self.btn_alterar_senha.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #3B82F6; font-weight: bold; border-radius: 8px; padding: 10px; border: 1px solid #3B82F6; font-size: 13px;}
            QPushButton:hover { background-color: #e0e6FF; }
        """)
        self.btn_alterar_senha.clicked.connect(self.alterar_senha)
        
        layout_dados.addSpacing(10)
        layout_dados.addWidget(self.btn_alterar_senha)

        content_layout.addLayout(layout_dados)
        layout_card.addLayout(content_layout)

        # --- RODAPÉ ---
        layout_card.addSpacing(15)
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.btn_excluir = QPushButton("Excluir Minha Conta")
        self.btn_excluir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_excluir.setStyleSheet("""
            QPushButton { background-color: transparent; color: #9CA3AF; text-decoration: underline; font-weight: bold; padding: 5px; border: none; font-size: 12px;}
            QPushButton:hover { color: #EF4444; }
        """)
        self.btn_excluir.clicked.connect(self.excluir_conta)
        footer_layout.addWidget(self.btn_excluir)
        
        layout_card.addLayout(footer_layout)

        layout_principal.addWidget(self.card)
        self.carregar_dados()

    def set_placeholder_foto(self):
        self.lbl_foto.setText("") 
        self.lbl_foto.setPixmap(QPixmap())

    def exibir_foto(self, caminho_foto):
        if caminho_foto and os.path.exists(caminho_foto):
            pixmap = QPixmap(caminho_foto)
            if not pixmap.isNull():
                tamanho = self.tamanho_foto
                margem = 4
                tamanho_interno = tamanho - (margem * 2)

                min_dim = min(pixmap.width(), pixmap.height())
                x_offset = (pixmap.width() - min_dim) // 2
                y_offset = (pixmap.height() - min_dim) // 2
                pixmap_quadrado = pixmap.copy(QRect(x_offset, y_offset, min_dim, min_dim))
                
                pixmap_redimensionado = pixmap_quadrado.scaled(
                    tamanho_interno, tamanho_interno, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                target = QPixmap(tamanho, tamanho)
                target.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(target)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                
                path = QPainterPath()
                path.addEllipse(margem, margem, tamanho_interno, tamanho_interno)
                painter.setClipPath(path)
                
                painter.drawPixmap(margem, margem, pixmap_redimensionado)
                painter.end()
                
                self.lbl_foto.setPixmap(target)
                self.lbl_foto.setText("") 
                return
        self.set_placeholder_foto()

    def selecionar_foto(self):
        file_dialog = QFileDialog()
        caminho_arquivo, _ = file_dialog.getOpenFileName(
            self, "Selecionar Foto de Perfil", "", 
            "Imagens (*.png *.jpg *.jpeg)"
        )
        
        if caminho_arquivo:
            self.caminho_foto_nova = caminho_arquivo
            self.exibir_foto(caminho_arquivo)
            if self.input_nome.isReadOnly():
                self.alternar_modo_edicao(True)

    def carregar_dados(self):
        usuario = obter_usuario_por_id(self.usuario_id)
        if usuario:
            self.input_nome.setText(usuario['nome'])
            self.input_login.setText(usuario['login'])
            self.login_atual = usuario['login']
            self.caminho_foto_atual = usuario.get('foto') 
            self.caminho_foto_nova = None
            self.exibir_foto(self.caminho_foto_atual)
            if not self.caminho_foto_atual:
                self.set_placeholder_foto()

    def alternar_modo_edicao(self, ativado):
        self.input_nome.setReadOnly(not ativado)
        self.input_login.setReadOnly(not ativado)
        
        if ativado:
            self.input_nome.setStyleSheet(self.estilo_edit)
            self.input_login.setStyleSheet(self.estilo_edit)
            self.lbl_foto.setStyleSheet(self.estilo_foto_edicao)
            self.btn_editar.hide()
            self.btn_cancelar.show()
            self.btn_salvar.show()
            self.input_nome.setFocus()
        else:
            self.input_nome.setStyleSheet(self.estilo_readonly)
            self.input_login.setStyleSheet(self.estilo_readonly)
            self.lbl_foto.setStyleSheet(self.estilo_foto_padrao)
            self.btn_cancelar.hide()
            self.btn_salvar.hide()
            self.btn_editar.show()

    def cancelar_edicao(self):
        self.carregar_dados() 
        self.alternar_modo_edicao(False)

    def salvar_perfil(self):
        novo_nome = self.input_nome.text().strip()
        novo_login = self.input_login.text().strip()

        if not novo_nome or not novo_login:
            QMessageBox.warning(self, "Aviso", "Os campos não podem ficar vazios!")
            return

        foto_para_salvar = self.caminho_foto_nova if self.caminho_foto_nova else self.caminho_foto_atual
        sucesso, mensagem = atualizar_dados_usuario(self.usuario_id, novo_nome, novo_login, foto_para_salvar)
        
        if sucesso:
            QMessageBox.information(self, "Sucesso", mensagem)
            self.login_atual = novo_login
            self.caminho_foto_atual = foto_para_salvar
            self.caminho_foto_nova = None
            self.alternar_modo_edicao(False)
        else:
            QMessageBox.warning(self, "Erro", mensagem)

    def alterar_senha(self):
        senha_antiga, ok = QInputDialog.getText(
            self, "Segurança", "Para continuar, digite sua senha atual:", 
            QLineEdit.EchoMode.Password
        )
        
        if not ok or not senha_antiga:
            return 
            
        if not autenticar_usuario(self.login_atual, senha_antiga):
            QMessageBox.critical(self, "Erro", "A senha atual está incorreta!")
            return

        nova_senha, ok_nova = QInputDialog.getText(
            self, "Nova Senha", "Digite sua nova senha:", 
            QLineEdit.EchoMode.Password
        )
        
        if ok_nova and nova_senha:
            confirmar_senha, ok_conf = QInputDialog.getText(
                self, "Confirmação", "Digite a nova senha novamente para confirmar:", 
                QLineEdit.EchoMode.Password
            )
            
            if ok_conf and nova_senha == confirmar_senha:
                atualizar_senha_usuario(self.usuario_id, nova_senha)
                QMessageBox.information(self, "Sucesso", "Sua senha foi alterada com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", "As senhas não coincidem. Tente novamente.")

    def excluir_conta(self):
        resposta = QMessageBox.question(
            self, "Excluir Conta", 
            "Tem certeza que deseja excluir sua conta?\nTodos os seus acessos serão perdidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            excluir_usuario_db(self.usuario_id)
            QMessageBox.warning(self, "Conta Excluída", "Sua conta foi excluída.")
            self.callback_logout()