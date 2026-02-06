"""
Modèles de données pour l'application de chronométrage
"""
from dataclasses import dataclass, field
from typing import Optional, List
import json


@dataclass
class Athlete:
    """Représente un athlète"""
    bib: int
    start_number: int
    first_name: str
    last_name: str
    category: str  # U6, U8, U10, etc.
    sex: str  # M, F
    team: str
    year_of_birth: int
    nat_number: str = ""
    status: str = "ACTIVE"  # ACTIVE ou ABSENT
    
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def display_name(self) -> str:
        return f"#{self.bib} - {self.last_name} {self.first_name}"
    
    def to_dict(self) -> dict:
        return {
            'bib': self.bib,
            'start_number': self.start_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'category': self.category,
            'sex': self.sex,
            'team': self.team,
            'year_of_birth': self.year_of_birth,
            'nat_number': self.nat_number,
            'status': self.status
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Athlete':
        # Rétrocompatibilité: ajouter status si absent
        if 'status' not in data:
            data['status'] = 'ACTIVE'
        return Athlete(**data)


@dataclass
class RunResult:
    """Résultat d'un run pour un athlète"""
    bib: int
    time_seconds: Optional[float] = None  # Temps en secondes décimales
    time_display: str = ""  # Temps en format m:ss.cc
    status: str = "PENDING"  # PENDING, FINISHED, DNS, DNF, DSQ
    
    def set_time(self, seconds: float, display: str):
        self.time_seconds = seconds
        self.time_display = display
        self.status = "FINISHED"
    
    def set_status(self, status: str):
        """Change le statut sans effacer le temps enregistré"""
        self.status = status
        # Ne plus effacer time_seconds ni time_display pour pouvoir revenir en arrière
    
    def is_valid(self) -> bool:
        return self.status == "FINISHED" and self.time_seconds is not None
    
    def to_dict(self) -> dict:
        return {
            'bib': self.bib,
            'time_seconds': self.time_seconds,
            'time_display': self.time_display,
            'status': self.status
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'RunResult':
        return RunResult(**data)


@dataclass
class Run:
    """Représente une manche de course"""
    number: int  # 1, 2, 3
    athletes: List[Athlete] = field(default_factory=list)
    results: dict = field(default_factory=dict)  # {bib: RunResult}
    
    def add_athlete(self, athlete: Athlete):
        self.athletes.append(athlete)
        self.results[athlete.bib] = RunResult(bib=athlete.bib)
    
    def get_result(self, bib: int) -> Optional[RunResult]:
        return self.results.get(bib)
    
    def set_result(self, bib: int, result: RunResult):
        self.results[bib] = result
    
    def get_completion_rate(self) -> tuple:
        """Retourne (complétés, total)"""
        completed = sum(1 for r in self.results.values() if r.status != "PENDING")
        return completed, len(self.results)
    
    def to_dict(self) -> dict:
        return {
            'number': self.number,
            'athletes': [a.to_dict() for a in self.athletes],
            'results': {bib: r.to_dict() for bib, r in self.results.items()}
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Run':
        run = Run(number=data['number'])
        run.athletes = [Athlete.from_dict(a) for a in data['athletes']]
        run.results = {int(bib): RunResult.from_dict(r) for bib, r in data['results'].items()}
        return run


@dataclass
class RaceConfig:
    """Configuration de la course"""
    race_name: str = "Course sans nom"
    race_date: str = ""
    num_runs: int = 2  # 1, 2, ou 3
    calculation_method: str = "BEST_2"  # BEST_1, BEST_2, SUM_3
    
    # Ordres de départ pour chaque run
    run1_order: List[str] = field(default_factory=lambda: ['category', 'bib_asc'])
    run2_order: List[str] = field(default_factory=lambda: ['category', 'bib_desc'])
    run3_order: List[str] = field(default_factory=lambda: ['category', 'bib_asc'])
    
    def to_dict(self) -> dict:
        return {
            'race_name': self.race_name,
            'race_date': self.race_date,
            'num_runs': self.num_runs,
            'calculation_method': self.calculation_method,
            'run1_order': self.run1_order,
            'run2_order': self.run2_order,
            'run3_order': self.run3_order
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'RaceConfig':
        return RaceConfig(**data)


@dataclass
class Race:
    """Représente une course complète"""
    config: RaceConfig = field(default_factory=RaceConfig)
    athletes: List[Athlete] = field(default_factory=list)
    runs: List[Run] = field(default_factory=list)
    
    def add_athlete(self, athlete: Athlete):
        self.athletes.append(athlete)
    
    def generate_runs(self):
        """Génère les runs selon la configuration"""
        self.runs = []
        
        for run_num in range(1, self.config.num_runs + 1):
            run = Run(number=run_num)
            
            # Déterminer l'ordre pour ce run
            if run_num == 1:
                order = self.config.run1_order
            elif run_num == 2:
                order = self.config.run2_order
            else:
                order = self.config.run3_order
            
            # Trier les athlètes selon l'ordre
            sorted_athletes = self._sort_athletes(order)
            
            for athlete in sorted_athletes:
                run.add_athlete(athlete)
            
            self.runs.append(run)
    
    def _category_sort_key(self, category: str) -> int:
        """Extrait le nombre de la catégorie pour le tri (U6->6, U10->10, etc.)"""
        import re
        match = re.search(r'\d+', category)
        if match:
            return int(match.group())
        return 999  # Catégories sans nombre à la fin

    def _sort_athletes(self, order: List[str]) -> List[Athlete]:
        """Trie les athlètes selon l'ordre spécifié"""
        athletes = self.athletes.copy()

        # Clés de tri
        keys = []
        reverse_flags = []

        for criterion in order:
            if criterion == 'category':
                keys.append(lambda a, c=criterion: self._category_sort_key(a.category))
                reverse_flags.append(False)
            elif criterion == 'sex':
                keys.append(lambda a, c=criterion: a.sex)
                reverse_flags.append(False)
            elif criterion == 'bib_asc':
                keys.append(lambda a, c=criterion: a.bib)
                reverse_flags.append(False)
            elif criterion == 'bib_desc':
                keys.append(lambda a, c=criterion: a.bib)
                reverse_flags.append(True)
            elif criterion == 'start_asc':
                keys.append(lambda a, c=criterion: a.start_number)
                reverse_flags.append(False)
            elif criterion == 'start_desc':
                keys.append(lambda a, c=criterion: a.start_number)
                reverse_flags.append(True)
        
        # Tri multiple
        from functools import cmp_to_key
        
        def compare(a1, a2):
            for key_func, reverse in zip(keys, reverse_flags):
                val1 = key_func(a1)
                val2 = key_func(a2)
                if val1 < val2:
                    return 1 if reverse else -1
                elif val1 > val2:
                    return -1 if reverse else 1
            return 0
        
        athletes.sort(key=cmp_to_key(compare))
        return athletes
    
    def save(self, filepath: str):
        """Sauvegarde la course en JSON"""
        data = {
            'config': self.config.to_dict(),
            'athletes': [a.to_dict() for a in self.athletes],
            'runs': [r.to_dict() for r in self.runs]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load(filepath: str) -> 'Race':
        """Charge une course depuis JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        race = Race()
        race.config = RaceConfig.from_dict(data['config'])
        race.athletes = [Athlete.from_dict(a) for a in data['athletes']]
        race.runs = [Run.from_dict(r) for r in data['runs']]
        return race
