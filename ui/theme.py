from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor


LOCALIZACOES_PADRAO = [
    "Sem Armário",
    "Armário 1",
    "Armário 2",
    "Armário 3",
    "Armário 4",
    "Cestos",
    "Bancada/Setor",
]


def palette(dark=False):
    if dark:
        return {
            "bg": "#0F172A",
            "card": "#111827",
            "card_alt": "#1F2937",
            "soft": "#172033",
            "border": "#334155",
            "text": "#E5E7EB",
            "muted": "#94A3B8",
            "header": "#0B1220",
            "header_text": "#FFFFFF",
            "header_muted": "#CBD5E1",
            "accent": "#60A5FA",
            "accent_hover": "#3B82F6",
            "good": "#34D399",
            "warning": "#FBBF24",
            "danger": "#F87171",
            "danger_bg": "#3B1117",
            "ok_bg": "#0D3328",
            "selection_bg": "#1D4ED8",
            "selection_text": "#FFFFFF",
            "table_alt": "#172033",
            "menu": "#020617",
            "menu_hover": "#1E293B",
            "menu_active": "#2563EB",
        }

    return {
        "bg": "#F3F6FA",
        "card": "#FFFFFF",
        "card_alt": "#F8FAFC",
        "soft": "#EAF2FF",
        "border": "#DDE6F0",
        "text": "#1F2937",
        "muted": "#6B7280",
        "header": "#223959",
        "header_text": "#FFFFFF",
        "header_muted": "#E5EAF3",
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "good": "#059669",
        "warning": "#D97706",
        "danger": "#DC2626",
        "danger_bg": "#FEF2F2",
        "ok_bg": "#ECFDF5",
        "selection_bg": "#DBEAFE",
        "selection_text": "#111827",
        "table_alt": "#F8FAFC",
        "menu": "#223959",
        "menu_hover": "#546DBF",
        "menu_active": "#60A5FA",
    }


def apply_shadow(widget, dark=False, blur=14, y=4):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(y)
    opacity = 70 if dark else 18
    shadow.setColor(QColor(0, 0, 0, opacity))
    widget.setGraphicsEffect(shadow)


def button_style(kind="primary", dark=False):
    p = palette(dark)
    colors = {
        "primary": (p["accent"], p["accent_hover"], "#FFFFFF"),
        "dark": (p["header"], p["menu_hover"] if dark else "#1F2937", "#FFFFFF"),
        "muted": ("#64748B" if dark else "#9CA3AF", "#475569" if dark else "#6B7280", "#FFFFFF"),
        "success": (p["good"], "#059669", "#FFFFFF"),
        "danger": (p["danger"], "#B91C1C", "#FFFFFF"),
        "ghost": ("transparent", p["soft"], p["accent"]),
    }
    bg, hover, fg = colors.get(kind, colors["primary"])
    border = f"1px solid {p['border']}" if kind == "ghost" else "none"
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border-radius: 6px;
            padding: 9px 14px;
            font-weight: 800;
            border: {border};
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:disabled {{
            background-color: {p['border']};
            color: {p['muted']};
        }}
    """


def input_style(dark=False):
    p = palette(dark)
    return f"""
        QLineEdit, QSpinBox, QComboBox {{
            padding: 8px 10px;
            border: 1px solid {p['border']};
            border-radius: 6px;
            background-color: {p['card']};
            color: {p['text']};
            selection-background-color: {p['selection_bg']};
            selection-color: {p['selection_text']};
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid {p['accent']};
        }}
        QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
            border: none;
            background: transparent;
            width: 24px;
        }}
    """


def table_style(dark=False):
    p = palette(dark)
    return f"""
        QTableWidget {{
            background-color: {p['card']};
            alternate-background-color: {p['table_alt']};
            border-radius: 8px;
            border: 1px solid {p['border']};
            gridline-color: {p['border']};
            color: {p['text']};
            selection-background-color: {p['selection_bg']};
            selection-color: {p['selection_text']};
            outline: 0;
        }}
        QHeaderView::section {{
            background-color: {p['header']};
            color: {p['header_text']};
            font-weight: 800;
            padding: 9px;
            border: none;
        }}
        QTableWidget::item {{
            padding: 8px;
            border: none;
        }}
    """


def card_style(dark=False):
    p = palette(dark)
    return f"""
        QFrame {{
            background-color: {p['card']};
            border-radius: 8px;
            border: 1px solid {p['border']};
        }}
        QLabel {{
            background-color: transparent;
            border: none;
            color: {p['text']};
        }}
    """
