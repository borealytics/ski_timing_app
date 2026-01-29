# Guide de Démarrage Rapide - Ski Timing Manager

## 🚀 Test rapide avec les données d'exemple

Voici comment tester l'application en 5 minutes avec les données fournies:

### 1. Lancer l'application

**Depuis le code source:**
```bash
python main.py
```

**Ou double-cliquez sur l'exécutable** (si vous l'avez compilé)

### 2. Créer une nouvelle course

1. Cliquez sur **"Nouvelle Course"**
2. Cliquez sur **"Parcourir..."**
3. Sélectionnez le fichier `example_athletes.csv`
4. → **65 coureurs importés!** ✓

### 3. Configuration

1. Nom: "Course Test 2025"
2. Type: **2 runs** (par défaut)
3. Calcul: **2 meilleurs temps** (par défaut)
4. Cliquez **"Générer les runs"**

### 4. Chronométrer le Run 1

1. Dans l'écran principal, cliquez **"Chronométrer"** pour Run 1
2. Le premier coureur s'affiche (Bib #1)
3. Essayez d'entrer un temps:
   - Minutes: `1`
   - Secondes: `15`
   - Centièmes: `34`
   - Cliquez **"Enregistrer"**
   
4. Le coureur suivant s'affiche automatiquement!

**Ou cliquez DNS/DNF/DSQ** pour ces statuts spéciaux.

### 5. Navigation rapide

- **"< Précédent"**: Revenir au coureur précédent
- **"Liste Complète"**: Voir tous les coureurs et leur progression
- **"Terminer"**: Quitter le chronométrage

### 6. Voir les résultats

1. Retour à l'écran principal
2. Cliquez **"Calculer résultats finaux"**
3. → Tableau avec rangs par catégorie-sexe

### 7. Exporter

1. Cliquez **"Exporter podiums (Excel)"**
2. Choisissez un nom: `test_podiums`
3. → Fichiers générés:
   - `test_podiums_U6_M.xlsx`
   - `test_podiums_U8_M.xlsx`
   - etc.

## 💡 Raccourcis clavier dans le chronométrage

- **Enter** sur chaque champ → Passe au suivant
- **Enter** sur le dernier champ → Enregistre automatiquement
- **Tab** → Navigation entre champs

## 🎯 Workflow réel de production

```
1. National/FIS Software
   ↓ Export CSV (liste des coureurs)
   
2. Ski Timing Manager
   ↓ Import CSV
   ↓ Configuration (type course, méthode)
   ↓ Chronométrage manuel Run 1
   
3. National/FIS Software (chronométrage officiel)
   ↓ Export CSV Run 1
   
4. Ski Timing Manager
   ↓ Import CSV Run 1 → Validation croisée
   ↓ Chronométrage manuel Run 2
   
5. National/FIS Software
   ↓ Export CSV Run 2
   
6. Ski Timing Manager
   ↓ Import CSV Run 2 → Validation croisée
   ↓ Calcul résultats finaux
   ↓ Export podiums Excel
```

## 📊 Données d'exemple fournies

Le fichier `example_athletes.csv` contient:
- 65 coureurs
- Catégories: U6, U8, U10, U12, U14, U16, U18
- Tous masculins (M)
- 4 clubs: ADSTO, MORI, MASUD, SKIB

## ⚡ Compilation des exécutables

### macOS
```bash
chmod +x build.sh
./build.sh
```
→ Crée `dist/SkiTimingManager.app`

### Windows
```
build.bat
```
→ Crée `dist\SkiTimingManager.exe`

## 🆘 Problème?

1. **L'application ne démarre pas**
   - Vérifiez que Python 3.8+ est installé
   - Installez les dépendances: `pip install -r requirements.txt`

2. **Erreur d'import CSV**
   - Vérifiez le format du fichier (doit venir de National/FIS Software)
   - Testez avec `example_athletes.csv` pour vérifier que l'app fonctionne

3. **Interface ne s'affiche pas**
   - Sur macOS: `xattr -cr SkiTimingManager.app`
   - Sur Windows: Clic droit → "Exécuter en tant qu'administrateur"

## 📚 Documentation complète

Voir `README.md` pour la documentation détaillée.

## 🎿 Prêt à chronométrer!

Vous avez maintenant tout ce qu'il faut pour gérer vos courses de ski alpin efficacement!

**Bons chronos! ⛷️**
