"""
Interface de chronométrage pour saisie des temps
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Callable
from models import Run, Athlete, RunResult
from utils import validate_time_input, format_time_msscc


class TimingInterface(tk.Toplevel):
    """Interface de saisie des temps pour un run"""

    def __init__(self, parent, run: Run, race=None, on_complete: Optional[Callable] = None, on_save: Optional[Callable] = None):
        super().__init__(parent)

        self.run = run
        self.race = race
        self.on_complete = on_complete
        self.on_save = on_save
        self.current_index = 0
        self._updating_fields = False  # Flag pour éviter auto-avancement lors du pré-remplissage
        self._sec_invalid = False  # Flag pour validation des secondes

        # Créer le style pour les champs en erreur
        style = ttk.Style()
        style.configure('Error.TEntry', fieldbackground='#ffcccc')

        self.title(f"Chronometrage - Run {run.number}")
        self.geometry("1100x650")

        # Empêcher la fermeture sans confirmation
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_widgets()
        self._update_display()

    def _create_widgets(self):
        """Crée les widgets de l'interface"""

        # Frame principale avec PanedWindow
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panneau gauche - Liste des coureurs
        left_frame = ttk.Frame(main_pane, width=300)
        main_pane.add(left_frame, weight=1)

        self._create_athlete_list(left_frame)

        # Panneau droit - Saisie du temps
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)

        self._create_timing_panel(right_frame)

    def _create_athlete_list(self, parent):
        """Crée le panneau de la liste des coureurs"""

        # En-tête
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            header_frame,
            text="Liste des coureurs",
            font=('Arial', 12, 'bold')
        ).pack(side=tk.LEFT)

        # Frame pour la liste avec scrollbar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview pour la liste
        self.athlete_tree = ttk.Treeview(
            list_frame,
            columns=('order', 'bib', 'name', 'cat', 'sex', 'club', 'time', 'status'),
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        scrollbar.config(command=self.athlete_tree.yview)

        # Configuration des colonnes
        self.athlete_tree.heading('order', text='#')
        self.athlete_tree.heading('bib', text='Bib')
        self.athlete_tree.heading('name', text='Nom')
        self.athlete_tree.heading('cat', text='Cat')
        self.athlete_tree.heading('sex', text='S')
        self.athlete_tree.heading('club', text='Club')
        self.athlete_tree.heading('time', text='Temps')
        self.athlete_tree.heading('status', text='')

        self.athlete_tree.column('order', width=30, anchor='center')
        self.athlete_tree.column('bib', width=40, anchor='center')
        self.athlete_tree.column('name', width=130)
        self.athlete_tree.column('cat', width=40, anchor='center')
        self.athlete_tree.column('sex', width=25, anchor='center')
        self.athlete_tree.column('club', width=70)
        self.athlete_tree.column('time', width=60, anchor='center')
        self.athlete_tree.column('status', width=35, anchor='center')

        # Tags pour les couleurs
        self.athlete_tree.tag_configure('active', background='#fff3cd', font=('Arial', 10, 'bold'))
        self.athlete_tree.tag_configure('completed', background='#d4edda')
        self.athlete_tree.tag_configure('dns', background='#e2e3e5', foreground='gray')
        self.athlete_tree.tag_configure('dnf', background='#f8d7da', foreground='#721c24')
        self.athlete_tree.tag_configure('dsq', background='#fff3cd', foreground='#856404')
        self.athlete_tree.tag_configure('pending', background='white')
        self.athlete_tree.tag_configure('absent', background='#ffcccc')

        self.athlete_tree.pack(fill=tk.BOTH, expand=True)

        # Double-clic pour naviguer
        self.athlete_tree.bind('<Double-1>', self._on_list_double_click)

        # Frame pour "Aller au #"
        goto_frame = ttk.Frame(parent)
        goto_frame.pack(fill=tk.X, pady=10)

        ttk.Label(goto_frame, text="Aller au #").pack(side=tk.LEFT)
        self.goto_entry = ttk.Entry(goto_frame, width=6)
        self.goto_entry.pack(side=tk.LEFT, padx=5)
        self.goto_entry.bind('<Return>', lambda e: self._go_to_bib())

        ttk.Button(
            goto_frame,
            text="Go",
            command=self._go_to_bib,
            width=5
        ).pack(side=tk.LEFT)

        # Frame pour le tri
        sort_frame = ttk.LabelFrame(parent, text="Ordre de tri", padding="5")
        sort_frame.pack(fill=tk.X, pady=10)

        sort_options = [
            ('', '(aucun)'),
            ('category', 'Catégorie'),
            ('sex', 'Sexe'),
            ('bib_asc', 'Dossard ↑'),
            ('bib_desc', 'Dossard ↓'),
        ]

        # Déterminer les valeurs par défaut selon le numéro du run
        if self.run.number == 2:
            default_sort = ['category', 'bib_desc', '']
        else:
            default_sort = ['category', 'bib_asc', '']

        # Niveau 1
        ttk.Label(sort_frame, text="1:", font=('Arial', 9)).grid(row=0, column=0, padx=2)
        self.sort1_var = tk.StringVar(value=default_sort[0])
        sort1_combo = ttk.Combobox(sort_frame, textvariable=self.sort1_var, width=10, state='readonly')
        sort1_combo['values'] = [opt[1] for opt in sort_options]
        sort1_combo.current([opt[0] for opt in sort_options].index(default_sort[0]))
        sort1_combo.grid(row=0, column=1, padx=2)

        # Niveau 2
        ttk.Label(sort_frame, text="2:", font=('Arial', 9)).grid(row=0, column=2, padx=2)
        self.sort2_var = tk.StringVar(value=default_sort[1])
        sort2_combo = ttk.Combobox(sort_frame, textvariable=self.sort2_var, width=10, state='readonly')
        sort2_combo['values'] = [opt[1] for opt in sort_options]
        sort2_combo.current([opt[0] for opt in sort_options].index(default_sort[1]))
        sort2_combo.grid(row=0, column=3, padx=2)

        # Niveau 3
        ttk.Label(sort_frame, text="3:", font=('Arial', 9)).grid(row=0, column=4, padx=2)
        self.sort3_var = tk.StringVar(value=default_sort[2])
        sort3_combo = ttk.Combobox(sort_frame, textvariable=self.sort3_var, width=10, state='readonly')
        sort3_combo['values'] = [opt[1] for opt in sort_options]
        sort3_combo.current([opt[0] for opt in sort_options].index(default_sort[2]))
        sort3_combo.grid(row=0, column=5, padx=2)

        # Stocker la correspondance label -> valeur
        self._sort_options_map = {opt[1]: opt[0] for opt in sort_options}

        # Bouton appliquer
        ttk.Button(
            sort_frame,
            text="Trier",
            command=self._apply_sort,
            width=6
        ).grid(row=0, column=6, padx=5)

    def _create_timing_panel(self, parent):
        """Crée le panneau de saisie du temps"""

        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # En-tête avec progression
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text=f"RUN {self.run.number}",
            font=('Arial', 14, 'bold')
        ).pack(side=tk.LEFT)

        self.progress_label = ttk.Label(
            header_frame,
            text="",
            font=('Arial', 12)
        )
        self.progress_label.pack(side=tk.RIGHT)

        # Séparateur
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Zone d'information coureur EN ATTENTE (prochain)
        self.next_athlete_frame = ttk.LabelFrame(main_frame, text="EN ATTENTE", padding="8")
        self.next_athlete_frame.pack(fill=tk.X, pady=(5, 2))

        # Conteneur pour infos du prochain coureur
        next_info_frame = ttk.Frame(self.next_athlete_frame)
        next_info_frame.pack(fill=tk.X)

        self.next_bib_label = ttk.Label(
            next_info_frame,
            text="",
            font=('Arial', 14, 'bold')
        )
        self.next_bib_label.pack(side=tk.LEFT)

        self.next_name_label = ttk.Label(
            next_info_frame,
            text="",
            font=('Arial', 12)
        )
        self.next_name_label.pack(side=tk.LEFT, padx=10)

        self.next_info_label = ttk.Label(
            next_info_frame,
            text="",
            font=('Arial', 10)
        )
        self.next_info_label.pack(side=tk.LEFT, padx=10)

        # Frame pour les alertes du prochain coureur
        self.next_alert_frame = ttk.Frame(self.next_athlete_frame)
        self.next_alert_frame.pack(fill=tk.X, pady=(3, 0))

        self.next_category_alert_label = ttk.Label(
            self.next_alert_frame,
            text="",
            font=('Arial', 9, 'bold'),
            foreground='#856404',
            background='#fff3cd'
        )

        self.next_slow_alert_label = ttk.Label(
            self.next_alert_frame,
            text="",
            font=('Arial', 9, 'bold'),
            foreground='white',
            background='#dc3545'
        )

        # Zone d'information coureur ACTIF
        athlete_frame = ttk.LabelFrame(main_frame, text="COUREUR ACTIF", padding="15")
        athlete_frame.pack(fill=tk.X, pady=10)

        # Indicateur d'absence
        self.absent_label = ttk.Label(
            athlete_frame,
            text="ABSENT",
            font=('Arial', 12, 'bold'),
            foreground='red'
        )
        # Ne pas pack ici, sera affiché si nécessaire

        self.bib_label = ttk.Label(
            athlete_frame,
            text="Bib: ",
            font=('Arial', 24, 'bold')
        )
        self.bib_label.pack()

        self.name_label = ttk.Label(
            athlete_frame,
            text="",
            font=('Arial', 18)
        )
        self.name_label.pack()

        self.info_label = ttk.Label(
            athlete_frame,
            text="",
            font=('Arial', 12)
        )
        self.info_label.pack()

        # Frame pour les indicateurs d'alerte
        self.alert_frame = ttk.Frame(athlete_frame)
        self.alert_frame.pack(pady=5)

        # Indicateur dernier/avant-dernier de catégorie
        self.category_alert_label = ttk.Label(
            self.alert_frame,
            text="",
            font=('Arial', 11, 'bold'),
            foreground='#856404',
            background='#fff3cd'
        )

        # Indicateur coureur lent (pour runs 2+)
        self.slow_alert_label = ttk.Label(
            self.alert_frame,
            text="",
            font=('Arial', 11, 'bold'),
            foreground='white',
            background='#dc3545'
        )

        # Zone de saisie du temps
        time_frame = ttk.LabelFrame(main_frame, text="TEMPS", padding="15")
        time_frame.pack(fill=tk.X, pady=10)

        # Inputs pour le temps
        input_frame = ttk.Frame(time_frame)
        input_frame.pack()

        # Variables pour les champs
        self.min_var = tk.StringVar()
        self.sec_var = tk.StringVar()
        self.cent_var = tk.StringVar()

        # Minutes (1 caractère max)
        ttk.Label(input_frame, text="Min:", font=('Arial', 12)).grid(row=0, column=0, padx=5)
        self.min_entry = ttk.Entry(input_frame, width=2, font=('Arial', 18), textvariable=self.min_var)
        self.min_entry.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text=":", font=('Arial', 18)).grid(row=0, column=2)

        # Secondes (2 caractères max, validation 0-59)
        ttk.Label(input_frame, text="Sec:", font=('Arial', 12)).grid(row=0, column=3, padx=5)
        self.sec_entry = ttk.Entry(input_frame, width=3, font=('Arial', 18), textvariable=self.sec_var)
        self.sec_entry.grid(row=0, column=4, padx=5)

        ttk.Label(input_frame, text=".", font=('Arial', 18)).grid(row=0, column=5)

        # Centièmes (2 caractères max)
        ttk.Label(input_frame, text="Cent:", font=('Arial', 12)).grid(row=0, column=6, padx=5)
        self.cent_entry = ttk.Entry(input_frame, width=3, font=('Arial', 18), textvariable=self.cent_var)
        self.cent_entry.grid(row=0, column=7, padx=5)

        # Traces pour auto-avancement
        self.min_var.trace_add('write', self._on_min_change)
        self.sec_var.trace_add('write', self._on_sec_change)
        self.cent_var.trace_add('write', self._on_cent_change)

        # Bindings pour navigation entre champs (Return)
        self.min_entry.bind('<Return>', lambda e: self.sec_entry.focus())
        self.sec_entry.bind('<Return>', lambda e: self.cent_entry.focus())
        self.cent_entry.bind('<Return>', lambda e: self._save_time())

        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)

        # Styles pour boutons de statut (normal et actif/gras)
        style = ttk.Style()
        style.configure('Status.TButton', font=('Arial', 10, 'normal'))
        style.configure('StatusActive.TButton', font=('Arial', 10, 'bold'))

        # Boutons de statut (toggle)
        self.dns_button = ttk.Button(
            button_frame,
            text="DNS",
            command=lambda: self._toggle_status('DNS'),
            width=8,
            style='Status.TButton'
        )
        self.dns_button.pack(side=tk.LEFT, padx=3)

        self.dnf_button = ttk.Button(
            button_frame,
            text="DNF",
            command=lambda: self._toggle_status('DNF'),
            width=8,
            style='Status.TButton'
        )
        self.dnf_button.pack(side=tk.LEFT, padx=3)

        self.dsq_button = ttk.Button(
            button_frame,
            text="DSQ",
            command=lambda: self._toggle_status('DSQ'),
            width=8,
            style='Status.TButton'
        )
        self.dsq_button.pack(side=tk.LEFT, padx=3)

        # Dictionnaire pour accès facile aux boutons
        self._status_buttons = {
            'DNS': self.dns_button,
            'DNF': self.dnf_button,
            'DSQ': self.dsq_button
        }

        ttk.Button(
            button_frame,
            text="Enregistrer",
            command=self._save_time,
            width=12
        ).pack(side=tk.RIGHT, padx=3)

        # Zone historique
        history_frame = ttk.LabelFrame(main_frame, text="DERNIER COUREUR", padding="10")
        history_frame.pack(fill=tk.X, pady=10)

        self.history_label = ttk.Label(
            history_frame,
            text="",
            font=('Arial', 11)
        )
        self.history_label.pack()

        # Boutons de navigation
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            nav_frame,
            text="< Precedent",
            command=self._prev_athlete,
            width=12
        ).pack(side=tk.LEFT)

        ttk.Button(
            nav_frame,
            text="Terminer",
            command=self._finish,
            width=12
        ).pack(side=tk.RIGHT)

    def _category_sort_key(self, category: str) -> int:
        """Extrait le nombre de la catégorie pour le tri (U6->6, U10->10, etc.)"""
        import re
        match = re.search(r'\d+', category)
        if match:
            return int(match.group())
        return 999  # Catégories sans nombre à la fin

    def _apply_sort(self):
        """Applique le tri sélectionné"""
        # Récupérer les critères de tri
        sort1 = self._sort_options_map.get(self.sort1_var.get(), '')
        sort2 = self._sort_options_map.get(self.sort2_var.get(), '')
        sort3 = self._sort_options_map.get(self.sort3_var.get(), '')

        order = [s for s in [sort1, sort2, sort3] if s]

        if not order:
            messagebox.showwarning("Attention", "Veuillez sélectionner au moins un critère de tri")
            return

        # Construire les clés de tri
        from functools import cmp_to_key

        keys = []
        reverse_flags = []

        for criterion in order:
            if criterion == 'category':
                keys.append(lambda a: self._category_sort_key(a.category))
                reverse_flags.append(False)
            elif criterion == 'sex':
                keys.append(lambda a: a.sex)
                reverse_flags.append(False)
            elif criterion == 'bib_asc':
                keys.append(lambda a: a.bib)
                reverse_flags.append(False)
            elif criterion == 'bib_desc':
                keys.append(lambda a: a.bib)
                reverse_flags.append(True)

        def compare(a1, a2):
            for key_func, reverse in zip(keys, reverse_flags):
                val1 = key_func(a1)
                val2 = key_func(a2)
                if val1 < val2:
                    return 1 if reverse else -1
                elif val1 > val2:
                    return -1 if reverse else 1
            return 0

        # Trier les athlètes
        self.run.athletes.sort(key=cmp_to_key(compare))

        # Réinitialiser à la position 0
        self.current_index = 0
        self._update_display()

        # Sauvegarder
        if self.on_save:
            self.on_save()

        messagebox.showinfo("Tri appliqué", "L'ordre des coureurs a été mis à jour")

    def _on_min_change(self, *args):
        """Gère le changement du champ minutes"""
        if self._updating_fields:
            return
        val = self.min_var.get()
        # Garder seulement les chiffres
        filtered = ''.join(c for c in val if c.isdigit())
        # Limiter à 1 caractère
        if len(filtered) > 1:
            filtered = filtered[:1]
        if filtered != val:
            self._updating_fields = True
            self.min_var.set(filtered)
            self._updating_fields = False
        # Auto-avancer si 1 caractère saisi
        if len(filtered) == 1:
            self.sec_entry.focus()

    def _on_sec_change(self, *args):
        """Gère le changement du champ secondes"""
        if self._updating_fields:
            return
        val = self.sec_var.get()
        # Garder seulement les chiffres
        filtered = ''.join(c for c in val if c.isdigit())
        # Limiter à 2 caractères
        if len(filtered) > 2:
            filtered = filtered[:2]
        if filtered != val:
            self._updating_fields = True
            self.sec_var.set(filtered)
            self._updating_fields = False
        # Valider max 59 - mettre en rouge si invalide
        if filtered and int(filtered) > 59:
            self.sec_entry.configure(style='Error.TEntry')
            self._sec_invalid = True
        else:
            self.sec_entry.configure(style='TEntry')
            self._sec_invalid = False
        # Auto-avancer si 2 caractères saisis et valide
        if len(filtered) == 2 and not self._sec_invalid:
            self.cent_entry.focus()

    def _on_cent_change(self, *args):
        """Gère le changement du champ centièmes"""
        if self._updating_fields:
            return
        val = self.cent_var.get()
        # Garder seulement les chiffres
        filtered = ''.join(c for c in val if c.isdigit())
        # Limiter à 2 caractères
        if len(filtered) > 2:
            filtered = filtered[:2]
        if filtered != val:
            self._updating_fields = True
            self.cent_var.set(filtered)
            self._updating_fields = False

    def _get_category_position(self, athlete, from_index=None) -> tuple:
        """Retourne (position, total, label) du coureur dans sa catégorie+sexe parmi ceux restants"""
        category = athlete.category
        sex = athlete.sex

        if from_index is None:
            from_index = self.current_index

        # Trouver tous les coureurs de la même catégorie ET sexe à partir de l'index donné
        remaining = []
        for i, a in enumerate(self.run.athletes):
            if i >= from_index and a.category == category and a.sex == sex:
                remaining.append((i, a))

        # Trouver la position du coureur parmi les restants
        position = None
        for pos, (idx, a) in enumerate(remaining):
            if a.bib == athlete.bib:
                position = pos + 1
                break

        # Label pour l'affichage (ex: "U10 F" ou "U10 M")
        label = f"{category} {sex}"

        return position, len(remaining), label

    def _is_slow_runner(self, athlete) -> tuple:
        """Vérifie si le coureur est plus lent que la moyenne de sa catégorie (runs précédentes)
        Retourne (is_slow, previous_time, category_avg)"""
        if not self.race or self.run.number == 1:
            return False, None, None

        # Récupérer les temps des runs précédentes pour ce coureur
        athlete_times = []
        for prev_run in self.race.runs:
            if prev_run.number >= self.run.number:
                break
            result = prev_run.get_result(athlete.bib)
            if result and result.status == 'FINISHED' and result.time_seconds:
                athlete_times.append(result.time_seconds)

        if not athlete_times:
            return False, None, None

        athlete_avg = sum(athlete_times) / len(athlete_times)

        # Calculer la moyenne de la catégorie pour les runs précédentes
        category_times = []
        for prev_run in self.race.runs:
            if prev_run.number >= self.run.number:
                break
            for a in prev_run.athletes:
                if a.category == athlete.category:
                    result = prev_run.get_result(a.bib)
                    if result and result.status == 'FINISHED' and result.time_seconds:
                        category_times.append(result.time_seconds)

        if not category_times:
            return False, athlete_avg, None

        category_avg = sum(category_times) / len(category_times)

        # Considérer comme lent si > 10% plus lent que la moyenne
        is_slow = athlete_avg > category_avg * 1.10

        return is_slow, athlete_avg, category_avg

    def _update_alerts(self, athlete):
        """Met à jour les indicateurs d'alerte pour le coureur actuel"""
        # Cacher tous les labels d'alerte
        self.category_alert_label.pack_forget()
        self.slow_alert_label.pack_forget()

        # Vérifier position dans la catégorie+sexe
        position, total, label = self._get_category_position(athlete)
        if position and total:
            if position == total and total > 0:
                self.category_alert_label.config(text=f"  DERNIER {label}  ")
                self.category_alert_label.pack(side=tk.LEFT, padx=5)
            elif position == total - 1 and total > 1:
                self.category_alert_label.config(text=f"  AVANT-DERNIER {label}  ")
                self.category_alert_label.pack(side=tk.LEFT, padx=5)

        # Vérifier si coureur lent (runs 2+)
        is_slow, athlete_time, category_avg = self._is_slow_runner(athlete)
        if is_slow and athlete_time:
            from utils import format_time_msscc
            self.slow_alert_label.config(text=f"  LENT ({format_time_msscc(athlete_time)})  ")
            self.slow_alert_label.pack(side=tk.LEFT, padx=5)

    def _update_next_athlete(self):
        """Met à jour l'affichage du coureur en attente (prochain)"""
        next_index = self.current_index + 1

        # Cacher les alertes du prochain coureur
        self.next_category_alert_label.pack_forget()
        self.next_slow_alert_label.pack_forget()

        if next_index >= len(self.run.athletes):
            # Pas de prochain coureur
            self.next_bib_label.config(text="")
            self.next_name_label.config(text="(aucun)")
            self.next_info_label.config(text="")
            return

        next_athlete = self.run.athletes[next_index]

        # Mettre à jour les infos
        self.next_bib_label.config(text=f"#{next_athlete.bib}")
        self.next_name_label.config(text=f"{next_athlete.last_name} {next_athlete.first_name}")
        self.next_info_label.config(text=f"{next_athlete.category} - {next_athlete.sex} - {next_athlete.team}")

        # Vérifier position dans la catégorie+sexe (à partir du prochain coureur)
        position, total, label = self._get_category_position(next_athlete, from_index=next_index)
        if position and total:
            if position == total and total > 0:
                self.next_category_alert_label.config(text=f"  DERNIER {label}  ")
                self.next_category_alert_label.pack(side=tk.LEFT, padx=3)
            elif position == total - 1 and total > 1:
                self.next_category_alert_label.config(text=f"  AVANT-DERNIER {label}  ")
                self.next_category_alert_label.pack(side=tk.LEFT, padx=3)

        # Vérifier si coureur lent (runs 2+)
        is_slow, athlete_time, category_avg = self._is_slow_runner(next_athlete)
        if is_slow and athlete_time:
            from utils import format_time_msscc
            self.next_slow_alert_label.config(text=f"  LENT ({format_time_msscc(athlete_time)})  ")
            self.next_slow_alert_label.pack(side=tk.LEFT, padx=3)

    def _update_athlete_list(self):
        """Met à jour la liste des coureurs"""
        # Sauvegarder la sélection actuelle
        current_item = None

        # Vider la liste
        for item in self.athlete_tree.get_children():
            self.athlete_tree.delete(item)

        # Remplir avec les données
        for i, athlete in enumerate(self.run.athletes):
            result = self.run.get_result(athlete.bib)

            # Déterminer le tag
            if i == self.current_index:
                tag = 'active'
            elif result.status == 'FINISHED':
                tag = 'completed'
            elif result.status == 'DNS':
                tag = 'dns'
            elif result.status == 'DNF':
                tag = 'dnf'
            elif result.status == 'DSQ':
                tag = 'dsq'
            else:
                # Vérifier si absent
                if hasattr(athlete, 'status') and athlete.status == 'ABSENT':
                    tag = 'absent'
                else:
                    tag = 'pending'

            # Temps à afficher (toujours montrer le temps s'il existe)
            if result.time_display:
                time_display = result.time_display
            elif result.status in ['DNS', 'DNF', 'DSQ']:
                time_display = '-'  # Pas de temps enregistré
            else:
                time_display = '-'

            # Indicateur de statut
            status_icon = ''
            if result.status == 'FINISHED':
                status_icon = ''
            elif result.status in ['DNS', 'DNF', 'DSQ']:
                status_icon = result.status

            item_id = self.athlete_tree.insert('', tk.END, values=(
                i + 1,
                athlete.bib,
                f"{athlete.first_name} {athlete.last_name}",
                athlete.category,
                athlete.sex,
                athlete.team,
                time_display,
                status_icon
            ), tags=(tag,))

            if i == self.current_index:
                current_item = item_id

        # Scroll vers le coureur actif
        if current_item:
            self.athlete_tree.see(current_item)
            self.athlete_tree.selection_set(current_item)

    def _update_display(self):
        """Met à jour l'affichage pour le coureur actuel"""
        if self.current_index >= len(self.run.athletes):
            self._finish()
            return

        athlete = self.run.athletes[self.current_index]
        result = self.run.get_result(athlete.bib)

        # Indicateur d'absence
        if hasattr(athlete, 'status') and athlete.status == 'ABSENT':
            self.absent_label.pack(before=self.bib_label)
        else:
            self.absent_label.pack_forget()

        # Mettre à jour les labels
        self.bib_label.config(text=f"Bib: #{athlete.bib}")
        self.name_label.config(text=f"{athlete.last_name} {athlete.first_name}")
        self.info_label.config(text=f"{athlete.category} - {athlete.sex} - {athlete.team}")

        # Mettre à jour les alertes (dernier de catégorie, coureur lent)
        self._update_alerts(athlete)

        # Mettre à jour le coureur en attente (prochain)
        self._update_next_athlete()

        # Progression
        completed, total = self.run.get_completion_rate()
        self.progress_label.config(text=f"[{completed}/{total}]")

        # Pré-remplir si déjà saisi (désactiver auto-avancement)
        self._updating_fields = True
        self._sec_invalid = False
        self.sec_entry.configure(style='TEntry')

        # Afficher le temps s'il existe (même avec statut DSQ/DNF/DNS)
        if result and result.time_display and ':' in result.time_display:
            time_str = result.time_display
            parts = time_str.split(':')
            self.min_var.set(parts[0])
            sec_parts = parts[1].split('.')
            self.sec_var.set(sec_parts[0])
            self.cent_var.set(sec_parts[1])
        else:
            # Vider les champs
            self.min_var.set('')
            self.sec_var.set('')
            self.cent_var.set('')
        self._updating_fields = False

        # Mettre à jour les boutons de statut
        self._update_status_buttons(result)

        # Focus sur le premier champ
        self.min_entry.focus()

        # Mettre à jour l'historique
        if self.current_index > 0:
            prev_athlete = self.run.athletes[self.current_index - 1]
            prev_result = self.run.get_result(prev_athlete.bib)
            self.history_label.config(
                text=f"#{prev_athlete.bib} {prev_athlete.last_name} - {prev_result.time_display}"
            )
        else:
            self.history_label.config(text="")

        # Mettre à jour la liste
        self._update_athlete_list()

    def _auto_save_current(self) -> bool:
        """Sauvegarde automatiquement le temps saisi si les champs sont remplis.
        Retourne True si une sauvegarde a été effectuée ou si les champs sont vides."""
        min_val = self.min_entry.get().strip()
        sec_val = self.sec_entry.get().strip()
        cent_val = self.cent_entry.get().strip()

        # Si tous les champs sont vides, rien à sauvegarder
        if not min_val and not sec_val and not cent_val:
            return True

        # Si au moins un champ est rempli, valider et sauvegarder
        valid, error = validate_time_input(min_val, sec_val, cent_val)

        if not valid:
            response = messagebox.askyesno(
                "Temps invalide",
                f"Le temps saisi est invalide: {error}\n\n"
                "Voulez-vous continuer sans sauvegarder?"
            )
            return response

        # Sauvegarder le temps
        athlete = self.run.athletes[self.current_index]
        minutes = int(min_val or 0)
        seconds = int(sec_val or 0)
        centiseconds = int(cent_val or 0)

        total_seconds = minutes * 60 + seconds + centiseconds / 100
        time_display = format_time_msscc(total_seconds)

        # Récupérer le résultat existant pour conserver le statut si DSQ/DNF/DNS
        result = self.run.get_result(athlete.bib)
        if result is None:
            result = RunResult(bib=athlete.bib)

        # Si le statut est DSQ/DNF/DNS, ne pas écraser - juste mettre à jour le temps
        if result.status in ['DNS', 'DNF', 'DSQ']:
            result.time_seconds = total_seconds
            result.time_display = time_display
        else:
            result.set_time(total_seconds, time_display)

        self.run.set_result(athlete.bib, result)

        # Sauvegarde automatique
        if self.on_save:
            self.on_save()

        return True

    def _go_to_athlete(self, index: int):
        """Navigate vers un coureur spécifique par son index"""
        if index < 0 or index >= len(self.run.athletes):
            return

        athlete = self.run.athletes[index]

        # Confirmation
        response = messagebox.askyesno(
            "Navigation",
            f"Aller au coureur #{athlete.bib} {athlete.last_name}?"
        )

        if not response:
            return

        # Auto-save si nécessaire
        if not self._auto_save_current():
            return

        self.current_index = index
        self._update_display()

    def _go_to_bib(self):
        """Navigate vers un coureur par son numéro de dossard"""
        bib_str = self.goto_entry.get().strip()

        if not bib_str:
            return

        try:
            bib = int(bib_str)
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un numéro valide")
            return

        # Trouver l'index du coureur
        for i, athlete in enumerate(self.run.athletes):
            if athlete.bib == bib:
                self._go_to_athlete(i)
                self.goto_entry.delete(0, tk.END)
                return

        messagebox.showerror("Erreur", f"Coureur #{bib} non trouvé dans ce run")

    def _on_list_double_click(self, event):
        """Gère le double-clic sur la liste"""
        selection = self.athlete_tree.selection()
        if not selection:
            return

        # Récupérer l'index à partir de la première colonne (ordre)
        item = self.athlete_tree.item(selection[0])
        order = int(item['values'][0])
        index = order - 1

        if index != self.current_index:
            self._go_to_athlete(index)

    def _save_time(self):
        """Enregistre le temps saisi"""
        athlete = self.run.athletes[self.current_index]

        # Vérifier si les secondes sont invalides
        if self._sec_invalid:
            messagebox.showwarning("Secondes invalides", "Les secondes doivent être entre 0 et 59")
            self.sec_entry.focus()
            return

        # Valider l'entrée
        valid, error = validate_time_input(
            self.min_entry.get(),
            self.sec_entry.get(),
            self.cent_entry.get()
        )

        if not valid:
            messagebox.showerror("Erreur", error)
            return

        # Calculer le temps
        minutes = int(self.min_entry.get() or 0)
        seconds = int(self.sec_entry.get() or 0)
        centiseconds = int(self.cent_entry.get() or 0)

        total_seconds = minutes * 60 + seconds + centiseconds / 100
        time_display = format_time_msscc(total_seconds)

        # Enregistrer (récupérer le résultat existant ou en créer un nouveau)
        result = self.run.get_result(athlete.bib)
        if result is None:
            result = RunResult(bib=athlete.bib)
        result.set_time(total_seconds, time_display)
        self.run.set_result(athlete.bib, result)

        # Sauvegarde automatique
        if self.on_save:
            self.on_save()

        # Passer au suivant
        self.current_index += 1
        self._update_display()

    def _update_status_buttons(self, result):
        """Met à jour l'apparence des boutons de statut selon le résultat actuel"""
        current_status = result.status if result else 'PENDING'

        for status, button in self._status_buttons.items():
            if current_status == status:
                # Bouton actif - texte en gras
                button.configure(style='StatusActive.TButton')
            else:
                # Bouton inactif - texte normal
                button.configure(style='Status.TButton')

    def _toggle_status(self, status: str):
        """Toggle un statut spécial (DNS, DNF, DSQ)"""
        athlete = self.run.athletes[self.current_index]

        # Récupérer le résultat existant
        result = self.run.get_result(athlete.bib)
        if result is None:
            result = RunResult(bib=athlete.bib)

        # Sauvegarder le temps saisi dans les champs (s'il y en a un valide)
        min_val = self.min_entry.get().strip()
        sec_val = self.sec_entry.get().strip()
        cent_val = self.cent_entry.get().strip()

        if min_val or sec_val or cent_val:
            valid, error = validate_time_input(min_val, sec_val, cent_val)
            if valid:
                minutes = int(min_val or 0)
                seconds = int(sec_val or 0)
                centiseconds = int(cent_val or 0)
                total_seconds = minutes * 60 + seconds + centiseconds / 100
                time_display = format_time_msscc(total_seconds)
                result.time_seconds = total_seconds
                result.time_display = time_display

        if result.status == status:
            # Désactiver le statut - revenir à FINISHED si temps existe, sinon PENDING
            if result.time_seconds is not None:
                result.status = 'FINISHED'
            else:
                result.status = 'PENDING'
        else:
            # Activer ce statut
            result.set_status(status)

        self.run.set_result(athlete.bib, result)

        # Sauvegarde automatique
        if self.on_save:
            self.on_save()

        # Mettre à jour l'affichage (sans changer de coureur)
        self._update_status_buttons(result)
        self._update_athlete_list()

    def _prev_athlete(self):
        """Revenir au coureur précédent"""
        if self.current_index > 0:
            # Auto-save si nécessaire
            if not self._auto_save_current():
                return

            self.current_index -= 1
            self._update_display()

    def _finish(self):
        """Termine le chronométrage"""
        completed, total = self.run.get_completion_rate()

        if completed < total:
            response = messagebox.askyesno(
                "Confirmation",
                f"Seulement {completed}/{total} coureurs ont un temps enregistré.\n"
                "Voulez-vous vraiment terminer?"
            )
            if not response:
                return

        if self.on_complete:
            self.on_complete()

        self.destroy()

    def _on_close(self):
        """Gère la fermeture de la fenêtre"""
        response = messagebox.askyesno(
            "Confirmer",
            "Voulez-vous vraiment quitter le chronometrage?"
        )
        if response:
            self.destroy()
