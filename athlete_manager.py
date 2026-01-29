"""
Interface de gestion des coureurs (fichier maître)
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional
from models import Race, Athlete


class AthleteManagerWindow(tk.Toplevel):
    """Fenêtre de gestion des coureurs"""

    def __init__(self, parent, race: Race, on_update: Optional[Callable] = None):
        super().__init__(parent)

        self.race = race
        self.on_update = on_update

        self.title("Gestion des coureurs")
        self.geometry("900x600")

        self._create_widgets()
        self._populate_list()

    def _create_widgets(self):
        """Crée les widgets de l'interface"""

        # Frame principale
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # En-tête
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Gestion des coureurs",
            font=('Arial', 16, 'bold')
        ).pack(side=tk.LEFT)

        self.count_label = ttk.Label(
            header_frame,
            text="",
            font=('Arial', 11)
        )
        self.count_label.pack(side=tk.RIGHT)

        # Frame pour la liste avec scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self.tree = ttk.Treeview(
            list_frame,
            columns=('bib', 'name', 'firstname', 'category', 'sex', 'team', 'year', 'status'),
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)

        # Configuration des colonnes
        self.tree.heading('bib', text='Dossard')
        self.tree.heading('name', text='Nom')
        self.tree.heading('firstname', text='Prénom')
        self.tree.heading('category', text='Cat.')
        self.tree.heading('sex', text='Sexe')
        self.tree.heading('team', text='Club')
        self.tree.heading('year', text='Année')
        self.tree.heading('status', text='Statut')

        self.tree.column('bib', width=70, anchor='center')
        self.tree.column('name', width=150)
        self.tree.column('firstname', width=120)
        self.tree.column('category', width=60, anchor='center')
        self.tree.column('sex', width=50, anchor='center')
        self.tree.column('team', width=150)
        self.tree.column('year', width=60, anchor='center')
        self.tree.column('status', width=80, anchor='center')

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Tags pour les couleurs
        self.tree.tag_configure('absent', foreground='gray', background='#ffeeee')
        self.tree.tag_configure('active', foreground='black')

        # Double-clic pour éditer
        self.tree.bind('<Double-1>', self._on_double_click)

        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Marquer absent",
            command=self._toggle_absent,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Modifier dossard",
            command=self._change_bib,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Ajouter coureur",
            command=self._add_athlete,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Supprimer",
            command=self._delete_athlete,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Fermer",
            command=self._close,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

    def _populate_list(self):
        """Remplit la liste avec les coureurs"""
        # Vider la liste
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Remplir avec les athlètes
        for athlete in self.race.athletes:
            tag = 'absent' if athlete.status == 'ABSENT' else 'active'
            status_text = 'ABSENT' if athlete.status == 'ABSENT' else 'Actif'

            self.tree.insert('', tk.END, iid=str(athlete.bib), values=(
                athlete.bib,
                athlete.last_name,
                athlete.first_name,
                athlete.category,
                athlete.sex,
                athlete.team,
                athlete.year_of_birth,
                status_text
            ), tags=(tag,))

        # Mettre à jour le compteur
        total = len(self.race.athletes)
        absents = sum(1 for a in self.race.athletes if a.status == 'ABSENT')
        self.count_label.config(text=f"{total} coureurs ({absents} absents)")

    def _get_selected_athlete(self) -> Optional[Athlete]:
        """Retourne l'athlète sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un coureur")
            return None

        bib = int(selection[0])
        for athlete in self.race.athletes:
            if athlete.bib == bib:
                return athlete
        return None

    def _toggle_absent(self):
        """Bascule le statut absent/actif"""
        athlete = self._get_selected_athlete()
        if not athlete:
            return

        if athlete.status == 'ABSENT':
            athlete.status = 'ACTIVE'
            messagebox.showinfo("Succès", f"#{athlete.bib} {athlete.last_name} est maintenant ACTIF")
        else:
            athlete.status = 'ABSENT'
            messagebox.showinfo("Succès", f"#{athlete.bib} {athlete.last_name} est maintenant ABSENT")

        self._populate_list()
        self._notify_update()

    def _change_bib(self):
        """Change le numéro de dossard d'un coureur"""
        athlete = self._get_selected_athlete()
        if not athlete:
            return

        new_bib = simpledialog.askinteger(
            "Modifier dossard",
            f"Nouveau numéro de dossard pour {athlete.last_name} {athlete.first_name}:\n"
            f"(Actuel: #{athlete.bib})",
            parent=self,
            minvalue=1
        )

        if new_bib is None:
            return

        # Vérifier que le nouveau numéro n'existe pas déjà
        if new_bib != athlete.bib:
            for a in self.race.athletes:
                if a.bib == new_bib:
                    messagebox.showerror("Erreur", f"Le dossard #{new_bib} est déjà attribué à {a.last_name} {a.first_name}")
                    return

        old_bib = athlete.bib
        athlete.bib = new_bib

        # Mettre à jour dans les runs
        for run in self.race.runs:
            # Mettre à jour l'athlète dans la liste du run
            for i, a in enumerate(run.athletes):
                if a.bib == old_bib:
                    run.athletes[i].bib = new_bib

            # Mettre à jour les résultats
            if old_bib in run.results:
                result = run.results.pop(old_bib)
                result.bib = new_bib
                run.results[new_bib] = result

        messagebox.showinfo("Succès", f"Dossard modifié: #{old_bib} -> #{new_bib}")
        self._populate_list()
        self._notify_update()

    def _add_athlete(self):
        """Ajoute un nouveau coureur"""
        dialog = AddAthleteDialog(self, self.race)
        self.wait_window(dialog)

        if dialog.result:
            self.race.athletes.append(dialog.result)

            # Ajouter aux runs existants
            for run in self.race.runs:
                run.add_athlete(dialog.result)

            messagebox.showinfo("Succès", f"Coureur #{dialog.result.bib} ajouté")
            self._populate_list()
            self._notify_update()

    def _delete_athlete(self):
        """Supprime un coureur"""
        athlete = self._get_selected_athlete()
        if not athlete:
            return

        response = messagebox.askyesno(
            "Confirmer suppression",
            f"Voulez-vous vraiment supprimer #{athlete.bib} {athlete.last_name} {athlete.first_name}?\n\n"
            "Cette action est irréversible."
        )

        if not response:
            return

        # Supprimer de la liste principale
        self.race.athletes = [a for a in self.race.athletes if a.bib != athlete.bib]

        # Supprimer des runs
        for run in self.race.runs:
            run.athletes = [a for a in run.athletes if a.bib != athlete.bib]
            if athlete.bib in run.results:
                del run.results[athlete.bib]

        messagebox.showinfo("Succès", f"Coureur #{athlete.bib} supprimé")
        self._populate_list()
        self._notify_update()

    def _on_double_click(self, event):
        """Gère le double-clic pour éditer"""
        self._change_bib()

    def _notify_update(self):
        """Notifie les changements"""
        if self.on_update:
            self.on_update()

    def _close(self):
        """Ferme la fenêtre"""
        self.destroy()


class AddAthleteDialog(tk.Toplevel):
    """Dialog pour ajouter un nouveau coureur"""

    def __init__(self, parent, race: Race):
        super().__init__(parent)

        self.race = race
        self.result = None

        self.title("Ajouter un coureur")
        self.geometry("400x350")
        self.resizable(False, False)

        # Modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Crée les widgets du formulaire"""

        frame = ttk.Frame(self, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Dossard
        ttk.Label(frame, text="Dossard *:").grid(row=0, column=0, sticky='w', pady=5)
        self.bib_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.bib_var, width=10).grid(row=0, column=1, sticky='w', pady=5)

        # Nom
        ttk.Label(frame, text="Nom *:").grid(row=1, column=0, sticky='w', pady=5)
        self.lastname_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.lastname_var, width=25).grid(row=1, column=1, sticky='w', pady=5)

        # Prénom
        ttk.Label(frame, text="Prénom *:").grid(row=2, column=0, sticky='w', pady=5)
        self.firstname_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.firstname_var, width=25).grid(row=2, column=1, sticky='w', pady=5)

        # Catégorie
        ttk.Label(frame, text="Catégorie *:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        categories = ['U6', 'U8', 'U10', 'U12', 'U14', 'U16', 'U18', 'U21', 'Senior']
        ttk.Combobox(frame, textvariable=self.category_var, values=categories, width=10).grid(row=3, column=1, sticky='w', pady=5)

        # Sexe
        ttk.Label(frame, text="Sexe *:").grid(row=4, column=0, sticky='w', pady=5)
        self.sex_var = tk.StringVar(value='M')
        sex_frame = ttk.Frame(frame)
        sex_frame.grid(row=4, column=1, sticky='w', pady=5)
        ttk.Radiobutton(sex_frame, text="M", variable=self.sex_var, value='M').pack(side=tk.LEFT)
        ttk.Radiobutton(sex_frame, text="F", variable=self.sex_var, value='F').pack(side=tk.LEFT)

        # Club
        ttk.Label(frame, text="Club:").grid(row=5, column=0, sticky='w', pady=5)
        self.team_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.team_var, width=25).grid(row=5, column=1, sticky='w', pady=5)

        # Année de naissance
        ttk.Label(frame, text="Année naissance:").grid(row=6, column=0, sticky='w', pady=5)
        self.year_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.year_var, width=10).grid(row=6, column=1, sticky='w', pady=5)

        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Ajouter", command=self._validate).pack(side=tk.LEFT, padx=10)

    def _validate(self):
        """Valide et crée l'athlète"""

        # Validation
        try:
            bib = int(self.bib_var.get())
            if bib <= 0:
                raise ValueError("Le dossard doit être positif")
        except ValueError:
            messagebox.showerror("Erreur", "Le dossard doit être un nombre positif")
            return

        # Vérifier que le dossard n'existe pas
        for a in self.race.athletes:
            if a.bib == bib:
                messagebox.showerror("Erreur", f"Le dossard #{bib} existe déjà")
                return

        lastname = self.lastname_var.get().strip()
        firstname = self.firstname_var.get().strip()
        category = self.category_var.get().strip()

        if not lastname or not firstname or not category:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs obligatoires (*)")
            return

        year = 0
        if self.year_var.get().strip():
            try:
                year = int(self.year_var.get())
            except ValueError:
                messagebox.showerror("Erreur", "L'année de naissance doit être un nombre")
                return

        # Créer l'athlète
        self.result = Athlete(
            bib=bib,
            start_number=bib,  # Par défaut, même que le dossard
            first_name=firstname,
            last_name=lastname,
            category=category,
            sex=self.sex_var.get(),
            team=self.team_var.get().strip(),
            year_of_birth=year,
            nat_number="",
            status="ACTIVE"
        )

        self.destroy()
