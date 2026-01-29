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

    def __init__(self, parent, run: Run, on_complete: Optional[Callable] = None):
        super().__init__(parent)

        self.run = run
        self.on_complete = on_complete
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
        self.athlete_tree.column('name', width=100)
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

        # Zone d'information coureur
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

        ttk.Button(
            button_frame,
            text="DNS",
            command=lambda: self._save_status('DNS'),
            width=8
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            button_frame,
            text="DNF",
            command=lambda: self._save_status('DNF'),
            width=8
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            button_frame,
            text="DSQ",
            command=lambda: self._save_status('DSQ'),
            width=8
        ).pack(side=tk.LEFT, padx=3)

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

            # Temps ou status à afficher
            time_display = result.time_display if result.time_display else '-'

            # Indicateur de statut
            status_icon = ''
            if result.status == 'FINISHED':
                status_icon = ''
            elif result.status in ['DNS', 'DNF', 'DSQ']:
                status_icon = result.status

            item_id = self.athlete_tree.insert('', tk.END, values=(
                i + 1,
                athlete.bib,
                athlete.last_name,
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

        # Progression
        completed, total = self.run.get_completion_rate()
        self.progress_label.config(text=f"[{completed}/{total}]")

        # Pré-remplir si déjà saisi (désactiver auto-avancement)
        self._updating_fields = True
        self._sec_invalid = False
        self.sec_entry.configure(style='TEntry')
        if result and result.status != 'PENDING':
            if result.status == 'FINISHED':
                # Parser le temps pour pré-remplir
                time_str = result.time_display
                if ':' in time_str:
                    parts = time_str.split(':')
                    self.min_var.set(parts[0])
                    sec_parts = parts[1].split('.')
                    self.sec_var.set(sec_parts[0])
                    self.cent_var.set(sec_parts[1])
            else:
                self.min_var.set('')
                self.sec_var.set('')
                self.cent_var.set('')
        else:
            # Vider les champs
            self.min_var.set('')
            self.sec_var.set('')
            self.cent_var.set('')
        self._updating_fields = False

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

        result = RunResult(bib=athlete.bib)
        result.set_time(total_seconds, time_display)
        self.run.set_result(athlete.bib, result)

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

        # Enregistrer
        result = RunResult(bib=athlete.bib)
        result.set_time(total_seconds, time_display)
        self.run.set_result(athlete.bib, result)

        # Passer au suivant
        self.current_index += 1
        self._update_display()

    def _save_status(self, status: str):
        """Enregistre un statut spécial (DNS, DNF, DSQ)"""
        athlete = self.run.athletes[self.current_index]

        result = RunResult(bib=athlete.bib)
        result.set_status(status)
        self.run.set_result(athlete.bib, result)

        # Passer au suivant
        self.current_index += 1
        self._update_display()

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
