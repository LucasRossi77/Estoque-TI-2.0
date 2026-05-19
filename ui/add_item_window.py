import os
import shutil
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QScrollArea,
    QSpinBox, QMessageBox, QFrame, QComboBox,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from services.item_service import adicionar_item

class AddItemWidget(QWidget):
    def __init__(self, atualizar_tabela, voltar_callback):
        super().__init__()
        self.atualizar_tabela = atualizar_tabela
        self.voltar_callback = voltar_callback 
        self.foto_path = ""
        self.cor_azul = "#1F2937" # Azul padrão do sistema

        # --- Interface Base ---
        self.setStyleSheet("background-color: #e8e0cc;")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        container = QWidget()
        layout_container = QVBoxLayout(container)
        layout_container.setContentsMargins(30, 30, 30, 30)
        layout_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- CARD PRINCIPAL ---
        self.card = QFrame()
        self.card.setMinimumWidth(700)
        self.card.setStyleSheet("background-color: #e8e0cc; border-radius: 20px; border: 1px solid #d1c9b8;")

        # Efeito de Sombra
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(30)
        sombra.setColor(QColor(0, 0, 0, 50))
        self.card.setGraphicsEffect(sombra)

        layout_card = QVBoxLayout(self.card)
        layout_card.setSpacing(10)
        layout_card.setContentsMargins(40, 40, 40, 40)

        titulo = QLabel("NOVO CADASTRO DE ITEM")
        titulo.setStyleSheet(f"font-size: 22px; color: {self.cor_azul}; border: none; font-weight: bold; margin-bottom: 10px;")
        layout_card.addWidget(titulo)

        # --- SEÇÃO SUPERIOR: FOTO + NOME (O padrão que você gostou) ---
        secao_topo = QHBoxLayout()
        secao_topo.setSpacing(25)
        secao_topo.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Container da Foto (200x200 com borda Azul)
        self.frame_foto = QFrame()
        self.frame_foto.setFixedSize(200, 200)
        self.frame_foto.setStyleSheet(f"border: 3px solid {self.cor_azul}; border-radius: 15px; background-color: white;")
        layout_f = QVBoxLayout(self.frame_foto)
        
        self.lbl_foto = QLabel("SEM FOTO")
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto.setStyleSheet("border: none; color: #9c9075; font-weight: bold;")
        layout_f.addWidget(self.lbl_foto)

        # Lado direito: Nome e Botão de Foto
        vbox_nome = QVBoxLayout()
        vbox_nome.setSpacing(8)
        
        lbl_n = QLabel("Nome do Item:")
        lbl_n.setStyleSheet("color: #1F2937; font-weight: bold; border: none; font-size: 14px;")
        
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Digite o nome do produto...")
        self.nome.setStyleSheet(self.estilo_input())
        self.nome.setFixedHeight(50)
        
        self.btn_foto = QPushButton("📸 Adicionar Imagem")
        self.btn_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_foto.setStyleSheet(f"background-color: {self.cor_azul}; color: white; border-radius: 8px; padding: 12px; font-weight: bold; border: none;")
        self.btn_foto.clicked.connect(self.selecionar_foto)

        vbox_nome.addWidget(lbl_n)
        vbox_nome.addWidget(self.nome)
        vbox_nome.addSpacing(10)
        vbox_nome.addWidget(self.btn_foto)
        vbox_nome.addStretch()

        secao_topo.addWidget(self.frame_foto)
        secao_topo.addLayout(vbox_nome)
        layout_card.addLayout(secao_topo)

        # --- SEÇÃO INFERIOR: GRID DE CAMPOS ---
        layout_form = QGridLayout()
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(0, 10, 0, 10)
        estilo_label = "color: #1F2937; font-weight: bold; border: none;"

        # Caixa
        layout_form.addWidget(QLabel("Caixa:", styleSheet=estilo_label), 0, 0)
        self.caixa = QLineEdit()
        self.caixa.setPlaceholderText("Ex: Caixa HDMI")
        self.caixa.setStyleSheet(self.estilo_input())
        layout_form.addWidget(self.caixa, 1, 0)

        # Localização (Com suas novas opções)
        layout_form.addWidget(QLabel("Localização:", styleSheet=estilo_label), 0, 1)
        self.localizacao = QComboBox()
        self.localizacao.addItems(["Sem Armário", "Armário 1", "Armário 2", "Armário 3", "Cestos", "Bancada/Setor"])
        self.localizacao.setStyleSheet(self.estilo_combo())
        layout_form.addWidget(self.localizacao, 1, 1)

        # Quantidades
        layout_form.addWidget(QLabel("Quantidade Inicial:", styleSheet=estilo_label), 2, 0)
        self.quantidade = QSpinBox()
        self.quantidade.setMaximum(999999)
        self.quantidade.setStyleSheet(self.estilo_input())
        layout_form.addWidget(self.quantidade, 3, 0)

        layout_form.addWidget(QLabel("Estoque Mínimo (Alerta):", styleSheet=estilo_label), 2, 1)
        self.quantidade_minima = QSpinBox()
        self.quantidade_minima.setMaximum(999999)
        self.quantidade_minima.setStyleSheet(self.estilo_input())
        layout_form.addWidget(self.quantidade_minima, 3, 1)

        layout_card.addLayout(layout_form)

        # Botões de Ação
        self.btn_salvar = QPushButton("CADASTRAR ITEM NO SISTEMA")
        self.btn_salvar.setMinimumHeight(55)
        self.btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salvar.setStyleSheet(f"background-color: {self.cor_azul}; color: white; border-radius: 12px; font-weight: bold; font-size: 15px; border: none;")
        self.btn_salvar.clicked.connect(self.salvar_item)
        layout_card.addWidget(self.btn_salvar)

        self.btn_voltar = QPushButton("Cancelar e Voltar")
        self.btn_voltar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_voltar.setStyleSheet("color: #4B5563; text-decoration: underline; border: none; background: transparent; font-size: 14px;")
        self.btn_voltar.clicked.connect(self.voltar_callback)
        layout_card.addWidget(self.btn_voltar)

        layout_container.addWidget(self.card)
        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

    def estilo_input(self):
        return """
            QLineEdit, QSpinBox {
                padding: 10px; border: 1px solid #d1c9b8; border-radius: 8px;
                background: white; color: #333; font-size: 14px;
                /* Remove o fundo azul e garante que o texto continue visível ao selecionar */
                selection-background-color: transparent;
                selection-color: #333;
            }
            QLineEdit:focus, QSpinBox:focus { border: 2px solid #1F2937; }
        """

    def estilo_combo(self):
        return """
            QComboBox {
                padding: 10px; border: 1px solid #d1c9b8; border-radius: 8px;
                background: white; color: #333; font-size: 14px;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-top: 6px solid #1F2937; border-left: 4px solid transparent; border-right: 4px solid transparent; }
        """

    def selecionar_foto(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Foto", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.foto_path = file
            pixmap = QPixmap(file)
            self.lbl_foto.setPixmap(pixmap.scaled(190, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_foto.setText("")
            self.btn_foto.setText("🔄 Trocar Imagem")

    def salvar_item(self):
        nome = self.nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "O nome do item é obrigatório.")
            return

        caminho_banco = ""
        if self.foto_path:
            try:
                if not os.path.exists("fotos"): os.makedirs("fotos")
                ext = os.path.splitext(self.foto_path)[1]
                novo_nome = f"{uuid.uuid4().hex}{ext}"
                caminho_dest = os.path.join("fotos", novo_nome).replace("\\", "/")
                shutil.copy(self.foto_path, caminho_dest)
                caminho_banco = caminho_dest
            except Exception as e:
                print(f"Erro ao salvar foto: {e}")

        try:
            adicionar_item(
                nome, 
                self.caixa.text(), 
                self.localizacao.currentText(), 
                self.quantidade.value(), 
                self.quantidade_minima.value(), 
                caminho_banco
            )
            QMessageBox.information(self, "Sucesso", "Item cadastrado com sucesso!")
            self.atualizar_tabela()
            self.voltar_callback()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar: {e}")