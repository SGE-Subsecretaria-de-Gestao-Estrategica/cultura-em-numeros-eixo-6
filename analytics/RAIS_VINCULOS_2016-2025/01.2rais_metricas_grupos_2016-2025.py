"""
rais_metricas_grupos.py
====
Extrai métricas agregadas da RAIS Vínculos 2016–2025 por:

1) Grupo de CNAE:
  - Brasil
  - Cultura (CNAEs em E:\\Rais\\Rais\\Auxiliares\\CNAE-ibge.xlsx, col. CNAE_IBGE)
  - Agricultura...
  - Indústria extrativa
  - Construção

2) Recortes adicionais — apenas Total e Cultura:
  - UF (derivada do município IBGE: 2 primeiros dígitos)
  - Capitais (municípios IBGE das capitais)

Métricas por "grupo" × ano
----
  total_vinculos          : contagem de linhas (vínculos ativos)
  massa_salarial_nom      : soma Jan–Nov + Dezembro (nominal)
  massa_salarial_def      : massa deflacionada para preços de 2024
  media_nom               : média da remuneração média (nominal), calculada APENAS onde remuneração média nominal > 0
  media_def               : idem, deflacionada para 2024

Saída
----
  E:\\Rais\\DF1\\rais_metricas_grupos_2016_2025.csv
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

PASTA_BASE      = Path(r"E:\Rais\Vinculos")
PASTA_AUX       = Path(r"E:\Rais\Rais\Auxiliares")
PASTA_OUTPUT    = Path(r"E:\Rais\DF1")

CNAE_IBGE_XLSX  = PASTA_AUX / "CNAE-ibge.xlsx"
CNAE_IBGE_COL   = "CNAE_IBGE"

OUTPUT_CSV      = PASTA_OUTPUT / "rais_metricas_grupos_2016_2025.csv"
CSV_SEP         = ";"
CSV_DECIMAL     = ","
CSV_ENCODING    = "utf-8-sig"

CHUNK_SIZE      = 300_000

# Rode em True para inspecionar 1 chunk antes de processar tudo
MODO_VALIDACAO  = False

ANOS            = list(range(2016, 2026))   # 2016 a 2025 inclusive


# ====
# DEFLATOR  (base 2024 = 1,0)
# Inflação anual % (IPCA anual fornecida)
# ====

_INFLACAO_ANUAL = {
    2015: 7.60,
    2016: 8.10,
    2017: 3.70,
    2018: 4.49,
    2019: 4.22,
    2020: 6.47,
    2021: 13.05,
    2022: 8.57,
    2023: 5.16,
    2024: 4.08,
    2025: 4.26,
}


def _calcular_fator(ano_origem: int) -> float:
    """
    Fator multiplicador para trazer valores nominais de `ano_origem` a preços de 2024.
    - Anos anteriores a 2024: acumula inflação até 2024 (fator > 1).
    - 2024: fator = 1,0 (ano-base).
    - Anos posteriores a 2024: deflaciona dividindo pela inflação acumulada (fator < 1).
    """
    if ano_origem == 2024:
        return 1.0
    if ano_origem < 2024:
        fator = 1.0
        for t in range(ano_origem + 1, 2025):
            fator *= 1.0 + _INFLACAO_ANUAL[t] / 100.0
        return fator
    # anos após 2024: divide pela inflação acumulada desde 2025 até ano_origem
    fator = 1.0
    for t in range(2025, ano_origem + 1):
        fator /= (1.0 + _INFLACAO_ANUAL[t] / 100.0)
    return fator


FATORES_DEFLACAO: dict[int, float] = {ano: _calcular_fator(ano) for ano in ANOS}


# ====
# UF / CAPITAIS
# ====

UF_MAP = {
    "52": "Goiás",
    "31": "Minas Gerais",
    "15": "Pará",
    "23": "Ceará",
    "29": "Bahia",
    "41": "Paraná",
    "42": "Santa Catarina",
    "26": "Pernambuco",
    "17": "Tocantins",
    "21": "Maranhão",
    "24": "Rio Grande do Norte",
    "22": "Piauí",
    "43": "Rio Grande do Sul",
    "51": "Mato Grosso",
    "12": "Acre",
    "35": "São Paulo",
    "32": "Espírito Santo",
    "25": "Paraíba",
    "27": "Alagoas",
    "50": "Mato Grosso do Sul",
    "11": "Rondônia",
    "14": "Roraima",
    "13": "Amazonas",
    "16": "Amapá",
    "28": "Sergipe",
    "33": "Rio de Janeiro",
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
    """
    Normaliza código de município para string de 6 dígitos (IBGE).
    Mantém só dígitos e faz zfill(6).
    """
    s = (
        series.astype("string")
        .str.strip()
        .str.replace(r"\D", "", regex=True)
        .str.zfill(6)
    )
    s = s.mask(s == "0000", pd.NA)
    return s


def _extrair_uf_nome(mun_cod6: pd.Series) -> pd.Series:
    uf_cod = mun_cod6.str[:2]
    return uf_cod.map(UF_MAP)


def _extrair_capital_nome(mun_cod6: pd.Series) -> pd.Series:
    return mun_cod6.map(CAPITAIS)


# ====
# RESOLUÇÃO DE COLUNAS (accent-insensitive)
# ====

def _canon_colname(s: str) -> str:
    """Remove acentos, strip, lower, colapsa espaços — para comparação robusta."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s.strip().lower())


def _resolver_coluna_municipio(cols_arquivo: list[str], col_mun_preferida: str) -> str:
    if col_mun_preferida in cols_arquivo:
        return col_mun_preferida

    alternativas = ["Município - Código", "Município"]
    for alt in alternativas:
        if alt in cols_arquivo:
            return alt

    raise ValueError(
        "Não encontrei coluna de município no arquivo. "
        f"Tentei: {[col_mun_preferida] + alternativas} | "
        f"Colunas disponíveis (amostra): {cols_arquivo[:30]}"
    )


def _resolver_coluna_cnae(cols_arquivo: list[str], col_cnae_preferida: str) -> str:
    """
    Resolve o nome real da coluna CNAE Subclasse no arquivo,
    de forma accent-insensitive (ex: 'Codigo' vs 'Código').
    """
    canon_map = {_canon_colname(c): c for c in cols_arquivo}

    # 1) preferida (canônico)
    if _canon_colname(col_cnae_preferida) in canon_map:
        return canon_map[_canon_colname(col_cnae_preferida)]

    # 2) alternativas conhecidas (canônico)
    alternativas = [
        "CNAE 2.0 Subclasse - Código",
        "CNAE 2.0 Subclasse - Codigo",
        "CNAE 2.0 Subclasse",
    ]
    for alt in alternativas:
        if _canon_colname(alt) in canon_map:
            return canon_map[_canon_colname(alt)]

    # 3) heurística: única coluna com "cnae" + "subclasse"
    candidatos = [
        c for c in cols_arquivo
        if "cnae" in _canon_colname(c) and "subclasse" in _canon_colname(c)
    ]
    if len(candidatos) == 1:
        return candidatos[0]

    cols_cnae = [c for c in cols_arquivo if "cnae" in _canon_colname(c)]
    raise ValueError(
        "Não encontrei (ou encontrei mais de uma) coluna de CNAE/Subclasse no arquivo. "
        f"Preferida: '{col_cnae_preferida}'. "
        f"Candidatos subclasse: {candidatos}. "
        f"Colunas com 'CNAE' (amostra): {cols_cnae[:30]}"
    )


# ====
# LAYOUT POR ANO
# ====

_MESES_NOMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro",
]


def _colunas_mensais(sufixo: str) -> list[str]:
    return [f"Vl Rem {m} {sufixo}" for m in _MESES_NOMES]


def _layout(ano: int) -> dict:
    """
    Períodos, adicionando coluna de município:
      - <=2022: município costuma vir como "Município"
      - >=2023: município vem como "Município - Código"
    """
    if ano <= 2019:
        sufixo_mes   = "CC"
        sep          = ";"
        decimal      = ","
        col_ativo    = "Vínculo Ativo 31/12"
        col_cnae     = "CNAE 2.0 Subclasse"
        col_media    = "Vl Remun Média Nom"
        col_dezembro = "Vl Remun Dezembro Nom"
        col_mun      = "Município"
    elif ano <= 2022:
        sufixo_mes   = "SC"
        sep          = ";"
        decimal      = ","
        col_ativo    = "Vínculo Ativo 31/12"
        col_cnae     = "CNAE 2.0 Subclasse"
        col_media    = "Vl Remun Média Nom"
        col_dezembro = "Vl Remun Dezembro Nom"
        col_mun      = "Município"
    else:  # 2023–2025
        sufixo_mes   = "SC"
        sep          = ","
        decimal      = "."
        col_ativo    = "Ind Vínculo Ativo 31/12 - Código"
        col_cnae     = "CNAE 2.0 Subclasse - Código"
        col_media    = "Vl Rem Média Nom"
        col_dezembro = "Vl Rem Dezembro Nom"
        col_mun      = "Município - Código"

    meses = _colunas_mensais(sufixo_mes)

    return {
        "sep":          sep,
        "decimal":      decimal,
        "col_ativo":    col_ativo,
        "col_cnae":     col_cnae,
        "col_media":    col_media,
        "col_dezembro": col_dezembro,
        "col_mun":      col_mun,
        "meses":        meses,
    }


def _listar_arquivos(ano: int) -> list[Path]:
    pasta = PASTA_BASE / str(ano)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta}")

    if ano <= 2017:
        arquivos = sorted(pasta.glob(f"*{ano}ID*"))
    else:
        ext = ".COMT" if ano >= 2023 else ".txt"
        arquivos = sorted(pasta.glob(f"RAIS_VINC_ID_*{ext}"))

    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em {pasta} para o ano {ano}.")

    return arquivos


# ====
# UTILITÁRIOS
# ====

def _to_float(series: pd.Series, decimal: str) -> pd.Series:
    """Converte coluna string para float, tratando decimal ',' ou '.'."""
    x = series.astype(str).str.strip()
    x = x.replace({"": np.nan, "nan": np.nan, "None": np.nan, "NaN": np.nan})
    if decimal == ",":
        x = x.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(x, errors="coerce").fillna(0.0)


def _normalizar_cnae5(series: pd.Series) -> pd.Series:
    """
    Normaliza CNAE para 5 dígitos (classe).
    """
    x = (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
    )
    tam = x.str.len()
    out = pd.Series(pd.NA, index=x.index, dtype="string")
    out = out.mask(tam == 7, x.str[:5])
    out = out.mask(tam == 6, x.str.zfill(7).str[:5])
    out = out.mask(tam == 5, x)
    return out


# ====
# GRUPOS DE CNAE
# ====

def _carregar_cnaes_cultura() -> set[str]:
    """Lê CNAE-ibge.xlsx e retorna conjunto de códigos de 5 dígitos."""
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
    codigos = codigos[codigos.str.len().between(5, 7)]
    codigos = codigos.apply(
        lambda v: v.zfill(7)[:5] if len(v) == 6 else (v[:5] if len(v) == 7 else v)
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
    Acumula somas e contagens por (grupo, ano) de forma incremental.

    Regra importante:
      - total_vinculos: conta TODOS os vínculos ativos (não muda)
      - soma_media_* e cont_media_pos: acumulam APENAS vínculos com media_nom > 0
        (denominador da média NÃO é total_vinculos)
    """

    def __init__(self):
        self._acc: dict[tuple[str, int], dict] = {}

    def _get(self, grupo: str, ano: int) -> dict:
        key = (grupo, ano)
        if key not in self._acc:
            self._acc[key] = {
                "total_vinculos":     0,
                "soma_massa_nom":     0.0,
                "soma_massa_def":     0.0,
                "cont_media_pos":     0,
                "soma_media_nom_pos": 0.0,
                "soma_media_def_pos": 0.0,
            }
        return self._acc[key]

    def atualizar_flags(
        self,
        flags: pd.DataFrame,
        massa_nom: pd.Series,
        media_nom: pd.Series,
        fator: float,
        ano: int,
    ) -> None:
        massa_def = massa_nom * fator
        media_def = media_nom * fator

        media_pos_mask_global = media_nom.gt(0)

        for grupo in flags.columns:
            mask_total = flags[grupo]
            if not mask_total.any():
                continue

            acc = self._get(grupo, ano)

            # total_vinculos: TODOS os vínculos ativos no grupo
            n_total = int(mask_total.sum())
            acc["total_vinculos"] += n_total

            # massa: sem mudança (usa todos os vínculos do grupo)
            acc["soma_massa_nom"] += float(massa_nom[mask_total].sum())
            acc["soma_massa_def"] += float(massa_def[mask_total].sum())

            # média: somente vínculos com media_nom > 0
            mask_media = mask_total & media_pos_mask_global
            n_media = int(mask_media.sum())
            if n_media > 0:
                acc["cont_media_pos"] += n_media
                acc["soma_media_nom_pos"] += float(media_nom[mask_media].sum())
                acc["soma_media_def_pos"] += float(media_def[mask_media].sum())

    def atualizar_agregado(
        self,
        grupo: str,
        ano: int,
        total_vinculos: int,
        soma_massa_nom: float,
        cont_media_pos: int,
        soma_media_nom_pos: float,
        fator: float,
    ) -> None:
        if total_vinculos <= 0:
            return

        acc = self._get(grupo, ano)

        acc["total_vinculos"] += int(total_vinculos)
        acc["soma_massa_nom"] += float(soma_massa_nom)
        acc["soma_massa_def"] += float(soma_massa_nom * fator)

        if cont_media_pos > 0:
            acc["cont_media_pos"] += int(cont_media_pos)
            acc["soma_media_nom_pos"] += float(soma_media_nom_pos)
            acc["soma_media_def_pos"] += float(soma_media_nom_pos * fator)

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for (grupo, ano), acc in self._acc.items():
            denom = acc["cont_media_pos"]
            rows.append({
                "grupo":              grupo,
                "ano":                ano,
                "total_vinculos":     acc["total_vinculos"],
                "massa_salarial_nom": round(acc["soma_massa_nom"], 2),
                "massa_salarial_def": round(acc["soma_massa_def"], 2),
                "media_nom":          round(acc["soma_media_nom_pos"] / denom, 2) if denom > 0 else np.nan,
                "media_def":          round(acc["soma_media_def_pos"] / denom, 2) if denom > 0 else np.nan,
            })
        return pd.DataFrame(rows)


# ====
# PROCESSAMENTO POR ANO
# ====

def _acumular_por_chave(
    acumulador: AcumuladorMetricas,
    chave: pd.Series,            # ex: UF nome ou Capital nome
    ano: int,
    massa_nom: pd.Series,
    media_nom: pd.Series,
    fator: float,
    prefixo_grupo: str,          # "UF" ou "Capital"
    escopo: str,                 # "Total" ou "Cultura"
) -> None:
    df = pd.DataFrame({
        "chave": chave.astype("string"),
        "massa": massa_nom.astype(float),
        "media": media_nom.astype(float),
    }).dropna(subset=["chave"])

    if df.empty:
        return

    # total_vinculos e massa: todos
    counts_total = df.groupby("chave").size()
    soma_massa = df.groupby("chave")["massa"].sum()

    # média: só media > 0
    df_media = df[df["media"] > 0]
    if df_media.empty:
        counts_media = pd.Series(dtype="int64")
        soma_media = pd.Series(dtype="float64")
    else:
        counts_media = df_media.groupby("chave").size()
        soma_media = df_media.groupby("chave")["media"].sum()

    for k in counts_total.index:
        grupo_nome = f"{prefixo_grupo} - {k} - {escopo}"
        acumulador.atualizar_agregado(
            grupo=grupo_nome,
            ano=ano,
            total_vinculos=int(counts_total.loc[k]),
            soma_massa_nom=float(soma_massa.loc[k]),
            cont_media_pos=int(counts_media.loc[k]) if k in counts_media.index else 0,
            soma_media_nom_pos=float(soma_media.loc[k]) if k in soma_media.index else 0.0,
            fator=fator,
        )


def processar_ano(
    ano: int,
    acumulador: AcumuladorMetricas,
    cnaes_cultura: set[str],
) -> None:
    layout   = _layout(ano)
    arquivos = _listar_arquivos(ano)
    fator    = FATORES_DEFLACAO[ano]

    print(
        f"\n[{ano}] {len(arquivos)} arquivo(s) | sep='{layout['sep']}' | "
        f"decimal='{layout['decimal']}' | fator_deflacao={fator:.6f}"
    )

    for arq in arquivos:
        print(f"  -> {arq.name}")

        # Lê cabeçalho para resolver colunas de município e CNAE
        cols_arquivo = list(
            pd.read_csv(arq, sep=layout["sep"], encoding="latin1", nrows=0).columns
        )

        col_mun  = _resolver_coluna_municipio(cols_arquivo, layout["col_mun"])
        col_cnae = _resolver_coluna_cnae(cols_arquivo, layout["col_cnae"])

        usecols = [
            layout["col_ativo"], col_cnae, layout["col_media"],
            layout["col_dezembro"], col_mun
        ] + layout["meses"]

        faltantes = [c for c in usecols if c not in cols_arquivo]
        if faltantes:
            cols_cnae_disp = [c for c in cols_arquivo if "cnae" in _canon_colname(c)]
            raise ValueError(
                f"Colunas faltantes em {arq.name} (ano {ano}): {faltantes}\n"
                f"Colunas com 'CNAE' disponíveis: {cols_cnae_disp}\n"
                f"Dica: confira o separador/arquivo e o layout desse ano."
            )

        reader = pd.read_csv(
            arq,
            sep=layout["sep"],
            encoding="latin1",
            usecols=usecols,
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
            on_bad_lines="skip",
        )

        for i, chunk in enumerate(reader, start=1):
            lidas_brutas = len(chunk)

            # Strip em todas as colunas
            for col in chunk.columns:
                chunk[col] = chunk[col].astype(str).str.strip()

            # Filtro: vínculo ativo
            ativo_mask = chunk[layout["col_ativo"]].astype(str).str.strip() == "1"
            chunk = chunk[ativo_mask].copy()
            ativas = len(chunk)
            if chunk.empty:
                print(f"     chunk {i:>3} | lidas={lidas_brutas:,} | ativas=0")
                continue

            # CNAE normalizado — usa col_cnae (nome real do arquivo)
            cnae5 = _normalizar_cnae5(chunk[col_cnae])

            # Remunerações numéricas
            dec = layout["decimal"]
            meses_num = chunk[layout["meses"]].apply(lambda s: _to_float(s, dec))
            dez_num   = _to_float(chunk[layout["col_dezembro"]], dec)
            media_num = _to_float(chunk[layout["col_media"]], dec)

            # Massa salarial = Jan–Nov + Dezembro
            massa_nom = meses_num.sum(axis=1) + dez_num

            # Flags dos grupos originais
            flags = _classificar_grupos(cnae5, cnaes_cultura)

            # 1) Grupos originais
            acumulador.atualizar_flags(flags, massa_nom, media_num, fator, ano)

            # 2) UF e Capital (apenas Total e Cultura)
            mun_cod6 = _normalizar_mun_cod(chunk[col_mun])
            uf_nome  = _extrair_uf_nome(mun_cod6)
            cap_nome = _extrair_capital_nome(mun_cod6)

            # Total por UF
            _acumular_por_chave(
                acumulador=acumulador,
                chave=uf_nome,
                ano=ano,
                massa_nom=massa_nom,
                media_nom=media_num,
                fator=fator,
                prefixo_grupo="UF",
                escopo="Total",
            )
            # Cultura por UF
            _acumular_por_chave(
                acumulador=acumulador,
                chave=uf_nome[flags["Cultura"]],
                ano=ano,
                massa_nom=massa_nom[flags["Cultura"]],
                media_nom=media_num[flags["Cultura"]],
                fator=fator,
                prefixo_grupo="UF",
                escopo="Cultura",
            )

            # Total por Capital
            _acumular_por_chave(
                acumulador=acumulador,
                chave=cap_nome,
                ano=ano,
                massa_nom=massa_nom,
                media_nom=media_num,
                fator=fator,
                prefixo_grupo="Capital",
                escopo="Total",
            )
            # Cultura por Capital
            _acumular_por_chave(
                acumulador=acumulador,
                chave=cap_nome[flags["Cultura"]],
                ano=ano,
                massa_nom=massa_nom[flags["Cultura"]],
                media_nom=media_num[flags["Cultura"]],
                fator=fator,
                prefixo_grupo="Capital",
                escopo="Cultura",
            )

            print(f"     chunk {i:>3} | lidas={lidas_brutas:,} | ativas={ativas:,}")

            if MODO_VALIDACAO:
                print("\n[VALIDAÇÃO] Amostra do chunk processado:")
                print(f"  CNAE5 amostra   : {cnae5.head(5).tolist()}")
                print(f"  col_cnae usada  : {col_cnae}")
                print(f"  UF amostra      : {uf_nome.head(5).tolist()}")
                print(f"  Capital amostra : {cap_nome.head(5).tolist()}")
                print(f"  Massa nom       : {massa_nom.head(5).tolist()}")
                print(f"  Média nom       : {media_num.head(5).tolist()}")
                print(f"  Qtde média > 0  : {int(media_num.gt(0).sum())}")
                print(f"  Flags (5 linhas):\n{flags.head(5).to_string()}")
                return


# ====
# MAIN
# ====

def main() -> None:
    print("=" * 70)
    print("RAIS Vínculos — Métricas por Grupo + (UF/Capitais p/ Total e Cultura) (2016–2025)")
    print("=" * 70)
    print(f"Saída          : {OUTPUT_CSV}")
    print(f"Modo validação : {MODO_VALIDACAO}")
    print()

    PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Fatores de deflação
    print("Fatores de deflação (base 2024):")
    for ano, f in FATORES_DEFLACAO.items():
        print(f"  {ano}: {f:.6f}")
    print()

    # Carrega CNAEs de cultura
    print(f"Carregando CNAEs de cultura: {CNAE_IBGE_XLSX.name} ...")
    cnaes_cultura = _carregar_cnaes_cultura()
    print(f"  {len(cnaes_cultura)} códigos de CNAE (5 dígitos) carregados.")

    acumulador = AcumuladorMetricas()

    for ano in ANOS:
        try:
            processar_ano(ano, acumulador, cnaes_cultura)
        except FileNotFoundError as e:
            print(f"  [AVISO] {e} — ano {ano} ignorado.")
            continue

        if MODO_VALIDACAO:
            print("\n[OK] Validação concluída. Mude MODO_VALIDACAO = False para rodar completo.")
            return

    print("\nConsolidando resultados...")
    df_resultado = acumulador.to_dataframe()

    # Ordenação (mantém grupos originais no topo)
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

    df_resultado["__rank"] = df_resultado["grupo"].astype(str).map(_rank)
    df_resultado = df_resultado.sort_values(["__rank", "ano"]).drop(columns="__rank").reset_index(drop=True)

    df_resultado.to_csv(
        OUTPUT_CSV,
        sep=CSV_SEP,
        decimal=CSV_DECIMAL,
        encoding=CSV_ENCODING,
        index=False,
    )

    print(f"\n[OK] CSV gerado: {OUTPUT_CSV}")
    print(f"[OK] Linhas no output: {len(df_resultado)}")
    print("\nPreview do resultado (primeiras 60 linhas):")
    print(df_resultado.head(60).to_string(index=False))


if __name__ == "__main__":
    main()
