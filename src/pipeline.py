from pathlib import Path

from integracion import integrar, agregar_siap_anual
from limpieza import (diagnostico_faltantes, imputar_faltantes,
                      marcar_atipicos_iqr, normalizar, discretizar, reducir)

RAIZ = Path(__file__).resolve().parent.parent


def main():
    integrado, sniim_d, siap_h = integrar(
        RAIZ / "data/bronce/sniim", RAIZ / "data/bronce/siap")

    plata = RAIZ / "data/plata"
    plata.mkdir(parents=True, exist_ok=True)

    # Paso 3 (SIAP): IQR informativo sobre el rendimiento
    siap_h = marcar_atipicos_iqr(siap_h, "rendimiento_ton_ha")

    # Copias intermedias SIN imputar (trazabilidad)
    integrado.to_parquet(plata / "integrado_sin_validar.parquet", index=False)
    sniim_d.to_parquet(plata / "sniim_diario_homologado.parquet", index=False)
    siap_h.to_parquet(plata / "siap_municipal_homologado.parquet", index=False)

    # Reporte de atípicos e incoherencias del SNIIM (evidencia para la entrega)
    reporte = sniim_d[sniim_d["es_atipico"] | sniim_d["precio_incoherente"]]
    reporte.to_csv(plata / "reporte_atipicos_sniim.csv", index=False)
    print("\nFilas integradas:", len(integrado))

    # Paso 2: valores faltantes
    print("\n===== PASO 2: DIAGNÓSTICO DE FALTANTES =====")
    diagnostico_faltantes(integrado)
    siap_anual = agregar_siap_anual(siap_h)
    integrado = imputar_faltantes(integrado, siap_anual)
    integrado.to_parquet(plata / "integrado_imputado.parquet", index=False)

    # Paso 4: normalización y estandarización
    print("\n===== PASO 4: NORMALIZACIÓN =====")
    integrado = normalizar(integrado)

    # Paso 5: discretización y jerarquías
    print("\n===== PASO 5: DISCRETIZACIÓN =====")
    integrado = discretizar(integrado)
    integrado.to_parquet(plata / "integrado_transformado.parquet", index=False)

    # Paso 6: reducción de datos
    print("\n===== PASO 6: REDUCCIÓN =====")
    reducido, eliminadas = reducir(integrado, siap_h, sniim_d)
    reducido.to_parquet(plata / "integrado_reducido.parquet", index=False)
    print("\nColumnas finales:", list(reducido.columns))


if __name__ == "__main__":
    main()