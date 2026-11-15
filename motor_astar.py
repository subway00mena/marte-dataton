# archivo: motor_astar.py
import heapq
import json
import math
import os
import sqlite3

RUTA_BASE_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marte_telemetria.db")


# ==============================================================================
# SECCIÓN 1: DATOS OFICIALES PULIDOS (EXCEL 1.2 + REGIONAL_RISK_RESULTS JSON)
# ==============================================================================

UBICACIONES_PRINCIPALES_SEMILLA = [
    {
        "id_ubicacion": "arcadia_planitia",
        "nombre": "Arcadia Planitia",
        "subregion": "Planicie central",
        "clasificacion_excel": "Zona segura (campamento)",
        "tipo_zona": "segura",
        "es_refugio": 1,
        "lat_central": 47.19124055,
        "lon_central": -175.6891,
        "diametro_km": 1871.97,
        "temperatura_valor_k": 200.0,
        "temperatura_min_k": 150.0,
        "temperatura_max_k": 260.0,
        "temperatura_confianza": "medium",
        "temperatura_notas": "Temperatura superficial (skin temperature) radiometrica, NO temperatura del aire. En invierno boreal alcanza el punto de escarcha de CO2 (~150 K).",
        "presion_valor_pa": 840.0,
        "presion_min_pa": 750.0,
        "presion_max_pa": 950.0,
        "presion_confianza": "medium",
        "presion_notas": "Estimacion derivada/recuperada (NO existe barometro in situ en Arcadia). Alta densidad relativa que favorece paracaidas y desaceleracion supersonica.",
        "polvo_clase": "moderate_to_high_northern_storm_track",
        "polvo_susceptibilidad_atm": "moderate_to_high",
        "polvo_deposicion_sup": "not_quantified",
        "polvo_confianza": "qualitative_only",
        "polvo_notas": "Susceptibilidad Moderada-Alta (Corredor de secuencias frontales del norte; Ls 180-360 deg).",
        "elevacion_valor_m": -3800.0,
        "elevacion_min_m": -4500.0,
        "elevacion_max_m": -3000.0,
        "elevacion_confianza": "high",
        "elevacion_notas": "Elevacion medida directamente respecto al areoide de referencia MOLA. Ideal para frenado atmosferico EDL.",
        "pendiente_valor_grados": 0.3,
        "pendiente_min_grados": 0.1,
        "pendiente_max_grados": 0.5,
        "pendiente_confianza": "high",
        "pendiente_notas": "Pendiente regional muy baja en MOLA (<0.5 deg). HiRISE muestra texturas periglaciares y crateres secundarios sub-metricos.",
        "riesgos_principales_json": json.dumps([
            "Temperaturas superficiales invernales extremas (~150 K) con deposicion estacional de escarcha de CO2/H2O",
            "Paso frecuente de secuencias de tormentas de polvo baroclinicas (Arcadia storm track en MDAD, Ls 180-360 deg)",
            "Terreno periglaciar con poligonos de contraccion termica y crateres secundarios sub-metricos no resueltos por MOLA"
        ], ensure_ascii=False),
        "limitaciones_json": json.dumps([
            "Ausencia de estacion meteorologica in situ (presion y temperatura provienen de teledeteccion orbital THEMIS/MCS y modelos)",
            "Falta un valor numerico unico estandarizado de opacidad optica de polvo (tau) co-temporal con las demas regiones; por Regla 12 no se calcula un ERI definitivo"
        ], ensure_ascii=False),
        "prob_peligro_base": 0.03,
    },
    {
        "id_ubicacion": "olympus_mons",
        "nombre": "Olympus Mons",
        "subregion": "Escarpe basal, flancos de escudo y calderas somitales (Base / Laderas / Cima)",
        "clasificacion_excel": "Zona montañosa",
        "tipo_zona": "peligrosa",
        "es_refugio": 0,
        "lat_central": 18.40196418,
        "lon_central": -133.5645,
        "diametro_km": 1914.77,
        "temperatura_valor_k": 190.0,
        "temperatura_min_k": 130.0,
        "temperatura_max_k": 270.0,
        "temperatura_confianza": "low_to_medium",
        "temperatura_notas": "Base: ~205 K estimado (rango 150-270 K, confianza baja); Laderas: 190 K (135-265 K, confianza media); Cima: 185 K (130-260 K, amplitud diurna >120 K).",
        "presion_valor_pa": 560.0,
        "presion_min_pa": 30.0,
        "presion_max_pa": 680.0,
        "presion_confianza": "medium",
        "presion_notas": "Base: 560 Pa (450-680 Pa); Laderas: 180 Pa (100-350 Pa); Cima: 50 Pa (30-72 Pa, cuasi-vacio operacional).",
        "polvo_clase": "moderate_orographic_base_circulation_and_dust_mantle",
        "polvo_susceptibilidad_atm": "moderate_base_to_very_low_summit",
        "polvo_deposicion_sup": "high_susceptibility",
        "polvo_confianza": "qualitative_only",
        "polvo_notas": "Baja opacidad de columna en altura, pero grueso manto superficial de polvo fino propenso a avalanchas secas (slope streaks) y hundimiento mecanico.",
        "elevacion_valor_m": 250.0,
        "elevacion_min_m": -2500.0,
        "elevacion_max_m": 21229.0,
        "elevacion_confianza": "high",
        "elevacion_notas": "Base: 250 m (-2500 a 6000 m); Laderas: 13000 m (6000 a 20000 m); Cima: 21229 m (18000 a 21229 m, punto mas alto de Marte).",
        "pendiente_valor_grados": 20.0,
        "pendiente_min_grados": 1.5,
        "pendiente_max_grados": 45.0,
        "pendiente_confianza": "high",
        "pendiente_notas": "Escarpe basal: 20 deg (15-35 deg); Laderas: 5 deg (4-7 deg); Cima: piso 1.5 deg y paredes de caldera 20-45 deg.",
        "riesgos_principales_json": json.dumps([
            "Pendientes topograficas extremas en el escarpe basal (15 a 35 deg, localmente >40 deg) con desniveles de 4 a 8 km",
            "Elevacion en laderas y cima (+6 a +21.2 km) y baja presion (30-350 Pa) con maxima exposicion a radiacion y desgaste de soporte vital",
            "Manto superficial grueso de polvo fino propenso a avalanchas secas (slope streaks), canales de lava y oscilaciones termicas diurnas >120 K"
        ], ensure_ascii=False),
        "limitaciones_json": json.dumps([
            "Fuerte heterogeneidad altitudinal (-2,500 m en base a +21,229 m en cima) impide usar un valor unico de presion o temperatura sin definir subsector puntual",
            "Presion estimada por escala hidrostatica, no medida in situ; el riesgo dominante de polvo es superficial (manto fino y slope streaks)"
        ], ensure_ascii=False),
        "prob_peligro_base": 0.82,
    },
    {
        "id_ubicacion": "hellas_planitia",
        "nombre": "Hellas Planitia",
        "subregion": "Piso interior de la cuenca",
        "clasificacion_excel": "Zona peligrosa",
        "tipo_zona": "peligrosa",
        "es_refugio": 0,
        "lat_central": -42.43011121,
        "lon_central": 70.5025,
        "diametro_km": 2299.16,
        "temperatura_valor_k": 205.0,
        "temperatura_min_k": 145.0,
        "temperatura_max_k": 285.0,
        "temperatura_confianza": "medium",
        "temperatura_notas": "Temperatura superficial (skin). Fuerte asimetria estacional: veranos australes calidos e inviernos largos con escarcha de CO2.",
        "presion_valor_pa": 1050.0,
        "presion_min_pa": 950.0,
        "presion_max_pa": 1240.0,
        "presion_confianza": "medium",
        "presion_notas": "Presion superficial mas alta de Marte (~11.5 a 12.4 mbar max en el fondo de la cuenca, >2x el datum de 610 Pa).",
        "polvo_clase": "critical_primary_dust_source_and_optical_trap",
        "polvo_susceptibilidad_atm": "very_high",
        "polvo_deposicion_sup": "high_susceptibility",
        "polvo_confianza": "qualitative_only",
        "polvo_notas": "Susceptibilidad Critica / Maxima (Fuente primaria de tormentas regionales y globales; Ls 180-330 deg).",
        "elevacion_valor_m": -7152.0,
        "elevacion_min_m": -8200.0,
        "elevacion_max_m": -5000.0,
        "elevacion_confianza": "high",
        "elevacion_notas": "Contiene el punto topografico mas bajo de todo Marte (-8200 m respecto al areoide MOLA).",
        "pendiente_valor_grados": 0.8,
        "pendiente_min_grados": 0.3,
        "pendiente_max_grados": 1.5,
        "pendiente_confianza": "high",
        "pendiente_notas": "Piso central con pendiente baja (<1.5 deg), pero paredes del anillo >10-20 deg y unidades de flujo viscoso (banded terrain).",
        "riesgos_principales_json": json.dumps([
            "Riesgo critico de tormentas de polvo locales, regionales y precursores de eventos globales (PEDEs) en primavera/verano austral (Ls 180-330 deg)",
            "Acumulacion extrema de opacidad optica en la columna atmosferica profunda, bloqueando la radiacion solar para sistemas fotovoltaicos",
            "Rugosidad geomorfologica local compleja en unidades de flujo viscoso (banded terrain) y campos de dunas"
        ], ensure_ascii=False),
        "limitaciones_json": json.dumps([
            "Sin aterrizadores ni mediciones meteorologicas in situ en el piso de la cuenca",
            "Durante tormentas intensas, la alta opacidad de polvo degrada las recuperaciones orbitales de temperatura y presion superficial cerca del suelo"
        ], ensure_ascii=False),
        "prob_peligro_base": 0.88,
    },
    {
        "id_ubicacion": "utopia_planitia",
        "nombre": "Utopia Planitia",
        "subregion": "Cuenca media-norte",
        "clasificacion_excel": "Zona de exploración",
        "tipo_zona": "segura",
        "es_refugio": 1,
        "lat_central": 46.73628499,
        "lon_central": 117.5168,
        "diametro_km": 3560.45,
        "temperatura_valor_k": 200.0,
        "temperatura_min_k": 150.0,
        "temperatura_max_k": 265.0,
        "temperatura_confianza": "high",
        "temperatura_notas": "VL2 midio T atmosferica a 1.5 m (~150 K min invernal a ~245 K max); THEMIS mide T superficial hasta ~265 K en verano.",
        "presion_valor_pa": 880.0,
        "presion_min_pa": 730.0,
        "presion_max_pa": 1080.0,
        "presion_confianza": "high",
        "presion_notas": "UNICA medicion barometrica directa in situ entre las regiones (Viking Lander 2: 730 a 1080 Pa).",
        "polvo_clase": "high_seasonal_utopia_storm_track",
        "polvo_susceptibilidad_atm": "high_seasonal",
        "polvo_deposicion_sup": "not_quantified",
        "polvo_confianza": "qualitative_only",
        "polvo_notas": "Susceptibilidad Alta estacional (Rutas frontales del borde polar norte y corredor Utopia; Ls 140-250 y 300-360 deg).",
        "elevacion_valor_m": -4300.0,
        "elevacion_min_m": -5000.0,
        "elevacion_max_m": -3500.0,
        "elevacion_confianza": "high",
        "elevacion_notas": "Elevacion medida por altimetria laser MOLA (VL2: -4460 m; Zhurong: -4099 m).",
        "pendiente_valor_grados": 0.3,
        "pendiente_min_grados": 0.1,
        "pendiente_max_grados": 0.5,
        "pendiente_confianza": "high",
        "pendiente_notas": "Pendiente regional MOLA <0.5 deg, pero en Viking 2 el ~16% de la superficie esta cubierta por bloques rocosos.",
        "riesgos_principales_json": json.dumps([
            "Alta densidad local de bloques rocosos (~16% de cobertura de rocas en Viking 2) invisible a la resolucion regional de MOLA",
            "Corredor activo de tormentas frontales de polvo del borde polar norte (Utopia storm track en MDAD)",
            "Frio invernal severo (~150 K) con condensacion superficial de escarcha"
        ], ensure_ascii=False),
        "limitaciones_json": json.dumps([
            "Las mediciones in situ de Viking Lander 2 (1976-1980) son puntuales y no representan uniformemente toda la cuenca de 3,300 km",
            "Variable de polvo expresada como susceptibilidad categorica MDAD; se mantiene eri: null hasta estandarizar tau optico cuantitativo"
        ], ensure_ascii=False),
        "prob_peligro_base": 0.05,
    },
]

PERFILES_REGIONALES_JSON_SEMILLA = [
    {
        "id_perfil": "arcadia_planitia",
        "region": "Arcadia Planitia",
        "subregion": "Planicie central",
        "ubicacion_asociada": "arcadia_planitia",
        "temperatura_k": 200.0,
        "temperatura_rango_k": "150.0 - 260.0",
        "temperatura_confianza": "medium",
        "presion_pa": 840.0,
        "presion_rango_pa": "750.0 - 950.0",
        "presion_confianza": "medium",
        "elevacion_m": -3800.0,
        "elevacion_rango_m": "-4500.0 a -3000.0",
        "elevacion_confianza": "high",
        "pendiente_grados": 0.3,
        "pendiente_rango_grados": "0.1 - 0.5",
        "pendiente_confianza": "high",
        "polvo_clase": "moderate_to_high_northern_storm_track",
        "polvo_susceptibilidad": "moderate_to_high",
        "polvo_confianza": "qualitative_only",
        "riesgos_principales": [
            "Temperaturas superficiales invernales extremas (~150 K) con deposicion estacional de escarcha de CO2/H2O",
            "Paso frecuente de secuencias de tormentas de polvo baroclinicas (Arcadia storm track en MDAD, Ls 180-360 deg)",
            "Terreno periglaciar con poligonos de contraccion termica y crateres secundarios sub-metricos no resueltos por MOLA"
        ],
        "limitaciones": [
            "Ausencia de estacion meteorologica in situ (presion y temperatura provienen de teledeteccion orbital THEMIS/MCS y modelos)",
            "Falta un valor numerico unico estandarizado de opacidad optica de polvo (tau) co-temporal con las demas regiones; por Regla 12 no se calcula un ERI definitivo"
        ],
    },
    {
        "id_perfil": "utopia_planitia",
        "region": "Utopia Planitia",
        "subregion": "Cuenca media-norte",
        "ubicacion_asociada": "utopia_planitia",
        "temperatura_k": 200.0,
        "temperatura_rango_k": "150.0 - 265.0",
        "temperatura_confianza": "high",
        "presion_pa": 880.0,
        "presion_rango_pa": "730.0 - 1080.0",
        "presion_confianza": "high",
        "elevacion_m": -4300.0,
        "elevacion_rango_m": "-5000.0 a -3500.0",
        "elevacion_confianza": "high",
        "pendiente_grados": 0.3,
        "pendiente_rango_grados": "0.1 - 0.5",
        "pendiente_confianza": "high",
        "polvo_clase": "high_seasonal_utopia_storm_track",
        "polvo_susceptibilidad": "high_seasonal",
        "polvo_confianza": "qualitative_only",
        "riesgos_principales": [
            "Alta densidad local de bloques rocosos (~16% de cobertura de rocas en Viking 2) invisible a la resolucion regional de MOLA",
            "Corredor activo de tormentas frontales de polvo del borde polar norte (Utopia storm track en MDAD)",
            "Frio invernal severo (~150 K) con condensacion superficial de escarcha"
        ],
        "limitaciones": [
            "Las mediciones in situ de Viking Lander 2 (1976-1980) son puntuales y no representan uniformemente toda la cuenca de 3,300 km",
            "Variable de polvo expresada como susceptibilidad categorica MDAD; se mantiene eri: null hasta estandarizar tau optico cuantitativo"
        ],
    },
    {
        "id_perfil": "hellas_planitia",
        "region": "Hellas Planitia",
        "subregion": "Piso interior de la cuenca",
        "ubicacion_asociada": "hellas_planitia",
        "temperatura_k": 205.0,
        "temperatura_rango_k": "145.0 - 285.0",
        "temperatura_confianza": "medium",
        "presion_pa": 1050.0,
        "presion_rango_pa": "950.0 - 1240.0",
        "presion_confianza": "medium",
        "elevacion_m": -7152.0,
        "elevacion_rango_m": "-8200.0 a -5000.0",
        "elevacion_confianza": "high",
        "pendiente_grados": 0.8,
        "pendiente_rango_grados": "0.3 - 1.5",
        "pendiente_confianza": "high",
        "polvo_clase": "critical_primary_dust_source_and_optical_trap",
        "polvo_susceptibilidad": "very_high",
        "polvo_confianza": "qualitative_only",
        "riesgos_principales": [
            "Riesgo critico de tormentas de polvo locales, regionales y precursores de eventos globales (PEDEs) en primavera/verano austral (Ls 180-330 deg)",
            "Acumulacion extrema de opacidad optica en la columna atmosferica profunda, bloqueando la radiacion solar para sistemas fotovoltaicos",
            "Rugosidad geomorfologica local compleja en unidades de flujo viscoso (banded terrain) y campos de dunas"
        ],
        "limitaciones": [
            "Sin aterrizadores ni mediciones meteorologicas in situ en el piso de la cuenca",
            "Durante tormentas intensas, la alta opacidad de polvo degrada las recuperaciones orbitales de temperatura y presion superficial cerca del suelo"
        ],
    },
    {
        "id_perfil": "olympus_mons_base",
        "region": "Olympus Mons — Base",
        "subregion": "Escarpe basal y pie perimetral",
        "ubicacion_asociada": "olympus_mons",
        "temperatura_k": None,
        "temperatura_rango_k": "150.0 - 270.0 (~205 K est.)",
        "temperatura_confianza": "low",
        "presion_pa": 560.0,
        "presion_rango_pa": "450.0 - 680.0",
        "presion_confianza": "medium",
        "elevacion_m": 250.0,
        "elevacion_rango_m": "-2500.0 a 6000.0",
        "elevacion_confianza": "high",
        "pendiente_grados": 20.0,
        "pendiente_rango_grados": "15.0 - 35.0",
        "pendiente_confianza": "high",
        "polvo_clase": "moderate_orographic_base_circulation_and_dust_mantle",
        "polvo_susceptibilidad": "moderate",
        "polvo_confianza": "qualitative_only",
        "riesgos_principales": [
            "Pendientes topograficas extremas en el escarpe basal (15 a 35 deg, localmente >40 deg) con desniveles de 4 a 8 km",
            "Terreno caotico de grandes deslizamientos gravitacionales y bloques en la aureola proximal",
            "Fuertes gradientes de viento catabatico/orografico y manto de polvo suelto de baja inercia termica"
        ],
        "limitaciones": [
            "Fuerte heterogeneidad altitudinal (-2,500 m a +6,000 m en pocos kilometros) impide usar un valor unico de presion o temperatura sin definir un sitio de aterrizaje puntual",
            "Datos termicos específicos del anillo del escarpe basal requieren procesamiento zonal directo de granulos THEMIS RDR"
        ],
    },
]

ZONAS_OBSTACULOS_SEMILLA = [
    {
        "id_obstaculo": "lycus_sulci",
        "nombre": "Lycus Sulci",
        "lat_central": 28.14044343,
        "lon_central": -144.4701,
        "diametro_km": 1350.61,
        "tipo_riesgo": "Zona deslaves (slope streaks y polvo fino DCI < 0.93)",
        "accion_requerida": "Precaucion",
        "pendiente_estimada_grados": 15.0,
        "prob_accidente": 0.65,
    },
    {
        "id_obstaculo": "erebus_montes",
        "nombre": "Erebus Montes",
        "lat_central": 35.66126179,
        "lon_central": -174.9771,
        "diametro_km": 811.667,
        "tipo_riesgo": "Zona montañosa",
        "accion_requerida": "Esquivar",
        "pendiente_estimada_grados": 22.0,
        "prob_accidente": 0.92,
    },
    {
        "id_obstaculo": "acheron_fossae",
        "nombre": "Acheron Fossae",
        "lat_central": 38.27416563,
        "lon_central": -135.0238,
        "diametro_km": 703.111,
        "tipo_riesgo": "Zona de fracturas (escarpes graben y horst)",
        "accion_requerida": "Precaucion",
        "pendiente_estimada_grados": 20.0,
        "prob_accidente": 0.68,
    },
    {
        "id_obstaculo": "olympus_mons_obstaculo",
        "nombre": "Olympus Mons",
        "lat_central": 18.40196418,
        "lon_central": -133.5645,
        "diametro_km": 1914.77,
        "tipo_riesgo": "Zona montañosa",
        "accion_requerida": "Esquivar",
        "pendiente_estimada_grados": 20.0,
        "prob_accidente": 0.95,
    },
    {
        "id_obstaculo": "valles_marineris",
        "nombre": "Valles Marineris",
        "lat_central": -14.00586857,
        "lon_central": -58.5877,
        "diametro_km": 3761.28,
        "tipo_riesgo": "Zona peligrosa",
        "accion_requerida": "Esquivar",
        "pendiente_estimada_grados": 25.0,
        "prob_accidente": 0.94,
    },
    {
        "id_obstaculo": "noctis_labyrinthus",
        "nombre": "Noctis Labyrinthus",
        "lat_central": -6.362483392,
        "lon_central": -101.1889,
        "diametro_km": 1190.31,
        "tipo_riesgo": "Zona peligrosa",
        "accion_requerida": "Esquivar",
        "pendiente_estimada_grados": 22.0,
        "prob_accidente": 0.91,
    },
]

PARAMETROS_FISIOLOGICOS_ATMOSFERA = {
    "id_registro": 1,
    "temperatura_nominal_c": -73.15,
    "temperatura_tormenta_c": -123.15,
    "presion_nominal_pa": 840.0,
    "gravedad_ms2": 3.711,
    "prob_tormenta_arena_base": 0.12,
    "prob_tormenta_emergencia": 0.85,
    "tasa_oxigeno_base_l_hora": 52.0,
    "consumo_energia_base_kwh_km": 1.15,
    "velocidad_base_rover_kmh": 4.5,
}


def inicializar_base_datos_sqlite():
    """
    Crea y sincroniza la base de datos SQLite marte_telemetria.db con las
    4 ubicaciones principales, las 4 zonas de obstáculos y los 6 perfiles regionales.
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    cursor = conexion.cursor()

    cursor.execute("DROP TABLE IF EXISTS ubicaciones_principales")
    cursor.execute("DROP TABLE IF EXISTS zonas_obstaculos")
    cursor.execute("DROP TABLE IF EXISTS perfiles_regionales_json")
    cursor.execute("DROP TABLE IF EXISTS parametros_atmosfericos")

    cursor.execute("""
        CREATE TABLE ubicaciones_principales (
            id_ubicacion TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            subregion TEXT,
            clasificacion_excel TEXT,
            tipo_zona TEXT,
            es_refugio INTEGER,
            lat_central REAL,
            lon_central REAL,
            diametro_km REAL,
            temperatura_valor_k REAL,
            temperatura_min_k REAL,
            temperatura_max_k REAL,
            temperatura_confianza TEXT,
            temperatura_notas TEXT,
            presion_valor_pa REAL,
            presion_min_pa REAL,
            presion_max_pa REAL,
            presion_confianza TEXT,
            presion_notas TEXT,
            polvo_clase TEXT,
            polvo_susceptibilidad_atm TEXT,
            polvo_deposicion_sup TEXT,
            polvo_confianza TEXT,
            polvo_notas TEXT,
            elevacion_valor_m REAL,
            elevacion_min_m REAL,
            elevacion_max_m REAL,
            elevacion_confianza TEXT,
            elevacion_notas TEXT,
            pendiente_valor_grados REAL,
            pendiente_min_grados REAL,
            pendiente_max_grados REAL,
            pendiente_confianza TEXT,
            pendiente_notas TEXT,
            riesgos_principales_json TEXT,
            limitaciones_json TEXT,
            prob_peligro_base REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE zonas_obstaculos (
            id_obstaculo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            lat_central REAL,
            lon_central REAL,
            diametro_km REAL,
            tipo_riesgo TEXT,
            accion_requerida TEXT,
            pendiente_estimada_grados REAL,
            prob_accidente REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE perfiles_regionales_json (
            id_perfil TEXT PRIMARY KEY,
            region TEXT,
            subregion TEXT,
            ubicacion_asociada TEXT,
            temperatura_k REAL,
            temperatura_rango_k TEXT,
            temperatura_confianza TEXT,
            presion_pa REAL,
            presion_rango_pa TEXT,
            presion_confianza TEXT,
            elevacion_m REAL,
            elevacion_rango_m TEXT,
            elevacion_confianza TEXT,
            pendiente_grados REAL,
            pendiente_rango_grados TEXT,
            pendiente_confianza TEXT,
            polvo_clase TEXT,
            polvo_susceptibilidad TEXT,
            polvo_confianza TEXT,
            riesgos_principales_json TEXT,
            limitaciones_json TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE parametros_atmosfericos (
            id_registro INTEGER PRIMARY KEY,
            temperatura_nominal_c REAL,
            temperatura_tormenta_c REAL,
            presion_nominal_pa REAL,
            gravedad_ms2 REAL,
            prob_tormenta_arena_base REAL,
            prob_tormenta_emergencia REAL,
            tasa_oxigeno_base_l_hora REAL,
            consumo_energia_base_kwh_km REAL,
            velocidad_base_rover_kmh REAL
        )
    """)

    for u in UBICACIONES_PRINCIPALES_SEMILLA:
        cursor.execute("""
            INSERT INTO ubicaciones_principales VALUES (
                :id_ubicacion, :nombre, :subregion, :clasificacion_excel,
                :tipo_zona, :es_refugio, :lat_central, :lon_central, :diametro_km,
                :temperatura_valor_k, :temperatura_min_k, :temperatura_max_k,
                :temperatura_confianza, :temperatura_notas,
                :presion_valor_pa, :presion_min_pa, :presion_max_pa,
                :presion_confianza, :presion_notas,
                :polvo_clase, :polvo_susceptibilidad_atm, :polvo_deposicion_sup,
                :polvo_confianza, :polvo_notas,
                :elevacion_valor_m, :elevacion_min_m, :elevacion_max_m,
                :elevacion_confianza, :elevacion_notas,
                :pendiente_valor_grados, :pendiente_min_grados, :pendiente_max_grados,
                :pendiente_confianza, :pendiente_notas,
                :riesgos_principales_json, :limitaciones_json, :prob_peligro_base
            )
        """, u)

    for z in ZONAS_OBSTACULOS_SEMILLA:
        cursor.execute("""
            INSERT INTO zonas_obstaculos VALUES (
                :id_obstaculo, :nombre, :lat_central, :lon_central, :diametro_km,
                :tipo_riesgo, :accion_requerida, :pendiente_estimada_grados, :prob_accidente
            )
        """, z)

    for p in PERFILES_REGIONALES_JSON_SEMILLA:
        fila_p = dict(p)
        fila_p["riesgos_principales_json"] = json.dumps(p["riesgos_principales"], ensure_ascii=False)
        fila_p["limitaciones_json"] = json.dumps(p["limitaciones"], ensure_ascii=False)
        cursor.execute("""
            INSERT INTO perfiles_regionales_json VALUES (
                :id_perfil, :region, :subregion, :ubicacion_asociada,
                :temperatura_k, :temperatura_rango_k, :temperatura_confianza,
                :presion_pa, :presion_rango_pa, :presion_confianza,
                :elevacion_m, :elevacion_rango_m, :elevacion_confianza,
                :pendiente_grados, :pendiente_rango_grados, :pendiente_confianza,
                :polvo_clase, :polvo_susceptibilidad, :polvo_confianza,
                :riesgos_principales_json, :limitaciones_json
            )
        """, fila_p)

    cursor.execute("""
        INSERT INTO parametros_atmosfericos VALUES (
            :id_registro, :temperatura_nominal_c, :temperatura_tormenta_c,
            :presion_nominal_pa, :gravedad_ms2, :prob_tormenta_arena_base,
            :prob_tormenta_emergencia, :tasa_oxigeno_base_l_hora,
            :consumo_energia_base_kwh_km, :velocidad_base_rover_kmh
        )
    """, PARAMETROS_FISIOLOGICOS_ATMOSFERA)

    conexion.commit()
    conexion.close()


inicializar_base_datos_sqlite()


def obtener_zonas_exploracion_bd():
    """
    Retorna las 4 ubicaciones posibles de navegación con todos sus datos
    ambientales, confianzas, limitaciones y riesgos principales.
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM ubicaciones_principales")
    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for f in filas:
        d = dict(f)
        d["id_zona"] = d["id_ubicacion"]
        d["es_refugio"] = bool(d["es_refugio"])
        d["prob_peligro_zona"] = d["prob_peligro_base"]
        d["riesgos_principales"] = json.loads(d.pop("riesgos_principales_json", "[]"))
        d["limitaciones"] = json.loads(d.pop("limitaciones_json", "[]"))
        resultado.append(d)
    return resultado


def obtener_obstaculos_topograficos_bd():
    """
    Retorna las 4 zonas a evitar / tener precaución del lado derecho del Excel:
    Lycus Sulci (Zona deslaves - Precaucion), Erebus Montes (Zona montañosa - Esquivar),
    Acheron Fossae (Zona de fracturas - Precaucion), Olympus Mons (Zona montañosa - Esquivar).
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM zonas_obstaculos")
    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for f in filas:
        d = dict(f)
        d["id_montana"] = d["id_obstaculo"]
        d["pendiente_grados"] = d["pendiente_estimada_grados"]
        d["prob_accidente_montana"] = d["prob_accidente"]
        resultado.append(d)
    return resultado


def obtener_perfiles_regionales_bd():
    """
    Retorna los 6 perfiles detallados de regional_risk_results (2).json
    (incluyendo Base, Laderas y Cima de Olympus Mons).
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM perfiles_regionales_json")
    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for f in filas:
        d = dict(f)
        d["riesgos_principales"] = json.loads(d.pop("riesgos_principales_json", "[]"))
        d["limitaciones"] = json.loads(d.pop("limitaciones_json", "[]"))
        resultado.append(d)
    return resultado


def obtener_parametros_atmosfericos_bd():
    """
    Retorna los parámetros atmosféricos y fisiológicos del astronauta.
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM parametros_atmosfericos WHERE id_registro = 1")
    fila = cursor.fetchone()
    conexion.close()
    d = dict(fila) if fila else dict(PARAMETROS_FISIOLOGICOS_ATMOSFERA)
    d["temperatura_c"] = d["temperatura_nominal_c"]
    d["presion_atmosfera_kpa"] = round(d["presion_nominal_pa"] / 1000.0, 3)
    d["tasa_oxigeno_l_hora"] = d["tasa_oxigeno_base_l_hora"]
    d["consumo_energia_kwh_km"] = d["consumo_energia_base_kwh_km"]
    return d


# ==============================================================================
# SECCIÓN 2: MOTOR A* CON REGLAS ESQUIVAR / PRECAUCIÓN Y FISIOLOGÍA DEL ASTRONAUTA
# ==============================================================================

def normalizar_longitud(lon):
    if lon is None:
        return None
    return round(max(-179.0, min(179.0, float(lon))), 4)


def calcular_distancia_marte_km(lat1, lon1, lat2, lon2):
    """
    Distancia en km marcianos a lo largo del plano del mapa 2D (sin cruzar el borde -180/+180),
    integrando en 10 sub-segmentos con escala esferica marciana (R = 3389.5 km).
    """
    km_por_grado_lat = 59.158
    pasos = 10
    dlat_paso = (float(lat2) - float(lat1)) / pasos
    dlon_paso = (float(lon2) - float(lon1)) / pasos
    total_km = 0.0
    for i in range(pasos):
        lat_m = float(lat1) + (i + 0.5) * dlat_paso
        cos_lat = max(0.2, math.cos(math.radians(lat_m)))
        dy_km = dlat_paso * km_por_grado_lat
        dx_km = dlon_paso * km_por_grado_lat * cos_lat
        total_km += math.hypot(dx_km, dy_km)
    return total_km


def evaluar_interseccion_tramo(
    nodo_a,
    nodo_b,
    zonas_obstaculos,
    id_inicio_global,
    id_destino_global,
):
    """
    Muestrea 20 puntos a lo largo del segmento lineal (lat, lon) entre nodo_a y nodo_b
    para detectar si la línea cruza alguna de las 4 zonas de obstáculos del Excel:
    - Si cruza una zona con 'Esquivar' (Erebus Montes u Olympus Mons cuando no es destino),
      marca el tramo como bloqueado para obligar a A* a mover la línea.
    - Si cruza una zona con 'Precaucion' (Lycus Sulci o Acheron Fossae), aplica penalización
      y registra el aviso de deslave o fracturas.
    """
    obstaculos_esquivar_tocados = []
    obstaculos_precaucion_tocados = []
    max_pendiente_tramo = 0.5
    max_prob_accidente = 0.03

    for obs in zonas_obstaculos:
        if obs["id_obstaculo"] == "olympus_mons_obstaculo" and (
            id_inicio_global == "olympus_mons" or id_destino_global == "olympus_mons"
        ):
            continue

        radio_km = (float(obs["diametro_km"]) / 2.0) * 1.05
        intersecta = False

        for paso in range(1, 51):
            t = paso / 50.0
            lat_i = nodo_a["latitud"] + t * (nodo_b["latitud"] - nodo_a["latitud"])
            lon_i = nodo_a["longitud"] + t * (nodo_b["longitud"] - nodo_a["longitud"])
            dist = calcular_distancia_marte_km(
                lat_i, lon_i, float(obs["lat_central"]), float(obs["lon_central"])
            )
            if dist <= radio_km:
                intersecta = True
                break

        if intersecta:
            max_pendiente_tramo = max(max_pendiente_tramo, float(obs["pendiente_estimada_grados"]))
            max_prob_accidente = max(max_prob_accidente, float(obs["prob_accidente"]))
            if obs["accion_requerida"].strip().lower() == "esquivar":
                obstaculos_esquivar_tocados.append(obs)
            else:
                obstaculos_precaucion_tocados.append(obs)

    return {
        "bloqueado_por_esquivar": len(obstaculos_esquivar_tocados) > 0,
        "obstaculos_esquivar": obstaculos_esquivar_tocados,
        "obstaculos_precaucion": obstaculos_precaucion_tocados,
        "max_pendiente_obstaculo": max_pendiente_tramo,
        "max_prob_accidente": max_prob_accidente,
    }


def construir_grafo_navegacion(ubicaciones, zonas_obstaculos):
    """
    Construye el grafo con las 4 ubicaciones posibles y genera nodos de desvío
    alrededor de las 4 zonas de obstáculos para que A* pueda esquivarlas moviendo la línea.
    """
    nodos = {}

    for u in ubicaciones:
        uid = u["id_ubicacion"]
        nodos[uid] = {
            "id_nodo": uid,
            "nombre": u["nombre"],
            "latitud": float(u["lat_central"]),
            "longitud": normalizar_longitud(u["lon_central"]),
            "es_ubicacion_principal": True,
            "datos_ambientales": u,
        }

    for obs in zonas_obstaculos:
        oid = obs["id_obstaculo"]
        lat_o = float(obs["lat_central"])
        lon_o = normalizar_longitud(obs["lon_central"])
        radio_km = float(obs["diametro_km"]) / 2.0
        # Radio del anillo de desvio circular (7% por fuera del radio base para obligar avance en arco suave)
        radio_anillo_km = radio_km * 1.07
        km_por_grado_lat = 59.158
        cos_lat = max(0.25, math.cos(math.radians(lat_o)))
        km_por_grado_lon = km_por_grado_lat * cos_lat

        # 24 nodos en circulo (cada 15 grados) alrededor del hitbox para rodearlo en arco circular rapido
        num_puntos_anillo = 24
        for idx_ang in range(num_puntos_anillo):
            angulo_deg = idx_ang * (360.0 / num_puntos_anillo)
            angulo_rad = math.radians(angulo_deg)
            dlat = (radio_anillo_km * math.cos(angulo_rad)) / km_por_grado_lat
            dlon = (radio_anillo_km * math.sin(angulo_rad)) / km_por_grado_lon
            nlat = round(max(-84.0, min(84.0, lat_o + dlat)), 4)
            nlon = normalizar_longitud(lon_o + dlon)
            did = f"{oid}_arco_{int(angulo_deg)}"
            nodos[did] = {
                "id_nodo": did,
                "nombre": f"Arco {int(angulo_deg)} deg ({obs['nombre']})",
                "latitud": nlat,
                "longitud": nlon,
                "es_ubicacion_principal": False,
                "obstaculo_origen": obs["nombre"],
                "accion_obstaculo": obs["accion_requerida"].strip(),
            }

    ids = list(nodos.keys())
    tramos = [{"origen": a, "destino": b} for a in ids for b in ids if a != b]
    return nodos, tramos


def calcular_rendimiento_y_costo_tramo(
    nodo_a,
    nodo_b,
    ubicacion_inicio,
    ubicacion_destino,
    zonas_obstaculos,
    parametros_atm,
    boton_tormenta_activo=False,
    permitir_precaucion=True,
):
    """
    Calcula el impacto ambiental y topográfico sobre el rendimiento del astronauta:
    - Pendiente (slope): reduce la velocidad de desplazamiento e incrementa consumo de O2 y fatiga.
    - Presión (pressure) y Elevación (elevation): menor presión atmosférica (como en Olympus Mons)
      incrementa la exigencia de presurización del traje y el gasto metabólico de O2.
    - Temperatura (temperature): frío extremo incrementa el consumo energético de calefacción.
    - Polvo (dust): reduce visibilidad, tracción y eficiencia energética.
    """
    distancia_km = calcular_distancia_marte_km(
        nodo_a["latitud"], nodo_a["longitud"],
        nodo_b["latitud"], nodo_b["longitud"]
    )

    interseccion = evaluar_interseccion_tramo(
        nodo_a,
        nodo_b,
        zonas_obstaculos,
        ubicacion_inicio["id_ubicacion"],
        ubicacion_destino["id_ubicacion"],
    )

    if (
        ubicacion_inicio["id_ubicacion"] == "olympus_mons"
        or ubicacion_destino["id_ubicacion"] == "olympus_mons"
    ) and (
        str(nodo_a.get("id_nodo", "")).startswith("olympus_mons_obstaculo_")
        or str(nodo_b.get("id_nodo", "")).startswith("olympus_mons_obstaculo_")
    ):
        return None

    if interseccion["bloqueado_por_esquivar"]:
        return None

    if permitir_precaucion and (
        nodo_a.get("accion_obstaculo", "").lower() == "precaucion"
        or nodo_b.get("accion_obstaculo", "").lower() == "precaucion"
    ):
        return None

    if not permitir_precaucion and len(interseccion["obstaculos_precaucion"]) > 0:
        return None

    hay_precaucion = len(interseccion["obstaculos_precaucion"]) > 0
    obs_prec = interseccion["obstaculos_precaucion"][0] if hay_precaucion else None

    pendiente_reg = (
        float(ubicacion_inicio["pendiente_valor_grados"])
        + float(ubicacion_destino["pendiente_valor_grados"])
    ) / 2.0
    pendiente_prec = 4.0 if (obs_prec and obs_prec["id_obstaculo"] == "lycus_sulci") else (5.5 if obs_prec else 0.0)
    pendiente_efectiva = max(pendiente_reg, pendiente_prec)

    eta_destino = 1.8 if ubicacion_destino["id_ubicacion"] in ("hellas_planitia", "olympus_mons") else 1.3
    eta_efectivo = 1.8 if hay_precaucion else eta_destino

    presion_media_pa = (
        670.0 if (obs_prec and obs_prec["id_obstaculo"] == "lycus_sulci")
        else (580.0 if obs_prec else (float(ubicacion_inicio["presion_valor_pa"]) + float(ubicacion_destino["presion_valor_pa"])) / 2.0)
    )
    temp_media_k = (
        200.0 if (obs_prec and obs_prec["id_obstaculo"] == "lycus_sulci")
        else (195.0 if obs_prec else (float(ubicacion_inicio["temperatura_valor_k"]) + float(ubicacion_destino["temperatura_valor_k"])) / 2.0)
    )

    # Fórmulas MEIS — Parámetros Fisiológicos, del Traje Espacial (PLSS) y Nominales de Marte:
    # v_0 = 0.85 m/s; eta = 1.0 -> 100%, eta = 1.3 -> 87.7% (0.75 m/s), eta = 1.8 -> 74.5% (0.63 m/s)
    v0_ms = 0.85
    factor_deslizamiento_vel = 0.745 if eta_efectivo >= 1.75 else (0.877 if eta_efectivo >= 1.2 else 1.0)
    factor_pendiente_vel = max(0.45, 1.0 - 0.022 * abs(pendiente_efectiva))
    v_ef_ms = max(0.28, v0_ms * factor_deslizamiento_vel * factor_pendiente_vel * (0.85 if boton_tormenta_activo else 1.0))
    velocidad_real_kmh = v_ef_ms * 3.6
    tiempo_horas = distancia_km / velocidad_real_kmh

    # Masa corporal m_b = 80 kg, masa traje + PLSS m_s = 65 kg, gamma_g = 0.3783, f_g = 0.6892, k_suit = 1.5
    m_b = 80.0
    m_s = 65.0
    m_tot = m_b + m_s
    gamma_g = 0.3783
    f_g = 0.6892
    k_suit = 1.5

    m_dot_stand_wth = 1.5 * m_b + 2.0 * m_tot * ((m_s / m_b) ** 2) * gamma_g
    grade_pct = math.tan(math.radians(pendiente_efectiva)) * 100.0
    factor_presion_traje = 1.0 + max(0.0, (610.0 - presion_media_pa) / 3000.0)
    trabajo_locomocion_wth = (
        k_suit
        * eta_efectivo
        * m_tot
        * (0.70 * (v_ef_ms ** 2) * f_g + 0.35 * v_ef_ms * max(0.0, grade_pct) * gamma_g)
        * factor_presion_traje
    )
    m_dot_eva_wth = min(500.0, m_dot_stand_wth + trabajo_locomocion_wth)

    # Oxigeno requerido (Ecuación de Weir c_O2 = 0.2527 g/Wh_th + fuga estructural PLSS 8.0 g/h)
    c_o2 = 0.2527
    fuga_o2_gh = 8.0
    tasa_o2_gh = m_dot_eva_wth * c_o2 + fuga_o2_gh
    tasa_o2_real = tasa_o2_gh * 0.7005
    o2_consumido_l = tiempo_horas * tasa_o2_real

    # Potencia eléctrica traje PLSS (95 W_e base + 0.03*M_dot + 0.04*max(0, M_dot-250) + 0.65*max(0, 240-T) + polvo)
    p_elec_base_we = 95.0
    p_pump_we = 0.03 * m_dot_eva_wth
    p_lss_we = 0.04 * max(0.0, m_dot_eva_wth - 250.0)
    p_calefaccion_we = 0.65 * max(0.0, 240.0 - temp_media_k)
    p_polvo_we = 10.0 if (boton_tormenta_activo or hay_precaucion or ubicacion_destino["id_ubicacion"] == "hellas_planitia") else 5.0
    potencia_plss_we = p_elec_base_we + p_pump_we + p_lss_we + p_calefaccion_we + p_polvo_we
    energia_kwh = (tiempo_horas * potencia_plss_we) / 1000.0

    prob_tormenta = (
        float(parametros_atm["prob_tormenta_emergencia"])
        if boton_tormenta_activo
        else float(parametros_atm["prob_tormenta_arena_base"])
    )
    factor_inclinacion = m_dot_eva_wth / 300.0
    factor_presion_altitud = 1.0

    prob_riesgo_tramo = min(
        0.95,
        1.0 - ((1.0 - interseccion["max_prob_accidente"]) * (1.0 - prob_tormenta * 0.5)),
    )
    # El costo de A* prioriza el camino mas rapido (menor distancia/tiempo),
    # esquivando al 100% los obstaculos 'Esquivar' y avisando en los de 'Precaucion'
    costo_optimo = distancia_km

    avisos_tramo = [
        f"PRECAUCION: Paso por hitbox de {o['nombre']} ({o['tipo_riesgo']}, Pendiente: {o['pendiente_estimada_grados']} deg, Riesgo: {int(o['prob_accidente']*100)}%)"
        for o in interseccion["obstaculos_precaucion"]
    ]

    return {
        "distancia_km": round(distancia_km, 2),
        "costo_optimo": round(costo_optimo, 2),
        "velocidad_media_kmh": round(velocidad_real_kmh, 2),
        "tiempo_horas": round(tiempo_horas, 2),
        "o2_consumido_l": round(o2_consumido_l, 2),
        "tasa_o2_l_hora": round(tasa_o2_real, 2),
        "energia_usada_kwh": round(energia_kwh, 2),
        "pendiente_max_grados": round(pendiente_efectiva, 2),
        "factor_esfuerzo_astronauta": round(factor_inclinacion * factor_presion_altitud, 2),
        "prob_supervivencia": round(1.0 - prob_riesgo_tramo, 4),
        "prob_riesgo_total": round(prob_riesgo_tramo, 4),
        "avisos_precaucion_tramo": avisos_tramo,
        "zonas_precaucion_tocadas": [
            {"id": o["id_obstaculo"], "nombre": o["nombre"], "tipo_riesgo": o["tipo_riesgo"]}
            for o in interseccion["obstaculos_precaucion"]
        ],
    }


def _correr_busqueda_astar(
    id_inicio,
    id_destino,
    nodos,
    vecinos_de,
    ubicacion_inicio,
    ubicacion_destino,
    zonas_obstaculos,
    parametros_atm,
    boton_tormenta_activo,
    permitir_precaucion,
):
    meta = nodos[id_destino]

    def heuristica(id_actual):
        actual = nodos[id_actual]
        return calcular_distancia_marte_km(
            actual["latitud"], actual["longitud"],
            meta["latitud"], meta["longitud"]
        )

    cola_abierta = [(heuristica(id_inicio), id_inicio)]
    g_score = {id_inicio: 0.0}
    vino_de = {}
    visitados = set()

    while cola_abierta:
        _, actual = heapq.heappop(cola_abierta)
        if actual == id_destino:
            break
        if actual in visitados:
            continue
        visitados.add(actual)

        for tramo in vecinos_de.get(actual, []):
            sig_nodo = tramo["destino"]
            metricas = calcular_rendimiento_y_costo_tramo(
                nodos[actual],
                nodos[sig_nodo],
                ubicacion_inicio,
                ubicacion_destino,
                zonas_obstaculos,
                parametros_atm,
                boton_tormenta_activo=boton_tormenta_activo,
                permitir_precaucion=permitir_precaucion,
            )
            if metricas is None:
                continue

            tentativo_g = g_score[actual] + metricas["costo_optimo"]
            if tentativo_g < g_score.get(sig_nodo, float("inf")):
                g_score[sig_nodo] = tentativo_g
                vino_de[sig_nodo] = (actual, metricas)
                f_score = tentativo_g + heuristica(sig_nodo)
                heapq.heappush(cola_abierta, (f_score, sig_nodo))

    if id_inicio != id_destino and id_destino not in vino_de:
        return None
    return g_score, vino_de


def ejecutar_astar_optimo(id_inicio, id_destino, boton_tormenta_activo=False):
    """
    Ejecuta A* entre cualquiera de las 4 ubicaciones posibles:
    1. Analiza qué obstáculos habría en línea recta (Esquivar vs Precaucion).
    2. Obligatoriamente esquiva las zonas 'Esquivar' (Erebus Montes y Olympus Mons)
       moviendo la polilínea de la ruta y recalculando todo.
    3. Intenta evitar también las zonas 'Precaucion' (Lycus Sulci y Acheron Fossae)
       si el desvío es razonable; si no o si la ruta original las cruzaba, emite los
       avisos de Zona de deslaves o Zona de fracturas.
    """
    ubicaciones = obtener_zonas_exploracion_bd()
    zonas_obstaculos = obtener_obstaculos_topograficos_bd()
    parametros_atm = obtener_parametros_atmosfericos_bd()

    mapa_ubicaciones = {u["id_ubicacion"]: u for u in ubicaciones}
    if id_inicio not in mapa_ubicaciones or id_destino not in mapa_ubicaciones:
        raise ValueError(
            f"Ubicación inválida. Las 4 ubicaciones posibles son: {list(mapa_ubicaciones.keys())}"
        )

    ubicacion_inicio = mapa_ubicaciones[id_inicio]
    ubicacion_destino = mapa_ubicaciones[id_destino]
    nodos, tramos = construir_grafo_navegacion(ubicaciones, zonas_obstaculos)

    vecinos_de = {nid: [] for nid in nodos}
    for t in tramos:
        vecinos_de[t["origen"]].append(t)

    eval_recta = evaluar_interseccion_tramo(
        nodos[id_inicio],
        nodos[id_destino],
        zonas_obstaculos,
        id_inicio,
        id_destino,
    )

    res_optimo = _correr_busqueda_astar(
        id_inicio, id_destino, nodos, vecinos_de,
        ubicacion_inicio, ubicacion_destino, zonas_obstaculos,
        parametros_atm, boton_tormenta_activo, permitir_precaucion=True
    )

    if res_optimo is not None:
        g_score, vino_de = res_optimo
    else:
        raise ValueError("No se encontro ruta valida entre las ubicaciones seleccionadas.")

    ruta_ids = [id_destino]
    detalles_tramos = []
    prob_exito_acumulada = 1.0
    alertas_ruta = []

    curr = id_destino
    while curr != id_inicio:
        prev, met = vino_de[curr]
        prob_exito_acumulada *= met["prob_supervivencia"]
        for aviso in met["avisos_precaucion_tramo"]:
            if aviso not in alertas_ruta:
                alertas_ruta.append(aviso)
        detalles_tramos.append({
            "desde_id": prev,
            "desde_nombre": nodos[prev]["nombre"],
            "hacia_id": curr,
            "hacia_nombre": nodos[curr]["nombre"],
            **met,
        })
        ruta_ids.append(prev)
        curr = prev

    ruta_ids.reverse()
    detalles_tramos.reverse()

    for obs_esq in eval_recta["obstaculos_esquivar"]:
        msg = f"ESQUIVADO OBLIGATORIO: Ruta desviada para evitar {obs_esq['nombre']} ({obs_esq['tipo_riesgo']})"
        if msg not in alertas_ruta:
            alertas_ruta.append(msg)

    for obs_prec in eval_recta["obstaculos_precaucion"]:
        msg = f"AVISO DE PRECAUCIÓN EN CORREDOR: {obs_prec['nombre']} es {obs_prec['tipo_riesgo']} (Regla: {obs_prec['accion_requerida']})"
        if msg not in alertas_ruta:
            alertas_ruta.append(msg)

    distancia_total = round(sum(d["distancia_km"] for d in detalles_tramos), 2)
    tiempo_total = round(sum(d["tiempo_horas"] for d in detalles_tramos), 2)
    o2_total = round(sum(d["o2_consumido_l"] for d in detalles_tramos), 2)
    energia_total = round(sum(d["energia_usada_kwh"] for d in detalles_tramos), 2)
    esfuerzo_medio = round(
        sum(d["factor_esfuerzo_astronauta"] for d in detalles_tramos) / max(1, len(detalles_tramos)), 2
    )
    indice_fatiga_pct = round(min(100.0, (esfuerzo_medio - 1.0) * 45.0 + (tiempo_total / 40.0)), 1)

    return {
        "ruta_mas_optima_ids": ruta_ids,
        "pasos_nombres": [nodos[nid]["nombre"] for nid in ruta_ids],
        "coordenadas_ruta": [
            {
                "id": nid,
                "nombre": nodos[nid]["nombre"],
                "latitud": nodos[nid]["latitud"],
                "longitud": nodos[nid]["longitud"],
            }
            for nid in ruta_ids
        ],
        "distancia_total_km": distancia_total,
        "distancia_linea_recta_km": round(
            calcular_distancia_marte_km(
                nodos[id_inicio]["latitud"], nodos[id_inicio]["longitud"],
                nodos[id_destino]["latitud"], nodos[id_destino]["longitud"]
            ), 2
        ),
        "tiempo_total_horas": tiempo_total,
        "o2_total_consumido_l": o2_total,
        "energia_total_usada_kwh": energia_total,
        "rendimiento_astronauta": {
            "factor_esfuerzo_medio": esfuerzo_medio,
            "indice_fatiga_estimado_pct": indice_fatiga_pct,
            "pendiente_maxima_superada_grados": max((d["pendiente_max_grados"] for d in detalles_tramos), default=0.3),
            "efecto_ambiental_destino": {
                "region": ubicacion_destino["nombre"],
                "temperatura_k": ubicacion_destino["temperatura_valor_k"],
                "presion_pa": ubicacion_destino["presion_valor_pa"],
                "elevacion_m": ubicacion_destino["elevacion_valor_m"],
                "pendiente_grados": ubicacion_destino["pendiente_valor_grados"],
                "polvo_clase": ubicacion_destino["polvo_clase"],
            },
        },
        "alertas_ruta": alertas_ruta,
        "costo_optimo_total": round(g_score[id_destino], 2),
        "probabilidad_exito_pct": round(prob_exito_acumulada * 100.0, 2),
        "probabilidad_riesgo_pct": round((1.0 - prob_exito_acumulada) * 100.0, 2),
        "tormenta_activa": boton_tormenta_activo,
        "desglose_tramos": detalles_tramos,
    }


def desviar_a_refugio_mas_seguro(id_nodo_actual):
    """
    Evacúa hacia la zona segura de refugio (Arcadia Planitia - Campamento o Utopia Planitia)
    esquivando obligatoriamente las zonas marcadas como 'Esquivar'.
    """
    ubicaciones = obtener_zonas_exploracion_bd()
    refugios = [u["id_ubicacion"] for u in ubicaciones if u.get("es_refugio")]

    mejor_escape = None
    menor_costo =    float("inf")

    for id_ref in refugios:
        resultado = ejecutar_astar_optimo(
            id_inicio=id_nodo_actual,
            id_destino=id_ref,
            boton_tormenta_activo=True,
        )
        if resultado["costo_optimo_total"] < menor_costo:
            menor_costo = resultado["costo_optimo_total"]
            mejor_escape = {
                "refugio_destino_id": id_ref,
                "ruta_escape": resultado,
            }

    return mejor_escape
