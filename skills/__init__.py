import sys

# Fix centralise (voir BLOCKERS.md) : sous Windows, des que stdout n'est pas un
# terminal interactif (log redirige, test runner, service...), Python encode
# sur le codepage systeme (ex: cp1254) qui ne supporte pas les emojis utilises
# dans les logs -> UnicodeEncodeError. Applique ici, au niveau du package
# `skills`, pour couvrir TOUS les points d'entree (pas seulement server.py/
# otis.py/scheduler.py) sans dupliquer le correctif partout.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
