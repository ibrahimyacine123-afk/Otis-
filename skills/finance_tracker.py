from datetime import datetime
from .db import get_supabase_client

DEFAULT_ACCOUNT = "Principal"


class FinanceTracker:
    def __init__(self):
        self.db = get_supabase_client()

    def _get_or_create_account(self, name: str) -> dict:
        """Récupère un compte par nom ou le crée (inspiré Firefly III : comptes multiples)."""
        existing = self.db.table("accounts").select("*").eq("name", name).execute()
        if existing.data:
            return existing.data[0]
        created = self.db.table("accounts").insert({"name": name}).execute()
        return created.data[0]

    def add_transaction(self, amount: float, description: str, transaction_type: str, category: str = "general", account: str = DEFAULT_ACCOUNT) -> dict:
        """Ajoute une dépense ('expense') ou un revenu ('income') sur un compte donné."""
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

            try:
                account_row = self._get_or_create_account(account or DEFAULT_ACCOUNT)
                account_id = account_row["id"]
            except Exception as account_err:
                # La colonne/table 'accounts' peut ne pas encore exister si la migration
                # backend/migrations/finance_accounts.sql n'a pas été appliquée. On dégrade
                # proprement plutôt que de casser l'ajout de transaction.
                print(f"[FinanceTracker] Comptes indisponibles, transaction non rattachée : {account_err}")
                account_id = None

            data = {
                "amount": amount,
                "description": description,
                "type": transaction_type,
                "category": category,  # On garde l'ancien champ pour rétrocompatibilité
                "category_id": category_id
            }
            if account_id:
                data["account_id"] = account_id

            response = self.db.table("finances").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"Erreur lors de l'ajout de la transaction : {e}")
            return {"success": False, "error": str(e)}

    def get_summary(self) -> dict:
        """Calcule un résumé rapide des finances actuelles (tous comptes confondus)."""
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

    def get_account_balance(self, account: str = DEFAULT_ACCOUNT) -> dict:
        """Calcule le solde d'un compte précis."""
        try:
            account_row = self._get_or_create_account(account)
            response = self.db.table("finances").select("amount, type").eq("account_id", account_row["id"]).execute()
            transactions = response.data

            total_income = sum(float(t["amount"]) for t in transactions if t["type"] == "income")
            total_expense = sum(float(t["amount"]) for t in transactions if t["type"] == "expense")

            return {
                "success": True,
                "account": account,
                "balance": total_income - total_expense
            }
        except Exception as e:
            print(f"Erreur lors du calcul du solde du compte '{account}' : {e}")
            return {"success": False, "account": account, "balance": 0, "error": str(e)}

    def get_monthly_summary(self, year: int = None, month: int = None) -> dict:
        """Résumé du mois courant (ou du mois donné) : total par type et par catégorie."""
        try:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
            start = datetime(year, month, 1).isoformat()
            end_month = month + 1 if month < 12 else 1
            end_year = year if month < 12 else year + 1
            end = datetime(end_year, end_month, 1).isoformat()

            response = self.db.table("finances").select("amount, type, category").gte("created_at", start).lt("created_at", end).execute()
            transactions = response.data

            total_income = sum(float(t["amount"]) for t in transactions if t["type"] == "income")
            total_expense = sum(float(t["amount"]) for t in transactions if t["type"] == "expense")

            by_category = {}
            for t in transactions:
                cat = t.get("category") or "general"
                by_category[cat] = by_category.get(cat, 0) + float(t["amount"])

            return {
                "success": True,
                "period": f"{year}-{month:02d}",
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense,
                "by_category": by_category
            }
        except Exception as e:
            print(f"Erreur lors du résumé mensuel : {e}")
            return {"success": False, "error": str(e)}
