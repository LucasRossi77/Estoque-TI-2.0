import os
import shutil
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QScrollArea,
    QSpinBox, QMessageBox, QFrame, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from services.item_service import buscar_item_por_id, atualizar_item
from ui.theme import (
    LOCALIZACOES_PADRAO, apply_shadow, button_style, card_style,
    header_banner_style, input_style, palette
)


class EditItemWidget(QWidget):
    def __init__(self, item_id, atualizar_tabela, voltar_callback):
        super().__init__()
        self.item_id = item_id
        self.atualizar_tabela = atualizar_tabela
        self.voltar_callback = voltar_callback
        self.dark_mode = False

        self.item_info = buscar_item_por_id(self.item_id)
        if not self.item_info:
            QMessageBox.critical(self, "Erro", "Item não encontrado!")
            self.voltar_callback()
            return

        self.foto_path = self.item_info.get("foto", "") or ""
        self.foto_nova = ""

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: transparent;")

        self.container = QWidget()
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(30, 24, 30, 30)
        self.layout_container.setSpacing(18)
        self.layout_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout_container.addWidget(self.criar_cabecalho())
        self.layout_container.addWidget(self.criar_card_formulario())

        self.scroll.setWidget(self.container)
        layout_principal.addWidget(self.scroll)
        self.aplicar_tema(False)
        self.exibir_foto(self.foto_path)

    def criar_cabecalho(self):
        self.header = QFrame()
        self.header.setObjectName("headerEdicao")
        layout = QVBoxLayout(self.header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)

        self.lbl_header_titulo = QLabel("Editar Item")
        self.lbl_header_titulo.setObjectName("headerTitulo")
        self.lbl_header_subtitulo = QLabel(
            "Atualize os dados do item mantendo o controle com o cálculo automático de estoque mínimo."
        )
        self.lbl_header_subtitulo.setObjectName("headerSubtitulo")
        self.lbl_header_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_header_titulo)
        layout.addWidget(self.lbl_header_subtitulo)
        apply_shadow(self.header)
        return self.header

    def criar_card_formulario(self):
        self.card = QFrame()
        self.card.setObjectName("cardEdicao")
        layout_card = QVBoxLayout(self.card)
        layout_card.setSpacing(18)
        layout_card.setContentsMargins(24, 22, 24, 24)

        secao_topo = QHBoxLayout()
        secao_topo.setSpacing(20)
        secao_topo.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.frame_foto = QFrame()
        self.frame_foto.setObjectName("frameFoto")
        self.frame_foto.setFixedSize(190, 190)
        layout_foto = QVBoxLayout(self.frame_foto)
        layout_foto.setContentsMargins(8, 8, 8, 8)

        self.lbl_foto = QLabel("SEM FOTO")
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto.setWordWrap(True)
        layout_foto.addWidget(self.lbl_foto)

        vbox_nome = QVBoxLayout()
        vbox_nome.setSpacing(8)
        self.lbl_nome = QLabel("Nome do item")
        self.nome = QLineEdit(str(self.item_info.get("nome", "")))

        self.btn_foto = QPushButton("Alterar imagem")
        self.btn_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_foto.clicked.connect(self.selecionar_foto)

        self.lbl_dica_minimo = QLabel(
            "O estoque mínimo operacional é calculado automaticamente como 10% da quantidade atual."
        )
        self.lbl_dica_minimo.setWordWrap(True)

        vbox_nome.addWidget(self.lbl_nome)
        vbox_nome.addWidget(self.nome)
        vbox_nome.addWidget(self.btn_foto)
        vbox_nome.addWidget(self.lbl_dica_minimo)
        vbox_nome.addStretch()

        secao_topo.addWidget(self.frame_foto)
        secao_topo.addLayout(vbox_nome)
        layout_card.addLayout(secao_topo)

        layout_form = QGridLayout()
        layout_form.setSpacing(14)

        self.caixa = QLineEdit(str(self.item_info.get("caixa", "") or ""))
        self.localizacao = QComboBox()
        self.localizacao.addItems(LOCALIZACOES_PADRAO)
        idx = self.localizacao.findText(str(self.item_info.get("localizacao", "") or ""))
        if idx >= 0:
            self.localizacao.setCurrentIndex(idx)

        self.quantidade = QSpinBox()
        self.quantidade.setMaximum(999999)
        self.quantidade.setValue(int(self.item_info.get("quantidade", 0) or 0))

        layout_form.addWidget(self.criar_label("Caixa"), 0, 0)
        layout_form.addWidget(self.caixa, 1, 0)
        layout_form.addWidget(self.criar_label("Localização"), 0, 1)
        layout_form.addWidget(self.localizacao, 1, 1)
        layout_form.addWidget(self.criar_label("Quantidade atual"), 2, 0)
        layout_form.addWidget(self.quantidade, 3, 0)
        layout_card.addLayout(layout_form)

        self.btn_salvar = QPushButton("Salvar alterações")
        self.btn_salvar.setMinimumHeight(48)
        self.btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salvar.clicked.connect(self.salvar_edicao)
        layout_card.addWidget(self.btn_salvar)

        self.btn_voltar = QPushButton("Cancelar e sair")
        self.btn_voltar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_voltar.clicked.connect(self.voltar_callback)
        layout_card.addWidget(self.btn_voltar, alignment=Qt.AlignmentFlag.AlignCenter)

        apply_shadow(self.card)
        return self.card

    def criar_label(self, texto):
        label = QLabel(texto)
        label.setObjectName("formLabel")
        return label

    def resolver_caminho_foto(self, caminho):
        if not caminho:
            return ""
        if os.path.isabs(caminho) and os.path.exists(caminho):
            return caminho
        absoluto = os.path.abspath(caminho)
        return absoluto if os.path.exists(absoluto) else ""

    def exibir_foto(self, caminho):
        caminho_real = self.resolver_caminho_foto(caminho)
        if caminho_real:
            pixmap = QPixmap(caminho_real)
            if not pixmap.isNull():
                self.lbl_foto.setPixmap(
                    pixmap.scaled(174, 174, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
                self.lbl_foto.setText("")

    def aplicar_tema(self, dark=False):
        self.dark_mode = dark
        p = palette(dark)
        self.setStyleSheet(f"background-color: {p['bg']}; color: {p['text']};")
        self.container.setStyleSheet(f"background-color: {p['bg']};")
        self.scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {p['bg']}; }}")
        self.header.setStyleSheet(header_banner_style("headerEdicao", dark))
        self.card.setStyleSheet(card_style(dark))
        self.frame_foto.setStyleSheet(f"""
            QFrame#frameFoto {{
                background-color: {p['card_alt']};
                border-radius: 8px;
                border: 1px solid {p['border']};
            }}
            QLabel {{
                color: {p['muted']};
                border: none;
                font-weight: 800;
            }}
        """)
        for widget in [self.nome, self.caixa, self.localizacao, self.quantidade]:
            widget.setStyleSheet(input_style(dark))
        for label in self.findChildren(QLabel, "formLabel") + [self.lbl_nome]:
            label.setStyleSheet(f"color: {p['text']}; font-weight: 800; border: none;")
        self.lbl_dica_minimo.setStyleSheet(f"color: {p['muted']}; border: none; font-size: 12px;")
        self.btn_foto.setStyleSheet(button_style("dark", dark))
        self.btn_salvar.setStyleSheet(button_style("primary", dark))
        self.btn_voltar.setStyleSheet(button_style("ghost", dark))
        apply_shadow(self.header, dark, blur=18)
        apply_shadow(self.card, dark, blur=18)

    def selecionar_foto(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Foto", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.foto_nova = file
            self.exibir_foto(file)
            self.btn_foto.setText("Trocar imagem")

    def copiar_foto_para_app(self):
        if not self.foto_nova:
            return self.foto_path

        try:
            os.makedirs("fotos", exist_ok=True)
            ext = os.path.splitext(self.foto_nova)[1]
            novo_nome = f"{uuid.uuid4().hex}{ext}"
            caminho_dest = os.path.join("fotos", novo_nome).replace("\\", "/")
            shutil.copy(self.foto_nova, caminho_dest)
            return caminho_dest
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Não foi possível salvar a foto: {exc}")
            return self.foto_path

    def salvar_edicao(self):
        nome = self.nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "O nome é obrigatório.")
            return

        caminho_final = self.copiar_foto_para_app()
        quantidade_minima = int(self.quantidade.value() * 0.10)

        try:
            atualizar_item(
                self.item_id,
                nome,
                self.caixa.text().strip(),
                self.localizacao.currentText(),
                quantidade_minima,
                self.quantidade.value(),
                caminho_final,
            )
            QMessageBox.information(self, "Sucesso", "Item atualizado!")
            self.atualizar_tabela()
            self.voltar_callback()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar: {exc}")