import os
import shutil
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout, QFrame, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QCursor, QPixmap, QPainter, QPainterPath

from services.usuario_service import (
    obter_usuario_por_id, atualizar_dados_usuario,
    atualizar_senha_usuario, excluir_usuario_db, autenticar_usuario
)
from ui.theme import apply_shadow, button_style, card_style, header_banner_style, input_style, palette


class PerfilWidget(QWidget):
    def __init__(self, usuario_id, callback_logout):
        super().__init__()
        self.usuario_id = usuario_id
        self.callback_logout = callback_logout
        self.login_atual = ""
        self.caminho_foto_atual = ""
        self.caminho_foto_nova = ""
        self.dark_mode = False
        self.app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.pasta_perfis = os.path.join(self.app_root, "fotos", "perfis")

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_principal.setContentsMargins(30, 24, 30, 30)
        self.layout_principal.setSpacing(18)

        self.layout_principal.addWidget(self.criar_cabecalho())
        self.layout_principal.addWidget(self.criar_card_perfil())

        self.carregar_dados()
        self.aplicar_tema(False)

    def criar_cabecalho(self):
        self.header = QFrame()
        self.header.setObjectName("headerPerfil")
        layout = QVBoxLayout(self.header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)

        self.lbl_header_titulo = QLabel("Meu Perfil")
        self.lbl_header_titulo.setObjectName("headerTitulo")
        self.lbl_header_subtitulo = QLabel(
            "Atualize seus dados de acesso, foto e senha com segurança."
        )
        self.lbl_header_subtitulo.setObjectName("headerSubtitulo")
        self.lbl_header_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_header_titulo)
        layout.addWidget(self.lbl_header_subtitulo)
        apply_shadow(self.header)
        return self.header

    def criar_card_perfil(self):
        self.card = QFrame()
        self.card.setObjectName("cardPerfil")
        layout_card = QHBoxLayout(self.card)
        layout_card.setContentsMargins(28, 28, 28, 28)
        layout_card.setSpacing(28)

        coluna_foto = QVBoxLayout()
        coluna_foto.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        coluna_foto.setSpacing(10)

        self.tamanho_foto = 180
        self.lbl_foto = QLabel("SEM FOTO")
        self.lbl_foto.setFixedSize(self.tamanho_foto, self.tamanho_foto)
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_alterar_foto = QPushButton("Alterar foto")
        self.btn_alterar_foto.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_alterar_foto.clicked.connect(self.selecionar_foto)

        coluna_foto.addWidget(self.lbl_foto, alignment=Qt.AlignmentFlag.AlignCenter)
        coluna_foto.addWidget(self.btn_alterar_foto, alignment=Qt.AlignmentFlag.AlignCenter)

        coluna_dados = QVBoxLayout()
        coluna_dados.setAlignment(Qt.AlignmentFlag.AlignTop)
        coluna_dados.setSpacing(12)

        topo_dados = QHBoxLayout()
        self.lbl_titulo_dados = QLabel("Dados da conta")
        self.lbl_titulo_dados.setObjectName("tituloSecao")
        topo_dados.addWidget(self.lbl_titulo_dados)
        topo_dados.addStretch()

        self.btn_editar = QPushButton("Editar informações")
        self.btn_editar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_editar.clicked.connect(lambda: self.alternar_modo_edicao(True))
        topo_dados.addWidget(self.btn_editar)
        coluna_dados.addLayout(topo_dados)

        self.lbl_nome = QLabel("Nome")
        self.input_nome = QLineEdit()
        self.input_nome.setReadOnly(True)

        self.lbl_login = QLabel("Usuário")
        self.input_login = QLineEdit()
        self.input_login.setReadOnly(True)

        coluna_dados.addWidget(self.lbl_nome)
        coluna_dados.addWidget(self.input_nome)
        coluna_dados.addWidget(self.lbl_login)
        coluna_dados.addWidget(self.input_login)

        self.layout_botoes_edicao = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancelar.clicked.connect(self.cancelar_edicao)
        self.btn_cancelar.hide()

        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_salvar.clicked.connect(self.salvar_perfil)
        self.btn_salvar.hide()

        self.layout_botoes_edicao.addWidget(self.btn_cancelar)
        self.layout_botoes_edicao.addWidget(self.btn_salvar)
        coluna_dados.addLayout(self.layout_botoes_edicao)

        self.btn_alterar_senha = QPushButton("Alterar senha")
        self.btn_alterar_senha.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_alterar_senha.clicked.connect(self.alterar_senha)
        coluna_dados.addWidget(self.btn_alterar_senha, alignment=Qt.AlignmentFlag.AlignLeft)
        coluna_dados.addStretch()

        self.btn_excluir = QPushButton("Excluir minha conta")
        self.btn_excluir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_excluir.clicked.connect(self.excluir_conta)
        coluna_dados.addWidget(self.btn_excluir, alignment=Qt.AlignmentFlag.AlignRight)

        layout_card.addLayout(coluna_foto)
        layout_card.addLayout(coluna_dados, stretch=1)
        apply_shadow(self.card)
        return self.card

    def aplicar_tema(self, dark=False):
        self.dark_mode = dark
        p = palette(dark)
        self.setStyleSheet(f"background-color: {p['bg']}; color: {p['text']};")
        self.header.setStyleSheet(header_banner_style("headerPerfil", dark))
        self.card.setStyleSheet(card_style(dark))
        self.lbl_foto.setStyleSheet(f"""
            QLabel {{
                background-color: {p['card_alt']};
                color: {p['muted']};
                border-radius: {self.tamanho_foto // 2}px;
                border: 3px solid {p['border']};
                font-weight: 800;
            }}
        """)
        for label in [self.lbl_titulo_dados, self.lbl_nome, self.lbl_login]:
            label.setStyleSheet(f"color: {p['text']}; font-weight: 800; border: none; background: transparent;")
        self.input_nome.setStyleSheet(input_style(dark))
        self.input_login.setStyleSheet(input_style(dark))
        self.btn_alterar_foto.setStyleSheet(button_style("ghost", dark))
        self.btn_editar.setStyleSheet(button_style("dark", dark))
        self.btn_cancelar.setStyleSheet(button_style("muted", dark))
        self.btn_salvar.setStyleSheet(button_style("success", dark))
        self.btn_alterar_senha.setStyleSheet(button_style("primary", dark))
        self.btn_excluir.setStyleSheet(button_style("danger", dark))
        apply_shadow(self.header, dark, blur=18)
        apply_shadow(self.card, dark, blur=18)

    def resolver_caminho_foto(self, caminho_foto):
        if not caminho_foto:
            return ""
        if os.path.isabs(caminho_foto) and os.path.exists(caminho_foto):
            return caminho_foto
        relativo_app = os.path.join(self.app_root, caminho_foto)
        if os.path.exists(relativo_app):
            return relativo_app
        return ""

    def set_placeholder_foto(self):
        self.lbl_foto.setText("SEM FOTO")
        self.lbl_foto.setPixmap(QPixmap())

    def exibir_foto(self, caminho_foto):
        caminho_real = self.resolver_caminho_foto(caminho_foto)
        if not caminho_real:
            self.set_placeholder_foto()
            return

        pixmap = QPixmap(caminho_real)
        if pixmap.isNull():
            self.set_placeholder_foto()
            return

        tamanho = self.tamanho_foto
        margem = 5
        tamanho_interno = tamanho - margem * 2

        min_dim = min(pixmap.width(), pixmap.height())
        x_offset = (pixmap.width() - min_dim) // 2
        y_offset = (pixmap.height() - min_dim) // 2
        pixmap_quadrado = pixmap.copy(QRect(x_offset, y_offset, min_dim, min_dim))
        pixmap_redimensionado = pixmap_quadrado.scaled(
            tamanho_interno,
            tamanho_interno,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
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

    def selecionar_foto(self):
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Foto de Perfil",
            "",
            "Imagens (*.png *.jpg *.jpeg)",
        )

        if caminho_arquivo:
            self.caminho_foto_nova = caminho_arquivo
            self.exibir_foto(caminho_arquivo)
            if self.input_nome.isReadOnly():
                self.alternar_modo_edicao(True)

    def copiar_foto_perfil(self, caminho_origem):
        if not caminho_origem:
            return self.caminho_foto_atual

        try:
            os.makedirs(self.pasta_perfis, exist_ok=True)
            ext = os.path.splitext(caminho_origem)[1]
            nome_arquivo = f"{uuid.uuid4().hex}{ext}"
            destino = os.path.join(self.pasta_perfis, nome_arquivo)
            shutil.copy(caminho_origem, destino)
            return os.path.relpath(destino, self.app_root).replace("\\", "/")
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Não foi possível salvar a foto: {exc}")
            return self.caminho_foto_atual

    def carregar_dados(self):
        usuario = obter_usuario_por_id(self.usuario_id)
        if not usuario:
            return

        self.input_nome.setText(usuario["nome"])
        self.input_login.setText(usuario["login"])
        self.login_atual = usuario["login"]
        self.caminho_foto_atual = usuario.get("foto") or ""
        self.caminho_foto_nova = ""
        self.exibir_foto(self.caminho_foto_atual)

    def alternar_modo_edicao(self, ativado):
        self.input_nome.setReadOnly(not ativado)
        self.input_login.setReadOnly(not ativado)
        self.btn_editar.setVisible(not ativado)
        self.btn_cancelar.setVisible(ativado)
        self.btn_salvar.setVisible(ativado)
        if ativado:
            self.input_nome.setFocus()

    def cancelar_edicao(self):
        self.carregar_dados()
        self.alternar_modo_edicao(False)

    def salvar_perfil(self):
        novo_nome = self.input_nome.text().strip()
        novo_login = self.input_login.text().strip()

        if not novo_nome or not novo_login:
            QMessageBox.warning(self, "Aviso", "Os campos não podem ficar vazios!")
            return

        foto_para_salvar = self.copiar_foto_perfil(self.caminho_foto_nova) if self.caminho_foto_nova else self.caminho_foto_atual
        sucesso, mensagem = atualizar_dados_usuario(self.usuario_id, novo_nome, novo_login, foto_para_salvar)

        if sucesso:
            QMessageBox.information(self, "Sucesso", mensagem)
            self.login_atual = novo_login
            self.caminho_foto_atual = foto_para_salvar
            self.caminho_foto_nova = ""
            self.alternar_modo_edicao(False)
            self.exibir_foto(self.caminho_foto_atual)
        else:
            QMessageBox.warning(self, "Erro", mensagem)

    def alterar_senha(self):
        senha_antiga, ok = QInputDialog.getText(
            self,
            "Segurança",
            "Para continuar, digite sua senha atual:",
            QLineEdit.EchoMode.Password,
        )

        if not ok or not senha_antiga:
            return

        if not autenticar_usuario(self.login_atual, senha_antiga):
            QMessageBox.critical(self, "Erro", "A senha atual está incorreta!")
            return

        nova_senha, ok_nova = QInputDialog.getText(
            self,
            "Nova Senha",
            "Digite sua nova senha:",
            QLineEdit.EchoMode.Password,
        )

        if not ok_nova or not nova_senha:
            return

        confirmar_senha, ok_conf = QInputDialog.getText(
            self,
            "Confirmação",
            "Digite a nova senha novamente para confirmar:",
            QLineEdit.EchoMode.Password,
        )

        if ok_conf and nova_senha == confirmar_senha:
            atualizar_senha_usuario(self.usuario_id, nova_senha)
            QMessageBox.information(self, "Sucesso", "Sua senha foi alterada com sucesso!")
        else:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem. Tente novamente.")

    def excluir_conta(self):
        resposta = QMessageBox.question(
            self,
            "Excluir Conta",
            "Tem certeza que deseja excluir sua conta?\nTodos os seus acessos serão perdidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            excluir_usuario_db(self.usuario_id)
            QMessageBox.warning(self, "Conta Excluída", "Sua conta foi excluída.")
            self.callback_logout()
