# 🚀 Comment lancer l'application

Vous avez **deux options** pour lancer l'application sans ligne de commande :

## Option 1 : Avec fenêtre de console (Recommandé)
📄 **Double-cliquez sur `launch_app.bat`**

- Affiche une fenêtre de console avec les logs de l'application
- Utile pour voir les messages et erreurs éventuelles
- Fermer la fenêtre arrête l'application

## Option 2 : Mode silencieux (sans console)
📄 **Double-cliquez sur `launch_app_silent.vbs`**

- Lance l'application en arrière-plan sans fenêtre
- Plus propre visuellement
- Pour arrêter l'application : ouvrir le Gestionnaire des tâches et terminer le processus "python.exe"

---

## 🌐 Accès à l'application

Après le lancement, votre navigateur s'ouvrira automatiquement à :
**http://localhost:8501**

Si le navigateur ne s'ouvre pas automatiquement, copiez cette adresse dans votre navigateur.

---

## ⚠️ En cas de problème

Si vous obtenez une erreur "Python n'est pas reconnu" :
1. Vérifiez que Python est bien installé
2. Ouvrez une ligne de commande dans ce dossier
3. Tapez : `python --version` pour vérifier

Si l'application ne se lance pas :
- Assurez-vous d'avoir installé les dépendances : `pip install -r requirements.txt`
- Vérifiez qu'aucune autre instance n'est déjà en cours d'exécution
