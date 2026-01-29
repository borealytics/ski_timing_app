"""
Calcul des résultats finaux
"""
from typing import List, Dict
from models import Race, Athlete, RunResult
from utils import calculate_best_times, format_time_msscc


class ResultsCalculator:
    """Calcule les résultats finaux d'une course"""
    
    def __init__(self, race: Race):
        self.race = race
    
    def calculate_final_results(self) -> List[Dict]:
        """
        Calcule les résultats finaux selon la méthode de calcul configurée
        
        Returns:
            Liste de résultats triés [{bib, times, total, rank, status}]
        """
        results = []
        
        for athlete in self.race.athletes:
            result = self._calculate_athlete_result(athlete)
            results.append(result)
        
        # Trier les résultats
        results = self._rank_results(results)
        
        return results
    
    def _calculate_athlete_result(self, athlete: Athlete) -> Dict:
        """Calcule le résultat pour un athlète"""
        bib = athlete.bib
        
        # Récupérer les temps de tous les runs
        times = []
        time_displays = []
        statuses = []
        
        for run in self.race.runs:
            result = run.get_result(bib)
            if result:
                times.append(result.time_seconds)
                time_displays.append(result.time_display)
                statuses.append(result.status)
            else:
                times.append(None)
                time_displays.append('')
                statuses.append('PENDING')
        
        # Calculer le temps total selon la méthode
        total_time, status = self._calculate_total(times, statuses)
        
        result_dict = {
            'bib': bib,
            'category': athlete.category,
            'sex': athlete.sex,
            'total_seconds': total_time,
            'total_display': format_time_msscc(total_time) if total_time else status,
            'status': status
        }
        
        # Ajouter les temps individuels
        for i, (time, display) in enumerate(zip(times, time_displays), 1):
            result_dict[f'run{i}'] = display if display else 'PENDING'
            result_dict[f'run{i}_seconds'] = time
        
        return result_dict
    
    def _calculate_total(self, times: List, statuses: List) -> tuple:
        """
        Calcule le temps total selon la méthode configurée

        DSQ, DNF et DNS sont traités de la même façon: le temps de ce run n'est pas valide.
        Le coureur peut quand même être classé s'il a assez de temps valides dans les autres runs.

        Returns:
            (total_seconds, status)
        """
        method = self.race.config.calculation_method

        # Vérifier si tous les runs sont sans temps valide
        if all(s in ('DNS', 'DNF', 'DSQ', 'PENDING') for s in statuses):
            # Déterminer le statut à afficher
            if all(s == 'DNS' for s in statuses):
                return None, 'DNS'
            elif all(s == 'DSQ' for s in statuses):
                return None, 'DSQ'
            elif 'DNF' in statuses:
                return None, 'DNF'
            elif 'DSQ' in statuses:
                return None, 'DSQ'
            else:
                return None, 'DNS'

        # Filtrer les temps valides (ignorer DNS, DNF, DSQ)
        valid_times = [t for t in times if t is not None]

        if method == 'BEST_1':
            if len(valid_times) < 1:
                return None, self._get_failure_status(statuses)
            return min(valid_times), 'FINISHED'

        elif method == 'BEST_2':
            if len(valid_times) < 2:
                return None, self._get_failure_status(statuses)
            sorted_times = sorted(valid_times)
            return sum(sorted_times[:2]), 'FINISHED'

        elif method == 'SUM_3':
            if len(valid_times) < 3:
                return None, self._get_failure_status(statuses)
            return sum(valid_times), 'FINISHED'

        return None, 'UNKNOWN'

    def _get_failure_status(self, statuses: List) -> str:
        """Détermine le statut à afficher quand il n'y a pas assez de temps valides"""
        if 'DNF' in statuses:
            return 'DNF'
        elif 'DSQ' in statuses:
            return 'DSQ'
        elif 'DNS' in statuses:
            return 'DNS'
        return 'DNF'
    
    def _rank_results(self, results: List[Dict]) -> List[Dict]:
        """
        Attribue les rangs aux résultats
        Trie par: Catégorie -> Sexe -> Temps
        """
        # Séparer les résultats valides des invalides
        valid_results = [r for r in results if r['status'] == 'FINISHED']
        invalid_results = [r for r in results if r['status'] != 'FINISHED']
        
        # Trier les résultats valides par catégorie, sexe, puis temps
        valid_results.sort(key=lambda x: (
            x['category'],
            x['sex'],
            x['total_seconds']
        ))
        
        # Attribuer les rangs par catégorie-sexe
        current_category = None
        current_sex = None
        rank = 0
        
        for result in valid_results:
            if (result['category'] != current_category or 
                result['sex'] != current_sex):
                current_category = result['category']
                current_sex = result['sex']
                rank = 1
            else:
                rank += 1
            
            result['rank'] = rank
        
        # Les résultats invalides n'ont pas de rang
        for result in invalid_results:
            result['rank'] = None
        
        # Retourner tous les résultats combinés
        return valid_results + invalid_results
    
    def get_podium_by_category(self, category: str, sex: str, top_n: int = 5) -> List[Dict]:
        """
        Retourne le podium pour une catégorie/sexe donnée
        
        Args:
            category: Catégorie (U6, U8, etc.)
            sex: Sexe (M, F)
            top_n: Nombre de résultats à retourner
            
        Returns:
            Liste des top_n résultats
        """
        all_results = self.calculate_final_results()
        
        # Filtrer par catégorie et sexe
        filtered = [
            r for r in all_results 
            if r['category'] == category and r['sex'] == sex and r['status'] == 'FINISHED'
        ]
        
        return filtered[:top_n]
    
    def export_podiums_to_excel(self, base_filepath: str):
        """
        Exporte les podiums de chaque catégorie-sexe dans des fichiers Excel séparés
        
        Args:
            base_filepath: Chemin de base (sans extension)
        """
        import pandas as pd
        from pathlib import Path
        
        all_results = self.calculate_final_results()
        
        # Obtenir toutes les combinaisons catégorie-sexe
        categories = set(r['category'] for r in all_results)
        sexes = set(r['sex'] for r in all_results)
        
        base_path = Path(base_filepath)
        base_path.parent.mkdir(parents=True, exist_ok=True)
        
        for category in sorted(categories):
            for sex in sorted(sexes):
                podium = self.get_podium_by_category(category, sex, top_n=5)
                
                if not podium:
                    continue
                
                # Préparer les données pour Excel
                data = []
                for result in podium:
                    athlete = next(a for a in self.race.athletes if a.bib == result['bib'])
                    data.append({
                        'Rang': result['rank'],
                        'Bib': result['bib'],
                        'Nom': athlete.last_name,
                        'Prénom': athlete.first_name,
                        'Club': athlete.team,
                        'Temps Total': result['total_display']
                    })
                
                df = pd.DataFrame(data)
                
                # Nom du fichier
                filename = base_path.parent / f"{base_path.stem}_{category}_{sex}.xlsx"
                
                # Export
                df.to_excel(filename, index=False, sheet_name=f"{category}-{sex}")
                print(f"Exporté: {filename}")
