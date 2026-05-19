from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QGuiApplication # <-- Adicionado QGuiApplication
from services.usuario_service import registrar_usuario

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nova Conta - Estoque TI")
        self.setFixedSize(550, 650) 
        
        # --- CENTRALIZAÇÃO COM OFFSET ---
        self.centralizar_direita()

        self.setStyleSheet("""
            LoginWindow, RegisterWindow { 
                background-color: #1E293B; 
            }
            QMessageBox {
                background-color: #F3F4F6;
            }
            QMessageBox QLabel {
                color: #1F2937;
                background: transparent;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #1F2937;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                min-width: 80px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #374151;
            }
        """) 

        layout_principal = QVBoxLayout()
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.setContentsMargins(40, 40, 40, 40)

        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color: #e8e0cc; /* Bege original mantido */
                border-radius: 20px;
                border: 1px solid #d1c9b8;
            }
            QLabel { 
                border: none; 
                color: #1F2937; 
                font-weight: bold;
                background: transparent;
            }
        """)

        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(30)
        sombra.setXOffset(-10)
        sombra.setYOffset(20)
        sombra.setColor(QColor(0, 0, 0, 160))
        self.card.setGraphicsEffect(sombra)

        layout_card = QVBoxLayout(self.card)
        layout_card.setSpacing(12)
        layout_card.setContentsMargins(30, 35, 30, 35)

        titulo = QLabel("CADASTRO DE USUÁRIO")
        titulo.setStyleSheet("font-size: 20px; margin-bottom: 15px; color: #1F2937; background: transparent;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_card.addWidget(titulo)

        layout_card.addWidget(QLabel("Nome e Sobrenome:"))
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: João Pedro")
        self.input_nome.setStyleSheet(self.estilo_input())
        layout_card.addWidget(self.input_nome)

        layout_card.addWidget(QLabel("Nome de Usuário (Login):"))
        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Como irá entrar no sistema...")
        self.input_login.setStyleSheet(self.estilo_input())
        layout_card.addWidget(self.input_login)

        layout_card.addWidget(QLabel("Senha:"))
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Crie uma senha forte")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_senha.setStyleSheet(self.estilo_input())
        layout_card.addWidget(self.input_senha)

        layout_card.addWidget(QLabel("Confirme a Senha:"))
        self.input_confirma_senha = QLineEdit()
        self.input_confirma_senha.setPlaceholderText("Repita a senha")
        self.input_confirma_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirma_senha.setStyleSheet(self.estilo_input())
        layout_card.addWidget(self.input_confirma_senha)

        self.btn_cadastrar = QPushButton("FINALIZAR CADASTRO")
        self.btn_cadastrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cadastrar.setMinimumHeight(55) 
        self.btn_cadastrar.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 20px;
                border: none;
            }
            QPushButton:hover { background-color: #334155; }
            QPushButton:pressed { background-color: #0F172A; }
        """)
        self.btn_cadastrar.clicked.connect(self.salvar_cadastro)
        layout_card.addWidget(self.btn_cadastrar)

        layout_principal.addWidget(self.card)
        self.setLayout(layout_principal)

    def centralizar_direita(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        nova_pos = qr.topLeft()
        self.move(nova_pos.x() + 50, nova_pos.y()) 

    def estilo_input(self):
        return """
            QLineEdit {
                padding: 10px;
                border: 1px solid #d1c9b8;
                border-radius: 8px;
                background: white;
                color: #333;
                font-size: 13px;
            }
        """

    def salvar_cadastro(self):
        nome = self.input_nome.text().strip()
        login = self.input_login.text().strip()
        senha = self.input_senha.text()
        confirma = self.input_confirma_senha.text()

        if not nome or not login or not senha:
            QMessageBox.warning(self, "Atenção", "Por favor, preencha todos os campos obrigatórios!")
            return
            
        if senha != confirma:
            QMessageBox.warning(self, "Atenção", "As senhas digitadas não coincidem!")
            return

        sucesso, mensagem = registrar_usuario(nome, login, senha)

        if sucesso:
            QMessageBox.information(self, "Sucesso", "Conta criada com sucesso! Agora você já pode fazer login.")
            self.close() 
        else:
            QMessageBox.critical(self, "Erro", mensagem)