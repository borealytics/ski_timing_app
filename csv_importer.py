"""
Importation et export de données CSV
"""
import pandas as pd
from typing import List, Optional
from models import Athlete, RunResult
from utils import parse_time_msscc, clean_dataframe


class CSVImporter:
    """Gestion de l'import/export CSV"""
    
    @staticmethod
    def import_athletes(filepath: str) -> List[Athlete]:
        """
        Importe les athlètes depuis un CSV National/FIS Software
        
        Args:
            filepath: Chemin vers le fichier CSV
            
        Returns:
            Liste d'athlètes
        """
        df = pd.read_csv(filepath)
        df = clean_dataframe(df)
        
        athletes = []
        
        for _, row in df.iterrows():
            try:
                athlete = Athlete(
                    bib=int(row['Bib']),
                    start_number=int(row['Start Number']) if pd.notna(row['Start Number']) else 0,
                    first_name=str(row['First']).strip(),
                    last_name=str(row['Last']).strip(),
                    category=str(row['Class']).strip(),
                    sex=str(row['Sex (Masters or XC)']).strip(),
                    team=str(row['Team']).strip() if pd.notna(row['Team']) else '',
                    year_of_birth=int(row['Year of Birth']) if pd.notna(row['Year of Birth']) else 0,
                    nat_number=str(row['NAT Number']) if pd.notna(row['NAT Number']) else ''
                )
                athletes.append(athlete)
            except Exception as e:
                print(f"Erreur lors de l'import de la ligne {row['Bib']}: {e}")
                continue
        
        return athletes
    
    @staticmethod
    def import_run_results(filepath: str, run_number: int) -> dict:
        """
        Importe les résultats d'un run depuis un CSV National/FIS
        
        Args:
            filepath: Chemin vers le fichier CSV
            run_number: Numéro du run (1, 2, 3)
            
        Returns:
            Dictionnaire {bib: RunResult}
        """
        df = pd.read_csv(filepath)
        df = clean_dataframe(df)
        
        # Déterminer la colonne de résultat
        if run_number == 1:
            result_col = 'First Run Result'
        elif run_number == 2:
            result_col = 'Second Run Result'
        else:
            # Pour run 3, pas de colonne native dans le format
            # On suppose qu'il y a une colonne custom ou on retourne vide
            return {}
        
        results = {}
        
        for _, row in df.iterrows():
            try:
                bib = int(row['Bib'])
                time_str = str(row[result_col]).strip()
                
                result = RunResult(bib=bib)
                
                # Parser le temps
                if time_str.upper() in ['DNS', 'DNF', 'DSQ']:
                    result.set_status(time_str.upper())
                else:
                    time_seconds = parse_time_msscc(time_str)
                    if time_seconds is not None:
                        result.set_time(time_seconds, time_str)
                
                results[bib] = result
                
            except Exception as e:
                print(f"Erreur lors de l'import du résultat pour bib {row['Bib']}: {e}")
                continue
        
        return results
    
    @staticmethod
    def compare_results(manual_results: dict, imported_results: dict) -> List[dict]:
        """
        Compare les résultats manuels avec les résultats importés
        
        Args:
            manual_results: Dictionnaire {bib: RunResult} manuel
            imported_results: Dictionnaire {bib: RunResult} importé
            
        Returns:
            Liste de différences [{bib, manual, imported, diff}]
        """
        differences = []
        
        all_bibs = set(manual_results.keys()) | set(imported_results.keys())
        
        for bib in sorted(all_bibs):
            manual = manual_results.get(bib)
            imported = imported_results.get(bib)
            
            # Cas où un résultat existe dans un seul fichier
            if manual is None:
                differences.append({
                    'bib': bib,
                    'manual': 'ABSENT',
                    'imported': imported.time_display,
                    'diff': 'Manquant dans manuel',
                    'type': 'missing_manual'
                })
                continue
            
            if imported is None:
                differences.append({
                    'bib': bib,
                    'manual': manual.time_display,
                    'imported': 'ABSENT',
                    'diff': 'Manquant dans import',
                    'type': 'missing_import'
                })
                continue
            
            # Comparer les statuts et temps
            if manual.status != imported.status:
                differences.append({
                    'bib': bib,
                    'manual': manual.time_display,
                    'imported': imported.time_display,
                    'diff': f'Statut différent',
                    'type': 'status_diff'
                })
            elif manual.status == 'FINISHED' and imported.status == 'FINISHED':
                # Comparer les temps (tolérance de 0.01s pour arrondis)
                if abs(manual.time_seconds - imported.time_seconds) > 0.01:
                    diff_seconds = manual.time_seconds - imported.time_seconds
                    differences.append({
                        'bib': bib,
                        'manual': manual.time_display,
                        'imported': imported.time_display,
                        'diff': f'{diff_seconds:+.2f}s',
                        'type': 'time_diff'
                    })
        
        return differences
    
    @staticmethod
    def export_to_excel(race, filepath: str):
        """
        Export les résultats vers Excel
        
        Args:
            race: Objet Race
            filepath: Chemin du fichier Excel de sortie
        """
        from results import ResultsCalculator
        
        calculator = ResultsCalculator(race)
        final_results = calculator.calculate_final_results()
        
        # Créer un DataFrame
        data = []
        for result in final_results:
            athlete = next(a for a in race.athletes if a.bib == result['bib'])
            data.append({
                'Rang': result['rank'],
                'Bib': result['bib'],
                'Nom': athlete.last_name,
                'Prénom': athlete.first_name,
                'Catégorie': athlete.category,
                'Sexe': athlete.sex,
                'Club': athlete.team,
                'Run 1': result.get('run1', ''),
                'Run 2': result.get('run2', ''),
                'Run 3': result.get('run3', ''),
                'Temps Total': result['total_display'],
                'Status': result['status']
            })
        
        df = pd.DataFrame(data)
        
        # Export vers Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Feuille globale
            df.to_excel(writer, sheet_name='Résultats Globaux', index=False)
            
            # Feuilles par catégorie-sexe
            for cat_sex in df.groupby(['Catégorie', 'Sexe']).groups.keys():
                cat, sex = cat_sex
                sheet_name = f"{cat}-{sex}"[:31]  # Limite Excel
                
                df_filtered = df[
                    (df['Catégorie'] == cat) & (df['Sexe'] == sex)
                ].head(5)  # Top 5
                
                df_filtered.to_excel(writer, sheet_name=sheet_name, index=False)
