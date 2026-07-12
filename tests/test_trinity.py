"""Tests Phase 5 : verifient le filtre Trinity au niveau de l'orchestrateur SANS
dependre d'un appel reseau reel (LLM NVIDIA mocke), pour rester deterministes et
executables meme quand l'API externe est indisponible (voir BLOCKERS.md).

Lancer : python -m unittest tests.test_trinity -v   (depuis la racine du projet)
"""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.orchestrator import MPCOrchestrator


def _fake_completion(content: str):
    message = MagicMock()
    message.content = content
    message.tool_calls = None
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


class TestTrinityFilter(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MPCOrchestrator()

    def test_high_stakes_message_triggers_clarification_and_audit_log(self):
        """Scenario Phase 5 #1 : "Dois-je faire du levier x3 sur USDT/TRY ? Le marche
        est chaud" -> ego eleve + clarte faible -> OTIS repond par des questions
        (n'execute PAS la boucle ReAct/tool-calling) et journalise dans decision_audit."""
        trinity_json = json.dumps({
            "is_high_stakes": True,
            "ego_test_score": 8,
            "desire_clarity_score": 2,
            "faith_score": 6,
            "emotion_identified": "avidite",
            "emotion_score": 8
        })
        clarify_response = (
            "Avant d'aller plus loin : qu'est-ce qui te pousse vraiment vers ce levier x3 ? "
            "Quel montant exact es-tu prêt à risquer, et selon quelle méthode précise ?"
        )

        # orchestrator.client et trinity.client sont le MEME client partage (Phase 3,
        # skills/llm_client.py) : on mocke un seul point d'entree, avec un side_effect
        # ordonne (1er appel = evaluation Trinity, 2e = clarification OTIS).
        with patch.object(
            self.orchestrator.client.chat.completions, "create",
            side_effect=[_fake_completion(trinity_json), _fake_completion(clarify_response)]
        ) as mock_create, patch.object(self.orchestrator.trinity.db, "rpc") as mock_rpc:
            mock_rpc.return_value.execute.return_value = MagicMock(data=[{"id": "fake-uuid"}])

            response = self.orchestrator.process_request(
                "Dois-je faire du levier x3 sur USDT/TRY ? Le marche est chaud"
            )

            self.assertEqual(response, clarify_response)
            self.assertEqual(mock_create.call_count, 2, "evaluation Trinity + clarification, jamais la boucle ReAct")

            mock_rpc.assert_called_once()
            self.assertEqual(mock_rpc.call_args[0][0], "log_decision_with_trinity")
            rpc_params = mock_rpc.call_args[0][1]
            self.assertEqual(rpc_params["p_ego_test_score"], 8)
            self.assertEqual(rpc_params["p_desire_clarity_score"], 2)
            self.assertEqual(rpc_params["p_emotion_identified"], "avidite")

    def test_trivial_message_skips_trinity_filter_and_audit_log(self):
        """Scenario Phase 5 #2 : message trivial ("Quelle heure est-il ?") -> filtre
        Trinity non declenche (is_high_stakes=False), pas de log decision_audit,
        execution normale de la boucle ReAct."""
        trivial_json = json.dumps({
            "is_high_stakes": False,
            "ego_test_score": 0,
            "desire_clarity_score": 0,
            "faith_score": 0,
            "emotion_identified": "neutre",
            "emotion_score": 0
        })
        direct_response = "Il est 14h32 !"

        with patch.object(
            self.orchestrator.client.chat.completions, "create",
            side_effect=[_fake_completion(trivial_json), _fake_completion(direct_response)]
        ) as mock_create, patch.object(self.orchestrator.trinity.db, "rpc") as mock_rpc:
            response = self.orchestrator.process_request("Quelle heure est-il ?")

            self.assertEqual(response, direct_response)
            self.assertEqual(mock_create.call_count, 2, "evaluation Trinity (triviale) + 1 iteration ReAct normale")
            mock_rpc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
