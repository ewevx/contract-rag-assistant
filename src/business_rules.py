import re

def audit_contract_compliance(contract_text: str) -> dict:
    """
    Executa a verificação determinística de regras de compliance
    sobre uma string de contrato juridico
    """
    audit_results = {
        "status_multa": "CONFORME",
        "status_reajuste": "CONFORME",
        "alertas": []
    }


    # Regra-multa-001: Chegagem do teto da multa (>10%)
    multa_match = re.search(r'multa\s+(?:rescisória\s+)?(?:de\s+)?(\d+(?:\,\d+)?)\s*\%', contract_text, re.IGNORECASE)

    if multa_match:
        valor_str = multa_match.group(1).replace(',', '.')
        try:
            multa_valor = float(valor_str)
            if multa_valor > 10.0:
                audit_results["status_multa"] = "ALTO RISCO"
                audit_results["alertas"].append(
                    f"[REGRA-MULTA-001] Violação: Multa identificada em {multa_valor}%, superando o limite legal de 10%."
                )
        except ValueError:
            pass # Ignora caso de formatação inesperada

    # Regra-reajuste-001: Presença de índice inesperada
    indices_validos = ["IPCA", "IGP-M", "INPC", "FIPE", "SELIC"]
    tem_indice = any(indice in contract_text.upper() for indice in indices_validos)

    if not tem_indice:
        audit_results["status_reajuste"] = "ATENÇÃO"
        audit_results["alertas"].append(
            "[REGRA-REAJUSTE-001] Risco: Nenhum índice padrão de reajuste (IPCA, IGP-M, etc.) localizado no contrato."
        )
    return audit_results

print("Módulo de auditoria de regras de negócio carregado com sucesso.")