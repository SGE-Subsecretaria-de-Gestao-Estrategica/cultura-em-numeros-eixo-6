from __future__ import annotations

"""
02_estab_detalhes_2025.py
----
Processamento RAIS Estabelecimentos (2025)

Lógica de Saída:
  1. Base Cultura: Filtra Ind Rais Negativa == "0" AND CNAE Cultura.
     Gera CSV com CNAE (5 dígitos), Tamanho e Natureza Jurídica.
  2. Síntese Brasil NJ: Filtra apenas Ind Rais Negativa == "0" (Todos os CNAEs).
     Gera totais por Categoria de Natureza Jurídica.
  3. Síntese Brasil Tamanho: Filtra apenas Ind Rais Negativa == "0" (Todos os CNAEs).
     Gera totais por Categoria de Tamanho.

Padrão de saída: CSV brasileiro (sep=";", decimal=",", encoding=utf-8-sig)
"""

from pathlib import Path
from collections import defaultdict
import re
import csv
import sys
import pandas as pd

# Evita "_csv.Error: field larger than field limit" em arquivos com campos grandes
csv.field_size_limit(sys.maxsize)

# ====
# CONFIGURAÇÃO DE CAMINHOS
# ====

DIR_ESTAB = Path(r"E:\Rais\Estabelecimentos")

# Mapeamento ano -> nome do arquivo
ARQUIVOS_POR_ANO: dict[int, Path] = {
    2025: DIR_ESTAB / "Estb2025ID.COMT",
}

CNAE_CULTURA_XLSX = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\auxiliares\CNAE-ibge.xlsx")
CNAE_CULTURA_COL  = "CNAE_IBGE"

OUT_DIR = Path(r"E:\Rais\DF2\data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT1 = OUT_DIR / "saida_1_estab_cultura_2025_base.csv"
OUT2 = OUT_DIR / "saida_2_brasil_natureza_juridica_categoria.csv"
OUT3 = OUT_DIR / "saida_3_brasil_tamanho_estabelecimento_categoria.csv"

CHUNK_SIZE = 300_000

# Padrão de escrita CSV brasileiro
CSV_PARAMS = dict(
    sep      = ";",
    decimal  = ",",
    encoding = "utf-8-sig",
    index    = False,
)

# ====
# MAPEAMENTOS E CATEGORIZAÇÃO
# ====

NJ_ADMIN_PUBLICA = {
    "1015","1023","1031","1040","1058","1066","1074","1082","1104","1112",
    "1120","1139","1147","1155","1163","1171","1180","1198","1210","1228",
    "1236","1244","1252","1260","1279","1287","1295","1309","1317","1325",
    "1333","1341",
}
NJ_EMPRESARIAIS = {
    "2011","2038","2046","2054","2062","2070","2089","2097","2127","2135",
    "2143","2151","2160","2178","2194","2216","2224","2232","2240","2259",
    "2267","2275","2283","2291","2305","2313","2321","2330","2348","2356",
}
NJ_SEM_FINS = {
    "3034","3069","3077","3085","3107","3115","3131","3204","3212","3220",
    "3239","3247","3255","3263","3271","3280","3298","3301","3310","3328",
    "3999",
}
NJ_PESSOAS_FISICAS = {"4014","4022","4081","4090","4111","4120"}
NJ_ORG_INT         = {"5010","5029","5037"}

def categorizar_nj(nj_cod: str) -> str:
    if nj_cod in NJ_ADMIN_PUBLICA: return "Administração Pública"
    if nj_cod in NJ_EMPRESARIAIS:  return "Entidades Empresariais"
    if nj_cod in NJ_SEM_FINS:      return "Entidades sem Fins Lucrativos"
    if nj_cod in NJ_PESSOAS_FISICAS: return "Pessoas Físicas"
    if nj_cod in NJ_ORG_INT:       return "Organizações Internacionais e Outras Instituições Extraterritoriais"
    return "Outros"

TAM_MAP = {
    "1":  "0 Empregados",
    "2":  "1 a 4",
    "3":  "5 a 9",
    "4":  "10 a 19",
    "5":  "20 a 49",
    "6":  "50 a 99",
    "7":  "100 a 249",
    "8":  "250 a 499",
    "9":  "500 a 999",
    "10": "1000 ou mais",
}
ORDEM_TAM = list(TAM_MAP.values()) + ["Outros/Inválido"]

# ====
# UTILITÁRIOS
# ====

def _norm_5(v: str) -> str:
    d = re.sub(r"\D", "", str(v))
    return d[:5].zfill(5) if len(d) >= 5 else d.zfill(5)

def _norm_dig(v: str) -> str:
    return re.sub(r"\D", "", str(v)).lstrip("0")

def _norm_nj(v: str) -> str:
    return re.sub(r"\D", "", str(v))

def _kwargs_csv(arquivo: Path) -> dict:
    """
    Retorna kwargs de leitura específicos por tipo de arquivo.
    .COMT (2025): sep=',', engine c, quoting padrão (CSV bem formado)
    """
    return {"sep": ",", "engine": "c"}

def _escolher_coluna(colunas: list[str], candidatos: list[str]) -> str:
    cols_norm = [c.replace("\ufeff", "").strip() for c in colunas]
    for cand in candidatos:
        if cand in cols_norm:
            return colunas[cols_norm.index(cand)]
    raise KeyError(
        f"Coluna não encontrada.\n"
        f"  Candidatos : {candidatos}\n"
        f"  Disponíveis: {cols_norm}"
    )

# ====
# PROCESSAMENTO POR ARQUIVO
# ====

def processar_ano(
    arquivo: Path,
    ano: int,
    cnaes_cultura: set[str],
    nj_counts: dict,
    tam_counts: dict,
    out1_path: Path,
    ref_primeiro_write: list[bool],
) -> None:

    kw = _kwargs_csv(arquivo)

    df0 = pd.read_csv(arquivo, nrows=0, encoding="latin1", dtype=str,
                    on_bad_lines="skip", **kw)
    raw_cols     = df0.columns.tolist()
    clean_cols   = [c.replace("\ufeff", "").strip().strip('"') for c in raw_cols]
    raw_to_clean = dict(zip(raw_cols, clean_cols))
    clean_to_raw = dict(zip(clean_cols, raw_cols))

    col_cnae = _escolher_coluna(clean_cols, ["CNAE 2.0 Subclasse", "CNAE 2.0 Subclasse - Código", "CNAE 2.0 Subclasse - Codigo"])
    col_tam  = _escolher_coluna(clean_cols, ["Tamanho Estabelecimento", "Tamanho Estabelecimento - Código"])
    col_nj   = _escolher_coluna(clean_cols, ["Natureza Jurídica", "Natureza Jurídica - Código"])
    col_ind  = _escolher_coluna(clean_cols, ["Ind Rais Negativa", "Ind RAIS Negativa - Código", "Ind Rais Negativa - Código"])

    usecols_raw = [clean_to_raw[c] for c in [col_cnae, col_tam, col_nj, col_ind]]

    print(f"\n[{ano}] {arquivo.name}")
    print(f"       CNAE={col_cnae!r} | TAM={col_tam!r} | NJ={col_nj!r} | IND_NEG={col_ind!r}")

    total_lidas     = 0
    total_filtradas = 0
    n_chunk         = 0

    for chunk in pd.read_csv(
        arquivo,
        encoding="latin1",
        usecols=usecols_raw,
        dtype=str,
        chunksize=CHUNK_SIZE,
        on_bad_lines="skip",
        **kw,
    ):
        n_chunk += 1
        print(f"       chunk {n_chunk:>3} | linhas acumuladas: {total_lidas + len(chunk):>10,}", end="\r")

        chunk.columns = [raw_to_clean.get(c, c.replace("\ufeff", "").strip().strip('"')) for c in chunk.columns]
        for c in chunk.columns:
            chunk[c] = chunk[c].astype(str).str.strip()

        total_lidas += len(chunk)

        # Filtro global: apenas Ind Rais Negativa == "0"
        chunk = chunk[chunk[col_ind] == "0"]
        if chunk.empty:
            continue

        # Normalizar campos
        njs  = chunk[col_nj].apply(_norm_nj)
        tams = chunk[col_tam].apply(_norm_dig)

        # ── Síntese Brasil (todos os CNAEs) ────
        for cat, cnt in njs.apply(categorizar_nj).value_counts().items():
            nj_counts[(ano, cat)] += int(cnt)

        for cat, cnt in tams.map(lambda x: TAM_MAP.get(x, "Outros/Inválido")).value_counts().items():
            tam_counts[(ano, cat)] += int(cnt)

        # ── Base Cultura (filtro adicional por CNAE) ────
        cnae5        = chunk[col_cnae].apply(_norm_5)
        mask_cultura = cnae5.isin(cnaes_cultura)

        if mask_cultura.any():
            total_filtradas += mask_cultura.sum()
            df_cultura = pd.DataFrame({
                "ano":              ano,
                "cnae_5":           cnae5[mask_cultura].values,
                "tam_estab":        tams[mask_cultura].values,
                "natureza_juridica": njs[mask_cultura].values,
            })
            df_cultura.to_csv(
                out1_path,
                mode="a",
                header=ref_primeiro_write[0],
                **CSV_PARAMS,
            )
            ref_primeiro_write[0] = False

    print(f"       Linhas lidas: {total_lidas:>10,} | Cultura após filtros: {total_filtradas:>8,}")

# ====
# MAIN
# ====

def main() -> None:
    # Validar entradas
    ausentes = [str(arq) for arq in ARQUIVOS_POR_ANO.values() if not arq.exists()]
    if ausentes:
        raise FileNotFoundError(
            "Arquivo(s) não encontrado(s):\n  " + "\n  ".join(ausentes)
        )

    # Carregar CNAEs Cultura
    df_cult = pd.read_excel(CNAE_CULTURA_XLSX, dtype={CNAE_CULTURA_COL: str})
    cnaes_set = set(df_cult[CNAE_CULTURA_COL].astype(str).str.strip().apply(_norm_5).tolist())
    print(f"CNAEs Cultura carregados: {len(cnaes_set)}")

    # Limpar saídas anteriores
    for f in [OUT1, OUT2, OUT3]:
        if f.exists():
            f.unlink()

    nj_counts:  dict[tuple[int, str], int] = defaultdict(int)
    tam_counts: dict[tuple[int, str], int] = defaultdict(int)
    ref_primeiro_write = [True]

    for ano, arq in sorted(ARQUIVOS_POR_ANO.items()):
        processar_ano(arq, ano, cnaes_set, nj_counts, tam_counts, OUT1, ref_primeiro_write)

    # ── Saída 2: Brasil por Natureza Jurídica ────
    df_out2 = (
        pd.DataFrame([
            {"ano": ano, "categoria_natureza_juridica": cat, "total_estabelecimentos": total}
            for (ano, cat), total in nj_counts.items()
        ])
        .sort_values(["ano", "categoria_natureza_juridica"])
        .reset_index(drop=True)
    )
    df_out2.to_csv(OUT2, **CSV_PARAMS)

    # ── Saída 3: Brasil por Tamanho de Estabelecimento ────
    df_out3 = pd.DataFrame([
        {"ano": ano, "categoria_tamanho_estabelecimento": cat, "total_estabelecimentos": total}
        for (ano, cat), total in tam_counts.items()
    ])
    df_out3["categoria_tamanho_estabelecimento"] = pd.Categorical(
        df_out3["categoria_tamanho_estabelecimento"],
        categories=ORDEM_TAM,
        ordered=True,
    )
    df_out3 = (
        df_out3
        .sort_values(["ano", "categoria_tamanho_estabelecimento"])
        .reset_index(drop=True)
    )
    df_out3.to_csv(OUT3, **CSV_PARAMS)

    # ── Resumo ────
    print("\n" + "=" * 70)
    print(f"Processamento concluído. Arquivos gerados em: {OUT_DIR.resolve()}")
    print(f"  1) {OUT1.name}")
    print(f"  2) {OUT2.name}")
    print(f"  3) {OUT3.name}")
    print("=" * 70)


if __name__ == "__main__":
    main()