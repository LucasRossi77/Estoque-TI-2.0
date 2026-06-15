import os
import math
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QGridLayout, QComboBox, QPushButton,
    QDialog, QScrollArea, QListWidget, QListWidgetItem, QTextBrowser
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QCursor

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from database.connection import connect, get_table_columns
from ui.theme import apply_shadow, button_style, card_style, como_usar_section_style, header_banner_style, input_style, palette, step_card_style, table_style

# ==========================================
# DIALOG POP-UP PARA MOSTRAR AS CAIXAS (DRILL-DOWN)
# ==========================================
class DialogoCaixas(QDialog):
    def __init__(self, localizacao, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Distribuição de Caixas - {localizacao}")
        self.setFixedSize(600, 450)
        self.setStyleSheet("background-color: #F6F4EF;")
        
        layout = QVBoxLayout(self)
        titulo = QLabel(f"Caixas na localização: {localizacao}")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#F6F4EF') 
        ax = fig.add_subplot(111)
        ax.set_facecolor('#F6F4EF')

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT caixa, SUM(quantidade) FROM itens 
            WHERE localizacao = ? AND caixa IS NOT NULL AND caixa != ''
            GROUP BY caixa ORDER BY SUM(quantidade) DESC
        """, (localizacao,))
        dados = cursor.fetchall()
        conn.close()

        if not dados:
            ax.text(0.5, 0.5, 'Nenhuma caixa cadastrada nesta localização', 
                    horizontalalignment='center', verticalalignment='center')
            ax.axis('off')
        else:
            nomes = [linha[0] for linha in dados]
            quantidades = [linha[1] for linha in dados]
            ax.bar(nomes, quantidades, color='#8B5CF6', width=0.5, zorder=3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#D1D5DB')
            ax.spines['bottom'].set_color('#D1D5DB')
            ax.grid(axis='y', linestyle='--', alpha=0.6, color='#E5E7EB', zorder=0)
            ax.tick_params(axis='x', colors='#4B5563', rotation=20)
            ax.tick_params(axis='y', colors='#4B5563')

        fig.tight_layout()
        fig.subplots_adjust(bottom=0.25) # Garante que o texto de baixo não corte
        canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(canvas)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_fechar.setStyleSheet("""
            QPushButton { background-color: #374151; color: white; border-radius: 6px; padding: 8px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #1F2937; }
        """)
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignmentFlag.AlignCenter)


# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================
class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.titulos_grafico = []
        self.pizza_start_angle = 90
        self.pizza_anim_frame = 0
        self.pizza_anim_total = 24
        self.pizza_anim_from = 90
        self.pizza_anim_to = 450
        self.pizza_dados = []
        self.pizza_caixas = []
        self.pizza_canvas = None
        self.pizza_fig = None
        self.pizza_ax = None
        self.localizacao_pizza_selecionada = None
        self.pizza_timer = QTimer(self)
        self.pizza_timer.setInterval(18)
        self.pizza_timer.timeout.connect(self.animar_pizza)
        self.verificar_colunas_banco()
        
        # --- ESTRUTURA DE ROLAMENTO (SCROLL AREA) ---
        layout_base = QVBoxLayout(self)
        layout_base.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # Permite que o conteúdo cresça livremente
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F6F4EF; }")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #F6F4EF;")
        
        self.layout_principal = QVBoxLayout(self.content_widget)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_principal.setContentsMargins(30, 20, 30, 30) # Espaço extra no final
        self.layout_principal.setSpacing(20)

        # Adiciona o conteúdo na área de scroll
        self.scroll_area.setWidget(self.content_widget)
        layout_base.addWidget(self.scroll_area)

        # --- CABEÇALHO ---
        self.layout_principal.addWidget(self.criar_cabecalho())
        self.layout_principal.addWidget(self.criar_cards_como_usar())

        # --- BARRA DE FILTROS ---
        self.criar_barra_filtros()

        # --- CARDS DE KPI ---
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(20)
        self.card_total, self.lbl_val_total = self.criar_card_kpi("ITENS CADASTRADOS", "#3B82F6")
        self.card_pecas, self.lbl_val_pecas = self.criar_card_kpi("UNIDADES EM ESTOQUE", "#3B82F6") 
        self.card_alerta, self.lbl_val_alerta = self.criar_card_kpi("ESTOQUE BAIXO", "#EF4444")
        layout_kpis.addWidget(self.card_total)
        layout_kpis.addWidget(self.card_pecas)
        layout_kpis.addWidget(self.card_alerta)
        self.layout_principal.addLayout(layout_kpis)

        layout_kpis_operacional = QHBoxLayout()
        layout_kpis_operacional.setSpacing(20)
        self.card_uso, self.lbl_val_uso = self.criar_card_kpi("UNIDADES EM USO", "#059669")
        self.card_manutencao, self.lbl_val_manutencao = self.criar_card_kpi("UNIDADES EM MANUTENÇÃO", "#D97706")
        self.card_cobertura, self.lbl_val_cobertura = self.criar_card_kpi("FALTA PARA 10% DO USO", "#DC2626")
        layout_kpis_operacional.addWidget(self.card_uso)
        layout_kpis_operacional.addWidget(self.card_manutencao)
        layout_kpis_operacional.addWidget(self.card_cobertura)
        self.layout_principal.addLayout(layout_kpis_operacional)

        # --- GRÁFICOS (GRID LAYOUT) ---
        layout_graficos = QGridLayout()
        layout_graficos.setSpacing(20)
        
        self.frame_baixo, self.layout_canvas_baixo = self.criar_frame_grafico("Top 5 - Estoque Baixo")
        self.frame_alto, self.layout_canvas_alto = self.criar_frame_grafico("Top 5 - Maior Volume")
        self.frame_operacional, self.layout_canvas_operacional = self.criar_frame_grafico("Estoque x Em Uso x Manutenção")
        self.frame_cobertura, self.layout_canvas_cobertura = self.criar_frame_grafico("Cobertura do Estoque para 10% do Uso")
        self.frame_local, self.layout_canvas_local = self.criar_frame_grafico("Distribuição por Localização (Clique na fatia)")
        self.frame_mov, self.layout_canvas_mov = self.criar_frame_grafico("Movimentações no Período (Entradas vs Saídas)")

        layout_graficos.addWidget(self.frame_baixo, 0, 0)
        layout_graficos.addWidget(self.frame_alto, 0, 1)
        layout_graficos.addWidget(self.frame_local, 1, 0) 
        layout_graficos.addWidget(self.frame_mov, 1, 1) 
        layout_graficos.addWidget(self.frame_operacional, 2, 0)
        layout_graficos.addWidget(self.frame_cobertura, 2, 1)

        self.layout_principal.addLayout(layout_graficos)

        # --- SEÇÃO DETALHES DE ITENS ---
        self.criar_secao_lista_itens()
        
        self.carregar_opcoes_filtros()
        self.atualizar_dashboard()
        self.aplicar_tema(False)

    def criar_cabecalho(self):
        self.header = QFrame()
        self.header.setObjectName("headerGraficos")
        layout = QVBoxLayout(self.header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)

        self.lbl_header_titulo = QLabel("Gráficos e Indicadores")
        self.lbl_header_titulo.setObjectName("headerTitulo")
        self.lbl_header_subtitulo = QLabel(
            "Veja o estoque, uso, manutenção e cobertura operacional com filtros por localização e caixa."
        )
        self.lbl_header_subtitulo.setObjectName("headerSubtitulo")
        self.lbl_header_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_header_titulo)
        layout.addWidget(self.lbl_header_subtitulo)
        apply_shadow(self.header)
        return self.header

    def criar_cards_como_usar(self):
        self.frame_como_usar = QFrame()
        self.frame_como_usar.setObjectName("comoUsarGraficos")
        layout = QVBoxLayout(self.frame_como_usar)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        self.lbl_como_titulo = QLabel("Como usar esta tela")
        self.lbl_como_titulo.setObjectName("comoTitulo")
        self.lbl_como_subtitulo = QLabel(
            "Acompanhe os indicadores gerais e use os gráficos para encontrar falta de cobertura."
        )
        self.lbl_como_subtitulo.setObjectName("comoSubtitulo")
        self.lbl_como_subtitulo.setWordWrap(True)
        layout.addWidget(self.lbl_como_titulo)
        layout.addWidget(self.lbl_como_subtitulo)

        grid = QGridLayout()
        grid.setSpacing(12)
        passos = [
            ("1", "Filtre", "Refine por período, localização ou caixa."),
            ("2", "Compare", "Veja estoque, uso e manutenção lado a lado."),
            ("3", "Priorize", "O gráfico de cobertura aponta quando falta estoque para 10% do uso."),
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

    def criar_secao_lista_itens(self):
        lbl_titulo_lista = QLabel("Catálogo e Detalhes dos Itens")
        lbl_titulo_lista.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937; margin-top: 20px; background: transparent;")
        self.layout_principal.addWidget(lbl_titulo_lista)

        layout_detalhes = QHBoxLayout()
        layout_detalhes.setSpacing(15)

        # Lista na Esquerda
        self.lista_itens = QListWidget()
        self.lista_itens.setFixedWidth(280)
        self.lista_itens.setMinimumHeight(250)
        self.lista_itens.setStyleSheet("""
            QListWidget { background-color: white; border-radius: 8px; border: 1px solid #D1D5DB; padding: 5px; font-size: 13px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #F3F4F6; }
            QListWidget::item:selected { background-color: #3B82F6; color: white; border-radius: 4px; }
            QListWidget::item:hover:!selected { background-color: #EFF6FF; }
        """)
        self.lista_itens.itemClicked.connect(self.mostrar_detalhes_item)
        
        # Painel de Detalhes na Direita (Usando QTextBrowser para ler HTML)
        self.painel_detalhes = QTextBrowser()
        self.painel_detalhes.setMinimumHeight(250)
        self.painel_detalhes.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #D1D5DB; padding: 15px; font-size: 14px;")

        layout_detalhes.addWidget(self.lista_itens)
        layout_detalhes.addWidget(self.painel_detalhes)
        
        self.layout_principal.addLayout(layout_detalhes)

    def atualizar_lista_itens(self, where_itens, params_itens):
        self.lista_itens.clear()
        self.painel_detalhes.setHtml("<p style='color: #6B7280; text-align: center; margin-top: 60px;'>Selecione um item na lista ao lado para ver todas as suas informações e movimentações.</p>")
        
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id_item, nome FROM itens {where_itens} ORDER BY nome", params_itens)
        for row in cursor.fetchall():
            item = QListWidgetItem(row[1])
            # Guardamos o ID do item "invisível" dentro da linha
            item.setData(Qt.ItemDataRole.UserRole, row[0])
            self.lista_itens.addItem(item)
        conn.close()

    def mostrar_detalhes_item(self, item):
        id_item = item.data(Qt.ItemDataRole.UserRole)
        
        conn = connect()
        cursor = conn.cursor()
        
        # Busca detalhes do Item
        cursor.execute(
            """
            SELECT
                nome,
                quantidade,
                quantidade_minima,
                localizacao,
                caixa,
                COALESCE(em_uso, 0),
                COALESCE(em_manutencao, 0)
            FROM itens
            WHERE id_item = ?
            """,
            (id_item,)
        )
        item_data = cursor.fetchone()
        
        # Busca Histórico do Item
        cursor.execute("SELECT tipo, quantidade, data, observacao FROM movimentacoes WHERE id_item = ? ORDER BY data DESC", (id_item,))
        movs_data = cursor.fetchall()
        
        conn.close()

        if not item_data: return

        p = palette(self.dark_mode)
        nome, qtd, qtd_min, loc, caixa, em_uso, em_manutencao = item_data
        qtd = qtd or 0
        qtd_min = qtd_min or 0
        em_uso = em_uso or 0
        em_manutencao = em_manutencao or 0
        meta_cobertura = math.ceil(em_uso / 2)
        falta_cobertura = max(0, meta_cobertura - qtd)
        texto_cobertura = (
            f"<span style='color: #B91C1C; font-weight: bold;'>Falta {falta_cobertura} para cobrir 10% do uso</span>"
            if falta_cobertura > 0
            else "<span style='color: #047857; font-weight: bold;'>Cobertura OK para 10% do uso</span>"
        )
        loc = loc if loc else "Não Definida"
        caixa = caixa if caixa else "Não Definida"

        cor_qtd = "#EF4444" if qtd_min > 0 and qtd <= qtd_min else "#10B981"
        texto_minimo = qtd_min if qtd_min > 0 else "sem mínimo"

        html = f"""
        <h2 style='color: {p['text']}; margin-bottom: 5px;'>{nome}</h2>
        <p style='margin-top: 0px;'>
            <b>Quantidade Atual:</b> <span style='color: {cor_qtd}; font-weight: bold;'>{qtd}</span> 
            (Mínimo: {texto_minimo})
        </p>
        <p>
            <b>Operacional:</b> <span style='color: #059669; font-weight: bold;'>{em_uso}</span> em uso
            &nbsp;&nbsp;|&nbsp;&nbsp;
            <span style='color: #D97706; font-weight: bold;'>{em_manutencao}</span> em manutenção
            &nbsp;&nbsp;|&nbsp;&nbsp; {texto_cobertura}
        </p>
        <p><b>📍 Localização:</b> {loc} &nbsp;&nbsp;|&nbsp;&nbsp; <b>📦 Caixa:</b> {caixa}</p>
        <hr style='border: 1px solid {p['border']};'>
        <h3 style='color: {p['text']};'>Histórico de Movimentações (Total: {len(movs_data)})</h3>
        """

        if not movs_data:
            html += f"<p style='color: {p['muted']};'>Nenhuma movimentação registrada para este item ainda.</p>"
        else:
            html += "<ul style='padding-left: 20px;'>"
            for m in movs_data:
                tipo, q_mov, data_mov, obs = m
                cor_tipo = "#10B981" if tipo == "ENTRADA" else "#EF4444"
                obs_text = f" - <i>Obs: {obs}</i>" if obs else ""
                
                # Corta os milissegundos da data se houver
                data_limpa = data_mov.split(".")[0] if data_mov else "Data Desconhecida"

                html += f"<li><b>{data_limpa}</b>: <span style='color: {cor_tipo};'><b>{tipo}</b> ({q_mov} un)</span>{obs_text}</li>"
            html += "</ul>"

        self.painel_detalhes.setHtml(html)

    # ==========================================
    # FILTROS
    # ==========================================
    def criar_barra_filtros(self):
        frame_filtros = QFrame()
        self.frame_filtros = frame_filtros
        frame_filtros.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E5E7EB;")
        self.aplicar_sombra(frame_filtros)
        
        layout = QHBoxLayout(frame_filtros)
        layout.setContentsMargins(15, 10, 15, 10)
        
        estilo_combo = "QComboBox { border: 1px solid #D1D5DB; border-radius: 4px; padding: 5px; background: white; } QComboBox::drop-down { border: none; }"
        
        self.combo_periodo = QComboBox()
        self.combo_periodo.setStyleSheet(estilo_combo)
        self.combo_periodo.addItems(["Todo o Período", "Hoje", "Última Semana", "Último Mês"])
        
        self.combo_loc = QComboBox()
        self.combo_loc.setStyleSheet(estilo_combo)
        
        self.combo_caixa = QComboBox()
        self.combo_caixa.setStyleSheet(estilo_combo)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_filtrar.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold;")
        self.btn_filtrar.clicked.connect(self.atualizar_dashboard)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_limpar.setStyleSheet("background-color: #9CA3AF; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold;")
        self.btn_limpar.clicked.connect(self.limpar_filtros)

        layout.addWidget(QLabel("Período:"))
        layout.addWidget(self.combo_periodo)
        layout.addWidget(QLabel("Localização:"))
        layout.addWidget(self.combo_loc)
        layout.addWidget(QLabel("Caixa:"))
        layout.addWidget(self.combo_caixa)
        layout.addWidget(self.btn_filtrar)
        layout.addWidget(self.btn_limpar)
        layout.addStretch()

        self.layout_principal.addWidget(frame_filtros)

    def carregar_opcoes_filtros(self):
        conn = connect()
        cursor = conn.cursor()
        
        self.combo_loc.blockSignals(True)
        self.combo_caixa.blockSignals(True)

        self.combo_loc.clear()
        self.combo_loc.addItem("Todas as Local")
        cursor.execute("SELECT DISTINCT localizacao FROM itens WHERE localizacao IS NOT NULL AND localizacao != ''")
        for row in cursor.fetchall(): self.combo_loc.addItem(row[0])

        self.combo_caixa.clear()
        self.combo_caixa.addItem("Todas as Caixas")
        cursor.execute("SELECT DISTINCT caixa FROM itens WHERE caixa IS NOT NULL AND caixa != ''")
        for row in cursor.fetchall(): self.combo_caixa.addItem(row[0])

        self.combo_loc.blockSignals(False)
        self.combo_caixa.blockSignals(False)
        conn.close()

    def limpar_filtros(self):
        self.combo_periodo.setCurrentIndex(0)
        self.combo_loc.setCurrentIndex(0)
        self.combo_caixa.setCurrentIndex(0)
        self.atualizar_dashboard()

    def aplicar_tema(self, dark=False):
        mudou = self.dark_mode != dark
        self.dark_mode = dark
        p = palette(dark)
        self.setStyleSheet(f"background-color: {p['bg']}; color: {p['text']};")
        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background-color: {p['bg']}; }}")
        self.content_widget.setStyleSheet(f"background-color: {p['bg']};")
        self.header.setStyleSheet(header_banner_style("headerGraficos", dark))
        self.frame_como_usar.setStyleSheet(como_usar_section_style(dark))
        for card in self.frame_como_usar.findChildren(QFrame, "cardPasso"):
            card.setStyleSheet(step_card_style(dark))

        self.frame_filtros.setStyleSheet(card_style(dark))
        for combo in [self.combo_periodo, self.combo_loc, self.combo_caixa]:
            combo.setStyleSheet(input_style(dark))
        self.btn_filtrar.setStyleSheet(button_style("primary", dark))
        self.btn_limpar.setStyleSheet(button_style("muted", dark))
        for frame in [
            self.card_total, self.card_pecas, self.card_alerta, self.card_uso,
            self.card_manutencao, self.card_cobertura, self.frame_baixo,
            self.frame_alto, self.frame_local, self.frame_mov,
            self.frame_operacional, self.frame_cobertura
        ]:
            frame.setStyleSheet(card_style(dark))
            apply_shadow(frame, dark)
        for label in [
            self.lbl_val_total, self.lbl_val_pecas, self.lbl_val_alerta,
            self.lbl_val_uso, self.lbl_val_manutencao, self.lbl_val_cobertura
        ]:
            label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {p['text']}; border: none; background-color: transparent;")
        for label in self.titulos_grafico:
            label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {p['text']}; border: none; background-color: transparent;")
        self.lista_itens.setStyleSheet(f"""
            QListWidget {{
                background-color: {p['card']};
                color: {p['text']};
                border-radius: 8px;
                border: 1px solid {p['border']};
                padding: 5px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {p['border']};
            }}
            QListWidget::item:selected {{
                background-color: {p['accent']};
                color: white;
                border-radius: 4px;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {p['soft']};
            }}
        """)
        self.painel_detalhes.setStyleSheet(
            f"background-color: {p['card']}; color: {p['text']}; border-radius: 8px; "
            f"border: 1px solid {p['border']}; padding: 15px; font-size: 14px;"
        )
        apply_shadow(self.header, dark, blur=18)
        apply_shadow(self.frame_como_usar, dark, blur=18)
        if mudou and hasattr(self, "layout_canvas_baixo"):
            self.atualizar_dashboard()

    # ==========================================
    # ATUALIZAÇÃO E DADOS
    # ==========================================
    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_opcoes_filtros()
        self.atualizar_dashboard()

    def limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

    def atualizar_dashboard(self):
        if self.pizza_timer.isActive():
            self.pizza_timer.stop()

        loc = self.combo_loc.currentText()
        caixa = self.combo_caixa.currentText()
        periodo = self.combo_periodo.currentText()

        filtros_itens = []
        params_itens = []
        if loc != "Todas as Local":
            filtros_itens.append("localizacao = ?")
            params_itens.append(loc)
        if caixa != "Todas as Caixas":
            filtros_itens.append("caixa = ?")
            params_itens.append(caixa)
        
        where_itens = ""
        if filtros_itens:
            where_itens = "WHERE " + " AND ".join(filtros_itens)

        conn = connect()
        cursor = conn.cursor()
        
        # 1. KPIs
        cursor.execute(f"SELECT COUNT(id_item) FROM itens {where_itens}", params_itens)
        self.lbl_val_total.setText(str(cursor.fetchone()[0] or 0))
        
        cursor.execute(f"SELECT SUM(quantidade) FROM itens {where_itens}", params_itens)
        self.lbl_val_pecas.setText(str(cursor.fetchone()[0] or 0))
        
        sql_alerta = "COALESCE(quantidade_minima, 0) > 0 AND quantidade <= quantidade_minima"
        if where_itens:
            cursor.execute(f"SELECT COUNT(id_item) FROM itens {where_itens} AND {sql_alerta}", params_itens)
        else:
            cursor.execute(f"SELECT COUNT(id_item) FROM itens WHERE {sql_alerta}")
        self.lbl_val_alerta.setText(str(cursor.fetchone()[0] or 0))

        cursor.execute(
            f"""
            SELECT
                COALESCE(SUM(em_uso), 0),
                COALESCE(SUM(em_manutencao), 0)
            FROM itens {where_itens}
            """,
            params_itens
        )
        total_uso, total_manutencao = cursor.fetchone()
        self.lbl_val_uso.setText(str(total_uso or 0))
        self.lbl_val_manutencao.setText(str(total_manutencao or 0))

        cursor.execute(
            f"SELECT COALESCE(quantidade, 0), COALESCE(em_uso, 0) FROM itens {where_itens}",
            params_itens
        )
        unidades_faltantes = 0
        for estoque, uso in cursor.fetchall():
            _, falta = self.calcular_cobertura(estoque, uso)
            unidades_faltantes += falta
        self.lbl_val_cobertura.setText(str(unidades_faltantes))
        conn.close()

        # 2. Gráficos
        self.limpar_layout(self.layout_canvas_baixo)
        self.layout_canvas_baixo.addWidget(self.criar_grafico_barras('ASC', '#EF4444', where_itens, params_itens))
        
        self.limpar_layout(self.layout_canvas_alto)
        self.layout_canvas_alto.addWidget(self.criar_grafico_barras('DESC', '#10B981', where_itens, params_itens))
        
        self.limpar_layout(self.layout_canvas_local)
        self.layout_canvas_local.addWidget(self.criar_grafico_pizza(where_itens, params_itens))

        self.limpar_layout(self.layout_canvas_mov)
        self.layout_canvas_mov.addWidget(self.criar_grafico_movimentacoes(periodo))

        self.limpar_layout(self.layout_canvas_operacional)
        self.layout_canvas_operacional.addWidget(self.criar_grafico_operacional(where_itens, params_itens))

        self.limpar_layout(self.layout_canvas_cobertura)
        self.layout_canvas_cobertura.addWidget(self.criar_grafico_cobertura_uso(where_itens, params_itens))

        # 3. Atualizar Lista de Itens
        self.atualizar_lista_itens(where_itens, params_itens)

    # ==========================================
    # GERAÇÃO DOS GRÁFICOS
    # ==========================================
    def cores_grafico(self):
        p = palette(self.dark_mode)
        return {
            "bg": p["card"],
            "text": p["text"],
            "muted": p["muted"],
            "grid": p["border"],
            "axis": p["border"],
        }

    def encurtar_nome(self, nome, limite=22):
        nome = str(nome or "Sem nome")
        return nome if len(nome) <= limite else nome[:limite - 3] + "..."

    def estilizar_eixos(self, ax):
        c = self.cores_grafico()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(c["axis"])
        ax.spines['bottom'].set_color(c["axis"])
        ax.grid(axis='x', linestyle='--', alpha=0.45, color=c["grid"], zorder=0)
        ax.tick_params(axis='x', colors=c["muted"], labelsize=8)
        ax.tick_params(axis='y', colors=c["text"], labelsize=8)

    def canvas_sem_dados(self, mensagem):
        c = self.cores_grafico()
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(c["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])
        ax.text(0.5, 0.5, mensagem, horizontalalignment='center', verticalalignment='center', color=c["muted"])
        ax.axis('off')
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(300)
        return canvas

    def calcular_cobertura(self, estoque, uso):
        estoque = int(estoque or 0)
        uso = int(uso or 0)
        meta = math.ceil(uso / 2)
        falta = max(0, meta - estoque)
        return meta, falta

    def criar_grafico_operacional(self, where_itens, params_itens):
        c = self.cores_grafico()
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(c["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])

        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                nome,
                COALESCE(quantidade, 0),
                COALESCE(em_uso, 0),
                COALESCE(em_manutencao, 0)
            FROM itens {where_itens}
            ORDER BY (
                COALESCE(quantidade, 0) +
                COALESCE(em_uso, 0) +
                COALESCE(em_manutencao, 0)
            ) DESC
            LIMIT 8
            """,
            params_itens
        )
        dados = cursor.fetchall()
        conn.close()

        if not dados:
            return self.canvas_sem_dados("Sem itens para comparar")

        dados = list(reversed(dados))
        nomes = [self.encurtar_nome(row[0]) for row in dados]
        estoque = [int(row[1] or 0) for row in dados]
        uso = [int(row[2] or 0) for row in dados]
        manutencao = [int(row[3] or 0) for row in dados]
        posicoes = list(range(len(dados)))

        ax.barh(posicoes, estoque, color='#3B82F6', label='Estoque', zorder=3)
        ax.barh(posicoes, uso, left=estoque, color='#10B981', label='Em uso', zorder=3)
        esquerda_manut = [e + u for e, u in zip(estoque, uso)]
        ax.barh(posicoes, manutencao, left=esquerda_manut, color='#F59E0B', label='Manutenção', zorder=3)

        totais = [e + u + m for e, u, m in zip(estoque, uso, manutencao)]
        max_total = max(totais) if totais else 1
        for idx, total in enumerate(totais):
            if total > 0:
                ax.text(total + max_total * 0.02, idx, str(total), va='center', fontsize=8, color=c["text"])

        ax.set_yticks(posicoes)
        ax.set_yticklabels(nomes)
        legend = ax.legend(loc='lower right', fontsize=8, frameon=False)
        for text in legend.get_texts():
            text.set_color(c["text"])
        self.estilizar_eixos(ax)

        fig.tight_layout()
        fig.subplots_adjust(left=0.32, right=0.96)
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(300)
        return canvas

    def criar_grafico_cobertura_uso(self, where_itens, params_itens):
        c = self.cores_grafico()
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(c["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])

        where_uso = "WHERE COALESCE(em_uso, 0) > 0"
        if where_itens:
            where_uso = where_itens + " AND COALESCE(em_uso, 0) > 0"

        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                nome,
                COALESCE(quantidade, 0),
                COALESCE(em_uso, 0)
            FROM itens {where_uso}
            """,
            params_itens
        )
        dados = cursor.fetchall()
        conn.close()

        if not dados:
            return self.canvas_sem_dados("Nenhum item está marcado como em uso")

        calculados = []
        for nome, estoque, uso in dados:
            estoque = int(estoque or 0)
            uso = int(uso or 0)
            meta, falta = self.calcular_cobertura(estoque, uso)
            calculados.append({
                "nome": nome,
                "estoque": estoque,
                "uso": uso,
                "meta": meta,
                "falta": falta,
            })

        total_falta = sum(item["falta"] for item in calculados)
        calculados = [item for item in calculados if item["falta"] > 0]
        if not calculados:
            return self.canvas_sem_dados("Todos os itens cobrem 10% do uso")

        calculados.sort(key=lambda item: (item["falta"], item["uso"]), reverse=True)
        calculados = list(reversed(calculados[:8]))

        nomes = [self.encurtar_nome(item["nome"]) for item in calculados]
        faltas = [item["falta"] for item in calculados]

        posicoes = list(range(len(calculados)))
        ax.barh(posicoes, faltas, color='#DC2626', zorder=3)

        maior_valor = max(faltas) if faltas else 1
        for idx, item in enumerate(calculados):
            texto = f"Estoque {item['estoque']} / meta {item['meta']}"
            x = item["falta"] + maior_valor * 0.04
            ax.text(x, idx, texto, va='center', fontsize=8, color=c["text"], fontweight='bold')

        ax.set_yticks(posicoes)
        ax.set_yticklabels(nomes)
        ax.set_xlabel("Unidades faltantes", color=c["muted"], fontsize=8)
        ax.text(
            0,
            1.04,
            f"Total faltando no filtro: {total_falta}",
            transform=ax.transAxes,
            color=c["muted"],
            fontsize=9,
            fontweight='bold',
            va='bottom',
        )
        ax.set_xlim(0, maior_valor * 1.45)
        self.estilizar_eixos(ax)

        fig.tight_layout()
        fig.subplots_adjust(left=0.32, right=0.96)
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(300)
        return canvas

    def criar_grafico_barras(self, ordem, cor_barra, where_itens, params_itens):
        c = self.cores_grafico()
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(c["bg"]) 
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])

        conn = connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT nome, quantidade FROM itens {where_itens} ORDER BY quantidade {ordem} LIMIT 5", params_itens)
        dados = cursor.fetchall()
        conn.close()

        nomes = [linha[0] for linha in dados] if dados else ["Sem dados"]
        quantidades = [linha[1] for linha in dados] if dados else [0]

        ax.bar(nomes, quantidades, color=cor_barra, width=0.6, zorder=3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(c["axis"])
        ax.spines['bottom'].set_color(c["axis"])
        ax.grid(axis='y', linestyle='--', alpha=0.6, color=c["grid"], zorder=0)
        
        # Ajustado a rotação para não consumir tanto espaço verticalmente e ajustado o bottom
        ax.tick_params(axis='x', colors=c["muted"], rotation=25)
        ax.tick_params(axis='y', colors=c["muted"])
        
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.3) 
        
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(280) 
        return canvas

    def criar_grafico_pizza(self, where_itens, params_itens):
        c = self.cores_grafico()
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(c["bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])

        conn = connect()
        cursor = conn.cursor()
        
        sql = "SELECT localizacao, SUM(quantidade) FROM itens WHERE localizacao IS NOT NULL AND localizacao != '' "
        if where_itens:
            sql += " AND " + where_itens.replace("WHERE ", "")
            
        sql += " GROUP BY localizacao ORDER BY SUM(quantidade) DESC LIMIT 5"
        
        cursor.execute(sql, params_itens)
        dados = cursor.fetchall()
        conn.close()

        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(280)
        self.pizza_fig = fig
        self.pizza_ax = ax
        self.pizza_canvas = canvas
        self.pizza_dados = [(linha[0], int(linha[1] or 0)) for linha in dados]
        self.localizacao_pizza_selecionada = None
        self.pizza_caixas = []

        if not self.pizza_dados:
            ax.text(0.5, 0.5, 'Sem dados no filtro', horizontalalignment='center', verticalalignment='center', color=c["muted"])
            ax.axis('off')
            return canvas

        self.desenhar_pizza_distribuicao()
        canvas.mpl_connect('pick_event', self.ao_clicar_na_pizza)
        return canvas

    def desenhar_pizza_distribuicao(self):
        if self.pizza_ax is None or self.pizza_canvas is None:
            return

        c = self.cores_grafico()
        ax = self.pizza_ax
        ax.clear()
        ax.set_facecolor(c["bg"])
        self.pizza_fig.patch.set_facecolor(c["bg"])

        labels = [linha[0] for linha in self.pizza_dados]
        valores = [linha[1] for linha in self.pizza_dados]
        cores = ['#2563EB', '#14B8A6', '#F59E0B', '#8B5CF6', '#EF4444', '#64748B']
        selecionada = self.localizacao_pizza_selecionada
        explode = [0.04 if label == selecionada else 0 for label in labels]

        def pct_label(pct):
            return f"{pct:.0f}%" if pct >= 5 else ""

        wedges, texts, autotexts = ax.pie(
            valores,
            labels=labels,
            autopct=pct_label,
            startangle=self.pizza_start_angle,
            colors=cores[:len(valores)],
            explode=explode,
            radius=1.0,
            wedgeprops=dict(width=0.31, edgecolor=c["bg"], linewidth=2),
            pctdistance=0.84,
            labeldistance=1.08,
        )

        for i, wedge in enumerate(wedges):
            wedge.set_picker(True)
            wedge.set_label(labels[i])
            if labels[i] == selecionada:
                wedge.set_linewidth(3)

        for text in texts:
            text.set_color(c["text"])
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color("#FFFFFF")
            autotext.set_fontsize(8)
            autotext.set_weight('bold')

        if selecionada:
            if self.pizza_caixas:
                caixa_labels = [self.encurtar_nome(linha[0], 14) for linha in self.pizza_caixas]
                caixa_valores = [int(linha[1] or 0) for linha in self.pizza_caixas]
                caixa_cores = ['#F97316', '#22C55E', '#06B6D4', '#A855F7', '#EAB308', '#EC4899']
                inner_wedges, inner_texts, inner_autotexts = ax.pie(
                    caixa_valores,
                    labels=caixa_labels,
                    autopct=pct_label,
                    startangle=-self.pizza_start_angle,
                    colors=caixa_cores[:len(caixa_valores)],
                    radius=0.62,
                    wedgeprops=dict(width=0.29, edgecolor=c["bg"], linewidth=2),
                    pctdistance=0.78,
                    labeldistance=0.54,
                )
                for text in inner_texts:
                    text.set_color(c["text"])
                    text.set_fontsize(8)
                for autotext in inner_autotexts:
                    autotext.set_color("#FFFFFF")
                    autotext.set_fontsize(7)
                    autotext.set_weight('bold')
                centro = f"{self.encurtar_nome(selecionada, 13)}\n{sum(caixa_valores)} un"
            else:
                centro = f"{self.encurtar_nome(selecionada, 13)}\nsem caixas"
        else:
            centro = "Clique\nna fatia"

        ax.text(
            0,
            0,
            centro,
            ha='center',
            va='center',
            color=c["text"],
            fontsize=9,
            fontweight='bold',
        )
        ax.set_aspect('equal')
        self.pizza_fig.tight_layout()
        self.pizza_canvas.draw_idle()

    def buscar_caixas_pizza(self, localizacao):
        sql = """
            SELECT caixa, SUM(quantidade)
            FROM itens
            WHERE localizacao = ? AND caixa IS NOT NULL AND caixa != ''
        """
        params = [localizacao]
        caixa = self.combo_caixa.currentText()
        if caixa != "Todas as Caixas":
            sql += " AND caixa = ?"
            params.append(caixa)
        sql += " GROUP BY caixa ORDER BY SUM(quantidade) DESC LIMIT 6"

        conn = connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        dados = cursor.fetchall()
        conn.close()
        return dados

    def ao_clicar_na_pizza(self, event):
        if hasattr(event.artist, 'get_label'):
            localizacao = event.artist.get_label()
            if localizacao and not localizacao.startswith('_'):
                self.localizacao_pizza_selecionada = localizacao
                self.pizza_caixas = self.buscar_caixas_pizza(localizacao)
                self.pizza_anim_frame = 0
                self.pizza_anim_from = self.pizza_start_angle
                self.pizza_anim_to = self.pizza_start_angle + 360
                self.desenhar_pizza_distribuicao()
                self.pizza_timer.start()

    def animar_pizza(self):
        if self.pizza_canvas is None:
            self.pizza_timer.stop()
            return

        self.pizza_anim_frame += 1
        progresso = min(1, self.pizza_anim_frame / self.pizza_anim_total)
        suavizado = 1 - (1 - progresso) ** 3
        self.pizza_start_angle = self.pizza_anim_from + (self.pizza_anim_to - self.pizza_anim_from) * suavizado
        self.desenhar_pizza_distribuicao()

        if progresso >= 1:
            self.pizza_timer.stop()
            self.pizza_start_angle = self.pizza_start_angle % 360
            self.desenhar_pizza_distribuicao()

    def criar_grafico_movimentacoes(self, periodo):
        c = self.cores_grafico()
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(c["bg"]) 
        ax = fig.add_subplot(111)
        ax.set_facecolor(c["bg"])

        where_data = ""
        params_data = []
        if periodo == "Hoje":
            inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            where_data = "WHERE data >= ?"
            params_data.append(inicio.strftime("%Y-%m-%d %H:%M:%S"))
        elif periodo == "Última Semana":
            where_data = "WHERE data >= ?"
            params_data.append((datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"))
        elif periodo == "Último Mês":
            where_data = "WHERE data >= ?"
            params_data.append((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"))

        conn = connect()
        cursor = conn.cursor()
        
        sql = f"SELECT tipo, SUM(quantidade) FROM movimentacoes {where_data} GROUP BY tipo"
        cursor.execute(sql, params_data)
        dados = cursor.fetchall()
        conn.close()

        val_entrada = 0
        val_saida = 0
        for linha in dados:
            if linha[0] == 'ENTRADA': val_entrada = linha[1]
            elif linha[0] == 'SAIDA': val_saida = linha[1]

        ax.bar(['Entradas', 'Saídas'], [val_entrada, val_saida], color=['#10B981', '#EF4444'], width=0.5, zorder=3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(c["axis"])
        ax.spines['bottom'].set_color(c["axis"])
        ax.grid(axis='y', linestyle='--', alpha=0.6, color=c["grid"], zorder=0)
        ax.tick_params(axis='x', colors=c["muted"])
        ax.tick_params(axis='y', colors=c["muted"])
        
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.2) 
        
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(280)
        return canvas

    def criar_card_kpi(self, titulo, cor_destaque):
        card = QFrame()
        card.setFixedHeight(110)
        card.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E5E7EB; }")
        self.aplicar_sombra(card)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {cor_destaque}; border: none; background-color: transparent;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_valor = QLabel("0") 
        lbl_valor.setStyleSheet("font-size: 32px; font-weight: bold; color: #1F2937; border: none; background-color: transparent;")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        return card, lbl_valor

    def criar_frame_grafico(self, titulo_texto):
        frame = QFrame()
        # Garantindo altura mínima para o card do gráfico para o texto caber
        frame.setMinimumHeight(320)
        frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E5E7EB; }")
        self.aplicar_sombra(frame)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
        titulo = QLabel(titulo_texto)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #374151; border: none; background-color: transparent;")
        self.titulos_grafico.append(titulo)
        layout.addWidget(titulo)
        
        layout_canvas = QVBoxLayout()
        layout.addLayout(layout_canvas)
        return frame, layout_canvas

    def aplicar_sombra(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        widget.setGraphicsEffect(shadow)
