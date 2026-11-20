import unittest
from pathlib import Path
import pandas as pd

from src.oro import (
    construir_oro_mensual,
    construir_matriz_linaje,
    rastrear_linaje_registro,
    verificar_conservacion_fechas_ingesta,
)

RAIZ = Path(__file__).resolve().parent.parent


class LinajeTrazabilidadTests(unittest.TestCase):
    def setUp(self):
        # Datos simulados que representan la salida validada de Plata
        self.datos_plata = pd.DataFrame([
            {
                "anio_mes": pd.Timestamp("2024-02-01"),
                "anio": 2024,
                "mes": 2,
                "trimestre": 1,
                "semestre": 1,
                "estado": "colima",
                "region": "occidente",
                "pais": "mexico",
                "precio_frec_media": 18.5,
                "precio_min": 17.0,
                "precio_max": 20.0,
                "n_cotizaciones": 12,
                "n_atipicos": 0,
                "produccion_ton": 15000.0,
                "valor_produccion": 30000000.0,
                "precio_rural_kg": 2.0,
                "en_siap": True,
                "anio_dato_siap": 2024,
                "siap_imputado": False,
                "temp_media_c": 24.2,
                "temp_min_c": 17.5,
                "temp_max_c": 31.0,
                "precipitacion_mm": 2.5,
                "precio_nivel": "medio",
                "precio_rango": "bajo",
                "produccion_nivel": "media",
                "archivos_bronce_sniim": "2024-02-01_2024-02-29.html",
                "fecha_ingesta_sniim": "2026-11-07T18:24:49+00:00",
                "sha256_bronce_sniim": "cb45d645c3077d001bbce069f6135b8547b0e300a27b8d4857b587c1e8ef4a6a",
                "archivo_bronce_siap": "cierre_2024.csv.gz",
                "fecha_ingesta_siap": "2026-11-07T18:35:12+00:00",
                "sha256_bronce_siap": "2c6c69dfa0b0cdc28db67a20a5043e9d95e9080cf7aba7ab44e2a5af6950617d",
                "archivo_bronce_clima": "colima_2023-11-01_2026-10-31.json",
                "fecha_ingesta_clima": "2026-11-20T19:25:44.327222+00:00",
                "fecha_ingesta_reciente_bronce": "2026-11-20T19:25:44.327222+00:00",
                "linaje_id": "9f8e7d6c5b4a3120",
            }
        ])

        self.bitacoras = {
            "sniim": {
                "2024-02-01_2024-02-29.html": {
                    "fecha_captura_utc": "2026-11-07T18:24:49+00:00",
                    "sha256": "cb45d645c3077d001bbce069f6135b8547b0e300a27b8d4857b587c1e8ef4a6a",
                }
            },
            "siap": {
                "cierre_2024.csv.gz": {
                    "fecha_captura_utc": "2026-11-07T18:35:12+00:00",
                    "sha256": "2c6c69dfa0b0cdc28db67a20a5043e9d95e9080cf7aba7ab44e2a5af6950617d",
                }
            },
            "clima": {
                "colima_2023-11-01_2026-10-31.json": {
                    "fecha_captura_utc": "2026-11-20T19:25:44.327222+00:00",
                    "sha256": "eeea53666d871b8c40cc45a8f1682a6222963b7af2601659c0ae9cc118b1e6c2",
                }
            },
        }

    def test_oro_mensual_conserva_linaje_y_genera_registro_id(self):
        oro_mensual = construir_oro_mensual(self.datos_plata)
        self.assertIn("registro_id_oro", oro_mensual.columns)
        self.assertIn("linaje_id", oro_mensual.columns)
        self.assertIn("fecha_ingesta_sniim", oro_mensual.columns)
        self.assertIn("fecha_ingesta_siap", oro_mensual.columns)
        self.assertIn("fecha_ingesta_clima", oro_mensual.columns)
        self.assertIn("fecha_ingesta_reciente_bronce", oro_mensual.columns)

        # Comprobar que no son nulos ni vacíos
        self.assertEqual(oro_mensual.loc[0, "fecha_ingesta_sniim"], "2026-11-07T18:24:49+00:00")
        self.assertEqual(oro_mensual.loc[0, "fecha_ingesta_siap"], "2026-11-07T18:35:12+00:00")
        self.assertEqual(oro_mensual.loc[0, "fecha_ingesta_clima"], "2026-11-20T19:25:44.327222+00:00")

    def test_matriz_linaje_permite_rastreo_bidireccional_a_bronce(self):
        oro_mensual = construir_oro_mensual(self.datos_plata)
        oro_geo_vacio = pd.DataFrame(columns=[
            "registro_id_oro", "origen_estado", "destino_mercado", "anio_mes",
            "archivos_bronce_sniim", "fecha_ingesta_bronce"
        ])

        matriz = construir_matriz_linaje(oro_mensual, oro_geo_vacio, self.bitacoras)
        
        reg_id = oro_mensual.loc[0, "registro_id_oro"]
        rastreo = matriz[matriz["registro_id_oro"] == reg_id]
        
        # Deben existir los 3 vínculos Bronce (sniim, siap, clima)
        fuentes = set(rastreo["fuente_bronce"])
        self.assertIn("sniim", fuentes)
        self.assertIn("siap", fuentes)
        self.assertIn("clima_open_meteo", fuentes)

        # Comprobar que los hashes SHA-256 coinciden con Bronce
        fila_clima = rastreo[rastreo["fuente_bronce"] == "clima_open_meteo"].iloc[0]
        self.assertEqual(fila_clima["archivo_bronce"], "colima_2023-11-01_2026-10-31.json")
        self.assertEqual(fila_clima["sha256_bronce"], "eeea53666d871b8c40cc45a8f1682a6222963b7af2601659c0ae9cc118b1e6c2")

    def test_verificar_conservacion_fechas_ingesta(self):
        oro_mensual = construir_oro_mensual(self.datos_plata)
        total_rev, disc = verificar_conservacion_fechas_ingesta(oro_mensual, self.bitacoras)
        self.assertGreater(total_rev, 0)
        self.assertEqual(disc, 0)


if __name__ == "__main__":
    unittest.main()

