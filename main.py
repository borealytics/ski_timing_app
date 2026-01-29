"""
Ski Timing Manager - Application de chronométrage pour ski alpin
Point d'entrée principal
"""
import sys
import tkinter as tk
from tkinter import ttk

from main_window import MainWindow


def main():
    """Point d'entrée de l'application"""
    
    # Configuration du style
    app = MainWindow()
    
    # Style personnalisé
    style = ttk.Style()
    style.theme_use('clam')
    
    # Lancer l'application
    app.mainloop()


if __name__ == "__main__":
    main()
