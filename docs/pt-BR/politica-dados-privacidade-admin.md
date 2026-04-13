# Anexo Administrativo: Política de Dados e Privacidade (Base Técnica)

## Escopo

Este anexo separa governança de dados/privacidade da operação administrativa diária.

## 1) Classes de dados tratadas na operação da plataforma
- Dados de conta/autenticação.
- Dados de observação georreferenciada (localização, relato, imagem).
- Metadados de inferência IA e validação científica.
- Dados de interação (mensagens, notificações, gamificação).
- Telemetria e logs operacionais/de integração.

## 2) Dados em contexto sensível
- Geolocalização pode expor áreas ambientalmente sensíveis.
- Imagens podem incluir metadados/traços contextuais.
- Logs operacionais podem conter rastros de incidentes e requerem acesso controlado.

## 3) Base de política (postura técnica alinhada à LGPD)
- Finalidade: processar dados apenas para finalidade científica/operacional da plataforma.
- Minimização: coletar/armazenar somente o necessário.
- Transparência: explicitar limites da IA assistiva e modelo de revisão humana.
- Controle de acesso: acesso por papel para operação admin/revisor.
- Gestão de segredos: credenciais fora do código e rotação quando necessário.

## 4) Retenção e minimização
- Manter histórico científico para auditabilidade e governança.
- Definir janelas de retenção por classe de dado (conta/imagem/log).
- Aplicar geoprecisão reduzida/anonimização em contextos públicos sensíveis quando política exigir.

## 5) Checklist operacional orientado à privacidade
1. Verificar privilégio mínimo antes de exportações/ações administrativas.
2. Evitar exposição desnecessária de dados pessoais/localização em painéis.
3. Garantir restrição de acesso a logs de incidente/auditoria.
4. Aplicar rotinas de retenção/eliminação conforme política aprovada.
