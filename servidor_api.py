# archivo: servidor_api.py
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from motor_astar import (
    desviar_a_refugio_mas_seguro,
    ejecutar_astar_optimo,
    normalizar_longitud,
    obtener_nomenclatura_marte_bd,
    obtener_obstaculos_topograficos_bd,
    obtener_parametros_atmosfericos_bd,
    obtener_perfiles_regionales_bd,
    obtener_zonas_exploracion_bd,
    obtener_zonas_seguras_auxiliares_bd,
)

DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))


class ServidorBackend(BaseHTTPRequestHandler):
    def _enviar_json(self, datos, codigo_http=200):
        respuesta = json.dumps(datos, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo_http)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(respuesta)

    def do_OPTIONS(self):
        self._enviar_json({"estado": "ok"}, 200)

    def do_GET(self):
        ruta_limpia = self.path.split("?")[0]
        if ruta_limpia in ("/", "/Archivo1.html", "/Archivo1.HTML"):
            with open("Archivo1.html", "rb") as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(contenido)
            return

        if ruta_limpia in ("/Vista_Dispositivos.html", "/simulador"):
            with open("Vista_Dispositivos.html", "rb") as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(contenido)
            return

        if ruta_limpia == "/api/datos-mapa":
            zonas = obtener_zonas_exploracion_bd()
            for z in zonas:
                if z.get("lon_central") is not None:
                    z["lon_central_mapa"] = normalizar_longitud(z["lon_central"])

            obstaculos = obtener_obstaculos_topograficos_bd()
            zonas_aux = obtener_zonas_seguras_auxiliares_bd()
            atmosfera = obtener_parametros_atmosfericos_bd()
            perfiles_json = obtener_perfiles_regionales_bd()
            nomenclatura = obtener_nomenclatura_marte_bd()

            self._enviar_json({
                "estado": "ok",
                "zonas_exploracion": zonas,
                "zonas_seguras_auxiliares": zonas_aux,
                "obstaculos_topograficos": obstaculos,
                "perfiles_regionales": perfiles_json,
                "parametros_atmosfericos": atmosfera,
                "nomenclatura": nomenclatura,
            }, 200)
            return

        # Servir archivos estaticos locales (ej. horizon_logo.png para la cortinilla)
        nombre_archivo = os.path.basename(ruta_limpia.lstrip("/"))
        ruta_local = os.path.join(DIRECTORIO_BASE, nombre_archivo)
        if nombre_archivo and os.path.isfile(ruta_local):
            tipo_mime, _ = mimetypes.guess_type(ruta_local)
            with open(ruta_local, "rb") as f:
                contenido_bin = f.read()
            self.send_response(200)
            self.send_header("Content-Type", tipo_mime or "application/octet-stream")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(contenido_bin)
            return

        self._enviar_json({"estado": "error", "mensaje": "Endpoint GET no encontrado"}, 404)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(largo).decode("utf-8") if largo > 0 else "{}"
        datos_entrada = json.loads(cuerpo)

        # ------------------------------------------------------------------
        # ENDPOINT 1: Calcular la Ruta Más Óptima (A* con riesgos y obstáculos)
        # ------------------------------------------------------------------
        if self.path == "/api/ruta-optima":
            try:
                origen = datos_entrada.get("origen", "arcadia_planitia")
                destino = datos_entrada.get("destino", "hellas_planitia")
                hay_tormenta = bool(datos_entrada.get("tormenta_activa", False))

                resultado = ejecutar_astar_optimo(
                    id_inicio=origen,
                    id_destino=destino,
                    boton_tormenta_activo=hay_tormenta,
                )
                self._enviar_json({"estado": "ok", "datos": resultado}, 200)
            except Exception as error:
                self._enviar_json({"estado": "error", "mensaje": str(error)}, 400)
            return

        # ------------------------------------------------------------------
        # ENDPOINT 2: Botón de Emergencia por Tormenta de Polvo
        # ------------------------------------------------------------------
        if self.path == "/api/emergencia-tormenta":
            try:
                posicion_actual = datos_entrada.get("nodo_actual", "hellas_planitia")
                plan_escape = desviar_a_refugio_mas_seguro(posicion_actual)
                self._enviar_json({
                    "estado": "alerta_tormenta_activa",
                    "plan_de_escape": plan_escape,
                }, 200)
            except Exception as error:
                self._enviar_json({"estado": "error", "mensaje": str(error)}, 400)
            return

        self._enviar_json({"estado": "error", "mensaje": "Endpoint POST no encontrado"}, 404)


if __name__ == "__main__":
    puerto = 8000
    print(f"Servidor de telemetría y ruteo A* corriendo en http://localhost:{puerto}")
    servidor = HTTPServer(("0.0.0.0", puerto), ServidorBackend)
    servidor.serve_forever()
