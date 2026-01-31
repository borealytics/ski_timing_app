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
    def detect_csv_format(filepath: str) -> str:
        """
        Détecte le format du fichier CSV

        Returns:
            'course_file' (fichier de course, séparateur ;)
            'national_fis' (format National/FIS, séparateur ,)
            'standard' (format standard)
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        # Détecter le séparateur
        if ';' in first_line:
            # Fichier de course avec séparateur point-virgule
            return 'course_file'

        # Vérifier si c'est un format National/FIS (avec virgule)
        if first_line.startswith('# ') and 'SQA' in first_line:
            return 'national_fis'

        # Essayer de lire avec virgule
        try:
            df = pd.read_csv(filepath, nrows=1)
            columns = [col.strip() for col in df.columns]
            if 'BIB' in columns or 'Nom' in columns or 'Prenom' in columns or 'StNb' in columns:
                return 'national_fis'
        except:
            pass

        return 'standard'

    @staticmethod
    def import_athletes_course_file(filepath: str) -> List[Athlete]:
        """
        Importe les athlètes depuis un fichier de course
        Format: # SQA;BIB;StNb;Nom;Prenom;Annee;Club;Sexe;Categorie
        Auto-détecte le séparateur (; ou ,)

        Args:
            filepath: Chemin vers le fichier CSV

        Returns:
            Liste d'athlètes
        """
        # Auto-détection du séparateur
        return CSVImporter._import_athletes_fis_format(filepath, separator=None)

    @staticmethod
    def import_athletes_national_fis(filepath: str) -> List[Athlete]:
        """
        Importe les athlètes depuis un CSV format National/FIS
        Format: # SQA,BIB,StNb,Nom,Prenom,Annee,Club,Sexe,Categorie
        Auto-détecte le séparateur (; ou ,)

        Args:
            filepath: Chemin vers le fichier CSV

        Returns:
            Liste d'athlètes
        """
        # Auto-détection du séparateur
        return CSVImporter._import_athletes_fis_format(filepath, separator=None)

    @staticmethod
    def _read_file_with_encoding(filepath: str):
        """Lit un fichier en essayant plusieurs encodages"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Vérifier que le contenu est lisible
                    if content and len(content) > 0:
                        return content, encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Fallback: lire en binaire et décoder
        with open(filepath, 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
        return content, 'utf-8'

    @staticmethod
    def _detect_separator(first_line: str) -> str:
        """Détecte le séparateur utilisé dans la ligne"""
        # Compter les occurrences
        semicolons = first_line.count(';')
        commas = first_line.count(',')

        # Le séparateur le plus fréquent gagne
        if semicolons > commas:
            return ';'
        return ','

    @staticmethod
    def _import_athletes_fis_format(filepath: str, separator: str = None) -> List[Athlete]:
        """
        Importe les athlètes depuis un CSV format FIS (National/FIS ou fichier de course)

        Args:
            filepath: Chemin vers le fichier CSV
            separator: Séparateur (virgule ou point-virgule) - auto-détecté si None

        Returns:
            Liste d'athlètes
        """
        # Lire le fichier avec le bon encodage
        content, encoding = CSVImporter._read_file_with_encoding(filepath)
        lines = content.strip().split('\n')

        if not lines:
            return []

        first_line = lines[0].strip()

        # Vérifier si les lignes sont entourées de guillemets (fichier mal formaté)
        if first_line.startswith('"') and first_line.endswith('"'):
            # Supprimer les guillemets de chaque ligne
            lines = [line.strip().strip('"') for line in lines]
            first_line = lines[0]

            # Réécrire le contenu nettoyé dans un StringIO pour pandas
            from io import StringIO
            clean_content = '\n'.join(lines)

            # Auto-détecter le séparateur
            if separator is None:
                separator = CSVImporter._detect_separator(first_line)

            # Si la première ligne commence par #, c'est l'en-tête avec commentaire
            if first_line.startswith('#'):
                header = first_line.lstrip('# ').split(separator)
                header = [h.strip() for h in header]
                df = pd.read_csv(StringIO('\n'.join(lines[1:])), names=header, sep=separator)
            else:
                df = pd.read_csv(StringIO(clean_content), sep=separator)
        else:
            # Fichier normal
            # Auto-détecter le séparateur si non spécifié
            if separator is None:
                separator = CSVImporter._detect_separator(first_line)

            # Si la première ligne commence par #, c'est l'en-tête avec commentaire
            if first_line.startswith('#'):
                # Nettoyer l'en-tête: "# SQA;BIB;..." -> "SQA,BIB,..."
                header = first_line.lstrip('# ').split(separator)
                header = [h.strip() for h in header]
                df = pd.read_csv(filepath, skiprows=1, names=header, sep=separator, encoding=encoding)
            else:
                df = pd.read_csv(filepath, sep=separator, encoding=encoding)

        # Nettoyage spécifique au format FIS (pas d'appel à clean_dataframe)
        # Supprimer les lignes sans BIB
        bib_col = 'BIB' if 'BIB' in df.columns else 'Bib' if 'Bib' in df.columns else None
        if bib_col:
            df = df[df[bib_col].notna()].copy()

        athletes = []

        # Mapper les colonnes (avec variantes possibles)
        col_mapping = {
            'bib': ['BIB', 'Bib', 'bib'],
            'start_number': ['StNb', 'Start Number', 'StartNb'],
            'last_name': ['Nom', 'Last', 'LastName'],
            'first_name': ['Prenom', 'First', 'FirstName'],
            'year_of_birth': ['Annee', 'Year of Birth', 'YearOfBirth', 'Year'],
            'team': ['Club', 'Team'],
            'sex': ['Sexe', 'Sex', 'Sex (Masters or XC)'],
            'category': ['Categorie', 'Class', 'Category'],
            'nat_number': ['SQA', '# SQA', 'NAT Number', 'NatNumber']
        }

        def get_col(df, possible_names):
            for name in possible_names:
                if name in df.columns:
                    return name
            return None

        for _, row in df.iterrows():
            try:
                bib_col = get_col(df, col_mapping['bib'])
                stnb_col = get_col(df, col_mapping['start_number'])
                nom_col = get_col(df, col_mapping['last_name'])
                prenom_col = get_col(df, col_mapping['first_name'])
                annee_col = get_col(df, col_mapping['year_of_birth'])
                club_col = get_col(df, col_mapping['team'])
                sexe_col = get_col(df, col_mapping['sex'])
                cat_col = get_col(df, col_mapping['category'])
                nat_col = get_col(df, col_mapping['nat_number'])

                athlete = Athlete(
                    bib=int(row[bib_col]) if bib_col and pd.notna(row[bib_col]) else 0,
                    start_number=int(row[stnb_col]) if stnb_col and pd.notna(row[stnb_col]) else 0,
                    first_name=str(row[prenom_col]).strip() if prenom_col and pd.notna(row[prenom_col]) else '',
                    last_name=str(row[nom_col]).strip() if nom_col and pd.notna(row[nom_col]) else '',
                    category=str(row[cat_col]).strip() if cat_col and pd.notna(row[cat_col]) else '',
                    sex=str(row[sexe_col]).strip() if sexe_col and pd.notna(row[sexe_col]) else '',
                    team=str(row[club_col]).strip() if club_col and pd.notna(row[club_col]) else '',
                    year_of_birth=int(row[annee_col]) if annee_col and pd.notna(row[annee_col]) else 0,
                    nat_number=str(row[nat_col]) if nat_col and pd.notna(row[nat_col]) else ''
                )
                athletes.append(athlete)
            except Exception as e:
                print(f"Erreur lors de l'import de la ligne: {e}")
                continue

        return athletes

    @staticmethod
    def import_athletes_auto(filepath: str) -> List[Athlete]:
        """
        Importe les athlètes en détectant automatiquement le format

        Args:
            filepath: Chemin vers le fichier CSV

        Returns:
            Liste d'athlètes
        """
        format_type = CSVImporter.detect_csv_format(filepath)

        if format_type == 'course_file':
            return CSVImporter.import_athletes_course_file(filepath)
        elif format_type == 'national_fis':
            return CSVImporter.import_athletes_national_fis(filepath)
        else:
            return CSVImporter.import_athletes(filepath)

    @staticmethod
    def import_athletes_by_format(filepath: str, format_type: str) -> List[Athlete]:
        """
        Importe les athlètes selon le format spécifié

        Args:
            filepath: Chemin vers le fichier CSV
            format_type: 'course_file', 'national_fis' ou 'standard'

        Returns:
            Liste d'athlètes
        """
        if format_type == 'course_file':
            return CSVImporter.import_athletes_course_file(filepath)
        elif format_type == 'national_fis':
            return CSVImporter.import_athletes_national_fis(filepath)
        else:
            return CSVImporter.import_athletes(filepath)

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
    def get_available_result_columns(filepath: str) -> List[str]:
        """
        Détecte les colonnes de résultats disponibles dans un fichier CSV

        Args:
            filepath: Chemin vers le fichier CSV

        Returns:
            Liste des colonnes de résultats trouvées
        """
        # Lire le fichier avec le bon encodage
        content, encoding = CSVImporter._read_file_with_encoding(filepath)
        lines = content.strip().split('\n')

        if not lines:
            return []

        first_line = lines[0].strip()

        # Gérer les lignes entourées de guillemets
        if first_line.startswith('"') and first_line.endswith('"'):
            first_line = first_line.strip('"')

        separator = CSVImporter._detect_separator(first_line)

        from io import StringIO

        if first_line.startswith('#'):
            header = first_line.lstrip('# ').split(separator)
            header = [h.strip() for h in header]
            df = pd.read_csv(StringIO('\n'.join(lines[1:])), names=header, sep=separator, nrows=0)
        else:
            df = pd.read_csv(StringIO(content), sep=separator, nrows=0, encoding=encoding)

        # Chercher les colonnes de résultats possibles
        result_columns = []
        possible_names = ['First Run Result', 'Second Run Result', 'Third Run Result',
                         'Run 1', 'Run 2', 'Run 3', 'Time', 'Temps']

        for col in df.columns:
            col_clean = col.strip()
            col_upper = col_clean.upper()

            # Exclure les colonnes de rang
            if 'RANK' in col_upper or 'RANG' in col_upper:
                continue

            if col_clean in possible_names or 'Run Result' in col_clean:
                result_columns.append(col_clean)

        return result_columns

    @staticmethod
    def import_run_results(filepath: str, run_number: int, result_column: str = None) -> dict:
        """
        Importe les résultats d'un run depuis un CSV National/FIS

        Args:
            filepath: Chemin vers le fichier CSV
            run_number: Numéro du run (1, 2, 3) - utilisé si result_column non spécifié
            result_column: Nom de la colonne de résultat à utiliser (optionnel)

        Returns:
            Dictionnaire {bib: RunResult}
        """
        # Lire le fichier avec le bon encodage
        content, encoding = CSVImporter._read_file_with_encoding(filepath)
        lines = content.strip().split('\n')

        if not lines:
            return {}

        first_line = lines[0].strip()

        # Gérer les lignes entourées de guillemets
        if first_line.startswith('"') and first_line.endswith('"'):
            lines = [line.strip().strip('"') for line in lines]
            first_line = lines[0]

        separator = CSVImporter._detect_separator(first_line)

        from io import StringIO

        if first_line.startswith('#'):
            header = first_line.lstrip('# ').split(separator)
            header = [h.strip() for h in header]
            df = pd.read_csv(StringIO('\n'.join(lines[1:])), names=header, sep=separator)
        else:
            df = pd.read_csv(StringIO('\n'.join(lines)), sep=separator)

        # Nettoyage - trouver la colonne Bib
        bib_col = None
        for col in df.columns:
            if col.strip().upper() == 'BIB':
                bib_col = col
                break

        if bib_col:
            df = df[df[bib_col].notna()].copy()

        # Déterminer la colonne de résultat
        if result_column:
            result_col = result_column
        elif run_number == 1:
            result_col = 'First Run Result'
        elif run_number == 2:
            result_col = 'Second Run Result'
        else:
            return {}

        if result_col not in df.columns:
            raise ValueError(f"Colonne '{result_col}' non trouvée dans le fichier")

        results = {}

        for _, row in df.iterrows():
            try:
                bib = int(row[bib_col]) if bib_col else int(row['Bib'])
                time_str = str(row[result_col]).strip()

                result = RunResult(bib=bib)

                # Parser le temps
                if time_str.upper() in ['DNS', 'DNF', 'DSQ', 'NAN', '']:
                    if time_str.upper() in ['DNS', 'DNF', 'DSQ']:
                        result.set_status(time_str.upper())
                else:
                    time_seconds = parse_time_msscc(time_str)
                    if time_seconds is not None:
                        result.set_time(time_seconds, time_str)

                results[bib] = result

            except Exception as e:
                print(f"Erreur lors de l'import du résultat: {e}")
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
