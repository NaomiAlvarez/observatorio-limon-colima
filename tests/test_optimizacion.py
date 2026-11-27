import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from src.geoespacial import (
    haversine_km,
    haversine_km_vectorizado,
    enriquecer_mercados_geoespacial,
)
from src.integracion import CULTIVOS_LIMON, limpiar_texto


class OptimizacionRendimientoTests(unittest.TestCase):
    def test_haversine_vectorizado_coincide_con_escalar(self):
        """Verifica que el cálculo geodésico vectorizado sea matemáticamente idéntico al escalar."""
        lats1 = [18.91, 19.09, 17.15, 22.99, 20.30]
        lons1 = [-103.88, -102.35, -99.53, -105.86, -89.42]
        lats2 = [19.36, 19.60, 16.85, 27.48, 19.09]
        lons2 = [-99.09, -99.03, -99.89, -109.93, -98.19]

        # Cálculo escalar
        escalares = [
            haversine_km(lat1, lon1, lat2, lon2)
            for lat1, lon1, lat2, lon2 in zip(lats1, lons1, lats2, lons2)
        ]

        # Cálculo vectorizado
        vectorizados = haversine_km_vectorizado(
            pd.Series(lats1), pd.Series(lons1), pd.Series(lats2), pd.Series(lons2)
        ).tolist()

        for esc, vec in zip(escalares, vectorizados):
            self.assertAlmostEqual(esc, vec, places=2)

    def test_haversine_vectorizado_maneja_nulos(self):
        """Comprueba que coordenadas nulas generen NaN sin levantar excepción."""
        s_lat1 = pd.Series([18.91, np.nan])
        s_lon1 = pd.Series([-103.88, -103.88])
        s_lat2 = pd.Series([19.36, 19.36])
        s_lon2 = pd.Series([-99.09, np.nan])

        res = haversine_km_vectorizado(s_lat1, s_lon1, s_lat2, s_lon2)
        self.assertFalse(np.isnan(res[0]))
        self.assertTrue(np.isnan(res[1]))

    def test_enriquecimiento_geoespacial_produce_mismo_esquema(self):
        """Verifica que el enriquecimiento optimizado genere las columnas requeridas."""
        datos = pd.DataFrame([{
            "origen_estado": "colima",
            "destino_mercado": "DF: Central de Abasto de Iztapalapa DF",
            "precio_min_corr": 20.0,
            "precio_max_corr": 25.0,
            "precio_frec_corr": 22.5,
            "es_duplicado": False,
            "precio_incoherente": False,
        }])
        geo = enriquecer_mercados_geoespacial(datos)
        for col in ["origen_lat", "origen_lon", "destino_lat", "destino_lon", "distancia_transporte_km"]:
            self.assertIn(col, geo.columns)
        self.assertGreater(geo.loc[0, "distancia_transporte_km"], 450.0)


if __name__ == "__main__":
    unittest.main()
