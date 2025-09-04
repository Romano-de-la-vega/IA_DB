# Assistant SQL

Application web légère permettant d'interroger une base de données SQL en langage naturel.

## Fonctionnalités

- Formulaire pour poser une question en texte libre
- Conversion de la question en requête SQL via l'API OpenAI
- Exécution de la requête sur la base configurée
- Interprétation des résultats par l'IA pour fournir une réponse concise
- Panneau de paramètres (type de base, hôte, utilisateur, etc.) avec bouton de test de connexion

## Lancement

```bash
python main_gui.py
```

Assurez-vous de disposer des dépendances listées dans `requirements.txt` et d'une clé API OpenAI valide (variable d'environnement `OPENAI_API_KEY` ou saisie dans l'interface).
