from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QHeaderView, QAbstractItemView, QFrame, QHBoxLayout, QLineEdit,
    QPushButton, QComboBox, QMenu, QFileDialog, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextDocument, QPdfWriter

from services.movimentacao_service import listar_historico
from ui.theme import apply_shadow, button_style, card_style, como_usar_section_style, header_banner_style, input_style, palette, step_card_style, table_style


class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.setWindowTitle("Relatórios de Movimentação")
        self.resize(900, 600)

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(30, 24, 30, 30)
        self.layout_principal.setSpacing(18)

        self.layout_principal.addWidget(self.criar_cabecalho())
        self.layout_principal.addWidget(self.criar_cards_como_usar())
        self.criar_barra_filtros()
        self.criar_tabela()

        self.carregar_dados()
        self.aplicar_tema(False)

    def criar_cabecalho(self):
        self.header = QFrame()
        self.header.setObjectName("headerRelatorios")
        layout = QVBoxLayout(self.header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)

        self.lbl_header_titulo = QLabel("Relatórios")
        self.lbl_header_titulo.setObjectName("headerTitulo")
        self.lbl_header_subtitulo = QLabel(
            "Acompanhe entradas, saídas, responsáveis e observações em uma linha do tempo filtrável."
        )
        self.lbl_header_subtitulo.setObjectName("headerSubtitulo")
        self.lbl_header_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_header_titulo)
        layout.addWidget(self.lbl_header_subtitulo)
        apply_shadow(self.header)
        return self.header

    def criar_cards_como_usar(self):
        self.frame_como_usar = QFrame()
        self.frame_como_usar.setObjectName("comoUsarRelatorios")
        layout = QVBoxLayout(self.frame_como_usar)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        self.lbl_como_titulo = QLabel("Como usar esta tela")
        self.lbl_como_titulo.setObjectName("comoTitulo")
        self.lbl_como_subtitulo = QLabel(
            "Filtre o histórico por item, tipo de movimentação ou responsável antes de exportar."
        )
        self.lbl_como_subtitulo.setObjectName("comoSubtitulo")
        self.lbl_como_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_como_titulo)
        layout.addWidget(self.lbl_como_subtitulo)

        grid = QGridLayout()
        grid.setSpacing(12)
        passos = [
            ("1", "Filtre", "Use item, caminho ou responsável para reduzir a lista."),
            ("2", "Confira", "Veja data, quantidade e observação de cada movimentação."),
            ("3", "Exporte", "Gere PDF ou Excel somente com as linhas visíveis."),
        ]
        for idx, (numero, titulo, descricao) in enumerate(passos):
            grid.addWidget(self.criar_card_passo(numero, titulo, descricao), 0, idx)
        layout.addLayout(grid)
        apply_shadow(self.frame_como_usar)
        return self.frame_como_usar

    def criar_card_passo(self, numero, titulo, descricao):
        card = QFrame()
        card.setObjectName("cardPasso")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        lbl_numero = QLabel(numero)
        lbl_numero.setObjectName("numeroPasso")
        lbl_numero.setFixedSize(34, 34)
        lbl_numero.setAlignment(Qt.AlignmentFlag.AlignCenter)

        textos = QVBoxLayout()
        textos.setSpacing(3)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("tituloPasso")
        lbl_desc = QLabel(descricao)
        lbl_desc.setObjectName("descPasso")
        lbl_desc.setWordWrap(True)
        textos.addWidget(lbl_titulo)
        textos.addWidget(lbl_desc)

        layout.addWidget(lbl_numero)
        layout.addLayout(textos)
        return card

    def criar_barra_filtros(self):
        self.frame_filtros = QFrame()
        layout_f = QHBoxLayout(self.frame_filtros)
        layout_f.setContentsMargins(15, 12, 15, 12)
        layout_f.setSpacing(10)

        self.txt_filtro_item = QLineEdit()
        self.txt_filtro_item.setPlaceholderText("Filtrar por item")
        self.combo_filtro_caminho = QComboBox()
        self.combo_filtro_caminho.addItems(["Todos", "ENTRADA", "SAIDA"])
        self.txt_filtro_resp = QLineEdit()
        self.txt_filtro_resp.setPlaceholderText("Responsável")

        self.btn_limpar = QPushButton("Limpar filtros")
        self.btn_limpar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpar.clicked.connect(self.limpar_filtros)

        self.btn_exportar = QPushButton("Exportar")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)

        self.menu_exportar = QMenu(self.btn_exportar)
        acao_pdf = self.menu_exportar.addAction("Exportar para PDF")
        acao_xlsx = self.menu_exportar.addAction("Exportar para Excel (.xlsx)")
        acao_pdf.triggered.connect(self.exportar_pdf)
        acao_xlsx.triggered.connect(self.exportar_excel)
        self.btn_exportar.setMenu(self.menu_exportar)

        self.txt_filtro_item.textChanged.connect(self.filtrar_tabela)
        self.combo_filtro_caminho.currentTextChanged.connect(self.filtrar_tabela)
        self.txt_filtro_resp.textChanged.connect(self.filtrar_tabela)

        self.lbl_filtros = QLabel("Filtros")
        layout_f.addWidget(self.lbl_filtros)
        layout_f.addWidget(self.txt_filtro_item)
        layout_f.addWidget(self.combo_filtro_caminho)
        layout_f.addWidget(self.txt_filtro_resp)
        layout_f.addWidget(self.btn_limpar)
        layout_f.addWidget(self.btn_exportar)
        self.layout_principal.addWidget(self.frame_filtros)

    def criar_tabela(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["Item", "Qtd", "Caminho", "Responsável", "Data", "Observação"])
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.layout_principal.addWidget(self.table)

    def aplicar_tema(self, dark=False):
        self.dark_mode = dark
        p = palette(dark)
        self.setStyleSheet(f"background-color: {p['bg']}; color: {p['text']};")
        self.header.setStyleSheet(header_banner_style("headerRelatorios", dark))
        self.frame_como_usar.setStyleSheet(como_usar_section_style(dark))
        for card in self.frame_como_usar.findChildren(QFrame, "cardPasso"):
            card.setStyleSheet(step_card_style(dark))
        self.frame_filtros.setStyleSheet(card_style(dark))
        self.lbl_filtros.setStyleSheet(f"color: {p['text']}; font-weight: 800; border: none;")
        for widget in [self.txt_filtro_item, self.combo_filtro_caminho, self.txt_filtro_resp]:
            widget.setStyleSheet(input_style(dark))
        self.btn_limpar.setStyleSheet(button_style("muted", dark))
        self.btn_exportar.setStyleSheet(button_style("success", dark))
        self.menu_exportar.setStyleSheet(f"""
            QMenu {{
                background-color: {p['card']};
                border: 1px solid {p['border']};
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                color: {p['text']};
                font-weight: bold;
            }}
            QMenu::item:selected {{
                background-color: {p['soft']};
            }}
        """)
        self.table.setStyleSheet(table_style(dark))
        apply_shadow(self.header, dark, blur=18)
        apply_shadow(self.frame_como_usar, dark, blur=18)

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

            match_caminho = filtro_caminho == "Todos" or filtro_caminho == caminho_texto
            match_item = filtro_item in item_texto
            match_resp = filtro_resp in resp_texto

            self.table.setRowHidden(row, not (match_item and match_caminho and match_resp))

    def exportar_pdf(self):
        from PyQt6.QtGui import QPageSize

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório PDF",
            "Historico_Movimentacoes.pdf",
            "Arquivos PDF (*.pdf)",
        )
        if not caminho:
            return

        html = """
        <html><head><style>
            table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; }
            th, td { border: 1px solid #E4DED2; padding: 8px; text-align: center; }
            th { background-color: #223959; color: white; }
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
            if self.table.isRowHidden(row):
                continue

            html += "<tr>"
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
        writer.setResolution(96)

        doc.print(writer)
        QMessageBox.information(self, "Sucesso", "Relatório exportado para PDF com sucesso!")

    def exportar_excel(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Planilha Excel",
            "Historico_Movimentacoes.xlsx",
            "Arquivos Excel (*.xlsx)",
        )
        if not caminho:
            return

        try:
            import openpyxl
        except ImportError:
            QMessageBox.warning(
                self,
                "Erro",
                "A biblioteca 'openpyxl' não está instalada.\n\nInstale com: pip install openpyxl",
            )
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
