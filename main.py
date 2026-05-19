import sys
from PyQt6.QtWidgets import QApplication
from database.create_tables import create_tables
from ui.login_window import LoginWindow 

def main():
    create_tables()
    app = QApplication(sys.argv)

    # O sistema agora começa pelo LOGIN
    window = LoginWindow() 
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()