# FAQ

## Nota de público

Este FAQ é voltado para **usuários finais e colaboradores**. Para operação administrativa profunda, consulte `docs/pt-BR/admin.md`.

## 1) O ColaboraPANC é apenas web?
Não. A plataforma inclui backend Django web/API e app mobile Expo/React Native.

## 2) A validação de espécies é totalmente automática por IA?
Não. A IA é assistiva. A validação científica final é feita por revisores humanos autorizados.

## 3) Por que meu ponto não ficou “validado” imediatamente?
Porque pontos podem passar por fila de revisão e checagens de qualidade antes da validação final.

## 4) Posso usar o app sem internet?
Sim, nos fluxos offline suportados. Registros podem ficar em fila local e sincronizar depois.

## 5) O que acontece se a sugestão da IA divergir da revisão humana?
A decisão humana revisada é a referência final; divergência faz parte da governança rastreável de qualidade.

## 6) Onde vejo as rotas e grupos de endpoint da API?
`mapping/urls.py` é a fonte de verdade. A documentação canônica agrupada está em `docs/pt-BR/api.md`.

## 7) Quem pode operar integrações no painel administrativo?
Perfis administrativos (`is_staff`/`is_superuser`) podem acessar painel e endpoints de teste de integrações.

## 8) Como a privacidade é tratada na prática operacional?
A plataforma segue diretrizes técnicas de governança de dados/privacidade (finalidade, minimização, controle de acesso, retenção por política).
Veja: `docs/pt-BR/politica-dados-privacidade-admin.md`.

## 9) Todas as integrações ficam sempre online?
Não. Provedores externos podem ficar degradados/offline. Há endpoints administrativos de health/teste para monitoramento.

## 10) Por onde um colaborador deve começar?
Leia políticas da raiz (`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`) e depois `docs/pt-BR/contribuicao.md`.

## 11) Quais docs são canônicas vs legadas?
Os conjuntos canônicos são `docs/en/` e `docs/pt-BR/`. Docs legadas/de apoio permanecem para rastreabilidade histórica.

## 12) Onde reporto vulnerabilidades?
Não abra issue pública. Siga o processo de divulgação responsável em `SECURITY.md`.
