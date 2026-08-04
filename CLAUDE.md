# CLAUDE.md — Calculadora Ambiental Battsaver

Instrucciones de contexto para trabajar en `Calculadora_Ambiental_Battsaver_v1.html`, la calculadora de impacto ambiental positivo (CO₂ y escoria tóxica evitados) de Battsaver. Este archivo es distinto del `CLAUDE.md` raíz del proyecto (ese gobierna voz/marca de documentos .docx/.pptx/.xlsx) y también distinto del `CLAUDE.md` de la calculadora comercial (`Calculadora_Battsaver_v5.html`) — este gobierna específicamente esta pieza.

---

## 1. Qué es este archivo

Un **HTML autocontenido de una sola página** (CSS inline en `<style>`, JS vanilla inline en `<script>`, sin build step, sin dependencias externas salvo la fuente de Google Fonts). Se abre directamente en el navegador o se sube como artifact. No hay backend: todo el cálculo ocurre en el cliente.

Uso previsto: **herramienta de venta y divulgación**, para mostrarle a un cliente (o usarla internamente en piezas de marketing) cuánto CO₂ y cuánta escoria tóxica deja de generarse al usar Battsaver, en lugar de reemplazar baterías con la frecuencia habitual. Comparte look & feel con la calculadora comercial pero es una herramienta independiente — no comparte estado ni cálculos con ella.

No hay framework (no React/Vue), no hay `package.json`, no hay tests automatizados más allá de verificación manual con Playwright (capturas de pantalla en desktop/móvil y aritmética cruzada) antes de cada entrega.

---

## 2. Modelo ambiental (fuente de verdad)

### Catálogo por tipo de vehículo (peso de batería de referencia)
```js
const SKUS = [
  {name:"12V · 10W", veh:"moto / carro pequeño", battKg:10, co2:15,  slag:1.5, dual:false},
  {name:"12V · 20W", veh:"camioneta / camión / náutico", battKg:20, co2:30, slag:3.0, dual:true},
  {name:"24V · 20W", veh:"camión 24V", battKg:20, co2:30, slag:3.0, dual:true},
];
```
`dual:true` habilita el selector "1 batería / 2 baterías" (camiones que montan doble batería).

### Factores de emisión
```js
const EF_CO2_PER_KG = 1.5;  // kg CO2e por kg de batería procesada (fundición + trituración)
const SLAG_PER_KG   = 0.15; // 15% del peso nominal de la batería, como escoria de fundición
```
Estos dos factores **no se usan directamente en el runtime** (los kg de CO₂ y escoria por SKU ya vienen precalculados en la tabla `SKUS` arriba: `battKg × 1.5` y `battKg × 0.15`). Se dejan declarados en el código como documentación viva de dónde salen esos números — si se cambia el peso de un SKU, hay que recalcular `co2` y `slag` a mano con estas dos constantes.

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
co2Evitado   = bateríasSalvadas × co2      (= kgEvitados × 1.5)
escoriaEvit. = bateríasSalvadas × slag     (= kgEvitados × 0.15)
```

Este modelo es deliberadamente el mismo de la calculadora comercial (vida útil que se duplica), para que ambas herramientas cuenten la misma historia con el mismo cliente.

---

## 3. Verificación de supuestos (julio 2026)

Se contrastaron los cinco supuestos numéricos contra fuentes externas. Ninguno se cambió; quedan documentados aquí para trazabilidad y para que Claude Code no los "corrija" sin criterio de negocio:

| Supuesto | Estado | Nota |
|---|---|---|
| 1,5 kg CO₂e / kg batería procesada | Razonable, no es cifra única de industria | Estudios de LCA de plomo-ácido dan un rango ~0,9–2,5 kg CO₂e/kg; 1,5 cae en la mitad. Es un promedio defendible, no una norma certificada. |
| Escoria = 10%–15% del peso de la batería | Razonable, extremo alto-medio | La literatura habla de 13%–25% **del plomo producido** (no del peso total de batería); traducido a peso total (~60% Pb) da ~8%–15%. |
| Pesos de referencia (10 kg / 20 kg) | Consistente | Alineados con pesos estándar de mercado para los segmentos declarados. |
| Árbol absorbe 22 kg CO₂/año | Bien soportado | Coincide con estimación EPA (~21,7 kg) y es la cifra más citada en fuentes en español. |
| Carro a gasolina: 0,17 kg CO₂/km | Extremo alto del rango típico | Autos pequeños/medianos suelen citarse en 0,12–0,15 kg/km; 0,17 es defendible para parque automotor más viejo (contexto colombiano) pero es conservador-alto, no el promedio global más citado. |

Si se audita esta calculadora externamente, los dos puntos a explicar primero son el factor de 1,5 kg/kg (es un promedio de industria) y el de 0,17 kg/km (está en el extremo alto).

### Dirección de uso de cada factor (importante, julio 2026)

"Extremo alto del rango" **no significa lo mismo** en todos los factores: depende de si el factor multiplica o divide el resultado. Esto se analizó al construir el bloque de metodología (§11) y corrige la lectura de riesgo de la tabla de arriba:

| Factor | Cómo se usa | Un valor alto… | Posición actual | Efecto neto |
|---|---|---|---|---|
| 1,5 kg CO₂e/kg | **multiplica** el CO₂ del hero | infla el resultado | punto medio de 0,9–2,5 | neutro |
| 15% escoria | **multiplica** la escoria destacada | infla el resultado | **tope** de la banda 8%–15% | **el supuesto menos conservador del modelo** |
| 22 kg/árbol | **divide** (CO₂ ÷ 22) | da *menos* árboles | ligeramente alto vs EPA 21,7 | conservador |
| 0,17 kg/km | **divide** (CO₂ ÷ 0,17) | da *menos* km | alto del rango típico | conservador |

Consecuencia: el pendiente que pedía evaluar bajar el 0,17 a 0,12–0,15 estaba invertido en su lógica de riesgo — bajarlo **aumentaría** los km equivalentes mostrados, o sea inflaría la cifra divulgativa. Se deja en 0,17 por ser la opción conservadora, y así queda declarado en la UI. El único factor que sí queda en el extremo generoso es la escoria al 15% (ver §8, pendiente abierto).

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

- Formato numérico con `toLocaleString("es-CO", …)`.
- Decimales con coma (`.replace(".",",")`), consistente con v5.
- Validación con Playwright: capturas en desktop (caso por defecto + caso camión 24V con 2 baterías) y móvil, más verificación aritmética directa vía `page.eval_on_selector` contrastando el resultado esperado a mano antes de dar por buena cualquier cifra en pantalla.
- Un solo archivo HTML; versiones anteriores (si las hay) se conservan como archivos separados en la misma carpeta, no se sobrescriben. Desde julio 2026 la carpeta sí está versionada con git (ver §10) — eso no cambia la convención de no sobrescribir versiones con nombres distintos.

---

## 8. Pendientes conocidos

1. **Fuente Cloud oficial** — ver §5.
2. **Comparativo con calculadora comercial**: podría valer la pena, a futuro, una vista que combine ahorro en pesos (v5) + impacto ambiental (este archivo) en una sola propuesta, pero hoy son herramientas separadas y no comparten estado — no fusionar sin pedirlo explícitamente.
3. **Botón de reinicio** de inputs a valores por defecto — no implementado.
4. **Accesibilidad de segmented controls** (`.seg`): mismo pendiente que en v5, impacto bajo para uso comercial en vivo.
5. ~~**Revisión del factor de 0,17 kg CO₂/km**~~ — **cerrado (julio 2026)**. Se analizó la dirección de uso (ver §3): al ser divisor, 0,17 produce *menos* kilómetros equivalentes, así que es la opción conservadora. Bajarlo a 0,12–0,15 inflaría la cifra. Se deja en 0,17 y queda declarado como conservador en la tabla de factores de la UI.
6. **Factor de escoria al 15%** — *abierto, decisión de negocio*. Es el único supuesto que queda en el extremo generoso de su banda (8%–15%) y multiplica directamente la cifra más destacada de la herramienta. Hoy la UI lo declara como "extremo alto" y muestra la banda completa, que es la salida honesta; la alternativa más defendible sería mover el valor puntual al centro de la banda (~11%–12%) y perder ~25% de la cifra de escoria. No cambiar sin decisión explícita de Miguel.
7. **Fuentes nominales de la tabla de factores** — hoy solo el factor de árbol cita fuente por nombre (US EPA, Greenhouse Gas Equivalencies Calculator), que es la única referencia documentada. Los demás describen honestamente la base de evidencia sin citar estudios concretos, a propósito: **no se inventaron citas**. Para que el pie sea auditable de verdad hay que reemplazar esas descripciones por las referencias reales (estudio de ACV de fundición secundaria de plomo, fuente del rango de escoria). Ver `FACTORS` en el `<script>`.

---

## 9. Qué NO hacer sin confirmar explícitamente

- No cambiar el **fondo** del bloque de escoria a ámbar ni a sunset — sigue siendo navy a propósito (ver §4/§5). Ámbar es solo para advertencias reales. El label de texto (`.slag .t`) sí usa sunset, a pedido explícito de Miguel (ver §5) — eso no aplica al fondo de la caja.
- No usar sunset en controles de UI de producto (inputs, sliders) — solo en los puntos de marketing/labels destacados ya definidos en §5.
- No mostrar cantidad de baterías salvadas sin desglosar por posición/vehículo — el KPI "Baterías salvadas" siempre debe traer la nota de cuántas posiciones y vehículos hay detrás.
- No cambiar el supuesto de "la vida se duplica con Battsaver" sin coordinarlo con la calculadora comercial — ambas herramientas deben seguir contando la misma historia de negocio.
- No agregar el impacto de fabricar la batería nueva de reemplazo (minería, fundición primaria) a menos que se pida explícitamente — el modelo actual es deliberadamente conservador y cubre solo el reciclaje de la batería que se deja de desechar.
- No cambiar "tú/tu" de vuelta a "usted/su".
- No tocar los factores de §3 (1,5 kg/kg, 15% escoria, 22 kg/árbol, 0,17 kg/km) sin dejar registro del cambio en esta misma tabla — son supuestos de negocio verificados, no bugs. Si se cambia un factor, actualizar también su **banda** (`EF_CO2_RANGE`, `SLAG_RANGE`) y su ficha en `FACTORS`.
- **No suavizar ni quitar las declaraciones incómodas del bloque de metodología** (§11): que la escoria usa el tope de su banda, que la extensión ×2 es supuesto propio y no literatura, y que no se resta la huella del propio Battsaver. Son precisamente lo que hace creíble el resto de la herramienta ante un auditor entrenado en detectar greenwashing — quitarlas la devuelve a folleto.
- **No inventar citas ni referencias** para llenar la columna de fuentes. Vago pero honesto le gana siempre a preciso pero fabricado: una cita falsa detectada destruye la credibilidad de toda la calculadora. Ver §8, pendiente 7.
- No abrir el bloque de metodología por defecto (va colapsado, ver §4) ni sacarlo del PDF (al imprimir sí se fuerza abierto).
- **No borrar la cadena de cálculo (`#mSteps`) por parecer redundante con el breakdown**, ni devolverle al `#breakdown` las filas de total que se le quitaron (ver §4). Ya se analizó: el paso 2 (`1 ÷ (2 × vida)`, la tasa de reemplazos evitados) no aparece en ningún otro lugar de la página, y los pasos 5–6 son el único punto donde los factores de §3 se conectan con la cifra del hero —el breakdown usa los valores ya precalculados por SKU y nunca muestra que `co2 = battKg × 1,5`. Sin la cadena, la tabla de factores no alcanza para reproducir el resultado y el anexo que viaja en el PDF deja de ser auditable. Además el párrafo que sigue a `#mSteps` arranca con "El paso 2 es la clave del modelo…" y quedaría huérfano.

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
- **Unidades en la cadena de cálculo (agosto 2026)** — cada cifra de `#mSteps` lleva su unidad, no solo el resultado: `20 vehículos × 1 batería/vehículo = 20 posiciones`, `200 kg × 1,5 kg CO₂e/kg = 300 kg CO₂e`. Es lo que permite auditar la coherencia dimensional de la cadena, no solo la aritmética. Reglas:
  - Se escriben con el helper `u(cifra, unidad)`, que mete la unidad en un `<span class="u">` (peso 500, opacidad .72) para que el número siga mandando visualmente, y la une a su cifra con `&nbsp;` para que el salto de línea nunca las separe. Las unidades que arrancan con `/` (`/año`, `/equipo`) van pegadas, sin espacio.
  - **Regla compacta**, a pedido explícito de Miguel: cuando un operando comparte exactamente la unidad del resultado, la unidad la carga solo el resultado. Por eso `.steps .sr` perdió el `white-space:nowrap` (las operaciones ahora son más largas y deben poder envolver dentro de su columna).
  - Las cifras adimensionales **no llevan unidad porque no la tienen**: el `2` de la extensión de vida es un factor, y en un porcentaje el `%` ya es su unidad. No inventarles una.
  - Los plurales concuerdan con los datos en pantalla (`1 vehículo` / `20 vehículos`, `1 posición` / `40 posiciones`, `1 batería/vehículo` / `2 baterías/vehículo`).
  - La tabla de factores (`FACTORS`) y la banda de sensibilidad (`#mSens`) ya traían unidades completas y **no se tocaron**.
