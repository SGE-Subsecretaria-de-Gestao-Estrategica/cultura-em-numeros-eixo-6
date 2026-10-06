"""
02adicionar_informalidade_metricas_2016_2025.py

Acrescenta ao CSV de métricas os valores absolutos de trabalhadores da tabela
Informalidade2.xlsx, sem estimar vínculos por meio de percentuais.

Saída:
- Renomeia total_vinculos para total_vinculos_rais, preservando seus valores.
- Preenche total_vinculos_informais_estimado com Trabalhadores - Cultura.
- Acrescenta total_vinculos_ibge com Trabalhadores - Total.
- 2025 e grupos sem correspondência ficam em branco.
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
        default=r"E:\Rais\Rais\Informalidade\Informalidade2.xlsx",
        help="Arquivo de informalidade (xlsx/csv)",
    )
    ap.add_argument(
        "--out",
        default=r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2025_com_informalidade.csv",
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

    df["_ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    df["_escopo_key"]  = df["_escopo"].apply(norm_key)
    df["_escala_key"]  = df["_escala"].apply(norm_key)
    df["_recorte_key"] = df["_recorte"].apply(norm_key)

    # 2) Lê informalidade
    inf = load_informalidade(informal_path)

    required_inf = {
        "Escopo", "Escala", "Recorte", "Ano",
        "Trabalhadores - Total", "Trabalhadores - Cultura",
    }
    missing = required_inf - set(inf.columns)
    if missing:
        print(f"[ERRO] Colunas ausentes em informalidade: {sorted(missing)}", file=sys.stderr)
        print(f"[INFO] Colunas encontradas em {informal_path}: {list(inf.columns)}", file=sys.stderr)
        print(
            "[INFO] O arquivo precisa ser a versão gerada pelo 01_extrai_informalidade.py, "
            "que contém as colunas 'Trabalhadores - Total' e 'Trabalhadores - Cultura'.",
            file=sys.stderr,
        )
        return 4

    inf["_ano"] = pd.to_numeric(inf["Ano"], errors="coerce").astype("Int64")
    inf["_trabalhadores_total"] = pd.to_numeric(
        inf["Trabalhadores - Total"], errors="coerce"
    ).round().astype("Int64")
    inf["_trabalhadores_cultura"] = pd.to_numeric(
        inf["Trabalhadores - Cultura"], errors="coerce"
    ).round().astype("Int64")

    inf["_escopo_key"]  = inf["Escopo"].apply(norm_key)
    inf["_escala_key"]  = inf["Escala"].apply(norm_key)
    inf["_recorte_key"] = inf["Recorte"].apply(norm_key)

    # 3) Garante unicidade da chave; não replica valores de 2024 para 2025.
    key_cols = ["_ano", "_escopo_key", "_escala_key", "_recorte_key"]
    if inf.duplicated(subset=key_cols).any():
        ex = inf.loc[
            inf.duplicated(subset=key_cols, keep=False),
            ["Ano", "Escopo", "Escala", "Recorte"]
        ].head(30)
        print("[ERRO] Há chaves duplicadas em Informalidade2. Exemplos:", file=sys.stderr)
        print(ex.to_string(index=False), file=sys.stderr)
        return 5

    inf_small = inf[key_cols + ["_trabalhadores_total", "_trabalhadores_cultura"]].copy()

    # 4) As métricas de entrada começam em 2016. Acrescenta ao conjunto as
    #    chaves de 2015 presentes na fonte, para que seus valores não sejam descartados.
    #    As colunas de métricas que só existem na RAIS permanecem vazias nessas linhas.
    existing_keys = set(
        map(tuple, df[key_cols].itertuples(index=False, name=None))
    )
    rows_2015 = []
    source_2015 = inf.loc[inf["_ano"].eq(2015)]
    for _, src in source_2015.iterrows():
        scope_key = src["_escopo_key"]
        scale_key = src["_escala_key"]
        scope_label = {"total": "Total", "cultura": "Cultura"}.get(scope_key)
        recorte = str(src["Recorte"]).strip()

        if scope_label is None:
            continue
        if scale_key == "nacional":
            grupo = "Brasil" if scope_key == "total" else "Cultura"
        elif scale_key == "estadual":
            grupo = f"UF - {recorte} - {scope_label}"
        elif scale_key == "municipal":
            grupo = f"Capital - {recorte} - {scope_label}"
        else:
            continue

        key = (2015, scope_key, scale_key, src["_recorte_key"])
        if key in existing_keys:
            continue

        new_row = {column: pd.NA for column in df.columns}
        new_row.update({
            "grupo": grupo,
            "ano": "2015",
            "total_vinculos": pd.NA,
            "_escopo": src["Escopo"],
            "_escala": src["Escala"],
            "_recorte": src["Recorte"],
            "_ano": 2015,
            "_escopo_key": scope_key,
            "_escala_key": scale_key,
            "_recorte_key": src["_recorte_key"],
        })
        rows_2015.append(new_row)
        existing_keys.add(key)

    if rows_2015:
        df = pd.concat(
            [df, pd.DataFrame(rows_2015, columns=df.columns)],
            ignore_index=True,
        )

    # 5) Associa os valores nominais diretamente, sem cálculo por percentuais.
    merged = df.merge(
        inf_small,
        how="left",
        on=key_cols,
    )
    # 2025 deve permanecer sem valores, mesmo se houver uma linha desse ano na fonte.
    mask_2025 = merged["_ano"] == 2025
    merged.loc[mask_2025, ["_trabalhadores_total", "_trabalhadores_cultura"]] = pd.NA

    # 5) Saída preservando os valores originais e adicionando as métricas da tabela.
    out = df.drop(
        columns=["_escopo", "_escala", "_recorte", "_ano",
                 "_escopo_key", "_escala_key", "_recorte_key"],
        errors="ignore"
    ).copy()
    out = out.rename(columns={"total_vinculos": "total_vinculos_rais"})
    out["total_vinculos_informais_estimado"] = merged["_trabalhadores_cultura"].astype("Int64")
    out["total_vinculos_ibge"] = merged["_trabalhadores_total"].astype("Int64")

    # Coloca as duas colunas novas logo após total_vinculos_rais.
    cols = list(out.columns)
    for col_new in ["total_vinculos_informais_estimado", "total_vinculos_ibge"]:
        cols.remove(col_new)
    insert_at = cols.index("total_vinculos_rais") + 1
    cols[insert_at:insert_at] = [
        "total_vinculos_informais_estimado",
        "total_vinculos_ibge",
    ]
    out = out[cols]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, sep=";", index=False, encoding="utf-8-sig", na_rep="")

    # 6) Diagnóstico
    total = len(out)
    filled_cultura = out["total_vinculos_informais_estimado"].notna().sum()
    filled_total = out["total_vinculos_ibge"].notna().sum()
    print(f"[OK] Salvo: {out_path}")
    count_2015_source = int(source_2015.shape[0])
    count_2015_filled = int((merged["_ano"].eq(2015) & merged["_trabalhadores_total"].notna()).sum())
    print(f"[OK] Linhas totais: {total:,}")
    print(f"[INFO] Registros de 2015 na fonte: {count_2015_source:,}")
    print(f"[INFO] Registros de 2015 com Trabalhadores - Total associado: {count_2015_filled:,}")
    if count_2015_source and count_2015_filled == 0:
        print("[AVISO] A fonte tem ano 2015, mas nenhuma chave foi associada. Confira Escopo/Escala/Recorte.", file=sys.stderr)
    print(f"[OK] Linhas de 2015 acrescentadas ao CSV de métricas: {len(rows_2015):,}")
    print(f"[OK] Trabalhadores - Cultura preenchidos: {filled_cultura:,}")
    print(f"[OK] Trabalhadores - Total preenchidos  : {filled_total:,}")
    print(f"[OK] Valores de 2025 não são replicados; sem correspondência ficam em branco.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())