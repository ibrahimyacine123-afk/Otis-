"""Test du mecanisme de fallback NVIDIA (skills/llm_client.py) : si le modele
primaire ne repond pas dans PRIMARY_TIMEOUT_SECONDS, on bascule sur
FALLBACK_MODEL. Le timeout reel (30s) est patche a une valeur courte pour que
le test reste rapide -- la logique testee est identique.

Lancer : python -m unittest tests.test_llm_fallback -v
"""
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills import llm_client


def _fake_completion(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


class TestLLMFallback(unittest.TestCase):
    def test_fallback_triggers_on_primary_timeout(self):
        def slow_or_fast(model, **kwargs):
            if model == llm_client.get_llm_model():
                time.sleep(1)  # depasse le timeout patche (0.2s) -> doit declencher le fallback
                return _fake_completion("REPONSE PRIMAIRE (ne devrait jamais etre utilisee)")
            return _fake_completion("REPONSE FALLBACK")

        with patch.object(llm_client, "PRIMARY_TIMEOUT_SECONDS", 0.2), \
             patch.object(llm_client, "_call_model", side_effect=slow_or_fast) as mock_call:
            result = llm_client.chat_completion_with_fallback(
                messages=[{"role": "user", "content": "test"}]
            )

            self.assertEqual(result.choices[0].message.content, "REPONSE FALLBACK")
            # 1er appel sur le modele primaire (qui timeout), 2e sur le fallback
            self.assertEqual(mock_call.call_count, 2)
            self.assertEqual(mock_call.call_args_list[1].args[0], llm_client.FALLBACK_MODEL)

    def test_no_fallback_when_primary_responds_in_time(self):
        with patch.object(llm_client, "PRIMARY_TIMEOUT_SECONDS", 5), \
             patch.object(llm_client, "_call_model", return_value=_fake_completion("REPONSE PRIMAIRE")) as mock_call:
            result = llm_client.chat_completion_with_fallback(
                messages=[{"role": "user", "content": "test"}]
            )

            self.assertEqual(result.choices[0].message.content, "REPONSE PRIMAIRE")
            self.assertEqual(mock_call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
