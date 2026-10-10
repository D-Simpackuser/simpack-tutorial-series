# Tutoriels de dynamique ferroviaire avec Simpack

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Español](README.es.md) · [한국어](README.ko.md)

> Dépôt actuellement privé : un compte GitHub disposant des droits d’accès est nécessaire pour télécharger les vidéos et les sous-titres.

**Interaction véhicule–voie–pont · Corps flexibles · Restitution des contraintes et fatigue**

Ce dépôt réunit sept séries de tutoriels consacrées aux chaînes de calcul en dynamique ferroviaire avec Simpack, Abaqus, Ansys et fe-safe. Le classement couvre la modélisation des véhicules, les rails et fondations de voie flexibles, le couplage véhicule–voie–pont, ainsi que la restitution des contraintes et déformations et l’analyse de fatigue.

194 vidéos · 772 fichiers de sous-titres · 193 vidéos avec les quatre fichiers. Cours sans fichiers de sous-titres : `s05-e001` — 0-课程效果.

## Catalogue des séries

| Série | Sujet | Vidéos | Fichiers |
|---|---|---:|---|
| 1 | [Dynamique couplée véhicule ferroviaire–rail flexible–dalle flottante avec Abaqus et Simpack](series/1/README.fr.md) | 18 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-1-v1) |
| 2 | [Analyse des contraintes et déformations dynamiques et de la fatigue des corps flexibles avec Ansys/Abaqus, Simpack et fe-safe](series/2/README.fr.md) | 13 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-2-v1) |
| 3 | [Dynamique véhicule ferroviaire–voie flexible avec Ansys Workbench Mechanical, APDL et Simpack](series/3/README.fr.md) | 16 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-3-v1) |
| 5 | [Dynamique couplée véhicule–voie–pont avec Abaqus et Simpack](series/5/README.fr.md) | 42 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-5-v1) |
| 6 | [Prise en main de la dynamique des véhicules ferroviaires avec Simpack](series/6/README.fr.md) | 8 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-6-v1) |
| 7 | [Dynamique véhicule–voie–pont avec Ansys et Simpack : modélisation Beam–Solid](series/7/README.fr.md) | 46 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-7-v1) |
| 8 | [Dynamique véhicule–voie–pont avec Ansys et Simpack : modélisation Beam–Beam](series/8/README.fr.md) | 51 | [Release](https://github.com/D-Simpackuser/simpack-tutorial-series/releases/tag/series-8-v1) |

Le titre de chaque série ouvre son index existant, vidéo par vidéo. Les pages de release regroupent les fichiers à télécharger. Les numéros d’origine sont conservés ; il n’existe pas de série 4.

## Par où commencer

Pour construire un premier véhicule, commencez par la **série 6**. Pour la voie flexible, choisissez la **série 1** avec Abaqus ou la **série 3** avec Ansys, puis les **séries 5, 7 ou 8** pour les modèles véhicule–voie–pont. La **série 2** vise la restitution des contraintes et déformations et la fatigue. Il s’agit d’une proposition de parcours, et non d’un enchaînement de prérequis vérifié.

## Repères thématiques

Les groupes suivants sont établis à partir des titres fournis. Ils ne prouvent pas la validation indépendante d’un modèle, d’un résultat numérique ou d’une combinaison de versions logicielles.

### Série 1 — Dynamique couplée véhicule ferroviaire–rail flexible–dalle flottante avec Abaqus et Simpack

- Modélisation du rail flexible et de la dalle flottante sur ressorts dans Abaqus ; génération FBI
- Rédaction des fichiers FTR et configuration de la voie flexible dans Simpack
- Modèles d’essieu monté, de châssis de bogie et de véhicule complet ; couplage avec la dalle flottante
- Excitations TRE / PSD, animation des corps flexibles et post-traitement des réponses

### Série 2 — Analyse des contraintes et déformations dynamiques et de la fatigue des corps flexibles avec Ansys/Abaqus, Simpack et fe-safe

- Préparation des interfaces Abaqus / Ansys et génération des corps flexibles FBI
- Configuration des corps flexibles et restitution des contraintes et déformations dans Simpack
- Visualisation des déformées, contraintes et déformations dans Simpack Post
- Export vers fe-safe, analyse de fatigue et exemple de chaîne de calcul intégrée

### Série 3 — Dynamique véhicule ferroviaire–voie flexible avec Ansys Workbench Mechanical, APDL et Simpack

- Modèle de rail en poutres dans SpaceClaim ; sous-structuration dans Workbench Mechanical
- Procédures APDL par interface graphique et commandes ; interface FBI
- Connexions de fondation FTR et configuration groupée des éléments de force
- Véhicules simplifiés, excitations TRE / PSD, animations et paramètres de post-traitement

### Série 5 — Dynamique couplée véhicule–voie–pont avec Abaqus et Simpack

- Rails, dalles de voie CRTS III, couches de béton, dalles de base et poutre de pont simplement appuyée
- Matériaux, maillage, attaches, contacts internes et génération de sous-structures
- FBI / FTR, véhicules paramétrés, équilibre statique et couplage véhicule–voie–pont
- Précharge, solveur, irrégularités de voie et grandeurs d’évaluation dynamique abordées dans les vidéos

### Série 6 — Prise en main de la dynamique des véhicules ferroviaires avec Simpack

- Modélisation de l’essieu monté et du châssis de bogie
- Assemblage du véhicule complet
- Fichiers TRE et excitation PSD
- Post-traitement et analyse des réponses

### Série 7 — Dynamique véhicule–voie–pont avec Ansys et Simpack : modélisation Beam–Solid

- RAIL-EULER, rail-timo, pont modélisé en éléments volumiques et thèmes modaux
- Fichiers FBI du rail et du pont ; rédaction et diagnostic FTR
- Véhicules paramétrés, ordre du couplage, raideur et amortissement des zones de transition
- Précharge, solveur, excitation, réponses du pont et du rail, organisation des modèles

### Série 8 — Dynamique véhicule–voie–pont avec Ansys et Simpack : modélisation Beam–Beam

- RAIL-EULER, rail-timo, pont modélisé avec BEAM188 et thèmes modaux
- Configuration FBI / FTR, véhicules paramétrés et couplage véhicule–voie–pont
- Création groupée des points de connexion, liaisons, appuis et capteurs du rail et du pont
- Précharge, solveur, excitation, post-traitement et organisation des modèles

## Téléchargement et utilisation

Dans la série choisie, téléchargez le MP4 et son fichier `.zh-CN.srt` ou `.en.srt`. Conservez l’identifiant commun dans les noms de fichiers, puis sélectionnez le sous-titre dans votre lecteur vidéo local. Le format VTT est également proposé. Un clone du dépôt ou l’archive Code → Download ZIP ne contient pas les vidéos stockées dans Releases.

L’accès aux téléchargements dépend de la visibilité du dépôt. Tant qu’il est privé, un compte GitHub autorisé est nécessaire. Les liens vidéo servent au téléchargement et ne garantissent pas un lecteur de diffusion intégré.

## Langues

La présentation et le guide thématique existent en anglais, chinois simplifié, japonais, français, allemand, italien, espagnol et coréen. Cette localisation concerne les documents ; elle n’ajoute ni pistes de sous-titres ni doublage. Les sous-titres disponibles restent le chinois et l’anglais. Les titres chinois d’origine sont conservés pour identifier précisément les vidéos.

## Périmètre et limites techniques

Il s’agit d’une bibliothèque de tutoriels, pas d’un banc d’essai validé ni d’une distribution de logiciels. La présence d’un modèle dans une vidéo ne signifie pas que ses fichiers, les licences des solveurs ou ses données d’entrée sont fournis. Avant toute adaptation, vérifiez les versions, unités, conditions aux limites, amortissements, réglages de réduction et critères d’évaluation. Les normes évoquées dans des enregistrements anciens ne doivent pas être considérées comme les exigences en vigueur. Beam–Solid et Beam–Beam désignent deux parcours, sans établir une hiérarchie de précision.

La présence des sous-titres et la concordance des sommes de contrôle ne garantissent ni la précision des traductions ni leur synchronisation avec l’audio. Vérifiez les termes techniques dans la vidéo d’origine et la documentation du logiciel concerné.

## Corrections et contributions

Pour signaler une erreur, indiquez la série, l’identifiant stable de la vidéo, la langue du sous-titre et, si nécessaire, l’horodatage. Ne changez pas les identifiants d’origine pour améliorer un titre ou une traduction. Ne déposez pas de logiciel commercial, de licence, de cours tiers ou de modèle sans l’autorisation nécessaire.

## Sources et autorisations

La maintenance du dépôt, la création des cours et la propriété des logiciels sont des rôles distincts. Consultez la déclaration de provenance pour les sources et les droits enregistrés. Aucune affiliation ou approbation officielle des éditeurs n’est revendiquée. L’accès public ne constitue pas une licence générale de réutilisation ou de redistribution des médias.

[Sources et droits](PROVENANCE.md)

[Téléchargement](docs/using-the-library.md) · [Parcours suggérés](docs/learning-paths.md) · [Qualité et versions](docs/quality-and-versions.md) · [Terminologie](docs/terminology.md) · [Contributions](CONTRIBUTING.md) · [Sources et droits](PROVENANCE.md)
