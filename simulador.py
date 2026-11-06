"""
Simulador de escenarios de población (Proyecto de Aula PA5, Ecuaciones Diferenciales, UDES 2026B).

Módulo con las piezas del simulador:
    1. Lectura y limpieza de los datos (tasa de crecimiento y escenarios de la ONU).
    2. Interpolación lineal de la tasa entre los años con datos.
    3. Integración de P' = r(t) P por la regla del trapecio (solución con factor integrante).
    4. Métodos numéricos de paso fijo: Euler y Runge-Kutta de orden 4.
    5. Modelos cerrados: exponencial, hiperbólico (von Foerster), logístico con tasa variable.
    6. Modelo por edades (jóvenes, adultos, mayores) y su solución exacta con reemplazo.
    7. Guardas del simulador: población no negativa y detección de explosiones.

Unidades: tiempo en años, población en millones de personas, tasas en 1/año (fracción).

Equipo: Juan Camilo Castaño Rojas, Leder Andrés Cortes Cortes, Giovanny Esteban Arias Córdoba, Andrés Felipe Pabón Barbosa, Camilo José Luna y Andrés.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RUTA_DATOS = Path(__file__).parent / "datos" / "PA5_Simulador_poblacion.xlsx"

# Clave común de región para las dos fuentes (ver 02_Auditoría, sección E).
CLAVES_TASA = {
    "World": "MUN", "Colombia": "COL", "Africa": "AFR", "Asia": "ASI", "Europe": "EUR",
    "South America": "SAM", "China": "CHN", "India": "IND", "Japan": "JPN",
    "South Korea": "KOR", "Nigeria": "NGA",
}
CLAVES_ESC = {
    "WORLD": "MUN", "Colombia": "COL", "Africa": "AFR", "Asia": "ASI", "Europe": "EUR",
    "Latin America and the Caribbean": "LAC", "Northern America": "NAM", "China": "CHN",
    "India": "IND", "Japan": "JPN", "Republic of Korea": "KOR", "Nigeria": "NGA",
}
NOMBRES = {
    "MUN": "Mundo", "COL": "Colombia", "AFR": "África", "ASI": "Asia", "EUR": "Europa",
    "SAM": "Sudamérica", "LAC": "América Latina y el Caribe", "NAM": "Norteamérica",
    "CHN": "China", "IND": "India", "JPN": "Japón", "KOR": "Corea del Sur", "NGA": "Nigeria",
}
# Para comparar la tasa con los escenarios, Sudamérica se empareja (de forma aproximada) con LAC.
PAREJA_ESCENARIO = {"SAM": "LAC"}


# ---------------------------------------------------------------------------
# 1. Datos
# ---------------------------------------------------------------------------
@dataclass
class Datos:
    tasa: pd.DataFrame        # columnas: clave, anio, tasa_pct, tasa
    escenarios: pd.DataFrame  # columnas: clave, anio, constante, reemplazo, baja (millones)

    def serie_tasa(self, clave: str) -> tuple[np.ndarray, np.ndarray]:
        d = self.tasa[self.tasa.clave == clave].sort_values("anio")
        return d.anio.to_numpy(float), d.tasa.to_numpy(float)

    def escenario(self, clave: str, nombre: str) -> pd.Series:
        d = self.escenarios[self.escenarios.clave == clave].set_index("anio")
        return d[nombre]


def cargar_datos(ruta: Path | str = RUTA_DATOS) -> Datos:
    """Lee las hojas originales, asigna la clave común y convierte unidades."""
    t = pd.read_excel(ruta, sheet_name="Tasa_crecimiento")
    e = pd.read_excel(ruta, sheet_name="Escenarios_2020_2100")
    if t.isna().drop(columns="codigo").any().any() or e.isna().any().any():
        raise ValueError("La base tiene valores vacíos")
    if t.duplicated(["region", "anio"]).any() or e.duplicated(["region", "anio"]).any():
        raise ValueError("La base tiene registros duplicados región-año")
    t = t.assign(clave=t.region.map(CLAVES_TASA),
                 tasa_pct=t.tasa_crecimiento_pct,
                 tasa=t.tasa_crecimiento_pct / 100.0)
    e = e.assign(clave=e.region.map(CLAVES_ESC),
                 constante=e.fecundidad_constante / 1000.0,
                 reemplazo=e.reemplazo_inmediato / 1000.0,
                 baja=e.fecundidad_baja / 1000.0)
    if t.clave.isna().any() or e.clave.isna().any():
        raise ValueError("Hay regiones sin clave asignada")
    return Datos(t[["clave", "anio", "tasa_pct", "tasa"]].reset_index(drop=True),
                 e[["clave", "anio", "constante", "reemplazo", "baja"]].reset_index(drop=True))


# ---------------------------------------------------------------------------
# 2. Interpolación de la tasa
# ---------------------------------------------------------------------------
class TasaInterpolada:
    """r(t) lineal por tramos entre los años con datos. Fuera del rango se rechaza."""

    def __init__(self, anios: np.ndarray, tasas: np.ndarray):
        if np.any(np.diff(anios) <= 0):
            raise ValueError("Los años deben ser estrictamente crecientes")
        self.anios, self.tasas = anios, tasas

    def __call__(self, t):
        t_arr = np.asarray(t, float)
        if np.any(t_arr < self.anios[0] - 1e-9) or np.any(t_arr > self.anios[-1] + 1e-9):
            raise ValueError(f"t fuera del rango de datos [{self.anios[0]}, {self.anios[-1]}]")
        return np.interp(t_arr, self.anios, self.tasas)


# ---------------------------------------------------------------------------
# 3. Solución por factor integrante: P(t) = P(t0) exp(∫ r ds)
# ---------------------------------------------------------------------------
def integral_trapecio(r: TasaInterpolada, t0: float, t: np.ndarray, h: float = 1.0) -> np.ndarray:
    """∫_{t0}^{t} r(s) ds por la regla del trapecio sobre una malla de paso h.

    Si los nodos de la malla incluyen todos los años con datos (h = 1 y años enteros),
    la regla es exacta, porque r es lineal entre nodos.
    """
    t = np.atleast_1d(np.asarray(t, float))
    lo, hi = min(t.min(), t0), max(t.max(), t0)
    malla = np.arange(lo, hi + h / 2, h)
    rv = r(malla)
    acumulada = np.concatenate([[0.0], np.cumsum(h * (rv[1:] + rv[:-1]) / 2)])
    i0 = np.interp(t0, malla, acumulada)
    return np.interp(t, malla, acumulada) - i0


def reconstruir(r: TasaInterpolada, P0: float, t0: float, t: np.ndarray) -> np.ndarray:
    """Población desde P(t0) = P0 hacia atrás y hacia adelante."""
    return P0 * np.exp(integral_trapecio(r, t0, t))


# ---------------------------------------------------------------------------
# 4. Métodos numéricos de paso fijo con guardas del simulador
# ---------------------------------------------------------------------------
class ExplosionDetectada(RuntimeError):
    """La solución supera el umbral o deja de ser finita (como en el modelo de 1960)."""


class PoblacionNegativa(RuntimeError):
    """La solución numérica se volvió negativa."""


def _verificar(t, P, umbral):
    if not np.isfinite(P) or P > umbral:
        raise ExplosionDetectada(f"Explosión detectada en t = {t:.3f} (P = {P:.4g})")
    if P < 0:
        raise PoblacionNegativa(f"Población negativa en t = {t:.3f} (P = {P:.4g})")


def euler(f, t0: float, P0: float, t1: float, h: float, umbral: float = 1e7):
    n = int(round((t1 - t0) / h))
    ts, Ps = [t0], [P0]
    t, P = t0, P0
    for _ in range(n):
        P = P + h * f(t, P)
        t = t + h
        _verificar(t, P, umbral)
        ts.append(t); Ps.append(P)
    return np.array(ts), np.array(Ps)


def rk4(f, t0: float, P0: float, t1: float, h: float, umbral: float = 1e7):
    n = int(round((t1 - t0) / h))
    ts, Ps = [t0], [P0]
    t, P = t0, P0
    for _ in range(n):
        k1 = f(t, P)
        k2 = f(t + h / 2, P + h * k1 / 2)
        k3 = f(t + h / 2, P + h * k2 / 2)
        k4 = f(t + h, P + h * k3)
        P = P + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        t = t + h
        _verificar(t, P, umbral)
        ts.append(t); Ps.append(P)
    return np.array(ts), np.array(Ps)


def rk4_solo_enteros(r_enteros: dict, t0: int, P0: float, t1: int):
    """RK4 cuando la tasa solo se conoce en años enteros: se usa h = 2,
    de modo que el punto medio cae en un año entero (variante sin interpolar)."""
    f = lambda t, P: r_enteros[int(round(t))] * P
    ts, Ps = [t0], [P0]
    t, P = t0, P0
    while t < t1:
        h = 2
        k1 = f(t, P); k2 = f(t + 1, P + k1); k3 = f(t + 1, P + k2); k4 = f(t + 2, P + 2 * k3)
        P = P + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        t += h
        ts.append(t); Ps.append(P)
    return np.array(ts), np.array(Ps)


# ---------------------------------------------------------------------------
# 5. Modelos de primer orden con solución exacta
# ---------------------------------------------------------------------------
def exponencial(P0, r, t0, t):
    return P0 * np.exp(r * (np.asarray(t, float) - t0))


def tiempo_duplicacion(r):
    return math.log(2) / r


def hiperbolico(k, T, t):
    """Solución de P' = k P² por separación de variables: P = 1/[k (T − t)]."""
    t = np.asarray(t, float)
    return 1.0 / (k * (T - t))


def ajuste_hiperbolico(anios, P, r):
    """Regresión de r = P'/P contra P por el origen (r = k P).
    Devuelve k, el año de explosión T estimado con la función potencial
    F(t, P) = t + 1/(kP), y la dispersión de F a lo largo de los datos."""
    P = np.asarray(P, float); r = np.asarray(r, float)
    k = float(np.sum(r * P) / np.sum(P * P))
    F = np.asarray(anios, float) + 1.0 / (k * P)
    r2 = 1 - np.sum((r - k * P) ** 2) / np.sum((r - r.mean()) ** 2)
    return {"k": k, "T": float(F.mean()), "T_min": float(F.min()), "T_max": float(F.max()),
            "T_ultimo": float(F[-1]), "r2": float(r2)}


def logistica_tasa_variable(r: TasaInterpolada, K, P0, t0, t):
    """Solución exacta de P' = r(t) P (1 − P/K) con el factor integrante 1/[P (K − P)]:
    ln[P/(K − P)] = ∫ r dt + C."""
    I = integral_trapecio(r, t0, t)
    c = P0 / (K - P0)
    return K * c * np.exp(I) / (1 + c * np.exp(I))


def bernoulli_logistica(r: TasaInterpolada, K, P0, t0, t):
    """Misma ecuación resuelta con w = 1/P: w' + r(t) w = r(t)/K (lineal).
    Con μ = exp(∫r): w = 1/K + (1/P0 − 1/K) exp(−∫ r)."""
    I = integral_trapecio(r, t0, t)
    w = 1 / K + (1 / P0 - 1 / K) * np.exp(-I)
    return 1 / w


# ---------------------------------------------------------------------------
# 6. Modelo por edades
# ---------------------------------------------------------------------------
@dataclass
class Edades:
    gamma: float = 0.04       # 1/año, paso entre grupos (25 años por grupo)
    beta: float = 0.04        # 1/año, nacimientos por adulto
    delta: float = 1 / 27     # 1/año, salida de mayores (27 años promedio después de los 50)
    m: float = 0.0            # millones/año, inmigración de jóvenes

    def f(self, t, x, m_func=None):
        Y, A, O = x
        m = self.m if m_func is None else m_func(t)
        return np.array([self.beta * A - self.gamma * Y + m,
                         self.gamma * Y - self.gamma * A,
                         self.gamma * A - self.delta * O])

    def raices(self):
        """Raíces de la ecuación auxiliar de A'' + 2γA' + γ(γ − β)A = 0: −γ ± √(γβ)."""
        s = math.sqrt(self.gamma * self.beta)
        return (-self.gamma + s, -self.gamma - s)

    def discriminante(self):
        return 4 * self.beta * self.gamma


def rk4_sistema(f, t0, x0, t1, h):
    n = int(round((t1 - t0) / h))
    ts = [t0]; xs = [np.array(x0, float)]
    t, x = t0, np.array(x0, float)
    for _ in range(n):
        k1 = f(t, x); k2 = f(t + h / 2, x + h * k1 / 2)
        k3 = f(t + h / 2, x + h * k2 / 2); k4 = f(t + h, x + h * k3)
        x = x + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        t += h
        if np.any(x < -1e-9):
            raise PoblacionNegativa(f"Grupo de edad negativo en t = {t}")
        ts.append(t); xs.append(x)
    return np.array(ts), np.array(xs)


def inercia_exacta(gamma, delta, Y0, A0, O0, t):
    """Solución exacta con β = γ y m = 0.
    A(t) = c1 + c2 e^{−2γt}, Y = S − A con S = Y0 + A0 constante,
    O' + δ O = γ A(t) resuelta como ecuación lineal con factor integrante e^{δt}."""
    t = np.asarray(t, float)
    S = Y0 + A0
    c1 = S / 2
    c2 = A0 - c1
    A = c1 + c2 * np.exp(-2 * gamma * t)
    Y = S - A
    # O = particular + homogénea
    a = gamma * c1 / delta                      # respuesta a la parte constante
    b = gamma * c2 / (delta - 2 * gamma)        # respuesta a la parte exponencial
    C = O0 - a - b
    O = a + b * np.exp(-2 * gamma * t) + C * np.exp(-delta * t)
    return Y, A, O


def adultos_inmigracion(gamma, m0, m1, Omega, t):
    """Respuesta de A'' + 2γA' = γ m(t) con m = m0 + m1 sen(Ωt) y condiciones iniciales nulas
    (con β = γ). Devuelve las dos partes por separado (superposición)."""
    t = np.asarray(t, float)
    # constante: A = (m0/2) t − (m0 / (4γ)) (1 − e^{−2γt})
    A_const = (m0 / 2) * t - (m0 / (4 * gamma)) * (1 - np.exp(-2 * gamma * t))
    # oscilante: particular a cos + b sen, más homogénea para condiciones nulas
    b = -gamma * m1 / (Omega ** 2 + 4 * gamma ** 2)
    a = 2 * gamma * b / Omega
    Ap = a * np.cos(Omega * t) + b * np.sin(Omega * t)
    Ap0, dAp0 = a, b * Omega
    # c1 + c2 e^{−2γt}: c1 + c2 = −Ap0 ; −2γ c2 = −dAp0
    c2 = dAp0 / (2 * gamma)
    c1 = -Ap0 - c2
    A_osc = Ap + c1 + c2 * np.exp(-2 * gamma * t)
    return A_const, A_osc


# ---------------------------------------------------------------------------
# 7. Aplicaciones de la sala de servidores y cinemática
# ---------------------------------------------------------------------------
def co2_sala(V, c0_ppm, n_personas, emision, Q, c_ext_ppm, t):
    """x' = entrada − (Q/V) x, con x en m³ de CO₂. Devuelve concentración en ppm."""
    entrada = n_personas * emision + Q * c_ext_ppm * 1e-6
    x_eq = entrada * V / Q
    x0 = c0_ppm * 1e-6 * V
    x = x_eq + (x0 - x_eq) * np.exp(-Q / V * np.asarray(t, float))
    return x / V * 1e6


def ventilacion_minima(n_personas, emision, c_ext_ppm, c_max_ppm):
    return n_personas * emision / ((c_max_ppm - c_ext_ppm) * 1e-6)


def temperatura_sala(k, T_ext, q, T0, t):
    T_eq = T_ext + q / k
    return T_eq + (T0 - T_eq) * np.exp(-k * np.asarray(t, float))


def tiempo_hasta(k, T_ext, q, T0, T_obj):
    T_eq = T_ext + q / k
    return -math.log((T_obj - T_eq) / (T0 - T_eq)) / k


def velocidad_proyectil(g, c, v0, t):
    """v' = −g − c v: v = −g/c + (v0 + g/c) e^{−ct}."""
    return -g / c + (v0 + g / c) * np.exp(-c * np.asarray(t, float))


# ---------------------------------------------------------------------------
# 8. Ajuste de modelos cerrados y comparación con residuos
# ---------------------------------------------------------------------------
def _modelos_cerrados():
    return {
        "Exponencial": (lambda t, P0, r: P0 * np.exp(r * (t - 1900)), ["P0", "r"]),
        "Logística": (lambda t, K, P0, r: K / (1 + (K / P0 - 1) * np.exp(-r * (t - 1900))), ["K", "P0", "r"]),
        "Hiperbólico": (lambda t, k, T: 1.0 / (k * (T - t)), ["k", "T"]),
    }


def ajustar_modelos(anios, P, ventana=(1900, 1963), prueba=(1964, 2023)):
    """Ajusta los tres modelos cerrados por mínimos cuadrados en la ventana y mide
    el error (RMSE, millones) dentro de la ventana y fuera de ella."""
    from scipy.optimize import curve_fit
    anios = np.asarray(anios, float); P = np.asarray(P, float)
    m = (anios >= ventana[0]) & (anios <= ventana[1])
    o = (anios >= prueba[0]) & (anios <= prueba[1])
    iniciales = {"Exponencial": [P[m][0], 0.01], "Logística": [3 * P[m].max(), P[m][0], 0.02],
                 "Hiperbólico": [5e-6, anios[m][-1] + 50]}
    salida = {}
    for nombre, (f, nombres) in _modelos_cerrados().items():
        p, _ = curve_fit(f, anios[m], P[m], p0=iniciales[nombre], maxfev=50000)
        rm = lambda mask: float(np.sqrt(np.mean((P[mask] - f(anios[mask], *p)) ** 2)))
        salida[nombre] = {"parametros": dict(zip(nombres, map(float, p))),
                          "rmse_ajuste": rm(m), "rmse_prueba": rm(o) if o.any() else None,
                          "residuos_ajuste": (P[m] - f(anios[m], *p)).tolist()}
    return salida


def evaluar_modelo(nombre, parametros, t):
    f, nombres = _modelos_cerrados()[nombre]
    return f(np.asarray(t, float), *[parametros[n] for n in nombres])


# ---------------------------------------------------------------------------
# 9. Funciones de alto nivel para la línea de comandos y el cuaderno
# ---------------------------------------------------------------------------
METODOS = {"euler": euler, "rk4": rk4}


def proyectar_region(datos: Datos, clave: str, metodo: str = "rk4", h: float = 1.0,
                     desde: int = 2020, hasta: int = 2100) -> pd.DataFrame:
    """Proyección con la tasa de la región, junto con la integral exacta y la banda
    de escenarios de la ONU. Devuelve una tabla por año (millones)."""
    clave = clave.upper()
    if clave not in set(CLAVES_TASA.values()):
        raise ValueError(f"Región sin tasa: {clave}. Opciones: {sorted(set(CLAVES_TASA.values()))}")
    if metodo not in METODOS:
        raise ValueError(f"Método desconocido: {metodo}. Opciones: {list(METODOS)}")
    if not (2020 <= desde < hasta <= 2100):
        raise ValueError("El horizonte debe estar entre 2020 y 2100")
    clave_esc = PAREJA_ESCENARIO.get(clave, clave)
    a, r = datos.serie_tasa(clave)
    rf = TasaInterpolada(a, r)
    P0 = float(datos.escenario(clave_esc, "constante")[2020])
    if desde > 2020:
        P0 = float(reconstruir(rf, P0, 2020, [desde])[0])
    ts, Pn = METODOS[metodo](lambda t, P: rf(t) * P, desde, P0, hasta, h)
    tabla = pd.DataFrame({"anio": ts, "simulador": Pn,
                          "integral_exacta": reconstruir(rf, P0, desde, ts)})
    for k in ("constante", "reemplazo", "baja"):
        tabla[k] = datos.escenario(clave_esc, k).reindex(np.round(ts).astype(int)).to_numpy()
    tabla["banda_min"] = tabla[["constante", "reemplazo", "baja"]].min(axis=1)
    tabla["banda_max"] = tabla[["constante", "reemplazo", "baja"]].max(axis=1)
    tabla.attrs.update(region=NOMBRES[clave], comparada_con=NOMBRES[clave_esc],
                       aproximada=clave in PAREJA_ESCENARIO, metodo=metodo, paso=h)
    return tabla


def inercia_general(gamma, beta, delta, Y0, A0, O0, t1=150, h=0.5, m=0.0):
    """Modelo por edades con cualquier β (no solo reemplazo), resuelto con RK4."""
    modelo = Edades(gamma=gamma, beta=beta, delta=delta, m=m)
    ts, X = rk4_sistema(modelo.f, 0, [Y0, A0, O0], t1, h)
    return pd.DataFrame({"t": ts, "Y": X[:, 0], "A": X[:, 1], "O": X[:, 2], "P": X.sum(axis=1)})
