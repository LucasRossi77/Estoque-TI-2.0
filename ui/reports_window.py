from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QHeaderView, QAbstractItemView,
    QFrame, QHBoxLayout, QLineEdit, QPushButton, QComboBox,
    QMenu, QFileDialog, QMessageBox # <-- Adicionados para exportação
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextDocument, QPdfWriter
from services.movimentacao_service import listar_historico

class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Relatórios de Movimentação")
        self.resize(900, 600)
        self.setStyleSheet("background-color: #e8e0cc;")

        layout_principal = QVBoxLayout()

        titulo = QLabel("Histórico de Movimentações")
        titulo.setStyleSheet("""
            font-size: 26px; 
            font-weight: bold; 
            color: #1F2937; 
            padding-left: 10px; 
            margin-top: 10px; 
            margin-bottom: 5px;
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout_principal.addWidget(titulo)

        # --- BARRA DE FILTROS ---
        frame_filtros = QFrame()
        frame_filtros.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #d1c9b8;")
        layout_f = QHBoxLayout(frame_filtros)
        
        self.txt_filtro_item = QLineEdit(); self.txt_filtro_item.setPlaceholderText("🔍 Filtrar por Item...")
        self.combo_filtro_caminho = QComboBox()
        self.combo_filtro_caminho.addItems(["Todos", "ENTRADA", "SAIDA"])
        self.txt_filtro_resp = QLineEdit(); self.txt_filtro_resp.setPlaceholderText("👤 Responsável...")
        
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setStyleSheet("""
            QPushButton { background-color: #9c9075; color: white; border-radius: 4px; padding: 8px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #a39179; }
        """)
        btn_limpar.clicked.connect(self.limpar_filtros)

        # --- BOTÃO EXPORTAR (ADICIONADO) ---
        self.btn_exportar = QPushButton("📥 Exportar")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setStyleSheet("background-color: #059669; color: white; border-radius: 4px; padding: 8px 12px; font-weight: bold;")
        
        menu_exportar = QMenu(self.btn_exportar)
        menu_exportar.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #d1c9b8; border-radius: 4px; } 
            QMenu::item { padding: 8px 25px; color: #1F2937; font-weight: bold; } 
            QMenu::item:selected { background-color: #e8e0cc; }
        """)
        acao_pdf = menu_exportar.addAction("📄 Exportar para PDF")
        acao_xlsx = menu_exportar.addAction("📊 Exportar para Excel (.xlsx)")
        
        acao_pdf.triggered.connect(self.exportar_pdf)
        acao_xlsx.triggered.connect(self.exportar_excel)
        
        self.btn_exportar.setMenu(menu_exportar)
        # ----------------------------------
        
        estilo_input = "padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: #f9f9f9;"
        self.txt_filtro_item.setStyleSheet(estilo_input)
        self.combo_filtro_caminho.setStyleSheet(estilo_input)
        self.txt_filtro_resp.setStyleSheet(estilo_input)
        
        self.txt_filtro_item.textChanged.connect(self.filtrar_tabela)
        self.combo_filtro_caminho.currentTextChanged.connect(self.filtrar_tabela)
        self.txt_filtro_resp.textChanged.connect(self.filtrar_tabela)

        layout_f.addWidget(QLabel("Filtros:"))
        layout_f.addWidget(self.txt_filtro_item)
        layout_f.addWidget(self.combo_filtro_caminho)
        layout_f.addWidget(self.txt_filtro_resp)
        layout_f.addWidget(btn_limpar) 
        layout_f.addWidget(self.btn_exportar) # Adicionado ao lado do limpar

        layout_principal.addWidget(frame_filtros)

        # --- TABELA DE RELATÓRIOS ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["Item", "Qtd", "Caminho", "Responsável", "Data", "Observação"])
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        self.table.setStyleSheet("""
            QHeaderView::section { background-color: #e8e0cc; color: #1F2937; font-weight: bold; border: 1px solid #d1c9b8; }
            QTableWidget { background-color: white; gridline-color: #d1c9b8; outline: 0; color: #1F2937; }
            QTableWidget::item:selected { background-color: #a39179; color: #1F2937; }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout_principal.addWidget(self.table)
        self.setLayout(layout_principal)

        self.carregar_dados()

    def carregar_dados(self):
        dados = listar_historico()
        self.table.setRowCount(0)

        for row_idx, mov in enumerate(dados):
            self.table.insertRow(row_idx)
            
            data_raw = mov["data"]
            data_formatada = str(data_raw)[:19] if data_raw else "-"
            
            item_nome = mov["item_nome"] if mov["item_nome"] else "Desconhecido"
            quantidade = mov["quantidade"]
            tipo_mov = mov["tipo"]
            usuario = mov["usuario_nome"] if mov["usuario_nome"] else "Antigo"
            obs = mov["observacao"] if mov["observacao"] else "-"

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item_nome)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(quantidade)))
            
            item_tipo_widget = QTableWidgetItem(str(tipo_mov))
            cor = QColor("#10B981") if tipo_mov == "ENTRADA" else QColor("#EF4444")
            item_tipo_widget.setForeground(cor)
            font = item_tipo_widget.font()
            font.setBold(True)
            item_tipo_widget.setFont(font)
            self.table.setItem(row_idx, 2, item_tipo_widget)
            
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(usuario)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(data_formatada))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(obs)))
            
            for col in [1, 2, 4]:
                item = self.table.item(row_idx, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def limpar_filtros(self):
        self.txt_filtro_item.clear()
        self.combo_filtro_caminho.setCurrentIndex(0)
        self.txt_filtro_resp.clear()
        self.filtrar_tabela()

    def filtrar_tabela(self):
        filtro_item = self.txt_filtro_item.text().lower()
        filtro_caminho = self.combo_filtro_caminho.currentText()
        filtro_resp = self.txt_filtro_resp.text().lower()

        for row in range(self.table.rowCount()):
            item_texto = self.table.item(row, 0).text().lower()
            caminho_texto = self.table.item(row, 2).text()
            resp_texto = self.table.item(row, 3).text().lower()

            match_caminho = (filtro_caminho == "Todos") or (filtro_caminho == caminho_texto)
            match_item = filtro_item in item_texto
            match_resp = filtro_resp in resp_texto

            self.table.setRowHidden(row, not (match_item and match_caminho and match_resp))

    # =================================================================
    # FUNÇÕES DE EXPORTAÇÃO
    # =================================================================
    def exportar_pdf(self):
        from PyQt6.QtGui import QPageSize

        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", "Historico_Movimentacoes.pdf", "Arquivos PDF (*.pdf)")
        if not caminho: 
            return

        html = """
        <html><head><style>
            table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; }
            th, td { border: 1px solid #d1c9b8; padding: 8px; text-align: center; }
            th { background-color: #e8e0cc; color: #1F2937; }
        </style></head><body>
        <h2 style='text-align: center; font-family: Arial; color: #1F2937;'>Histórico de Movimentações</h2>
        <table>
            <tr>
                <th>Item</th>
                <th>Qtd</th>
                <th>Caminho</th>
                <th>Responsável</th>
                <th>Data</th>
                <th>Observação</th>
            </tr>
        """
        
        for row in range(self.table.rowCount()):
            # Pula a linha se estiver oculta pelos filtros
            if self.table.isRowHidden(row): 
                continue
                
            html += "<tr>"
            # As colunas da tabela relatórios: 0=Item, 1=Qtd, 2=Caminho, 3=Resp, 4=Data, 5=Obs
            for col in range(6): 
                item = self.table.item(row, col)
                texto = item.text() if item else ""
                html += f"<td>{texto}</td>"
            html += "</tr>"
        
        html += "</table></body></html>"
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        writer = QPdfWriter(caminho)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setResolution(96) # Corrige a proporção minúscula do QPdfWriter
        
        doc.print(writer)
        
        QMessageBox.information(self, "Sucesso", "Relatório exportado para PDF com sucesso!")

    def exportar_excel(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha Excel", "Historico_Movimentacoes.xlsx", "Arquivos Excel (*.xlsx)")
        if not caminho: 
            return

        try:
            import openpyxl
        except ImportError:
            QMessageBox.warning(self, "Erro", "A biblioteca 'openpyxl' não está instalada no seu Python.\n\nAbra o terminal e instale executando:\npip install openpyxl")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Histórico"
        
        ws.append(["Item", "Quantidade", "Caminho", "Responsável", "Data", "Observação"])
        
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            
            linha_dados = []
            for col in range(6):
                item = self.table.item(row, col)
                linha_dados.append(item.text() if item else "")
                
            ws.append(linha_dados)
            
        wb.save(caminho)
        QMessageBox.information(self, "Sucesso", "Planilha exportada com sucesso!")