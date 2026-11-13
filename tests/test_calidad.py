import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.calidad import (
    ESQUEMA_INTEGRADO,
    ESQUEMA_SNIIM,
    validar_archivo,
    validar_dataframe,
)


def fila_sniim(**cambios):
    fila = {
        "fecha": "2024-02-26",
        "anio": 2024,
        "anio_mes": "2024-02-01",
        "producto": "limon_c_semilla_4_primera",
        "presentacion": "caja de 19 kg.",
        "origen_estado": "colima",
        "destino_mercado": "Sonora: Central de Abasto",
        "destino_estado": "sonora",
        "precio_min": 18.42,
        "precio_max": 20.0,
        "precio_frec": 18.42,
        "archivo_origen": "2024-02-01_2024-02-29.html",
        "es_duplicado": False,
        "es_atipico": False,
        "precio_min_corr": 18.42,
        "precio_max_corr": 20.0,
        "precio_frec_corr": 18.42,
        "precio_incoherente": False,
    }
    return {**fila, **cambios}


def fila_integrada(**cambios):
    fila = {
        "anio_mes": "2024-02-01",
        "anio": 2024,
        "estado": "colima",
        "precio_frec_media": 18.42,
        "precio_min": 18.42,
        "precio_max": 20.0,
        "n_cotizaciones": 10,
        "n_atipicos": 1,
        "produccion_ton": 1000.0,
        "valor_produccion": 2000000.0,
        "precio_rural_kg": 2.0,
        "en_siap": True,
        "anio_dato_siap": 2024,
        "siap_imputado": False,
        "precio_frec_media_minmax": 0.5,
        "precio_frec_media_z": 0.1,
        "precio_min_minmax": 0.5,
        "precio_min_z": 0.1,
        "precio_max_minmax": 0.5,
        "precio_max_z": 0.1,
        "produccion_ton_minmax": 0.5,
        "produccion_ton_z": 0.1,
        "valor_produccion_minmax": 0.5,
        "valor_produccion_z": 0.1,
        "precio_rural_kg_minmax": -0.05,
        "precio_rural_kg_z": -0.1,
        "mes": 2,
        "trimestre": 1,
        "semestre": 1,
        "region": "occidente",
        "pais": "mexico",
        "precio_nivel": "medio",
        "precio_rango": "bajo",
        "produccion_nivel": "alta",
    }
    return {**fila, **cambios}


class PuertaDeCalidadTests(unittest.TestCase):
    def test_quarantines_bad_sniim_row_and_keeps_marked_flags(self):
        datos = pd.DataFrame([
            fila_sniim(es_duplicado=True, es_atipico=True),
            fila_sniim(
                fecha="2024-02-27",
                precio_min=25.0,
                precio_incoherente=True,
            ),
        ])

        validos, cuarentena = validar_dataframe(datos, ESQUEMA_SNIIM)

        self.assertEqual(len(validos), 1)
        self.assertTrue(validos.loc[0, "es_duplicado"])
        self.assertTrue(validos.loc[0, "es_atipico"])
        self.assertEqual(len(cuarentena), 1)
        self.assertIn("orden_precios", cuarentena.loc[0, "motivo"])
        self.assertIn("equal_to(False)", cuarentena.loc[0, "motivo"])

    def test_checks_integrated_ranges_and_allows_imputed_normalization(self):
        datos = pd.DataFrame([
            fila_integrada(),
            fila_integrada(mes=13),
        ])

        validos, cuarentena = validar_dataframe(datos, ESQUEMA_INTEGRADO)

        self.assertEqual(len(validos), 1)
        self.assertEqual(len(cuarentena), 1)
        self.assertAlmostEqual(validos.loc[0, "precio_rural_kg_minmax"], -0.05)
        self.assertIn("in_range(1, 12)", cuarentena.loc[0, "motivo"])

    def test_archives_quarantine_idempotently_and_preserves_row_counts(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            entrada = raiz / "entrada.parquet"
            salida = raiz / "validado.parquet"
            carpeta_cuarentena = raiz / "cuarentena"
            pd.DataFrame([
                fila_sniim(),
                fila_sniim(
                    fecha="2024-02-27",
                    precio_frec=0,
                    precio_incoherente=True,
                ),
            ]).to_parquet(entrada, index=False)

            conteos = validar_archivo(
                entrada,
                salida,
                carpeta_cuarentena,
                ESQUEMA_SNIIM,
                "sniim_diario",
            )
            validar_archivo(
                entrada,
                salida,
                carpeta_cuarentena,
                ESQUEMA_SNIIM,
                "sniim_diario",
            )

            self.assertEqual(conteos, (2, 1, 1))
            self.assertEqual(len(pd.read_parquet(salida)), 1)
            registros_cuarentena = pd.read_csv(carpeta_cuarentena / "sniim_diario.csv")
            self.assertEqual(len(registros_cuarentena), 1)
            self.assertIn("motivo", registros_cuarentena.columns)
            self.assertEqual(registros_cuarentena.loc[0, "fuente"], "sniim_diario")


if __name__ == "__main__":
    unittest.main()
