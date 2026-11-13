#!/usr/bin/env python3
"""Puerta de Calidad: valida las salidas Plata y conserva filas rechazadas."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa

RAIZ = Path(__file__).resolve().parent.parent
PLATA = RAIZ / "data" / "plata"
CUARENTENA = RAIZ / "data" / "cuarentena"


def _columna_float(checks=()):
    return pa.Column(
        float,
        checks=[pa.Check(lambda valores: np.isfinite(valores), name="finito"), *checks],
        nullable=False,
    )


def _texto_no_vacio():
    return pa.Column(
        pa.String,
        checks=pa.Check(
            lambda valores: valores.astype(str).str.strip().ne(""),
            name="no_vacio",
        ),
        nullable=False,
    )


ESQUEMA_SNIIM = pa.DataFrameSchema(
    {
        "fecha": pa.Column(pa.DateTime, nullable=False),
        "anio": pa.Column(int, checks=pa.Check.ge(2000), nullable=False),
        "anio_mes": pa.Column(pa.DateTime, nullable=False),
        "producto": pa.Column(
            pa.String,
            checks=pa.Check.isin(["limon_c_semilla_4_primera"]),
            nullable=False,
        ),
        "presentacion": _texto_no_vacio(),
        "origen_estado": _texto_no_vacio(),
        "destino_mercado": _texto_no_vacio(),
        "destino_estado": _texto_no_vacio(),
        "precio_min": _columna_float([pa.Check.gt(0)]),
        "precio_max": _columna_float([pa.Check.gt(0)]),
        "precio_frec": _columna_float([pa.Check.gt(0)]),
        "archivo_origen": _texto_no_vacio(),
        "es_duplicado": pa.Column(bool, nullable=False),
        "es_atipico": pa.Column(bool, nullable=False),
        "precio_min_corr": _columna_float([pa.Check.gt(0)]),
        "precio_max_corr": _columna_float([pa.Check.gt(0)]),
        "precio_frec_corr": _columna_float([pa.Check.gt(0)]),
        "precio_incoherente": pa.Column(
            bool, checks=pa.Check.eq(False), nullable=False
        ),
    },
    checks=[
        pa.Check(
            lambda df: df["anio"].eq(df["fecha"].dt.year),
            name="anio_coincide_con_fecha",
        ),
        pa.Check(
            lambda df: df["anio_mes"].eq(
                df["fecha"].dt.to_period("M").dt.to_timestamp()
            ),
            name="anio_mes_coincide_con_fecha",
        ),
        pa.Check(
            lambda df: (
                df["precio_min"] <= df["precio_frec"]
            ) & (df["precio_frec"] <= df["precio_max"]),
            name="orden_precios",
        ),
    ],
    strict=True,
    coerce=True,
)

ESQUEMA_INTEGRADO = pa.DataFrameSchema(
    {
        "anio_mes": pa.Column(pa.DateTime, nullable=False),
        "anio": pa.Column(int, checks=pa.Check.ge(2000), nullable=False),
        "estado": _texto_no_vacio(),
        "precio_frec_media": _columna_float([pa.Check.gt(0)]),
        "precio_min": _columna_float([pa.Check.gt(0)]),
        "precio_max": _columna_float([pa.Check.gt(0)]),
        "n_cotizaciones": pa.Column(int, checks=pa.Check.ge(1), nullable=False),
        "n_atipicos": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
        "produccion_ton": _columna_float([pa.Check.gt(0)]),
        "valor_produccion": _columna_float([pa.Check.gt(0)]),
        "precio_rural_kg": _columna_float([pa.Check.gt(0)]),
        "en_siap": pa.Column(bool, nullable=False),
        "anio_dato_siap": pa.Column(int, checks=pa.Check.ge(2000), nullable=False),
        "siap_imputado": pa.Column(bool, nullable=False),
        "precio_frec_media_minmax": _columna_float(),
        "precio_frec_media_z": _columna_float(),
        "precio_min_minmax": _columna_float(),
        "precio_min_z": _columna_float(),
        "precio_max_minmax": _columna_float(),
        "precio_max_z": _columna_float(),
        "produccion_ton_minmax": _columna_float(),
        "produccion_ton_z": _columna_float(),
        "valor_produccion_minmax": _columna_float(),
        "valor_produccion_z": _columna_float(),
        "precio_rural_kg_minmax": _columna_float(),
        "precio_rural_kg_z": _columna_float(),
        "mes": pa.Column(int, checks=pa.Check.in_range(1, 12), nullable=False),
        "trimestre": pa.Column(
            int, checks=pa.Check.in_range(1, 4), nullable=False
        ),
        "semestre": pa.Column(int, checks=pa.Check.in_range(1, 2), nullable=False),
        "region": pa.Column(
            pa.String,
            checks=pa.Check.isin(["occidente", "sur", "noroeste", "sureste"]),
            nullable=False,
        ),
        "pais": pa.Column(
            pa.String, checks=pa.Check.eq("mexico"), nullable=False
        ),
        "precio_nivel": pa.Column(
            pa.String,
            checks=pa.Check.isin(["bajo", "medio", "alto"]),
            nullable=False,
        ),
        "precio_rango": pa.Column(
            pa.String,
            checks=pa.Check.isin(["bajo", "medio", "alto"]),
            nullable=False,
        ),
        "produccion_nivel": pa.Column(
            pa.String,
            checks=pa.Check.isin(["baja", "media", "alta"]),
            nullable=False,
        ),
    },
    checks=[
        pa.Check(
            lambda df: df["anio"].eq(df["anio_mes"].dt.year),
            name="anio_coincide_con_anio_mes",
        ),
        pa.Check(
            lambda df: df["mes"].eq(df["anio_mes"].dt.month),
            name="mes_coincide_con_anio_mes",
        ),
        pa.Check(
            lambda df: df["trimestre"].eq(df["anio_mes"].dt.quarter),
            name="trimestre_coincide_con_anio_mes",
        ),
        pa.Check(
            lambda df: df["semestre"].eq((df["anio_mes"].dt.month - 1) // 6 + 1),
            name="semestre_coincide_con_anio_mes",
        ),
        pa.Check(
            lambda df: (
                df["precio_min"] <= df["precio_frec_media"] + 0.01
            ) & (df["precio_frec_media"] <= df["precio_max"] + 0.01),
            name="rango_precios_con_tolerancia_de_centavo",
        ),
        pa.Check(
            lambda df: df["n_atipicos"] <= df["n_cotizaciones"],
            name="atipicos_no_superan_cotizaciones",
        ),
        pa.Check(
            lambda df: df["anio_dato_siap"] <= df["anio"],
            name="anio_dato_siap_no_es_futuro",
        ),
    ],
    strict=True,
    coerce=True,
)


def validar_dataframe(datos, esquema):
    """Separa filas válidas e inválidas y asocia a cada inválida sus fallos."""
    datos = datos.reset_index(drop=True).copy()
    try:
        validos = esquema.validate(datos, lazy=True)
        return validos.reset_index(drop=True), datos.iloc[0:0].copy()
    except pa.errors.SchemaErrors as error:
        fallos = error.failure_cases
        motivos_por_fila = {}
        motivos_globales = []
        for fila in fallos.itertuples(index=False):
            indice = getattr(fila, "index", None)
            columna = getattr(fila, "column", None)
            comprobacion = getattr(fila, "check", None)
            contexto = getattr(fila, "schema_context", None)
            if contexto == "DataFrameSchema":
                motivo = str(comprobacion)
            else:
                motivo = f"{columna}: {comprobacion}" if columna else str(comprobacion)
            if pd.isna(indice):
                motivos_globales.append(motivo)
            else:
                motivos_por_fila.setdefault(int(indice), set()).add(motivo)

        if motivos_globales:
            globales = "; ".join(sorted(set(motivos_globales)))
            for indice in datos.index:
                motivos_por_fila.setdefault(indice, set()).add(
                    f"Error de esquema: {globales}"
                )
        if not motivos_por_fila:
            raise ValueError(
                "Pandera encontró un error que no se pudo asociar a filas; "
                "se detuvo la validación para evitar perder registros."
            ) from error

        indices_invalidos = sorted(motivos_por_fila)
        indices_validos = [i for i in datos.index if i not in motivos_por_fila]
        invalidos = datos.loc[indices_invalidos].copy()
        invalidos["motivo"] = [
            "; ".join(sorted(motivos_por_fila[i])) for i in indices_invalidos
        ]
        if indices_validos:
            validos = esquema.validate(datos.loc[indices_validos], lazy=True)
        else:
            validos = datos.iloc[0:0].copy()
        return validos.reset_index(drop=True), invalidos.reset_index(drop=True)
    except pa.errors.SchemaError as error:
        invalidos = datos.copy()
        invalidos["motivo"] = f"Error de esquema: {error}"
        return datos.iloc[0:0].copy(), invalidos


def _guardar_cuarentena(invalidos, fuente, ruta):
    if invalidos.empty:
        return

    cuarentena = invalidos.copy()
    cuarentena.insert(0, "fuente", fuente)
    cuarentena.insert(1, "fecha_cuarentena", datetime.now(timezone.utc).isoformat())
    hashes = pd.util.hash_pandas_object(invalidos.drop(columns="motivo"), index=False)
    cuarentena.insert(
        2,
        "registro_id",
        [
            hashlib.sha256(f"{fuente}:{pos}:{h}".encode("utf-8")).hexdigest()
            for pos, h in enumerate(hashes)
        ],
    )

    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        anterior = pd.read_csv(ruta)
        cuarentena = pd.concat([anterior, cuarentena], ignore_index=True)
        cuarentena = cuarentena.drop_duplicates(subset="registro_id", keep="first")
    cuarentena.to_csv(ruta, index=False)


def validar_archivo(entrada, salida, cuarentena, esquema, fuente):
    """Valida un Parquet, guarda válidos e incorpora los inválidos a cuarentena."""
    entrada = Path(entrada)
    salida = Path(salida)
    datos = pd.read_parquet(entrada)
    validos, invalidos = validar_dataframe(datos, esquema)

    salida.parent.mkdir(parents=True, exist_ok=True)
    validos.to_parquet(salida, index=False)
    ruta_cuarentena = Path(cuarentena) / f"{fuente}.csv"
    _guardar_cuarentena(invalidos, fuente, ruta_cuarentena)

    entrada_filas = len(datos)
    filas_validas = len(validos)
    filas_cuarentena = len(invalidos)
    if entrada_filas != filas_validas + filas_cuarentena:
        raise RuntimeError(
            f"Conservación de filas incumplida para {fuente}: "
            f"{entrada_filas} != {filas_validas} + {filas_cuarentena}"
        )
    print(
        f"{fuente}: entraron {entrada_filas} filas, "
        f"pasaron {filas_validas}, cuarentena {filas_cuarentena} "
        f"(total conservado: {filas_validas + filas_cuarentena})."
    )
    return entrada_filas, filas_validas, filas_cuarentena


def validar_archivos(plata=PLATA, cuarentena=CUARENTENA):
    """Ejecuta la Puerta de Calidad sobre los dos productos Plata requeridos."""
    plata = Path(plata)
    cuarentena = Path(cuarentena)
    return [
        validar_archivo(
            plata / "sniim_diario_homologado.parquet",
            plata / "sniim_diario_validado.parquet",
            cuarentena,
            ESQUEMA_SNIIM,
            "sniim_diario",
        ),
        validar_archivo(
            plata / "integrado_reducido.parquet",
            plata / "integrado_reducido_validado.parquet",
            cuarentena,
            ESQUEMA_INTEGRADO,
            "integrado_reducido",
        ),
    ]


if __name__ == "__main__":
    validar_archivos()
