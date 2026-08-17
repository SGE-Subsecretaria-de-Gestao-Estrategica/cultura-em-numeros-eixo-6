"""
03_caged_IRCA_frentes.py
====
Calcula o IRCA em duas frentes (Salarial e Vínculos) para todos os grupos.
Utiliza as âncoras de Dezembro/2024 a partir do arquivo RAIS.

Frente 1 (Salarial): Ajuste TF_2024/TF_ano + Deflação.
Frente 2 (Vínculos): Expansão para Total Estimado (Estoque/TF_ano).
"""

import pandas as pd
from pathlib import Path

# ==== CONFIGURAÇÃO DE CAMINHOS ====
PASTA_DATA = Path(r"E:\Rais\CAGED\data")
PASTA_AUX  = Path(r"E:\Rais\Rais\Auxiliares")

INPUT_CAGED    = PASTA_DATA / "caged_com_informalidade_2016_2026.csv"
INPUT_ANCORAS  = PASTA_DATA / "rais_cultura_uf_capitais_2024.csv"
INPUT_INFORMAL = PASTA_AUX / "Informalidade2.xlsx"

OUTPUT_FILE    = PASTA_DATA / "caged_IRCA_final_2016_2026.csv"

# Âncoras Fixas Brasil Total (Não apenas cultura)
ESTOQUE_VIN_BR_TOTAL = 45837596
ESTOQUE_SAL_BR_TOTAL = 215466645344.52
COMPETENCIA_BASE = 202412

def main():
    print("Processando tabelas de suporte...")
    # 1. Preparar Âncoras
    anc = pd.read_csv(INPUT_ANCORAS, sep=";", decimal=",", encoding="utf-8-sig")
    
    # Criar coluna 'grupo' para bater com o CAGED
    # Ex: "UF - Acre - Cultura" ou "Capital - Rio Branco - Cultura"
    anc["grupo"] = anc["recorte"] + " - " + anc["local"] + " - Cultura"
    
    anc_dict = anc.set_index("grupo")[["total_vinculos", "soma_vl_rem_dezembro_nom"]].to_dict('index')
    
    # Adicionar âncora Brasil Cultura (Soma das UFs)
    df_ufs = anc[anc["recorte"] == "UF"]
    anc_dict["Cultura"] = {
        "total_vinculos": df_ufs["total_vinculos"].sum(),
        "soma_vl_rem_dezembro_nom": df_ufs["soma_vl_rem_dezembro_nom"].sum()
    }
    
    # Adicionar âncora Brasil (Mercado Total)
    anc_dict["Brasil"] = {
        "total_vinculos": ESTOQUE_VIN_BR_TOTAL,
        "soma_vl_rem_dezembro_nom": ESTOQUE_SAL_BR_TOTAL
    }

    # 2. Carregar Informalidade para Taxa de Formalidade (TF)
    inf = pd.read_excel(INPUT_INFORMAL)
    inf["TF"] = pd.to_numeric(inf["Formal - Total"], errors="coerce")
    if inf["TF"].max() > 1.5: inf["TF"] /= 100.0
    
    # Criar mapeamento de TF (usamos Escopo Cultura/Nacional como referência padrão)
    # Para simplificar na escala Brasil/Cultura, pegamos a TF Nacional
    tf_nacional = inf[inf["Escopo"] == "Cultura"].set_index("Ano")["TF"].to_dict()
    tf_2024 = tf_nacional[2024]

    # 3. Carregar dados do CAGED
    print(f"Lendo {INPUT_CAGED.name}...")
    df = pd.read_csv(INPUT_CAGED, sep=";", decimal=",", encoding="utf-8-sig")
    df = df.sort_values(["grupo", "competencia"])

    def processar_grupo(g_name, g_data):
        if g_name not in anc_dict:
            return None
        
        # Pega as âncoras do grupo
        v_base = anc_dict[g_name]["total_vinculos"]
        s_base = anc_dict[g_name]["soma_vl_rem_dezembro_nom"]
        
        # Reconstrução de Estoques
        # Saldo acumulado (fluxo acumulado)
        g_data = g_data.copy()
        g_data["saldo_vin_acum"] = g_data["movimentacoes_liquidas"].cumsum()
        g_data["saldo_sal_acum"] = g_data["fluxo_salarial_def"].cumsum()

        # Achar o acumulado no ponto de âncora (Dez/2024)
        row_base = g_data[g_data["competencia"] == COMPETENCIA_BASE]
        if row_base.empty: return None
        
        offset_vin = row_base["saldo_vin_acum"].iloc[0]
        offset_sal = row_base["saldo_sal_acum"].iloc[0]

        # Estoque(t) = Âncora + (Acum_t - Acum_Base)
        g_data["estoque_vin_formal"] = v_base + (g_data["saldo_vin_acum"] - offset_vin)
        g_data["estoque_sal_formal"] = s_base + (g_data["saldo_sal_acum"] - offset_sal)

        # Taxa de Formalidade do ano (simplificado pela nacional para garantir consistência)
        g_data["TF_ano"] = g_data["ano"].map(lambda x: tf_nacional.get(x, tf_nacional[2024]))

        # --- FRENTE 1: Salarial (IRCA_Salarial) ---
        # Massa Ajustada = Massa Formal * (TF_2024 / TF_ano)
        g_data["fator_TF"] = tf_2024 / g_data["TF_ano"]
        g_data["massa_ajustada"] = g_data["estoque_sal_formal"] * g_data["fator_TF"]
        massa_base_ajustada = g_data.loc[g_data["competencia"] == COMPETENCIA_BASE, "massa_ajustada"].iloc[0]
        g_data["IRCA_Salarial"] = (g_data["massa_ajustada"] / massa_base_ajustada) * 100

        # --- FRENTE 2: Vínculos (IRCA_Vinculos) ---
        # Estoque Total Estimado = Estoque Formal / TF_ano
        g_data["vinculos_total_estimado"] = g_data["estoque_vin_formal"] / g_data["TF_ano"]
        vinculos_base_estimado = g_data.loc[g_data["competencia"] == COMPETENCIA_BASE, "vinculos_total_estimado"].iloc[0]
        g_data["IRCA_Vinculos"] = (g_data["vinculos_total_estimado"] / vinculos_base_estimado) * 100

        return g_data

    print("Calculando índices por grupo...")
    list_dfs = []
    for name, group in df.groupby("grupo"):
        res = processar_grupo(name, group)
        if res is not None:
            list_dfs.append(res)
    
    df_final = pd.concat(list_dfs)

    # Organização Final
    cols = [
        "grupo", "ano", "mes", "competencia",
        "estoque_vin_formal", "vinculos_total_estimado", "IRCA_Vinculos",
        "estoque_sal_formal", "massa_ajustada", "IRCA_Salarial"
    ]
    
    df_output = df_final[cols].round(4)
    df_output.to_csv(OUTPUT_FILE, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    
    print(f"\n[SUCESSO] IRCA calculado para {len(list_dfs)} grupos.")
    print(f"Arquivo salvo em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()