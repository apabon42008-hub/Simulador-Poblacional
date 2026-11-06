# Simulador de escenarios de población

Proyecto de Aula PA5 · Ecuaciones Diferenciales · Universidad de Santander (UDES) · 2026B
Ingeniería de Software · Grupo 2 · Docente: Prof. Botello

**Equipo:** Juan Camilo Castaño Rojas, Leder Andrés Cortes Cortes, Giovanny Esteban Arias Córdoba, Andrés Felipe Pabón Barbosa, Camilo José Luna y Andrés.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/apabon42008-hub/Simulador-Poblacional/blob/main/simulador_poblacional.ipynb)

En este repositorio se encuentra el simulador de población desarrollado para una entidad de planeación que debe decidir cuántos colegios, hospitales y cupos de pensión serán necesarios a 10, 30 y 80 años. Con el simulador se integra la tasa de crecimiento de 11 regiones (1700-2100), se compara el resultado con tres escenarios de la ONU y se modela la inercia demográfica con un sistema por edades de segundo orden. Todas las cifras del informe, del Excel y de las diapositivas se obtienen con este código.

## Resultados principales

| Resultado | Valor |
|---|---|
| Población mundial reconstruida en 1950 | 2.464 millones (Gapminder: 2.499) |
| Máximo de población según la tasa | 10.169 millones en 2084 |
| Error en 2100: Euler / RK4 con paso de 1 año | +43,6 millones / menos de 0,0001 millones |
| Modelo hiperbólico de 1960 ajustado | k = 5,34 × 10⁻⁶, explosión en T = 2022,6 |
| Colombia en 2100: tasa integrada / escenarios ONU | 47,3 millones / de 28,4 a 53,0 millones |
| Inercia con fecundidad de reemplazo | de 7.795 a 9.123 millones |

## Ejecución

Se requiere Python 3.10 o superior.

```bash
git clone https://github.com/apabon42008-hub/Simulador-Poblacional.git
cd Simulador-Poblacional
pip install -r requirements.txt
python -m unittest pruebas -v        # 16 pruebas automáticas
python ejecutar_analisis.py          # recalcula todo y regenera resultados/ y las figuras
```

### Línea de comandos

```bash
python simular.py --listar                                   # regiones disponibles
python simular.py --region COL                               # Colombia, RK4, paso 1, hasta 2100
python simular.py --region MUN --metodo euler --paso 5       # comparación de métodos y pasos
python simular.py --region COL --grafica col.png --csv col.csv
python simular.py --inercia                                  # modelo por edades con reemplazo
python simular.py --inercia --beta 1.1 --inmigracion 0.5     # otra natalidad y migración
```

Ejemplo de salida:

```
Región: Colombia  |  método: RK4  |  paso: 1.0 años
   Año   Simulador      Exacta       Baja  Reemplazo  Constante
  2020        50,9        50,9       50,9       50,9       50,9
  2050        59,7        59,7       50,8       54,1       58,1
  2100        47,3        47,3       28,4       38,5       53,0
```

### Cuaderno interactivo

Con el botón «Abrir en Colab» se abre el cuaderno `simulador_poblacional.ipynb`. Al ejecutar las celdas en orden se clona el repositorio y aparecen controles para cambiar la región, el método, el paso, la natalidad, la inmigración y la ventana de ajuste del modelo de 1960.

### GeoGebra

Los comandos para reproducir cada modelo en GeoGebra Clásico están en [`geogebra/comandos_geogebra.md`](geogebra/comandos_geogebra.md).

## Estructura

```
Simulador-Poblacional/
├── simulador.py                 Núcleo: datos, interpolación, integral, Euler, RK4, modelos y guardas
├── simular.py                   Línea de comandos
├── ejecutar_analisis.py         Pasos 1 a 23 de la guía; genera resultados y figuras
├── pruebas.py                   Pruebas automáticas
├── interactivo.py               Gráficas con controles para el cuaderno
├── simulador_poblacional.ipynb Cuaderno para Google Colab
├── requirements.txt
├── datos/
│   └── PA5_Simulador_poblacion.xlsx   Base original entregada por la docente, sin modificaciones
├── resultados/
│   ├── resultados.json          Valores clave de cada paso
│   ├── *.csv                    Tablas de trabajo
│   └── figuras/                 Figuras f01 a f14
├── geogebra/
│   └── comandos_geogebra.md
├── latex/                       Fuentes del informe y de las diapositivas
└── Informe_tecnico.pdf          Informe técnico
```

## Modelos

| Modelo | Ecuación | Método de solución |
|---|---|---|
| Exponencial | P' = rP | Variables separables |
| Tasa variable | P' = r(t)P | Lineal, factor integrante; regla del trapecio |
| Logística con tasa variable | P' = r(t)P(1 − P/K) | Factor integrante 1/[P(K − P)] y Bernoulli |
| Hiperbólico (von Foerster, 1960) | P' = kP² | Separable y exacta: F(t, P) = t + 1/(kP) |
| Por edades | A'' + 2γA' + γ(γ − β)A = γm | Coeficientes constantes, operador D y superposición |

## Pruebas automáticas

1. Comparación con soluciones exactas. Con RK4 deben reproducirse la exponencial, la integral de la tasa, la logística resuelta por dos métodos, la inercia exacta y los valores de control de la guía.
2. Población no negativa. Se revisa en las 11 regiones, y la guarda debe activarse cuando se usa un paso de Euler demasiado grande.
3. Detección de explosiones. La integración del modelo hiperbólico debe detenerse antes de 2022,6, sin falsas alarmas con datos reales.
4. Ajuste frente a predicción. El modelo hiperbólico se ajusta mejor a 1900-1963, pero predice peor 1964-2023 que el exponencial.

## Unidades y supuestos

El tiempo se expresa en años, la población en millones de personas y las tasas en 1/año.

Los siguientes valores son supuestos del escenario definidos en la guía, no datos:

- γ = 0,04 1/año y δ = 1/27 1/año.
- Estructura de edades de 2020: 41 % / 35 % / 24 %.
- Inmigración m = 0,1 + 0,05 sen(2πt/10) millones/año.
- Parámetros de la sala de servidores.
- Velocidad inicial de 20 m/s del proyectil.

La capacidad K de la logística no es un supuesto: se ajusta con la población de 1950-2023 (K ≈ 12.509 millones).

## Fuentes de datos

- Our World in Data, «Population growth rate», con base en HYDE 3.3 (antes de 1800), Gapminder v7 (1800-1949) y ONU WPP 2024 (desde 1950). https://ourworldindata.org/grapher/population-growth-rate
- Naciones Unidas, *World Population Prospects 2019*: escenarios de fecundidad constante, reemplazo inmediato y fecundidad baja. https://population.un.org/wpp/

La tasa y los escenarios provienen de revisiones distintas de la ONU, lo que explica parte de las diferencias entre ellos.
