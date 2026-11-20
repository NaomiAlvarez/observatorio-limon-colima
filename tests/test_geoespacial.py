import unittest
import numpy as np
import pandas as pd

from src.geoespacial import (
    haversine_km,
    enriquecer_mercados_geoespacial,
    COORDENADAS_ORIGEN,
    COORDENADAS_DESTINO,
)


class GeoespacialTests(unittest.TestCase):
    def test_haversine_km_distancia_conocida(self):
        # Tecomán, Colima a Central de Abasto Iztapalapa, CDMX
        lat_tecoman, lon_tecoman = 18.913, -103.874
        lat_iztapalapa, lon_iztapalapa = 19.371, -99.092
        distancia = haversine_km(lat_tecoman, lon_tecoman, lat_iztapalapa, lon_iztapalapa)
        
        # Distancia en línea recta esperada aprox: 504 km (+- 15 km)
        self.assertGreater(distancia, 490.0)
        self.assertLess(distancia, 520.0)

    def test_haversine_misma_coordenada_es_cero(self):
        dist = haversine_km(19.0, -102.0, 19.0, -102.0)
        self.assertEqual(dist, 0.0)

    def test_haversine_maneja_nulos(self):
        dist = haversine_km(np.nan, -102.0, 19.0, -102.0)
        self.assertTrue(np.isnan(dist))

    def test_enriquecer_mercados_geoespacial_agrega_coordenadas_y_distancia(self):
        df_dummy = pd.DataFrame([
            {
                "fecha": "2024-02-15",
                "origen_estado": "colima",
                "destino_mercado": "DF: Central de Abasto de Iztapalapa DF",
                "precio_frec": 18.5,
            },
            {
                "fecha": "2024-02-15",
                "origen_estado": "michoacan",
                "destino_mercado": "Puebla: Central de Abasto de Puebla",
                "precio_frec": 16.0,
            },
        ])
        
        enriquecido = enriquecer_mercados_geoespacial(df_dummy)
        
        self.assertIn("origen_lat", enriquecido.columns)
        self.assertIn("origen_lon", enriquecido.columns)
        self.assertIn("destino_lat", enriquecido.columns)
        self.assertIn("destino_lon", enriquecido.columns)
        self.assertIn("distancia_transporte_km", enriquecido.columns)
        
        self.assertAlmostEqual(enriquecido.loc[0, "origen_lat"], COORDENADAS_ORIGEN["colima"]["lat"])
        self.assertAlmostEqual(enriquecido.loc[0, "destino_lat"], COORDENADAS_DESTINO["DF: Central de Abasto de Iztapalapa DF"]["lat"])
        self.assertGreater(enriquecido.loc[0, "distancia_transporte_km"], 0.0)


if __name__ == "__main__":
    unittest.main()
