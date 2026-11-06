"""
Ejecuta el análisis completo del proyecto (pasos 1 a 23 de la guía) y guarda:
    resultados/resultados.json   valores clave de cada paso
    resultados/*.csv             tablas de trabajo
    resultados/figuras/*.png     figuras para el informe y las diapositivas

Uso:  python ejecutar_analisis.py

Equipo: Juan Camilo Castaño Rojas, Leder Andrés Cortes Cortes, Giovanny Esteban Arias Córdoba, Andrés Felipe Pabón Barbosa, Camilo José Luna y Andrés.
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import simulador as sim

import os
SALIDA = Path(__file__).parent / "resultados"
# Con PA5_DIAPOSITIVAS=1 se generan las figuras con letra grande para proyectar
DIAPOS = os.environ.get("PA5_DIAPOSITIVAS") == "1"
FIG = SALIDA / ("figuras_diapositivas" if DIAPOS else "figuras")
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 10, "font.family": "DejaVu Serif",
                     "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#444444", "axes.linewidth": 0.7,
                     "axes.titlesize": 10, "axes.titleweight": "normal",
                     "legend.frameon": False, "legend.fontsize": 8,
                     "lines.linewidth": 1.5,
                     "figure.dpi": 150, "savefig.dpi": 200, "savefig.bbox": "tight",
                     "figure.facecolor": "white"})
if DIAPOS:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.labelsize": 13,
                         "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 11,
                         "lines.linewidth": 2.2})
AZUL, NARANJA, VERDE, ROJO, GRIS = "#1f4e79", "#e08a2e", "#2e8b6e", "#c0392b", "#8c8c8c"
R = {}  # resultados


def guardar(nombre):
    """Las figuras de un panel van sin título (el pie de figura del informe lo reemplaza);
    las de varios paneles se rotulan (a), (b)."""
    ejes = [a for a in plt.gcf().axes if a.get_label() != "<colorbar>"]
    if len(ejes) == 1:
        ejes[0].set_title("")
    else:
        for letra, a in zip("abcd", ejes):
            titulo = a.get_title()
            a.set_title("")
            a.set_title(f"({letra}) {titulo}", loc="left", fontsize=9.5)
    plt.tight_layout()
    plt.savefig(FIG / f"{nombre}.png")
    plt.close()


d = sim.cargar_datos()

# ---------------------------------------------------------------- Paso 1 y 3
anios_m, tasa_m = d.serie_tasa("MUN")
r_mun = sim.TasaInterpolada(anios_m, tasa_m)
serie = pd.Series(tasa_m * 100, index=anios_m.astype(int))
R["paso1"] = {
    "registros_tasa": int(len(d.tasa)), "regiones_tasa": int(d.tasa.clave.nunique()),
    "anios_por_region": int(d.tasa.groupby("clave").size().iloc[0]),
    "registros_escenarios": int(len(d.escenarios)), "regiones_escenarios": int(d.escenarios.clave.nunique()),
    "tasa_1950": float(serie[1950]), "tasa_1959": float(serie[1959]), "tasa_1960": float(serie[1960]),
    "tasa_1961": float(serie[1961]), "tasa_1962": float(serie[1962]),
    "china_1960": float(d.tasa.query("clave=='CHN' and anio==1960").tasa_pct.iloc[0]),
}
R["paso3"] = {
    "tasa_1700": float(serie[1700]), "tasa_1900": float(serie[1900]),
    "tasa_max": float(serie.max()), "anio_max": int(serie.idxmax()),
    "tasa_2024": float(serie[2024]), "primer_negativo": int(serie[serie < 0].index.min()),
    "esc_2100": {k: float(d.escenario("MUN", k)[2100]) for k in ("constante", "reemplazo", "baja")},
    "esc_2020": float(d.escenario("MUN", "constante")[2020]),
}

fig, ax = plt.subplots(figsize=(7, 3.2))
ax.plot(anios_m, tasa_m * 100, "o-", ms=2.5, color=AZUL, lw=1.2)
ax.axhline(0, color="k", lw=0.8)
for y, lab, xy in [(1960, "1960: caída\n(hambruna china)", (1830, 1.45)), (1963, "1963: máximo 2,28 %", (1990, 2.3)),
                  (2084, "2084: primera\ntasa negativa", (2025, 0.55))]:
    ax.annotate(lab, (y, serie[y]), xytext=xy, fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.7))
ax.axvspan(2024, 2100, color=GRIS, alpha=0.15)
ax.text(2060, 1.2, "proyección\nONU", fontsize=8, color=GRIS, ha="center")
ax.set_ylim(-0.3, 2.6)
ax.set(xlabel="Año", ylabel="Tasa de crecimiento (% por año)", title="Tasa de crecimiento mundial, 1700-2100", xlim=(1700, 2100))
guardar("f01_tasa_mundial")

fig, ax = plt.subplots(figsize=(7, 3.6))
for clave in ["MUN", "COL", "AFR", "ASI", "EUR", "SAM", "CHN", "IND", "JPN", "KOR", "NGA"]:
    a, r = d.serie_tasa(clave)
    m = a >= 1950
    ax.plot(a[m], r[m] * 100, lw=2.2 if clave in ("MUN", "COL") else 0.9,
            color={"MUN": "k", "COL": ROJO}.get(clave), label=sim.NOMBRES[clave])
ax.axhline(0, color="k", lw=0.6)
ax.set(xlabel="Año", ylabel="% por año", title="Tasa de crecimiento por región, 1950-2100", xlim=(1950, 2100))
ax.legend(ncol=4, fontsize=7, loc="lower left")
guardar("f02_tasa_regiones")

fig, ax = plt.subplots(figsize=(7, 3.2))
for k, c, lab in [("constante", ROJO, "Fecundidad constante"), ("reemplazo", AZUL, "Reemplazo inmediato"), ("baja", VERDE, "Fecundidad baja")]:
    s = d.escenario("MUN", k)
    ax.plot(s.index, s.values, color=c, lw=1.8, label=f"{lab} ({s[2100]:,.0f} M en 2100)".replace(",", "."))
ax.set(xlabel="Año", ylabel="Millones de personas", title="Mundo: escenarios de la ONU, 2020-2100")
ax.legend(fontsize=8)
guardar("f03_escenarios_mundo")

# ---------------------------------------------------------------- Paso 5
r63 = serie[1963] / 100
R["paso5"] = {"r_1963": float(r63), "t_duplicacion": sim.tiempo_duplicacion(r63)}

# ---------------------------------------------------------------- Paso 6
P2020 = R["paso3"]["esc_2020"]
anios_rec = np.arange(1700, 2101)
P_rec = sim.reconstruir(r_mun, P2020, 2020, anios_rec)
rec = pd.DataFrame({"anio": anios_rec, "tasa": r_mun(anios_rec), "P": P_rec})
rec.to_csv(SALIDA / "reconstruccion_mundo.csv", index=False)
Ps = rec.set_index("anio").P
imax = int(Ps.loc[2020:].idxmax())
R["paso6"] = {"P2020": P2020, "P1700": float(Ps[1700]), "P1800": float(Ps[1800]), "P1900": float(Ps[1900]),
              "P1950": float(Ps[1950]), "P2000": float(Ps[2000]), "P2050": float(Ps[2050]),
              "P_max": float(Ps.loc[2020:].max()), "anio_max": imax, "P2100": float(Ps[2100]),
              "gapminder_1950": 2499.0, "error_1950_pct": float((Ps[1950] - 2499) / 2499 * 100)}

fig, ax = plt.subplots(figsize=(7, 3.4))
ax.plot(anios_rec, P_rec, color=AZUL, lw=1.8, label="Reconstrucción: $P_0\\,e^{\\int r\\,dt}$")
ax.plot(1950, 2499, "s", color=ROJO, label="Gapminder 1950 (2.499 M)")
ax.plot(2020, P2020, "o", color="k", label="Punto de partida 2020")
ax.axvline(imax, ls=":", color=GRIS)
ax.text(imax - 95, 600, f"máximo en {imax}:\n{Ps[imax]:,.0f} M".replace(",", "."), fontsize=8)
ax.set(xlabel="Año", ylabel="Millones de personas", title="Población mundial reconstruida desde la tasa", xlim=(1700, 2100))
ax.legend(fontsize=8, loc="upper left")
guardar("f04_reconstruccion")

# ---------------------------------------------------------------- Paso 7
f_mun = lambda t, P: r_mun(t) * P
ref2100 = R["paso6"]["P2100"]
tabla7 = []
for h in (1, 5, 10):
    for nombre, metodo in (("Euler", sim.euler), ("RK4", sim.rk4)):
        ts, Pn = metodo(f_mun, 2020, P2020, 2100, h)
        tabla7.append({"metodo": nombre, "h": h, "P2100": float(Pn[-1]),
                       "error_abs": float(Pn[-1] - ref2100), "error_rel_pct": float((Pn[-1] - ref2100) / ref2100 * 100)})
r_ent = {int(a): float(r) for a, r in zip(anios_m, tasa_m) if a >= 2020}
ts, Pn = sim.rk4_solo_enteros(r_ent, 2020, P2020, 2100)
tabla7.append({"metodo": "RK4 sin interpolar (h = 2)", "h": 2, "P2100": float(Pn[-1]),
               "error_abs": float(Pn[-1] - ref2100), "error_rel_pct": float((Pn[-1] - ref2100) / ref2100 * 100)})
pd.DataFrame(tabla7).to_csv(SALIDA / "metodos_numericos.csv", index=False)
R["paso7"] = {"referencia_2100": ref2100, "tabla": tabla7}

fig, ax = plt.subplots(figsize=(6, 3.2))
for nombre, c in (("Euler", NARANJA), ("RK4", AZUL)):
    filas = [x for x in tabla7 if x["metodo"] == nombre]
    ax.loglog([x["h"] for x in filas], [abs(x["error_abs"]) for x in filas], "o-", color=c, label=nombre)
ax.set(xlabel="Paso h (años)", ylabel="|Error en 2100| (millones)", title="Error frente a la integral exacta")
ax.set_xticks([1, 5, 10], ["1", "5", "10"])
ax.legend()
guardar("f05_error_metodos")

# ---------------------------------------------------------------- Paso 8
# Malla anual 1900-1963 (tasa interpolada y población reconstruida en el paso 6)
obs = rec[(rec.anio >= 1900) & (rec.anio <= 1963)]
P_obs = obs.P.to_numpy()
aj = sim.ajuste_hiperbolico(obs.anio.to_numpy(), P_obs, obs.tasa.to_numpy())
# Variante solo con los años que traen dato (sin interpolar), para la discusión
obs_d = d.tasa[(d.tasa.clave == "MUN") & (d.tasa.anio >= 1900) & (d.tasa.anio <= 1963)]
aj_d = sim.ajuste_hiperbolico(obs_d.anio.to_numpy(), Ps.loc[obs_d.anio.astype(int)].to_numpy(), obs_d.tasa.to_numpy())
k, T = aj["k"], aj["T"]
R["paso8"] = {**aj, "n_datos": int(len(obs)), "k_solo_datos": aj_d["k"], "T_solo_datos": aj_d["T"],
              "P_hiperbolico_2000": float(sim.hiperbolico(k, T, 2000)),
              "P_reconstruida_2000": float(Ps[2000]),
              "r_hiperbolico_2020": float(k * Ps[2020]), "r_observada_2020": float(serie[2020] / 100)}

fig, axs = plt.subplots(1, 2, figsize=(8, 3.2))
tt = np.linspace(1900, T - 0.5, 400)
axs[0].plot(anios_rec[200:], P_rec[200:], color=AZUL, lw=1.8, label="Reconstruida")
axs[0].plot(tt, sim.hiperbolico(k, T, tt), "--", color=ROJO, label="Hiperbólico $1/[k(T-t)]$")
axs[0].axvline(T, color=ROJO, lw=0.7)
axs[0].set(ylim=(0, 20000), xlabel="Año", ylabel="Millones", title=f"Explosión en T ≈ {T:.1f}".replace(".", ","))
axs[0].legend(fontsize=7)
axs[1].plot(Ps.loc[1900:2023], r_mun(np.arange(1900, 2024)), color=GRIS, lw=1, label="Datos 1900-2023")
axs[1].plot(P_obs, obs.tasa, "o", ms=3, color=AZUL, label="Ajuste 1900-1963 (anual)")
pp = np.linspace(0, 8000, 50)
axs[1].plot(pp, k * pp, "--", color=ROJO, label=f"r = kP, k = {k:.2e}")
axs[1].set(xlabel="P (millones)", ylabel="r (1/año)", title="Regresión de r contra P")
axs[1].legend(fontsize=7)
guardar("f06_hiperbolico")

# ---------------------------------------------------------------- Comparación de modelos (pasos 4, 5 y 8)
anios_c = np.arange(1900, 2024)
P_c = Ps.loc[1900:2023].to_numpy()
comp = sim.ajustar_modelos(anios_c, P_c, ventana=(1900, 1963), prueba=(1964, 2023))
comp_log = sim.ajustar_modelos(anios_c, P_c, ventana=(1950, 2023), prueba=(2024, 2023))["Logística"]
R["comparacion_modelos"] = {n: {k: v for k, v in c.items() if k != "residuos_ajuste"} for n, c in comp.items()}
R["logistica_1950_2023"] = {k: v for k, v in comp_log.items() if k != "residuos_ajuste"}
fig, axs = plt.subplots(1, 2, figsize=(8.4, 3.3))
axs[0].plot(anios_c, P_c, color="k", lw=2, label="Reconstruida")
axs[0].axvspan(1900, 1963, color="#eeeeee")
for nombre, c in (("Exponencial", VERDE), ("Hiperbólico", ROJO)):
    p = comp[nombre]["parametros"]
    tt = anios_c[anios_c < p.get("T", 1e9) - 1]
    axs[0].plot(tt, sim.evaluar_modelo(nombre, p, tt), "--", color=c, label=nombre)
pl = comp_log["parametros"]
axs[0].plot(anios_c, sim.evaluar_modelo("Logística", pl, anios_c), ":", color=AZUL, lw=2,
            label=f"Logística 1950-2023 (K = {pl['K']:,.0f})".replace(",", "."))
axs[0].set(ylim=(0, 12000), xlabel="Año", ylabel="Millones", title="Ajuste en 1900-1963 (sombreado)")
axs[0].legend(fontsize=7)
for nombre, c in (("Exponencial", VERDE), ("Hiperbólico", ROJO)):
    axs[1].plot(np.arange(1900, 1964), comp[nombre]["residuos_ajuste"], "o-", ms=2, lw=0.8, color=c, label=nombre)
axs[1].axhline(0, color="k", lw=0.7)
axs[1].set(xlabel="Año", ylabel="Residuo (millones)", title="Residuos dentro de la ventana")
axs[1].legend(fontsize=7)
guardar("f13_comparacion_modelos")

# ---------------------------------------------------------------- Paso 9 y 11
K_ilus = float(pl["K"])  # K ajustada con la logística 1950-2023
tt9 = np.arange(2020, 2101)
P_log = sim.logistica_tasa_variable(r_mun, K_ilus, P2020, 2020, tt9)
P_ber = sim.bernoulli_logistica(r_mun, K_ilus, P2020, 2020, tt9)
_, P_log_rk = sim.rk4(lambda t, P: r_mun(t) * P * (1 - P / K_ilus), 2020, P2020, 2100, 1)
R["paso9_11"] = {"K_ajustada": K_ilus, "P2100_factor_integrante": float(P_log[-1]),
                 "P2100_bernoulli": float(P_ber[-1]), "P2100_rk4": float(P_log_rk[-1]),
                 "max_dif_metodos": float(np.max(np.abs(P_log - P_ber)))}

# ---------------------------------------------------------------- Paso 12: campos de pendientes
fig, axs = plt.subplots(1, 2, figsize=(8, 3.2))
K, rr = 10.0, 0.5
T_, P_ = np.meshgrid(np.linspace(0, 10, 21), np.linspace(0, 14, 15))
for ax, F, tit, ylim in [(axs[0], lambda t, P: rr * P * (1 - P / K), "Logística: $P'=rP(1-P/K)$", 14),
                         (axs[1], lambda t, P: 0.05 * P ** 2, "Hiperbólico: $P'=kP^2$", 14)]:
    S = F(T_, P_); n = np.sqrt(1 + S ** 2)
    ax.quiver(T_, P_, 1 / n, S / n, angles="xy", color=GRIS, width=0.003, headwidth=0, headlength=0, pivot="mid")
    for P0 in (0.5, 2, 5, 12) if "Log" in tit else (1, 2, 3):
        ts, Pv = [0], [P0]
        while ts[-1] < 10 and Pv[-1] < 40:
            h = 0.01; Pv.append(Pv[-1] + h * F(ts[-1], Pv[-1])); ts.append(ts[-1] + h)
        ax.plot(ts, Pv, color=AZUL, lw=1.4)
    ax.set(xlim=(0, 10), ylim=(0, ylim), xlabel="t", ylabel="P", title=tit)
axs[0].axhline(K, color=VERDE, ls="--", lw=1); axs[0].text(0.3, K + 0.3, "equilibrio estable P = K", fontsize=7, color=VERDE)
axs[1].axhline(0, color=ROJO, ls="--", lw=1)
axs[1].text(0.3, 0.4, "único equilibrio P = 0 (inestable)", fontsize=7, color=ROJO)
guardar("f07_campos_pendientes")

# ---------------------------------------------------------------- Paso 10
ed = sim.Edades()
P0 = P2020
Y0, A0, O0 = 0.41 * P0, 0.35 * P0, 0.24 * P0
ts10, X10 = sim.rk4_sistema(ed.f, 0, [Y0, A0, O0], 150, 0.5)
fig, ax = plt.subplots(figsize=(4.6, 3.4))
for v0 in (0.4, 0.85, 1.6, 2.5):
    Yi, Ai = 4000, 4000 * v0
    S = Yi + Ai
    tt = np.linspace(0, 120, 200)
    A = S / 2 + (Ai - S / 2) * np.exp(-0.08 * tt); Y = S - A
    ax.plot(Y, A, color=GRIS, lw=1)
    ax.plot(Yi, Ai, "o", ms=3, color=GRIS)
ax.plot(X10[:, 0], X10[:, 1], color=AZUL, lw=2, label="Mundo 2020 (supuesto)")
lim = np.array([1500, 8000]); ax.plot(lim, lim, "--", color=VERDE, lw=1, label="A = Y (v = 1)")
ax.set(xlabel="Jóvenes Y (millones)", ylabel="Adultos A (millones)", title="Trayectorias con β = γ")
ax.legend(fontsize=7)
guardar("f08_trayectoria_edades")
R["paso10"] = {"v0": A0 / Y0, "v_150": float(X10[-1, 1] / X10[-1, 0]),
               "S0": Y0 + A0, "S_150": float(X10[-1, 0] + X10[-1, 1])}

# ---------------------------------------------------------------- Paso 13
filas13 = []
for clave in ["MUN", "COL", "AFR", "ASI", "EUR", "SAM", "CHN", "IND", "JPN", "KOR", "NGA"]:
    clave_esc = sim.PAREJA_ESCENARIO.get(clave, clave)
    a, r = d.serie_tasa(clave)
    rf = sim.TasaInterpolada(a, r)
    P0c = float(d.escenario(clave_esc, "constante")[2020])
    Pt = float(sim.reconstruir(rf, P0c, 2020, [2100])[0])
    esc = {k: float(d.escenario(clave_esc, k)[2100]) for k in ("constante", "reemplazo", "baja")}
    cercano = min(esc, key=lambda kk: abs(esc[kk] - Pt))
    filas13.append({"clave": clave, "region": sim.NOMBRES[clave], "comparada_con": sim.NOMBRES[clave_esc],
                    "P2020": P0c, "tasa_integrada_2100": Pt, **esc, "escenario_cercano": cercano,
                    "aproximada": clave in sim.PAREJA_ESCENARIO})
t13 = pd.DataFrame(filas13); t13.to_csv(SALIDA / "escenarios_por_region.csv", index=False)
R["paso13"] = filas13

fig, ax = plt.subplots(figsize=(7.5, 3.4))
sub = t13[t13.clave != "MUN"].copy()
x = np.arange(len(sub))
rel = lambda col: sub[col] / sub["P2020"]
ax.bar(x - 0.3, rel("constante"), 0.2, color=ROJO, label="Constante")
ax.bar(x - 0.1, rel("reemplazo"), 0.2, color=AZUL, label="Reemplazo")
ax.bar(x + 0.1, rel("baja"), 0.2, color=VERDE, label="Baja")
ax.bar(x + 0.3, rel("tasa_integrada_2100"), 0.2, color="k", label="Tasa integrada")
ax.axhline(1, color="k", lw=0.6)
ax.set_xticks(x, [s.replace("Sudamérica", "Sudamérica*") for s in sub.region], rotation=30, ha="right", fontsize=8)
ax.set(ylabel="P(2100) / P(2020)", title="Población 2100 relativa a 2020 por región")
ax.set_yscale("log"); ax.legend(fontsize=7, ncol=4)
guardar("f09_escenarios_regiones")

# ---------------------------------------------------------------- Paso 14
r_eq = math.log(float(d.escenario("MUN", "reemplazo")[2050]) / P2020) / 30
re = d.escenario("MUN", "reemplazo")
R["paso14"] = {"P2020": P2020, "P2050_reemplazo": float(re[2050]), "max_reemplazo": float(re.max()),
               "anio_max_reemplazo": int(re.idxmax()), "r_constante_equivalente": r_eq,
               "t_duplicacion_equivalente": math.log(2) / r_eq}

# ---------------------------------------------------------------- Paso 15
V, c0, npers, em, Q = 200, 400, 3, 0.03, 100
th = np.linspace(0, 12, 200)
c_t = sim.co2_sala(V, c0, npers, em, Q, 400, th)
Qmin = sim.ventilacion_minima(npers, em, 400, 1000)
T_t = sim.temperatura_sala(0.5, 30, 6, 20, th)
t35 = sim.tiempo_hasta(0.5, 30, 6, 20, 35)
R["paso15"] = {"co2_equilibrio": float(sim.co2_sala(V, c0, npers, em, Q, 400, 1e6)),
               "tau_horas": V / Q, "co2_1h": float(sim.co2_sala(V, c0, npers, em, Q, 400, 1)),
               "Q_min": Qmin, "T_final": 30 + 6 / 0.5, "t_35": t35}
fig, axs = plt.subplots(1, 2, figsize=(8, 3))
axs[0].plot(th, c_t, color=AZUL); axs[0].axhline(1000, color=ROJO, ls="--", lw=1)
axs[0].plot(th, sim.co2_sala(V, c0, npers, em, Qmin, 400, th), color=VERDE, label=f"Q = {Qmin:.0f} m³/h")
axs[0].set(xlabel="Horas", ylabel="CO₂ (ppm)", title="CO₂ en la sala (Q = 100 m³/h)"); axs[0].legend(fontsize=7)
axs[1].plot(th, T_t, color=NARANJA); axs[1].axhline(35, color=ROJO, ls="--", lw=1)
axs[1].axvline(t35, color=GRIS, ls=":"); axs[1].text(t35 + 0.2, 25, f"{t35:.2f} h".replace(".", ","), fontsize=8)
axs[1].set(xlabel="Horas", ylabel="°C", title="Temperatura si falla el aire")
guardar("f10_servidores")

# ---------------------------------------------------------------- Paso 16 (cinemática)
g, c, v0 = 9.81, 0.5, 20.0
# Euler escrito aparte: la velocidad sí puede ser negativa, así que no se usa la guarda de población
h16 = 1 / 60; v = v0
for _ in range(120):
    v = v + h16 * (-g - c * v)
v_ex = float(sim.velocidad_proyectil(g, c, v0, 2))
R["paso16"] = {"v0_supuesto": v0, "v_exacta_2s": v_ex, "v_euler_2s": v, "error": v - v_ex,
               "error_rel_pct": (v - v_ex) / abs(v_ex) * 100}

# ---------------------------------------------------------------- Pasos 17-21
gam = 0.04
roots = {}
for etiqueta, beta in (("reemplazo", gam), ("mas10", 1.1 * gam), ("menos10", 0.9 * gam)):
    e2 = sim.Edades(gamma=gam, beta=beta)
    roots[etiqueta] = {"beta": beta, "m1": e2.raices()[0], "m2": e2.raices()[1], "disc": e2.discriminante()}
Wr = -2 * gam  # wronskiano de {1, e^{-2γt}} en t = 0: W = -2γ e^{-2γt}
tt21 = np.array([0, 10, 50, 100])
Omega = 2 * math.pi / 10
A_c, A_o = sim.adultos_inmigracion(gam, 0.1, 0.05, Omega, tt21)
Ah = 0.5 * (Y0 + A0) + (A0 - 0.5 * (Y0 + A0)) * np.exp(-2 * gam * tt21)
R["pasos17_21"] = {"raices": roots, "wronskiano_t0": Wr,
                   "Y0": Y0, "A0": A0, "O0": O0, "dA0": gam * Y0 - gam * A0,
                   "particular_50": 0.1 / 2 * 50,
                   "respuesta_constante_50_cond_nulas": float(sim.adultos_inmigracion(gam, 0.1, 0, Omega, 50)[0]),
                   "superposicion": [{"t": int(t), "homogenea": float(h_), "transitorio": float(h_ - 0.5 * (Y0 + A0)),
                                      "constante": float(c_), "oscilante": float(o_)}
                                     for t, h_, c_, o_ in zip(tt21, Ah, A_c, A_o)],
                   "amplitud_oscilante": gam * 0.05 / (Omega * math.sqrt(Omega ** 2 + 4 * gam ** 2))}
tt = np.linspace(0, 100, 400)
A_c2, A_o2 = sim.adultos_inmigracion(gam, 0.1, 0.05, Omega, tt)
fig, axs = plt.subplots(1, 2, figsize=(8, 3))
tt_ = tt[1:]
axs[0].semilogy(tt_, np.abs((A0 - 0.5 * (Y0 + A0)) * np.exp(-2 * gam * tt_)), color=AZUL, label="|Transitorio de la estructura inicial|")
axs[0].semilogy(tt_, np.abs(A_c2[1:]), color=NARANJA, label="Inmigración constante")
axs[0].semilogy(tt_, np.abs(A_o2[1:]), color=VERDE, label="|Inmigración oscilante|")
for x_ in (10, 50, 100):
    axs[0].axvline(x_, color=GRIS, ls=":", lw=0.8)
axs[0].set(xlabel="Años desde 2020", ylabel="Millones de adultos (escala log)", title="Tamaño de cada parte (superposición)", ylim=(1e-3, 1e3))
axs[0].legend(fontsize=7)
for etiqueta, col, lab in (("mas10", ROJO, "β = 1,1γ"), ("reemplazo", "k", "β = γ"), ("menos10", VERDE, "β = 0,9γ")):
    m1, m2 = roots[etiqueta]["m1"], roots[etiqueta]["m2"]
    c2 = (gam * Y0 - gam * A0 - m1 * A0) / (m2 - m1); c1 = A0 - c2
    axs[1].plot(tt, c1 * np.exp(m1 * tt) + c2 * np.exp(m2 * tt), color=col, label=lab)
axs[1].set(xlabel="Años desde 2020", ylabel="Adultos (millones)", title="Adultos según la natalidad")
axs[1].legend(fontsize=7)
guardar("f11_segundo_orden")

# ---------------------------------------------------------------- Paso 22
delta = 1 / 27
tt22 = np.arange(0, 301)
Y, A, O = sim.inercia_exacta(gam, delta, Y0, A0, O0, tt22)
Ptot = Y + A + O
_, Xn = sim.rk4_sistema(sim.Edades(gam, gam, delta).f, 0, [Y0, A0, O0], 300, 1)
inercia = pd.DataFrame({"anio": 2020 + tt22, "Y": Y, "A": A, "O": O, "P": Ptot, "P_rk4": Xn[:, 0] + Xn[:, 1] + Xn[:, 2]})
inercia.to_csv(SALIDA / "inercia.csv", index=False)
Pi = inercia.set_index("anio").P
P_final = Y0 + A0 + gam / delta * 0.5 * (Y0 + A0)
R["paso22"] = {"P2050": float(Pi[2050]), "P2100": float(Pi[2100]), "P_final": float(P_final),
               "max_dif_rk4": float(np.max(np.abs(inercia.P - inercia.P_rk4))),
               "onu_2050": float(re[2050]), "onu_2100": float(re[2100]),
               "O_final": float(gam / delta * 0.5 * (Y0 + A0)), "S": Y0 + A0}
fig, ax = plt.subplots(figsize=(7, 3.3))
m = inercia.anio <= 2150
ax.plot(inercia.anio[m], inercia.P[m], color=AZUL, lw=2, label="Modelo por edades (β = γ)")
ax.plot(re.index, re.values, color=ROJO, lw=1.6, ls="--", label="ONU, reemplazo inmediato")
ax.axhline(P_final, color=GRIS, ls=":", lw=1); ax.text(2105, P_final + 60, f"límite {P_final:,.0f} M".replace(",", "."), fontsize=8)
ax.stackplot(inercia.anio[m], inercia.Y[m], inercia.A[m], inercia.O[m], colors=["#c6dbef", "#9ecae1", "#6baed6"], alpha=0.35,
             labels=["Jóvenes", "Adultos", "Mayores"])
ax.set(xlabel="Año", ylabel="Millones de personas", title="Inercia demográfica con reemplazo inmediato", ylim=(0, 10500))
ax.legend(fontsize=7, loc="lower right", ncol=2)
guardar("f12_inercia")

# ---------------------------------------------------------------- Demostración: banda de Colombia
tb = sim.proyectar_region(d, "COL")
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.fill_between(tb.anio, tb.banda_min, tb.banda_max, color="#c9d6e3", label="Banda de escenarios ONU")
for k, c in (("constante", ROJO), ("reemplazo", AZUL), ("baja", VERDE)):
    ax.plot(tb.anio, tb[k], "--", lw=1, color=c, label=k.capitalize())
ax.plot(tb.anio, tb.simulador, color="k", lw=2, label="Tasa integrada (RK4, h = 1)")
ax.set(xlabel="Año", ylabel="Millones de personas", title="Colombia")
ax.legend(fontsize=7, ncol=2)
guardar("f14_banda_colombia")

with open(SALIDA / ("resultados_diapositivas.json" if DIAPOS else "resultados.json"), "w", encoding="utf-8") as fh:
    json.dump(R, fh, ensure_ascii=False, indent=2, default=float)
print(json.dumps(R, ensure_ascii=False, indent=1, default=float)[:6000])
