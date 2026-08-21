from pathlib import Path

DATA_DIR = Path("C:/caminho/local/para/dados")

RAIS_VINCULOS_DIR = DATA_DIR / "raw" / "rais" / "vinculos"
RAIS_ESTABELECIMENTOS_DIR = DATA_DIR / "raw" / "rais" / "estabelecimentos"
CAGED_DIR = DATA_DIR / "raw" / "caged"
INFORMALIDADE_DIR = DATA_DIR / "raw" / "informalidade"

EXTERNAL_DIR = DATA_DIR / "external"
CNAE_PATH = EXTERNAL_DIR / "CNAE-ibge.xlsx"
MUNICIPIOS_PATH = EXTERNAL_DIR / "municipios.xlsx"
IPCA_PATH = EXTERNAL_DIR / "IPCA_mensal.xls"

PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs/tables")