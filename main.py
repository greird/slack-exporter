#!/usr/bin/env python3
"""
Automatisation de la sauvegarde des pièces jointes Slack
Exporte automatiquement l'historique Slack et télécharge les pièces jointes
"""

import time
import sys
from datetime import datetime, timedelta

from config import logger
from orchestration import Orchestration

def main():
    """Fonction principale"""
    automation = Orchestration()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run-once":
        # Exécution unique
        automation.run_backup()
    else:
        # Exécution périodique (tous les 3 mois)
        logger.info("Mode automatique activé - sauvegarde tous les 3 mois")
        
        while True:
            automation.run_backup()
            
            # Attendre 3 mois (90 jours)
            next_run = datetime.now() + timedelta(days=90)
            logger.info(f"Prochaine sauvegarde: {next_run}")
            
            # Attendre 3 mois
            time.sleep(90 * 24 * 60 * 60)  # 90 jours en secondes

if __name__ == "__main__":
    main()
