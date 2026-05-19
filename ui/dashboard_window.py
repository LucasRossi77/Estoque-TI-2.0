import sqlite3
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QGridLayout, QComboBox, QPushButton,
    QDialog, QScrollArea, QListWidget, QListWidgetItem, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

try:
    from database.connection import connect
except ImportError:
    def connect():
        return sqlite3.connect('database.db')

# ==========================================
# DIALOG POP-UP PARA MOSTRAR AS CAIXAS (DRILL-DOWN)
# ==========================================
class DialogoCaixas(QDialog):
    def __init__(self, localizacao, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Distribuição de Caixas - {localizacao}")
        self.setFixedSize(600, 450)
        self.setStyleSheet("background-color: #F3EFE0;")
        
        layout = QVBoxLayout(self)
        titulo = QLabel(f"Caixas na localização: {localizacao}")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#F3EFE0') 
        ax = fig.add_subplot(111)
        ax.set_facecolor('#F3EFE0')

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
        
        # --- ESTRUTURA DE ROLAMENTO (SCROLL AREA) ---
        layout_base = QVBoxLayout(self)
        layout_base.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # Permite que o conteúdo cresça livremente
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F3EFE0; }")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #F3EFE0;")
        
        self.layout_principal = QVBoxLayout(self.content_widget)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_principal.setContentsMargins(30, 20, 30, 30) # Espaço extra no final
        self.layout_principal.setSpacing(20)

        # Adiciona o conteúdo na área de scroll
        self.scroll_area.setWidget(self.content_widget)
        layout_base.addWidget(self.scroll_area)

        # --- CABEÇALHO ---
        titulo = QLabel("Painel de Controle")
        titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #1F2937; background-color: transparent;")
        self.layout_principal.addWidget(titulo)

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

        # --- GRÁFICOS (GRID LAYOUT) ---
        layout_graficos = QGridLayout()
        layout_graficos.setSpacing(20)
        
        self.frame_baixo, self.layout_canvas_baixo = self.criar_frame_grafico("Top 5 - Estoque Baixo")
        self.frame_alto, self.layout_canvas_alto = self.criar_frame_grafico("Top 5 - Maior Volume")
        self.frame_local, self.layout_canvas_local = self.criar_frame_grafico("Distribuição por Localização (Clique na fatia)")
        self.frame_mov, self.layout_canvas_mov = self.criar_frame_grafico("Movimentações no Período (Entradas vs Saídas)")

        layout_graficos.addWidget(self.frame_baixo, 0, 0)
        layout_graficos.addWidget(self.frame_alto, 0, 1)
        layout_graficos.addWidget(self.frame_local, 1, 0) 
        layout_graficos.addWidget(self.frame_mov, 1, 1) 

        self.layout_principal.addLayout(layout_graficos)

        # --- SEÇÃO DETALHES DE ITENS ---
        self.criar_secao_lista_itens()
        
        self.carregar_opcoes_filtros()
        self.atualizar_dashboard()

    # ==========================================
    # DETALHES DOS ITENS (NOVA FUNCIONALIDADE)
    # ==========================================
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
        cursor.execute("SELECT nome, quantidade, quantidade_minima, localizacao, caixa FROM itens WHERE id_item = ?", (id_item,))
        item_data = cursor.fetchone()
        
        # Busca Histórico do Item
        cursor.execute("SELECT tipo, quantidade, data, observacao FROM movimentacoes WHERE id_item = ? ORDER BY data DESC", (id_item,))
        movs_data = cursor.fetchall()
        
        conn.close()

        if not item_data: return

        nome, qtd, qtd_min, loc, caixa = item_data
        loc = loc if loc else "Não Definida"
        caixa = caixa if caixa else "Não Definida"

        cor_qtd = "#EF4444" if qtd <= qtd_min else "#10B981" # Vermelho se baixo, Verde se ok

        html = f"""
        <h2 style='color: #1F2937; margin-bottom: 5px;'>{nome}</h2>
        <p style='margin-top: 0px;'>
            <b>Quantidade Atual:</b> <span style='color: {cor_qtd}; font-weight: bold;'>{qtd}</span> 
            (Mínimo: {qtd_min})
        </p>
        <p><b>📍 Localização:</b> {loc} &nbsp;&nbsp;|&nbsp;&nbsp; <b>📦 Caixa:</b> {caixa}</p>
        <hr style='border: 1px solid #E5E7EB;'>
        <h3 style='color: #374151;'>Histórico de Movimentações (Total: {len(movs_data)})</h3>
        """

        if not movs_data:
            html += "<p style='color: #6B7280;'>Nenhuma movimentação registrada para este item ainda.</p>"
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

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_filtrar.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold;")
        btn_filtrar.clicked.connect(self.atualizar_dashboard)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_limpar.setStyleSheet("background-color: #9CA3AF; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold;")
        btn_limpar.clicked.connect(self.limpar_filtros)

        layout.addWidget(QLabel("Período:"))
        layout.addWidget(self.combo_periodo)
        layout.addWidget(QLabel("Localização:"))
        layout.addWidget(self.combo_loc)
        layout.addWidget(QLabel("Caixa:"))
        layout.addWidget(self.combo_caixa)
        layout.addWidget(btn_filtrar)
        layout.addWidget(btn_limpar)
        layout.addStretch()

        self.layout_principal.insertWidget(1, frame_filtros)

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
        
        sql_alerta = "quantidade <= quantidade_minima"
        if where_itens:
            cursor.execute(f"SELECT COUNT(id_item) FROM itens {where_itens} AND {sql_alerta}", params_itens)
        else:
            cursor.execute(f"SELECT COUNT(id_item) FROM itens WHERE {sql_alerta}")
        self.lbl_val_alerta.setText(str(cursor.fetchone()[0] or 0))
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

        # 3. Atualizar Lista de Itens
        self.atualizar_lista_itens(where_itens, params_itens)

    # ==========================================
    # GERAÇÃO DOS GRÁFICOS
    # ==========================================
    def criar_grafico_barras(self, ordem, cor_barra, where_itens, params_itens):
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor('#FFFFFF') 
        ax = fig.add_subplot(111)
        ax.set_facecolor('#FFFFFF')

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
        ax.spines['left'].set_color('#D1D5DB')
        ax.spines['bottom'].set_color('#D1D5DB')
        ax.grid(axis='y', linestyle='--', alpha=0.6, color='#E5E7EB', zorder=0)
        
        # Ajustado a rotação para não consumir tanto espaço verticalmente e ajustado o bottom
        ax.tick_params(axis='x', colors='#4B5563', rotation=25)
        
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.3) # Isso força o matplotlib a dar mais espaço na parte inferior para o texto não cortar!
        
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(280) # Evita que o gráfico seja esmagado pelo layout da tela
        return canvas

    def criar_grafico_pizza(self, where_itens, params_itens):
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor('#FFFFFF')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#FFFFFF')

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

        if not dados:
            ax.text(0.5, 0.5, 'Sem dados no filtro', horizontalalignment='center', verticalalignment='center')
            ax.axis('off')
            return canvas

        labels = [linha[0] for linha in dados]
        valores = [linha[1] for linha in dados]
        cores = ['#3B82F6', '#60A5FA', '#93C5FD', '#8B5CF6', '#A78BFA']

        wedges, texts, autotexts = ax.pie(
            valores, labels=labels, autopct='%1.1f%%', startangle=90, 
            colors=cores, wedgeprops=dict(width=0.4, edgecolor='w') 
        )

        for i, wedge in enumerate(wedges):
            wedge.set_picker(True) 
            wedge.set_label(labels[i]) 

        for text in texts:
            text.set_color('#374151')
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('#1F2937')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')

        fig.tight_layout()
        canvas.mpl_connect('pick_event', self.ao_clicar_na_pizza)
        
        return canvas

    def ao_clicar_na_pizza(self, event):
        if hasattr(event.artist, 'get_label'):
            localizacao = event.artist.get_label()
            if localizacao and not localizacao.startswith('_'):
                dialog = DialogoCaixas(localizacao, self)
                dialog.exec()

    def criar_grafico_movimentacoes(self, periodo):
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor('#FFFFFF') 
        ax = fig.add_subplot(111)
        ax.set_facecolor('#FFFFFF')

        where_data = ""
        if periodo == "Hoje":
            where_data = "WHERE date(data) = date('now', 'localtime')"
        elif periodo == "Última Semana":
            where_data = "WHERE data >= datetime('now', '-7 days', 'localtime')"
        elif periodo == "Último Mês":
            where_data = "WHERE data >= datetime('now', '-1 month', 'localtime')"

        conn = connect()
        cursor = conn.cursor()
        
        sql = f"SELECT tipo, SUM(quantidade) FROM movimentacoes {where_data} GROUP BY tipo"
        cursor.execute(sql)
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
        ax.spines['left'].set_color('#D1D5DB')
        ax.spines['bottom'].set_color('#D1D5DB')
        ax.grid(axis='y', linestyle='--', alpha=0.6, color='#E5E7EB', zorder=0)
        
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.2) 
        
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(280)
        return canvas

    # ==========================================
    # UTILITÁRIOS DE INTERFACE
    # ==========================================
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