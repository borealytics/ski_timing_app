"""
Fenêtre principale de l'application
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import datetime

from models import Race, RaceConfig, Athlete
from csv_importer import CSVImporter
from timing_interface import TimingInterface
from results import ResultsCalculator
from athlete_manager import AthleteManagerWindow


class MainWindow(tk.Tk):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()

        self.title("Ski Timing Manager")
        self.geometry("900x700")

        self.race = None
        self.current_file = None

        # Confirmation avant de fermer l'application
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_menu()
        self._show_welcome_screen()

    def _on_close(self):
        """Gère la fermeture de l'application"""
        if self.race:
            response = messagebox.askyesnocancel(
                "Quitter",
                "Voulez-vous sauvegarder la course avant de quitter?"
            )
            if response is None:  # Cancel
                return
            if response:  # Yes - sauvegarder
                self._save_race()
        self.destroy()
    
    def _create_menu(self):
        """Crée la barre de menu"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouvelle Course", command=self._new_race)
        file_menu.add_command(label="Ouvrir Course", command=self._open_race)
        file_menu.add_command(label="Sauvegarder", command=self._save_race)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self._show_about)
    
    def _show_welcome_screen(self):
        """Affiche l'écran d'accueil"""
        self._clear_main_frame()
        
        frame = ttk.Frame(self, padding="50")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="Ski Timing Manager",
            font=('Arial', 24, 'bold')
        ).pack(pady=30)
        
        ttk.Label(
            frame,
            text="Gestion de chronométrage pour courses de ski alpin",
            font=('Arial', 12)
        ).pack(pady=10)
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=50)
        
        ttk.Button(
            button_frame,
            text="Nouvelle Course",
            command=self._new_race,
            width=20
        ).pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Ouvrir Course Existante",
            command=self._open_race,
            width=20
        ).pack(pady=10)
    
    def _clear_main_frame(self):
        """Efface le contenu de la fenêtre"""
        for widget in self.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()
    
    def _new_race(self):
        """Démarre une nouvelle course"""
        self.race = Race()
        self._show_import_screen()
    
    def _open_race(self):
        """Ouvre une course existante"""
        filepath = filedialog.askopenfilename(
            title="Ouvrir une course",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.race = Race.load(filepath)
                self.current_file = filepath
                self._show_race_management()
                messagebox.showinfo("Succès", "Course chargée avec succès!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier:\n{e}")
    
    def _save_race(self):
        """Sauvegarde la course"""
        if not self.race:
            messagebox.showwarning("Attention", "Aucune course à sauvegarder")
            return
        
        if not self.current_file:
            filepath = filedialog.asksaveasfilename(
                title="Sauvegarder la course",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not filepath:
                return
            self.current_file = filepath
        
        try:
            self.race.save(self.current_file)
            messagebox.showinfo("Succès", "Course sauvegardée!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde:\n{e}")
    
    def _show_import_screen(self):
        """Écran d'import des coureurs"""
        self._clear_main_frame()
        
        frame = ttk.Frame(self, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="1. Importer les coureurs",
            font=('Arial', 18, 'bold')
        ).pack(pady=20)
        
        ttk.Label(
            frame,
            text="Importez le fichier CSV exporté de National/FIS Software",
            font=('Arial', 11)
        ).pack(pady=10)
        
        # Frame pour le bouton et le label
        import_frame = ttk.Frame(frame)
        import_frame.pack(pady=20)
        
        self.import_label = ttk.Label(import_frame, text="Aucun fichier sélectionné")
        self.import_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            import_frame,
            text="Parcourir...",
            command=self._import_athletes
        ).pack(side=tk.LEFT)
        
        # Frame pour la suite
        self.next_frame = ttk.Frame(frame)
        self.next_frame.pack(pady=30)
    
    def _import_athletes(self):
        """Import des athlètes depuis CSV"""
        filepath = filedialog.askopenfilename(
            title="Importer les coureurs",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                athletes = CSVImporter.import_athletes(filepath)
                
                if not athletes:
                    messagebox.showwarning("Attention", "Aucun coureur trouvé dans le fichier")
                    return
                
                # Ajouter les athlètes à la course
                self.race.athletes = athletes
                
                self.import_label.config(text=f"{len(athletes)} coureurs importés")
                
                # Afficher le bouton suivant
                ttk.Button(
                    self.next_frame,
                    text="Suivant: Configuration →",
                    command=self._show_config_screen
                ).pack()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{e}")
    
    def _show_config_screen(self):
        """Écran de configuration de la course"""
        self._clear_main_frame()
        
        frame = ttk.Frame(self, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="2. Configuration de la course",
            font=('Arial', 18, 'bold')
        ).pack(pady=20)
        
        # Nom de la course
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill=tk.X, pady=10)
        ttk.Label(name_frame, text="Nom de la course:", width=20).pack(side=tk.LEFT)
        self.race_name_var = tk.StringVar(value=f"Course {datetime.date.today()}")
        ttk.Entry(name_frame, textvariable=self.race_name_var, width=40).pack(side=tk.LEFT)
        
        # Type de course
        type_frame = ttk.LabelFrame(frame, text="Type de course", padding="15")
        type_frame.pack(fill=tk.X, pady=10)
        
        self.num_runs_var = tk.IntVar(value=2)
        ttk.Radiobutton(type_frame, text="1 run", variable=self.num_runs_var, value=1).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="2 runs", variable=self.num_runs_var, value=2).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="3 runs", variable=self.num_runs_var, value=3).pack(anchor=tk.W)
        
        # Méthode de calcul
        calc_frame = ttk.LabelFrame(frame, text="Méthode de calcul", padding="15")
        calc_frame.pack(fill=tk.X, pady=10)
        
        self.calc_method_var = tk.StringVar(value="BEST_2")
        ttk.Radiobutton(calc_frame, text="Meilleur temps", variable=self.calc_method_var, value="BEST_1").pack(anchor=tk.W)
        ttk.Radiobutton(calc_frame, text="2 meilleurs temps", variable=self.calc_method_var, value="BEST_2").pack(anchor=tk.W)
        ttk.Radiobutton(calc_frame, text="Somme des 3 temps", variable=self.calc_method_var, value="SUM_3").pack(anchor=tk.W)
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=30)
        
        ttk.Button(
            button_frame,
            text="← Retour",
            command=self._show_import_screen
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="Générer les runs",
            command=self._generate_runs
        ).pack(side=tk.LEFT, padx=10)
    
    def _generate_runs(self):
        """Génère les runs selon la configuration"""
        # Mettre à jour la config
        self.race.config.race_name = self.race_name_var.get()
        self.race.config.num_runs = self.num_runs_var.get()
        self.race.config.calculation_method = self.calc_method_var.get()

        # Générer les runs
        self.race.generate_runs()

        # Demander où sauvegarder
        if not self.current_file:
            default_name = f"course_{datetime.date.today()}.json"
            filepath = filedialog.asksaveasfilename(
                title="Sauvegarder la course",
                defaultextension=".json",
                initialfile=default_name,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not filepath:
                # L'utilisateur a annulé, utiliser le nom par défaut dans le répertoire courant
                filepath = default_name
            self.current_file = filepath

        self.race.save(self.current_file)

        messagebox.showinfo("Succès", f"{self.race.config.num_runs} runs générés!\n\nSauvegardé dans:\n{self.current_file}")
        self._show_race_management()
    
    def _show_race_management(self):
        """Écran de gestion de la course"""
        self._clear_main_frame()
        
        frame = ttk.Frame(self, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # En-tête
        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=20)
        
        ttk.Label(
            header,
            text=self.race.config.race_name,
            font=('Arial', 18, 'bold')
        ).pack()
        
        ttk.Label(
            header,
            text=f"{len(self.race.athletes)} coureurs - {self.race.config.num_runs} runs",
            font=('Arial', 11)
        ).pack()

        # Afficher le chemin du fichier
        if self.current_file:
            file_frame = ttk.Frame(header)
            file_frame.pack(pady=5)
            ttk.Label(
                file_frame,
                text="Fichier:",
                font=('Arial', 9)
            ).pack(side=tk.LEFT)
            ttk.Label(
                file_frame,
                text=self.current_file,
                font=('Arial', 9, 'italic'),
                foreground='gray'
            ).pack(side=tk.LEFT, padx=5)

        # Bouton gestion des coureurs
        ttk.Button(
            header,
            text="Gerer les coureurs",
            command=self._open_athlete_manager
        ).pack(pady=10)

        # Runs
        runs_frame = ttk.LabelFrame(frame, text="Chronométrage", padding="15")
        runs_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        for run in self.race.runs:
            run_frame = ttk.Frame(runs_frame)
            run_frame.pack(fill=tk.X, pady=5)
            
            completed, total = run.get_completion_rate()
            
            ttk.Label(
                run_frame,
                text=f"Run {run.number}:",
                width=10,
                font=('Arial', 12, 'bold')
            ).pack(side=tk.LEFT)
            
            ttk.Label(
                run_frame,
                text=f"[{completed}/{total}]",
                width=10
            ).pack(side=tk.LEFT)
            
            ttk.Button(
                run_frame,
                text="Chronomètrer",
                command=lambda r=run: self._open_timing(r)
            ).pack(side=tk.LEFT, padx=10)
            
            ttk.Button(
                run_frame,
                text="Importer résultats CSV",
                command=lambda r=run: self._import_run_results(r)
            ).pack(side=tk.LEFT)
        
        # Résultats
        results_frame = ttk.LabelFrame(frame, text="Résultats", padding="15")
        results_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            results_frame,
            text="Calculer résultats finaux",
            command=self._show_results
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            results_frame,
            text="Exporter podiums (Excel)",
            command=self._export_podiums
        ).pack(side=tk.LEFT, padx=5)
    
    def _open_timing(self, run):
        """Ouvre l'interface de chronométrage"""
        def on_save():
            # Sauvegarder automatiquement après chaque temps
            if self.current_file:
                self.race.save(self.current_file)

        TimingInterface(self, run, race=self.race, on_complete=lambda: self._show_race_management(), on_save=on_save)

    def _open_athlete_manager(self):
        """Ouvre la fenêtre de gestion des coureurs"""
        def on_update():
            # Sauvegarder automatiquement après modifications
            if self.current_file:
                self.race.save(self.current_file)

        AthleteManagerWindow(self, self.race, on_update=on_update)
    
    def _import_run_results(self, run):
        """Importe les résultats d'un run depuis CSV"""
        filepath = filedialog.askopenfilename(
            title=f"Importer résultats Run {run.number}",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            imported_results = CSVImporter.import_run_results(filepath, run.number)
            
            # Comparer avec les résultats manuels
            differences = CSVImporter.compare_results(run.results, imported_results)
            
            if differences:
                self._show_differences(differences, run, imported_results)
            else:
                messagebox.showinfo("Validation", "Aucune différence trouvée! 🎉")
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{e}")
    
    def _show_differences(self, differences, run, imported_results):
        """Affiche les différences trouvées"""
        diff_window = tk.Toplevel(self)
        diff_window.title("Validation - Différences trouvées")
        diff_window.geometry("950x500")

        frame = ttk.Frame(diff_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text=f"{len(differences)} différence(s) trouvée(s)",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)

        # Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(
            tree_frame,
            columns=('bib', 'name', 'category', 'club', 'manual', 'imported', 'diff'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)

        tree.heading('bib', text='Bib')
        tree.heading('name', text='Nom')
        tree.heading('category', text='Cat.')
        tree.heading('club', text='Club')
        tree.heading('manual', text='Manuel')
        tree.heading('imported', text='Importé')
        tree.heading('diff', text='Différence')

        tree.column('bib', width=50, anchor='center')
        tree.column('name', width=150)
        tree.column('category', width=50, anchor='center')
        tree.column('club', width=120)
        tree.column('manual', width=80, anchor='center')
        tree.column('imported', width=80, anchor='center')
        tree.column('diff', width=150)

        tree.pack(fill=tk.BOTH, expand=True)

        for diff in differences:
            # Trouver l'athlète correspondant
            athlete = next((a for a in self.race.athletes if a.bib == diff['bib']), None)
            if athlete:
                name = f"{athlete.first_name} {athlete.last_name}"
                category = athlete.category
                club = athlete.team
            else:
                name = "Inconnu"
                category = ""
                club = ""

            tree.insert('', tk.END, values=(
                diff['bib'],
                name,
                category,
                club,
                diff['manual'],
                diff['imported'],
                diff['diff']
            ))
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Utiliser les valeurs importées",
            command=lambda: self._apply_imported_results(run, imported_results, diff_window)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Fermer",
            command=diff_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def _apply_imported_results(self, run, imported_results, window):
        """Applique les résultats importés"""
        run.results = imported_results
        messagebox.showinfo("Succès", "Résultats importés appliqués!")
        window.destroy()
        self._show_race_management()
    
    def _show_results(self):
        """Affiche les résultats finaux"""
        calculator = ResultsCalculator(self.race)
        results = calculator.calculate_final_results()

        results_window = tk.Toplevel(self)
        results_window.title("Résultats Finaux")
        results_window.geometry("1000x600")

        frame = ttk.Frame(results_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Résultats Finaux",
            font=('Arial', 16, 'bold')
        ).pack(pady=10)

        # Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ['rank', 'bib', 'name', 'category', 'sex', 'total']
        if self.race.config.num_runs >= 1:
            columns.append('run1')
        if self.race.config.num_runs >= 2:
            columns.append('run2')
        if self.race.config.num_runs >= 3:
            columns.append('run3')

        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)

        # En-têtes des colonnes
        headings = {
            'rank': 'Rang',
            'bib': 'Bib',
            'name': 'Nom',
            'category': 'Cat.',
            'sex': 'Sexe',
            'total': 'Total',
            'run1': 'Run 1',
            'run2': 'Run 2',
            'run3': 'Run 3'
        }

        for col in columns:
            tree.heading(col, text=headings.get(col, col))

        tree.pack(fill=tk.BOTH, expand=True)

        # Préparer les données et calculer les largeurs
        all_values = []
        col_widths = {col: len(headings.get(col, col)) for col in columns}

        for result in results:
            athlete = next(a for a in self.race.athletes if a.bib == result['bib'])
            values = [
                str(result['rank']) if result['rank'] else '',
                str(result['bib']),
                f"{athlete.first_name} {athlete.last_name}",
                result['category'],
                result['sex'],
                result['total_display']
            ]
            if self.race.config.num_runs >= 1:
                values.append(result.get('run1', ''))
            if self.race.config.num_runs >= 2:
                values.append(result.get('run2', ''))
            if self.race.config.num_runs >= 3:
                values.append(result.get('run3', ''))

            all_values.append(values)

            # Mettre à jour les largeurs maximales
            for i, col in enumerate(columns):
                col_widths[col] = max(col_widths[col], len(str(values[i])))

        # Appliquer les largeurs (environ 8 pixels par caractère + marge)
        for col in columns:
            width = col_widths[col] * 9 + 20
            tree.column(col, width=width, minwidth=50)

        # Insérer les données
        for values in all_values:
            tree.insert('', tk.END, values=values)
    
    def _export_podiums(self):
        """Exporte les podiums vers Excel"""
        filepath = filedialog.asksaveasfilename(
            title="Exporter les podiums",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            calculator = ResultsCalculator(self.race)
            calculator.export_podiums_to_excel(filepath)
            messagebox.showinfo("Succès", f"Podiums exportés!\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export:\n{e}")
    
    def _show_about(self):
        """Affiche la boîte À propos"""
        messagebox.showinfo(
            "À propos",
            "Ski Timing Manager v1.0\n\n"
            "Application de chronométrage pour courses de ski alpin\n"
            "Support: 1-3 runs avec validation croisée CSV\n\n"
            "© 2025"
        )
