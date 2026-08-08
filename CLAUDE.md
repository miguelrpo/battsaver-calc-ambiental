# CLAUDE.md — Calculadora Ambiental Battsaver

Instrucciones de contexto para trabajar en `Calculadora_Ambiental_Battsaver_v1.html`, la calculadora de impacto ambiental positivo (CO₂ y escoria tóxica evitados) de Battsaver. Este archivo es distinto del `CLAUDE.md` raíz del proyecto (ese gobierna voz/marca de documentos .docx/.pptx/.xlsx) y también distinto del `CLAUDE.md` de la calculadora comercial (`Calculadora_Battsaver_v5.html`) — este gobierna específicamente esta pieza.

---

## 1. Qué es este archivo

Un **HTML autocontenido de una sola página** (CSS inline en `<style>`, JS vanilla inline en `<script>`, sin build step, sin dependencias externas salvo la fuente de Google Fonts). Se abre directamente en el navegador o se sube como artifact. No hay backend: todo el cálculo ocurre en el cliente.

Uso previsto: **herramienta de venta y divulgación**, para mostrarle a un cliente (o usarla internamente en piezas de marketing) cuánto CO₂ y cuánta escoria tóxica deja de generarse al usar Battsaver, en lugar de reemplazar baterías con la frecuencia habitual. Comparte look & feel con la calculadora comercial pero es una herramienta independiente — no comparte estado ni cálculos con ella.

No hay framework (no React/Vue) ni `package.json`. Sí hay **una verificación automatizada**: `verificar.py` (ver §7).

---

## 2. Modelo ambiental (fuente de verdad)

### Catálogo por tipo de vehículo (peso de batería de referencia)
```js
const SKUS = [
  {name:"12V · 10W", veh:"carro pequeño", battKg:12, dual:false},
  {name:"12V · 20W", veh:"camioneta / camión / náutico", battKg:20, dual:true},
  {name:"24V · 20W", veh:"camión 24V", battKg:20, dual:true},
].map(s => Object.assign(s, {
  co2 : +(s.battKg*EF_CO2_PER_KG).toFixed(2),
  slag: +(s.battKg*SLAG_PER_KG).toFixed(2)
}));
```
`dual:true` habilita el selector "1 batería / 2 baterías" (camiones que montan doble batería).

**La moto está fuera del alcance a propósito — decisión de Miguel, agosto 2026.** El segmento arranca en **carro pequeño (12 kg)**. Antes moto y carro pequeño compartían un bucket de 10 kg que inflaba el caso moto ~2× y era, además, el SKU que abría por defecto; la primera corrección fue separarlos en dos entradas (moto a 5 kg), pero la decisión final fue **no calcular impacto ambiental para moto en ningún caso**. El equipo `12V · 10W` sigue sirviendo motos comercialmente —y la calculadora comercial las mantiene en su catálogo—; lo que no se hace es cuantificarles impacto ambiental aquí. **No volver a agregar la moto sin pedirlo explícitamente.**

La lista es de **tipos de vehículo**, no de referencias de producto: dos entradas podrían compartir el mismo equipo si hiciera falta.

**`co2` y `slag` ahora se derivan en runtime** de `battKg`. Antes venían precalculados a mano y eso obligaba a recalcular dos números cada vez que cambiaba un peso — un footgun que ya no existe. No volver a escribirlos a mano.

### Factores de emisión (reencuadrados en agosto 2026 — ver §3)
```js
const PB_FRACTION      = 0.60;          // plomo como fracción del peso de batería
const EF_CO2_PER_KG_PB = 0.67;          // kg CO2e por kg de PLOMO (Ballantyne et al. 2018)
const EF_CO2_PB_RANGE  = [0.67, 1.00];  // piso Ballantyne → techo Boliden
const SLAG_PER_KG_PB   = 0.25;          // escoria como fracción del PLOMO (decisión de negocio)
const SLAG_PB_RANGE    = [0.10, 0.35];  // fracción del PLOMO producido (Pan et al. 2019)
const PB_RANGE         = [0.60, 0.65];  // banda del propio contenido de plomo

// derivados sobre peso total de batería, que es la base del cálculo
const EF_CO2_PER_KG = 0.40;             // = 0,67 × 0,60
const EF_CO2_RANGE  = [0.40, 0.65];     // piso×piso, techo×techo con PB_RANGE
const SLAG_PER_KG   = 0.15;             // = 0,25 × 0,60 — decisión de negocio
const SLAG_RANGE    = [0.06, 0.23];     // = [0,10, 0,35] × PB_RANGE
const EXT_FACTOR    = 2;                // extensión de vida, igual que la comercial
```

**Por qué los factores viven ahora sobre base plomo.** La literatura de fundición secundaria reporta emisión y escoria **por kg de plomo**, no por kg de batería. Antes la calculadora usaba 1,5 kg CO₂e/kg de *batería* con banda 0,9–2,5; ese orden de magnitud corresponde a **fabricar** una batería, no a reciclarla. Declarar el factor sobre base plomo y convertirlo con `PB_FRACTION` explícito es lo que hace auditable la frontera — y confundir producción con reciclaje es justamente lo primero que un director de sostenibilidad busca.

`EXT_FACTOR` se extrajo como constante y la tasa evitada se escribe en su **forma general** `(1 − 1/k)/vida`, no como `1/(2·vida)`: numéricamente idéntica hoy, pero correcta si el factor cambia. Sin eso, el mandato de §9 de coordinar el ×2 con la calculadora comercial no era cumplible sin reescribir fórmulas a mano.

### Equivalencias divulgativas
```js
const TREE_KG_YEAR = 22;   // kg CO2 que absorbe un árbol maduro al año
const CAR_KG_KM    = 0.17; // kg CO2 por km de un carro a gasolina promedio
```

### Fórmula de baterías salvadas
Sin Battsaver, cada posición de batería se reemplaza `1/vida` veces al año. Con Battsaver la vida se duplica (mismo supuesto de la calculadora comercial: `EXT_FACTOR = 2`), o sea `1/(2·vida)` reemplazos al año. La diferencia es lo que se evita:

```
posiciones      = vehículos × bateríasPorVehículo   (1 o 2, según dual)
evitadasPorAño  = 1 / (2 × vidaSinBattsaver)
bateríasSalvadas = posiciones × evitadasPorAño × horizonteAños

kgEvitados   = bateríasSalvadas × battKg
co2Evitado   = kgEvitados × EF_CO2_PER_KG   (0,40)
escoriaEvit. = kgEvitados × SLAG_PER_KG     (0,15)
```

Este modelo es deliberadamente el mismo de la calculadora comercial (vida útil que se duplica), para que ambas herramientas cuenten la misma historia con el mismo cliente.

---

## 3. Verificación de supuestos (revisada en agosto 2026)

> **Historial.** La verificación de julio 2026 dio por buenos los cinco supuestos. Una auditoría técnica posterior (agosto 2026) encontró que **dos de esas conclusiones eran incorrectas** y que **tres de las cuatro bandas declaradas no reproducían ninguna fuente**. Lo que sigue reemplaza aquella tabla. Los valores puntuales de escoria (15%), árbol (22) y carro (0,17) **no se movieron**; lo que cambió es el factor de CO₂, todas las bandas y las atribuciones.

### Estado vigente

| Supuesto | Valor | Banda | Fuente real | Estado |
|---|---|---|---|---|
| CO₂e del reciclaje | **0,40 kg/kg de batería** | 0,40 – 0,65 | Ballantyne et al. 2018, *R. Soc. Open Sci.* 5:171368 (0,55 fundición + 0,12 refinación = 0,67 kg CO₂/kg Pb); Boliden (<1 kg CO₂/kg Pb en reciclado) | **Corregido.** Antes 1,5 con banda 0,9–2,5 |
| Plomo en la batería | **60% del peso** | 60% – 65% | composición estándar de batería SLI | Supuesto propio nuevo, necesario para convertir de base plomo a base batería |
| Escoria de fundición | **15% del peso** (= 25% del plomo) | 6% – 23% | Pan et al. 2019, *Resour. Conserv. Recycl.* 146:140-155 (100–350 kg/t de plomo producido) | Valor sin cambio; **banda corregida** (antes 8%–15%) |
| Pesos de referencia | **12 / 20 kg** | — | pesos de mercado por segmento | **Corregido**: el bucket de 10 kg (moto + carro pequeño) se deshizo; la moto quedó fuera de alcance y el mínimo es carro pequeño a 12 kg |
| Árbol maduro | **22 kg CO₂e/año** | 10 – 40 | **Arbor Day Foundation** (>48 lb/año) | Valor sin cambio; **atribución corregida** |
| Carro a gasolina | **0,17 kg CO₂e/km** | 0,11 – 0,25 | EEA (107 g/km WLTP, autos nuevos UE) y US EPA (~400 g/milla = 0,249 kg/km) | Valor sin cambio; **banda corregida** (antes 0,12–0,17) |
| Extensión de vida | **×2** | sin banda externa | ninguna — supuesto de producto | Sin cambio. Correctamente declarado como propio |

### Los dos errores que se corrigieron, y por qué importaban

**1. Confusión de frontera en el factor de CO₂ (el más grave).** El factor estaba expresado por kg de *batería*, pero toda la evidencia de fundición secundaria está por kg de *plomo* y es mucho menor: ~0,67 kg CO₂/kg Pb, que con 60% de plomo da ~0,40 kg CO₂e/kg de batería. La banda declarada (0,9–2,5) **ni siquiera contenía** ese valor: su piso estaba por encima. Ese orden de magnitud corresponde a **fabricar** una batería, no a reciclarla. Consecuencia: la cifra del hero estaba ~3,7× alta, en el número principal de toda la pieza. Hoy el factor se declara sobre base plomo, se convierte con `PB_FRACTION` explícito, y se adopta el **piso** de la banda — así que el CO₂e mostrado es el mínimo defendible.

**2. Cita mal atribuida en el factor de árbol.** La ficha decía "US EPA, Greenhouse Gas Equivalencies Calculator". El EPA **no publica 21,7 kg/árbol/año**: publica 0,060 t CO₂ por árbol urbano *plantado*, promediado sobre 10 años de crecimiento (~6 kg/año), y desaconseja explícitamente usarlo para reforestación. El 22 kg/año trazable es de la **Arbor Day Foundation**. Era la única cita nominal de toda la tabla, o sea la primera que un auditor abre — y apuntaba a un organismo real que dice otra cosa. Eso es peor que no citar, y es la variante más cara de la prohibición de §9 sobre citas inventadas. El KPI además decía "Equivale a plantar N árboles", mezclando el marco de plantación (~6 kg el primer año) con el de árbol maduro (22 kg); ahora dice "Equivale a un año de N árboles maduros".

### Dirección de uso de cada factor (actualizada)

"Extremo alto del rango" **no significa lo mismo** en todos los factores: depende de si el factor multiplica o divide el resultado.

| Factor | Cómo se usa | Un valor alto… | Posición actual | Efecto neto |
|---|---|---|---|---|
| 0,40 kg CO₂e/kg | **multiplica** el CO₂e del hero | infla el resultado | **piso** de 0,40–0,65 | **conservador** |
| 60% de plomo | **multiplica** ambas cifras | infla el resultado | piso de 60%–65% | conservador |
| 15% escoria | **multiplica** la escoria destacada | infla el resultado | mitad alta de 6%–23% | **sigue siendo el supuesto menos conservador** |
| 22 kg/árbol | **divide** (CO₂e ÷ 22) | da *menos* árboles | centro de 10–40 | neutro |
| 0,17 kg/km | **divide** (CO₂e ÷ 0,17) | da *menos* km | centro de 0,11–0,25 | neutro |

Nota sobre el 0,17: el análisis de julio 2026 (que lo declaraba conservador por ser divisor) tenía la **lógica correcta pero el dato de entrada equivocado**. Con la banda real (0,11–0,25, no 0,12–0,17), 0,17 no está en el tope sino en el centro, así que el factor es neutro, no conservador. El valor no se movió; la declaración sí.

Si se audita esta calculadora externamente, el punto a explicar primero sigue siendo la escoria al 15% — es el único factor que empuja el resultado hacia arriba.

---

## 4. Reglas de UI/UX ya decididas

- El selector "Baterías por vehículo" (1/2) **solo aparece** para SKUs con `dual:true` (camiones). Para moto/carro pequeño se oculta y se fuerza `perVeh=1`.
- El bloque de escoria tiene **su propio tratamiento visual** (caja navy destacada, ícono, texto largo) porque es el argumento diferenciador que Miguel pidió resaltar: "residuo indestructible" / "pasivo ambiental eterno". No debe quedar como una fila más del breakdown ni perder ese peso visual.
- El hero muestra el CO₂ en **toneladas si ≥1 t**, si no en kg — no mostrar siempre en kg cuando la cifra es grande.
- Las equivalencias (árboles, km no recorridos) son **apoyo divulgativo**, secundarias al dato duro de CO₂ y escoria — no deben competir en tamaño visual con el hero ni con el bloque de escoria.
- El horizonte de análisis (slider de 1 a 10 años) es independiente de la vida de la batería; ambos controles alimentan la misma fórmula.
- Botón "⤓ Guardar PDF" con `window.print()` y hoja de impresión dedicada, igual que en la calculadora comercial.
- El bloque de **metodología** (§11) va **colapsado por defecto** — decisión explícita de Miguel: la calculadora abre limpia, sin el anexo técnico encima, y la metodología se despliega a demanda. Su estética es deliberadamente sobria (sin sunset, sin cifras grandes, sin hero): que se lea como anexo técnico y no como pieza de venta es parte del argumento frente a un auditor de sostenibilidad.
- **División de trabajo entre `#breakdown` y la cadena de cálculo (julio 2026).** El `#breakdown` de la tarjeta de resultados muestra **solo tasas unitarias de referencia** (peso de la batería, CO₂ por batería salvada, escoria por batería salvada). No lleva totales: las "baterías salvadas" ya están en el KPI y el CO₂ acumulado ya está en el hero, ambos en la misma tarjeta, y el `.pitch` de cierre repite las dos cifras finales en prosa. La aritmética completa que produce esos totales vive **únicamente** en `#mSteps` (§11). Se revisó explícitamente si la cadena de cálculo era redundante con el breakdown y la conclusión fue la inversa: el breakdown tenía tres de cinco filas duplicadas dentro de su propia tarjeta, y se recortaron esas dos filas (`Baterías salvadas`, y la fila total con su clase `.brow.tot`, cuyo CSS se eliminó por quedar muerto).

---

## 5. Identidad visual

Comparte paleta y logo con la calculadora comercial (`Calculadora_Battsaver.html`, repo `Calculadora-Battsaver`). Paleta migrada (2026-07-11) al design system BATTSAVER más nuevo (mismo entregado como `CLAUDE-CODE-INSTRUCCIONES.md` en el otro repo), que reemplaza el navy/teal/mint anterior del Manual de Marca:

- `--bs-blue #003B5C` (Pantone 302 C) protagonista — header, hero, sticky bar.
- `--bs-ink #0B1D35` reemplaza al negro puro.
- `--bs-electric #16A3CC` (+ soft/tint) — acento de **producto/UI**: focus, slider, ícono del bloque de escoria (antes usaba el teal viejo vía `rgba(14,140,127,...)`, ahora `rgba(22,163,204,...)`).
- `--bs-sunset*` (gradiente `#FFD9A6→#E2643C`) — acento **sunset**, usado en: eyebrow del hero, **label `.slag .t` ("Escoria tóxica que no se genera")** — a pedido explícito de Miguel, para que ambos labels destacados sobre navy (CO₂ y escoria) se vean consistentes —, tagline del header ("Más vida para tu batería"), la caja `.pitch` de cierre y el valor destacado de la sticky bar móvil.
- Ámbar reservado exclusivamente para advertencias reales (no se usa en esta calculadora). El **fondo** de la caja de escoria sigue siendo **navy**, no ámbar, a propósito: no es una advertencia, es una cifra dura de impacto evitado (ver §4 y §9). Solo el label de texto usa sunset, no el fondo de la caja.
- Sombras tintadas de azul 302 C (`rgba(0,59,92,...)`), nunca negras.
- **Implementación**: los tokens `--bs-*` viven en `:root`; las variables antiguas (`--navy`, `--teal`, `--mint`, etc.) quedan como alias hacia los tokens nuevos — no se tocó lógica, estructura ni ninguna regla que ya usara esas variables.

Tipografía oficial **Cloud**, sustituida temporalmente por Plus Jakarta Sans con `@font-face` placeholder listo para el archivo oficial. Logo oficial incrustado en base64 para mantener el archivo autocontenido.

> **Pendiente compartido con la calculadora comercial:** cuando Miguel entregue la fuente Cloud oficial, actualizar el `@font-face` en ambos archivos.

---

## 6. Layout responsivo

- Grid de dos columnas en desktop (inputs / resultados), una columna en móvil (`max-width:860px`).
- Barra sticky inferior en móvil con el CO₂ evitado y scroll a resultados al tocar.
- Selector de SKU pasa a una columna en móvil (a diferencia de v5, que usa grid 2×2 para sus segmentos de 3–4 opciones).
- Hoja de impresión oculta la barra sticky y el botón de imprimir.

---

## 7. Convenciones de desarrollo

- Formato numérico con `toLocaleString("es-CO", …)`, decimales con coma.
- **Decimales solo cuando el número los necesita** (agosto 2026, decisión de Miguel): `fmt(n, dec)` trata `dec` como **máximo**, no como mínimo (`minimumFractionDigits: 0`). Un entero se imprime entero ("96 kg de CO₂e", no "96,0") y 0,2 se imprime "0,2" y no "0,200". La **precisión del cálculo no cambia** —`dec()` sigue gobernando el redondeo real—; lo que desaparece son los ceros finales. Como el valor no se toca, la cadena sigue cerrando.
- **`verificar.py` antes de cada entrega** (`pip install playwright && python3 verificar.py`). Comprueba los 10 invariantes que las auditorías de agosto 2026 dejaron como innegociables: la cadena cierra con los operandos que muestra, el modelo no se desvía >1% de la matemática exacta, la tarjeta y la cadena imprimen el mismo número, las tasas del breakdown reconcilian con el hero, las entradas hostiles quedan saneadas, la accesibilidad estructural sigue en pie, la metodología viaja en el PDF, no hay desbordamiento a 320px (WCAG 1.4.10), no hay errores de página, y la divergencia con la calculadora comercial es exactamente el ×2 del doble batería.
  > **Por qué existe.** Tres regresiones se colaron entre rondas de revisión manual y las tres eran de esta clase. El script recalcula el modelo de referencia **de forma independiente del HTML**: si el código de la calculadora tiene un error, el verificador no lo hereda. Sale con código 1 si algo falla, así que se puede enganchar a un hook.
  > Sigue valiendo la pena una pasada visual con capturas en desktop y móvil para lo que ningún assert cubre.
- Un solo archivo HTML; versiones anteriores (si las hay) se conservan como archivos separados en la misma carpeta, no se sobrescriben. Desde julio 2026 la carpeta sí está versionada con git (ver §10) — eso no cambia la convención de no sobrescribir versiones con nombres distintos.

---

## 8. Pendientes conocidos

1. **Fuente Cloud oficial** — ver §5.
2. **Comparativo con calculadora comercial**: podría valer la pena, a futuro, una vista que combine ahorro en pesos (v5) + impacto ambiental (este archivo) en una sola propuesta, pero hoy son herramientas separadas y no comparten estado — no fusionar sin pedirlo explícitamente.
3. **Botón de reinicio** de inputs a valores por defecto — no implementado.
4. **Accesibilidad de segmented controls** (`.seg`): mismo pendiente que en v5, impacto bajo para uso comercial en vivo.
5. ~~**Revisión del factor de 0,17 kg CO₂/km**~~ — **cerrado (julio 2026)**. Se analizó la dirección de uso (ver §3): al ser divisor, 0,17 produce *menos* kilómetros equivalentes, así que es la opción conservadora. Bajarlo a 0,12–0,15 inflaría la cifra. Se deja en 0,17 y queda declarado como conservador en la tabla de factores de la UI.
6. **Factor de escoria al 15%** — *abierto, decisión de negocio*. Sigue siendo el único supuesto que empuja el resultado hacia arriba. Con la banda corregida (6%–23%, Pan et al. 2019) el 15% ya **no es el tope** —como se creía en julio— pero sí queda por encima del centro aritmético (14,5%) y de la media geométrica (11,7%). La UI lo declara con chip ámbar "Mitad alta" y muestra la banda completa, que es la salida honesta. Mover el valor puntual al centro restaría ~25% de la cifra de escoria. No cambiar sin decisión explícita de Miguel.
7. ~~**Fuentes nominales de la tabla de factores**~~ — **cerrado (agosto 2026)**. `FACTORS` ahora cita por nombre: Ballantyne et al. 2018 (*R. Soc. Open Sci.* 5:171368) para el CO₂ del reciclaje, Boliden para el techo de esa banda, Pan et al. 2019 (*Resour. Conserv. Recycl.* 146:140-155) para la escoria, Arbor Day Foundation para el árbol, y EEA + US EPA para el carro. Todas se verificaron contra la fuente antes de escribirlas — **ninguna se inventó**, que sigue siendo la regla de §9.
   > **Salvedad de trazabilidad:** las cifras se confirmaron por búsqueda con extracto textual, no abriendo el PDF original (el entorno de trabajo tenía bloqueado el acceso directo a esos hosts). Antes de usar la calculadora en una auditoría formal conviene abrir Ballantyne y Pan y confirmar cifra y frontera de primera mano.
   > **Corrección de agosto 2026 sobre Ballantyne:** el paper da 0,55 (fundición) + 0,12 (refinación) para plomo **primario**, y advierte literalmente *"While these values will be different than those for recycled (secondary) lead"*. La ficha los presentaba como si fueran del reciclaje. **El valor no se movió** —0,40 kg CO₂e/kg sigue por debajo del `<1 kg CO₂/kg Pb` que Boliden declara para reciclado, que es el único dato nominal sobre secundario— pero la ficha ahora dice que es una **cota inferior por proxy**, y `#mSens` dejó de afirmar que es "la cifra más baja que las fuentes sostienen", que ninguna fuente sostenía.
8. **Huella del propio Battsaver** — *abierto y ahora cuantificado, agosto 2026*. Una auditoría estimó que un módulo c-Si de 10 Wp tiene una huella cradle-to-gate de ~0,36–0,81 kg CO₂e/Wp, o sea **3,6–8,1 kg CO₂e solo el módulo**, sin controlador, carcasa, cableado ni flete. En el caso por defecto de la calculadora el resultado son 96,0 kg CO₂e para 20 equipos = **4,8 kg CO₂e evitados por equipo en 5 años**: del mismo orden. Con el factor en 0,40 (antes 1,5) esto pesa 3,7× más que en julio.
   > **Qué se hizo y qué no.** Se corrigió la frase de `.mintro` que afirmaba que todo lo excluido "solo puede aumentar el impacto real" —falsa, porque esta exclusión resta— y el bullet correspondiente ahora dice que en horizontes cortos puede ser del mismo orden que lo evitado. **No se publicó la cifra 3,6–8,1**: viene de un módulo c-Si genérico, no del equipo real de Battsaver, y sustituir una afirmación no verificada por otra no mejora nada. Para cerrar esto hace falta la huella medida del producto.

---

## 8.bis Criterio de rigor — cuánto es suficiente (agosto 2026)

**Decisión explícita de Miguel.** El objetivo es **validez a grandes rasgos, coherencia interna y matemáticas que no fallen**. No es exhaustividad ni cobertura defensiva de todo debate abierto.

- Los factores tienen que ser **defendibles en su orden de magnitud** y estar bien atribuidos. No tienen que resolver discusiones que la propia literatura tiene abiertas: buena parte de la ciencia de ACV lo está, y pretender cerrarla dentro de una calculadora comercial es peor que declarar el rango.
- Lo que **sí** es innegociable: que la aritmética cierre, que la misma magnitud no aparezca con dos valores distintos en la página, y que ninguna cita esté mal atribuida.
- **No acumular salvedades.** Cada advertencia nueva le resta peso a las que ya están. Las declaraciones incómodas de §11 se conservan porque son pocas y cada una carga un argumento; una lista larga de matices se lee como inseguridad, no como rigor, y ese es el efecto contrario al buscado.
- El **encabezado va en voz de marca, directo y en segunda persona** ("CO₂e que dejas de emitir"). Los matices contables —que es una emisión evitada aguas abajo y no una reducción del inventario propio— van en la metodología, que es donde el auditor los busca. No convertir el hero en una nota al pie.

Si una recomendación de auditoría pide más precisión de la que el dato de entrada soporta, o más salvedades de las que el argumento aguanta, la respuesta correcta es no implementarla y dejar constancia aquí.

---

## 9. Qué NO hacer sin confirmar explícitamente

- No cambiar el **fondo** del bloque de escoria a ámbar ni a sunset — sigue siendo navy a propósito (ver §4/§5). Ámbar es solo para advertencias reales. El label de texto (`.slag .t`) sí usa sunset, a pedido explícito de Miguel (ver §5) — eso no aplica al fondo de la caja.
- No usar sunset en controles de UI de producto (inputs, sliders) — solo en los puntos de marketing/labels destacados ya definidos en §5.
- No mostrar cantidad de baterías salvadas sin desglosar por posición/vehículo — el KPI "Baterías salvadas" siempre debe traer la nota de cuántas posiciones y vehículos hay detrás.
- No cambiar el supuesto de "la vida se duplica con Battsaver" sin coordinarlo con la calculadora comercial — ambas herramientas deben seguir contando la misma historia de negocio.
- No agregar el impacto de fabricar la batería nueva de reemplazo (minería, fundición primaria) a menos que se pida explícitamente — el modelo actual es deliberadamente conservador y cubre solo el reciclaje de la batería que se deja de desechar.
- No cambiar "tú/tu" de vuelta a "usted/su".
- No tocar los factores de §3 (0,40 kg CO₂e/kg de batería sobre base plomo, 15% escoria, 22 kg/árbol, 0,17 kg/km) sin dejar registro del cambio en esta misma tabla — son supuestos de negocio verificados, no bugs. Si se cambia un factor, actualizar también su **banda** (`EF_CO2_RANGE`, `SLAG_RANGE`) y su ficha en `FACTORS`.
- **No suavizar ni quitar las declaraciones incómodas del bloque de metodología** (§11): que la escoria usa el tope de su banda, que la extensión ×2 es supuesto propio y no literatura, y que no se resta la huella del propio Battsaver. Son precisamente lo que hace creíble el resto de la herramienta ante un auditor entrenado en detectar greenwashing — quitarlas la devuelve a folleto.
- **No inventar citas ni referencias** para llenar la columna de fuentes. Vago pero honesto le gana siempre a preciso pero fabricado: una cita falsa detectada destruye la credibilidad de toda la calculadora. Y una cita **mal atribuida** es todavía peor que una vaga: la ficha del árbol decía "US EPA" cuando el EPA publica otra cifra sobre otra frontera (ver §3), y era la única fuente nominal de la tabla, o sea la primera que un auditor abre.
- **No reescribir el texto de la caja de escoria** ("residuo indestructible" / "pasivo ambiental eterno"). Una auditoría de agosto 2026 propuso suavizarlo porque existe literatura revisada sobre valorización de escoria de plomo (recuperación de metales, geopolímeros, vitrocerámicas), lo que hace el absoluto técnicamente falsable; **Miguel decidió conservar la formulación original** por peso comercial. Queda declarado aquí: si un auditor de sostenibilidad objeta el absoluto, la salida es la formulación calibrada —"residuo peligroso que en la práctica termina en disposición controlada, con uso real marginal y riesgo de lixiviación"—, no defender el "no se recicla".
- **No devolver el factor de CO₂ a base "por kg de batería" sin su conversión explícita** desde base plomo (§2/§3). Esa era la confusión de frontera que inflaba el hero ~3,7×.
- **No volver a meter la moto en `SKUS`** (§2). El segmento arranca en carro pequeño por decisión explícita de Miguel; que el equipo `12V · 10W` sirva motos comercialmente no significa que aquí se les cuantifique impacto ambiental.
- No abrir el bloque de metodología por defecto (va colapsado, ver §4) ni sacarlo del PDF (al imprimir sí se fuerza abierto).
- **No borrar la cadena de cálculo (`#mSteps`) por parecer redundante con el breakdown**, ni devolverle al `#breakdown` las filas de total que se le quitaron (ver §4). Ya se analizó: el paso 2 (`1 ÷ (2 × vida)`, la tasa de reemplazos evitados) no aparece en ningún otro lugar de la página, y los pasos 5–6 son el único punto donde los factores de §3 se conectan con la cifra del hero —el breakdown usa las tasas por SKU y nunca muestra que `co2 = battKg × EF_CO2_PER_KG`. Sin la cadena, la tabla de factores no alcanza para reproducir el resultado y el anexo que viaja en el PDF deja de ser auditable. Además el párrafo que sigue a `#mSteps` arranca con "El paso 2 es la clave del modelo…" y quedaría huérfano.

---

## 10. Repositorio y despliegue

Desde julio 2026 la carpeta está en git y publicada:

- **Repo GitHub**: [github.com/miguelrpo/battsaver-calc-ambiental](https://github.com/miguelrpo/battsaver-calc-ambiental) (público, remoto `origin` por SSH).
- **URL en vivo (GitHub Pages)**: https://miguelrpo.github.io/battsaver-calc-ambiental/ — servida desde la raíz de la rama `main`, sin build step (Pages sirve los archivos tal cual).
- `index.html` es únicamente una redirección (`<meta http-equiv="refresh">`) hacia `Calculadora_Ambiental_Battsaver_v1.html`. Existe solo para que la raíz del sitio de Pages resuelva a algo — **no renombrar** `Calculadora_Ambiental_Battsaver_v1.html` a `index.html`, porque rompería la convención de versiones como archivos separados (§7) y el enlace directo que ya se pueda estar compartiendo.
- Para publicar cambios: commit + `git push origin main` — Pages se reconstruye solo (build "legacy", tarda ~15–30s en verse reflejado).
- No hay CI ni pasos de build: cualquier archivo en la raíz de `main` queda servido tal cual en Pages.

---

## 11. Bloque de metodología y fuentes (julio 2026)

Añadido porque el interlocutor real de esta pieza —un director de sostenibilidad— está entrenado para detectar greenwashing y castiga con desconfianza total. La diferencia con la calculadora de repago es que **aquí la metodología visible es el producto**, no un anexo opcional: sin ella la herramienta se lee como folleto verde.

`<details id="metodologia">` a ancho completo debajo del grid, **colapsado por defecto** (§4), con cuatro piezas:

1. **Cadena de cálculo con los datos en pantalla** (`#mSteps`) — los seis pasos con la aritmética real, re-renderizados en cada cambio de input. El objetivo es que el resultado se pueda rehacer a mano en una servilleta sin pedirnos nada. Incluye la aclaración de que se contabiliza *la diferencia* de reemplazos, no el parque completo.
2. **Tabla de factores** (`#mFactors`, desde la constante `FACTORS`) — parámetro, valor, banda de la literatura, base de la cifra y un **chip de posición**: `cons` (conservador en su dirección de uso), `mid` (punto medio), `high` (extremo alto → infla), `own` (supuesto propio, no literatura). Ese chip es lo que convierte la tabla en instrumento; declarar dónde estamos siendo generosos es lo que compra credibilidad para el resto.
3. **Qué NO está incluido** — fabricación de la batería de reemplazo, transporte, huella del propio Battsaver, contaminantes distintos de CO₂e, descuento temporal. El modelo es incompleto *hacia abajo* y decirlo es una ventaja, no una debilidad.
4. **Banda de sensibilidad** (`#mSens`) — con los datos en pantalla, entre qué y qué estaría el CO₂ y la escoria si el factor se moviera dentro de su banda. Más el efecto de que la extensión de vida fuera ×1,5 en vez de ×2 (67% del resultado, `#mExt`).

Notas de implementación:

- El chip `high` usa **ámbar**, y es uso legítimo de la excepción de §5 (ámbar solo para advertencias reales): advertir sobre nuestro propio supuesto más generoso es exactamente una advertencia real.
- El bloque **no usa sunset** — no es un momento comercial.
- Va colapsado en pantalla, pero **el contenido siempre está renderizado en el DOM** (`renderMethod()` corre en cada `render()`, esté plegado o no) — de eso dependen tanto la impresión como el despliegue instantáneo.
- `beforeprint` fuerza `open = true`: la metodología siempre viaja en el PDF, que es el anexo que se queda el cliente. En impresión arranca en página nueva (`break-before:page`).
- Enlace `.methodlink` desde la tarjeta de resultados hacia `#metodologia`; **su handler pone `open = true` antes del salto**, si no el ancla aterrizaría en un bloque cerrado. Se oculta al imprimir.
- En móvil (≤640px) la operación de cada paso baja a su propia línea, indentada 28px bajo el rótulo, para que las seis filas se lean uniformes. En desktop `.steps .sr` lleva el mismo `padding-left:28px`: no se nota cuando la operación cabe al lado del rótulo, y alinea la operación bajo el rótulo cuando no cabe y baja de línea (le pasa al paso 3, el más largo).
- **Unidades en la cadena de cálculo (agosto 2026)** — cada cifra de `#mSteps` lleva su unidad, no solo el resultado: `20 vehículos × 1 batería/vehículo = 20 posiciones`, `240 kg × 0,40 kg CO₂e/kg = 96,0 kg CO₂e`. Es lo que permite auditar la coherencia dimensional de la cadena, no solo la aritmética. Reglas:
  - Se escriben con el helper `u(cifra, unidad)`, que mete la unidad en un `<span class="u">` (peso 500, opacidad .72) para que el número siga mandando visualmente, y la une a su cifra con `&nbsp;` para que el salto de línea nunca las separe. Las unidades que arrancan con `/` (`/año`, `/equipo`) van pegadas, sin espacio.
  - **Regla compacta**, a pedido explícito de Miguel: cuando un operando comparte exactamente la unidad del resultado, la unidad la carga solo el resultado. Por eso `.steps .sr` perdió el `white-space:nowrap` (las operaciones ahora son más largas y deben poder envolver dentro de su columna).
  - Las cifras adimensionales **no llevan unidad porque no la tienen**: el `2` de la extensión de vida es un factor, y en un porcentaje el `%` ya es su unidad. No inventarles una.
  - Los plurales concuerdan con los datos en pantalla (`1 vehículo` / `20 vehículos`, `1 posición` / `40 posiciones`, `1 batería/vehículo` / `2 baterías/vehículo`).
  - La tabla de factores (`FACTORS`) y la banda de sensibilidad (`#mSens`) ya traían unidades completas y **no se tocaron**.
- **UNA sola tubería de cálculo (agosto 2026)** — `render()` redondea cada magnitud a la precisión con la que se muestra (`rnd()` + `dec()`) y ese valor es el único que circula: tarjeta, hero, caja de escoria, KPIs, pitch, sensibilidad y cadena imprimen **el mismo número**. Antes había dos —la tarjeta con precisión completa y la cadena con el redondeo propagado— y eso hacía que el hero y el paso 5 discreparan en ~30% de las combinaciones, hasta 6,7% con parques mínimos. La salvedad de "puede diferir en el último dígito" era literalmente cierta pero se leía como nota de redondeo, en el bloque cuyo propósito declarado es rehacerse a mano. **No reintroducir un cálculo de precisión completa en paralelo.**
- **Redondeo propagado en la cadena (agosto 2026)** — cada paso de `#mSteps` arrastra al siguiente el operando **ya redondeado que se ve en pantalla**, no el valor interno de precisión completa (helpers `rnd()` y `dec()`). Antes cada paso formateaba el valor exacto y la cadena **no cerraba en el 27% de las combinaciones** (`0,3 × 20 = 7`, `38 × 1,5 = 56`), justo en el bloque cuyo propósito declarado es que el resultado se pueda rehacer a mano — y que además viaja en el PDF. Hoy cierra en las 900 multiplicaciones que barre la verificación. Desde que hay **una sola tubería** (bullet anterior) la cadena y la tarjeta imprimen el mismo número, así que la salvedad ya no habla de una discrepancia entre bloques sino de la precisión de display: con tres cifras significativas **un paso puede diferir del anterior en el último dígito**. Eso se declara en el párrafo que sigue a `#mSteps` y **no se quita** — decir "la cadena cierra exactamente" era una afirmación absoluta que se refuta con una calculadora de mano en el 58% de las combinaciones.
- **Decimales de las tasas unitarias del `#breakdown`** — usan `rateDec()` (2 decimales por debajo de 1, 1 por encima), no `dec()`. La escoria de una batería de moto es 0,75 kg y mostrarla como "0,8" invitaba a multiplicar 20 × 0,8 = 16 kg contra un KPI que dice 15,0. Las tasas del breakdown tienen que reconciliar con los totales de la misma tarjeta.
- **Banda de sensibilidad de las equivalencias** — `#mSens` propaga la incertidumbre también a árboles y km (`TREE_RANGE`, `CAR_RANGE`). Son las cifras que el cliente repite fuera de la sala y antes salían como punto exacto, sin banda.
