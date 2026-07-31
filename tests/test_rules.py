import pytest
from src.business_rules import audit_contract_compliance

# =====================================================================
# SUÍTE 1: TESTES UNITÁRIOS DETERMINÍSTICOS (REGRA DE MULTA > 10%)
# =====================================================================
def test_multa_alto_risco():
    """Valida se uma multa > 10% aciona o status de ALTO RISCO."""
    texto = "Em caso de rescisão antecipada incidirá multa rescisória de 15% sobre o total."
    resultado = audit_contract_compliance(texto)
    
    assert resultado["status_multa"] == "ALTO RISCO"
    assert len(resultado["alertas"]) > 0
    assert "superando o limite legal de 10%" in resultado["alertas"][0]

def test_multa_conforme():
    """Valida se uma multa <= 10% permanece como CONFORME."""
    texto = "Aplica-se a multa rescisória de 10% em caso de quebra de contrato."
    resultado = audit_contract_compliance(texto)
    
    assert resultado["status_multa"] == "CONFORME"

# =====================================================================
# SUÍTE 2: TESTES UNITÁRIOS DETERMINÍSTICOS (REGRA DE ÍNDICE DE REAJUSTE)
# =====================================================================
def test_reajuste_ausente_atencao():
    """Valida se a ausência de índice financeiro dispara status ATENÇÃO."""
    texto = "O valor mensal será revisto mediante negociação de boa-fé entre as partes."
    resultado = audit_contract_compliance(texto)
    
    assert resultado["status_reajuste"] == "ATENÇÃO"
    assert any("Nenhum índice padrão de reajuste" in alt for alt in resultado["alertas"])

def test_reajuste_presente_conforme():
    """Valida se a presença do IPCA ou IGP-M mantém o status CONFORME."""
    texto = "Os valores serão corrigidos anualmente aplicando-se o índice IGP-M."
    resultado = audit_contract_compliance(texto)
    
    assert resultado["status_reajuste"] == "CONFORME"