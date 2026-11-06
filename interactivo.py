"""
Gráficas interactivas para el cuaderno (simulador_poblacional.ipynb).
Cada función recibe parámetros simples y dibuja una figura, de modo que
puede usarse con ipywidgets.interact o llamarse directamente.

Equipo: Juan Camilo Castaño Rojas, Leder Andrés Cortes Cortes, Giovanny Esteban Arias Córdoba, Andrés Felipe Pabón Barbosa, Camilo José Luna y Andrés.
"""
import matplotlib.pyplot as plt
import numpy as np

import simulador as sim

_DATOS = None


def datos():
    global _DATOS
    if _DATOS is None:
        _DATOS = sim.cargar_datos()
    return _DATOS


def grafica_region(region="COL", metodo="rk4", paso=1.0, hasta=2100):
    tabla = sim.proyectar_region(datos(), region, metodo, paso, 2020, hasta)
    a = tabla.attrs
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.fill_between(tabla.anio, tabla.banda_min, tabla.banda_max, color="#c9d6e3", label="Banda de escenarios ONU")
    for k, c in (("constante", "#9b2c2c"), ("reemplazo", "#1f3b57"), ("baja", "#2e8b6e")):
        ax.plot(tabla.anio, tabla[k], color=c, lw=1, ls="--", label=k.capitalize())
    ax.plot(tabla.anio, tabla.integral_exacta, color="#888888", lw=3, alpha=0.5, label="Integral exacta")
    ax.plot(tabla.anio, tabla.simulador, color="k", lw=1.5, label=f"{metodo.upper()}, h = {paso:g}")
    titulo = a["region"] + (" (escenarios de " + a["comparada_con"] + ", aprox.)" if a["aproximada"] else "")
    ax.set(title=titulo, xlabel="Año", ylabel="Millones de personas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False)
    plt.show()
    u = tabla.iloc[-1]
    print(f"{int(u.anio)}: simulador {u.simulador:,.1f} M | exacta {u.integral_exacta:,.1f} M | "
          f"error {u.simulador - u.integral_exacta:+.3f} M | escenarios {u.banda_min:,.1f} a {u.banda_max:,.1f} M")
    return tabla


def grafica_inercia(beta_sobre_gamma=1.0, inmigracion=0.0, delta_anios=27):
    d = datos()
    P0 = float(d.escenario("MUN", "constante")[2020])
    g = 0.04
    tabla = sim.inercia_general(g, beta_sobre_gamma * g, 1 / delta_anios, 0.41 * P0, 0.35 * P0, 0.24 * P0,
                                t1=130, m=inmigracion)
    onu = d.escenario("MUN", "reemplazo")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.stackplot(2020 + tabla.t, tabla.Y, tabla.A, tabla.O, colors=["#dbe4ee", "#b7c9dc", "#8faac6"],
                 labels=["Jóvenes", "Adultos", "Mayores"])
    ax.plot(2020 + tabla.t, tabla.P, color="k", lw=1.8, label="Total (modelo)")
    ax.plot(onu.index, onu.values, color="#9b2c2c", ls="--", label="ONU, reemplazo inmediato")
    ax.set(title=f"Modelo por edades: β = {beta_sobre_gamma:g}γ, m = {inmigracion:g} M/año",
           xlabel="Año", ylabel="Millones de personas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    plt.show()
    m1, m2 = sim.Edades(g, beta_sobre_gamma * g).raices()
    print(f"Raíces de la ecuación auxiliar: {m1:.5f} y {m2:.5f}  |  población en 2100: {tabla.P.iloc[160]:,.0f} M")


def grafica_hiperbolico(fin_ventana=1963):
    rec = sim.reconstruir(sim.TasaInterpolada(*datos().serie_tasa("MUN")),
                          float(datos().escenario("MUN", "constante")[2020]), 2020, np.arange(1900, 2101))
    anios = np.arange(1900, 2101)
    aj = sim.ajustar_modelos(anios, rec, ventana=(1900, fin_ventana), prueba=(fin_ventana + 1, 2023))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(anios, rec, color="k", lw=2, label="Población reconstruida")
    for nombre, c in (("Exponencial", "#2e8b6e"), ("Hiperbólico", "#9b2c2c")):
        p = aj[nombre]["parametros"]
        tt = anios if nombre != "Hiperbólico" else anios[anios < p["T"] - 0.5]
        ax.plot(tt, sim.evaluar_modelo(nombre, p, tt), ls="--", color=c,
                label=f"{nombre}: RMSE ajuste {aj[nombre]['rmse_ajuste']:,.0f} M, prueba {aj[nombre]['rmse_prueba']:,.0f} M")
    ax.axvspan(1900, fin_ventana, color="#eeeeee", label="Ventana de ajuste")
    ax.set(ylim=(0, 15000), xlabel="Año", ylabel="Millones de personas",
           title=f"Ajuste 1900-{fin_ventana}: T estimado = {aj['Hiperbólico']['parametros']['T']:.1f}")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    plt.show()
