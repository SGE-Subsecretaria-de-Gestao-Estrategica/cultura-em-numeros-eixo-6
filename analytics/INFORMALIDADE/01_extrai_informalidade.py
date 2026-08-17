"""
gerar_informalidade2.py
=======================
Lê o arquivo "Tabela 6.4.xlsx" (múltiplas abas anuais) e gera o arquivo
"Informalidade2.xlsx" no mesmo formato do arquivo original de referência.

Colunas de saída:
    Escopo | Escala | Recorte | Formal - Total | Informal - Total | Ano

Regras de mapeamento:
    - Brasil            → Escala = "Nacional",  Recorte = "Brasil"
    - Grandes Regiões   → ignoradas
    - Estados           → Escala = "Estadual",  Recorte = <nome do estado>
    - Municípios        → Escala = "Municipal",  Recorte = <nome do município>
    - "Rio de Janeiro" e "São Paulo" aparecem duas vezes por ano:
        1ª ocorrência → Estadual
        2ª ocorrência → Municipal
    - Escopo "Total"    → colunas de todos os setores (cols 3-4 da tabela)
    - Escopo "Cultura"  → colunas do setor cultural (cols 9-10 da tabela)
    - Ano 2014          → excluído (mantém apenas 2015-2024)
    - Ordenação final   → Escopo, Escala, Recorte, Ano (decrescente)
"""

import re
import pandas as pd

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
INPUT_FILE  = r"E:\Rais\Rais\Informalidade\Tabela 6.4.xlsx"
OUTPUT_FILE = r"E:\Rais\Rais\Informalidade\Informalidade2.xlsx"

# Grandes Regiões — linhas a ignorar
GRANDES_REGIOES = {
    "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"
}

# Municípios das capitais (nomes exatos como aparecem na tabela)
MUNICIPIOS = {
    "Porto Velho", "Rio Branco", "Manaus", "Boa Vista", "Belém",
    "Macapá", "Palmas", "São Luís", "Teresina", "Fortaleza",
    "Natal", "João Pessoa", "Recife", "Maceió", "Aracaju",
    "Salvador", "Belo Horizonte", "Vitória", "Curitiba",
    "Florianópolis", "Porto Alegre", "Campo Grande", "Cuiabá",
    "Goiânia", "Brasília",
    # RJ e SP municipais são tratados separadamente (2ª ocorrência)
}

# Nomes que aparecem tanto como Estado quanto como Município
DUPLOS = {"Rio de Janeiro", "São Paulo"}


def detect_year_from_title(title: str) -> int | None:
    """Extrai o ano de 4 dígitos do título da aba/tabela."""
    match = re.search(r"\b(20\d{2})\b", str(title))
    return int(match.group(1)) if match else None


def find_data_start(df: pd.DataFrame) -> int:
    """
    Localiza a linha onde os dados começam (linha com 'Brasil' na col 0).
    """
    for i, val in enumerate(df.iloc[:, 0]):
        if str(val).strip() == "Brasil":
            return i
    raise ValueError("Linha 'Brasil' não encontrada no bloco de dados.")


def classify_location(name: str, seen_duplos: dict) -> tuple[str, str] | None:
    """
    Retorna (escala, recorte) para um nome de localidade.
    Retorna None para linhas a ignorar (Grandes Regiões, NaN, rodapés).
    """
    name = str(name).strip()

    if not name or name.lower() == "nan":
        return None
    if name == "Brasil":
        return ("Nacional", "Brasil")
    if name in GRANDES_REGIOES:
        return None  # ignorar

    # Nomes que aparecem como Estado e Município
    if name in DUPLOS:
        count = seen_duplos.get(name, 0) + 1
        seen_duplos[name] = count
        if count == 1:
            return ("Estadual", name)
        else:
            return ("Municipal", name)

    if name in MUNICIPIOS:
        return ("Municipal", name)

    # Qualquer outro nome é tratado como Estado
    # (filtra rodapés pela ausência de padrão de nome geográfico)
    if re.match(r"^[A-ZÀ-Ú][a-zà-ú]", name):
        return ("Estadual", name)

    return None  # rodapé ou linha irrelevante


def parse_sheet(df: pd.DataFrame, year: int) -> list[dict]:
    """
    Processa um bloco de dados anual e retorna lista de registros.

    Layout das colunas (0-indexed, após localizar a linha de dados):
        col 0  → localidade
        col 3  → Formal  (todos os setores, proporção %)
        col 5  → Informal (todos os setores, proporção %)
        col 9  → Formal  (setor cultural, proporção %)
        col 11 → Informal (setor cultural, proporção %)
    """
    start = find_data_start(df)
    records = []
    seen_duplos: dict[str, int] = {}

    for _, row in df.iloc[start:].iterrows():
        name = str(row.iloc[0]).strip()

        # Para de processar ao encontrar linha de rodapé/fonte
        if "Fonte" in name or "Nota" in name or "Tabela" in name:
            break

        classification = classify_location(name, seen_duplos)
        if classification is None:
            continue

        escala, recorte = classification

        try:
            formal_total   = float(row.iloc[3]) / 100
            informal_total = float(row.iloc[5]) / 100
            formal_cult    = float(row.iloc[9]) / 100
            informal_cult  = float(row.iloc[11]) / 100
        except (ValueError, TypeError):
            continue  # linha sem dados numéricos válidos

        records.append({
            "Escopo": "Total",
            "Escala": escala,
            "Recorte": recorte,
            "Formal - Total": round(formal_total, 6),
            "Informal - Total": round(informal_total, 6),
            "Ano": year,
        })
        records.append({
            "Escopo": "Cultura",
            "Escala": escala,
            "Recorte": recorte,
            "Formal - Total": round(formal_cult, 6),
            "Informal - Total": round(informal_cult, 6),
            "Ano": year,
        })

    return records


def main():
    print(f"Lendo '{INPUT_FILE}'...")
    xl = pd.ExcelFile(INPUT_FILE)

    all_records: list[dict] = []

    for sheet_name in xl.sheet_names:
        # Ignora abas de coeficiente de variação (ex: "2024 (CV)")
        if re.search(r"\(CV\)", sheet_name, re.IGNORECASE):
            print(f"  Aba '{sheet_name}': coeficiente de variação — ignorada.")
            continue

        # Extrai o ano pelo nome da aba (mais confiável que o título da célula)
        year = detect_year_from_title(sheet_name)
        if year is None:
            # Fallback: tenta pelo título da célula (0, 0)
            raw_check = xl.parse(sheet_name, header=None)
            year = detect_year_from_title(str(raw_check.iloc[0, 0]))

        if year is None or year < 2015:
            print(f"  Aba '{sheet_name}': ano {year} — ignorada.")
            continue

        raw = xl.parse(sheet_name, header=None)
        print(f"  Processando aba '{sheet_name}' → ano {year}...")
        try:
            records = parse_sheet(raw, year)
            all_records.extend(records)
            print(f"    {len(records)} registros extraídos.")
        except ValueError as e:
            print(f"    AVISO: {e} — aba ignorada.")

    if not all_records:
        print("Nenhum registro encontrado. Verifique o arquivo de entrada.")
        return

    df_out = pd.DataFrame(all_records, columns=[
        "Escopo", "Escala", "Recorte", "Formal - Total", "Informal - Total", "Ano"
    ])

    # Ordenação: Escopo, Escala, Recorte (alfabético), Ano (decrescente)
    escopo_order = {"Total": 0, "Cultura": 1}
    escala_order = {"Nacional": 0, "Estadual": 1, "Municipal": 2}

    df_out["_escopo_ord"] = df_out["Escopo"].map(escopo_order)
    df_out["_escala_ord"] = df_out["Escala"].map(escala_order)

    df_out = (
        df_out
        .sort_values(
            by=["_escopo_ord", "_escala_ord", "Recorte", "Ano"],
            ascending=[True, True, True, False]
        )
        .drop(columns=["_escopo_ord", "_escala_ord"])
        .reset_index(drop=True)
    )

    print(f"\nTotal de registros gerados: {len(df_out)}")
    print(f"Salvando em '{OUTPUT_FILE}'...")

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name="Informalidade2")

    print("Concluído com sucesso!")


if __name__ == "__main__":
    main()