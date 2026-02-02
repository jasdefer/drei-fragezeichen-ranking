"""
Logging-Konfiguration für den Bot

Zentrale Stelle für die Konfiguration des Logging-Systems.
Console-basiert mit klaren Log-Levels (INFO, WARNING, ERROR).
"""

import logging
import sys


def setup_logging(level=logging.INFO):
    """
    Konfiguriert das Logging-System für den Bot.
    
    Args:
        level: Log-Level (default: logging.INFO)
    """
    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Handler für Console-Output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format: Zeitstempel, Level, Modul, Nachricht
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Handler zum Root-Logger hinzufügen
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name):
    """
    Gibt einen konfigurierten Logger zurück.
    
    Args:
        name: Name des Loggers (üblicherweise __name__)
    
    Returns:
        logging.Logger: Konfigurierter Logger
    """
    return logging.getLogger(name)
