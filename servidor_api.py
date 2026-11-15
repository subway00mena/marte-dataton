# archivo: servidor_api.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from motor_astar import (
    desviar_a_refugio_mas_seguro,
    ejecutar_astar_optimo,
    normalizar_longitud,
    obtener_obstaculos_topograficos_bd,
    obtener_parametros_atmosfericos_bd,
    obtener_perfiles_regionales_bd,
    obtener_zonas_exploracion_bd,
)


def leer_archivo_html(nombres_posibles):
  base_dir = os.path.dirname(os.path.abspath(__file__))
  for nombre in nombres_posibles:
    ruta = os.path.join(base_dir, nombre)
    if os.path.exists(ruta):
      with open(ruta, "rb") as f:
        return f.read()
  # Búsqueda insensible a mayúsculas/minúsculas en Linux
  archivos_actuales = os.listdir(base_dir)
  for nombre in nombres_posibles:
    for real in archivos_actuales:
      if real.lower() == nombre.lower():
        with open(os.path.join(base_dir, real), "rb") as f:
          return f.read()
  raise FileNotFoundError(f"No se encontró ninguno de: {nombres_posibles}")


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
    if ruta_limpia in ("/", "/index.html", "/Archivo1.html", "/Archivo1.HTML"):
      contenido = leer_archivo_html(
          ["Archivo1.html", "Archivo1.HTML", "Archivo1"]
      )
      self.send_response(200)
      self.send_header("Content-Type", "text/html; charset=utf-8")
      self.end_headers()
      self.wfile.write(contenido)
      return

    if ruta_limpia in (
        "/Vista_Dispositivos.html",
        "/Vista_Dispositivos.HTML",
        "/simulador",
    ):
      contenido = leer_archivo_html([
          "Vista_Dispositivos.html",
          "Vista_Dispositivos.HTML",
          "Vista_Dispositivos",
      ])
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
      atmosfera = obtener_parametros_atmosfericos_bd()
      perfiles_json = obtener_perfiles_regionales_bd()

      self._enviar_json(
          {
              "estado": "ok",
              "zonas_exploracion": zonas,
              "obstaculos_topograficos": obstaculos,
              "perfiles_regionales": perfiles_json,
              "parametros_atmosfericos": atmosfera,
          },
          200,
      )
      return

    self._enviar_json(
        {"estado": "error", "mensaje": "Endpoint GET no encontrado"}, 404
    )

  def do_POST(self):
    largo = int(self.headers.get("Content-Length", 0))
    cuerpo = self.rfile.read(largo).decode("utf-8") if largo > 0 else "{}"
    datos_entrada = json.loads(cuerpo)

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

    if self.path == "/api/emergencia-tormenta":
      try:
        posicion_actual = datos_entrada.get("nodo_actual", "hellas_planitia")
        plan_escape = desviar_a_refugio_mas_seguro(posicion_actual)
        self._enviar_json(
            {
                "estado": "alerta_tormenta_activa",
                "plan_de_escape": plan_escape,
            },
            200,
        )
      except Exception as error:
        self._enviar_json({"estado": "error", "mensaje": str(error)}, 400)
      return

    self._enviar_json(
        {"estado": "error", "mensaje": "Endpoint POST no encontrado"}, 404
    )


if __name__ == "__main__":
  puerto = int(os.environ.get("PORT", 8000))
  print(
      f"Servidor de telemetría y ruteo A* corriendo en"
      f" http://0.0.0.0:{puerto}"
  )
  servidor = HTTPServer(("0.0.0.0", puerto), ServidorBackend)
  servidor.serve_forever()