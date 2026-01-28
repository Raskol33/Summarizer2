# 🔒 Guide : Héberger le YouTube Summarizer sur votre VPS (100% Local)

Ce guide vous explique comment héberger l'application sur votre propre VPS pour que **toutes vos données restent sous votre contrôle** et ne soient jamais envoyées aux États-Unis ou à des services tiers.

---

## 📋 Table des matières

1. [Prérequis VPS](#prérequis-vps)
2. [Option 1 : Ollama (Recommandé)](#option-1--ollama-recommandé)
3. [Option 2 : vLLM (Pour GPU puissants)](#option-2--vllm-pour-gpu-puissants)
4. [Option 3 : Text Generation Inference](#option-3--text-generation-inference)
5. [Configuration de l'application](#configuration-de-lapplication)
6. [Accès distant sécurisé](#accès-distant-sécurisé)
7. [Comparaison des solutions](#comparaison-des-solutions)

---

## 🖥️ Prérequis VPS

### Configuration minimale recommandée :

| Composant | Minimum | Recommandé | Idéal |
|-----------|---------|------------|-------|
| **RAM** | 16 GB | 32 GB | 64 GB |
| **CPU** | 4 cœurs | 8 cœurs | 16+ cœurs |
| **GPU** | Optionnel | NVIDIA 8GB VRAM | NVIDIA 24GB VRAM |
| **Stockage** | 50 GB | 100 GB | 200 GB |
| **Bande passante** | 100 Mbps | 1 Gbps | 1 Gbps |

### OS recommandé :
- Ubuntu 22.04 LTS ou 24.04 LTS
- Debian 12
- Rocky Linux 9

---

## 🚀 Option 1 : Ollama (Recommandé)

### ✅ Avantages :
- Installation ultra-simple (1 commande)
- Gestion automatique des modèles
- Faible consommation de ressources
- Optimisé pour CPU et GPU
- Communauté active

### 📦 Installation sur votre VPS

```bash
# 1. Se connecter à votre VPS
ssh votre-utilisateur@votre-vps-ip

# 2. Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Télécharger un modèle
# Pour 16 GB RAM (version quantifiée, plus légère)
ollama pull llama3.1:8b-instruct-q4_0

# Pour 32+ GB RAM (version complète)
ollama pull llama3.1:8b

# Alternatives performantes
ollama pull mistral:7b          # Excellent pour le français
ollama pull gemma2:9b           # Très performant
ollama pull qwen2.5:7b          # Bon multilingue

# 4. Lancer le serveur Ollama
ollama serve

# Pour lancer en arrière-plan avec systemd (recommandé)
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

### 🔧 Configuration réseau

Par défaut, Ollama écoute sur `localhost:11434`. Pour y accéder depuis d'autres machines :

```bash
# Ouvrir le port dans le firewall (UFW sur Ubuntu)
sudo ufw allow 11434/tcp

# Ou configurer Ollama pour écouter sur toutes les interfaces
# Éditer le fichier de service
sudo systemctl edit ollama

# Ajouter ces lignes :
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"

# Redémarrer
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 📱 Utiliser l'application locale

```bash
# Sur votre VPS, installer les dépendances Python
pip install langchain langchain-community

# Lancer l'application locale
streamlit run app_local.py --server.port 8501 --server.address 0.0.0.0

# Ouvrir le port Streamlit
sudo ufw allow 8501/tcp

# Accéder depuis votre navigateur
# http://votre-vps-ip:8501
```

### 🧪 Tester la connexion

```bash
# Test local
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello, world!",
  "stream": false
}'

# Test distant (depuis votre PC)
curl http://votre-vps-ip:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Bonjour!",
  "stream": false
}'
```

---

## 🎯 Option 2 : vLLM (Pour GPU puissants)

### ✅ Avantages :
- Performance maximale avec GPU
- Support de nombreux modèles
- Optimisations avancées
- API compatible OpenAI

### ⚠️ Prérequis :
- GPU NVIDIA avec 16+ GB VRAM
- CUDA installé
- Plus complexe à configurer

### 📦 Installation

```bash
# 1. Installer CUDA (si pas déjà fait)
# Suivre : https://developer.nvidia.com/cuda-downloads

# 2. Installer vLLM
pip install vllm

# 3. Télécharger un modèle depuis Hugging Face
# Exemple : Meta-Llama-3.1-8B-Instruct
huggingface-cli login  # Entrer votre token HF

# 4. Lancer le serveur vLLM
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 8000
```

### 🔧 Adapter l'application pour vLLM

Remplacer dans le code :
```python
from langchain_community.llms import VLLMOpenAI

llm = VLLMOpenAI(
    openai_api_key="EMPTY",
    openai_api_base="http://votre-vps-ip:8000/v1",
    model_name="meta-llama/Meta-Llama-3.1-8B-Instruct"
)
```

---

## 🏗️ Option 3 : Text Generation Inference (TGI)

### ✅ Avantages :
- Développé par Hugging Face
- Très optimisé
- Support Docker
- Production-ready

### 📦 Installation avec Docker

```bash
# 1. Installer Docker
curl -fsSL https://get.docker.com | sh

# 2. Lancer TGI avec un modèle
docker run --gpus all --shm-size 1g -p 8080:80 \
    -v /data:/data \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id meta-llama/Meta-Llama-3.1-8B-Instruct \
    --quantize bitsandbytes

# Sans GPU (CPU uniquement)
docker run --shm-size 1g -p 8080:80 \
    -v /data:/data \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id meta-llama/Meta-Llama-3.1-8B-Instruct
```

---

## 🔐 Accès distant sécurisé

### Option A : Reverse Proxy avec Nginx + SSL

```bash
# 1. Installer Nginx et Certbot
sudo apt install nginx certbot python3-certbot-nginx

# 2. Configuration Nginx
sudo nano /etc/nginx/sites-available/summarizer

# Contenu :
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# 3. Activer et obtenir SSL
sudo ln -s /etc/nginx/sites-available/summarizer /etc/nginx/sites-enabled/
sudo certbot --nginx -d votre-domaine.com

# 4. Redémarrer Nginx
sudo systemctl restart nginx
```

### Option B : Tunnel SSH (Temporaire)

```bash
# Depuis votre PC local
ssh -L 8501:localhost:8501 -L 11434:localhost:11434 user@votre-vps-ip

# Accéder localement via :
# http://localhost:8501
```

### Option C : VPN (WireGuard)

Plus sécurisé pour un accès permanent. Configuration WireGuard disponible sur demande.

---

## 📊 Comparaison des solutions

| Critère | Ollama | vLLM | TGI | Groq (Cloud) |
|---------|--------|------|-----|--------------|
| **Facilité d'installation** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance CPU** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | N/A |
| **Performance GPU** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | N/A |
| **Gestion mémoire** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | N/A |
| **Confidentialité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **Coût** | Gratuit | Gratuit | Gratuit | Limité gratuit |
| **Vitesse** | Rapide | Très rapide | Très rapide | Ultra rapide |
| **RAM minimum** | 8 GB | 16 GB | 16 GB | 0 |

---

## 🎯 Recommandation finale

### Pour vous (VPS sans GPU) :
👉 **Ollama avec llama3.1:8b-instruct-q4_0**

**Pourquoi ?**
- Installation en 2 minutes
- Fonctionne bien sur CPU
- Consommation RAM optimisée (8-12 GB)
- Modèles faciles à changer
- Maintenance minimale

### Commandes complètes pour démarrer :

```bash
# Sur votre VPS
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b-instruct-q4_0
sudo systemctl enable ollama
sudo systemctl start ollama

# Tester
curl http://localhost:11434/api/generate -d '{"model":"llama3.1:8b-instruct-q4_0","prompt":"Bonjour!","stream":false}'

# Sur votre PC (cloner le projet)
cd E:\Projets\Summarizer
pip install langchain-community
python -m streamlit run app_local.py

# Dans l'interface, configurer :
# URL Ollama : http://votre-vps-ip:11434
# Modèle : llama3.1:8b-instruct-q4_0
```

---

## 📞 Support et ressources

- **Documentation Ollama** : https://github.com/ollama/ollama
- **Liste des modèles** : https://ollama.com/library
- **Forum Ollama** : https://github.com/ollama/ollama/discussions
- **LangChain + Ollama** : https://python.langchain.com/docs/integrations/llms/ollama

---

## 🔄 Migration Groq → Ollama

Pour migrer votre application existante :

1. ✅ J'ai créé `app_local.py` (version locale)
2. ✅ Lancez Ollama sur votre VPS
3. ✅ Configurez l'URL du serveur dans l'app
4. ✅ Vos données ne quittent plus votre infrastructure !

**Comparaison :**
- **Avant** : Données → Groq (USA) → Retour
- **Maintenant** : Données → Votre VPS (France/EU) → Retour

---

Des questions sur l'installation ou besoin d'aide pour configurer votre VPS ? Je suis là ! 🚀
