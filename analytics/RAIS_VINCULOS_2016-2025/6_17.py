from __future__ import annotations

from pathlib import Path
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_BASE  = Path(r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2016_2025_com_informalidade.csv")
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.17.csv")

# Mapeamento: nome exato no CSV -> nome de exibição
GRUPOS_MAPPING = {
    "Brasil":                                                                    "Brasil",
    "Cultura":                                                                   "Economia Criativa",
    "Agricultura, pecuária, produção florestal, pesca e aquicultura":            "Agricultura",
    "Indústria extrativa":                                                       "Indústria extrativa",
    "Construção":                                                                "Construção Civil",
}

ANOS = list(range(2016, 2026))


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def parse_num_col(serie: pd.Series) -> pd.Series:
    """Converte coluna numérica com possível formatação brasileira para float."""
    s = serie.astype(str).str.strip()
    s = s.str.replace(r'(?i)\s*e\+?', 'E', regex=True)
    s = s.str.replace(r'\.(?=\d{3}(\D|$))', '', regex=True)
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce')


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        if not ARQUIVO_BASE.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_BASE}")

        # Leitura do arquivo base
        try:
            df = pd.read_csv(ARQUIVO_BASE, sep=';', encoding='utf-8-sig', engine='python')
        except Exception:
            df = pd.read_csv(ARQUIVO_BASE, sep=',', encoding='utf-8-sig', engine='python')

        df.columns = [c.strip('\ufeff').strip() for c in df.columns]

        if 'media_def' not in df.columns:
            raise KeyError(f"Coluna 'media_def' não encontrada. Colunas disponíveis: {list(df.columns)}")
        if 'grupo' not in df.columns:
            raise KeyError(f"Coluna 'grupo' não encontrada. Colunas disponíveis: {list(df.columns)}")

        df['media_def'] = parse_num_col(df['media_def'])
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').astype('Int64')

        # Filtra apenas os anos de interesse
        df = df[df['ano'].isin(ANOS)].copy()

        registros = []

        for csv_nome, exibicao_nome in GRUPOS_MAPPING.items():
            subset = df[df['grupo'] == csv_nome].copy()

            if subset.empty:
                subset = df[df['grupo'].str.strip() == csv_nome].copy()

            if subset.empty:
                print(f"Aviso: Grupo '{csv_nome}' não localizado no CSV.")
                continue

            # Média por ano (caso haja mais de uma linha por ano/grupo)
            serie_anual = (
                subset.groupby('ano')['media_def']
                .mean()
                .reindex(ANOS)
            )

            for ano, valor in serie_anual.items():
                registros.append({
                    "grupo": exibicao_nome,
                    "ano":   int(ano),
                    "media_salarial_deflacionada": round(float(valor), 2) if pd.notna(valor) else None,
                })

        if not registros:
            raise ValueError(
                "Nenhum dado encontrado após os filtros. "
                "Verifique os grupos e o arquivo de entrada."
            )

        resultado = pd.DataFrame(registros)

        ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=".",
            encoding="utf-8-sig",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(f"Registros exportados : {len(resultado)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()