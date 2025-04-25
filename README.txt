# SIMULATION DE SÉCURITÉ LORAWAN POUR L'IOT

Ce projet contient une simulation de réseau LoRaWAN avec focus sur les aspects de sécurité pour l'Internet des Objets (IoT).

## Fichiers inclus

1. **lora-server.py** - Serveur LoRaWAN avec système de détection d'intrusion
2. **lora-simulation.py** - Simulation d'un nœud LoRaWAN envoyant des données de capteurs
3. **lora-replay-attack.py** - Outil simulant différentes attaques contre le réseau LoRaWAN

## Prérequis

- Python 3.6+
- Bibliothèque Paho MQTT (`pip install paho-mqtt`)
- Broker MQTT local (comme Mosquitto) ou distant

## Configuration

Tous les fichiers utilisent les paramètres par défaut suivants:
- Serveur MQTT: localhost:1883
- Identifiants MQTT: lorauser/lorapass
- Topic MQTT: lorawan/uplink
- Clé d'application: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4

Vous pouvez modifier ces paramètres dans chaque fichier selon vos besoins.

## Comment utiliser

### 1. Démarrer le serveur

```
python lora-server.py
```

Le serveur écoute les messages LoRaWAN sur le topic MQTT et les analyse pour détecter:
- Attaques par rejeu (via vérification des compteurs)
- Passerelles non autorisées
- Anomalies de puissance de signal (RSSI)
- Problèmes d'intégrité des messages

### 2. Simuler un nœud IoT légitime

```
python lora-simulation.py
```

Ce script simule un nœud agricole avec quatre capteurs:
- Température
- Humidité du sol
- Intensité lumineuse
- Détection de parasites

Les données sont chiffrées, signées avec un code d'intégrité (MIC) et envoyées au serveur via une passerelle LoRaWAN.

### 3. Simuler des attaques

```
python lora-replay-attack.py
```

Ce script permet de simuler trois types d'attaques:
1. **Capture de paquets** - Écoute passive du réseau
2. **Attaque par rejeu** - Retransmission de paquets capturés (avec ou sans modification)
3. **Attaque par brouillage** - Inondation du canal avec des messages invalides

## Scénarios de test

1. **Test de base**: Démarrez le serveur et le nœud simulé dans deux terminaux différents
2. **Test d'attaque**: Démarrez le serveur, le nœud simulé, puis l'outil d'attaque
3. **Détection d'intrusion**: Observez comment le serveur détecte et signale les attaques

## Architecture de la simulation

```
+------------+     +-----------+     +-------------+
| Capteurs   |     | Passerelle|     | Serveur     |
| Simulés    |---->| LoRaWAN   |---->| (avec IDS)  |
| (nœud IoT) |     |           |     |             |
+------------+     +-----------+     +-------------+
                         ^
                         |
                   +------------+
                   | Attaquant  |
                   | (Capture/  |
                   |  Rejeu)    |
                   +------------+
```

## Protocoles implémentés

- **MQTT** pour la communication entre passerelle et serveur
- **LoRaWAN simulé** pour la communication entre nœuds et passerelle
  - Chiffrement des données
  - Compteurs de trames (protection contre rejeu)
  - Codes d'intégrité de message (MIC)

## Remarques sur la sécurité

Cette simulation implémente plusieurs aspects de sécurité LoRaWAN:
- Chiffrement AES pour la confidentialité (simulé)
- MIC pour l'intégrité (HMAC-SHA256 simplifié)
- Compteurs de trames pour la protection contre le rejeu
- Détection d'anomalies de signal (anti-usurpation)
- Autorisation de passerelles

Note: Cette simulation est conçue à des fins éducatives et n'implémente pas toutes les fonctionnalités d'un réseau LoRaWAN réel. 