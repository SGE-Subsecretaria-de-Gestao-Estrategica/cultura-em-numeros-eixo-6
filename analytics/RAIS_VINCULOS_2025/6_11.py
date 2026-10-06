import os
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd


# ====
# CONFIGURACOES
# ====

CAMINHO_BASE = (
    r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
)
CAMINHO_CNAE = r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx"
CAMINHO_MUNICIPIOS = r"E:\Rais\Rais\Auxiliares\municipios.xlsx"
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6.11.csv"

TAMANHO_CHUNK = 300_000

ANO_REFERENCIA = 2025
CASAS_DECIMAIS_TAXA = 5

COL_CNAE_BASE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_IBGE = "CNAE_IBGE"
COL_MUN_BASE = "Município - Código"
COL_MUN_AUX = "Cod_Município"
COL_MUN_NOME = "Município"


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_codigo(valor) -> str:
    """Retorna somente os dígitos do código, sem tratar ausente como zero."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return ""

    # Remove a terminação .0 que pode surgir de células numéricas do Excel.
    texto = re.sub(r"\.0+$", "", texto)

    return re.sub(r"\D", "", texto)


def padronizar_codigo_base(valor) -> tuple[str, str]:
    """
    Código municipal vindo do arquivo-base.
    Retorna (chave_6, codigo_7_quando_o_proprio_base_ja_traz_7_digitos).
    """
    codigo = normalizar_codigo(valor)

    if not codigo:
        return "", ""

    if len(codigo) >= 7:
        codigo_7 = codigo[:7]
        return codigo_7[:6], codigo_7

    return codigo.zfill(6), ""


def padronizar_codigo_aux(valor) -> tuple[str, str]:
    """
    Código municipal vindo da tabela auxiliar.
    Retorna (chave_6, codigo_7). Se a auxiliar só tiver 6 dígitos,
    o segundo elemento fica vazio, pois não há como derivar o código
    completo de 7 dígitos sem uma fonte que o contenha.
    """
    codigo = normalizar_codigo(valor)

    if not codigo:
        return "", ""

    if len(codigo) >= 7:
        codigo_7 = codigo[:7]
        return codigo_7[:6], codigo_7

    return codigo.zfill(6), ""


def normalizar_codigo_cnae(valor) -> str:
    """Normaliza o código CNAE para comparação entre os arquivos."""
    return normalizar_codigo(valor)


def carregar_codigos_ec(caminho: str) -> set[str]:
    """Carrega os códigos CNAE da Economia Criativa da planilha auxiliar."""
    df = pd.read_excel(caminho, dtype=str)
    df.columns = df.columns.astype(str).str.strip()

    if COL_CNAE_IBGE not in df.columns:
        raise KeyError(
            f"Coluna '{COL_CNAE_IBGE}' não encontrada em {caminho}. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )

    codigos = {
        normalizar_codigo_cnae(valor)
        for valor in df[COL_CNAE_IBGE]
        if normalizar_codigo_cnae(valor)
    }

    if not codigos:
        raise ValueError(
            f"Nenhum código CNAE válido encontrado na coluna "
            f"'{COL_CNAE_IBGE}'."
        )

    print(f"Códigos CNAE da Economia Criativa carregados: {len(codigos)}")
    return codigos


def carregar_municipios(caminho: str) -> pd.DataFrame:
    """Carrega a tabela auxiliar com chave de 6 dígitos, código de 7 e nome."""
    df = pd.read_excel(caminho, dtype=str)
    df.columns = df.columns.astype(str).str.strip()

    colunas_necessarias = [COL_MUN_AUX, COL_MUN_NOME]
    ausentes = sorted(set(colunas_necessarias) - set(df.columns))

    if ausentes:
        raise KeyError(
            f"Colunas ausentes em {caminho}: {', '.join(ausentes)}"
        )

    codigos = df[COL_MUN_AUX].map(padronizar_codigo_aux)

    df["cod_6"] = codigos.map(lambda item: item[0])
    df["cod_ibge_aux"] = codigos.map(lambda item: item[1])
    df["nome_municipio"] = df[COL_MUN_NOME].fillna("").astype(str).str.strip()

    municipios = (
        df.loc[df["cod_6"].ne(""), ["cod_6", "cod_ibge_aux", "nome_municipio"]]
        .drop_duplicates(subset="cod_6", keep="first")
        .reset_index(drop=True)
    )

    if municipios.empty:
        raise ValueError(
            f"Nenhum código municipal válido foi lido de {caminho}."
        )

    com_sete_digitos = municipios["cod_ibge_aux"].ne("").sum()
    if com_sete_digitos == 0:
        print(
            "Aviso: a tabela auxiliar não traz códigos de 7 dígitos. "
            "O código IBGE será obtido a partir do arquivo-base."
        )

    print(f"Municípios carregados: {len(municipios)}")
    return municipios


def detectar_separador(caminho: str) -> str:
    """Detecta se o arquivo CSV usa ponto e vírgula ou vírgula."""
    with open(caminho, "r", encoding="utf-8-sig", errors="replace") as arquivo:
        primeira_linha = arquivo.readline()

    return ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","


def calcular_taxa(quantidade_ec, quantidade_total):
    """
    Taxa de trabalhadores da Economia Criativa por 1.000 trabalhadores,
    calculada em Decimal e limitada ao número de casas definido.
    Retorna None quando não é possível calcular.
    """
    if pd.isna(quantidade_ec) or pd.isna(quantidade_total):
        return None

    total = int(quantidade_total)

    if total == 0:
        return None

    taxa = (
        Decimal(int(quantidade_ec))
        / Decimal(total)
        * Decimal(1000)
    )

    fator = Decimal(1).scaleb(-CASAS_DECIMAIS_TAXA)
    return taxa.quantize(fator, rounding=ROUND_HALF_UP)


def formatar_taxa(valor) -> str:
    """Formata a taxa como texto com ponto decimal, sem notação científica."""
    if valor is None:
        return ""

    try:
        texto = format(valor, "f")
    except (ValueError, ArithmeticError):
        return ""

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


# ====
# PROCESSAMENTO EM CHUNKS
# ====

def processar_chunks(
    caminho: str,
    codigos_ec: set[str],
    separador: str,
) -> tuple[pd.Series, pd.Series, dict]:
    """
    Acumula por município (chave de 6 dígitos):
    - contagem total de registros;
    - contagem de registros da Economia Criativa;
    - mapa de código IBGE de 7 dígitos quando o próprio base o traz.
    """
    contagem_total = pd.Series(dtype="int64")
    contagem_ec = pd.Series(dtype="int64")
    mapa_cod_7_base = {}

    chunks_lidos = 0

    for chunk in pd.read_csv(
        caminho,
        sep=separador,
        dtype=str,
        chunksize=TAMANHO_CHUNK,
        encoding="utf-8-sig",
        on_bad_lines="skip",
    ):
        chunk.columns = (
            chunk.columns.astype(str)
            .str.strip()
            .str.replace("\ufeff", "", regex=False)
        )

        colunas_necessarias = [COL_CNAE_BASE, COL_MUN_BASE]
        ausentes = sorted(set(colunas_necessarias) - set(chunk.columns))

        if ausentes:
            raise KeyError(
                "Colunas ausentes no arquivo base: " + ", ".join(ausentes)
            )

        codigos_mun = chunk[COL_MUN_BASE].map(padronizar_codigo_base)
        chunk["cod_6"] = codigos_mun.map(lambda item: item[0])
        chunk["cod_7"] = codigos_mun.map(lambda item: item[1])
        chunk["cnae_normalizada"] = chunk[COL_CNAE_BASE].map(
            normalizar_codigo_cnae
        )

        # Registros sem código municipal não são atribuídos a um município.
        chunk = chunk.loc[chunk["cod_6"].ne("")]

        if chunk.empty:
            chunks_lidos += 1
            print(f"Chunk {chunks_lidos} processado (0 registros válidos).")
            continue

        com_sete = chunk.loc[chunk["cod_7"].ne(""), ["cod_6", "cod_7"]]
        for cod_6, cod_7 in zip(com_sete["cod_6"], com_sete["cod_7"]):
            mapa_cod_7_base.setdefault(cod_6, cod_7)

        total_chunk = chunk.groupby("cod_6").size()
        contagem_total = contagem_total.add(total_chunk, fill_value=0)

        ec_chunk = chunk.loc[chunk["cnae_normalizada"].isin(codigos_ec)]

        if not ec_chunk.empty:
            ec_por_municipio = ec_chunk.groupby("cod_6").size()
            contagem_ec = contagem_ec.add(ec_por_municipio, fill_value=0)

        chunks_lidos += 1
        print(
            f"Chunk {chunks_lidos} processado "
            f"({len(chunk)} registros com município válido)."
        )

    if contagem_total.empty:
        raise ValueError(
            "Nenhum registro com código municipal válido foi encontrado "
            "no arquivo-base."
        )

    return (
        contagem_total.astype("int64"),
        contagem_ec.astype("int64"),
        mapa_cod_7_base,
    )


# ====
# EXECUCAO PRINCIPAL
# ====

def main() -> None:
    try:
        caminhos = [CAMINHO_BASE, CAMINHO_CNAE, CAMINHO_MUNICIPIOS]

        for caminho in caminhos:
            if not os.path.isfile(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        print("Carregando códigos CNAE da Economia Criativa...")
        codigos_ec = carregar_codigos_ec(CAMINHO_CNAE)

        print("\nCarregando tabela de municípios...")
        municipios = carregar_municipios(CAMINHO_MUNICIPIOS)

        separador = detectar_separador(CAMINHO_BASE)
        print(
            f"\nProcessando arquivo-base em chunks de "
            f"{TAMANHO_CHUNK} registros..."
        )

        contagem_total, contagem_ec, mapa_cod_7_base = processar_chunks(
            caminho=CAMINHO_BASE,
            codigos_ec=codigos_ec,
            separador=separador,
        )

        resultado = pd.DataFrame(
            {
                "cod_6": contagem_total.index,
                "num_trabalhadores": contagem_total.values,
            }
        )

        # Ausência de registros EC para um município com registros totais
        # significa zero registros EC, não dado ausente.
        resultado["num_trabalhadores_ec"] = (
            resultado["cod_6"].map(contagem_ec).fillna(0).astype("int64")
        )

        resultado["cod_ibge_base"] = (
            resultado["cod_6"].map(mapa_cod_7_base)
        )

        resultado = resultado.merge(
            municipios,
            on="cod_6",
            how="left",
            validate="many_to_one",
        )

        resultado["cod_ibge_aux"] = (
            resultado["cod_ibge_aux"].replace("", pd.NA)
        )
        resultado["cod_ibge"] = (
            resultado["cod_ibge_base"].fillna(resultado["cod_ibge_aux"])
        )

        sem_codigo = resultado["cod_ibge"].isna()

        if sem_codigo.all():
            raise ValueError(
                "Não foi possível montar o código IBGE de 7 dígitos: nem o "
                "arquivo-base nem a tabela auxiliar contêm o código completo. "
                f"Verifique se '{COL_MUN_AUX}' em municipios.xlsx tem 7 dígitos."
            )

        if sem_codigo.any():
            print(
                f"\nAviso: {int(sem_codigo.sum())} município(s) ficaram sem "
                "código IBGE de 7 dígitos e não foram exportados."
            )
            resultado = resultado.loc[~sem_codigo]

        resultado["nome_municipio"] = (
            resultado["nome_municipio"].fillna("").astype(str).str.strip()
        )

        taxas = [
            calcular_taxa(ec, total)
            for ec, total in zip(
                resultado["num_trabalhadores_ec"],
                resultado["num_trabalhadores"],
            )
        ]
        resultado["ec_por_1000_trabalhadores"] = [
            formatar_taxa(valor) for valor in taxas
        ]

        saida = (
            resultado[
                [
                    "cod_ibge",
                    "ec_por_1000_trabalhadores",
                    "nome_municipio",
                ]
            ]
            .copy()
            .sort_values(
                ["nome_municipio", "cod_ibge"],
                na_position="last",
                kind="stable",
            )
            .reset_index(drop=True)
        )
        saida.insert(1, "ano", ANO_REFERENCIA)

        diretorio = os.path.dirname(ARQUIVO_SAIDA)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)

        saida.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=".",
            na_rep="",
            encoding="utf-8-sig",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(
            "Colunas: cod_ibge;ano;ec_por_1000_trabalhadores;nome_municipio"
        )
        print(f"Municípios exportados: {len(saida)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()