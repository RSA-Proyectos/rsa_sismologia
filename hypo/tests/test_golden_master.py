"""
Prueba automática de equivalencia numérica contra el caso Golden Master:
  - Phase191.701 -> 111917.01P (convert1.py)
  - 111917.01P   -> 111917.01L / 111917.01S / 11191701.rsa (fasthypo.py)
"""

import sys
from pathlib import Path

RAIZ_HYPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_HYPO / "src"))

import convert1
import fasthypo


def ejecutar_pruebas() -> None:
    bin_dir = RAIZ_HYPO / "binarios_originales"
    gold_dir = RAIZ_HYPO / "casos_prueba" / "salidas_originales"
    out_dir = RAIZ_HYPO / "casos_prueba" / "salidas_reconstruidas"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Validar convert1.py (coincidencia exacta carácter por carácter)
    generados = convert1.convertir_pecq_a_fasthypo(gold_dir / "Phase191.701", out_dir)
    assert len(generados) == 1, "Debe generar exactamente 1 evento .P"
    ev_pecq, ruta_p = generados[0]

    orig_p = (gold_dir / "111917.01P").read_text(encoding="latin-1").splitlines()
    gen_p = ruta_p.read_text(encoding="latin-1").splitlines()
    assert orig_p == gen_p, f"Diferencia en .P:\nORIG: {orig_p}\nGEN : {gen_p}"
    print("[OK] convert1.py: coincidencia 100% exacta con 111917.01P")

    # 2. Validar fasthypo.py contra 111917.01S / 111917.01L
    modelos = fasthypo.leer_modelos_velocidad(bin_dir / "FHVELOC.DAT")
    estaciones = fasthypo.leer_estaciones(bin_dir / "FHSTA.DAT")
    ev_p = fasthypo.leer_archivo_p(ruta_p)
    mapa_coda = {l.estacion.upper(): l.coda for l in ev_pecq.lecturas}
    for f in ev_p.fases:
        f.coda = mapa_coda.get(f.estacion.upper(), 0.0)

    res = fasthypo.localizar_hipocentro(
        evento=ev_p,
        estaciones_cat=estaciones,
        capas=modelos["asw"],
        modelo_nombre="asw",
        lat_ini=-2.5,
        lon_ini=-79.0,
        prof_ini=60.0,
        t0_ini=0.0,
        max_iter=100,
    )
    ruta_mag = RAIZ_HYPO / "fuentes_vb5" / "ProcesoV2Con rsa" / "Iaspe-ArchDConfig" / "Mag2000.txt"
    coefs_mag = fasthypo.leer_coeficientes_magnitud(ruta_mag)
    fasthypo.calcular_magnitud_coda(res, coeficientes_estacion=coefs_mag)

    # Escribir salidas reconstruidas actualizadas
    base = ev_pecq.nombre_base_evento
    (out_dir / f"{base}L").write_text(fasthypo.formatear_salida_l(res), encoding="ascii")
    (out_dir / f"{base}S").write_text(fasthypo.formatear_salida_s(res), encoding="ascii")
    rsa_nom = f"{ev_p.mes:02d}{ev_p.dia:02d}{ev_p.hora:02d}{ev_p.minuto:02d}.rsa"
    (out_dir / rsa_nom).write_text(fasthypo.formatear_salida_rsa(res), encoding="ascii")

    # Tolerancias metrológicas contra el Golden Master (111917.01S):
    #   t0 = 0.55 s, lat = -1.8273, lon = -79.2904, prof = 161.90 km, rms = 0.053
    assert abs(res.tiempo_origen_s - 0.55) <= 0.02, f"t0 fuera de tolerancia: {res.tiempo_origen_s}"
    assert abs(res.latitud - (-1.8273)) <= 0.005, f"lat fuera de tolerancia: {res.latitud}"
    assert abs(res.longitud - (-79.2904)) <= 0.006, f"lon fuera de tolerancia: {res.longitud}"
    assert abs(res.profundidad_km - 161.90) <= 0.20, f"prof fuera de tolerancia: {res.profundidad_km}"
    assert abs(res.rms - 0.053) <= 0.005, f"rms fuera de tolerancia: {res.rms}"
    assert abs(res.elipse_x_km - 2.14) <= 0.50, f"elipse_x fuera de tolerancia: {res.elipse_x_km}"
    assert abs(res.elipse_y_km - 2.41) <= 0.50, f"elipse_y fuera de tolerancia: {res.elipse_y_km}"
    assert abs(res.err_prof_km - 1.55) <= 0.30, f"err_prof fuera de tolerancia: {res.err_prof_km}"
    assert res.magnitud_promedio is not None and abs(round(res.magnitud_promedio, 1) - 3.7) < 1e-6, (
        f"Md fuera de tolerancia: {res.magnitud_promedio}"
    )

    print("[OK] fasthypo.py: hipocentro, RMS, elipse de error y magnitud Md (3.7) validados:")
    print(f"     ORIGINAL     : {(gold_dir / '111917.01S').read_text(encoding='latin-1').strip()}")
    print(f"     RECONSTRUIDO : {fasthypo.formatear_salida_s(res).strip()}")


if __name__ == "__main__":
    ejecutar_pruebas()
