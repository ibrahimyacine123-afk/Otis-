import os
import sys

# Voir server.py pour le detail : force l'UTF-8 pour eviter un UnicodeEncodeError
# sur les emojis quand stdout n'est pas un terminal interactif (ex: log redirige).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Importer le nouvel orchestrateur
from skills.orchestrator import MPCOrchestrator

# Couleurs pour le stylisme dans la console
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_otis(msg):
    """Fonction d'affichage standardisée pour les réponses du majordome."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🤖 OTIS :{Colors.RESET} {msg}\n")

def main():
    print(f"{Colors.GREEN}🚀 Initialisation du système OTIS (Moteur MPC)...{Colors.RESET}")
    load_dotenv()
    
    try:
        # Initialisation de l'orchestrateur autonome
        orchestrator = MPCOrchestrator()
        print(f"{Colors.GREEN}✅ Orchestrateur MPC chargé avec succès.{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur critique lors de l'initialisation : {e}{Colors.RESET}")
        sys.exit(1)

    print_otis("Bonjour ! Je suis en ligne et totalement autonome. Que souhaitez-vous faire ? (tapez 'exit' pour quitter)")

    while True:
        try:
            # Saisie utilisateur
            user_input = input(f"{Colors.YELLOW}Vous :{Colors.RESET} ")
            
            if not user_input.strip():
                continue
                
            if user_input.strip().lower() in ['exit', 'quit', 'quitter']:
                print_otis("À bientôt !")
                break
                
            print(f"  {Colors.CYAN}[OTIS réfléchit...]{Colors.RESET}")
            
            # Délégation complète de la tâche à l'orchestrateur (ReAct Loop)
            final_response = orchestrator.process_request(user_input)
            
            # Affichage de la réponse finale synthétisée par le LLM
            print_otis(final_response)

        except KeyboardInterrupt:
            print_otis("Interruption détectée. À bientôt !")
            break
        except Exception as e:
            print(f"{Colors.RED}\n❌ Erreur inattendue : {e}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
