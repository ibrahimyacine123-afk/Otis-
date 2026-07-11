from .db import get_supabase_client

class FinanceTracker:
    def __init__(self):
        self.db = get_supabase_client()

    def add_transaction(self, amount: float, description: str, transaction_type: str, category: str = "general") -> dict:
        """Ajoute une dépense ('expense') ou un revenu ('income')."""
        if transaction_type not in ["income", "expense"]:
            return {"success": False, "error": "Le type de transaction doit être 'income' ou 'expense'."}
            
        try:
            # Recherche de la catégorie
            cat_query = self.db.table("finance_categories").select("*").ilike("name", category).execute()
            if cat_query.data:
                category_id = cat_query.data[0]["id"]
            else:
                # Création dynamique de la catégorie si elle n'existe pas
                new_cat = self.db.table("finance_categories").insert({"name": category, "type": "both"}).execute()
                category_id = new_cat.data[0]["id"]

            data = {
                "amount": amount,
                "description": description,
                "type": transaction_type,
                "category": category, # On garde l'ancien champ pour rétrocompatibilité
                "category_id": category_id
            }
            response = self.db.table("finances").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"Erreur lors de l'ajout de la transaction : {e}")
            return {"success": False, "error": str(e)}

    def get_summary(self) -> dict:
        """Calcule un résumé rapide des finances actuelles."""
        try:
            response = self.db.table("finances").select("amount, type").execute()
            transactions = response.data
            
            total_income = sum(float(t["amount"]) for t in transactions if t["type"] == "income")
            total_expense = sum(float(t["amount"]) for t in transactions if t["type"] == "expense")
            balance = total_income - total_expense
            
            return {
                "success": True,
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": balance
            }
        except Exception as e:
            print(f"Erreur lors de la génération du résumé financier : {e}")
            return {"success": False, "total_income": 0, "total_expense": 0, "balance": 0, "error": str(e)}
