"""Caminhos de sucesso e de erro das rotas de regras (com o banco simulado)."""
import psycopg2
import requests

from conftest import AUTH

REGRA = {"type": "PERCENTAGE", "value": 50}
CORPO = {"flag_name": "novo-checkout", "rules": REGRA}


def test_chave_invalida_retorna_401(svc):
    svc.auth_get.return_value.status_code = 401
    resp = svc.client.get("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 401


def test_auth_service_em_timeout_retorna_504(svc):
    svc.auth_get.side_effect = requests.exceptions.Timeout()
    resp = svc.client.get("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 504


def test_criar_regra_duplicada_retorna_409(svc):
    svc.cursor.execute.side_effect = psycopg2.IntegrityError()
    resp = svc.client.post("/rules", json=CORPO, headers=AUTH)
    assert resp.status_code == 409
    svc.conn.rollback.assert_called_once()
    svc.pool.putconn.assert_called_once_with(svc.conn)


def test_criar_regra_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.post("/rules", json=CORPO, headers=AUTH)
    assert resp.status_code == 500
    svc.conn.rollback.assert_called_once()


def test_erro_ao_pegar_conexao_do_pool_retorna_500(svc):
    # Sem conexão nem cursor: o finally não tenta fechar nem devolver nada.
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.post("/rules", json=CORPO, headers=AUTH)
    assert resp.status_code == 500
    svc.pool.putconn.assert_not_called()


def test_buscar_regra(svc):
    svc.cursor.fetchone.return_value = {**CORPO, "is_enabled": True}
    resp = svc.client.get("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["rules"] == REGRA


def test_buscar_regra_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.get("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 500


def test_buscar_regra_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.get("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 500


def test_atualizar_regra_sem_corpo_retorna_400(svc):
    resp = svc.client.put("/rules/novo-checkout", json={}, headers=AUTH)
    assert resp.status_code == 400


def test_atualizar_regra(svc):
    svc.cursor.rowcount = 1
    svc.cursor.fetchone.return_value = {**CORPO, "is_enabled": False}
    resp = svc.client.put(
        "/rules/novo-checkout", json={"rules": REGRA, "is_enabled": False}, headers=AUTH
    )
    assert resp.status_code == 200
    query, values = svc.cursor.execute.call_args.args
    assert "rules = %s" in query and "is_enabled = %s" in query
    assert values[1:] == (False, "novo-checkout")
    svc.conn.commit.assert_called_once()


def test_atualizar_regra_inexistente_retorna_404(svc):
    svc.cursor.rowcount = 0
    resp = svc.client.put("/rules/nao-existe", json={"is_enabled": True}, headers=AUTH)
    assert resp.status_code == 404


def test_atualizar_regra_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.put("/rules/novo-checkout", json={"is_enabled": True}, headers=AUTH)
    assert resp.status_code == 500
    svc.conn.rollback.assert_called_once()


def test_atualizar_regra_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.put("/rules/novo-checkout", json={"is_enabled": True}, headers=AUTH)
    assert resp.status_code == 500


def test_remover_regra(svc):
    svc.cursor.rowcount = 1
    resp = svc.client.delete("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 204
    svc.conn.commit.assert_called_once()


def test_remover_regra_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.delete("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 500
    svc.conn.rollback.assert_called_once()


def test_remover_regra_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.delete("/rules/novo-checkout", headers=AUTH)
    assert resp.status_code == 500
