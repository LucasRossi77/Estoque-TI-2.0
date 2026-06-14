from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QGraphicsOpacityEffect
)
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QIcon

from ui.profile_window import PerfilWidget
from ui.main_window import EstoqueWidget
from ui.reports_window import ReportsWindow
from ui.add_item_window import AddItemWidget
from ui.edit_item_window import EditItemWidget
from ui.dashboard_window import DashboardWidget
from ui.operacional_window import OperacionalWidget
from ui.theme import palette

class AppWindow(QMainWindow):
    def __init__(self, usuario_id, login_window): 
        super().__init__()
        self.usuario_id = usuario_id
        self.login_window = login_window 
        self.dark_mode = False

        # Configurações Básicas
        self.setWindowTitle("Sistema de Gestão - TI")
        self.resize(1200, 800)
        self.setWindowIcon(QIcon('assets/icon.png')) 

        # --- ESTRUTURA PRINCIPAL ---
        central_widget = QWidget()
        self.central_widget = central_widget
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- MENU LATERAL ---
        menu_widget = QWidget()
        self.menu_widget = menu_widget
        menu_widget.setFixedWidth(260)
        self.menu_layout = QVBoxLayout(menu_widget)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(0)

        # Título do Menu
        self.label_titulo = QLabel("ESTOQUE - TI")
        self.label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_titulo.setStyleSheet("""
            font-size: 30px; 
            font-weight: bold; 
            color: white; 
            padding: 40px 10px;
            margin-bottom: 10px;
        """)
        self.menu_layout.addWidget(self.label_titulo)

        # Botões do Menu
        self.btn_perfil = self.criar_botao_menu("   Perfil")
        self.btn_estoque = self.criar_botao_menu("   Estoque")
        self.btn_operacional = self.criar_botao_menu("   Operacional")
        self.btn_relatorios = self.criar_botao_menu("   Relatórios")
        self.btn_dashboard = self.criar_botao_menu("   Gráficos")
        self.btn_modo = self.criar_botao_menu("   Modo Noturno")

        self.btn_sair = self.criar_botao_menu("   Sair")
        
        self.menu_layout.addWidget(self.btn_perfil)
        self.menu_layout.addWidget(self.btn_estoque)
        self.menu_layout.addWidget(self.btn_operacional)
        self.menu_layout.addWidget(self.btn_relatorios)
        self.menu_layout.addWidget(self.btn_dashboard)

        self.menu_layout.addStretch() 
        self.menu_layout.addWidget(self.btn_modo)
        self.menu_layout.addWidget(self.btn_sair)

        # --- ÁREA DE CONTEÚDO (STACKED WIDGET) ---
        self.stacked_widget = QStackedWidget()
       
        self.tela_perfil = PerfilWidget(self.usuario_id, self.logout)
        self.tela_estoque = EstoqueWidget(
            self.usuario_id, 
            self.ir_para_adicionar, 
            self.ir_para_editar     
        )
        self.tela_relatorios = ReportsWindow()
        self.tela_adicionar = AddItemWidget(self.tela_estoque.carregar_itens, self.voltar_para_estoque)
        self.tela_dashboard = DashboardWidget()
        self.tela_operacional = OperacionalWidget()

        # Adicionando ao Stack
        self.stacked_widget.addWidget(self.tela_perfil)      # Índice 0
        self.stacked_widget.addWidget(self.tela_estoque)     # Índice 1
        self.stacked_widget.addWidget(self.tela_relatorios)  # Índice 2
        self.stacked_widget.addWidget(self.tela_adicionar)   # Índice 3
        self.stacked_widget.addWidget(self.tela_dashboard)   # Índice 4
        self.stacked_widget.addWidget(self.tela_operacional) # Índice 5

        # Variável para controlar a tela de edição
        self.tela_editar = None
        self.animacao_tela = None

        # Montando o Layout Final
        main_layout.addWidget(menu_widget)
        main_layout.addWidget(self.stacked_widget)

        # Conectar Eventos
        self.btn_perfil.clicked.connect(lambda: self.mudar_tela(0))
        self.btn_estoque.clicked.connect(lambda: self.mudar_tela(1))
        self.btn_relatorios.clicked.connect(lambda: self.mudar_tela(2))
        self.btn_dashboard.clicked.connect(lambda: self.mudar_tela(4))
        self.btn_operacional.clicked.connect(lambda: self.mudar_tela(5))
        self.btn_modo.clicked.connect(self.alternar_modo_noturno)
        self.btn_sair.clicked.connect(self.logout)

        # Começar na tela de Estoque
        self.stacked_widget.setCurrentIndex(1)

        self.aplicar_tema()

    def criar_botao_menu(self, texto):
        btn = QPushButton(texto)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(60)
        return btn

    def estilo_botao_menu(self):
        p = palette(self.dark_mode)
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {p['header_text']};
                text-align: left;
                padding-left: 25px;
                font-size: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {p['menu_hover']};
                border-left: 5px solid {p['menu_active']};
            }}
        """

    def aplicar_tema(self):
        p = palette(self.dark_mode)
        self.central_widget.setStyleSheet(f"background-color: {p['bg']}; color: {p['text']};")
        self.menu_widget.setStyleSheet(f"background-color: {p['menu']}; border: none;")
        self.label_titulo.setStyleSheet(f"""
            font-size: 30px;
            font-weight: bold;
            color: {p['header_text']};
            padding: 40px 10px;
            margin-bottom: 10px;
        """)

        for btn in [
            self.btn_perfil, self.btn_estoque, self.btn_operacional,
            self.btn_relatorios, self.btn_dashboard, self.btn_modo, self.btn_sair
        ]:
            btn.setStyleSheet(self.estilo_botao_menu())
        self.btn_modo.setStyleSheet(self.btn_modo.styleSheet() + "margin-top: 20px;")
        self.btn_sair.setStyleSheet(self.btn_sair.styleSheet() + f"color: {p['danger']};")

        self.btn_modo.setText("☀️   Modo Claro" if self.dark_mode else "🌙   Modo Noturno")
        for tela in [
            self.tela_perfil, self.tela_estoque, self.tela_relatorios,
            self.tela_adicionar, self.tela_dashboard, self.tela_operacional
        ]:
            if hasattr(tela, "aplicar_tema"):
                tela.aplicar_tema(self.dark_mode)
        if self.tela_editar and hasattr(self.tela_editar, "aplicar_tema"):
            self.tela_editar.aplicar_tema(self.dark_mode)

    def alternar_modo_noturno(self):
        self.dark_mode = not self.dark_mode
        self.aplicar_tema()

    def mudar_tela(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index == 2:
            self.tela_relatorios.carregar_dados()
        elif index == 5:
            self.tela_operacional.carregar_dados()
        self.animar_tela_atual()

    def animar_tela_atual(self):
        widget = self.stacked_widget.currentWidget()
        if not widget:
            return

        efeito = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(efeito)

        animacao = QPropertyAnimation(efeito, b"opacity", self)
        animacao.setDuration(220)
        animacao.setStartValue(0.35)
        animacao.setEndValue(1.0)
        animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        animacao.finished.connect(lambda: widget.setGraphicsEffect(None))
        self.animacao_tela = animacao
        animacao.start()

    def ir_para_adicionar(self):
        self.stacked_widget.setCurrentIndex(3)
        self.animar_tela_atual()

    def ir_para_editar(self, item_id):
        if self.tela_editar:
            self.stacked_widget.removeWidget(self.tela_editar)
            self.tela_editar.deleteLater()

        self.tela_editar = EditItemWidget(item_id, self.tela_estoque.carregar_itens, self.voltar_para_estoque)
        self.stacked_widget.addWidget(self.tela_editar)
        if hasattr(self.tela_editar, "aplicar_tema"):
            self.tela_editar.aplicar_tema(self.dark_mode)
        self.stacked_widget.setCurrentWidget(self.tela_editar)
        self.animar_tela_atual()

    def voltar_para_estoque(self):
        self.stacked_widget.setCurrentIndex(1)
        self.tela_estoque.carregar_itens()
        self.animar_tela_atual()

    def logout(self):
        self.close()
        self.login_window.show()
