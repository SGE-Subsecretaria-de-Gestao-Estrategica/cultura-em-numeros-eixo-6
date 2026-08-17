"""
02_caged_adicionar_informalidade.py
====
Adiciona colunas de fluxo salarial total (estimativa de informalidade)
no CSV consolidado do CAGED.

Métricas adicionadas:
    fluxo_salarial_nom_total
    fluxo_salarial_def_total

Fórmulas:
    fator = (Formal - Total + Informal - Total) / Formal - Total
    valor_total = valor_formal * fator

Fonte de Informalidade:
    E:\\Rais\\Rais\\Auxiliares\\Informalidade2.xlsx
    Colunas: Escopo, Escala, Recorte, Formal - Total, Informal - Total, Ano
"""

import re
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np

# ==== CONFIGURAÇÃO ====
PASTA_DATA      = Path(r"E:\Rais\CAGED\data")
PASTA_AUX       = Path(r"E:\Rais\Rais\Auxiliares")

INPUT_CAGED     = PASTA_DATA / "caged_metricas_grupos_2016_2026_salario1M.csv"
INPUT_INFORMAL  = PASTA_AUX / "Informalidade2.xlsx"

OUTPUT_CAGED    = PASTA_DATA / "caged_com_informalidade_2016_2026.csv"

# Regex para UFs e Capitais (mesmo do script da RAIS)
REGEX_GRUPO = re.compile(r"^(UF|Capital)\s*-\s*(.*?)\s*-\s*(Total|Cultura)\s*$")

def norm_key(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    s = re.sub(r"\s+", " ", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.casefold()

def parse_grupo_caged(grupo):
    """Mapeia o nome do grupo do CAGED para os escopos da informalidade."""
    g = (grupo or "").strip()
    if g == "Brasil": return "Total", "Nacional", "Brasil"
    if g == "Cultura": return "Cultura", "Nacional", "Brasil"
    
    m = REGEX_GRUPO.match(g)
    if m:
        tipo, recorte, escopo = m.group(1), m.group(2).strip(), m.group(3)
        escala = "Estadual" if tipo == "UF" else "Municipal"
        return escopo, escala, recorte
    return None, None, None

def main():
    print(f"Lendo dados do CAGED: {INPUT_CAGED.name}")
    # Lê usando vírgula como decimal e ponto e vírgula como separador
    df = pd.read_csv(INPUT_CAGED, sep=";", decimal=",", encoding="utf-8-sig")

    # Parsing dos grupos para cruzamento
    parsed = df["grupo"].apply(parse_grupo_caged)
    df["_escopo"]  = parsed.apply(lambda x: x[0])
    df["_escala"]  = parsed.apply(lambda x: x[1])
    df["_recorte"] = parsed.apply(lambda x: x[2])
    
    df["_escopo_key"]  = df["_escopo"].apply(norm_key)
    df["_escala_key"]  = df["_escala"].apply(norm_key)
    df["_recorte_key"] = df["_recorte"].apply(norm_key)

    print(f"Lendo informalidade: {INPUT_INFORMAL.name}")
    inf = pd.read_excel(INPUT_INFORMAL)
    
    # Normalização de percentuais/frações
    inf["_pct_formal"]   = pd.to_numeric(inf["Formal - Total"], errors="coerce")
    inf["_pct_informal"] = pd.to_numeric(inf["Informal - Total"], errors="coerce")
    
    # Se os valores estiverem em formato 0-100, converte para 0-1
    if inf["_pct_formal"].max() > 1.5:
        inf["_pct_formal"] /= 100.0
        inf["_pct_informal"] /= 100.0

    inf["_escopo_key"]  = inf["Escopo"].apply(norm_key)
    inf["_escala_key"]  = inf["Escala"].apply(norm_key)
    inf["_recorte_key"] = inf["Recorte"].apply(norm_key)

    # ==== REPLICAR 2024 PARA 2025 E 2026 ====
    inf_2024 = inf[inf["Ano"] == 2024].copy()
    if not inf_2024.empty:
        for ano_futuro in [2025, 2026]:
            inf_f = inf_2024.copy()
            inf_f["Ano"] = ano_futuro
            inf = pd.concat([inf, inf_f], ignore_index=True)
        print(f"Informalidade de 2024 replicada para 2025 e 2026.")

    # Merge
    inf_small = inf[["Ano", "_escopo_key", "_escala_key", "_recorte_key", "_pct_formal", "_pct_informal"]]
    merged = df.merge(
        inf_small,
        left_on=["ano", "_escopo_key", "_escala_key", "_recorte_key"],
        right_on=["Ano", "_escopo_key", "_escala_key", "_recorte_key"],
        how="left"
    )

    # Cálculo do Fator (População Total / População Formal)
    # Fator = (Pct Formal + Pct Informal) / Pct Formal
    merged["_fator_informal"] = (merged["_pct_formal"] + merged["_pct_informal"]) / merged["_pct_formal"]

    # Aplicar estimativa
    # ONDE não temos dados de informalidade (setores específicos), o fluxo total = fluxo formal (fator=1)
    merged["_fator_informal"] = merged["_fator_informal"].fillna(1.0)
    
    merged["fluxo_salarial_nom_total"] = (merged["fluxo_salarial_nom"] * merged["_fator_informal"]).round(2)
    merged["fluxo_salarial_def_total"] = (merged["fluxo_salarial_def"] * merged["_fator_informal"]).round(2)

    # Limpeza e Organização
    colunas_finais = [
        "grupo", "ano", "mes", "competencia", "movimentacoes_liquidas",
        "fluxo_salarial_nom", "fluxo_salarial_def", 
        "salario_medio_adm_nom", "salario_medio_adm_def",
        "fluxo_salarial_nom_total", "fluxo_salarial_def_total"
    ]
    
    out = merged[colunas_finais]

    # Salva no padrão BR
    out.to_csv(OUTPUT_CAGED, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    
    print(f"\n[OK] Arquivo gerado: {OUTPUT_CAGED.name}")
    print(f"Total de linhas: {len(out)}")
    print(f"Recortes com informalidade aplicada: {len(merged[merged['_pct_formal'].notna()])}")

if __name__ == "__main__":
    main()