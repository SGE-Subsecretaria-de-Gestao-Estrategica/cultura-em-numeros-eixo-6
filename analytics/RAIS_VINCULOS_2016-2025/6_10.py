import os
import re
import unicodedata
from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd


# ====
# CONFIGURACOES
# ====

CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2025_com_informalidade.csv"
)
DIRETORIO_SAIDA = r"E:\Rais\Rais\csvs"

ARQUIVO_SAIDA_CAPITAIS = os.path.join(DIRETORIO_SAIDA, "6.10.1.csv")
ARQUIVO_SAIDA_UFS = os.path.join(DIRETORIO_SAIDA, "6.10.2.csv")

ANO_REFERENCIA = 2024


# Mapeamento local de UFs: aceita siglas e nomes por extenso.
CODIGOS_UF = {
    "ac": "AC",
    "acre": "AC",
    "al": "AL",
    "alagoas": "AL",
    "ap": "AP",
    "amapa": "AP",
    "am": "AM",
    "amazonas": "AM",
    "ba": "BA",
    "bahia": "BA",
    "ce": "CE",
    "ceara": "CE",
    "df": "DF",
    "distrito federal": "DF",
    "es": "ES",
    "espirito santo": "ES",
    "go": "GO",
    "goias": "GO",
    "ma": "MA",
    "maranhao": "MA",
    "mt": "MT",
    "mato grosso": "MT",
    "ms": "MS",
    "mato grosso do sul": "MS",
    "mg": "MG",
    "minas gerais": "MG",
    "pa": "PA",
    "para": "PA",
    "pb": "PB",
    "paraiba": "PB",
    "pr": "PR",
    "parana": "PR",
    "pe": "PE",
    "pernambuco": "PE",
    "pi": "PI",
    "piaui": "PI",
    "rj": "RJ",
    "rio de janeiro": "RJ",
    "rn": "RN",
    "rio grande do norte": "RN",
    "rs": "RS",
    "rio grande do sul": "RS",
    "ro": "RO",
    "rondonia": "RO",
    "rr": "RR",
    "roraima": "RR",
    "sc": "SC",
    "santa catarina": "SC",
    "sp": "SP",
    "sao paulo": "SP",
    "se": "SE",
    "sergipe": "SE",
    "to": "TO",
    "tocantins": "TO",
}


# Mapeamento local das capitais para códigos municipais IBGE de 7 dígitos.
CODIGOS_CAPITAIS = {
    "aracaju": "2800308",
    "belem": "1501402",
    "belo horizonte": "3106200",
    "boa vista": "1400100",
    "brasilia": "5300108",
    "campo grande": "5002704",
    "cuiaba": "5103403",
    "curitiba": "4106902",
    "florianopolis": "4205407",
    "fortaleza": "2304400",
    "goiania": "5208707",
    "joao pessoa": "2507507",
    "macapa": "1600303",
    "maceio": "2704302",
    "manaus": "1302603",
    "natal": "2408102",
    "palmas": "1721000",
    "porto alegre": "4314902",
    "porto velho": "1100205",
    "recife": "2611606",
    "rio branco": "1200401",
    "rio de janeiro": "3304557",
    "salvador": "2927408",
    "sao luis": "2111300",
    "sao paulo": "3550308",
    "teresina": "2211001",
    "vitoria": "3205309",
}


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_texto(valor) -> str:
    """Remove acentos e padroniza espaços e capitalização."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().casefold()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"\s+", " ", texto)


def parse_num(valor):
    """Converte números com separadores brasileiros ou notação científica."""
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return np.nan

    texto = texto.replace(" ", "")

    if "e" in texto.casefold():
        try:
            return float(texto.replace(",", "."))
        except ValueError:
            return np.nan

    if "," in texto and "." in texto:
        # Considera como decimal o separador que aparece por último.
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):
        texto = texto.replace(".", "")

    try:
        return float(texto)
    except ValueError:
        return np.nan


def formatar_decimal_sem_cientifica(valor) -> str:
    """Formata número com ponto decimal, sem notação científica."""
    if pd.isna(valor):
        return ""

    try:
        texto = format(Decimal(str(valor)), "f")
    except (InvalidOperation, ValueError):
        return ""

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


def separar_grupo(valor):
    """
    Separa um rótulo no formato:
    Prefixo - Localidade - Tipo

    O tipo é lido a partir do último segmento, permitindo hífens
    dentro do nome da localidade.
    """
    if pd.isna(valor):
        return None, None, None

    partes = re.split(r"\s*[-–]\s*", str(valor).strip())

    if len(partes) < 3:
        return None, None, None

    prefixo = partes[0].strip()
    tipo = partes[-1].strip()
    localidade = " - ".join(parte.strip() for parte in partes[1:-1])

    if not prefixo or not localidade or not tipo:
        return None, None, None

    return prefixo, localidade, tipo


def converter_capital(localidade: str) -> str:
    """Converte uma capital ou código municipal para código IBGE."""
    texto = str(localidade).strip()

    if re.fullmatch(r"\d{7}", texto):
        return texto

    codigo = CODIGOS_CAPITAIS.get(normalizar_texto(texto))

    if codigo is None:
        raise ValueError(
            f"Capital sem código IBGE cadastrado localmente: '{localidade}'. "
            "Inclua a correspondência em CODIGOS_CAPITAIS."
        )

    return codigo


def converter_uf(localidade: str) -> str:
    """Converte o nome ou a sigla de uma UF para a sigla oficial."""
    uf = CODIGOS_UF.get(normalizar_texto(localidade))

    if uf is None:
        raise ValueError(
            f"UF sem correspondência cadastrada localmente: '{localidade}'. "
            "Inclua a correspondência em CODIGOS_UF."
        )

    return uf


# ====
# CALCULO DA PARTICIPACAO
# ====

def calcular_participacao(
    df: pd.DataFrame,
    prefixo_procurado: str,
    tipo_localidade: str,
) -> pd.DataFrame:
    """
    Calcula a participação de Cultura por localidade.

    O numerador vem de total_vinculos_informais_estimado (linhas Cultura) e o
    denominador de total_vinculos_ibge (linhas Total). Valores ausentes não
    são substituídos por zero.
    """
    prefixo_normalizado = normalizar_texto(prefixo_procurado)

    linhas = []

    for grupo, ano, total_informais, total_ibge in zip(
        df["grupo"],
        df["ano"],
        df["total_vinculos_informais_estimado"],
        df["total_vinculos_ibge"],
    ):
        if pd.isna(ano) or ano != ANO_REFERENCIA:
            continue

        prefixo, localidade, tipo = separar_grupo(grupo)

        if prefixo is None:
            continue

        prefixo_linha = normalizar_texto(prefixo)

        # Correspondência tolerante ao texto do prefixo.
        if prefixo_normalizado not in prefixo_linha:
            continue

        tipo_normalizado = normalizar_texto(tipo)

        if "cultura" in tipo_normalizado:
            tipo_padronizado = "cultura"
        elif "total" in tipo_normalizado:
            tipo_padronizado = "total"
        else:
            continue

        # Numerador: informais de Cultura; denominador: total do IBGE.
        valor = total_informais if tipo_padronizado == "cultura" else total_ibge

        if tipo_localidade == "capital":
            codigo_geografico = converter_capital(localidade)
        elif tipo_localidade == "uf":
            codigo_geografico = converter_uf(localidade)
        else:
            raise ValueError(
                f"Tipo de localidade não previsto: '{tipo_localidade}'."
            )

        linhas.append(
            {
                "localidade": codigo_geografico,
                "tipo": tipo_padronizado,
                "valor": valor,
            }
        )

    recorte = pd.DataFrame(linhas)

    if recorte.empty:
        raise ValueError(
            f"Nenhum registro encontrado para o prefixo "
            f"'{prefixo_procurado}' e ano {ANO_REFERENCIA}."
        )

    # Agrupa por código geográfico e tipo, sem transformar valores ausentes
    # em zero. min_count=1 mantém ausente quando todos os valores são ausentes.
    agrupado = (
        recorte.groupby(
            ["localidade", "tipo"],
            as_index=False,
            dropna=False,
        )["valor"]
        .sum(min_count=1)
    )

    total = (
        agrupado.loc[agrupado["tipo"] == "total", ["localidade", "valor"]]
        .rename(columns={"valor": "total_ibge"})
    )
    cultura = (
        agrupado.loc[
            agrupado["tipo"] == "cultura",
            ["localidade", "valor"],
        ]
        .rename(columns={"valor": "total_cultura"})
    )

    if total.empty:
        raise ValueError(
            f"Nenhum registro do tipo 'Total' encontrado "
            f"para '{prefixo_procurado}'."
        )

    if cultura.empty:
        raise ValueError(
            f"Nenhum registro do tipo 'Cultura' encontrado "
            f"para '{prefixo_procurado}'."
        )

    dados = pd.merge(total, cultura, on="localidade", how="outer")

    denominador_valido = (
        dados["total_ibge"].notna()
        & dados["total_ibge"].ne(0)
        & dados["total_cultura"].notna()
    )

    dados["pct_participacao"] = np.nan
    dados.loc[denominador_valido, "pct_participacao"] = (
        dados.loc[denominador_valido, "total_cultura"]
        / dados.loc[denominador_valido, "total_ibge"]
    )

    dados["ano"] = ANO_REFERENCIA

    return dados[
        ["localidade", "ano", "pct_participacao"]
    ].sort_values("localidade").reset_index(drop=True)


# ====
# EXPORTACAO
# ====

def salvar_csv(
    df: pd.DataFrame,
    caminho: str,
    coluna_geografica: str,
) -> None:
    """Salva o resultado em CSV com os padrões definidos."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    resultado = df.rename(
        columns={
            "localidade": coluna_geografica,
        }
    ).copy()

    resultado["pct_participacao"] = resultado[
        "pct_participacao"
    ].map(formatar_decimal_sem_cientifica)

    resultado.to_csv(
        caminho,
        index=False,
        sep=";",
        decimal=".",
        na_rep="",
        encoding="utf-8-sig",
    )

    print(f"Arquivo gerado com sucesso: {caminho}")
    print(f"Registros exportados: {len(resultado)}\n")


# ====
# EXECUCAO PRINCIPAL
# ====

def main() -> None:
    try:
        if not os.path.isfile(CAMINHO_CSV_ENTRADA):
            raise FileNotFoundError(
                f"Arquivo de entrada não encontrado: {CAMINHO_CSV_ENTRADA}"
            )

        df = pd.read_csv(
            CAMINHO_CSV_ENTRADA,
            sep=";",
            dtype=str,
            encoding="utf-8-sig",
        )

        df.columns = [
            str(coluna).strip().replace("\ufeff", "")
            for coluna in df.columns
        ]

        colunas_necessarias = [
            "grupo",
            "ano",
            "total_vinculos_informais_estimado",
            "total_vinculos_ibge",
        ]

        colunas_ausentes = sorted(
            set(colunas_necessarias) - set(df.columns)
        )

        if colunas_ausentes:
            raise KeyError(
                "Colunas ausentes no arquivo de origem: "
                + ", ".join(colunas_ausentes)
            )

        df["ano"] = df["ano"].map(parse_num)
        df["total_vinculos_ibge"] = df["total_vinculos_ibge"].map(parse_num)
        df["total_vinculos_informais_estimado"] = df[
            "total_vinculos_informais_estimado"
        ].map(parse_num)

        df["grupo"] = df["grupo"].fillna("").astype(str).str.strip()

        capitais = calcular_participacao(
            df=df,
            prefixo_procurado="Capital",
            tipo_localidade="capital",
        )
        salvar_csv(
            capitais,
            ARQUIVO_SAIDA_CAPITAIS,
            coluna_geografica="cod_ibge",
        )

        ufs = calcular_participacao(
            df=df,
            prefixo_procurado="UF",
            tipo_localidade="uf",
        )
        salvar_csv(
            ufs,
            ARQUIVO_SAIDA_UFS,
            coluna_geografica="uf",
        )

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()