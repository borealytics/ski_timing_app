"""
Utilitaires pour la conversion de temps et validations
"""
import re
from typing import Optional, Tuple


def parse_time_msscc(time_str: str) -> Optional[float]:
    """
    Convertit un temps au format m:ss.cc en secondes décimales
    
    Args:
        time_str: Temps au format "m:ss.cc" ou "ss.cc"
        
    Returns:
        Temps en secondes (float) ou None si invalide
        
    Examples:
        "1:15.34" -> 75.34
        "45.67" -> 45.67
        "DNS" -> None
    """
    if not time_str or pd.isna(time_str):
        return None
        
    time_str = str(time_str).strip().upper()
    
    # Gestion des statuts spéciaux
    if time_str in ['DNS', 'DNF', 'DSQ']:
        return None
    
    # Pattern pour m:ss.cc ou ss.cc
    pattern = r'^(?:(\d+):)?(\d{1,2})\.(\d{2})$'
    match = re.match(pattern, time_str)
    
    if not match:
        return None
    
    minutes = int(match.group(1)) if match.group(1) else 0
    seconds = int(match.group(2))
    centiseconds = int(match.group(3))
    
    return minutes * 60 + seconds + centiseconds / 100


def format_time_msscc(seconds: Optional[float]) -> str:
    """
    Convertit des secondes décimales en format m:ss.cc
    
    Args:
        seconds: Temps en secondes
        
    Returns:
        Temps formaté "m:ss.cc"
        
    Examples:
        75.34 -> "1:15.34"
        45.67 -> "0:45.67"
        None -> ""
    """
    if seconds is None or pd.isna(seconds):
        return ""
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    return f"{minutes}:{remaining_seconds:05.2f}"


def validate_time_input(minutes: str, seconds: str, centiseconds: str) -> Tuple[bool, str]:
    """
    Valide les entrées de temps avant conversion
    
    Returns:
        (is_valid, error_message)
    """
    try:
        m = int(minutes) if minutes else 0
        s = int(seconds) if seconds else 0
        cs = int(centiseconds) if centiseconds else 0
        
        if m < 0 or m > 9:
            return False, "Minutes doivent être entre 0 et 9"
        if s < 0 or s > 59:
            return False, "Secondes doivent être entre 0 et 59"
        if cs < 0 or cs > 99:
            return False, "Centièmes doivent être entre 0 et 99"
            
        return True, ""
    except ValueError:
        return False, "Entrée invalide - utilisez uniquement des chiffres"


def calculate_best_times(times: list, count: int) -> Optional[float]:
    """
    Calcule la somme des N meilleurs temps
    
    Args:
        times: Liste des temps (peut contenir None pour DNS/DNF/DSQ)
        count: Nombre de meilleurs temps à prendre
        
    Returns:
        Somme des meilleurs temps ou None si pas assez de temps valides
    """
    valid_times = [t for t in times if t is not None and not pd.isna(t)]
    
    if len(valid_times) < count:
        return None
    
    valid_times.sort()
    return sum(valid_times[:count])


import pandas as pd
import numpy as np


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie le dataframe importé
    """
    # Supprimer les lignes sans Bib
    df = df[df['Bib'].notna()].copy()
    
    # Remplir les valeurs manquantes
    df['Start Number'] = df['Start Number'].fillna(0).astype(int)
    df['Class'] = df['Class'].fillna('Unknown')
    df['Team'] = df['Team'].fillna('Unknown')
    df['First'] = df['First'].fillna('')
    df['Last'] = df['Last'].fillna('')
    
    return df
