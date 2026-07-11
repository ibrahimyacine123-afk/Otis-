import os
import sys
import psycopg2

def main():
    # Load DATABASE_URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Erreur : La variable d'environnement DATABASE_URL n'est pas définie.")
        print("Veuillez définir DATABASE_URL (et non SUPABASE_URL) pour vous connecter directement à PostgreSQL.")
        print("Exemple : postgresql://postgres:[MOT_DE_PASSE]@[HOST]:5432/postgres")
        sys.exit(1)

    print("Connexion à la base de données...")
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("Exécution du script SQL...")
        cursor.execute(sql_script)

        print("Les tables ont été créées avec succès ! (tasks, thoughts, finances, reminders)")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Une erreur est survenue lors de l'exécution de la migration : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
