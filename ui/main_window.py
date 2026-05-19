import sqlite3
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
    QColor, QIcon, QPixmap, 
    QTextDocument, QPdfWriter
)

# =====================================================================
# NOVA CLASSE: VISUALIZAÇÃO EM BLOCOS (DRILL-DOWN)
# =====================================================================
class VisaoBlocosWidget(QWidget):
    def __init__(self, caminho_db, pasta_fotos):
        super().__init__()
        self.caminho_db = caminho_db
        self.pasta_fotos = pasta_fotos
        self.nivel_atual = "LOCALIZACAO"
        self.local_selecionado = ""

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

    def carregar_localizacoes(self):
        self.limpar_grid()
        self.nivel_atual = "LOCALIZACAO"
        self.lbl_caminho.setText("🏠 Todas as Localizações")
        self.btn_voltar.hide()
        
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT localizacao FROM itens WHERE localizacao IS NOT NULL AND localizacao != ''")
        locais = cursor.fetchall()
        conn.close()

        for index, (local,) in enumerate(locais):
            btn = QPushButton(f"📍\n{local}")
            # --- BLOCOS MAIORES AQUI ---
            btn.setFixedSize(180, 130) 
            btn.setStyleSheet("background-color: #223959; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, l=local: self.carregar_caixas(l))
            
            # Ajustei o divisor para 4 colunas ao invés de 5, já que os blocos ficaram maiores
            linha, coluna = divmod(index, 4)
            self.layout_grid.addWidget(btn, linha, coluna)

    def carregar_caixas(self, local):
        self.limpar_grid()
        self.nivel_atual = "CAIXA"
        self.local_selecionado = local
        self.lbl_caminho.setText(f"🏠 {local} > Selecione uma Caixa")
        self.btn_voltar.show()

        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT caixa FROM itens WHERE localizacao = ? AND caixa IS NOT NULL AND caixa != ''", (local,))
        caixas = cursor.fetchall()
        conn.close()

        for index, (caixa,) in enumerate(caixas):
            btn = QPushButton(f"📦\n{caixa}")
            # --- BLOCOS MAIORES AQUI ---
            btn.setFixedSize(180, 130)
            btn.setStyleSheet("background-color: #223959; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=caixa: self.carregar_itens_final(c))
            linha, coluna = divmod(index, 4)
            self.layout_grid.addWidget(btn, linha, coluna)

    def carregar_itens_final(self, caixa):
        self.limpar_grid()
        self.nivel_atual = "ITEM"
        self.lbl_caminho.setText(f"🏠 {self.local_selecionado} > {caixa} > Itens")
        
        conn = sqlite3.connect(self.caminho_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT nome, foto, quantidade, quantidade_minima FROM itens WHERE localizacao = ? AND caixa = ?", (self.local_selecionado, caixa))
        itens = cursor.fetchall()
        conn.close()

        for index, row in enumerate(itens):
            card = QFrame()
            # --- TAMANHO DO ITEM MANTIDO ORIGINAL ---
            card.setFixedSize(160, 200)
            card.setStyleSheet("background-color: white; border: 1px solid #d1c9b8; border-radius: 8px;")
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
            lbl_n.setStyleSheet("font-weight: bold; font-size: 12px; border: none; color: #223959;")
            
            qtd, q_min = row['quantidade'], row['quantidade_minima']
            cor = "#EF4444" if qtd <= q_min else "#10B981"
            lbl_q = QLabel(f"Qtd: {qtd} (Mín: {q_min})")
            lbl_q.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_q.setStyleSheet(f"color: {cor}; font-weight: bold; font-size: 11px; border: none;")

            l_card.addWidget(lbl_f)
            l_card.addWidget(lbl_n)
            l_card.addWidget(lbl_q)
            
            linha, coluna = divmod(index, 5) # Itens cabem mais, então mantive 5
            self.layout_grid.addWidget(card, linha, coluna)

    def voltar_nivel(self):
        if self.nivel_atual == "ITEM": self.carregar_caixas(self.local_selecionado)
        elif self.nivel_atual == "CAIXA": self.carregar_localizacoes()


# =====================================================================
# CLASSE PRINCIPAL
# =====================================================================
class EstoqueWidget(QWidget):
    def __init__(self, usuario_id, callback_adicionar, callback_editar):
        super().__init__()
        self.usuario_id = usuario_id
        self.callback_adicionar = callback_adicionar
        self.callback_editar = callback_editar
        
        pasta_ui = os.path.dirname(os.path.abspath(__file__))
        self.caminho_db = os.path.abspath(os.path.join(pasta_ui, "..", "database.db"))
        self.pasta_fotos = os.path.abspath(os.path.join(pasta_ui, "..")) 
        
        self.setStyleSheet("background-color: #e8e0cc;")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        lbl_titulo = QLabel("Controle de Estoque")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        layout_principal.addWidget(lbl_titulo)

        layout_cards = QHBoxLayout()
        self.lbl_total_itens = self.criar_cartao(layout_cards, "Itens Cadastrados")
        self.lbl_unidades = self.criar_cartao(layout_cards, "Unidades em Estoque")
        self.lbl_estoque_baixo = self.criar_cartao(layout_cards, "Estoque Baixo")
        self.lbl_movimentacoes = self.criar_cartao(layout_cards, "Movimentações Hoje")
        layout_principal.addLayout(layout_cards)

        frame_filtros = QFrame()
        frame_filtros.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #d1c9b8;")
        layout_f = QHBoxLayout(frame_filtros)
        
        self.txt_filtro_nome = QLineEdit()
        self.txt_filtro_nome.setPlaceholderText("🔍 Buscar por nome...")
        
        self.combo_filtro_local = QComboBox()
        self.combo_filtro_local.addItems(["Todos", "Sem Armário", "Armário 1", "Armário 2", "Armário 3", "Cestos", "Bancada/Setor"])
        
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

        # =========================================================
        # SEPARAÇÃO DOS BOTÕES DE AÇÃO (ESQUERDA E DIREITA)
        # =========================================================
        layout_acoes = QHBoxLayout()
        
        # --- Botões de CRUD (Ficam na Esquerda) ---
        layout_esq = QHBoxLayout()
        layout_esq.addWidget(self.criar_botao_acao("Adicionar", "#9c9075", self.callback_adicionar))
        layout_esq.addWidget(self.criar_botao_acao("Editar", "#9c9075", self.editar_selecionado))
        layout_esq.addWidget(self.criar_botao_acao("Excluir", "#9c9075", self.deletar_item))
        layout_acoes.addLayout(layout_esq)

        # O addStretch funciona como uma mola que empurra os botões seguintes para a direita
        layout_acoes.addStretch()

        # --- Botões Especiais (Ficam na Direita) ---
        layout_dir = QHBoxLayout()
        self.btn_exportar = QPushButton("📥 Exportar")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setStyleSheet("background-color: #059669; color: white; border-radius: 5px; padding: 10px 18px; font-weight: bold;")
        
        menu_exportar = QMenu(self.btn_exportar)
        menu_exportar.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #d1c9b8; border-radius: 4px; } 
            QMenu::item { padding: 8px 25px; color: #223959; font-weight: bold; } 
            QMenu::item:selected { background-color: #e8e0cc; }
        """)
        acao_pdf = menu_exportar.addAction("📄 Exportar para PDF")
        acao_xlsx = menu_exportar.addAction("📊 Exportar para Excel (.xlsx)")
        
        acao_pdf.triggered.connect(self.exportar_pdf)
        acao_xlsx.triggered.connect(self.exportar_excel)
        
        self.btn_exportar.setMenu(menu_exportar)
        layout_dir.addWidget(self.btn_exportar)

        self.btn_toggle_vista = self.criar_botao_acao("🗂️ Ver em Blocos", "#223959", self.alternar_vista)
        layout_dir.addWidget(self.btn_toggle_vista)

        layout_acoes.addLayout(layout_dir)
        # =========================================================

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
        
        self.tabela.setStyleSheet("""
            QHeaderView::section { background-color: #e8e0cc; color: #1F2937; font-weight: bold; border: 1px solid #d1c9b8; }
            QTableWidget { background-color: white; color: #1F2937; gridline-color: #d1c9b8; outline: 0; }
            QTableWidget::item:selected { background-color: #a39179; color: #1F2937; border: none; }
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
        
        btn_entrada = QPushButton("ENTRADA")
        btn_entrada.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_entrada.setStyleSheet("background-color: #00a941; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        btn_entrada.clicked.connect(self.registrar_entrada)
        
        btn_saida = QPushButton("SAÍDA")
        btn_saida.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_saida.setStyleSheet("background-color: #F03330; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        btn_saida.clicked.connect(self.registrar_saida)

        layout_mov.addWidget(lbl_mov)
        layout_mov.addWidget(QLabel("Qtd:", styleSheet="color:white; border:none;"))
        layout_mov.addWidget(self.spin_qtd_mov)
        layout_mov.addWidget(self.txt_obs_mov)
        layout_mov.addWidget(btn_entrada)
        layout_mov.addWidget(btn_saida)
        
        layout_principal.addWidget(self.frame_mov)

        self.carregar_itens()

    def alternar_vista(self):
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.btn_toggle_vista.setText("📋 Ver em Tabela")
            self.visao_blocos.carregar_localizacoes()
        else:
            self.stack.setCurrentIndex(0)
            self.btn_toggle_vista.setText("🗂️ Ver em Blocos")
            self.carregar_itens()

    def criar_cartao(self, layout, titulo):
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #d1c9b8;")
        c_layout = QVBoxLayout(card)
        lbl_t = QLabel(titulo); lbl_t.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold; border: none;")
        lbl_v = QLabel("0"); lbl_v.setStyleSheet("color: #1E3A8A; font-size: 20px; font-weight: bold; border: none;")
        c_layout.addWidget(lbl_t); c_layout.addWidget(lbl_v)
        layout.addWidget(card)
        return lbl_v

    def criar_botao_acao(self, texto, cor, funcao):
        btn = QPushButton(texto)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {cor}; color: white; border-radius: 5px; padding: 10px 18px; font-weight: bold;")
        btn.clicked.connect(funcao)
        return btn

    def limpar_filtros(self):
        self.txt_filtro_nome.clear()
        self.combo_filtro_local.setCurrentIndex(0) 
        self.txt_filtro_caixa.clear()
        self.carregar_itens()

    def carregar_itens(self):
        if not os.path.exists(self.caminho_db):
            return

        conn = sqlite3.connect(self.caminho_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(itens)")
            colunas = [col[1].lower() for col in cursor.fetchall()]
            
            col_nome = 'nome' if 'nome' in colunas else colunas[1]
            col_local = 'localizacao' if 'localizacao' in colunas else (colunas[4] if len(colunas) > 4 else None)
            col_caixa = 'caixa' if 'caixa' in colunas else ('categoria' if 'categoria' in colunas else None)
            
            f_nome = f"%{self.txt_filtro_nome.text()}%"
            f_caixa = f"%{self.txt_filtro_caixa.text()}%"
            
            texto_local = self.combo_filtro_local.currentText()
            if texto_local == "Todos":
                f_local = "%%"
            else:
                f_local = f"%{texto_local}%"

            query = f"SELECT * FROM itens WHERE {col_nome} LIKE ?"
            params = [f_nome]
            if col_local:
                query += f" AND {col_local} LIKE ?"
                params.append(f_local)
            if col_caixa:
                query += f" AND {col_caixa} LIKE ?"
                params.append(f_caixa)

            cursor.execute(query, params)
            dados = cursor.fetchall()
            
            self.tabela.setRowCount(0)
            total_unidades = 0
            baixo_estoque = 0
            
            for row_idx, row in enumerate(dados):
                self.tabela.insertRow(row_idx)
                self.tabela.setRowHeight(row_idx, 100) 

                try: qtd = int(row['quantidade'])
                except: qtd = 0
                try: min_q = int(row['quantidade_minima'])
                except: min_q = 0

                cor_fundo = QColor("#FFDADA") if qtd <= min_q else QColor("white")

                item_id = QTableWidgetItem(str(row[0]))
                item_id.setBackground(cor_fundo)
                self.tabela.setItem(row_idx, 0, item_id)

                label_foto = QLabel()
                label_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label_foto.setStyleSheet(f"background-color: {cor_fundo.name()}; border: none;")
                if 'foto' in colunas and row['foto']:
                    caminho_c = os.path.join(self.pasta_fotos, row['foto'])
                    if os.path.exists(caminho_c):
                        pixmap = QPixmap(caminho_c).scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        label_foto.setPixmap(pixmap)
                self.tabela.setCellWidget(row_idx, 1, label_foto)

                cols_mapping = {2: col_nome, 3: 'quantidade', 4: 'quantidade_minima', 5: col_local, 6: col_caixa}
                for col_idx, col_name in cols_mapping.items():
                    val = str(row[col_name]) if col_name and row[col_name] is not None else ""
                    item = QTableWidgetItem(val)
                    item.setBackground(cor_fundo)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col_idx != 2 else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    
                    if col_idx == 2 and qtd <= min_q:
                        baixo_estoque += 1
                        item.setForeground(QColor("#B91C1C"))
                        f = item.font(); f.setBold(True); item.setFont(f)
                    
                    self.tabela.setItem(row_idx, col_idx, item)
                
                total_unidades += qtd

            hoje = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE data LIKE ?", (f"{hoje}%",))
            total_mov_hoje = cursor.fetchone()[0]

            self.lbl_total_itens.setText(str(len(dados)))
            self.lbl_unidades.setText(str(total_unidades))
            self.lbl_estoque_baixo.setText(str(baixo_estoque))
            self.lbl_movimentacoes.setText(str(total_mov_hoje)) 

        except Exception as e:
            print(f"❌ Erro ao carregar: {e}")
        finally:
            conn.close()

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
            conn = sqlite3.connect(self.caminho_db)
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

        conn = sqlite3.connect(self.caminho_db)
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
            th, td { border: 1px solid #d1c9b8; padding: 8px; text-align: center; }
            th { background-color: #e8e0cc; color: #1F2937; }
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
            
            ws.append([
                self.tabela.item(row, 0).text(),
                self.tabela.item(row, 2).text(),
                int(self.tabela.item(row, 3).text()),
                int(self.tabela.item(row, 4).text()),
                self.tabela.item(row, 5).text(),
                self.tabela.item(row, 6).text()
            ])
            
        wb.save(caminho)
        QMessageBox.information(self, "Sucesso", "Planilha exportada com sucesso!")