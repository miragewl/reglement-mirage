# Règlement Mirage WL (V2)

Ce dépôt contient le règlement du serveur. Chaque fois qu'un fichier est modifié, le site se met à jour tout seul (en 1 à 2 minutes).

## Modifier une page

1. Ouvre le dossier **pages** et clique sur la page (par exemple `police.md`).
2. Clique sur le **crayon** en haut à droite du texte.
3. Modifie le texte, puis clique sur **Commit changes…** (en vert) et confirme.

C'est tout : le site est à jour une à deux minutes plus tard. L'onglet **Actions** montre l'avancement (rond orange = en cours, coche verte = en ligne, croix rouge = problème).

### Écrire le texte

- `## Titre` : grand titre de section (il apparaît dans « Sur cette page »)
- `#### Titre` : petit titre
- `**texte**` : gras
- `- texte` : ligne de liste
- `[texte](https://...)` : lien vers un site
- `[texte](police.md)` : lien vers une autre page du règlement
- Encadré :
  ```
  {% hint style="warning" %}
  Texte de l'encadré
  {% endhint %}
  ```
  Styles possibles : `info` (Conseil), `warning` (Important), `danger` (Attention), `success` (À retenir).

### Ajouter une image

1. Ouvre le dossier **images**, clique sur **Add file** puis **Upload files**, et dépose ton image (par exemple `carte.png`).
2. Dans la page, écris `![](images/carte.png)` à l'endroit voulu.

## Ajouter une page

1. Dans le dossier **pages**, clique sur **Add file** puis **Create new file**. Donne-lui un nom simple, sans espace ni accent, terminé par `.md` (par exemple `casino.md`).
2. Première ligne : `# Titre de la page`, puis le texte.
3. Ouvre **sommaire.txt**, clique sur le crayon et ajoute une ligne à l'endroit voulu :
   `casino | Casino | Règlement général`
   (nom du fichier sans .md | titre dans le menu | partie : Accueil, Bien débuter, Règlement général ou Règlement en jeu).

## Changer l'adresse du site

- L'adresse est `https://TON-PSEUDO.github.io/NOM-DU-DÉPÔT/`.
- Pour la changer : **Settings** (en haut), puis renomme le dépôt dans **Repository name**. L'ancienne adresse ne marche plus.
- Pour un nom de domaine à toi (par exemple `reglement.mirage-wl.fr`) : **Settings** puis **Pages** puis **Custom domain**, et suis les indications de GitHub.

## Si le site ne se met pas à jour

Va dans **Actions**, clique sur la ligne avec la croix rouge : le message explique souvent le problème (par exemple une page citée dans `sommaire.txt` qui n'existe pas).

## Contenu du dépôt

- `pages/` : le texte de chaque page
- `sommaire.txt` : l'ordre et les titres des pages dans le menu
- `images/` : logos, emojis des bannières et images des pages
- `modele.html` et `construire.py` : le design et le programme qui fabrique le site (pas besoin d'y toucher)
