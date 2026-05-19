import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QSpinBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

try:
    from database.connection import connect
except ImportError:
    def connect():
        return sqlite3.connect('database.db')

class OperacionalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F3EFE0;") 
        
        # Garante que o banco de dados tem as colunas necessárias
        self.verificar_colunas_banco()

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # --- CABEÇALHO ---
        titulo = QLabel("Gestão Operacional e Manutenção")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #1F2937;")
        layout_principal.addWidget(titulo)

        subtitulo = QLabel("Transfira itens entre o Estoque Geral, Uso Operacional e Manutenção.")
        subtitulo.setStyleSheet("font-size: 14px; color: #4B5563; margin-bottom: 10px;")
        layout_principal.addWidget(subtitulo)

        # --- MÓDULO DE TRANSFERÊNCIA ---
        frame_transferencia = QFrame()
        frame_transferencia.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #D1D5DB;
            }
            QLabel { border: none; font-weight: bold; color: #374151; }
            QComboBox, QSpinBox {
                padding: 8px;
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                background-color: #F9FAFB;
            }
        """)
        layout_transf = QHBoxLayout(frame_transferencia)
        layout_transf.setContentsMargins(20, 20, 20, 20)
        layout_transf.setSpacing(15)

        # Selecionar Item
        vbox_item = QVBoxLayout()
        vbox_item.addWidget(QLabel("Item:"))
        self.cb_item = QComboBox()
        vbox_item.addWidget(self.cb_item)
        layout_transf.addLayout(vbox_item, stretch=3)

        # Selecionar Origem
        vbox_origem = QVBoxLayout()
        vbox_origem.addWidget(QLabel("Origem:"))
        self.cb_origem = QComboBox()
        self.cb_origem.addItems(["Estoque Geral", "Em Uso", "Manutenção"])
        vbox_origem.addWidget(self.cb_origem)
        layout_transf.addLayout(vbox_origem, stretch=2)

        # Selecionar Destino
        vbox_destino = QVBoxLayout()
        vbox_destino.addWidget(QLabel("Destino:"))
        self.cb_destino = QComboBox()
        self.cb_destino.addItems(["Em Uso", "Manutenção", "Estoque Geral"])
        vbox_destino.addWidget(self.cb_destino)
        layout_transf.addLayout(vbox_destino, stretch=2)

        # Quantidade
        vbox_qtd = QVBoxLayout()
        vbox_qtd.addWidget(QLabel("Qtd:"))
        self.spin_qtd = QSpinBox()
        self.spin_qtd.setMinimum(1)
        self.spin_qtd.setMaximum(9999)
        vbox_qtd.addWidget(self.spin_qtd)
        layout_transf.addLayout(vbox_qtd, stretch=1)

        # Botão Transferir
        vbox_btn = QVBoxLayout()
        vbox_btn.addStretch()
        btn_transferir = QPushButton("Efetuar Transferência")
        btn_transferir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_transferir.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        btn_transferir.clicked.connect(self.efetuar_transferencia)
        vbox_btn.addWidget(btn_transferir)
        layout_transf.addLayout(vbox_btn, stretch=2)

        layout_principal.addWidget(frame_transferencia)

        # --- TABELA DE DISTRIBUIÇÃO ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "Item", "Estoque Geral", "Em Uso (Exposição)", "Em Manutenção", "Total Físico"
        ])
        
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #D1D5DB;
                gridline-color: #E5E7EB;
            }
            QHeaderView::section {
                background-color: #223959;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout_principal.addWidget(self.tabela)

        self.carregar_dados()

    def verificar_colunas_banco(self):
        # Cria as colunas automaticamente caso seja a primeira vez rodando
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(itens)")
        colunas = [col[1] for col in cursor.fetchall()]

        if 'em_uso' not in colunas:
            cursor.execute("ALTER TABLE itens ADD COLUMN em_uso INTEGER DEFAULT 0")
        if 'em_manutencao' not in colunas:
            cursor.execute("ALTER TABLE itens ADD COLUMN em_manutencao INTEGER DEFAULT 0")
        
        conn.commit()
        conn.close()

    def carregar_dados(self):
        self.cb_item.clear()
        self.tabela.setRowCount(0)

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id_item, nome, quantidade, em_uso, em_manutencao FROM itens ORDER BY nome")
        itens = cursor.fetchall()
        conn.close()

        for row_idx, (id_item, nome, estoque, uso, manutencao) in enumerate(itens):
            uso = uso if uso is not None else 0
            manutencao = manutencao if manutencao is not None else 0
            total = estoque + uso + manutencao

            # Preenche o ComboBox com o ID escondido no texto
            self.cb_item.addItem(f"{id_item} - {nome}", id_item)

            self.tabela.insertRow(row_idx)
            
            # Formatação da tabela
            item_nome = QTableWidgetItem(nome)
            item_estoque = QTableWidgetItem(str(estoque))
            item_uso = QTableWidgetItem(str(uso))
            item_manut = QTableWidgetItem(str(manutencao))
            item_total = QTableWidgetItem(str(total))

            # Cores para destacar
            item_uso.setForeground(QBrush(QColor("#10B981"))) # Verde
            item_manut.setForeground(QBrush(QColor("#EF4444"))) # Vermelho
            item_total.setForeground(QBrush(QColor("#4B5563"))) # Cinza escuro

            for item in [item_estoque, item_uso, item_manut, item_total]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela.setItem(row_idx, 0, item_nome)
            self.tabela.setItem(row_idx, 1, item_estoque)
            self.tabela.setItem(row_idx, 2, item_uso)
            self.tabela.setItem(row_idx, 3, item_manut)
            self.tabela.setItem(row_idx, 4, item_total)

    def efetuar_transferencia(self):
        if self.cb_item.count() == 0:
            return

        id_item = self.cb_item.currentData()
        origem = self.cb_origem.currentText()
        destino = self.cb_destino.currentText()
        qtd_transferir = self.spin_qtd.value()

        if origem == destino:
            QMessageBox.warning(self, "Aviso", "A origem e o destino não podem ser iguais.")
            return

        # Mapeando os nomes do ComboBox para as colunas do banco
        mapa_colunas = {
            "Estoque Geral": "quantidade",
            "Em Uso": "em_uso",
            "Manutenção": "em_manutencao"
        }
        
        coluna_origem = mapa_colunas[origem]
        coluna_destino = mapa_colunas[destino]

        conn = connect()
        cursor = conn.cursor()

        # Verifica se tem quantidade suficiente na origem
        cursor.execute(f"SELECT {coluna_origem} FROM itens WHERE id_item = ?", (id_item,))
        resultado = cursor.fetchone()
        
        qtd_disponivel = resultado[0] if resultado[0] is not None else 0

        if qtd_transferir > qtd_disponivel:
            QMessageBox.critical(self, "Erro", f"Quantidade insuficiente em '{origem}'. Disponível: {qtd_disponivel}")
            conn.close()
            return

        # Executa a transferência matemática no banco
        cursor.execute(f"UPDATE itens SET {coluna_origem} = {coluna_origem} - ?, {coluna_destino} = IFNULL({coluna_destino}, 0) + ? WHERE id_item = ?", 
                       (qtd_transferir, qtd_transferir, id_item))
        
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Sucesso", "Transferência realizada com sucesso!")
        self.spin_qtd.setValue(1)
        self.carregar_dados() # Atualiza a tabela instantaneamente