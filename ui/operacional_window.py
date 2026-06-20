import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QPushButton, QMessageBox, QScrollArea,
    QGridLayout, QGraphicsDropShadowEffect, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from database.connection import connect, get_table_columns
from ui.theme import card_style, como_usar_section_style, input_style, palette, step_card_style, table_style


class OperacionalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.itens_cache = {}
        self.dark_mode = False
        self.setStyleSheet("""
            QWidget {
                background-color: #F6F4EF;
                color: #1F2937;
                font-family: Segoe UI, Arial, sans-serif;
            }
            QLabel {
                background-color: transparent;
            }
            QComboBox, QSpinBox {
                min-height: 34px;
                padding: 6px 10px;
                border: 1px solid #D8D3C7;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #1F2937;
            }
            QComboBox:focus, QSpinBox:focus {
                border: 1px solid #3B82F6;
            }
            QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: transparent;
                width: 22px;
            }
        """)

        self.verificar_colunas_banco()

        layout_base = QVBoxLayout(self)
        layout_base.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: #F6F4EF; }")

        self.content_widget = QWidget()
        self.layout_principal = QVBoxLayout(self.content_widget)
        self.layout_principal.setContentsMargins(30, 24, 30, 30)
        self.layout_principal.setSpacing(18)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.content_widget)
        layout_base.addWidget(self.scroll_area)

        self.layout_principal.addWidget(self.criar_cabecalho())
        self.layout_principal.addLayout(self.criar_cards_resumo())
        self.layout_principal.addWidget(self.criar_cards_como_usar())
        self.layout_principal.addWidget(self.criar_modulo_transferencia())
        self.criar_tabela_distribuicao()

        self.carregar_dados()
        self.aplicar_tema(False)

    def criar_cabecalho(self):
        header = QFrame()
        header.setObjectName("headerOperacional")
        header.setStyleSheet("""
            QFrame#headerOperacional {
                background-color: #223959;
                border-radius: 8px;
                border: none;
            }
            QFrame#headerOperacional QLabel {
                color: white;
                border: none;
                background-color: transparent;
            }
        """)
        self.aplicar_sombra(header, blur=18, opacity=30)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)

        titulo = QLabel("Gestão Operacional")
        titulo.setStyleSheet("font-size: 28px; font-weight: 800;")
        subtitulo = QLabel(
            "Controle o que fica no estoque, o que está em uso e o que foi separado para manutenção."
        )
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("font-size: 14px; color: #E5EAF3;")

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        return header

    def criar_cards_resumo(self):
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.card_estoque, self.lbl_total_estoque, self.lbl_desc_estoque = self.criar_card_resumo(
            "Estoque Geral", "Unidades disponíveis", "#2563EB"
        )
        self.card_uso, self.lbl_total_uso, self.lbl_desc_uso = self.criar_card_resumo(
            "Em Uso", "Fora do estoque", "#059669"
        )
        self.card_manutencao, self.lbl_total_manutencao, self.lbl_desc_manutencao = self.criar_card_resumo(
            "Manutenção", "Itens em reparo", "#D97706"
        )
        self.card_cobertura, self.lbl_total_alertas, self.lbl_desc_alertas = self.criar_card_resumo(
            "Sem cobertura", "Meta: 10% do uso", "#DC2626"
        )

        layout.addWidget(self.card_estoque)
        layout.addWidget(self.card_uso)
        layout.addWidget(self.card_manutencao)
        layout.addWidget(self.card_cobertura)
        return layout

    def criar_card_resumo(self, titulo, descricao, cor):
        card = QFrame()
        card.setObjectName("cardResumo")
        card.setMinimumHeight(104)
        card.setStyleSheet(f"""
            QFrame#cardResumo {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E4DED2;
            }}
            QLabel#cardTitulo {{
                color: {cor};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0px;
                border: none;
                background-color: transparent;
            }}
            QLabel#cardValor {{
                color: #111827;
                font-size: 30px;
                font-weight: 800;
                border: none;
                background-color: transparent;
            }}
            QLabel#cardDesc {{
                color: #6B7280;
                font-size: 12px;
                border: none;
                background-color: transparent;
            }}
        """)
        self.aplicar_sombra(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(3)

        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setObjectName("cardTitulo")
        lbl_valor = QLabel("0")
        lbl_valor.setObjectName("cardValor")
        lbl_desc = QLabel(descricao)
        lbl_desc.setObjectName("cardDesc")
        lbl_desc.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        layout.addWidget(lbl_desc)
        return card, lbl_valor, lbl_desc

    def criar_cards_como_usar(self):
        frame = QFrame()
        frame.setObjectName("comoUsar")
        self.aplicar_sombra(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Como usar esta tela")
        titulo.setObjectName("comoTitulo")
        subtitulo = QLabel("A transferência muda somente a distribuição física do item dentro do sistema.")
        subtitulo.setObjectName("comoSubtitulo")
        subtitulo.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        grid = QGridLayout()
        grid.setSpacing(12)
        passos = [
            ("1", "Escolha o item", "Selecione o equipamento ou acessório que será movimentado."),
            ("2", "Defina a origem", "Informe de onde a quantidade vai sair: estoque, uso ou manutenção."),
            ("3", "Defina o destino", "Escolha para onde ela deve ir e confira se origem e destino são diferentes."),
            ("4", "Transfira", "Digite a quantidade e confirme. Os cards e a tabela atualizam na hora."),
        ]
        for idx, (numero, titulo_passo, descricao) in enumerate(passos):
            grid.addWidget(self.criar_card_passo(numero, titulo_passo, descricao), 0, idx)

        layout.addLayout(grid)
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

    def criar_modulo_transferencia(self):
        frame = QFrame()
        frame.setObjectName("transferencia")
        frame.setStyleSheet("""
            QFrame#transferencia {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E4DED2;
            }
            QLabel#tituloSecao {
                color: #1F2937;
                font-size: 18px;
                font-weight: 800;
                border: none;
                background-color: transparent;
            }
            QLabel#rotuloCampo {
                color: #374151;
                font-size: 12px;
                font-weight: 800;
                border: none;
                background-color: transparent;
            }
            QLabel#saldoOrigem {
                color: #374151;
                font-size: 13px;
                font-weight: 700;
                border: none;
                background-color: transparent;
            }
            QLabel#dicaTransferencia {
                color: #6B7280;
                font-size: 12px;
                border: none;
                background-color: transparent;
            }
            QPushButton#btnTransferir {
                background-color: #2563EB;
                color: white;
                font-weight: 800;
                padding: 10px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton#btnTransferir:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnTransferir:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }
        """)
        self.aplicar_sombra(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Transferência operacional")
        titulo.setObjectName("tituloSecao")
        layout.addWidget(titulo)

        layout_transf = QHBoxLayout()
        layout_transf.setSpacing(14)

        self.cb_item = QComboBox()
        layout_transf.addLayout(self.criar_campo("Item", self.cb_item), stretch=3)

        self.cb_origem = QComboBox()
        self.cb_origem.addItems(["Estoque Geral", "Em Uso", "Manutenção"])
        layout_transf.addLayout(self.criar_campo("Origem", self.cb_origem), stretch=2)

        # ADICIONADO: Seta direcional para deixar o fluxo de transição intuitivo e visual
        vbox_seta = QVBoxLayout()
        lbl_espaco_seta = QLabel(" ")
        lbl_espaco_seta.setObjectName("rotuloCampo") 
        vbox_seta.addWidget(lbl_espaco_seta)
        
        lbl_seta = QLabel("➔")
        lbl_seta.setStyleSheet("font-size: 18px; font-weight: bold; color: #9CA3AF; background-color: transparent;")
        lbl_seta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox_seta.addWidget(lbl_seta)
        layout_transf.addLayout(vbox_seta)

        self.cb_destino = QComboBox()
        self.cb_destino.addItems(["Em Uso", "Manutenção", "Estoque Geral"])
        layout_transf.addLayout(self.criar_campo("Destino", self.cb_destino), stretch=2)

        self.spin_qtd = QSpinBox()
        self.spin_qtd.setMinimum(1)
        self.spin_qtd.setMaximum(9999)
        layout_transf.addLayout(self.criar_campo("Quantidade", self.spin_qtd), stretch=1)

        vbox_btn = QVBoxLayout()
        lbl_espaco = QLabel(" ")
        lbl_espaco.setObjectName("rotuloCampo")
        vbox_btn.addWidget(lbl_espaco)
        self.btn_transferir = QPushButton("Efetuar transferência")
        self.btn_transferir.setObjectName("btnTransferir")
        self.btn_transferir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_transferir.clicked.connect(self.efetuar_transferencia)
        vbox_btn.addWidget(self.btn_transferir)
        layout_transf.addLayout(vbox_btn, stretch=2)

        self.lbl_saldo_origem = QLabel("Saldo da origem: 0 unidade(s)")
        self.lbl_saldo_origem.setObjectName("saldoOrigem")
        self.lbl_dica_transferencia = QLabel("Escolha o caminho do item e confira o saldo antes de confirmar.")
        self.lbl_dica_transferencia.setObjectName("dicaTransferencia")
        self.lbl_dica_transferencia.setWordWrap(True)

        layout.addLayout(layout_transf)
        layout.addWidget(self.lbl_saldo_origem)
        layout.addWidget(self.lbl_dica_transferencia)

        self.cb_item.currentIndexChanged.connect(self.atualizar_saldo_origem)
        self.cb_origem.currentIndexChanged.connect(self.atualizar_saldo_origem)
        self.cb_destino.currentIndexChanged.connect(self.atualizar_saldo_origem)
        return frame

    def criar_campo(self, titulo, widget):
        layout = QVBoxLayout()
        layout.setSpacing(6)
        rotulo = QLabel(titulo)
        rotulo.setObjectName("rotuloCampo")
        layout.addWidget(rotulo)
        layout.addWidget(widget)
        return layout

    def criar_tabela_distribuicao(self):
        self.lbl_titulo_tabela = QLabel("Distribuição atual dos itens")
        self.lbl_titulo_tabela.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #1F2937; margin-top: 4px; background: transparent;"
        )
        self.layout_principal.addWidget(self.lbl_titulo_tabela)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Item", "Estoque Geral", "Em Uso", "Manutenção", "Total Físico", "Cobertura"
        ])
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabela.verticalHeader().setVisible(False)

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #FAFAF7;
                border-radius: 8px;
                border: 1px solid #E4DED2;
                gridline-color: #E5E7EB;
                color: #1F2937;
                selection-background-color: #DBEAFE;
                selection-color: #111827;
            }
            QHeaderView::section {
                background-color: #223959;
                color: #FFFFFF;
                font-weight: 800;
                padding: 9px;
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
        """)

        self.layout_principal.addWidget(self.tabela)

    def aplicar_tema(self, dark=False):
        self.dark_mode = dark
        p = palette(dark)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p['bg']};
                color: {p['text']};
                font-family: Segoe UI, Arial, sans-serif;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background: {p['bg']}; }}")
        self.content_widget.setStyleSheet(f"background-color: {p['bg']};")
        self.findChild(QFrame, "headerOperacional").setStyleSheet(f"""
            QFrame#headerOperacional {{
                background-color: {p['header']};
                border-radius: 8px;
                border: none;
            }}
            QFrame#headerOperacional QLabel {{
                color: {p['header_text']};
                border: none;
                background-color: transparent;
            }}
        """)
        for frame in self.findChildren(QFrame, "cardResumo"):
            frame.setStyleSheet(f"""
                QFrame#cardResumo {{
                    background-color: {p['card']};
                    border-radius: 8px;
                    border: 1px solid {p['border']};
                }}
                QLabel#cardTitulo {{
                    background-color: transparent;
                }}
                QLabel#cardValor {{
                    color: {p['text']};
                    font-size: 30px;
                    font-weight: 800;
                    border: none;
                    background-color: transparent;
                }}
                QLabel#cardDesc {{
                    color: {p['muted']};
                    font-size: 12px;
                    border: none;
                    background-color: transparent;
                }}
            """)
        self.findChild(QFrame, "comoUsar").setStyleSheet(como_usar_section_style(dark))
        for card in self.findChildren(QFrame, "cardPasso"):
            card.setStyleSheet(step_card_style(dark))
        self.findChild(QFrame, "transferencia").setStyleSheet(card_style(dark))
        for widget in [self.cb_item, self.cb_origem, self.cb_destino, self.spin_qtd]:
            widget.setStyleSheet(input_style(dark))
        self.lbl_titulo_tabela.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {p['text']}; margin-top: 4px; background: transparent;"
        )
        self.tabela.setStyleSheet(table_style(dark))
        self.btn_transferir.setStyleSheet(f"""
            QPushButton#btnTransferir {{
                background-color: {p['accent']};
                color: white;
                font-weight: 800;
                padding: 10px 18px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton#btnTransferir:hover {{
                background-color: {p['accent_hover']};
            }}
            QPushButton#btnTransferir:disabled {{
                background-color: {p['border']};
                color: {p['muted']};
            }}
        """)
        self.carregar_dados()

    def verificar_colunas_banco(self):
        colunas = {coluna.lower() for coluna in get_table_columns("itens")}

        if 'em_uso' not in colunas:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE itens ADD COLUMN em_uso INTEGER DEFAULT 0")
            conn.commit()
            conn.close()
        if 'em_manutencao' not in colunas:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE itens ADD COLUMN em_manutencao INTEGER DEFAULT 0")
            conn.commit()
            conn.close()

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_dados()

    def carregar_dados(self):
        self.cb_item.blockSignals(True)
        self.cb_item.clear()
        self.tabela.setRowCount(0)
        self.itens_cache = {}

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id_item,
                nome,
                COALESCE(quantidade, 0),
                COALESCE(em_uso, 0),
                COALESCE(em_manutencao, 0)
            FROM itens
            ORDER BY nome
        """)
        itens = cursor.fetchall()
        conn.close()

        total_estoque = 0
        total_uso = 0
        total_manutencao = 0
        alertas_cobertura = 0
        p = palette(self.dark_mode)

        for row_idx, (id_item, nome, estoque, uso, manutencao) in enumerate(itens):
            estoque = int(estoque or 0)
            uso = int(uso or 0)
            manutencao = int(manutencao or 0)
            total = estoque + uso + manutencao

            self.itens_cache[id_item] = {
                "nome": nome,
                "quantidade": estoque,
                "em_uso": uso,
                "em_manutencao": manutencao,
            }
            self.cb_item.addItem(f"{nome}", id_item)

            total_estoque += estoque
            total_uso += uso
            total_manutencao += manutencao

            cobertura_texto, cobertura_cor, cobertura_fundo, falta = self.descrever_cobertura(estoque, uso)
            if falta > 0:
                alertas_cobertura += 1

            self.tabela.insertRow(row_idx)
            valores = [
                (nome, p["text"], None, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                (str(estoque), p["accent"], None, Qt.AlignmentFlag.AlignCenter),
                (str(uso), p["good"], None, Qt.AlignmentFlag.AlignCenter),
                (str(manutencao), p["warning"], None, Qt.AlignmentFlag.AlignCenter),
                (str(total), p["muted"], None, Qt.AlignmentFlag.AlignCenter),
                (cobertura_texto, cobertura_cor, cobertura_fundo, Qt.AlignmentFlag.AlignCenter),
            ]

            for col_idx, (texto, cor, fundo, alinhamento) in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setForeground(QBrush(QColor(cor)))
                item.setTextAlignment(alinhamento)
                if col_idx in (1, 2, 3, 4, 5):
                    fonte = item.font()
                    fonte.setBold(True)
                    item.setFont(fonte)
                if fundo:
                    item.setBackground(QBrush(QColor(fundo)))
                self.tabela.setItem(row_idx, col_idx, item)

        self.cb_item.blockSignals(False)

        self.lbl_total_estoque.setText(str(total_estoque))
        self.lbl_total_uso.setText(str(total_uso))
        self.lbl_total_manutencao.setText(str(total_manutencao))
        self.lbl_total_alertas.setText(str(alertas_cobertura))
        # Mantém a lógica atual de cobertura no card superior,
        # mas deixa o texto coerente com o título quando não houver faltas.
        self.lbl_desc_alertas.setText(
            "itens faltando cobertura" if alertas_cobertura else "estoque cobre a meta"
        )


        self.tabela.resizeRowsToContents()
        self.atualizar_saldo_origem()

    def descrever_cobertura(self, estoque, uso):
        p = palette(self.dark_mode)
        if uso <= 0:
            return "Sem uso", "#64748B", None, 0

        necessario = math.ceil(uso / 10)
        falta = max(0, necessario - estoque)
        if falta > 0:
            return f"Falta {falta} p/ 10%", p["danger"], p["danger_bg"], falta
        return "Cobre 10%", p["good"], p["ok_bg"], 0

    def atualizar_saldo_origem(self):
        if not hasattr(self, "cb_item") or self.cb_item.count() == 0:
            if hasattr(self, "btn_transferir"):
                self.btn_transferir.setEnabled(False)
            return

        id_item = self.cb_item.currentData()
        origem = self.cb_origem.currentText()
        destino = self.cb_destino.currentText()
        p = palette(self.dark_mode)
        mapa_colunas = {
            "Estoque Geral": "quantidade",
            "Em Uso": "em_uso",
            "Manutenção": "em_manutencao",
        }

        item = self.itens_cache.get(id_item, {})
        saldo = int(item.get(mapa_colunas.get(origem, "quantidade"), 0) or 0)
        self.lbl_saldo_origem.setText(f"Saldo em {origem}: {saldo} unidade(s)")
        self.spin_qtd.setMaximum(max(1, saldo))

        origem_valida = origem != destino
        tem_saldo = saldo > 0
        self.btn_transferir.setEnabled(origem_valida and tem_saldo)

        if not origem_valida:
            self.lbl_dica_transferencia.setText("Escolha origem e destino diferentes para liberar a transferência.")
            self.lbl_dica_transferencia.setStyleSheet(f"color: {p['danger']}; font-size: 12px; border: none; background: transparent;")
        elif not tem_saldo:
            self.lbl_dica_transferencia.setText("A origem selecionada está sem saldo para este item.")
            self.lbl_dica_transferencia.setStyleSheet(f"color: {p['danger']}; font-size: 12px; border: none; background: transparent;")
        else:
            self.lbl_dica_transferencia.setText("Pronto para transferir. A tabela será atualizada automaticamente.")
            self.lbl_dica_transferencia.setStyleSheet(f"color: {p['good']}; font-size: 12px; border: none; background: transparent;")

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

        mapa_colunas = {
            "Estoque Geral": "quantidade",
            "Em Uso": "em_uso",
            "Manutenção": "em_manutencao",
        }

        coluna_origem = mapa_colunas[origem]
        coluna_destino = mapa_colunas[destino]

        conn = connect()
        cursor = conn.cursor()

        cursor.execute(f"SELECT COALESCE({coluna_origem}, 0) FROM itens WHERE id_item = ?", (id_item,))
        resultado = cursor.fetchone()
        qtd_disponivel = int(resultado[0] if resultado else 0)

        if qtd_transferir > qtd_disponivel:
            QMessageBox.critical(
                self,
                "Erro",
                f"Quantidade insuficiente em '{origem}'. Disponível: {qtd_disponivel}"
            )
            conn.close()
            return

        cursor.execute(
            f"""
            UPDATE itens
            SET
                {coluna_origem} = COALESCE({coluna_origem}, 0) - ?,
                {coluna_destino} = COALESCE({coluna_destino}, 0) + ?
            WHERE id_item = ?
            """,
            (qtd_transferir, qtd_transferir, id_item)
        )

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Sucesso", "Transferência realizada com sucesso!")
        self.spin_qtd.setValue(1)

        # Mantém o item selecionado após recarregar os dados
        id_item_atual = id_item

        # Recarrega a tela e o banco
        self.carregar_dados()

        # Restaura seleção no combobox pelo id
        idx_restaurar = -1
        for i in range(self.cb_item.count()):
            if self.cb_item.itemData(i) == id_item_atual:
                idx_restaurar = i
                break
        if idx_restaurar != -1:
            self.cb_item.setCurrentIndex(idx_restaurar)

    def aplicar_sombra(self, widget, blur=14, opacity=18):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(17, 24, 39, opacity))
        widget.setGraphicsEffect(shadow)
