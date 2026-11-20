"""
================================================================================
Módulo: convert1.py
Propósito: Reconstrucción en Python puro de CONVERT1.EXE (MS-DOS 16-bit Fortran).
           Convierte archivos de fases en formato PECQ / HYPO71 (ej. Phase191.701)
           al formato de entrada de FASTHYPO (ej. 111917.01P).
================================================================================
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class LecturaFase:
    """Representa la lectura de fases P, S y Coda de una estación."""
    estacion: str
    inicio_p: str
    polaridad_p: str
    peso_p: int
    anio: int
    mes: int
    dia: int
    hora: int
    minuto: int
    seg_p: float
    seg_s: float
    peso_s: int
    coda: float = 0.0


@dataclass
class EventoFases:
    """Evento sísmico convertido al formato FASTHYPO."""
    anio: int
    mes: int
    dia: int
    hora: int
    minuto: int
    lecturas: List[LecturaFase]

    @property
    def nombre_archivo_p(self) -> str:
        """Nombre estándar FASTHYPO: MMDDHH.MMP (ej. 111917.01P)."""
        return f"{self.mes:02d}{self.dia:02d}{self.hora:02d}.{self.minuto:02d}P"

    @property
    def nombre_base_evento(self) -> str:
        """Prefijo estándar MMDDHH.MM para salidas .P, .L, .S."""
        return f"{self.mes:02d}{self.dia:02d}{self.hora:02d}.{self.minuto:02d}"


def mapear_polaridad_fasthypo(polaridad_pecq: str) -> str:
    """
    Mapea la polaridad del formato PECQ/HYPO71 al carácter esperado por FASTHYPO.
    En CONVERT1.EXE:
      - '+', 'C', 'c' -> '+'
      - '-', 'D', 'd' -> '-'
      - 'U', 'u', ' ' -> 'u' (desconocida / indeterminada)
    """
    ch = (polaridad_pecq or " ").strip()
    if ch in ("+", "C", "c"):
        return "+"
    if ch in ("-", "D", "d"):
        return "-"
    if ch in ("U", "u", ""):
        return "u"
    return ch.lower()


def _parsear_float(texto: str, defecto: float = 0.0) -> float:
    t = texto.strip()
    if not t:
        return defecto
    try:
        return float(t)
    except ValueError:
        return defecto


def _parsear_int(texto: str, defecto: int = 0) -> int:
    t = texto.strip()
    if not t:
        return defecto
    try:
        return int(t)
    except ValueError:
        return defecto


def leer_archivo_pecq(ruta_phase: Path) -> List[EventoFases]:
    """
    Lee un archivo en formato PECQ / HYPO71 (ej. Phase191.701) y retorna la lista
    de eventos contenidos (soporta un evento o varios separados por tarjeta final).
    """
    lineas = ruta_phase.read_bytes().decode("latin-1", errors="replace").splitlines()
    eventos: List[EventoFases] = []
    lecturas_actuales: List[LecturaFase] = []

    for linea in lineas:
        # Tarjeta terminadora de evento (estación en blanco, ej. '                  10 ')
        estacion = linea[0:4].strip() if len(linea) >= 4 else ""
        if not estacion:
            if lecturas_actuales:
                prim = lecturas_actuales[0]
                eventos.append(
                    EventoFases(
                        anio=prim.anio,
                        mes=prim.mes,
                        dia=prim.dia,
                        hora=prim.hora,
                        minuto=prim.minuto,
                        lecturas=lecturas_actuales,
                    )
                )
                lecturas_actuales = []
            continue

        # Asegurar longitud mínima para indexado seguro de columnas fijas
        pad = linea.ljust(80)
        inicio_p = pad[4:5]
        polaridad_raw = pad[6:7]
        peso_p = _parsear_int(pad[7:8], defecto=0)

        anio = _parsear_int(pad[9:11], defecto=0)
        mes = _parsear_int(pad[11:13], defecto=0)
        dia = _parsear_int(pad[13:15], defecto=0)
        hora = _parsear_int(pad[15:17], defecto=0)
        minuto = _parsear_int(pad[17:19], defecto=0)

        seg_p = _parsear_float(pad[19:24], defecto=0.0)
        seg_s = _parsear_float(pad[31:36], defecto=0.0)
        peso_s = _parsear_int(pad[39:40], defecto=4 if seg_s == 0.0 else 0)
        coda = _parsear_float(pad[70:76], defecto=0.0)

        lecturas_actuales.append(
            LecturaFase(
                estacion=estacion[:4],
                inicio_p=inicio_p,
                polaridad_p=mapear_polaridad_fasthypo(polaridad_raw),
                peso_p=peso_p,
                anio=anio,
                mes=mes,
                dia=dia,
                hora=hora,
                minuto=minuto,
                seg_p=seg_p,
                seg_s=seg_s,
                peso_s=peso_s,
                coda=coda,
            )
        )

    if lecturas_actuales:
        prim = lecturas_actuales[0]
        eventos.append(
            EventoFases(
                anio=prim.anio,
                mes=prim.mes,
                dia=prim.dia,
                hora=prim.hora,
                minuto=prim.minuto,
                lecturas=lecturas_actuales,
            )
        )

    return eventos


def formatear_archivo_p(evento: EventoFases) -> str:
    """
    Genera el contenido exacto del archivo .P de FASTHYPO:
      Línea 1: (5(i2,1x)) -> '26 11 19 17  1'
      Estaciones: (a4,f6.2,1x,a1,1x,i2,1x,f6.2,1x,i2) -> 'LABR 26.62 +  0  44.30  2'
    """
    lineas = [
        f"{evento.anio:2d} {evento.mes:2d} {evento.dia:2d} {evento.hora:2d} {evento.minuto:2d}"
    ]
    for lec in evento.lecturas:
        linea = (
            f"{lec.estacion:<4s}"
            f"{lec.seg_p:6.2f} "
            f"{lec.polaridad_p:1s} "
            f"{lec.peso_p:2d} "
            f"{lec.seg_s:6.2f} "
            f"{lec.peso_s:2d}"
        )
        lineas.append(linea)
    return "\n".join(lineas) + "\n"


def convertir_pecq_a_fasthypo(
    ruta_phase: Path,
    carpeta_salida: Optional[Path] = None,
) -> List[Tuple[EventoFases, Path]]:
    """Convierte uno o varios eventos PECQ a archivos .P de FASTHYPO."""
    eventos = leer_archivo_pecq(ruta_phase)
    destino = carpeta_salida or ruta_phase.parent
    destino.mkdir(parents=True, exist_ok=True)

    resultados: List[Tuple[EventoFases, Path]] = []
    for ev in eventos:
        ruta_p = destino / ev.nombre_archivo_p
        ruta_p.write_text(formatear_archivo_p(ev), encoding="ascii")
        resultados.append((ev, ruta_p))
    return resultados


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python convert1.py <archivo_Phase> [carpeta_salida]")
        sys.exit(1)

    entrada = Path(sys.argv[1])
    salida = Path(sys.argv[2]) if len(sys.argv) >= 3 else entrada.parent
    generados = convertir_pecq_a_fasthypo(entrada, salida)
    for ev, ruta in generados:
        print(f"Generado: {ruta} ({len(ev.lecturas)} estaciones)")
