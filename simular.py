"""
Simulador de escenarios de población: interfaz de línea de comandos.

Ejemplos:
    python simular.py --listar
    python simular.py --region COL
    python simular.py --region MUN --metodo euler --paso 5 --hasta 2060
    python simular.py --region COL --grafica colombia.png --csv colombia.csv
    python simular.py --inercia --beta 1.1

Equipo: Juan Camilo Castaño Rojas, Leder Andrés Cortes Cortes, Giovanny Esteban Arias Córdoba, Andrés Felipe Pabón Barbosa, Camilo José Luna y Andrés.
"""
import argparse
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import simulador as sim


def fmt(x):
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mostrar_region(args, datos):
    tabla = sim.proyectar_region(datos, args.region, args.metodo, args.paso, args.desde, args.hasta)
    a = tabla.attrs
    print(f"\nRegión: {a['region']}  |  método: {a['metodo'].upper()}  |  paso: {a['paso']} años")
    if a["aproximada"]:
        print(f"Aviso: los escenarios corresponden a {a['comparada_con']} (comparación aproximada).")
    print("Unidades: millones de personas. Escenarios: ONU WPP 2019; tasa: OWID / ONU WPP 2024.\n")
    print(f"{'Año':>6} {'Simulador':>11} {'Exacta':>11} {'Baja':>10} {'Reemplazo':>10} {'Constante':>10}")
    for _, f in tabla.iterrows():
        if int(f.anio) % 10 == 0 or f.anio == tabla.anio.iloc[-1]:
            print(f"{int(f.anio):>6} {fmt(f.simulador):>11} {fmt(f.integral_exacta):>11} "
                  f"{fmt(f.baja):>10} {fmt(f.reemplazo):>10} {fmt(f.constante):>10}")
    ult = tabla.iloc[-1]
    err = ult.simulador - ult.integral_exacta
    err = 0.0 if abs(err) < 5e-4 else err
    pct = f"{err / ult.integral_exacta * 100:+.4f}".replace(".", ",")
    print(f"\nError del método en {int(ult.anio)}: {err:+.3f} M ({pct} %).".replace(".", ",", 1))
    print(f"Rango de escenarios en {int(ult.anio)}: {fmt(ult.banda_min)} a {fmt(ult.banda_max)} M.")
    if args.csv:
        tabla.to_csv(args.csv, index=False)
        print(f"Tabla guardada en {args.csv}")
    if args.grafica:
        fig, ax = plt.subplots(figsize=(7, 3.6))
        ax.fill_between(tabla.anio, tabla.banda_min, tabla.banda_max, color="#c9d6e3", label="Banda de escenarios ONU")
        for k, c in (("constante", "#9b2c2c"), ("reemplazo", "#1f3b57"), ("baja", "#2e8b6e")):
            ax.plot(tabla.anio, tabla[k], color=c, lw=1, ls="--", label=k.capitalize())
        ax.plot(tabla.anio, tabla.simulador, color="k", lw=2, label=f"Tasa integrada ({a['metodo'].upper()}, h = {a['paso']:g})")
        ax.set(xlabel="Año", ylabel="Millones de personas")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=8, frameon=False)
        fig.tight_layout(); fig.savefig(args.grafica, dpi=200)
        print(f"Gráfica guardada en {args.grafica}")


def mostrar_inercia(args, datos):
    P0 = float(datos.escenario("MUN", "constante")[2020])
    g = 0.04
    tabla = sim.inercia_general(g, args.beta * g, 1 / 27, 0.41 * P0, 0.35 * P0, 0.24 * P0, t1=args.hasta - 2020, m=args.inmigracion)
    print(f"\nModelo por edades del mundo: β = {args.beta:g}·γ, m = {args.inmigracion:g} M/año (supuestos de la guía)\n")
    print(f"{'Año':>6} {'Jóvenes':>10} {'Adultos':>10} {'Mayores':>10} {'Total':>10}")
    for _, f in tabla.iterrows():
        if f.t % 10 == 0:
            print(f"{int(2020 + f.t):>6} {fmt(f.Y):>10} {fmt(f.A):>10} {fmt(f.O):>10} {fmt(f.P):>10}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Simulador de escenarios de población (PA5, UDES).")
    p.add_argument("--listar", action="store_true", help="muestra las regiones disponibles")
    p.add_argument("--region", default="MUN", help="clave de la región (MUN, COL, AFR, ...)")
    p.add_argument("--metodo", default="rk4", choices=["rk4", "euler"])
    p.add_argument("--paso", type=float, default=1.0, help="paso en años (por defecto 1)")
    p.add_argument("--desde", type=int, default=2020)
    p.add_argument("--hasta", type=int, default=2100)
    p.add_argument("--grafica", help="archivo PNG para la gráfica con la banda de escenarios")
    p.add_argument("--csv", help="archivo CSV para la tabla anual")
    p.add_argument("--inercia", action="store_true", help="simula el modelo por edades del mundo")
    p.add_argument("--beta", type=float, default=1.0, help="β como múltiplo de γ (1 = reemplazo)")
    p.add_argument("--inmigracion", type=float, default=0.0, help="inmigración de jóvenes, millones/año")
    args = p.parse_args(argv)
    datos = sim.cargar_datos()
    try:
        if args.listar:
            for clave in sorted(set(sim.CLAVES_TASA.values())):
                extra = " (escenarios de América Latina y el Caribe)" if clave in sim.PAREJA_ESCENARIO else ""
                print(f"{clave}  {sim.NOMBRES[clave]}{extra}")
        elif args.inercia:
            mostrar_inercia(args, datos)
        else:
            mostrar_region(args, datos)
    except (ValueError, sim.ExplosionDetectada, sim.PoblacionNegativa) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
