import pytest
from src.rag_engine import query_contract_copilot

def test_rag_consulta_valida_rastreabilidade():
    """
    Testa se o RAG responde corretamente uma consulta sobre um contrato
    e se o retorno inclui a citação do arquivo original no array de fontes.
    """
    pergunta = "Qual é a porcentagem da multa rescisória estipulada no contrato de serviços de TI?"
    resultado = query_contract_copilot(pergunta)
    
    # 1. Valida se a resposta contém a informação correta (15%)
    assert "15%" in resultado["resposta"]
    
    # 2. Valida se o sistema listou corretamente o arquivo nas fontes consultadas
    fontes_str = " ".join(resultado["documentos_consultados"])
    assert "Prestação de Serviços de TI" in fontes_str or "Alto Risco" in fontes_str

def test_rag_anti_alucinacao():
    """
    Testa a diretiva de Zero Alucinação: quando a informação não consta nos contratos,
    o sistema deve recusar-se a responder inventando fatos.
    """
    pergunta = "Qual é o valor diário do vale-refeição e do auxílio-creche mencionado no contrato?"
    resultado = query_contract_copilot(pergunta)
    
    # Valida se a frase exata de bloqueio foi retornada
    resposta_limpa = resultado["resposta"].strip()
    assert "Informação não encontrada na documentação fornecida" in resposta_limpa