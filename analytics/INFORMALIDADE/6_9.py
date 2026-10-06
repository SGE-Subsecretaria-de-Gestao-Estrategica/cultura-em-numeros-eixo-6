import os
import re
import unicodedata

import pandas as pd


# ====
# CONFIGURACOES
# ====

CAMINHO_XLSX_ENTRADA = r"E:\Rais\Rais\Auxiliares\Informalidade2.xlsx"
DIRETORIO_SAIDA = r"E:\Rais\Rais\csvs"

ARQUIVO_SAIDA_ESTADUAL = os.path.join(DIRETORIO_SAIDA, "6.9.1.csv")
ARQUIVO_SAIDA_MUNICIPAL = os.path.join(DIRETORIO_SAIDA, "6.9.2.csv")

ANO_REFERENCIA = 2024
ESCOPO_ORIGEM = "Cultura"
NOME_GRUPO_SAIDA = "Economia Criativa"

COLUNAS_OBRIGATORIAS = [
    "Escopo",
    "Escala",
    "Recorte",
    "Ano",
    "Formal - Total",
    "Informal - Total",
]


# Mapeamento local de nomes de estados para siglas.
CODIGOS_UF = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "goias": "GO",
    "maranhao": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "paraiba": "PB",
    "parana": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}


# Mapeamento local de capitais para códigos municipais IBGE de 7 dígitos.
CODIGOS_MUNICIPIOS = {
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
# FUNCOES
# ====

def normalizar_texto(valor) -> str:
    """Remove acentos, espaços excedentes e diferenças entre maiúsculas/minúsculas."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().casefold()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    texto = re.sub(r"\s+", " ", texto)

    return texto


def validar_colunas(df: pd.DataFrame) -> None:
    """Verifica se todas as colunas necessárias existem na planilha."""
    colunas_ausentes = sorted(
        set(COLUNAS_OBRIGATORIAS) - set(df.columns)
    )

    if colunas_ausentes:
        raise KeyError(
            "Colunas obrigatórias não encontradas na planilha: "
            + ", ".join(colunas_ausentes)
        )


def padronizar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza cabeçalhos, textos e tipos numéricos da planilha."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    validar_colunas(df)

    for coluna in ["Escopo", "Escala", "Recorte"]:
        df[coluna] = df[coluna].fillna("").astype(str).str.strip()

    for coluna in ["Ano", "Formal - Total", "Informal - Total"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df


def converter_uf(recorte: str) -> str:
    """Converte o nome de um estado para sua sigla, sem consulta externa."""
    chave = normalizar_texto(recorte)
    uf = CODIGOS_UF.get(chave)

    if uf is None:
        raise ValueError(
            f"Não há sigla de UF cadastrada localmente para o recorte "
            f"'{recorte}'. Inclua a correspondência em CODIGOS_UF."
        )

    return uf


def converter_municipio(recorte: str) -> str:
    """Converte o nome de uma capital para seu código IBGE local."""
    texto = str(recorte).strip()

    if re.fullmatch(r"\d{7}", texto):
        return texto

    chave = normalizar_texto(texto)
    codigo = CODIGOS_MUNICIPIOS.get(chave)

    if codigo is None:
        raise ValueError(
            f"Não há código municipal cadastrado localmente para o recorte "
            f"'{recorte}'. Inclua a correspondência em CODIGOS_MUNICIPIOS."
        )

    return codigo


def gerar_csv_por_escala(
    df: pd.DataFrame,
    escala: str,
    caminho_saida: str,
) -> None:
    """Filtra Cultura no ano de referência e grava um CSV por escala."""

    escopo_normalizado = normalizar_texto(ESCOPO_ORIGEM)
    escala_normalizada = normalizar_texto(escala)

    escopos = df["Escopo"].map(normalizar_texto)
    escalas = df["Escala"].map(normalizar_texto)

    # Busca tolerante a diferenças de maiúsculas, acentos e texto excedente.
    filtro = (
        escopos.str.contains(
            re.escape(escopo_normalizado),
            regex=True,
            na=False,
        )
        & escalas.str.contains(
            re.escape(escala_normalizada),
            regex=True,
            na=False,
        )
        & df["Ano"].eq(ANO_REFERENCIA)
    )

    resultado = df.loc[
        filtro,
        ["Recorte", "Ano", "Formal - Total", "Informal - Total"],
    ].copy()

    if resultado.empty:
        raise ValueError(
            f"Nenhum registro encontrado para Escopo='{ESCOPO_ORIGEM}', "
            f"Escala='{escala}' e Ano={ANO_REFERENCIA}."
        )

    resultado.insert(0, "grupo", NOME_GRUPO_SAIDA)
    resultado["ano"] = resultado["Ano"].astype("Int64")

    if normalizar_texto(escala) == "estadual":
        resultado["uf"] = resultado["Recorte"].map(converter_uf)
        colunas_saida = [
            "grupo",
            "uf",
            "ano",
            "pct_formal",
            "pct_informal",
        ]
        resultado = resultado.rename(
            columns={
                "Formal - Total": "pct_formal",
                "Informal - Total": "pct_informal",
            }
        )

    elif normalizar_texto(escala) == "municipal":
        resultado["cod_ibge"] = resultado["Recorte"].map(
            converter_municipio
        )
        colunas_saida = [
            "grupo",
            "cod_ibge",
            "ano",
            "pct_formal",
            "pct_informal",
        ]
        resultado = resultado.rename(
            columns={
                "Formal - Total": "pct_formal",
                "Informal - Total": "pct_informal",
            }
        )

    else:
        raise ValueError(f"Escala não prevista: '{escala}'.")

    resultado = resultado.sort_values(
        by=colunas_saida[1:3],
        kind="stable",
    ).reset_index(drop=True)

    resultado = resultado[colunas_saida]

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    resultado.to_csv(
        caminho_saida,
        index=False,
        sep=";",
        decimal=".",
        na_rep="",
        encoding="utf-8-sig",
    )

    print(f"Arquivo gerado com sucesso: {caminho_saida}")
    print(f"Registros exportados: {len(resultado)}")


# ====
# EXECUCAO PRINCIPAL
# ====

def main() -> None:
    """Lê a planilha e gera os CSVs estadual e municipal."""
    try:
        if not os.path.isfile(CAMINHO_XLSX_ENTRADA):
            raise FileNotFoundError(
                f"Arquivo de entrada não encontrado: "
                f"{CAMINHO_XLSX_ENTRADA}"
            )

        df = pd.read_excel(CAMINHO_XLSX_ENTRADA)
        df = padronizar_dados(df)

        gerar_csv_por_escala(
            df=df,
            escala="Estadual",
            caminho_saida=ARQUIVO_SAIDA_ESTADUAL,
        )

        gerar_csv_por_escala(
            df=df,
            escala="Municipal",
            caminho_saida=ARQUIVO_SAIDA_MUNICIPAL,
        )

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado ao processar os arquivos: {erro}")


if __name__ == "__main__":
    main()