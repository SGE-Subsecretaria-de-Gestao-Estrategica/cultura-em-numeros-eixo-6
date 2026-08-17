"""
01_caged_metricas_grupos.py
====
Extrai métricas mensais de fluxo salarial do CAGED por:

1) Grupos nacionais de CNAE:
   - Brasil (todos os setores)
   - Cultura (CNAEs em E:\\Rais\\Rais\\Auxiliares\\CNAE-ibge.xlsx, col. CNAE_IBGE)
   - Agricultura, pecuária, produção florestal, pesca e aquicultura
   - Indústria extrativa
   - Construção

2) Recortes adicionais — apenas Total e Cultura:
   - UF
   - Capitais

Métricas por "grupo" × competência (ano + mês)
----
  movimentacoes_liquidas  : saldo líquido de movimentações (admissões - desligamentos)
  fluxo_salarial_nom      : soma de (salário × saldo_mov) — nominal
  fluxo_salarial_def      : fluxo salarial deflacionado para preços de dez/2024
  salario_medio_adm_nom   : salário médio das admissões (saldo_mov = +1) — nominal
  salario_medio_adm_def   : idem, deflacionado para dez/2024

Fontes por período
----
  2016–2019 : CAGED Legado — CAGEDEST_MMAAAA.txt (um arquivo por mês)
  2020–2026 : Novo CAGED   — CAGEDMOV, CAGEDFOR, CAGEDEXC (três arquivos por mês)
              EXC inverte o sinal: fluxo = salário × (−saldo_mov)

Deflação
----
  Base: dezembro de 2024 (fator = 1,0)
  Fonte: E:\\Rais\\CAGED\\Ipca\\ipca_202605SerieHist.xlsx
  Colunas esperadas: ano (ex: 2024), mes (ex: DEZ), ipca (ex: 0,43)
  O fator mensal acumula o IPCA de cada mês entre a competência e dez/2024.

Saída
----
  E:\\Rais\\CAGED\\data\\caged_metricas_grupos_2016_2026_salario1M.csv
  sep=';' | decimal=',' | encoding='utf-8-sig'

Requisitos
----
  pip install pandas openpyxl
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


# ====
# CONFIGURAÇÃO
# ====

PASTA_CAGED     = Path(r"E:\Rais\CAGED")
PASTA_AUX       = Path(r"E:\Rais\Rais\Auxiliares")
PASTA_OUTPUT    = Path(r"E:\Rais\CAGED\data")

CNAE_IBGE_XLSX  = PASTA_AUX / "CNAE-ibge.xlsx"
CNAE_IBGE_COL   = "CNAE_IBGE"

ARQUIVO_IPCA    = PASTA_CAGED / "Ipca" / "IPCA_mensal.xls"

OUTPUT_CSV      = PASTA_OUTPUT / "caged_metricas_grupos_2016_2026_salario1M.csv"
CSV_SEP         = ";"
CSV_DECIMAL     = ","
CSV_ENCODING    = "utf-8-sig"

CHUNK_SIZE      = 300_000

# Rode em True para inspecionar apenas o primeiro chunk e encerrar
MODO_VALIDACAO  = False

# Filtro de salário: registros com salário ACIMA deste valor são excluídos
# do fluxo salarial (mas ainda contam para movimentacoes_liquidas)
SALARIO_MAXIMO  = 1_000_000

# Competência-base para deflação e normalização: dezembro de 2024
ANO_BASE        = 2024
MES_BASE        = 12

# Anos a processar
ANOS            = list(range(2024, 2027))  # 2024 a 2026 inclusive


# ====
# MAPA DE MESES (abreviatura → número)
# ====

_MES_ABREV = {
    "JAN": 1,  "FEV": 2,  "MAR": 3,  "ABR": 4,
    "MAI": 5,  "JUN": 6,  "JUL": 7,  "AGO": 8,
    "SET": 9,  "OUT": 10, "NOV": 11, "DEZ": 12,
}


# ====
# DEFLAÇÃO MENSAL
# ====

def _carregar_ipca(caminho: Path) -> dict[tuple[int, int], float]:
    """
    Lê o arquivo de IPCA (.xls ou .xlsx) e retorna
    {(ano, mes): taxa}.

    A função detecta automaticamente a extensão do arquivo.
    """

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo IPCA não encontrado: {caminho}")

    # Escolhe o engine conforme a extensão
    if caminho.suffix.lower() == ".xls":
        df = pd.read_excel(caminho, dtype=str, engine="xlrd")
    else:
        df = pd.read_excel(caminho, dtype=str)

    # Normaliza nomes das colunas
    df.columns = [_canon_colname(c) for c in df.columns]

    col_ano = _resolver_col_flex(df.columns.tolist(), ["ano"])
    col_mes = _resolver_col_flex(df.columns.tolist(), ["mes", "mês"])
    col_ipca = _resolver_col_flex(df.columns.tolist(), ["ipca"])

    df["_ano"] = pd.to_numeric(df[col_ano], errors="coerce").astype("Int64")

    # Mês pode vir como número ou abreviação
    mes = df[col_mes].astype(str).str.strip().str.upper()

    if mes.str.fullmatch(r"\d+").all():
        df["_mes"] = pd.to_numeric(mes, errors="coerce").astype("Int64")
    else:
        df["_mes"] = mes.map(_MES_ABREV)

    taxa = (
        df[col_ipca]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["_taxa"] = pd.to_numeric(taxa, errors="coerce")

    df = df.dropna(subset=["_ano", "_mes", "_taxa"])

    return {
        (int(r["_ano"]), int(r["_mes"])): float(r["_taxa"])
        for _, r in df.iterrows()
    }


def _construir_fatores_mensais(
    ipca: dict[tuple[int, int], float],
    anos: list[int],
    ano_base: int = ANO_BASE,
    mes_base: int = MES_BASE,
) -> dict[tuple[int, int], float]:
    """
    Para cada (ano, mês) calcula o fator multiplicador que traz valores
    nominais daquela competência a preços de (ano_base, mes_base).

    Fórmula:
      - Se competência == base: fator = 1,0
      - Se competência < base : acumula (1 + ipca/100) de cada mês
                    entre competência+1 e base (inclusive)
      - Se competência > base : divide pelo acumulado de base+1 até competência
    """
    # Gera lista ordenada de todas as competências (ano, mês)
    todas = sorted(
        {(a, m) for a in anos for m in range(1, 13)},
        key=lambda x: x[0] * 100 + x[1],
    )

    base_idx = (ano_base, mes_base)
    fatores: dict[tuple[int, int], float] = {}

    for comp in todas:
        if comp == base_idx:
            fatores[comp] = 1.0
            continue

        # Determina direção
        comp_num = comp[0] * 100 + comp[1]
        base_num = ano_base * 100 + mes_base

        fator = 1.0

        if comp_num < base_num:
            # Acumula do mês seguinte à competência até o mês-base
            cur = comp
            while True:
                prox = _proximo_mes(cur)
                taxa = ipca.get(prox, None)
                if taxa is None:
                    # Sem dado de IPCA: mantém fator atual (aviso emitido depois)
                    break
                fator *= 1.0 + taxa / 100.0
                if prox == base_idx:
                    break
                cur = prox
        else:
            # Divide pelo acumulado do mês seguinte à base até a competência
            cur = base_idx
            while True:
                prox = _proximo_mes(cur)
                taxa = ipca.get(prox, None)
                if taxa is None:
                    break
                fator /= 1.0 + taxa / 100.0
                if prox == comp:
                    break
                cur = prox

        fatores[comp] = fator

    return fatores


def _proximo_mes(comp: tuple[int, int]) -> tuple[int, int]:
    ano, mes = comp
    if mes == 12:
        return (ano + 1, 1)
    return (ano, mes + 1)


# ====
# UF / CAPITAIS
# ====

UF_MAP = {
    "11": "Rondônia",
    "12": "Acre",
    "13": "Amazonas",
    "14": "Roraima",
    "15": "Pará",
    "16": "Amapá",
    "17": "Tocantins",
    "21": "Maranhão",
    "22": "Piauí",
    "23": "Ceará",
    "24": "Rio Grande do Norte",
    "25": "Paraíba",
    "26": "Pernambuco",
    "27": "Alagoas",
    "28": "Sergipe",
    "29": "Bahia",
    "31": "Minas Gerais",
    "32": "Espírito Santo",
    "33": "Rio de Janeiro",
    "35": "São Paulo",
    "41": "Paraná",
    "42": "Santa Catarina",
    "43": "Rio Grande do Sul",
    "50": "Mato Grosso do Sul",
    "51": "Mato Grosso",
    "52": "Goiás",
    "53": "Distrito Federal",
}

CAPITAIS = {
    "280030": "Aracaju",
    "150140": "Belém",
    "310620": "Belo Horizonte",
    "140010": "Boa Vista",
    "530010": "Brasília",
    "500270": "Campo Grande",
    "510340": "Cuiabá",
    "410690": "Curitiba",
    "420540": "Florianópolis",
    "230440": "Fortaleza",
    "520870": "Goiânia",
    "250750": "João Pessoa",
    "160030": "Macapá",
    "270430": "Maceió",
    "130260": "Manaus",
    "240810": "Natal",
    "172100": "Palmas",
    "431490": "Porto Alegre",
    "110020": "Porto Velho",
    "261160": "Recife",
    "120040": "Rio Branco",
    "330455": "Rio de Janeiro",
    "292740": "Salvador",
    "211130": "São Luís",
    "355030": "São Paulo",
    "221100": "Teresina",
    "320530": "Vitória",
}


def _normalizar_mun_cod(series: pd.Series) -> pd.Series:
    s = (
        series.astype("string")
        .str.strip()
        .str.replace(r"\D", "", regex=True)
        .str.zfill(6)
    )
    s = s.mask(s.str.len() != 6, pd.NA)
    s = s.mask(s == "0000", pd.NA)
    return s


def _extrair_uf_nome(mun_cod6: pd.Series) -> pd.Series:
    return mun_cod6.str[:2].map(UF_MAP)


def _extrair_capital_nome(mun_cod6: pd.Series) -> pd.Series:
    return mun_cod6.map(CAPITAIS)


# ====
# UTILITÁRIOS DE COLUNAS
# ====

def _canon_colname(s: str) -> str:
    """Remove acentos, strip, lower, colapsa espaços."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s.strip().lower())


def _resolver_col_flex(cols: list[str], candidatos: list[str]) -> str:
    """
    Resolve nome real de coluna de forma accent-insensitive.
    Tenta cada candidato (já em forma canônica) contra o mapa canônico das colunas.
    """
    canon_map = {_canon_colname(c): c for c in cols}
    for cand in candidatos:
        key = _canon_colname(cand)
        if key in canon_map:
            return canon_map[key]
    raise ValueError(
        f"Nenhuma das colunas candidatas encontrada: {candidatos}. "
        f"Colunas disponíveis: {cols[:40]}"
    )


def _to_float_br(series: pd.Series) -> pd.Series:
    """
    Converte coluna string para float.
    Trata tanto formato BR (vírgula decimal) quanto ponto decimal.
    """
    x = series.astype(str).str.strip()
    x = x.replace({"": np.nan, "nan": np.nan, "None": np.nan, "NaN": np.nan})
    # Se contém vírgula, assume BR
    tem_virgula = x.str.contains(",", na=False)
    x_br  = x.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    x_out = x.copy()
    x_out[tem_virgula]  = x_br[tem_virgula]
    return pd.to_numeric(x_out, errors="coerce").fillna(0.0)


def _normalizar_cnae7(series: pd.Series) -> pd.Series:
    """Normaliza CNAE para string de 7 dígitos (subclasse)."""
    x = (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
    )
    return x.where(x.str.len() == 7, pd.NA)


def _cnae7_para_5(cnae7: pd.Series) -> pd.Series:
    """Extrai os 5 primeiros dígitos (classe) do CNAE subclasse."""
    return cnae7.str[:5]


# ====
# GRUPOS DE CNAE
# ====

def _carregar_cnaes_cultura() -> set[str]:
    if not CNAE_IBGE_XLSX.exists():
        raise FileNotFoundError(f"Arquivo auxiliar não encontrado: {CNAE_IBGE_XLSX}")
    df = pd.read_excel(CNAE_IBGE_XLSX, dtype=str)
    if CNAE_IBGE_COL not in df.columns:
        raise ValueError(
            f"Coluna '{CNAE_IBGE_COL}' não encontrada em {CNAE_IBGE_XLSX.name}. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )
    codigos = (
        df[CNAE_IBGE_COL]
        .dropna()
        .astype(str)
        .str.strip()
        .str.replace(r"\D", "", regex=True)
    )
    # Normaliza para 5 dígitos (classe)
    codigos = codigos[codigos.str.len().between(5, 7)]
    codigos = codigos.apply(
        lambda v: v[:5] if len(v) == 7 else (v.zfill(7)[:5] if len(v) == 6 else v)
    )
    return set(codigos.unique())


_PREFIXOS_GRUPOS = {
    "Agricultura, pecuária, produção florestal, pesca e aquicultura": ("01", "02", "03"),
    "Indústria extrativa": ("05", "06", "07", "08", "09"),
    "Construção": ("41", "42", "43"),
}


def _classificar_grupos(cnae5: pd.Series, cnaes_cultura: set[str]) -> pd.DataFrame:
    flags = pd.DataFrame(index=cnae5.index)
    flags["Brasil"]  = True
    flags["Cultura"] = cnae5.isin(cnaes_cultura)
    for nome, prefixos in _PREFIXOS_GRUPOS.items():
        flags[nome] = cnae5.str.startswith(prefixos, na=False)
    return flags


# ====
# ACUMULADOR DE MÉTRICAS
# ====

class AcumuladorMetricas:
    """
    Acumula métricas de fluxo salarial por (grupo, ano, mês).

    Campos acumulados:
      movimentacoes_liquidas : saldo líquido de TODAS as movimentações (sem filtro de salário)
      soma_fluxo_nom         : soma de (salário × saldo_mov) — apenas registros com
                               salário <= SALARIO_MAXIMO (nominal)
      cont_adm               : contagem de admissões (saldo_mov = +1) com
                               0 < salário <= SALARIO_MAXIMO
      soma_sal_adm_nom       : soma dos salários das admissões filtradas (para média)
    """

    def __init__(self):
        self._acc: dict[tuple[str, int, int], dict] = {}

    def _get(self, grupo: str, ano: int, mes: int) -> dict:
        key = (grupo, ano, mes)
        if key not in self._acc:
            self._acc[key] = {
                "movimentacoes_liquidas": 0,
                "soma_fluxo_nom":         0.0,
                "cont_adm":               0,
                "soma_sal_adm_nom":       0.0,
            }
        return self._acc[key]

    def atualizar(
        self,
        grupo: str,
        ano: int,
        mes: int,
        saldo_mov: pd.Series,
        salario: pd.Series,
    ) -> None:
        if saldo_mov.empty:
            return

        acc = self._get(grupo, ano, mes)

        # movimentacoes_liquidas: conta TODOS os registros (independente do salário)
        acc["movimentacoes_liquidas"] += int(saldo_mov.sum())

        # Fluxo salarial: apenas registros com salário <= SALARIO_MAXIMO
        mask_sal_valido = salario <= SALARIO_MAXIMO
        salario_filtrado = salario[mask_sal_valido]
        saldo_filtrado   = saldo_mov[mask_sal_valido]

        acc["soma_fluxo_nom"] += float((salario_filtrado * saldo_filtrado).sum())

        # Salário médio de admissão: apenas admissões com 0 < salário <= SALARIO_MAXIMO
        mask_adm = (saldo_filtrado == 1) & (salario_filtrado > 0)
        acc["cont_adm"]         += int(mask_adm.sum())
        acc["soma_sal_adm_nom"] += float(salario_filtrado[mask_adm].sum())

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for (grupo, ano, mes), acc in self._acc.items():
            denom = acc["cont_adm"]
            rows.append({
                "grupo":                  grupo,
                "ano":                    ano,
                "mes":                    mes,
                "competencia":            ano * 100 + mes,
                "movimentacoes_liquidas": acc["movimentacoes_liquidas"],
                "fluxo_salarial_nom":     round(acc["soma_fluxo_nom"], 2),
                "salario_medio_adm_nom":  round(acc["soma_sal_adm_nom"] / denom, 2) if denom > 0 else np.nan,
            })
        return pd.DataFrame(rows)


# ====
# LAYOUT DOS ARQUIVOS
# ====

def _layout_legado() -> dict:
    """Layout do CAGED Legado (2016–2019)."""
    return {
        "tipo":       "legado",
        "sep":        ";",
        "encoding":   "latin1",
        "col_cnae":   "CNAE 2.0 Subclas",
        "col_mun":    "Município",
        "col_saldo":  "Saldo Mov",
        "col_sal":    "Salário Mensal",
        "sinal_exc":  False,
    }


def _layout_novo() -> dict:
    """Layout do Novo CAGED (2020–2026) — MOV e FOR."""
    return {
        "tipo":       "novo",
        "sep":        ";",
        "encoding":   "utf-8",
        "col_cnae":   "subclasse",
        "col_mun":    "município",
        "col_saldo":  "saldomovimentação",
        "col_sal":    "salário",
        "sinal_exc":  False,
    }


def _layout_exc() -> dict:
    """Layout do Novo CAGED — EXC (sinal invertido)."""
    layout = _layout_novo()
    layout["sinal_exc"] = True
    return layout


# ====
# LISTAGEM DE ARQUIVOS
# ====

def _listar_competencias_legado(ano: int) -> list[tuple[int, int, Path]]:
    """Retorna lista de (ano, mês, caminho) para o período legado."""
    pasta = PASTA_CAGED / str(ano)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta}")

    resultado = []
    for arq in sorted(pasta.glob("CAGEDEST_*.txt")):
        # Nome: CAGEDEST_MMAAAA.txt
        stem = arq.stem  # ex: CAGEDEST_012019
        partes = stem.split("_")
        if len(partes) < 2 or len(partes[-1]) != 6:
            continue
        mmaaaa = partes[-1]
        try:
            mes_arq = int(mmaaaa[:2])
            ano_arq = int(mmaaaa[2:])
        except ValueError:
            continue
        if ano_arq == ano:
            resultado.append((ano_arq, mes_arq, arq))

    return sorted(resultado, key=lambda x: x[1])


def _listar_competencias_novo(ano: int) -> list[tuple[int, int, dict[str, Path]]]:
    """
    Retorna lista de (ano, mês, {MOV: path, FOR: path, EXC: path})
    para o período do Novo CAGED.
    """
    pasta_ano = PASTA_CAGED / str(ano)
    if not pasta_ano.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta_ano}")

    resultado = []
    for subpasta in sorted(pasta_ano.iterdir()):
        if not subpasta.is_dir() or len(subpasta.name) != 6:
            continue
        try:
            aaaamm = int(subpasta.name)
            ano_sub = aaaamm // 100
            mes_sub = aaaamm % 100
        except ValueError:
            continue
        if ano_sub != ano:
            continue

        arquivos = {}
        for tipo in ["MOV", "FOR", "EXC"]:
            candidatos = list(subpasta.glob(f"CAGED{tipo}{subpasta.name}.txt"))
            if candidatos:
                arquivos[tipo] = candidatos[0]
            else:
                # Tenta glob mais amplo (case-insensitive em alguns sistemas)
                candidatos = list(subpasta.glob(f"CAGED{tipo}*.txt"))
                if candidatos:
                    arquivos[tipo] = candidatos[0]

        if arquivos:
            resultado.append((ano_sub, mes_sub, arquivos))

    return sorted(resultado, key=lambda x: x[1])


# ====
# LEITURA E NORMALIZAÇÃO DE CHUNK
# ====

def _ler_chunk_normalizado(
    arq: Path,
    layout: dict,
    cnaes_cultura: set[str],
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Lê o arquivo em chunks e retorna iterador de tuplas:
      (cnae5, mun_cod6, saldo_mov, salario, flags_df)

    Retorna um gerador para uso com chunksize.
    """
    # Lê cabeçalho para resolver nomes reais das colunas
    try:
        header = pd.read_csv(
            arq,
            sep=layout["sep"],
            encoding=layout["encoding"],
            nrows=0,
        )
    except UnicodeDecodeError:
        # Fallback de encoding
        enc_fallback = "latin1" if layout["encoding"] == "utf-8" else "utf-8"
        header = pd.read_csv(
            arq,
            sep=layout["sep"],
            encoding=enc_fallback,
            nrows=0,
        )
        layout = {**layout, "encoding": enc_fallback}

    cols_reais = header.columns.tolist()

    col_cnae  = _resolver_col_flex(cols_reais, [layout["col_cnae"], "subclasse", "CNAE 2.0 Subclas"])
    col_mun   = _resolver_col_flex(cols_reais, [layout["col_mun"],  "município", "Município"])
    col_saldo = _resolver_col_flex(cols_reais, [layout["col_saldo"], "saldomovimentação", "Saldo Mov"])
    col_sal   = _resolver_col_flex(cols_reais, [layout["col_sal"],   "salário", "Salário Mensal"])

    usecols = list({col_cnae, col_mun, col_saldo, col_sal})

    reader = pd.read_csv(
        arq,
        sep=layout["sep"],
        encoding=layout["encoding"],
        usecols=usecols,
        dtype=str,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        on_bad_lines="skip",
    )

    return reader, col_cnae, col_mun, col_saldo, col_sal, layout


# ====
# ACUMULAÇÃO POR CHAVE GEOGRÁFICA
# ====

def _acumular_por_chave(
    acumulador: AcumuladorMetricas,
    chave: pd.Series,
    ano: int,
    mes: int,
    saldo_mov: pd.Series,
    salario: pd.Series,
    prefixo: str,
    escopo: str,
) -> None:
    df = pd.DataFrame({
        "chave":   chave.astype("string"),
        "saldo":   saldo_mov.astype(float),
        "salario": salario.astype(float),
    }).dropna(subset=["chave"])

    if df.empty:
        return

    for k, grp in df.groupby("chave"):
        grupo_nome = f"{prefixo} - {k} - {escopo}"
        acumulador.atualizar(
            grupo=grupo_nome,
            ano=ano,
            mes=mes,
            saldo_mov=grp["saldo"],
            salario=grp["salario"],
        )


# ====
# PROCESSAMENTO DE UM ARQUIVO
# ====

def _processar_arquivo(
    arq: Path,
    layout: dict,
    ano: int,
    mes: int,
    acumulador: AcumuladorMetricas,
    cnaes_cultura: set[str],
    label: str,
) -> None:
    print(f"    [{label}] {arq.name}")

    reader, col_cnae, col_mun, col_saldo, col_sal, layout = _ler_chunk_normalizado(
        arq, layout, cnaes_cultura
    )

    for i, chunk in enumerate(reader, start=1):
        n_lidas = len(chunk)

        for col in chunk.columns:
            chunk[col] = chunk[col].astype(str).str.strip()

        # Saldo de movimentação
        saldo_raw = pd.to_numeric(chunk[col_saldo], errors="coerce").fillna(0).astype(int)

        # Inverte sinal para exclusões
        if layout["sinal_exc"]:
            saldo_raw = -saldo_raw

        # Filtra apenas movimentações com saldo ≠ 0
        mask_valido = saldo_raw != 0
        if not mask_valido.any():
            print(f"      chunk {i:>3} | lidas={n_lidas:,} | válidas=0")
            continue

        chunk    = chunk[mask_valido].copy()
        saldo    = saldo_raw[mask_valido]
        n_valido = len(chunk)

        # CNAE normalizado
        cnae7 = _normalizar_cnae7(chunk[col_cnae])
        cnae5 = _cnae7_para_5(cnae7)

        # Salário
        salario = _to_float_br(chunk[col_sal])

        # Município
        mun_cod6 = _normalizar_mun_cod(chunk[col_mun])
        uf_nome  = _extrair_uf_nome(mun_cod6)
        cap_nome = _extrair_capital_nome(mun_cod6)

        # Flags de grupo
        flags = _classificar_grupos(cnae5, cnaes_cultura)

        # 1) Grupos nacionais
        for grupo in flags.columns:
            mask = flags[grupo]
            if not mask.any():
                continue
            acumulador.atualizar(
                grupo=grupo,
                ano=ano,
                mes=mes,
                saldo_mov=saldo[mask],
                salario=salario[mask],
            )

        # 2) UF — Total
        _acumular_por_chave(acumulador, uf_nome, ano, mes, saldo, salario, "UF", "Total")

        # 3) UF — Cultura
        mask_cult = flags["Cultura"]
        _acumular_por_chave(
            acumulador, uf_nome[mask_cult], ano, mes,
            saldo[mask_cult], salario[mask_cult], "UF", "Cultura"
        )

        # 4) Capital — Total
        _acumular_por_chave(acumulador, cap_nome, ano, mes, saldo, salario, "Capital", "Total")

        # 5) Capital — Cultura
        _acumular_por_chave(
            acumulador, cap_nome[mask_cult], ano, mes,
            saldo[mask_cult], salario[mask_cult], "Capital", "Cultura"
        )

        print(f"      chunk {i:>3} | lidas={n_lidas:,} | válidas={n_valido:,}")

        if MODO_VALIDACAO:
            print("\n  [VALIDAÇÃO] Amostra do chunk:")
            print(f"    CNAE5 amostra  : {cnae5.head(5).tolist()}")
            print(f"    Saldo amostra  : {saldo.head(5).tolist()}")
            print(f"    Salário amostra: {salario.head(5).tolist()}")
            print(f"    UF amostra     : {uf_nome.head(5).tolist()}")
            print(f"    Capital amostra: {cap_nome.head(5).tolist()}")
            return


# ====
# PROCESSAMENTO POR ANO
# ====

def processar_ano_legado(
    ano: int,
    acumulador: AcumuladorMetricas,
    cnaes_cultura: set[str],
) -> None:
    competencias = _listar_competencias_legado(ano)
    if not competencias:
        print(f"  [AVISO] Nenhum arquivo legado encontrado para {ano}.")
        return

    layout = _layout_legado()

    for ano_arq, mes, arq in competencias:
        print(f"\n  [{ano_arq}/{mes:02d}] LEGADO")
        _processar_arquivo(arq, layout, ano_arq, mes, acumulador, cnaes_cultura, "EST")

        if MODO_VALIDACAO:
            return


def processar_ano_novo(
    ano: int,
    acumulador: AcumuladorMetricas,
    cnaes_cultura: set[str],
) -> None:
    competencias = _listar_competencias_novo(ano)
    if not competencias:
        print(f"  [AVISO] Nenhuma subpasta encontrada para {ano}.")
        return

    for ano_sub, mes, arquivos in competencias:
        print(f"\n  [{ano_sub}/{mes:02d}] NOVO CAGED")

        for tipo, layout_fn in [("MOV", _layout_novo), ("FOR", _layout_novo), ("EXC", _layout_exc)]:
            if tipo not in arquivos:
                print(f"    [{tipo}] não encontrado — competência {ano_sub}{mes:02d}")
                continue
            _processar_arquivo(
                arquivos[tipo], layout_fn(), ano_sub, mes,
                acumulador, cnaes_cultura, tipo
            )

        if MODO_VALIDACAO:
            return


# ====
# APLICAÇÃO DOS FATORES DE DEFLAÇÃO
# ====

def _aplicar_deflacao(
    df: pd.DataFrame,
    fatores: dict[tuple[int, int], float],
) -> pd.DataFrame:
    """
    Adiciona colunas deflacionadas ao DataFrame de métricas.
    Emite aviso para competências sem fator disponível.
    """
    df["_fator"] = df.apply(
        lambda r: fatores.get((int(r["ano"]), int(r["mes"])), None), axis=1
    )

    sem_fator = df[df["_fator"].isna()]["competencia"].unique()
    if len(sem_fator) > 0:
        print(
            f"\n[AVISO] {len(sem_fator)} competência(s) sem fator de deflação "
            f"(IPCA ausente). Será usado fator=1 nesses casos: {sorted(sem_fator)[:10]}"
        )
        df["_fator"] = df["_fator"].fillna(1.0)

    df["fluxo_salarial_def"]     = (df["fluxo_salarial_nom"]    * df["_fator"]).round(2)
    df["salario_medio_adm_def"]  = (df["salario_medio_adm_nom"] * df["_fator"]).round(2)

    return df.drop(columns=["_fator"])


# ====
# ORDENAÇÃO FINAL
# ====

def _ordenar(df: pd.DataFrame) -> pd.DataFrame:
    ordem_grupos_base = [
        "Brasil",
        "Cultura",
        "Agricultura, pecuária, produção florestal, pesca e aquicultura",
        "Indústria extrativa",
        "Construção",
    ]
    base_rank = {g: i for i, g in enumerate(ordem_grupos_base)}

    def _rank(grupo: str) -> tuple:
        if grupo in base_rank:
            return (0, base_rank[grupo], grupo)
        if grupo.startswith("UF - "):
            return (1, 0, grupo)
        if grupo.startswith("Capital - "):
            return (2, 0, grupo)
        return (9, 0, grupo)

    df["__rank"] = df["grupo"].map(_rank)
    df = (
        df.sort_values(["__rank", "ano", "mes"])
        .drop(columns="__rank")
        .reset_index(drop=True)
    )
    return df


# ====
# MAIN
# ====

def main() -> None:
    print("=" * 70)
    print("CAGED — Métricas de Fluxo Salarial por Grupo (2016–2026)")
    print("=" * 70)
    print(f"Saída          : {OUTPUT_CSV}")
    print(f"Modo validação : {MODO_VALIDACAO}")
    print(f"Filtro salarial: salário <= R$ {SALARIO_MAXIMO:,.0f} (apenas para fluxo salarial)")
    print()

    PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Carrega IPCA e constrói fatores mensais
    print(f"Carregando IPCA: {ARQUIVO_IPCA.name} ...")
    ipca = _carregar_ipca(ARQUIVO_IPCA)
    print(f"  {len(ipca)} registros mensais de IPCA carregados.")

    fatores = _construir_fatores_mensais(ipca, ANOS)
    print(f"  {len(fatores)} fatores mensais de deflação calculados (base: dez/{ANO_BASE}).")

    # Carrega CNAEs de cultura
    print(f"\nCarregando CNAEs de cultura: {CNAE_IBGE_XLSX.name} ...")
    cnaes_cultura = _carregar_cnaes_cultura()
    print(f"  {len(cnaes_cultura)} códigos de CNAE (5 dígitos) carregados.")

    acumulador = AcumuladorMetricas()

    for ano in ANOS:
        print(f"\n{'=' * 70}")
        print(f"ANO: {ano}")
        print(f"{'=' * 70}")

        try:
            if ano <= 2019:
                processar_ano_legado(ano, acumulador, cnaes_cultura)
            else:
                processar_ano_novo(ano, acumulador, cnaes_cultura)
        except FileNotFoundError as e:
            print(f"  [AVISO] {e} — ano {ano} ignorado.")
            continue

        if MODO_VALIDACAO:
            print("\n[OK] Validação concluída. Mude MODO_VALIDACAO = False para rodar completo.")
            return

    print("\nConsolidando resultados...")
    df = acumulador.to_dataframe()

    # Aplica deflação
    print("Aplicando deflação mensal...")
    df = _aplicar_deflacao(df, fatores)

    # Ordena
    df = _ordenar(df)

    # Reordena colunas
    colunas_saida = [
        "grupo", "ano", "mes", "competencia",
        "movimentacoes_liquidas",
        "fluxo_salarial_nom",
        "fluxo_salarial_def",
        "salario_medio_adm_nom",
        "salario_medio_adm_def",
    ]
    df = df[colunas_saida]

    # Salva
    df.to_csv(
        OUTPUT_CSV,
        sep=CSV_SEP,
        decimal=CSV_DECIMAL,
        encoding=CSV_ENCODING,
        index=False,
    )

    print(f"\n[OK] CSV gerado: {OUTPUT_CSV}")
    print(f"[OK] Linhas no output: {len(df):,}")
    print("\nPreview (primeiras 30 linhas):")
    print(df.head(30).to_string(index=False))


if __name__ == "__main__":
    main()