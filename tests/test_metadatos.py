import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.metadatos import generar_metadatos


class GenerarMetadatosTests(unittest.TestCase):
    def setUp(self):
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.raiz_bronce = Path(self.directorio_temporal.name)

    def tearDown(self):
        self.directorio_temporal.cleanup()

    def test_generates_sidecar_with_raw_file_hash_and_size(self):
        archivo = self.raiz_bronce / "siap" / "municipal" / "cierre_2025.csv.gz"
        archivo.parent.mkdir(parents=True)
        contenido = b"\x1f\x8braw compressed bytes"
        archivo.write_bytes(contenido)

        generados = generar_metadatos(self.raiz_bronce)

        self.assertEqual(generados, [archivo.with_name(archivo.name + ".metadata.json")])
        datos = json.loads(generados[0].read_text(encoding="utf-8"))
        self.assertEqual(datos, {
            "archivo": "siap/municipal/cierre_2025.csv.gz",
            "bytes": len(contenido),
            "algoritmo": "SHA-256",
            "sha256": hashlib.sha256(contenido).hexdigest(),
        })

    def test_omits_capture_support_files_and_existing_sidecars(self):
        (self.raiz_bronce / "lote.html").write_bytes(b"<html/>")
        (self.raiz_bronce / "_bitacora.csv").write_text("sha256\n", encoding="utf-8")
        (self.raiz_bronce / "_robots_20261107.txt").write_text("User-agent: *", encoding="utf-8")
        (self.raiz_bronce / ".gitkeep").touch()

        primera_generacion = generar_metadatos(self.raiz_bronce)
        segunda_generacion = generar_metadatos(self.raiz_bronce)

        self.assertEqual(len(primera_generacion), 1)
        self.assertEqual(primera_generacion, segunda_generacion)
        self.assertEqual(len(list(self.raiz_bronce.rglob("*.metadata.json"))), 1)

    def test_updates_metadata_when_raw_file_changes(self):
        archivo = self.raiz_bronce / "lote.html"
        archivo.write_bytes(b"primera version")
        metadato = generar_metadatos(self.raiz_bronce)[0]
        archivo.write_bytes(b"segunda version")

        generar_metadatos(self.raiz_bronce)

        datos = json.loads(metadato.read_text(encoding="utf-8"))
        self.assertEqual(datos["sha256"], hashlib.sha256(b"segunda version").hexdigest())
        self.assertEqual(datos["bytes"], len(b"segunda version"))


if __name__ == "__main__":
    unittest.main()
