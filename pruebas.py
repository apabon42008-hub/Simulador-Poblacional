"""
Pruebas automáticas del simulador (paso 12 de la guía).

Uso:  python -m unittest pruebas -v

Equipo: Juan Camilo Castaño Rojas, Leder Andrés Cortes Cortes, Giovanny Esteban Arias Córdoba, Andrés Felipe Pabón Barbosa, Camilo José Luna y Andrés.
"""
import math
import unittest

import numpy as np

import simulador as sim


class PruebasSimulador(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = sim.cargar_datos()
        a, r = cls.d.serie_tasa("MUN")
        cls.r = sim.TasaInterpolada(a, r)
        cls.P2020 = float(cls.d.escenario("MUN", "constante")[2020])

    # --- Prueba 1: comparación con soluciones exactas conocidas -------------
    def test_rk4_contra_exponencial(self):
        """Con r constante, RK4 debe reproducir P0·e^{rt} con error relativo < 1e-8."""
        r = 0.02
        _, P = sim.rk4(lambda t, P: r * P, 0, 100.0, 50, 1)
        self.assertAlmostEqual(P[-1] / sim.exponencial(100.0, r, 0, 50) - 1, 0, delta=1e-8)

    def test_rk4_contra_integral_tasa_variable(self):
        """Con la tasa real, RK4 de paso 1 debe coincidir con la integral exacta del paso 6."""
        exacta = sim.reconstruir(self.r, self.P2020, 2020, [2100])[0]
        _, P = sim.rk4(lambda t, P: self.r(t) * P, 2020, self.P2020, 2100, 1)
        self.assertLess(abs(P[-1] - exacta) / exacta, 1e-6)

    def test_logistica_factor_integrante_igual_a_bernoulli(self):
        t = np.arange(2020, 2101)
        a = sim.logistica_tasa_variable(self.r, 12000, self.P2020, 2020, t)
        b = sim.bernoulli_logistica(self.r, 12000, self.P2020, 2020, t)
        self.assertTrue(np.allclose(a, b, rtol=1e-12))

    def test_inercia_exacta_contra_rk4(self):
        Y0, A0, O0 = 0.41 * self.P2020, 0.35 * self.P2020, 0.24 * self.P2020
        Y, A, O = sim.inercia_exacta(0.04, 1 / 27, Y0, A0, O0, np.arange(0, 101))
        _, X = sim.rk4_sistema(sim.Edades(0.04, 0.04, 1 / 27).f, 0, [Y0, A0, O0], 100, 1)
        self.assertLess(np.max(np.abs(Y + A + O - X.sum(axis=1))), 1e-3)

    def test_valores_de_control_de_la_guia(self):
        t = np.array([1900, 1950, 2000, 2050, 2100])
        P = sim.reconstruir(self.r, self.P2020, 2020, t)
        for obtenido, esperado in zip(P, [1582, 2464, 6100, 9552, 10061]):
            self.assertAlmostEqual(obtenido, esperado, delta=1)

    # --- Prueba 2: la población nunca es negativa ---------------------------
    def test_poblacion_no_negativa_en_todas_las_regiones(self):
        for clave in sim.CLAVES_TASA.values():
            a, r = self.d.serie_tasa(clave)
            P = sim.reconstruir(sim.TasaInterpolada(a, r), 100.0, 2020, np.arange(1700, 2101))
            self.assertTrue(np.all(P > 0), clave)

    def test_guarda_detecta_poblacion_negativa(self):
        """Un paso de Euler demasiado grande con decrecimiento fuerte da P < 0 y debe detectarse."""
        with self.assertRaises(sim.PoblacionNegativa):
            sim.euler(lambda t, P: -0.5 * P, 0, 100.0, 20, 5)

    # --- Prueba 3: detección de explosiones ---------------------------------
    def test_detecta_explosion_hiperbolica(self):
        """P' = kP² con k = 5,3e-6 explota cerca de 2022: el simulador debe detenerse."""
        k, T = 5.336e-6, 2022.57
        P1900 = sim.hiperbolico(k, T, 1900)
        with self.assertRaises(sim.ExplosionDetectada):
            sim.rk4(lambda t, P: k * P * P, 1900, P1900, 2100, 0.5, umbral=1e5)

    def test_no_hay_falsas_alarmas_con_datos_reales(self):
        sim.rk4(lambda t, P: self.r(t) * P, 2020, self.P2020, 2100, 1, umbral=1e5)

    # --- Pruebas de datos ---------------------------------------------------
    def test_integridad_de_la_base(self):
        self.assertEqual(len(self.d.tasa), 1793)
        self.assertEqual(self.d.tasa.groupby("clave").size().unique().tolist(), [163])
        self.assertEqual(len(self.d.escenarios), 972)

    def test_interpolacion_rechaza_extrapolar(self):
        with self.assertRaises(ValueError):
            self.r(2101)

    def test_raices_segundo_orden(self):
        m1, m2 = sim.Edades(0.04, 0.04).raices()
        self.assertAlmostEqual(m1, 0, places=12)
        self.assertAlmostEqual(m2, -0.08, places=12)
        self.assertAlmostEqual(sim.Edades(0.04, 0.044).raices()[0], 0.0020, places=4)

    # --- Ajuste de modelos y funciones de alto nivel ------------------------
    def test_ajuste_no_es_prediccion(self):
        """El hiperbólico ajusta mejor 1900-1963 pero predice peor 1964-2023 que el exponencial."""
        t = np.arange(1900, 2024)
        P = sim.reconstruir(self.r, self.P2020, 2020, t)
        aj = sim.ajustar_modelos(t, P)
        self.assertLess(aj["Hiperbólico"]["rmse_ajuste"], aj["Exponencial"]["rmse_ajuste"])
        self.assertGreater(aj["Hiperbólico"]["rmse_prueba"], aj["Exponencial"]["rmse_prueba"])

    def test_capacidad_logistica_razonable(self):
        t = np.arange(1900, 2024)
        P = sim.reconstruir(self.r, self.P2020, 2020, t)
        K = sim.ajustar_modelos(t, P, ventana=(1950, 2023), prueba=(2024, 2023))["Logística"]["parametros"]["K"]
        self.assertTrue(10000 < K < 16000, K)

    def test_proyeccion_region_y_banda(self):
        tabla = sim.proyectar_region(self.d, "COL")
        self.assertAlmostEqual(tabla.simulador.iloc[-1], 47.3, delta=0.1)
        self.assertTrue((tabla.banda_min <= tabla.banda_max).all())
        with self.assertRaises(ValueError):
            sim.proyectar_region(self.d, "XYZ")

    def test_linea_de_comandos(self):
        import io, contextlib
        import simular
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(simular.main(["--region", "COL", "--hasta", "2050"]), 0)
            self.assertEqual(simular.main(["--inercia"]), 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(simular.main(["--region", "XYZ"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
