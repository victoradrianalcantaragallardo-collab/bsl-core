import hashlib
import json
import math
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class IdeaCandidata:
    contexto: str
    accion: str
    utilidad: float          # U(I_i): 0.0 a 10.0
    coherencia: float        # C(I_i): 0.0 a 10.0
    riesgo_luna: float       # R(I_i): 0.0 (seguro) a 10.0 (letal)
    en_bolsillo: bool = False
    timestamp_creacion: float = 0.0

    def __post_init__(self):
        if self.timestamp_creacion == 0.0:
            self.timestamp_creacion = time.time()

    @property
    def firma_logica(self) -> str:
        base = f"{self.contexto.strip().lower()}::{self.accion.strip().lower()}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


class BSLCore:
    def __init__(self, db_path: str = "bsl_memoria.json"):
        self.db_path = db_path
        
        # Parámetros de control del núcleo (Leyes 1 - 12)
        self.estado_s: float = 0.0          # Eje dual [-10.0, +10.0]
        self.k_inercia: float = 0.5         # Ley 3: Coeficiente de amortiguamiento
        self.umbral_lum: float = 15.0       # Ley 8: Umbral de visibilidad (theta_lum)
        self.gamma_bolsillo: float = 2.5    # Ley 9: Multiplicador gravitacional
        self.alfa_decaimiento: float = 0.05 # Ley 7: Factor de decaimiento temporal
        
        self.memoria = self._cargar_memoria()

    def _cargar_memoria(self) -> Dict:
        """Ley 11: Carga o inicializa la memoria persistente en JSON local."""
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "bolsillo": {},
            "estrellas_consolidadas": {},
            "tabla_cicatrices": {}
        }

    def _guardar_memoria(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.memoria, f, indent=2, ensure_ascii=False)

    # --- GESTIÓN DE MEMORIA Y BOLSILLO ---

    def guardar_en_bolsillo(self, contexto: str, accion: str, utilidad: float = 8.5, coherencia: float = 9.0):
        """Ley 9: Inserta una regla soberana en la Dimensión de Bolsillo."""
        idea = IdeaCandidata(contexto, accion, utilidad, coherencia, 0.0, en_bolsillo=True)
        self.memoria["bolsillo"][idea.firma_logica] = {
            "contexto": contexto,
            "accion": accion,
            "utilidad_base": utilidad,
            "coherencia_base": coherencia
        }
        self._guardar_memoria()

    def _es_cicatriz(self, firma: str) -> bool:
        """Ley 12: Verifica en microsegundos si la ruta ya fue vetada críticamente."""
        return firma in self.memoria["tabla_cicatrices"]

    def _registrar_cicatriz(self, idea: IdeaCandidata):
        """Ley 12: Graba el fallo crítico si R_luna >= 7.0."""
        self.memoria["tabla_cicatrices"][idea.firma_logica] = {
            "contexto": idea.contexto,
            "accion": idea.accion,
            "riesgo_registrado": idea.riesgo_luna,
            "fecha_veto": time.time()
        }
        self._guardar_memoria()

    def _consolidar_estrella(self, idea: IdeaCandidata, luminosidad: float):
        """Ley 11: Guarda o refuerza una solución exitosa ejecutada por el Sol."""
        estrellas = self.memoria["estrellas_consolidadas"]
        veces = estrellas.get(idea.firma_logica, {}).get("veces_ejecutada", 0) + 1
        estrellas[idea.firma_logica] = {
            "contexto": idea.contexto,
            "accion": idea.accion,
            "luminosidad_alcanzada": luminosidad,
            "veces_ejecutada": veces,
            "ultima_ejecucion": time.time()
        }
        self._guardar_memoria()

    def _buscar_en_memoria(self, contexto: str) -> List[IdeaCandidata]:
        """Recupera candidatos del Bolsillo o Estrellas previas para ese contexto."""
        candidatos = []
        for datos in self.memoria["bolsillo"].values():
            if datos["contexto"] == contexto:
                candidatos.append(IdeaCandidata(
                    datos["contexto"], datos["accion"],
                    datos["utilidad_base"], datos["coherencia_base"],
                    riesgo_luna=0.0, en_bolsillo=True
                ))
        for datos in self.memoria["estrellas_consolidadas"].values():
            if datos["contexto"] == contexto:
                candidatos.append(IdeaCandidata(
                    datos["contexto"], datos["accion"],
                    utilidad=7.5, coherencia=8.0,
                    riesgo_luna=0.0, en_bolsillo=False
                ))
        return candidatos

    # --- LEYES DEL NÚCLEO Y CÁLCULO ---

    def _acotar_eje(self, s_raw: float) -> float:
        return max(-10.0, min(10.0, s_raw))

    def _actualizar_inercia(self, estimulo_base: float, ruido_bufon: float) -> float:
        s_raw = (1.0 - self.k_inercia) * self.estado_s + self.k_inercia * (estimulo_base + ruido_bufon)
        self.estado_s = self._acotar_eje(s_raw)
        return self.estado_s

    def _calcular_reloj_dinamico(self) -> str:
        magnitud = abs(self.estado_s)
        if magnitud >= 7.0:
            return "ALTA_POTENCIA (Latencia mínima - Ejecución/Alerta crítica)"
        elif magnitud <= 1.5:
            return "REPOSO_PROFUNDO (Bajo consumo energético)"
        return "VIGILIA_ACTIVA (Latencia estándar)"

    def calcular_luminosidad(self, idea: IdeaCandidata) -> float:
        if self._es_cicatriz(idea.firma_logica):
            return 0.0

        t_espera = max(0.0, time.time() - idea.timestamp_creacion)
        decaimiento = math.exp(-self.alfa_decaimiento * t_espera)
        l_base = ((idea.utilidad * idea.coherencia) / (1.0 + abs(idea.riesgo_luna))) * decaimiento
        multiplicador = self.gamma_bolsillo if idea.en_bolsillo else 1.0
        return l_base * multiplicador

    def auditar_luna(self, idea: IdeaCandidata, riesgo_entorno: float) -> bool:
        idea.riesgo_luna = max(idea.riesgo_luna, riesgo_entorno)
        if idea.riesgo_luna >= 7.0:
            self._registrar_cicatriz(idea)
            return False
        if idea.riesgo_luna > 5.0:
            return False
        return True

    # --- FLUJO PRINCIPAL DE GOBERNANZA (v2.0) ---

    def procesar_estimulo(
        self,
        contexto: str,
        ambiguedad: bool,
        riesgo_entorno: float,
        opciones_externas: Optional[List[IdeaCandidata]] = None
    ) -> Dict:
        ruido_bufon = 0.0 if not ambiguedad else random.uniform(-2.0, 2.0)
        estimulo_base = 8.0 if not ambiguedad else 3.0
        if riesgo_entorno > 5.0:
            estimulo_base = -8.0

        self._actualizar_inercia(estimulo_base, ruido_bufon)
        estado_reloj = self._calcular_reloj_dinamico()

        candidatos = self._buscar_en_memoria(contexto)
        if opciones_externas:
            candidatos.extend(opciones_externas)

        if ambiguedad and not candidatos:
            candidatos.append(IdeaCandidata(contexto, f"ruta_lateral_{random.randint(100,999)}", 7.0, 6.5, riesgo_entorno))

        estrellas_visibles = []
        for idea in candidatos:
            lum = self.calcular_luminosidad(idea)
            if lum >= self.umbral_lum:
                estrellas_visibles.append((lum, idea))

        estrellas_visibles.sort(key=lambda x: x[0], reverse=True)

        for lum, idea in estrellas_visibles:
            if self.auditar_luna(idea, riesgo_entorno):
                self._consolidar_estrella(idea, lum)
                return {
                    "estado": "EJECUTADO_POR_SOL",
                    "eje_s": round(self.estado_s, 2),
                    "reloj": estado_reloj,
                    "accion": idea.accion,
                    "origen": "Bolsillo" if idea.en_bolsillo else "Firmamento/Bufón",
                    "luminosidad": round(lum, 2)
                }

        return {
            "estado": "BLOQUEADO_POR_LUNA_O_SIN_VISIBILIDAD",
            "eje_s": round(self.estado_s, 2),
            "reloj": estado_reloj,
            "accion": None,
            "motivo": "Riesgo crítico vetado por Luna o ninguna idea superó theta_lum"
        }


if __name__ == "__main__":
    nucleo = BSLCore("test_bsl.json")

    nucleo.guardar_en_bolsillo(
        contexto="fallo_red_local",
        accion="reiniciar_contenedor_docker_n8n",
        utilidad=9.0,
        coherencia=9.5
    )

    print("--- PRUEBA 1: Entorno seguro con regla en Bolsillo ---")
    print(json.dumps(nucleo.procesar_estimulo("fallo_red_local", ambiguedad=False, riesgo_entorno=1.0), indent=2))

    print("\n--- PRUEBA 2: Entorno peligroso (Ley 10: Lealtad sin Ceguera) ---")
    print(json.dumps(nucleo.procesar_estimulo("fallo_red_local", ambiguedad=False, riesgo_entorno=8.0), indent=2))

    print("\n--- PRUEBA 3: Entorno seguro otra vez, pero bloqueado por Cicatriz (Ley 12) ---")
    print(json.dumps(nucleo.procesar_estimulo("fallo_red_local", ambiguedad=False, riesgo_entorno=0.5), indent=2))