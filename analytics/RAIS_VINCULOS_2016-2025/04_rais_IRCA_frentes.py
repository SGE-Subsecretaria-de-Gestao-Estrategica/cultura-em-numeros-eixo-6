"""
04_rais_IRCA_frentes.py
=======================
Gera dois índices de acompanhamento a partir do CSV da RAIS com informalidade:

  1) IRCA_Salarial  — baseado na massa salarial formal ajustada pela TF e deflacionada
  2) IRCA_Vinculos  — baseado nos vínculos formais ajustados pela TF

Ambos normalizados para 2024 = 1,0 (escala 0–1, compatível com o IRCA original da RAIS).

Lógica de ajuste pela Taxa de Formalidade (TF):
  - TF_ano     = total_vinculos / (total_vinculos + total_vinculos_informais_estimado)
  - fator_TF   = TF_2024 / TF_ano   (normaliza para a estrutura de formalidade de 2024)
  - valor_ajustado = valor_formal * fator_TF

Saída:
  - rais_IRCA_frentes.csv  (sep=';', decimal=',', encoding='utf-8-sig')
  - rais_IRCA_frentes.xlsx (com abas por nível: Nacional, Estadual, Municipal)

Compatibilidade:
  - Grupos disponíveis: Brasil, Cultura, UF - <nome> - <escopo>, Capital - <nome> - <escopo>
  - Setores sem informalidade (Agricultura, Indústria, Construção) ficam com IRCA_Vinculos = NaN
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_DATA   = Path(r"E:\Rais\Rais\DF1\data")

INPUT_CSV    = PASTA_DATA / "rais_metricas_grupos_2016_2025_com_informalidade.csv"
OUTPUT_CSV   = PASTA_DATA / "rais_IRCA_frentes.csv"
OUTPUT_XLSX  = PASTA_DATA / "rais_IRCA_frentes.xlsx"

BASE_YEAR    = 2024

# ============================================================
# LEITURA
# ============================================================

def ler_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig", low_memory=False)
    # fallback encoding
    if df.shape[1] <= 1:
        df = pd.read_csv(path, sep=";", decimal=",", encoding="utf-8", low_memory=False)
    return df


# ============================================================
# CLASSIFICAÇÃO DE GRUPOS
# ============================================================

_REGEX_UF      = re.compile(r"^UF\s*-\s*(.*?)\s*-\s*(Total|Cultura)\s*$")
_REGEX_CAPITAL = re.compile(r"^Capital\s*-\s*(.*?)\s*-\s*(Total|Cultura)\s*$")


def classificar_grupo(grupo: str) -> tuple[str, str, str]:
    """
    Retorna (nivel, regiao, escopo).
    nivel  : 'Nacional' | 'Estadual' | 'Municipal'
    regiao : nome da região (ex: 'Brasil', 'São Paulo', 'Curitiba')
    escopo : 'Total' | 'Cultura' | <setor>
    """
    g = str(grupo).strip()

    if g == "Brasil":
        return "Nacional", "Brasil", "Total"
    if g == "Cultura":
        return "Nacional", "Brasil", "Cultura"

    m = _REGEX_UF.match(g)
    if m:
        return "Estadual", m.group(1).strip(), m.group(2).strip()

    m = _REGEX_CAPITAL.match(g)
    if m:
        return "Municipal", m.group(1).strip(), m.group(2).strip()

    # Setores (Agricultura, Indústria, Construção)
    return "Nacional", "Brasil", g


# ============================================================
# CÁLCULO DOS ÍNDICES
# ============================================================

def calcular_irca(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o CSV bruto e retorna DataFrame com os dois índices por grupo × ano.
    """
    df = df_raw.copy()

    # Colunas numéricas
    for col in ["total_vinculos", "total_vinculos_informais_estimado",
                "massa_salarial_nom", "massa_salarial_def"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

    # Classificação
    parsed = df["grupo"].apply(classificar_grupo)
    df["nivel"]  = parsed.apply(lambda x: x[0])
    df["regiao"] = parsed.apply(lambda x: x[1])
    df["escopo"] = parsed.apply(lambda x: x[2])

    # ---- Taxa de Formalidade ----
    # TF = formais / (formais + informais_estimados)
    total_estimado = df["total_vinculos"] + df["total_vinculos_informais_estimado"].fillna(0)
    df["TF"] = np.where(
        total_estimado > 0,
        df["total_vinculos"] / total_estimado,
        np.nan
    )

    # TF âncora de 2024 por (nivel, regiao, escopo)
    tf_2024 = (
        df[df["ano"] == BASE_YEAR]
        [["nivel", "regiao", "escopo", "TF"]]
        .rename(columns={"TF": "TF_2024"})
    )
    df = df.merge(tf_2024, on=["nivel", "regiao", "escopo"], how="left")

    # Fator de ajuste TF
    df["fator_TF"] = np.where(
        df["TF"].notna() & df["TF_2024"].notna() & (df["TF"] > 0),
        df["TF_2024"] / df["TF"],
        np.nan
    )

    # ---- IRCA Salarial ----
    # Usa massa_salarial_def (já deflacionada para 2024 pelo script 01)
    df["massa_ajustada"] = df["massa_salarial_def"] * df["fator_TF"].fillna(1.0)

    ref_sal = (
        df[df["ano"] == BASE_YEAR]
        [["nivel", "regiao", "escopo", "massa_ajustada"]]
        .rename(columns={"massa_ajustada": "massa_base_2024"})
    )
    df = df.merge(ref_sal, on=["nivel", "regiao", "escopo"], how="left")

    df["IRCA_Salarial"] = np.where(
        df["massa_base_2024"].notna() & (df["massa_base_2024"] > 0),
        df["massa_ajustada"] / df["massa_base_2024"],
        np.nan
    )

    # ---- IRCA Vínculos ----
    # Vínculos formais ajustados pela TF
    df["vinculos_ajustados"] = df["total_vinculos"] * df["fator_TF"].fillna(1.0)

    ref_vin = (
        df[df["ano"] == BASE_YEAR]
        [["nivel", "regiao", "escopo", "vinculos_ajustados"]]
        .rename(columns={"vinculos_ajustados": "vinculos_base_2024"})
    )
    df = df.merge(ref_vin, on=["nivel", "regiao", "escopo"], how="left")

    df["IRCA_Vinculos"] = np.where(
        df["vinculos_base_2024"].notna() & (df["vinculos_base_2024"] > 0)
        & df["total_vinculos_informais_estimado"].notna(),  # só calcula onde há TF disponível
        df["vinculos_ajustados"] / df["vinculos_base_2024"],
        np.nan
    )

    return df


# ============================================================
# FORMATAÇÃO DA SAÍDA
# ============================================================

_COLUNAS_SAIDA = [
    "grupo", "nivel", "regiao", "escopo", "ano",
    "total_vinculos", "total_vinculos_informais_estimado",
    "massa_salarial_nom", "massa_salarial_def",
    "TF", "TF_2024", "fator_TF",
    "massa_ajustada", "massa_base_2024", "IRCA_Salarial",
    "vinculos_ajustados", "vinculos_base_2024", "IRCA_Vinculos",
]

_RENAME_XLSX = {
    "grupo":                              "Grupo",
    "nivel":                              "Nível",
    "regiao":                             "Região",
    "escopo":                             "Escopo",
    "ano":                                "Ano",
    "total_vinculos":                     "Vínculos Formais",
    "total_vinculos_informais_estimado":  "Vínculos Informais Estimados",
    "massa_salarial_nom":                 "Massa Salarial Nominal (R$)",
    "massa_salarial_def":                 "Massa Salarial Real (R$ 2024)",
    "TF":                                 "TF Ano",
    "TF_2024":                            "TF 2024 (âncora)",
    "fator_TF":                           "Fator Ajuste TF",
    "massa_ajustada":                     "Massa Real Ajustada (R$ 2024)",
    "massa_base_2024":                    "Massa Base 2024 (R$ 2024)",
    "IRCA_Salarial":                      "IRCA Salarial (2024=1)",
    "vinculos_ajustados":                 "Vínculos Ajustados",
    "vinculos_base_2024":                 "Vínculos Base 2024",
    "IRCA_Vinculos":                      "IRCA Vínculos (2024=1)",
}


def _ordenar(df: pd.DataFrame) -> pd.DataFrame:
    ordem_nivel = {"Nacional": 0, "Estadual": 1, "Municipal": 2}
    df["_ord_nivel"] = df["nivel"].map(ordem_nivel).fillna(9)
    df = df.sort_values(["_ord_nivel", "regiao", "escopo", "ano"]).drop(columns="_ord_nivel")
    return df.reset_index(drop=True)


# ============================================================
# EXPORTAÇÃO CSV
# ============================================================

def exportar_csv(df: pd.DataFrame, path: Path) -> None:
    df_out = df[[c for c in _COLUNAS_SAIDA if c in df.columns]].copy()
    df_out = _ordenar(df_out)

    # Arredondamentos
    for col in ["TF", "TF_2024", "fator_TF"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].round(6)
    for col in ["IRCA_Salarial", "IRCA_Vinculos"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].round(6)
    for col in ["massa_salarial_nom", "massa_salarial_def", "massa_ajustada", "massa_base_2024"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].round(2)

    path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(path, sep=";", decimal=",", encoding="utf-8-sig", index=False)
    print(f"[OK] CSV salvo: {path}  ({len(df_out):,} linhas)")


# ============================================================
# EXPORTAÇÃO XLSX
# ============================================================

def exportar_xlsx(df: pd.DataFrame, path: Path) -> None:
    df_out = df[[c for c in _COLUNAS_SAIDA if c in df.columns]].copy()
    df_out = _ordenar(df_out)
    df_out = df_out.rename(columns=_RENAME_XLSX)

    path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for nivel in ["Nacional", "Estadual", "Municipal"]:
            df_nivel = df_out[df_out["Nível"] == nivel].copy()
            if df_nivel.empty:
                continue
            sheet = nivel[:31]
            df_nivel.to_excel(writer, sheet_name=sheet, index=False)

        # Aba resumo com apenas os índices
        cols_resumo = [
            "Grupo", "Nível", "Região", "Escopo", "Ano",
            "TF Ano", "TF 2024 (âncora)", "Fator Ajuste TF",
            "IRCA Salarial (2024=1)", "IRCA Vínculos (2024=1)",
        ]
        cols_resumo_disp = [c for c in cols_resumo if c in df_out.columns]
        df_out[cols_resumo_disp].to_excel(writer, sheet_name="IRCA_series", index=False)

    # Formatação PT-BR via openpyxl
    wb = load_workbook(path)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        headers = [cell.value for cell in ws[1]]

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                h = headers[cell.column - 1]
                if h is None or not isinstance(cell.value, (int, float, np.floating, np.integer)):
                    continue
                h_low = str(h).lower()
                if "massa" in h_low or "vínculos" in h_low and "base" in h_low:
                    cell.number_format = "R$ #.##0,00"
                elif "tf" in h_low or "taxa" in h_low or "fator" in h_low:
                    cell.number_format = "0,0000"
                elif "irca" in h_low:
                    cell.number_format = "#.##0,0000"
                elif "vínculos" in h_low:
                    cell.number_format = "#.##0"

    wb.save(path)
    print(f"[OK] XLSX salvo: {path}")


# ============================================================
# DIAGNÓSTICO
# ============================================================

def diagnostico(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DOS ÍNDICES")
    print("=" * 60)

    grupos_chave = ["Brasil - Total", "Brasil - Cultura"]
    for _, row in df[
        (df["regiao"] == "Brasil") & (df["nivel"] == "Nacional")
    ].sort_values(["escopo", "ano"]).iterrows():
        label = f"{row['escopo']:10s} | {int(row['ano'])}"
        sal = f"{row['IRCA_Salarial']:.4f}" if pd.notna(row["IRCA_Salarial"]) else "  NaN "
        vin = f"{row['IRCA_Vinculos']:.4f}" if pd.notna(row["IRCA_Vinculos"]) else "  NaN "
        tf  = f"{row['TF']:.4f}"            if pd.notna(row["TF"])            else "  NaN "
        print(f"  {label} | TF={tf} | IRCA_Sal={sal} | IRCA_Vin={vin}")

    print()
    n_sal_nan = df["IRCA_Salarial"].isna().sum()
    n_vin_nan = df["IRCA_Vinculos"].isna().sum()
    print(f"  IRCA_Salarial NaN : {n_sal_nan:,} linhas")
    print(f"  IRCA_Vinculos NaN : {n_vin_nan:,} linhas  (esperado: setores sem TF)")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 60)
    print("04_rais_IRCA_frentes.py — Índices Salarial e Vínculos (RAIS)")
    print("=" * 60)
    print(f"Input  : {INPUT_CSV}")
    print(f"Output : {OUTPUT_CSV}")
    print(f"Output : {OUTPUT_XLSX}")
    print(f"Base   : {BASE_YEAR} = 1,0")
    print()

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_CSV}")

    print("Lendo CSV...")
    df_raw = ler_csv(INPUT_CSV)
    print(f"  {len(df_raw):,} linhas | {df_raw.shape[1]} colunas")
    print(f"  Grupos únicos: {df_raw['grupo'].nunique()}")
    print(f"  Anos: {sorted(df_raw['ano'].dropna().unique().tolist())}")

    print("\nCalculando índices...")
    df_irca = calcular_irca(df_raw)

    diagnostico(df_irca)

    print("\nExportando...")
    exportar_csv(df_irca, OUTPUT_CSV)
    exportar_xlsx(df_irca, OUTPUT_XLSX)

    print("\n[CONCLUÍDO]")


if __name__ == "__main__":
    main()
