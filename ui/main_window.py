import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView, QSpinBox, QComboBox, QGridLayout, QScrollArea, QStackedWidget,
    QMenu, QFileDialog
)
from datetime import datetime 
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QBrush, QColor, QIcon, QPixmap, 
    QTextDocument, QPdfWriter
)
from database.connection import DB_PATH, connect, get_table_columns
from ui.theme import LOCALIZACOES_PADRAO, apply_shadow, button_style, card_style, como_usar_section_style, header_banner_style, input_style, palette, step_card_style, table_style

class VisaoBlocosWidget(QWidget):
    def __init__(self, caminho_db, pasta_fotos):
        super().__init__()
        self.caminho_db = caminho_db
        self.pasta_fotos = pasta_fotos
        self.nivel_atual = "LOCALIZACAO"
        self.local_selecionado = ""
        self.dark_mode = False

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        
        self.layout_nav = QHBoxLayout()
        self.btn_voltar = QPushButton("⬅ Voltar")
        self.btn_voltar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_voltar.setStyleSheet("padding: 5px 10px; background-color: #223959; color: white; border-radius: 4px; font-weight: bold;")
        self.btn_voltar.clicked.connect(self.voltar_nivel)
        self.btn_voltar.hide()
        
        self.lbl_caminho = QLabel("🏠 Selecione a Localização")
        self.lbl_caminho.setStyleSheet("font-weight: bold; color: #223959; font-size: 14px;")
        
        self.layout_nav.addWidget(self.btn_voltar)
        self.layout_nav.addWidget(self.lbl_caminho)
        self.layout_nav.addStretch()
        self.layout_principal.addLayout(self.layout_nav)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.container_grid = QWidget()
        self.layout_grid = QGridLayout(self.container_grid)
        self.layout_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layout_grid.setSpacing(15)
        self.scroll.setWidget(self.container_grid)
        self.layout_principal.addWidget(self.scroll)

    def limpar_grid(self):
        for i in reversed(range(self.layout_grid.count())): 
            widget = self.layout_grid.itemAt(i).widget()
            if widget: widget.deleteLater()

    def aplicar_tema(self, dark=False):
        self.dark_mode = dark
        p = palette(dark)
        self.btn_voltar.setStyleSheet(button_style("dark", dark))
        self.lbl_caminho.setStyleSheet(f"font-weight: bold; color: {p['accent']}; font-size: 14px;")
        self.scroll.setStyleSheet(f"border: none; background: {p['bg']};")

    def carregar_localizacoes(self):
        self.limpar_grid()
        self.nivel_atual = "LOCALIZACAO"
        self.lbl_caminho.setText("🏠 Todas as Localizações")
        self.btn_voltar.hide()
        
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT localizacao FROM itens WHERE localizacao IS NOT NULL AND localizacao != ''")
        locais = cursor.fetchall()
        conn.close()

        for index, (local,) in enumerate(locais):
            btn = QPushButton(f"📍\n{local}")
            btn.setFixedSize(180, 130) 
            btn.setStyleSheet(button_style("dark", self.dark_mode) + "QPushButton { font-size: 16px; }")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, l=local: self.carregar_caixas(l))
            
            linha, coluna = divmod(index, 4)
            self.layout_grid.addWidget(btn, linha, coluna)

    def carregar_caixas(self, local):
        self.limpar_grid()
        self.nivel_atual = "CAIXA"
        self.local_selecionado = local
        self.lbl_caminho.setText(f"🏠 {local} > Selecione uma Caixa")
        self.btn_voltar.show()

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT caixa FROM itens WHERE localizacao = ? AND caixa IS NOT NULL AND caixa != ''", (local,))
        caixas = cursor.fetchall()
        conn.close()

        for index, (caixa,) in enumerate(caixas):
            btn = QPushButton(f"📦\n{caixa}")
            btn.setFixedSize(180, 130)
            btn.setStyleSheet(button_style("dark", self.dark_mode) + "QPushButton { font-size: 16px; }")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=caixa: self.carregar_itens_final(c))
            linha, coluna = divmod(index, 4)
            self.layout_grid.addWidget(btn, linha, coluna)

    def carregar_itens_final(self, caixa):
        self.limpar_grid()
        self.nivel_atual = "ITEM"
        self.lbl_caminho.setText(f"🏠 {self.local_selecionado} > {caixa} > Itens")
        
        conn = connect()
        cursor = conn.cursor()
        # Adicionado o em_uso na busca
        cursor.execute("SELECT nome, foto, quantidade, quantidade_minima, em_uso FROM itens WHERE localizacao = ? AND caixa = ?", (self.local_selecionado, caixa))
        itens = cursor.fetchall()
        conn.close()

        for index, row in enumerate(itens):
            card = QFrame()
            card.setFixedSize(160, 200)
            
            # Tratamento de erro para garantir números inteiros
            try: qtd = int(row['quantidade'] or 0)
            except: qtd = 0
            
            try: em_uso = int(row['em_uso'] or 0) if 'em_uso' in row.keys() else 0
            except: em_uso = 0

            # Lógica Dinâmica: 10% do que está em uso
            if em_uso > 0:
                q_min_automatico = max(1, int(em_uso * 0.10))
                estoque_baixo = qtd <= q_min_automatico
                texto_minimo = str(q_min_automatico)
            else:
                estoque_baixo = False
                texto_minimo = "-"
            
            p = palette(self.dark_mode)
            if estoque_baixo:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {p['danger_bg']};
                        border-radius: 8px;
                        border: 1px solid {p['danger']};
                    }}
                    QLabel {{
                        background-color: transparent;
                        border: none;
                    }}
                """)
            else:
                card.setStyleSheet(card_style(self.dark_mode))
            l_card = QVBoxLayout(card)
            l_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl_f = QLabel()
            lbl_f.setFixedSize(80, 80)
            lbl_f.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if row['foto']:
                cam = os.path.join(self.pasta_fotos, row['foto'])
                if os.path.exists(cam):
                    lbl_f.setPixmap(QPixmap(cam).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            lbl_n = QLabel(row['nome'])
            lbl_n.setWordWrap(True)
            lbl_n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_n.setStyleSheet(f"font-weight: bold; font-size: 12px; border: none; color: {palette(self.dark_mode)['text']};")
            
            cor = "#EF4444" if estoque_baixo else "#10B981"
            lbl_q = QLabel(f"Qtd: {qtd} (Mín: {texto_minimo})")
            lbl_q.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_q.setStyleSheet(f"color: {cor}; font-weight: bold; font-size: 11px; border: none;")

            l_card.addWidget(lbl_f)
            l_card.addWidget(lbl_n)
            l_card.addWidget(lbl_q)
            
            linha, coluna = divmod(index, 5)
            self.layout_grid.addWidget(card, linha, coluna)
    def voltar_nivel(self):
        if self.nivel_atual == "ITEM": self.carregar_caixas(self.local_selecionado)
        elif self.nivel_atual == "CAIXA": self.carregar_localizacoes()


class EstoqueWidget(QWidget):
    def __init__(self, usuario_id, callback_adicionar, callback_editar):
        super().__init__()
        self.usuario_id = usuario_id
        self.callback_adicionar = callback_adicionar
        self.callback_editar = callback_editar
        self.dark_mode = False
        self.botoes_acao = []
        self.cards_kpi = []
        self.titulos_kpi = []
        
        pasta_ui = os.path.dirname(os.path.abspath(__file__))
        self.caminho_db = DB_PATH
        self.pasta_fotos = os.path.abspath(os.path.join(pasta_ui, "..")) 
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        self.layout_principal = layout_principal
        layout_principal.addWidget(self.criar_cabecalho())
        layout_principal.addWidget(self.criar_cards_como_usar())

        layout_cards = QHBoxLayout()
        self.lbl_total_itens = self.criar_cartao(layout_cards, "Itens Cadastrados")
        self.lbl_unidades = self.criar_cartao(layout_cards, "Unidades em Estoque")
        self.lbl_estoque_baixo = self.criar_cartao(layout_cards, "Estoque Baixo")
        self.lbl_movimentacoes = self.criar_cartao(layout_cards, "Movimentações Hoje")
        layout_principal.addLayout(layout_cards)

        frame_filtros = QFrame()
        self.frame_filtros = frame_filtros
        frame_filtros.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #E4DED2;")
        layout_f = QHBoxLayout(frame_filtros)
        
        self.txt_filtro_nome = QLineEdit()
        self.txt_filtro_nome.setPlaceholderText("🔍 Buscar por nome...")
        
        self.combo_filtro_local = QComboBox()
        self.combo_filtro_local.addItems(["Todos"] + LOCALIZACOES_PADRAO)
        
        self.txt_filtro_caixa = QLineEdit()
        self.txt_filtro_caixa.setPlaceholderText("📦 Caixa...")
        
        estilo_input = "padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: #f9f9f9;"
        estilo_combo = """
            QComboBox { padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: #f9f9f9; min-width: 150px; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border-top: 5px solid #223959; border-left: 4px solid transparent; border-right: 4px solid transparent; margin-right: 8px; }
        """
        
        self.txt_filtro_nome.setStyleSheet(estilo_input)
        self.combo_filtro_local.setStyleSheet(estilo_combo)
        self.txt_filtro_caixa.setStyleSheet(estilo_input)
        
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.clicked.connect(self.limpar_filtros)
        
        self.txt_filtro_nome.textChanged.connect(self.carregar_itens)
        self.combo_filtro_local.currentTextChanged.connect(self.carregar_itens)
        self.txt_filtro_caixa.textChanged.connect(self.carregar_itens)

        layout_f.addWidget(QLabel("Filtros:"))
        layout_f.addWidget(self.txt_filtro_nome)
        layout_f.addWidget(QLabel("📍"))
        layout_f.addWidget(self.combo_filtro_local)
        layout_f.addWidget(self.txt_filtro_caixa)
        layout_f.addWidget(btn_limpar)
        layout_principal.addWidget(frame_filtros)

        layout_acoes = QHBoxLayout()
        
        layout_esq = QHBoxLayout()
        layout_esq.addWidget(self.criar_botao_acao("Adicionar", "#2563EB", self.callback_adicionar))
        layout_esq.addWidget(self.criar_botao_acao("Editar", "#2563EB", self.editar_selecionado))
        layout_esq.addWidget(self.criar_botao_acao("Excluir", "#DC2626", self.deletar_item))
        layout_acoes.addLayout(layout_esq)

        layout_acoes.addStretch()

        layout_dir = QHBoxLayout()
        self.btn_exportar = QPushButton("📥 Exportar")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setStyleSheet("background-color: #059669; color: white; border-radius: 5px; padding: 10px 18px; font-weight: bold;")
        
        self.menu_exportar = QMenu(self.btn_exportar)
        self.menu_exportar.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #E4DED2; border-radius: 4px; } 
            QMenu::item { padding: 8px 25px; color: #223959; font-weight: bold; } 
            QMenu::item:selected { background-color: #EFF6FF; }
        """)
        acao_pdf = self.menu_exportar.addAction("📄 Exportar para PDF")
        acao_xlsx = self.menu_exportar.addAction("📊 Exportar para Excel (.xlsx)")
        
        acao_pdf.triggered.connect(self.exportar_pdf)
        acao_xlsx.triggered.connect(self.exportar_excel)
        
        self.btn_exportar.setMenu(self.menu_exportar)
        layout_dir.addWidget(self.btn_exportar)

        self.btn_toggle_vista = self.criar_botao_acao("🗂️ Ver em Blocos", "#223959", self.alternar_vista)
        layout_dir.addWidget(self.btn_toggle_vista)

        layout_acoes.addLayout(layout_dir)
        layout_principal.addLayout(layout_acoes)

        self.stack = QStackedWidget()

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7) 
        self.tabela.setHorizontalHeaderLabels(["ID", "Fotos", "Nome", "Qtd", "Min", "Localização", "Caixa"])

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(1, 100)    

        self.tabela.setColumnHidden(0, True) 
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) 
        self.tabela.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        self.tabela.setAlternatingRowColors(False)
        
        self.tabela.setStyleSheet("""
            QHeaderView::section { background-color: #223959; color: #FFFFFF; font-weight: bold; border: none; }
            QTableWidget { background-color: white; color: #1F2937; gridline-color: #E4DED2; outline: 0; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1F2937; border: none; }
        """)
        
        self.stack.addWidget(self.tabela)

        self.visao_blocos = VisaoBlocosWidget(self.caminho_db, self.pasta_fotos)
        self.stack.addWidget(self.visao_blocos)

        layout_principal.addWidget(self.stack) 

        self.frame_mov = QFrame()
        self.frame_mov.setFixedHeight(80)
        self.frame_mov.setStyleSheet("background-color: #223959; border-radius: 12px;")
        layout_mov = QHBoxLayout(self.frame_mov)
        layout_mov.setContentsMargins(20, 10, 20, 10)
        
        lbl_mov = QLabel("MOVIMENTAÇÃO RÁPIDA:")
        lbl_mov.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: none;")
        
        self.spin_qtd_mov = QSpinBox()
        self.spin_qtd_mov.setMinimum(1)
        self.spin_qtd_mov.setMaximum(10000)
        self.spin_qtd_mov.setStyleSheet("""
            QSpinBox {
                padding: 6px; border: 1px solid #ccc; border-radius: 4px; background: white;
                selection-background-color: transparent; 
                selection-color: #223959;
            }
        """)
        
        self.txt_obs_mov = QLineEdit()
        self.txt_obs_mov.setPlaceholderText("Observação (opcional)...")
        self.txt_obs_mov.setStyleSheet("padding: 8px; border-radius: 5px; background: white; min-width: 200px;")
        
        self.btn_entrada = QPushButton("ENTRADA")
        self.btn_entrada.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_entrada.setStyleSheet("background-color: #00a941; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        self.btn_entrada.clicked.connect(self.registrar_entrada)
        
        self.btn_saida = QPushButton("SAÍDA")
        self.btn_saida.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_saida.setStyleSheet("background-color: #F03330; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        self.btn_saida.clicked.connect(self.registrar_saida)

        layout_mov.addWidget(lbl_mov)
        layout_mov.addWidget(QLabel("Qtd:", styleSheet="color:white; border:none;"))
        layout_mov.addWidget(self.spin_qtd_mov)
        layout_mov.addWidget(self.txt_obs_mov)
        layout_mov.addWidget(self.btn_entrada)
        layout_mov.addWidget(self.btn_saida)
        
        layout_principal.addWidget(self.frame_mov)

        self.carregar_itens()
        self.aplicar_tema(self.dark_mode)

    def showEvent(self, event):
        super().showEvent(event)
        # Sempre que essa tela for exibida, recarrega a tabela de itens
        self.carregar_itens()

    def criar_cabecalho(self):
        frame = QFrame()
        frame.setObjectName("headerEstoque")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)

        self.lbl_header_titulo = QLabel("Controle de Estoque")
        self.lbl_header_titulo.setObjectName("headerTitulo")
        self.lbl_header_subtitulo = QLabel(
            "Cadastre, encontre, organize e movimente os itens de TI com uma visão clara do saldo."
        )
        self.lbl_header_subtitulo.setObjectName("headerSubtitulo")
        self.lbl_header_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_header_titulo)
        layout.addWidget(self.lbl_header_subtitulo)
        apply_shadow(frame)
        return frame

    def criar_cards_como_usar(self):
        frame = QFrame()
        frame.setObjectName("comoUsarEstoque")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        self.lbl_como_titulo = QLabel("Como usar esta tela")
        self.lbl_como_titulo.setObjectName("comoTitulo")
        self.lbl_como_subtitulo = QLabel(
            "Use os filtros para localizar itens, selecione uma linha para editar ou faça entradas e saídas rápidas."
        )
        self.lbl_como_subtitulo.setObjectName("comoSubtitulo")
        self.lbl_como_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_como_titulo)
        layout.addWidget(self.lbl_como_subtitulo)

        grid = QGridLayout()
        grid.setSpacing(12)
        passos = [
            ("1", "Filtre", "Busque por nome, armário ou caixa antes de movimentar."),
            ("2", "Selecione", "Clique em uma linha da tabela para editar, excluir ou movimentar."),
            ("3", "Movimente", "Use entrada e saída rápida para ajustar o saldo do estoque."),
            ("4", "Organize", "Alterne para blocos para navegar por localização e caixa."),
        ]
        self.cards_como_estoque = []
        for idx, (numero, titulo, descricao) in enumerate(passos):
            card = self.criar_card_passo(numero, titulo, descricao)
            self.cards_como_estoque.append(card)
            grid.addWidget(card, 0, idx)
        layout.addLayout(grid)
        apply_shadow(frame)
        return frame

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

    def aplicar_tema(self, dark=False):
        self.dark_mode = dark
        p = palette(dark)
        self.setStyleSheet(f"background-color: {p['bg']}; color: {p['text']};")
        self.frame_filtros.setStyleSheet(card_style(dark))
        self.txt_filtro_nome.setStyleSheet(input_style(dark))
        self.combo_filtro_local.setStyleSheet(input_style(dark))
        self.txt_filtro_caixa.setStyleSheet(input_style(dark))
        self.tabela.setStyleSheet(table_style(dark))

        self.findChild(QFrame, "headerEstoque").setStyleSheet(header_banner_style("headerEstoque", dark))

        self.findChild(QFrame, "comoUsarEstoque").setStyleSheet(como_usar_section_style(dark))
        for card in self.findChildren(QFrame, "cardPasso"):
            card.setStyleSheet(step_card_style(dark))

        for card in self.cards_kpi:
            card.setStyleSheet(card_style(dark))
            apply_shadow(card, dark)
        for label in [self.lbl_total_itens, self.lbl_unidades, self.lbl_estoque_baixo, self.lbl_movimentacoes]:
            label.setStyleSheet(f"color: {p['accent']}; font-size: 20px; font-weight: bold; border: none;")
        for label in self.titulos_kpi:
            label.setStyleSheet(f"color: {p['muted']}; font-size: 11px; font-weight: bold; border: none;")

        for btn, texto in self.botoes_acao:
            if "Excluir" in texto:
                btn.setStyleSheet(button_style("danger", dark))
            elif "Blocos" in texto or "Tabela" in texto:
                btn.setStyleSheet(button_style("dark", dark))
            else:
                btn.setStyleSheet(button_style("primary", dark))

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
        self.frame_mov.setStyleSheet(f"background-color: {p['header']}; border-radius: 8px;")
        self.spin_qtd_mov.setStyleSheet(input_style(dark))
        self.txt_obs_mov.setStyleSheet(input_style(dark))
        self.btn_entrada.setStyleSheet(button_style("success", dark))
        self.btn_saida.setStyleSheet(button_style("danger", dark))
        if hasattr(self.visao_blocos, "aplicar_tema"):
            self.visao_blocos.aplicar_tema(dark)

    def alternar_vista(self):
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.btn_toggle_vista.setText("📋 Ver em Tabela")
            self.visao_blocos.carregar_localizacoes()
        else:
            self.stack.setCurrentIndex(0)
            self.btn_toggle_vista.setText("🗂️ Ver em Blocos")
            self.carregar_itens()
        self.aplicar_tema(self.dark_mode)

    def criar_cartao(self, layout, titulo):
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #E4DED2;")
        self.cards_kpi.append(card)
        c_layout = QVBoxLayout(card)
        lbl_t = QLabel(titulo); lbl_t.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold; border: none;")
        self.titulos_kpi.append(lbl_t)
        lbl_v = QLabel("0"); lbl_v.setStyleSheet("color: #1E3A8A; font-size: 20px; font-weight: bold; border: none;")
        c_layout.addWidget(lbl_t); c_layout.addWidget(lbl_v)
        layout.addWidget(card)
        return lbl_v

    def criar_botao_acao(self, texto, cor, funcao):
        btn = QPushButton(texto)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {cor}; color: white; border-radius: 5px; padding: 10px 18px; font-weight: bold;")
        btn.clicked.connect(funcao)
        self.botoes_acao.append((btn, texto))
        return btn

    def limpar_filtros(self):
        self.txt_filtro_nome.clear()
        self.combo_filtro_local.setCurrentIndex(0) 
        self.txt_filtro_caixa.clear()
        self.carregar_itens()

    def carregar_itens(self):
        self.tabela.setRowCount(0)
        conn = connect()
        cursor = conn.cursor()
        
        f_nome = f"%{self.txt_filtro_nome.text()}%"
        f_caixa = f"%{self.txt_filtro_caixa.text()}%"
        
        texto_local = self.combo_filtro_local.currentText()
        if texto_local == "Todos":
            f_local = "%%"
        else:
            f_local = f"%{texto_local}%"
            
        # Adicionado o em_uso na busca SQL principal da tabela
        cursor.execute("""
            SELECT id_item, foto, nome, quantidade, quantidade_minima, localizacao, caixa, em_uso 
            FROM itens 
            WHERE nome LIKE ? AND localizacao LIKE ? AND caixa LIKE ? 
            ORDER BY id_item DESC
        """, (f_nome, f_local, f_caixa))
        
        dados = cursor.fetchall()
        conn.close()

        total_unidades = 0
        baixo_estoque = 0

        for row_idx, row in enumerate(dados):
            self.tabela.insertRow(row_idx)
            self.tabela.setRowHeight(row_idx, 100) 

            try: qtd = int(row['quantidade'])
            except: qtd = 0
            
            try: em_uso = int(row['em_uso']) if 'em_uso' in row.keys() else 0
            except: em_uso = 0

            # LÓGICA DINÂMICA: 10% do que está em uso
            if em_uso > 0:
                q_min_automatico = max(1, int(em_uso * 0.10))
                estoque_baixo = qtd <= q_min_automatico
                texto_minimo = str(q_min_automatico)
            else:
                estoque_baixo = False
                texto_minimo = "-"

            cor_alerta = "#3B1117" if self.dark_mode else "#FEE2E2"
            cor_normal = palette(self.dark_mode)["card"]
            cor_fundo = QColor(cor_alerta if estoque_baixo else cor_normal)
            cor_texto_alerta = QColor("#FCA5A5" if self.dark_mode else "#7F1D1D")
            brush_fundo = QBrush(cor_fundo)

            item_id = QTableWidgetItem(str(row[0]))
            item_id.setBackground(brush_fundo)
            item_id.setData(Qt.ItemDataRole.BackgroundRole, brush_fundo)
            if estoque_baixo:
                item_id.setForeground(QBrush(cor_texto_alerta))
            self.tabela.setItem(row_idx, 0, item_id)

            item_foto = QTableWidgetItem("")
            item_foto.setBackground(brush_fundo)
            item_foto.setData(Qt.ItemDataRole.BackgroundRole, brush_fundo)
            self.tabela.setItem(row_idx, 1, item_foto)

            label_foto = QLabel()
            label_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_foto.setStyleSheet(f"background-color: {cor_fundo.name()}; border: none;")
            if 'foto' in row.keys() and row['foto']:
                caminho_c = os.path.join(self.pasta_fotos, row['foto'])
                if os.path.exists(caminho_c):
                    pixmap = QPixmap(caminho_c).scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    label_foto.setPixmap(pixmap)
            self.tabela.setCellWidget(row_idx, 1, label_foto)

            cols_mapping = {2: 'nome', 3: 'quantidade', 4: 'quantidade_minima', 5: 'localizacao', 6: 'caixa'}
            for col_idx, col_name in cols_mapping.items():
                if col_idx == 4:
                    val = texto_minimo # Aqui exibimos o '-' ou o número automático calculado
                else:
                    val = str(row[col_name]) if col_name in row.keys() and row[col_name] is not None else ""
                    
                item = QTableWidgetItem(val)
                item.setBackground(brush_fundo)
                item.setData(Qt.ItemDataRole.BackgroundRole, brush_fundo)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col_idx != 2 else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                if estoque_baixo:
                    item.setForeground(QBrush(cor_texto_alerta))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                if col_idx == 2 and estoque_baixo:
                    baixo_estoque += 1
                
                self.tabela.setItem(row_idx, col_idx, item)
            
            total_unidades += qtd

        self.lbl_total_itens.setText(str(len(dados)))
        self.lbl_unidades.setText(str(total_unidades))
        self.lbl_estoque_baixo.setText(str(baixo_estoque))
    def editar_selecionado(self):
        linha = self.tabela.currentRow()
        if linha >= 0:
            self.callback_editar(self.tabela.item(linha, 0).text())
        else:
            QMessageBox.warning(self, "Aviso", "Selecione um item!")

    def deletar_item(self):
        linha = self.tabela.currentRow()
        if linha < 0: return
        
        item_id = self.tabela.item(linha, 0).text()
        if QMessageBox.question(self, "Excluir", "Deseja apagar este item?") == QMessageBox.StandardButton.Yes:
            conn = connect()
            conn.cursor().execute("DELETE FROM itens WHERE id_item = ?", (item_id,))
            conn.commit()
            conn.close()
            self.carregar_itens()

    def registrar_entrada(self):
        self._processar_movimentacao("ENTRADA")

    def registrar_saida(self):
        self._processar_movimentacao("SAÍDA")

    def _processar_movimentacao(self, tipo):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um item na tabela primeiro!")
            return

        qtd_movimento = self.spin_qtd_mov.value()
        observacao = self.txt_obs_mov.text()

        item_id_valor = self.tabela.item(linha, 0).text() 
        nome_item = self.tabela.item(linha, 2).text()
        
        try:
            qtd_atual = int(self.tabela.item(linha, 3).text())
        except:
            qtd_atual = 0

        tipo_db = "SAIDA" if "SAÍ" in tipo.upper() else "ENTRADA"

        if tipo_db == "SAIDA" and qtd_movimento > qtd_atual:
            QMessageBox.critical(self, "Erro", f"Estoque insuficiente de '{nome_item}'!\nSaldo atual: {qtd_atual}")
            return

        nova_qtd = (qtd_atual + qtd_movimento) if tipo_db == "ENTRADA" else (qtd_atual - qtd_movimento)
        data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE itens 
                SET quantidade = ? 
                WHERE id_item = ?
            """, (nova_qtd, item_id_valor))

            cursor.execute("""
                INSERT INTO movimentacoes (id_item, id_usuario, tipo, quantidade, observacao, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item_id_valor, self.usuario_id, tipo_db, qtd_movimento, observacao, data_hora_atual))

            conn.commit()
            
            self.spin_qtd_mov.setValue(1)
            self.txt_obs_mov.clear()
            self.carregar_itens()
            self.tabela.selectRow(linha)

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao salvar no banco de dados: {e}")
        finally:
            conn.close()

    def exportar_pdf(self):
        from PyQt6.QtGui import QPageSize

        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório PDF", "Relatorio_Estoque.pdf", "Arquivos PDF (*.pdf)")
        if not caminho: 
            return

        html = """
        <html><head><style>
            table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; }
            th, td { border: 1px solid #E4DED2; padding: 8px; text-align: center; }
            th { background-color: #223959; color: #FFFFFF; }
        </style></head><body>
        <h2 style='text-align: center; font-family: Arial; color: #1F2937;'>Relatório de Estoque</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Nome do Item</th>
                <th>Qtd</th>
                <th>Min</th>
                <th>Localização</th>
                <th>Caixa</th>
            </tr>
        """
        
        for row in range(self.tabela.rowCount()):
            if self.tabela.isRowHidden(row): 
                continue
            
            html += "<tr>"
            for col in [0, 2, 3, 4, 5, 6]: 
                item = self.tabela.item(row, col)
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
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Planilha Excel", "Planilha_Estoque.xlsx", "Arquivos Excel (*.xlsx)")
        if not caminho: 
            return

        try:
            import openpyxl
        except ImportError:
            QMessageBox.warning(self, "Erro", "A biblioteca 'openpyxl' não está instalada no seu Python.\n\nAbra o terminal e instale executando:\npip install openpyxl")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Estoque"
        
        ws.append(["ID", "Nome do Item", "Quantidade", "Qtd Mínima", "Localização", "Caixa"])
        
        for row in range(self.tabela.rowCount()):
            if self.tabela.isRowHidden(row):
                continue
                
            texto_minimo = self.tabela.item(row, 4).text()
            # Retorna zero no excel se na tela estiver com o traço "-"
            qtd_minima_excel = 0 if texto_minimo == "-" else int(texto_minimo)
            
            ws.append([
                self.tabela.item(row, 0).text(),
                self.tabela.item(row, 2).text(),
                int(self.tabela.item(row, 3).text()),
                qtd_minima_excel,
                self.tabela.item(row, 5).text(),
                self.tabela.item(row, 6).text()
            ])
            
        wb.save(caminho)
        QMessageBox.information(self, "Sucesso", "Relatório exportado para Excel com sucesso!")
