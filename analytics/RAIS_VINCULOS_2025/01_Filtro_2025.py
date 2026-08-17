from __future__ import annotations

from pathlib import Path
import csv
import pandas as pd
import numpy as np


# ====
# CONFIG
# ====
PASTA_2025 = Path(r"E:\Rais\Vinculos\2025")

ARQUIVOS_2025 = [
    "RAIS_VINC_ID_CENTRO_OESTE_2025.COMT",
    "RAIS_VINC_ID_MG_ES_RJ_2025.COMT",
    "RAIS_VINC_ID_NORDESTE_2025.COMT",
    "RAIS_VINC_ID_NORTE_2025.COMT",
    "RAIS_VINC_ID_SP_2025.COMT",
    "RAIS_VINC_ID_SUL_2025.COMT",
]

# Output
OUTPUT_DIR = Path(r"E:\Rais\DF5_DF6\data")
OUTPUT_CSV = OUTPUT_DIR / "rais_2025_filtrado.csv"

# Padrão Brasil
CSV_SEP = ";"
CSV_DECIMAL = ","
CSV_ENCODING = "utf-8-sig"

CHUNK_SIZE = 300_000

# Rode primeiro em True; quando OK, mude para False para gerar o CSV completo
MODO_VALIDACAO = False

# Progresso
PRINT_PROGRESso = True
PROGRESS_EVERY_N_CHUNKS = 1  # 1 = imprime todo chunk; 5 = imprime a cada 5 chunks


# ====
# DEFLATOR (base 2024)
# ====
INFLACAO = {
    2025: 4.26,
}


def fator_deflator(ano_origem: int, ano_base: int = 2024) -> float:
    """Traz valores nominais do ano_origem para preços do ano_base."""
    if ano_origem == ano_base:
        return 1.0
    fator = 1.0
    if ano_origem < ano_base:
        for t in range(ano_origem + 1, ano_base + 1):
            fator *= (1.0 + INFLACAO[t] / 100.0)
    else:
        for t in range(ano_base + 1, ano_origem + 1):
            fator /= (1.0 + INFLACAO[t] / 100.0)
    return fator


FATOR_2025 = fator_deflator(2025, 2024)


# ====
# COLUNAS CANÔNICAS (nomes de 2024)
# ====
COL_CBO = "CBO 2002 Ocupação - Código"
COL_CNAE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_2025 = "CNAE 2.0 Subclasse - Codigo"  # typo introduzido em 2025
COL_ESCOL = "Escolaridade Após 2005 - Código"
COL_DEFIC = "Ind Portador Defic - Código"
COL_INTERM = "Ind Trabalho Intermitente - Código"
COL_ATIVO = "Ind Vínculo Ativo 31/12 - Código"
COL_MUN = "Município - Código"
COL_NATJUR = "Natureza Jurídica - Código"
COL_RACA = "Raça Cor - Código"
COL_SEXO = "Sexo - Código"
COL_TAMESTAB = "Tamanho Estabelecimento - Código"
COL_IDADE = "Idade"
COL_REM_MEDIA = "Vl Rem Média Nom"
COL_REM_DEZ = "Vl Rem Dezembro Nom"

# Colunas mensais 2025 (Jan-Nov SC + Dez Nom)
MESES_2025 = [
    "Vl Rem Janeiro SC",
    "Vl Rem Fevereiro SC",
    "Vl Rem Março SC",
    "Vl Rem Abril SC",
    "Vl Rem Maio SC",
    "Vl Rem Junho SC",
    "Vl Rem Julho SC",
    "Vl Rem Agosto SC",
    "Vl Rem Setembro SC",
    "Vl Rem Outubro SC",
    "Vl Rem Novembro SC",
    COL_REM_DEZ,  # dezembro entra na soma e depois é excluído
]

# Colunas finais no CSV (ordem fixa; sem meses; sem dezembro; sem ativo)
COLS_FINAIS = [
    COL_CBO,
    COL_CNAE,
    COL_ESCOL,
    COL_DEFIC,
    COL_INTERM,
    COL_MUN,
    COL_NATJUR,
    COL_RACA,
    COL_SEXO,
    COL_TAMESTAB,
    COL_IDADE,
    COL_REM_MEDIA,
    "massa_salarial",
    "meses_com_salario",
    "massa_salarial_deflacionada_2024",
    "vl_rem_media_nom_deflacionada_2024",
    "ano",
]


# ====
# UTIL
# ====
def to_num_brl(s: pd.Series) -> pd.Series:
    """Converte strings BR ('1.234,56') ou simples ('1234.56') para float."""
    x = s.astype(str).str.strip().replace({"": np.nan, "nan": np.nan, "None": np.nan})
    has_comma = x.str.contains(",", na=False)
    x = x.where(
        ~has_comma,
        x.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
    )
    return pd.to_numeric(x, errors="coerce")


def normalizar_cnae_classe(s: pd.Series) -> pd.Series:
    """
    Normaliza CNAE para CLASSE (5 dígitos).

    Regras:
    - 7 dígitos: pega os 5 primeiros
    - 6 dígitos: zfill(7) e pega os 5 primeiros
    - 5 dígitos (classe): mantém
    - 4 dígitos: zfill(5) (raro)
    - demais: NA
    """
    x = (
        s.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
    )

    tam = x.str.len()
    out = pd.Series(pd.NA, index=x.index, dtype="string")

    out = out.mask(tam == 7, x.str[:5])
    out = out.mask(tam == 6, x.str.zfill(7).str[:5])
    out = out.mask(tam == 5, x)
    out = out.mask(tam == 4, x.str.zfill(5))

    return out


def escrever_csv_append(df: pd.DataFrame, output_path: Path, primeiro: bool) -> None:
    df.to_csv(
        output_path,
        sep=CSV_SEP,
        decimal=CSV_DECIMAL,
        encoding=CSV_ENCODING,
        index=False,
        mode="w" if primeiro else "a",
        header=primeiro,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )


def log_progresso(prefixo: str, arq: str, chunk_idx: int, lidas: int, ativas: int, escritas: int, total: int) -> None:
    if not PRINT_PROGRESso:
        return
    if (chunk_idx % PROGRESS_EVERY_N_CHUNKS) != 0:
        return
    print(
        f"[{prefixo}] {arq} | chunk {chunk_idx} | lidas={lidas:,} | ativas={ativas:,} | escritas={escritas:,} | total={total:,}"
    )


def transformar_chunk(chunk: pd.DataFrame, meses: list[str], fator: float, ano: int) -> pd.DataFrame:
    """
    Aplica as transformações:
    - filtra ativos
    - CNAE: subclasse(7) -> classe(5); lida com 6/5 também
    - massa_salarial = soma 12 meses (inclui dezembro)
    - cria deflacionadas (base 2024)
    - adiciona ano
    - remove ativo + meses (inclui dezembro)
    """
    # 1) filtro vínculo ativo
    chunk = chunk[chunk[COL_ATIVO].astype(str).str.strip() == "1"].copy()
    if chunk.empty:
        return chunk

    # 2) CNAE: normalizar para classe (5 dígitos) de forma robusta
    chunk[COL_CNAE] = normalizar_cnae_classe(chunk[COL_CNAE])

    # 3) converter numéricos (meses + média)
    for c in meses + [COL_REM_MEDIA]:
        chunk[c] = to_num_brl(chunk[c])

    # 4) massa salarial
    chunk["massa_salarial"] = chunk[meses].sum(axis=1, skipna=True)

    # 4.1) meses_com_salario: conta meses com valor > 0 (NaNs e zeros não contam)
    chunk["meses_com_salario"] = chunk[meses].gt(0).sum(axis=1)

    # 5) deflacionados (base 2024)
    chunk["massa_salarial_deflacionada_2024"] = chunk["massa_salarial"] * fator
    chunk["vl_rem_media_nom_deflacionada_2024"] = chunk[COL_REM_MEDIA] * fator

    # 6) ano
    chunk["ano"] = ano

    # 7) excluir ativo + meses (inclui dezembro)
    chunk = chunk.drop(columns=[COL_ATIVO] + meses, errors="ignore")

    # 8) selecionar finais
    return chunk[COLS_FINAIS]


# ====
# PROCESSADOR
# ====
def processar_2025(output_path: Path, primeiro: bool, total_escrito: int) -> tuple[bool, int]:
    params = dict(sep=",", encoding="latin1")

    required = [
        COL_CBO,
        COL_CNAE,
        COL_ESCOL,
        COL_DEFIC,
        COL_INTERM,
        COL_ATIVO,
        COL_MUN,
        COL_NATJUR,
        COL_RACA,
        COL_SEXO,
        COL_TAMESTAB,
        COL_IDADE,
        COL_REM_MEDIA,
    ] + MESES_2025

    for nome in ARQUIVOS_2025:
        arq = PASTA_2025 / nome
        if not arq.exists():
            raise FileNotFoundError(f"Não encontrei: {arq}")

        # Validação tolerante ao typo de 2025
        cols_arq = list(pd.read_csv(arq, sep=",", encoding="latin1", nrows=0).columns)
        cols_norm = [COL_CNAE if c == COL_CNAE_2025 else c for c in cols_arq]
        falt = [c for c in required if c not in cols_norm]
        if falt:
            raise ValueError(f"Colunas faltantes em {arq.name}: {falt}")

        if PRINT_PROGRESso and not MODO_VALIDACAO:
            print(f"\n[2025] Iniciando arquivo: {arq.name}")

        # usecols tolerante: aceita COL_CNAE_2025 se COL_CNAE não existir
        usecols_raw = [COL_CNAE_2025 if c == COL_CNAE and COL_CNAE not in cols_arq else c for c in required]

        reader = pd.read_csv(
            arq,
            **params,
            usecols=usecols_raw,
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
            on_bad_lines="skip",
        )

        for i, chunk in enumerate(reader, start=1):
            lidas = len(chunk)

            for c in chunk.columns:
                chunk[c] = chunk[c].astype(str).str.strip()

            # Normaliza nome da coluna CNAE se vier com typo
            if COL_CNAE_2025 in chunk.columns:
                chunk = chunk.rename(columns={COL_CNAE_2025: COL_CNAE})

            ativas = int((chunk[COL_ATIVO] == "1").sum())

            out = transformar_chunk(chunk, MESES_2025, FATOR_2025, 2025)
            escritas = len(out)

            if out.empty:
                log_progresso("2025", arq.name, i, lidas, ativas, 0, total_escrito)
                continue

            if MODO_VALIDACAO:
                print(f"[VALIDAÇÃO 2025] {arq.name} | chunk {i} | linhas ativas: {escritas:,}")
                print("Colunas:", out.columns.tolist())
                print(out.head(3).to_string())
                return primeiro, total_escrito

            escrever_csv_append(out, output_path, primeiro)
            primeiro = False
            total_escrito += escritas
            log_progresso("2025", arq.name, i, lidas, ativas, escritas, total_escrito)

    return primeiro, total_escrito


# ====
# MAIN
# ====
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_CSV.exists() and not MODO_VALIDACAO:
        raise FileExistsError(
            f"'{OUTPUT_CSV}' já existe. Apague ou renomeie antes de rodar."
        )

    print(f"Deflator 2025 -> 2024 : {FATOR_2025:.6f}")
    print(f"MODO_VALIDACAO        : {MODO_VALIDACAO}")
    print(f"Saída                 : {OUTPUT_CSV}")
    print(f"Formato CSV           : sep='{CSV_SEP}' | decimal='{CSV_DECIMAL}' | encoding='{CSV_ENCODING}'")
    if not MODO_VALIDACAO:
        print(f"Progresso             : a cada {PROGRESS_EVERY_N_CHUNKS} chunk(s)")
    print()

    primeiro = True
    total_escrito = 0

    primeiro, total_escrito = processar_2025(OUTPUT_CSV, primeiro, total_escrito)

    if MODO_VALIDACAO:
        print("\n[OK] Validação OK. Mude MODO_VALIDACAO = False e rode novamente para gerar o CSV completo.")
    else:
        print(f"\n[OK] CSV gerado: {OUTPUT_CSV}")
        print(f"[OK] Total de linhas escritas: {total_escrito:,}")


if __name__ == "__main__":
    main()