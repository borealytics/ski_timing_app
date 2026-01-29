# Ski Timing Manager

Application de chronométrage pour courses de ski alpin avec support de 1-3 runs et validation croisée avec National/FIS Software.

## 🎯 Fonctionnalités

- ✅ Import des coureurs depuis CSV National/FIS Software
- ✅ Configuration flexible (1-3 runs, différentes méthodes de calcul)
- ✅ Interface de chronométrage intuitive (format m:ss.cc)
- ✅ Support DNS, DNF, DSQ
- ✅ Validation croisée avec résultats CSV National/FIS
- ✅ Calcul automatique des résultats finaux
- ✅ Export des podiums par catégorie-sexe vers Excel
- ✅ Sauvegarde automatique (format JSON)
- ✅ 100% offline, aucune connexion Internet requise

## 📦 Installation

### Option 1: Exécutable (Recommandé)

Aucune installation Python requise! Téléchargez simplement l'exécutable pour votre plateforme:

**macOS:**
1. Téléchargez `SkiTimingManager.app`
2. Copiez dans `/Applications` ou n'importe où
3. Double-cliquez pour lancer

**Windows:**
1. Téléchargez `SkiTimingManager.exe`
2. Copiez n'importe où
3. Double-cliquez pour lancer

### Option 2: Depuis le code source

Requis: Python 3.8+

```bash
# Cloner ou télécharger le projet
cd ski_timing_app

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

## 🔨 Compilation des exécutables

Si vous voulez compiler vous-même les exécutables:

**macOS/Linux:**
```bash
chmod +x build.sh
./build.sh
```

**Windows:**
```
build.bat
```

L'exécutable sera dans le dossier `dist/`

## 📖 Guide d'utilisation

### 1. Préparation

1. Dans **National/FIS Software**, exportez votre liste de coureurs en CSV
2. Lancez **Ski Timing Manager**
3. Cliquez sur "Nouvelle Course"

### 2. Import des coureurs

1. Cliquez sur "Parcourir..." pour sélectionner votre fichier CSV
2. L'application importe automatiquement:
   - Bib (dossard)
   - Start Number
   - Nom, Prénom
   - Catégorie (U6, U8, U10, etc.)
   - Sexe
   - Club/Équipe
   - Année de naissance

### 3. Configuration de la course

Configurez selon vos besoins:

**Type de course:**
- 1 run
- 2 runs  
- 3 runs

**Méthode de calcul:**
- Meilleur temps (1 run)
- 2 meilleurs temps (pour courses à 3 runs)
- Somme des 3 temps

L'application génère automatiquement l'ordre de départ pour chaque run selon les conventions:
- Run 1: Catégorie → Sexe → Bib (ascendant)
- Run 2: Catégorie → Sexe → Start# (descendant)
- Run 3: Catégorie → Sexe → Bib (ascendant)

### 4. Chronométrage manuel

Pour chaque run:

1. Cliquez sur "Chronométrer" pour le run voulu
2. L'interface affiche le prochain coureur avec ses infos
3. **Entrer le temps:**
   - Minutes: 1 caractère (0-9)
   - Secondes: 2 caractères (00-59)
   - Centièmes: 2 caractères (00-99)
   - Appuyez Enter pour passer au champ suivant
   - Cliquez "Enregistrer" ou Enter sur le dernier champ

4. **Ou cliquez sur un statut:**
   - DNS (Did Not Start)
   - DNF (Did Not Finish)
   - DSQ (Disqualified)

5. Le temps est converti automatiquement:
   - Format affiché: `1:15.34`
   - Décimal calculé: `75.34` secondes

6. Navigation:
   - "< Précédent" pour corriger le coureur précédent
   - "Liste Complète" pour voir tous les coureurs et leur statut
   - "Terminer" quand c'est fini

**Progression:** Le compteur `[12/45]` montre combien de coureurs ont un temps enregistré.

### 5. Validation croisée avec National/FIS

Après avoir chronométré manuellement:

1. Exportez les résultats depuis **National/FIS Software** (CSV)
2. Dans l'application, cliquez "Importer résultats CSV" pour le run
3. L'application compare automatiquement:
   - Temps manuel vs CSV
   - Statuts (DNS/DNF/DSQ)
   - Détecte les écarts de temps (tolérance 0.01s)

4. Si des différences sont trouvées:
   - L'application les affiche dans un tableau
   - Vous pouvez choisir:
     - Utiliser les valeurs importées (remplace le manuel)
     - Garder les valeurs manuelles
     - Corriger manuellement

### 6. Résultats finaux

Une fois tous les runs validés:

1. Cliquez "Calculer résultats finaux"
2. L'application:
   - Applique la méthode de calcul configurée
   - Trie par Catégorie → Sexe → Temps
   - Attribue les rangs par catégorie-sexe
   - Affiche le classement complet

### 7. Export des podiums

1. Cliquez "Exporter podiums (Excel)"
2. Choisissez un nom de fichier de base (ex: `podiums_course1`)
3. L'application génère automatiquement:
   - `podiums_course1_U6_M.xlsx` (Top 5 U6 Masculins)
   - `podiums_course1_U6_F.xlsx` (Top 5 U6 Féminins)
   - `podiums_course1_U8_M.xlsx`
   - etc.

Chaque fichier Excel contient:
- Rang
- Bib
- Nom
- Prénom
- Club
- Temps Total

## 📁 Structure des fichiers

```
ski_timing_app/
├── main.py                 # Point d'entrée
├── main_window.py          # Interface principale
├── timing_interface.py     # Interface de chronométrage
├── models.py               # Structures de données
├── utils.py                # Fonctions utilitaires
├── csv_importer.py         # Import/Export CSV
├── results.py              # Calcul des résultats
├── requirements.txt        # Dépendances Python
├── build.sh               # Script de build macOS/Linux
└── build.bat              # Script de build Windows
```

## 🔄 Format de sauvegarde

Les courses sont sauvegardées en JSON:

```json
{
  "config": {
    "race_name": "Slalom 2025",
    "num_runs": 3,
    "calculation_method": "BEST_2"
  },
  "athletes": [...],
  "runs": [
    {
      "number": 1,
      "results": {
        "8": {
          "time_seconds": 75.34,
          "time_display": "1:15.34",
          "status": "FINISHED"
        }
      }
    }
  ]
}
```

Vous pouvez rouvrir une course sauvegardée à tout moment avec "Fichier → Ouvrir Course".

## 🐛 Dépannage

### L'application ne démarre pas (macOS)

Si vous voyez "L'app ne peut pas être ouverte car elle provient d'un développeur non identifié":

1. Allez dans Préférences Système → Sécurité et confidentialité
2. Cliquez "Ouvrir quand même"

OU en ligne de commande:
```bash
xattr -cr /path/to/SkiTimingManager.app
```

### L'application ne démarre pas (Windows)

Si Windows Defender bloque l'application:
1. Cliquez "Plus d'infos"
2. Cliquez "Exécuter quand même"

### Erreur d'import CSV

Vérifiez que:
- Le fichier est bien exporté depuis National/FIS Software
- Les colonnes importantes sont présentes: Bib, Start Number, Class, First, Last, Sex (Masters or XC)
- Le fichier n'est pas corrompu (ouvrez-le dans un éditeur de texte)

### Problème de conversion temps

Le format attendu est `m:ss.cc`:
- ✅ `1:15.34` → 75.34 secondes
- ✅ `0:45.67` → 45.67 secondes  
- ❌ `75.34` → invalide (doit avoir les `:`)
- ❌ `1:15:34` → invalide (trop de `:`)

## 📝 Notes importantes

- **Backup:** Les courses sont sauvegardées automatiquement en JSON. Faites des copies de ces fichiers!
- **Offline:** L'application fonctionne 100% offline, parfait pour le terrain
- **Validation:** Validez toujours avec National/FIS Software pour les résultats officiels
- **Corrections:** Vous pouvez revenir en arrière dans le chronométrage avec "< Précédent"
- **Export:** Les podiums Excel sont prêts pour impression ou partage

## 🤝 Support

Pour des questions ou problèmes:
1. Vérifiez ce README
2. Vérifiez le format de vos fichiers CSV
3. Testez avec les données d'exemple fournies

## 📄 Licence

Utilisation libre pour chronométrage de courses de ski.

## 🎿 Bon chronométrage!
