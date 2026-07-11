import os
import sys
from supabase import create_client, Client

def main():
    # Attempt to load credentials from the environment or a .env file if it exists
    from dotenv import load_dotenv
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Erreur : SUPABASE_URL et SUPABASE_KEY introuvables dans l'environnement.")
        sys.exit(1)

    print("Initialisation du client Supabase...")
    supabase: Client = create_client(url, key)

    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    print("Tentative d'exécution via RPC (Remote Procedure Call)...")
    try:
        # Note: L'appel RPC 'exec_sql' ou 'run_sql' nécessite qu'une telle fonction 
        # ait été préalablement créée côté base de données avec des droits sécurisés.
        # Supabase ne fournit pas cette fonction par défaut pour des raisons de sécurité.
        response = supabase.rpc("exec_sql", {"sql_string": sql_script}).execute()
        print("Requête RPC exécutée avec succès !")
        print("Réponse :", response.data)
    except Exception as e:
        print(f"Échec de l'exécution RPC : {e}")
        print("\nNote: Si la fonction RPC n'existe pas, vous devrez exécuter le fichier schema.sql manuellement dans l'éditeur SQL de votre tableau de bord Supabase.")

if __name__ == "__main__":
    main()
