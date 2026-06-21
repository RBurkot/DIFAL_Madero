from difal_importacao.config import ImportacaoConfig
from difal_importacao.transformer import resolve_debito_credito


def _cfg() -> ImportacaoConfig:
    return ImportacaoConfig(
        conta_icms_recolher="20140010007",
        conta_imobilizado_2551="12050010100",
    )


def test_cfop_2551_ajuste_positivo():
    debito, credito = resolve_debito_credito("2551", 10.0, _cfg())
    assert debito == "12050010100"
    assert credito == "20140010007"


def test_cfop_2551_ajuste_negativo():
    debito, credito = resolve_debito_credito("2551", -5.0, _cfg())
    assert debito == "20140010007"
    assert credito == "12050010100"


def test_cfop_2556_ajuste_positivo_usa_sb1():
    sb1 = {"P001": "11010020003"}
    contas = resolve_debito_credito(
        "2556", 12.0, _cfg(), cod_produto="P001", sb1_map=sb1
    )
    assert contas == ("11010020003", "20140010007")


def test_cfop_2556_ajuste_negativo_usa_sb1():
    sb1 = {"P001": "11010020003"}
    contas = resolve_debito_credito(
        "2556", -8.0, _cfg(), cod_produto="P001", sb1_map=sb1
    )
    assert contas == ("20140010007", "11010020003")


def test_cfop_2556_sem_sb1_retorna_none():
    assert resolve_debito_credito("2556", 1.0, _cfg(), cod_produto="X", sb1_map={}) is None


def test_cfop_2556_usa_conta_difal_quando_sb1_ausente():
    contas = resolve_debito_credito(
        "2556",
        2.0,
        _cfg(),
        cod_produto="X",
        conta_contabil="11010020003",
        sb1_map={},
    )
    assert contas == ("11010020003", "20140010007")


def test_cfop_2556_normaliza_cfop_excel():
    sb1 = {"12345": "11010020003"}
    contas = resolve_debito_credito(
        "2556.0", 1.0, _cfg(), cod_produto="12345.0", sb1_map=sb1
    )
    assert contas == ("11010020003", "20140010007")


def test_outro_cfop_mantem_conta_contabil():
    contas = resolve_debito_credito(
        "2407", 3.0, _cfg(), conta_contabil="11010020099"
    )
    assert contas == ("11010020099", "20140010007")
