from mapping.services.integrations.status_utils import (
    classify_error_type,
    friendly_message,
    latency_level,
    is_timeout_error,
    is_auth_error,
)


def test_timeout_detection():
    assert is_timeout_error("request timed out") is True
    assert is_timeout_error("erro qualquer") is False


def test_auth_detection():
    assert is_auth_error("401 unauthorized") is True
    assert is_auth_error("invalid api key") is True
    assert is_auth_error("sem autenticação") is False


def test_error_type_classification():
    assert classify_error_type("timeout", "timeout", True) == "timeout"
    assert classify_error_type("erro_autenticacao", "403", True) == "credencial_invalida"
    assert classify_error_type("offline", "json decode error", True) == "erro_parsing"
    assert classify_error_type("offline", "connection refused", True) == "servico_indisponivel"
    assert classify_error_type("offline", "unexpected", True) == "erro_inesperado"
    assert classify_error_type("online", "", True) == "nenhum"


def test_friendly_message():
    assert "não configurada" in friendly_message("offline", False, "credencial_ausente").lower()
    assert "sucesso" in friendly_message("online", True, "nenhum").lower()
    assert "timeout" in friendly_message("timeout", True, "timeout").lower()


def test_latency_level():
    assert latency_level(None) == "nao_disponivel"
    assert latency_level(200) == "baixa"
    assert latency_level(1200) == "media"
    assert latency_level(4200) == "alta"
