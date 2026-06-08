from datetime import date

from difal_apuracao.ncm_rules import RegraNcm, regra_aplicavel, regra_vigente


def _regra(**kwargs) -> RegraNcm:
    defaults = dict(
        ncm="85437099",
        carga_tributaria_pct=8.8,
        ufs_origem=frozenset({"SP"}),
        exclusao_uf=frozenset(),
        tipo="test",
        metodo_novo_difal="formula_padrao",
        vigencia_inicio=None,
        vigencia_fim=date(2026, 5, 31),
    )
    defaults.update(kwargs)
    return RegraNcm(**defaults)


def test_regra_vigente_dentro_do_periodo():
    r = _regra()
    assert regra_vigente(r, date(2026, 5, 15))


def test_regra_expirada_apos_vigencia_fim():
    r = _regra()
    assert not regra_vigente(r, date(2026, 6, 1))


def test_regra_aplicavel_respeita_vigencia():
    r = _regra()
    regras = {r.ncm: r}
    assert regra_aplicavel("85437099", "SP", regras, date(2026, 5, 1))
    assert regra_aplicavel("85437099", "SP", regras, date(2026, 7, 1)) is None
