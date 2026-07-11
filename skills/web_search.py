from duckduckgo_search import DDGS

class WebSearcher:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 5) -> dict:
        """Effectue une recherche web via DuckDuckGo et retourne les résultats pertinents."""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            formatted_results = []
            
            for r in results:
                formatted_results.append({
                    "title": r.get("title"),
                    "snippet": r.get("body"),
                    "link": r.get("href")
                })
                
            return {
                "success": True,
                "data": formatted_results
            }
        except Exception as e:
            print(f"Erreur lors de la recherche web : {e}")
            return {
                "success": False,
                "error": str(e)
            }
