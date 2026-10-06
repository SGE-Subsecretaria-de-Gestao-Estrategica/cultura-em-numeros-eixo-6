from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_BASE = Path(
    r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
)
ARQUIVO_CNAE_CRIATIVA = Path(
    r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx"
)
ARQUIVO_MUNICIPIOS = Path(
    r"E:\Rais\Rais\Auxiliares\municipios.xlsx"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.18.csv")

CHUNK_SIZE = 300_000
CASAS_DECIMAIS_NOMINAL = 3

COL_CNAE_BASE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"
COL_MUN_BASE = "Município - Código"

COL_COD_MUN_AUX = "Cod_Município"
COL_MUNICIPIO_AUX = "Município"
COL_COD_UF_AUX = "Cod_UF"
COL_MACRORREGIAO_AUX = "Macrorregiões"
COL_SIGLA_MACRORREGIAO_AUX = "Abrev_Macrorregiões"
COL_ESTADO_AUX = "Estado"


# Prefixo IBGE -> sigla da UF.
SIGLAS_UF_POR_PREFIXO = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


# Chave municipal RAIS de 6 dígitos -> código IBGE de 7 dígitos,
# nome da capital e UF.
CAPITAIS = {
    "280030": ("2800308", "Aracaju", "SE"),
    "150140": ("1501402", "Belém", "PA"),
    "310620": ("3106200", "Belo Horizonte", "MG"),
    "140010": ("1400100", "Boa Vista", "RR"),
    "530010": ("5300108", "Brasília", "DF"),
    "500270": ("5002704", "Campo Grande", "MS"),
    "510340": ("5103403", "Cuiabá", "MT"),
    "410690": ("4106902", "Curitiba", "PR"),
    "420540": ("4205407", "Florianópolis", "SC"),
    "230440": ("2304400", "Fortaleza", "CE"),
    "520870": ("5208707", "Goiânia", "GO"),
    "250750": ("2507507", "João Pessoa", "PB"),
    "160030": ("1600303", "Macapá", "AP"),
    "270430": ("2704302", "Maceió", "AL"),
    "130260": ("1302603", "Manaus", "AM"),
    "240810": ("2408102", "Natal", "RN"),
    "172100": ("1721000", "Palmas", "TO"),
    "431490": ("4314902", "Porto Alegre", "RS"),
    "110020": ("1100205", "Porto Velho", "RO"),
    "261160": ("2611606", "Recife", "PE"),
    "120040": ("1200401", "Rio Branco", "AC"),
    "330455": ("3304557", "Rio de Janeiro", "RJ"),
    "292740": ("2927408", "Salvador", "BA"),
    "211130": ("2111300", "São Luís", "MA"),
    "355030": ("3550308", "São Paulo", "SP"),
    "221100": ("2211001", "Teresina", "PI"),
    "320530": ("3205309", "Vitória", "ES"),
}


# ====
# FUNCOES AUXILIARES
# ====

def validar_colunas(
    dataframe: pd.DataFrame,
    colunas: list[str],
    caminho: Path,
) -> None:
    ausentes = [coluna for coluna in colunas if coluna not in dataframe.columns]

    if ausentes:
        raise KeyError(
            f"Colunas ausentes em {caminho}: {ausentes}. "
            f"Colunas disponíveis: {list(dataframe.columns)}"
        )


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Normaliza códigos CNAE para sete dígitos."""
    codigos = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos.str.zfill(7)


def normalizar_codigo_municipio(valor) -> str | None:
    """
    Normaliza o código municipal da RAIS para seis dígitos.
    Códigos com sete dígitos têm o dígito verificador removido.
    """
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    if texto.endswith(".0"):
        texto = texto[:-2]

    digitos = "".join(caractere for caractere in texto if caractere.isdigit())

    if len(digitos) == 7:
        return digitos[:6]

    if len(digitos) == 6:
        return digitos

    if len(digitos) == 5:
        return digitos.zfill(6)

    return None


def normalizar_codigo_municipio_aux(serie: pd.Series) -> pd.Series:
    """Normaliza o código da tabela municipal para extrair o prefixo da UF."""
    codigos = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos


def converter_decimal(valor) -> Decimal | None:
    """Converte números com ponto ou vírgula decimal para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "")

    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    return numero if numero.is_finite() else None


def truncar_casas(valor: Decimal, casas: int) -> Decimal:
    """Trunca casas decimais excedentes, sem arredondar."""
    fator = Decimal(1).scaleb(-casas)

    with localcontext() as contexto:
        contexto.prec = 50
        return valor.quantize(fator, rounding=ROUND_DOWN)


def formatar_decimal(valor: Decimal | None) -> str:
    """Formata o decimal com ponto e sem zeros finais desnecessários."""
    if valor is None:
        return ""

    texto = format(valor, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


def primeiro_valor_preenchido(serie: pd.Series) -> str:
    """Retorna o primeiro valor não vazio da série."""
    for valor in serie:
        if pd.notna(valor):
            texto = str(valor).strip()
            if texto:
                return texto
    return ""


def carregar_metadados_uf() -> dict[str, dict[str, str]]:
    """
    Carrega os campos descritivos por UF.

    A tabela é reduzida a uma linha por prefixo estadual, evitando
    a junção por código municipal, que pode ter chaves duplicadas.
    """
    municipios = pd.read_excel(ARQUIVO_MUNICIPIOS, dtype=str)
    municipios.columns = [
        str(coluna).replace("\ufeff", "").strip()
        for coluna in municipios.columns
    ]

    colunas_necessarias = [
        COL_COD_MUN_AUX,
        COL_COD_UF_AUX,
        COL_MACRORREGIAO_AUX,
        COL_SIGLA_MACRORREGIAO_AUX,
        COL_ESTADO_AUX,
    ]
    validar_colunas(municipios, colunas_necessarias, ARQUIVO_MUNICIPIOS)

    codigos = normalizar_codigo_municipio_aux(
        municipios[COL_COD_MUN_AUX]
    )
    municipios["prefixo_uf"] = codigos.str[:2]

    municipios = municipios.loc[
        municipios["prefixo_uf"].isin(SIGLAS_UF_POR_PREFIXO)
    ].copy()

    metadados = {}

    for prefixo, grupo in municipios.groupby("prefixo_uf", sort=False):
        metadados[prefixo] = {
            "codigo_uf": primeiro_valor_preenchido(
                grupo[COL_COD_UF_AUX]
            ),
            "macrorregiao": primeiro_valor_preenchido(
                grupo[COL_MACRORREGIAO_AUX]
            ),
            "sigla_macrorregiao": primeiro_valor_preenchido(
                grupo[COL_SIGLA_MACRORREGIAO_AUX]
            ),
            "estado": primeiro_valor_preenchido(
                grupo[COL_ESTADO_AUX]
            ),
        }

    return metadados


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    for caminho in (
        ARQUIVO_BASE,
        ARQUIVO_CNAE_CRIATIVA,
        ARQUIVO_MUNICIPIOS,
    ):
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df_cnae = pd.read_excel(
        ARQUIVO_CNAE_CRIATIVA,
        usecols=[COL_CNAE_AUX],
        dtype=str,
    )
    cnaes_criativos = set(
        normalizar_cnae(df_cnae[COL_CNAE_AUX]).dropna()
    )

    if not cnaes_criativos:
        raise ValueError(
            f"Nenhum CNAE válido encontrado em {ARQUIVO_CNAE_CRIATIVA}."
        )

    metadados_uf = carregar_metadados_uf()

    # Acumuladores para capitais: soma salarial e quantidade de registros.
    soma_por_capital = {
        chave: Decimal("0") for chave in CAPITAIS
    }
    qtd_por_capital = {
        chave: 0 for chave in CAPITAIS
    }

    # Acumuladores por UF: incluem os registros válidos de todos os municípios.
    soma_por_uf = {
        prefixo: Decimal("0") for prefixo in SIGLAS_UF_POR_PREFIXO
    }
    qtd_por_uf = {
        prefixo: 0 for prefixo in SIGLAS_UF_POR_PREFIXO
    }

    print(f"CNAEs da Economia Criativa carregados: {len(cnaes_criativos):,}")
    print(f"Processando a base em chunks de {CHUNK_SIZE:,} linhas...")

    leitor = pd.read_csv(
        ARQUIVO_BASE,
        sep=";",
        encoding="utf-8-sig",
        usecols=[
            COL_MUN_BASE,
            COL_CNAE_BASE,
            COL_SALARIO,
        ],
        dtype=str,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for numero_chunk, chunk in enumerate(leitor, start=1):
        mascara_cnae = normalizar_cnae(
            chunk[COL_CNAE_BASE]
        ).isin(cnaes_criativos)
        chunk = chunk.loc[mascara_cnae].copy()

        if chunk.empty:
            print(f"  Chunk {numero_chunk}: nenhum registro de EC.")
            continue

        chunk["codigo_municipio_base"] = chunk[COL_MUN_BASE].map(
            normalizar_codigo_municipio
        )
        chunk = chunk.loc[
            chunk["codigo_municipio_base"].notna()
        ].copy()

        if chunk.empty:
            print(
                f"  Chunk {numero_chunk}: nenhum código municipal válido."
            )
            continue

        chunk["prefixo_uf"] = chunk["codigo_municipio_base"].str[:2]
        chunk = chunk.loc[
            chunk["prefixo_uf"].isin(SIGLAS_UF_POR_PREFIXO)
        ].copy()

        if chunk.empty:
            print(f"  Chunk {numero_chunk}: nenhum código de UF reconhecido.")
            continue

        for codigo_municipio, prefixo_uf, valor_salario in zip(
            chunk["codigo_municipio_base"],
            chunk["prefixo_uf"],
            chunk[COL_SALARIO],
        ):
            salario = converter_decimal(valor_salario)

            if salario is None or salario <= 0:
                continue

            # Mantém o dado agregado por UF.
            soma_por_uf[prefixo_uf] += salario
            qtd_por_uf[prefixo_uf] += 1

            # Mantém também os dados das capitais.
            if codigo_municipio in CAPITAIS:
                soma_por_capital[codigo_municipio] += salario
                qtd_por_capital[codigo_municipio] += 1

        print(f"  Chunk {numero_chunk} processado.")

    registros = []

    # Linhas por capital.
    for chave, (codigo_ibge, nome_capital, uf) in CAPITAIS.items():
        quantidade = qtd_por_capital[chave]

        if quantidade == 0:
            continue

        with localcontext() as contexto:
            contexto.prec = 50
            media = soma_por_capital[chave] / Decimal(quantidade)

        media = truncar_casas(media, CASAS_DECIMAIS_NOMINAL)
        prefixo_uf = chave[:2]
        metadados = metadados_uf.get(prefixo_uf, {})

        registros.append(
            {
                "tipo_recorte": "capital",
                "codigo_municipio": codigo_ibge,
                "nome_municipio": nome_capital,
                "uf": uf,
                "codigo_uf": metadados.get("codigo_uf", ""),
                "macrorregiao": metadados.get("macrorregiao", ""),
                "sigla_macrorregiao": metadados.get(
                    "sigla_macrorregiao", ""
                ),
                "estado": metadados.get("estado", ""),
                "media_salarial_deflacionada_2024": formatar_decimal(media),
                "num_salarios_validos": quantidade,
            }
        )

    # Linhas agregadas por UF, calculadas usando todos os municípios da UF.
    for prefixo_uf, uf in SIGLAS_UF_POR_PREFIXO.items():
        quantidade = qtd_por_uf[prefixo_uf]

        if quantidade == 0:
            continue

        with localcontext() as contexto:
            contexto.prec = 50
            media = soma_por_uf[prefixo_uf] / Decimal(quantidade)

        media = truncar_casas(media, CASAS_DECIMAIS_NOMINAL)
        metadados = metadados_uf.get(prefixo_uf, {})

        registros.append(
            {
                "tipo_recorte": "uf",
                "codigo_municipio": "",
                "nome_municipio": "",
                "uf": uf,
                "codigo_uf": metadados.get("codigo_uf", ""),
                "macrorregiao": metadados.get("macrorregiao", ""),
                "sigla_macrorregiao": metadados.get(
                    "sigla_macrorregiao", ""
                ),
                "estado": metadados.get("estado", ""),
                "media_salarial_deflacionada_2024": formatar_decimal(media),
                "num_salarios_validos": quantidade,
            }
        )

    if not registros:
        raise ValueError(
            "Nenhum salário válido foi encontrado para a Economia Criativa. "
            "Verifique os códigos CNAE, municípios e salários da base."
        )

    colunas_saida = [
        "tipo_recorte",
        "codigo_municipio",
        "nome_municipio",
        "uf",
        "codigo_uf",
        "macrorregiao",
        "sigla_macrorregiao",
        "estado",
        "media_salarial_deflacionada_2024",
        "num_salarios_validos",
    ]

    resultado = pd.DataFrame(registros, columns=colunas_saida)
    resultado = resultado.sort_values(
        ["tipo_recorte", "uf", "nome_municipio"],
        kind="stable",
    ).reset_index(drop=True)

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        sep=";",
        encoding="utf-8-sig",
        na_rep="",
    )

    quantidade_capitais = int(
        resultado["tipo_recorte"].eq("capital").sum()
    )
    quantidade_ufs = int(
        resultado["tipo_recorte"].eq("uf").sum()
    )

    print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
    print(f"Linhas por capital: {quantidade_capitais}")
    print(f"Linhas por UF: {quantidade_ufs}")
    print(f"Total de linhas exportadas: {len(resultado)}")


if __name__ == "__main__":
    main()