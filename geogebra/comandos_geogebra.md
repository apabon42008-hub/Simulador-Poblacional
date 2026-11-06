# Comandos para GeoGebra Clásico

## Forma rápida: una sola línea por construcción

Se abre https://www.geogebra.org/classic, se copia una de estas líneas completa en la barra de entrada y se presiona Enter. GeoGebra acepta los nombres de comandos en inglés aunque la interfaz esté en español.

**Construcción 1. Modelo hiperbólico y su explosión (pasos 5, 8 y 12):**

```
Execute({"k=0.00534", "SlopeField(k y^2)", "A=(1900, 1.582)", "f=SolveODE(k y^2, A)", "T=x(A)+1/(k y(A))", "r: x=T", "ZoomIn(1880, -0.5, 2040, 12)"})
```

Se ve el campo de pendientes, la solución que pasa por el dato de 1900 (población en miles de millones) y la recta vertical x = T, donde la curva se dispara. Si se arrastra el punto A sobre la curva, T no cambia.

**Construcción 2. Adultos con deslizador de natalidad (pasos 10, 18 y 22):** se recomienda abrir una ventana nueva de GeoGebra.

```
Execute({"g=0.04", "b=Slider(0.8, 1.2, 0.01)", "SetValue(b, 1)", "Y0=3195.9", "A0=2728.2", "m1=-g+sqrt(g*g*b)", "m2=-g-sqrt(g*g*b)", "c2=(g*Y0-g*A0-m1*A0)/(m2-m1)", "c1=A0-c2", "Adultos(x)=c1*exp(m1*x)+c2*exp(m2*x)", "ZoomIn(-5, 2300, 150, 3700)"})
```

Con b = 1 (reemplazo) la curva de adultos se estabiliza en 2.962 millones; al mover el deslizador a 1,1 crece y a 0,9 decrece.

Para guardar la imagen: menú ☰ > Exportar imagen > PNG (o una captura de pantalla).

---

## Construcciones paso a paso (versión detallada)

Se usa https://www.geogebra.org/classic. Cada línea se escribe en la barra de entrada. Entre paréntesis va el nombre del comando en inglés, por si la interfaz está en ese idioma. En todas las construcciones, x representa el tiempo (años) e y la población.

## 1. Modelo hiperbólico y su explosión (pasos 5, 8 y 12)

Población en miles de millones, de modo que k = 5,34×10⁻³ por mil millones y por año.

```
k = 0.00534
CampoDirecciones(k y^2)                      (SlopeField)
A = (1900, 1.582)
ResuelveEDO(k y^2, A)                         (SolveODE)
T = x(A) + 1 / (k y(A))
Recta(T, x = T)
```

Vista sugerida: x de 1880 a 2040, y de 0 a 12. La curva se dispara al acercarse a la recta vertical x = T (cerca de 2018 con el dato de 1900). Si se mueve el punto A sobre la curva, T no cambia: es la función potencial F(t, P) = t + 1/(kP).

## 2. Logística con capacidad ajustada (pasos 9 y 12)

```
r = Deslizador(0.005, 0.04, 0.001)            (Slider)
K = Deslizador(5, 20, 0.5)
CampoDirecciones(r y (1 - y / K))
ResuelveEDO(r y (1 - y / K), (1950, 2.464))
```

Valores de referencia: K = 12,5 y r = 0,0276 (ajuste 1950-2023 del código). Se observan los dos equilibrios, y = 0 (inestable) e y = K (estable).

## 3. Comparación de modelos con los datos (pasos 4 y 6)

Se pega en la Hoja de cálculo de GeoGebra la columna anio y P (en miles de millones) de `resultados/reconstruccion_mundo.csv` para 1900-2023, y se crea la lista de puntos L. Luego:

```
AjusteExp(L)                                   (FitExp)
AjusteLogístico(L)                             (FitLogistic)
```

Los ajustes se comparan visualmente con la curva hiperbólica del punto 1.

## 4. Jóvenes y adultos con deslizadores (pasos 10, 18 y 22)

Población en millones; t en años desde 2020.

```
γ = 0.04
b = Deslizador(0.8, 1.2, 0.01)
β = b γ
Y0 = 3195.9
A0 = 2728.2
m1 = -γ + sqrt(γ β)
m2 = -γ - sqrt(γ β)
c2 = (γ Y0 - γ A0 - m1 A0) / (m2 - m1)
c1 = A0 - c2
Adultos(x) = c1 exp(m1 x) + c2 exp(m2 x)
```

Con b = 1 la curva de adultos se estabiliza en 2.962 M; con b = 1,1 crece y con b = 0,9 decrece. Para la trayectoria en el plano (Y, A) con reemplazo:

```
S = Y0 + A0
Curva(S - (S/2 + (A0 - S/2) exp(-2γ t)), S/2 + (A0 - S/2) exp(-2γ t), t, 0, 150)      (Curve)
```

Es un segmento de pendiente −1 que termina en la recta A = Y.

## 5. Inmigración constante (paso 20)

```
m = Deslizador(0, 1, 0.05)
Particular(x) = m / 2 x
```

Con β = γ, la respuesta a una inmigración constante es una recta: los adultos crecen sin límite.

Para el informe y el video no basta una captura: debe explicarse qué modelo se probó, por qué y qué se concluyó (guía, sección 8).
