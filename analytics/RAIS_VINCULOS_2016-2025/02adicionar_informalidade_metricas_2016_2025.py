"""
02adicionar_informalidade_metricas_2016_2025.py

Adiciona a coluna:
    total_vinculos_informais_estimado

no CSV:
    rais_metricas_grupos_2016_2025.csv

A partir do arquivo de informalidade (xlsx/csv) com colunas:
    Escopo, Escala, Recorte, Formal - Total, Informal - Total, Ano

Regra:
    informais_estimados = formais * (pct_informal / pct_formal)

Observações:
- Preenche apenas para grupos do tipo Brasil / Cultura / UF - ... / Capital - ...
- Setores (Indústria, Construção etc.) ficam em branco (NaN), pois não há percentuais.
- 2025: replica os percentuais de 2024 (não há dado disponível para 2025).
- Saída no padrão Brasil: sep=';' e encoding='utf-8-sig', NaN em branco.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


REGEX_GRUPO = re.compile(r"^(UF|Capital)\s*-\s*(.*?)\s*-\s*(Total|Cultura)\s*$")


def norm_key(x: object) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    s = re.sub(r"\s+", " ", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()


def parse_grupo(grupo: str) -> tuple[str | None, str | None, str | None]:
    """
    Retorna (Escopo, Escala, Recorte) conforme padrão do Informalidade2.
    """
    g = (grupo or "").strip()

    if g == "Brasil":
        return "Total", "Nacional", "Brasil"

    if g == "Cultura":
        return "Cultura", "Nacional", "Brasil"

    m = REGEX_GRUPO.match(g)
    if not m:
        return None, None, None

    tipo, recorte, escopo = m.group(1), m.group(2).strip(), m.group(3)
    escala = "Estadual" if tipo == "UF" else "Municipal"
    return escopo, escala, recorte


def coerce_pct(s: pd.Series) -> pd.Series:
    """
    Garante percentuais como fração 0-1. Se vier 0-100, reescala.
    """
    out = pd.to_numeric(s, errors="coerce")
    vmax = out.max(skipna=True)
    if pd.notna(vmax) and vmax > 1.5:
        out = out / 100.0
    return out


def parse_int_safe(s: pd.Series) -> pd.Series:
    """
    Converte total_vinculos para numérico, tolerando separador de milhar '.'.
    """
    x = s.astype(str).str.strip().str.replace(".", "", regex=False)
    return pd.to_numeric(x, errors="coerce")


def load_informalidade(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    try:
        return pd.read_csv(path, sep=";", encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path, sep=",", encoding="utf-8-sig")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--metrics",
        default=r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2016_2025.csv",
        help="CSV de métricas (sep=';')",
    )
    ap.add_argument(
        "--informalidade",
        default=r"E:\Rais\Rais\Auxiliares\Informalidade2.xlsx",
        help="Arquivo de informalidade (xlsx/csv)",
    )
    ap.add_argument(
        "--out",
        default=r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2016_2025_com_informalidade.csv",
        help="Caminho de saída",
    )
    args = ap.parse_args()

    metrics_path  = Path(args.metrics)
    informal_path = Path(args.informalidade)
    out_path      = Path(args.out)

    if not metrics_path.exists():
        print(f"[ERRO] Não encontrei metrics: {metrics_path}", file=sys.stderr)
        return 2
    if not informal_path.exists():
        print(f"[ERRO] Não encontrei informalidade: {informal_path}", file=sys.stderr)
        return 2

    # 1) Lê métricas como texto para preservar formatação BR existente nas outras colunas
    df = pd.read_csv(metrics_path, sep=";", dtype=str, encoding="utf-8-sig")

    for col in ["grupo", "ano", "total_vinculos"]:
        if col not in df.columns:
            print(f"[ERRO] Coluna obrigatória ausente em metrics: {col}", file=sys.stderr)
            return 3

    parsed = df["grupo"].apply(parse_grupo)
    df["_escopo"]  = parsed.apply(lambda x: x[0])
    df["_escala"]  = parsed.apply(lambda x: x[1])
    df["_recorte"] = parsed.apply(lambda x: x[2])

    df["_ano"]         = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["_formais_num"] = parse_int_safe(df["total_vinculos"])

    df["_escopo_key"]  = df["_escopo"].apply(norm_key)
    df["_escala_key"]  = df["_escala"].apply(norm_key)
    df["_recorte_key"] = df["_recorte"].apply(norm_key)

    # 2) Lê informalidade
    inf = load_informalidade(informal_path)

    required_inf = {"Escopo", "Escala", "Recorte", "Formal - Total", "Informal - Total", "Ano"}
    missing = required_inf - set(inf.columns)
    if missing:
        print(f"[ERRO] Colunas ausentes em informalidade: {sorted(missing)}", file=sys.stderr)
        return 4

    inf["_ano"]          = pd.to_numeric(inf["Ano"], errors="coerce").astype("Int64")
    inf["_pct_formal"]   = coerce_pct(inf["Formal - Total"])
    inf["_pct_informal"] = coerce_pct(inf["Informal - Total"])

    inf["_escopo_key"]  = inf["Escopo"].apply(norm_key)
    inf["_escala_key"]  = inf["Escala"].apply(norm_key)
    inf["_recorte_key"] = inf["Recorte"].apply(norm_key)

    # =====================================================
    # 2025: replica percentuais de 2024
    # =====================================================

    inf_2024 = inf[inf["_ano"] == 2024].copy()

    if not inf_2024.empty:
        inf_2025 = inf_2024.copy()
        inf_2025["Ano"]  = 2025
        inf_2025["_ano"] = 2025

        inf = pd.concat([inf, inf_2025], ignore_index=True)

        print(
            f"[INFO] Replicados {len(inf_2025):,} registros de informalidade "
            f"de 2024 para 2025."
        )
    else:
        print(
            "[AVISO] Nenhum registro de 2024 encontrado na tabela "
            "de informalidade. 2025 ficará sem preenchimento."
        )

    # 3) Garante unicidade da chave
    key_cols = ["_ano", "_escopo_key", "_escala_key", "_recorte_key"]
    if inf.duplicated(subset=key_cols).any():
        ex = inf.loc[
            inf.duplicated(subset=key_cols, keep=False),
            ["Ano", "Escopo", "Escala", "Recorte"]
        ].head(30)
        print("[ERRO] Ainda há chaves duplicadas em Informalidade2. Exemplos:", file=sys.stderr)
        print(ex.to_string(index=False), file=sys.stderr)
        return 5

    inf_small = inf[key_cols + ["_pct_formal", "_pct_informal"]].copy()

    # 4) Merge e cálculo
    merged = df.merge(
        inf_small,
        how="left",
        left_on=["_ano", "_escopo_key", "_escala_key", "_recorte_key"],
        right_on=["_ano", "_escopo_key", "_escala_key", "_recorte_key"],
    )

    cond = (
        merged["_escopo"].notna()
        & merged["_formais_num"].notna()
        & merged["_pct_formal"].notna()
        & (merged["_pct_formal"] > 0)
        & merged["_pct_informal"].notna()
    )

    col_new = "total_vinculos_informais_estimado"
    estim = pd.Series(pd.NA, index=merged.index, dtype="Int64")
    estim.loc[cond] = (
        merged.loc[cond, "_formais_num"]
        * (merged.loc[cond, "_pct_informal"] / merged.loc[cond, "_pct_formal"])
    ).round().astype("Int64")

    # 5) Saída preservando colunas originais (texto) + coluna nova
    out = df.drop(
        columns=["_escopo", "_escala", "_recorte", "_ano", "_formais_num",
                 "_escopo_key", "_escala_key", "_recorte_key"],
        errors="ignore"
    )
    out[col_new] = estim.astype("Int64")

    # Coloca a coluna nova logo após total_vinculos
    cols = list(out.columns)
    if "total_vinculos" in cols:
        cols.remove(col_new)
        cols.insert(cols.index("total_vinculos") + 1, col_new)
        out = out[cols]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, sep=";", index=False, encoding="utf-8-sig", na_rep="")

    # 6) Diagnóstico
    total  = len(out)
    filled = out[col_new].notna().sum()
    print(f"[OK] Salvo: {out_path}")
    print(f"[OK] Linhas totais       : {total:,}")
    print(f"[OK] Linhas preenchidas  : {filled:,}")
    print(f"[OK] Linhas em branco    : {total - filled:,}  (setores sem percentual de informalidade)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())