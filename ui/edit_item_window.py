import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QScrollArea,
    QSpinBox, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import shutil
import uuid
from services.item_service import buscar_item_por_id, atualizar_item

class EditItemWidget(QWidget):
    def __init__(self, item_id, atualizar_tabela, voltar_callback):
        super().__init__()
        self.item_id = item_id
        self.atualizar_tabela = atualizar_tabela
        self.voltar_callback = voltar_callback
        
        # 1. Busca os dados
        self.item_info = buscar_item_por_id(self.item_id)
        if not self.item_info:
            QMessageBox.critical(self, "Erro", "Item não encontrado!")
            self.voltar_callback()
            return

        self.foto_path = self.item_info.get("foto", "") or ""
        self.cor_azul = "#1F2937" # O azul do botão salvar

        # --- Interface ---
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

        self.card = QFrame()
        self.card.setMinimumWidth(700) # Aumentei um pouco a largura para acomodar a foto maior
        self.card.setStyleSheet("background-color: #e8e0cc; border-radius: 20px; border: 1px solid #d1c9b8;")

        layout_card = QVBoxLayout(self.card)
        layout_card.setSpacing(10) # Reduzido para aproximar os elementos
        layout_card.setContentsMargins(40, 40, 40, 40)

        titulo = QLabel("EDITAR INFORMAÇÕES")
        titulo.setStyleSheet("font-size: 22px; color: #1F2937; border: none; font-weight: bold; margin-bottom: 10px;")
        layout_card.addWidget(titulo)

        # --- SEÇÃO SUPERIOR: FOTO + NOME ---
        secao_topo = QHBoxLayout()
        secao_topo.setSpacing(25)
        secao_topo.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinha o topo da foto com o topo do texto

        # Container da Foto (Aumentado para 200x200)
        self.frame_foto = QFrame()
        self.frame_foto.setFixedSize(200, 200)
        # Borda com o mesmo azul do salvar
        self.frame_foto.setStyleSheet(f"border: 3px solid {self.cor_azul}; border-radius: 15px; background-color: white;")
        layout_f = QVBoxLayout(self.frame_foto)
        
        self.lbl_foto = QLabel("SEM FOTO")
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto.setStyleSheet("border: none; color: #9c9075; font-weight: bold;")
        layout_f.addWidget(self.lbl_foto)
        
        if self.foto_path:
            caminho_absoluto = os.path.abspath(self.foto_path)
            if os.path.exists(caminho_absoluto):
                pixmap = QPixmap(caminho_absoluto)
                if not pixmap.isNull():
                    self.lbl_foto.setPixmap(pixmap.scaled(190, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.lbl_foto.setText("")

        # Lado direito: Nome e Botão de Foto
        vbox_nome = QVBoxLayout()
        vbox_nome.setSpacing(8)
        vbox_nome.setContentsMargins(0, 0, 0, 0)
        
        lbl_n = QLabel("Nome do Item:")
        lbl_n.setStyleSheet("color: #1F2937; font-weight: bold; border: none; font-size: 14px;")
        
        self.nome = QLineEdit(str(self.item_info.get("nome", "")))
        self.nome.setStyleSheet(self.estilo_input())
        self.nome.setFixedHeight(50) # Deixa a caixa de nome mais robusta
        
        # Botão Alterar Foto com o mesmo azul do salvar
        self.btn_foto = QPushButton("📸 Alterar Imagem do Item")
        self.btn_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_foto.setStyleSheet(f"""
            background-color: {self.cor_azul}; 
            color: white; 
            border-radius: 8px; 
            padding: 12px; 
            font-weight: bold; 
            border: none;
        """)
        self.btn_foto.clicked.connect(self.selecionar_foto)

        vbox_nome.addWidget(lbl_n)
        vbox_nome.addWidget(self.nome)
        vbox_nome.addSpacing(10)
        vbox_nome.addWidget(self.btn_foto)
        vbox_nome.addStretch() # Empurra tudo para cima para alinhar com a foto

        secao_topo.addWidget(self.frame_foto)
        secao_topo.addLayout(vbox_nome)
        layout_card.addLayout(secao_topo)

        # --- SEÇÃO INFERIOR: GRID DE CAMPOS ---
        layout_form = QGridLayout()
        layout_form.setSpacing(15)
        layout_form.setContentsMargins(0, 10, 0, 10) # Margem pequena para encostar na foto
        estilo_label = "color: #1F2937; font-weight: bold; border: none;"

        layout_form.addWidget(QLabel("Caixa:", styleSheet=estilo_label), 0, 0)
        self.caixa = QLineEdit(str(self.item_info.get("caixa", "")))
        self.caixa.setStyleSheet(self.estilo_input())
        layout_form.addWidget(self.caixa, 1, 0)

        layout_form.addWidget(QLabel("Localização:", styleSheet=estilo_label), 0, 1)
        self.localizacao = QComboBox()
        self.localizacao.addItems(["Sem Armário", "Armário 1", "Armário 2", "Armário 3", "Cestos", "Bancada/Setor"])
        idx = self.localizacao.findText(str(self.item_info.get("localizacao", "")))
        if idx >= 0: self.localizacao.setCurrentIndex(idx)
        self.localizacao.setStyleSheet(self.estilo_combo())
        layout_form.addWidget(self.localizacao, 1, 1)

        layout_form.addWidget(QLabel("Quantidade Atual:", styleSheet=estilo_label), 2, 0)
        self.quantidade = QSpinBox()
        self.quantidade.setMaximum(999999)
        self.quantidade.setValue(int(self.item_info.get("quantidade", 0)))
        self.quantidade.setStyleSheet(self.estilo_input())
        layout_form.addWidget(self.quantidade, 3, 0)

        layout_form.addWidget(QLabel("Quantidade Mínima:", styleSheet=estilo_label), 2, 1)
        self.quantidade_minima = QSpinBox()
        self.quantidade_minima.setMaximum(999999)
        self.quantidade_minima.setValue(int(self.item_info.get("quantidade_minima", 0)))
        self.quantidade_minima.setStyleSheet(self.estilo_input())
        layout_form.addWidget(self.quantidade_minima, 3, 1)

        layout_card.addLayout(layout_form)

        # Botões Finais
        self.btn_salvar = QPushButton("SALVAR ALTERAÇÕES")
        self.btn_salvar.setMinimumHeight(55)
        self.btn_salvar.setStyleSheet(f"background-color: {self.cor_azul}; color: white; border-radius: 12px; font-weight: bold; font-size: 15px; border: none;")
        self.btn_salvar.clicked.connect(self.salvar_edicao)
        layout_card.addWidget(self.btn_salvar)

        self.btn_voltar = QPushButton("Cancelar e Sair")
        self.btn_voltar.setStyleSheet("color: #4B5563; text-decoration: underline; border: none; background: transparent;")
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
                /* Força a cor do texto na seleção para não ficar branco no fundo branco */
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

    def salvar_edicao(self):
        nome = self.nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "O nome é obrigatório.")
            return

        caminho_final = self.foto_path
        if self.foto_path and not self.foto_path.startswith("fotos"):
            try:
                if not os.path.exists("fotos"): os.makedirs("fotos")
                ext = os.path.splitext(self.foto_path)[1]
                novo_nome = f"{uuid.uuid4().hex}{ext}"
                caminho_final = os.path.join("fotos", novo_nome).replace("\\", "/")
                shutil.copy(self.foto_path, caminho_final)
            except Exception as e:
                print(f"Erro ao copiar foto: {e}")

        try:
            atualizar_item(
                self.item_id, nome, self.caixa.text(), 
                self.localizacao.currentText(), self.quantidade_minima.value(), 
                self.quantidade.value(), caminho_final
            )
            QMessageBox.information(self, "Sucesso", "Item atualizado!")
            self.atualizar_tabela()
            self.voltar_callback()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar: {e}")