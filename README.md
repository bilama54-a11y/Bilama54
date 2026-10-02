# Bilama54
Parieur sportif

## MatchLab — mini-application de prédiction football

Application web en français, adaptée au mobile, construite à partir des captures fournies. **L’outil est exploratoire, ne place aucun pari et ne garantit ni score ni gain.** Il n’est pas connecté à un flux FotMob ou à un bookmaker en direct.

### Fonctionnalités

- Comparaison Arsenal–Leeds préremplie avec les statistiques des trois captures FotMob.
- Import de 1 à 6 captures PNG/JPG/WEBP/BMP, avec reconnaissance OCR locale et validation des chiffres avant application.
- Lecture des colonnes gauche/droite, des décimales françaises et des libellés de statistiques.
- Refus d’interpréter un coupon de pari comme des statistiques de match.
- Saisie manuelle, choix des xG totaux ou moyens et du nombre de matchs de chaque équipe.
- Recalcul automatique des probabilités 1/N/2, doubles chances, totaux de buts, BTTS et scores possibles.
- Matrice des scores et distribution des buts par équipe.
- Comparateur de cotes et calcul du seuil d’équilibre. Le coupon NVSL de la capture est disponible comme exemple, **sans probabilité ni résultat inventé**.
- Historique local des analyses complètes, export et réimport JSON.
- Hypothèses du modèle modifiables et documentées dans « Méthode & réglages ».
- Manifest d’application installable et cache hors connexion en version de production.

### Démarrer

Node.js 20.19+ recommandé (testé avec Node.js 22).

```bash
npm ci
npm run dev
```

L’application écoute sur `0.0.0.0:5173`. Les hôtes de prévisualisation sont acceptés. Tout le code navigateur utilise des URL relatives : aucun appel à un backend sur localhost.

### Version de production

```bash
npm run build
npm run preview
```

Le dossier `dist/` contient un site statique, déployable sur un hébergement HTTPS. Il n’est pas versionné. La prévisualisation de production utilise le port 4173 par défaut ; `npm run preview -- --port 5173` permet de conserver le même port que le développement.

### Utiliser ses propres captures

1. Cliquer sur **Importer des captures** et choisir les images de comparaison FotMob.
2. Vérifier les noms et les chiffres reconnus. Une reconnaissance OCR n’est pas une certification de la donnée.
3. Appliquer les valeurs. Si une donnée essentielle manque, le calcul reste en pause.
4. Renseigner le nombre réel de matchs utilisés et vérifier l’unité des xG.
5. Comparer les scénarios ; ajouter une cote seulement si elle a été vérifiée chez le bookmaker.

Par défaut, l’import remplace les statistiques de l’analyse. L’option « Compléter les données actuelles » ne doit être utilisée que pour les mêmes équipes, la même saison et la même période. Les chiffres non reconnus ne sont pas inventés.

**Précaution sur l’exemple fourni :** les captures n’indiquent pas le nombre de matchs de saison. L’exemple utilise **5 matchs par équipe comme hypothèse explicitement signalée**, pas comme une donnée confirmée. Les cinq derniers résultats et les 13 confrontations historiques ne permettent pas de déduire ce nombre.

### Méthode de calcul

Pour chaque équipe :

1. Conversion des xG totaux en xG par match (ou conservation des moyennes si ce mode est sélectionné).
2. Mélange de l’attaque observée : 70 % xG créés / 30 % buts marqués, et de la défense : 70 % xG concédés / 30 % buts encaissés.
3. Lissage vers une référence générique de 1,35 but avec 4 matchs fictifs. Cette référence est une **hypothèse**, pas une moyenne mesurée de Premier League 2026/2027.
4. Moyenne géométrique entre attaque et défense adverse. Par défaut, bonus domicile +12 % et réduction extérieure −6 %, désactivés sur terrain neutre.
5. Deux distributions de Poisson indépendantes et addition des probabilités des cases pour chaque marché. Les intensités sont bornées à 0,02–8 buts pour la stabilité numérique ; la troncature est large et normalisée.

La possession, la forme, les tirs et les confrontations restent du contexte : ils ne sont pas ajoutés arbitrairement aux xG. Le modèle n’intègre pas les compositions, blessures, météo, force des adversaires ou un historique calibré de domicile/extérieur. **Les tests valident la cohérence logicielle et mathématique, pas une performance prédictive.**

La cote neutre vaut `1 / probabilité`. La cote proposée exige un taux de réussite de `1 / cote`. L’espérance théorique vaut `probabilité × cote − 1`. Une espérance positive selon un modèle non calibré ne prouve pas la rentabilité. Les probabilités combinées sont désactivées si des estimations manquent ou si plusieurs sélections concernent le même match.

### Données et confidentialité

- Les images sont traitées sur l’appareil ; aucune image n’est envoyée à un service OCR distant.
- Tesseract, son moteur WASM et le modèle français sont servis localement par l’application.
- `npm ci` prépare les fichiers OCR dans `public/ocr/` à partir des dépendances npm. Les fichiers générés et les poids ne sont pas conservés dans Git.
- Les images importées ne sont pas stockées dans l’historique. Seuls les chiffres, les paramètres et les analyses sont conservés dans le navigateur.
- Les analyses complètes sont sauvegardées automatiquement ; la dernière analyse valide est conservée pendant une saisie temporairement incomplète.
- Aucun compte, aucune clé API, aucun identifiant de bookmaker, aucun tracking.
- La PWA met l’interface en cache en production. Une première lecture OCR en ligne reste nécessaire avant d’utiliser l’OCR hors connexion.
- Les repères AR/LU sont des monogrammes locaux, pas des écussons officiels. Les fontes Manrope et DM Sans sont accompagnées de leurs licences dans `public/fonts/`.

### Tests

```bash
npm test
npm run build
```

24 tests unitaires couvrent les distributions, les partitions à 100 %, la conversion des unités, les données invalides, les cotes, les coupons, la sécurité de l’import JSON et le parseur OCR.

Tests navigateur (nécessitent un serveur lancé et Chromium) :

```bash
npx playwright install chromium
npm run test:ui
```

Le script couvre le recalcul, la validation, l’historique, l’export/réimport JSON, le coupon NVSL, les paramètres, **une lecture OCR réelle sur une capture synthétique**, la navigation mobile et les erreurs JavaScript. Les captures originales ont été retranscrites dans l’exemple ; la qualité de reconnaissance d’une autre image doit toujours être contrôlée par l’utilisateur.

En CI, `CHROME_PATH` permet de fournir un binaire existant et `TEST_BASE_URL` un autre serveur de test. Les artefacts de test restent dans `.cache/`, hors Git.

### Ouvrir l’application sans panneau d’aperçu

Le fichier **`MatchLab.html`** est une distribution autonome de l’application (environ 6,6 Mo). Téléchargez-le puis ouvrez-le avec un navigateur moderne, par exemple Chrome ou Firefox. Il embarque l’interface, les fontes, les repères d’équipe, le moteur OCR et le modèle français. Aucun serveur, clé API, jeton d’accès ou téléchargement complémentaire n’est nécessaire.

Si un lecteur de fichiers affiche seulement le code ou une page inerte, choisissez « Ouvrir avec » votre navigateur : certains aperçus de fichiers ne permettent pas l’exécution de JavaScript.

Pour reconstruire ou tester cette distribution :

```bash
npm run build:portable
npm run test:portable
```

Le test ouvre réellement le fichier en `file://`, coupe le réseau, vérifie les calculs et effectue une lecture OCR sur une capture synthétique. Cette distribution est conservée car elle constitue un livrable directement ouvrable, indépendant de la disponibilité du serveur de prévisualisation.
