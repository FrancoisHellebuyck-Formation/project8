# Répertoire du Modèle

Ce répertoire contient le modèle de machine learning utilisé dans ce projet.

## Source

Le modèle est téléchargé depuis un serveur de suivi MLflow. Il est le résultat d'une expérience d'entraînement et a été enregistré dans le Registre de Modèles MLflow.

## Usage

Le modèle est chargé par l'application pour effectuer des prédictions. La version spécifique du modèle à utiliser est généralement définie dans la configuration de l'application.

Pour mettre à jour le modèle, une nouvelle version doit être entraînée, enregistrée dans MLflow, puis la configuration doit être mise à jour pour pointer vers la nouvelle version. L'application téléchargera et utilisera alors le modèle mis à jour.

## Contenu

Ce répertoire contiendra les fichiers qui constituent le modèle de ML, tels que :
- `MLmodel` : Un fichier de métadonnées qui décrit le modèle.
- `model.pkl` : L'objet du modèle sérialisé.
- `conda.yaml` ou `requirements.txt` : Les dépendances requises pour exécuter le modèle.
- `python_env.yaml` : Un fichier décrivant l'environnement python.

Ces fichiers sont générés et gérés automatiquement par MLflow. Ne les modifiez pas manuellement.