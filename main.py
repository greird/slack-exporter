#!/usr/bin/env python3
"""
Automatisation de la sauvegarde des pièces jointes Slack
Exporte automatiquement l'historique Slack et télécharge les pièces jointes
"""

from orchestration import Orchestration


def main():
    automation = Orchestration()
    automation.run_backup()

if __name__ == "__main__":
    main()
