from pathlib import Path
import pandas as pd

from integracion import integrar, agregar_siap_anual
from limpieza import (diagnostico_faltantes, imputar_faltantes,
                      marcar_atipicos_iqr, normalizar, discretizar, reducir)
from calidad import validar_archivos
from oro import (construir_oro_mensual, construir_oro_geoespacial,
                 construir_matriz_linaje, verificar_conservacion_fechas_ingesta)

RAIZ = Path(__file__).resolve().parent.parent


def main():
    print("=======================================================")
    print("OBSERVATORIO DEL LIMÓN EN COLIMA - PIPELINE MEDALLION")
    print("=======================================================")

    # Paso 1: Ingesta e Integración (SNIIM + SIAP + Clima Open-Meteo)
    integrado, sniim_d, siap_h, clima_d, bitacoras = integrar(
        RAIZ / "data/bronce/sniim",
        RAIZ / "data/bronce/siap",
        RAIZ / "data/bronce/clima",
    )

    plata = RAIZ / "data/plata"
    plata.mkdir(parents=True, exist_ok=True)
    oro = RAIZ / "data" / "oro"
    oro.mkdir(parents=True, exist_ok=True)

    # Paso 3 (SIAP): IQR informativo sobre el rendimiento
    siap_h = marcar_atipicos_iqr(siap_h, "rendimiento_ton_ha")

    # Copias intermedias SIN imputar (trazabilidad y reproducibilidad)
    integrado.to_parquet(plata / "integrado_sin_validar.parquet", index=False)
    sniim_d.to_parquet(plata / "sniim_diario_homologado.parquet", index=False)
    siap_h.to_parquet(plata / "siap_municipal_homologado.parquet", index=False)
    if not clima_d.empty:
        clima_d.to_parquet(plata / "clima_diario_homologado.parquet", index=False)

    # Reporte de atípicos e incoherencias del SNIIM (evidencia para auditoría)
    reporte = sniim_d[sniim_d["es_atipico"] | sniim_d["precio_incoherente"]]
    reporte.to_csv(plata / "reporte_atipicos_sniim.csv", index=False)
    print("\nFilas integradas:", len(integrado))

    # Paso 2: valores faltantes (Diagnóstico MAR e Imputación)
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
    print("\nColumnas finales en Plata:", list(reducido.columns))

    # Paso 7: Puerta de Calidad Plata (Pandera)
    print("\n===== PUERTA DE CALIDAD (PLATA) =====")
    validar_archivos(plata, RAIZ / "data/cuarentena", oro)

    # Paso 8: Construcción de la Capa Oro y Linaje Bronce -> Plata -> Oro
    print("\n===== PASO 8: GENERACIÓN DE CAPA ORO Y LINAJE =====")
    reducido_validado = pd.read_parquet(plata / "integrado_reducido_validado.parquet")
    sniim_validado = pd.read_parquet(plata / "sniim_diario_validado.parquet")

    # 1. Tabla Oro Mensual (Lags predictivos + Clima + Producción + Linaje)
    oro_mensual = construir_oro_mensual(reducido_validado)
    oro_mensual.to_parquet(oro / "oro_serie_mensual_observatorio.parquet", index=False)
    print(f"  Tabla Oro Mensual generada: {oro_mensual.shape} en {oro / 'oro_serie_mensual_observatorio.parquet'}")

    # 2. Tabla Oro Geoespacial (Rutas comerciales + Distancia Haversine + Spreads de precios)
    oro_geo = construir_oro_geoespacial(sniim_validado, siap_anual)
    oro_geo.to_parquet(oro / "oro_mercados_geoespacial.parquet", index=False)
    print(f"  Tabla Oro Geoespacial generada: {oro_geo.shape} en {oro / 'oro_mercados_geoespacial.parquet'}")

    # 3. Matriz de Linaje y Trazabilidad Extremo a Extremo
    matriz_linaje = construir_matriz_linaje(oro_mensual, oro_geo, bitacoras)
    matriz_linaje.to_parquet(oro / "oro_linaje_matriz.parquet", index=False)
    matriz_linaje.to_csv(oro / "oro_linaje_matriz.csv", index=False)
    print(f"  Matriz de Linaje generada: {len(matriz_linaje)} vínculos trazables Bronce -> Oro")

    # Paso 9: Verificación de Conservación de Fechas de Ingesta y Calidad Oro
    print("\n===== VERIFICACIÓN DE LINAJE Y CONSERVACIÓN DE FECHAS =====")
    total_rev, disc = verificar_conservacion_fechas_ingesta(oro_mensual, bitacoras)
    print(f"  Fechas de ingesta auditadas en Oro: {total_rev} | Discrepancias encontradas: {disc}")
    if disc > 0:
        raise RuntimeError("Fallo de linaje: se detectaron discrepancias en las fechas de ingesta.")
    print("  Conservación de fechas de ingesta comprobada al 100%.")

    print("\n=======================================================")
    print("PIPELINE COMPLETADO CON ÉXITO: BRONCE -> PLATA -> ORO")
    print("=======================================================")


if __name__ == "__main__":
    main()
