# Especificação de Regras de Negócio — Auditoria Contratual (RAG)

## 1. Visão Geral
Este documento define as verificações determinísticas executadas pelo módulo `business_rules.py`. As regras atuam como uma camada de segurança paralela ao modelo de linguagem (LLM), garantindo que métricas críticas de compliance contratual sejam auditadas com precisão zero-alucinação.

---

## 2. Regra 01: Validação do Teto de Multa Rescisória (`REGRA-MULTA-001`)
- **Parâmetro:** Cláusula de Rescisão e Penalidades.
- **Lógica:** Identificar o percentual monetário associado à quebra de contrato ou rescisão antecipada.
- **Condição de Risco:** Se o valor identificado for `> 10.0%`, o contrato transita para o estado de **ALTO RISCO**.
- **Ação:** O sistema deve registrar uma advertência explícita indicando violação do teto permitido de 10%.

---

## 3. Regra 02: Existência de Índice Formal de Reajuste (`REGRA-REAJUSTE-001`)
- **Parâmetro:** Cláusulas de Valor, Remuneração e Correção Monetária.
- **Lógica:** Verificar se o texto menciona pelo menos um dos índices econômicos aceitos para reajuste contratual automático:
  - `IPCA`, `IGP-M`, `INPC`, `FIPE` ou `SELIC`.
- **Condição de Risco:** Se nenhum dos índices citados for localizado, o contrato transita para o estado de **ATENÇÃO**.
- **Ação:** O sistema deve sinalizar a ausência de índice de correção, indicando risco de inflação não compensada na remuneração.