"""Testes unitários do targeting-service (sem banco e sem auth-service reais)."""
import requests

from conftest import AUTH

REGRA = {"type": "PERCENTAGE", "value": 50}


def test_health(svc):
    resp = svc.client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_sem_header_de_autorizacao_retorna_401(svc):
    resp = svc.client.get("/rules/novo-checkout")
    assert resp.status_code == 401
    svc.auth_get.assert_not_called()


def test_auth_service_indisponivel_retorna_503(svc):
    svc.auth_get.side_effect = requests.exceptions.ConnectionError()
    resp = svc.client.get("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 503


def test_criar_regra_exige_flag_e_regra(svc):
    resp = svc.client.post("/rules", json={"flag_name": "novo-checkout"}, headers=AUTH)
    assert resp.status_code == 400


def test_criar_regra(svc):
    svc.cursor.fetchone.return_value = {"flag_name": "novo-checkout", "rules": REGRA, "is_enabled": True}
    resp = svc.client.post("/rules", json={"flag_name": "novo-checkout", "rules": REGRA}, headers=AUTH)
    assert resp.status_code == 201
    assert resp.get_json()["rules"] == REGRA
    svc.conn.commit.assert_called_once()


def test_buscar_regra_inexistente_retorna_404(svc):
    svc.cursor.fetchone.return_value = None
    resp = svc.client.get("/rules/nao-existe", headers=AUTH)
    assert resp.status_code == 404


def test_atualizar_regra_sem_campos_retorna_400(svc):
    resp = svc.client.put("/rules/novo-checkout", json={"outro": 1}, headers=AUTH)
    assert resp.status_code == 400


def test_remover_regra_inexistente_retorna_404(svc):
    svc.cursor.rowcount = 0
    resp = svc.client.delete("/rules/nao-existe", headers=AUTH)
    assert resp.status_code == 404
