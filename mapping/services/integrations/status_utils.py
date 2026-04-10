def is_timeout_error(error_message: str) -> bool:
    texto = (error_message or "").lower()
    return any(token in texto for token in ["timeout", "timed out", "time out"])


def is_auth_error(error_message: str) -> bool:
    texto = (error_message or "").lower()
    return any(token in texto for token in ["401", "403", "unauthorized", "forbidden", "invalid token", "invalid api key"])


def classify_error_type(status_detail: str, error_message: str, configured: bool) -> str:
    texto = (error_message or "").lower()
    if not configured:
        return "credencial_ausente"
    if status_detail == "nao_configurada":
        return "credencial_ausente"
    if status_detail == "configuracao_invalida":
        return "configuracao_invalida"
    if status_detail == "timeout":
        return "timeout"
    if status_detail == "auth_error":
        return "auth_error"
    if status_detail == "forbidden":
        return "forbidden"
    if status_detail == "not_found":
        return "not_found"
    if status_detail == "rate_limit":
        return "rate_limit"
    if status_detail == "http_error":
        return "http_error"
    if status_detail == "verificacao_limitada":
        return "verificacao_limitada"
    if status_detail == "parcial":
        if "verificacao_limitada" in texto:
            return "verificacao_limitada"
        return "response_empty"
    if status_detail == "response_empty":
        return "response_empty"
    if status_detail == "connection_error":
        return "connection_error"
    if status_detail == "parse_error":
        return "parse_error"
    if status_detail == "schema_error":
        return "schema_error"
    if status_detail == "endpoint_error":
        return "endpoint_error"
    if status_detail == "service_unavailable":
        return "service_unavailable"
    if status_detail == "offline":
        if any(token in texto for token in ["parse", "json", "decode"]):
            return "parse_error"
        if any(token in texto for token in ["dns", "connection", "unreachable", "refused"]):
            return "service_unavailable"
        return "erro_inesperado"
    return "nenhum"


def friendly_message(status_detail: str, configured: bool, error_type: str) -> str:
    if not configured:
        return "Integração não configurada: defina as variáveis de ambiente obrigatórias."
    if status_detail == "online":
        return "Teste concluído com sucesso."
    if status_detail == "parcial":
        return "Teste parcial: integração respondeu, mas com degradação."
    if status_detail == "verificacao_limitada":
        return "Integração configurada; verificação funcional limitada sem endpoint dedicado de healthcheck."
    if status_detail == "timeout":
        return "Teste com timeout: a integração demorou para responder."
    if status_detail == "auth_error":
        return "Teste falhou por autenticação/configuração inválida."
    if error_type == "forbidden":
        return "Credencial sem permissão para o endpoint de healthcheck."
    if error_type == "parse_error":
        return "A integração respondeu com formato inesperado."
    if error_type == "schema_error":
        return "A integração respondeu sem os campos mínimos esperados."
    if error_type == "endpoint_error":
        return "Endpoint externo respondeu com erro HTTP."
    if error_type == "service_unavailable":
        return "Serviço indisponível no momento."
    return "Falha ao executar o teste da integração."


def latency_level(tempo_ms: int | None) -> str:
    if tempo_ms is None:
        return "nao_disponivel"
    if tempo_ms < 800:
        return "baixa"
    if tempo_ms < 2500:
        return "media"
    return "alta"
