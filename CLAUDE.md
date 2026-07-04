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

---

## 4. Reglas de UI/UX ya decididas

- El selector "Baterías por vehículo" (1/2) **solo aparece** para SKUs con `dual:true` (camiones). Para moto/carro pequeño se oculta y se fuerza `perVeh=1`.
- El bloque de escoria tiene **su propio tratamiento visual** (caja navy destacada, ícono, texto largo) porque es el argumento diferenciador que Miguel pidió resaltar: "residuo indestructible" / "pasivo ambiental eterno". No debe quedar como una fila más del breakdown ni perder ese peso visual.
- El hero muestra el CO₂ en **toneladas si ≥1 t**, si no en kg — no mostrar siempre en kg cuando la cifra es grande.
- Las equivalencias (árboles, km no recorridos) son **apoyo divulgativo**, secundarias al dato duro de CO₂ y escoria — no deben competir en tamaño visual con el hero ni con el bloque de escoria.
- El horizonte de análisis (slider de 1 a 10 años) es independiente de la vida de la batería; ambos controles alimentan la misma fórmula.
- Botón "⤓ Guardar PDF" con `window.print()` y hoja de impresión dedicada, igual que en la calculadora comercial.

---

## 5. Identidad visual

Comparte paleta y logo con `Calculadora_Battsaver_v5.html` (Manual de Marca): navy `#08344D` primario, teal `#0E8C7F`/mint `#C2E9D5` como acento comercial, ámbar reservado exclusivamente para advertencias (no se usa en esta calculadora — la caja de escoria es **navy**, no ámbar, a propósito: no es una advertencia, es una cifra positiva de impacto evitado). Tipografía oficial **Cloud**, sustituida temporalmente por Plus Jakarta Sans con `@font-face` placeholder listo para el archivo oficial. Logo oficial incrustado en base64 para mantener el archivo autocontenido.

> **Pendiente compartido con v5:** cuando Miguel entregue la fuente Cloud oficial, actualizar el `@font-face` en ambos archivos.

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
- Un solo archivo HTML, sin versionado interno de commits — versiones anteriores (si las hay) se conservan como archivos separados en la misma carpeta, no se sobrescriben.

---

## 8. Pendientes conocidos

1. **Fuente Cloud oficial** — ver §5.
2. **Comparativo con calculadora comercial**: podría valer la pena, a futuro, una vista que combine ahorro en pesos (v5) + impacto ambiental (este archivo) en una sola propuesta, pero hoy son herramientas separadas y no comparten estado — no fusionar sin pedirlo explícitamente.
3. **Botón de reinicio** de inputs a valores por defecto — no implementado.
4. **Accesibilidad de segmented controls** (`.seg`): mismo pendiente que en v5, impacto bajo para uso comercial en vivo.
5. **Revisión del factor de 0,17 kg CO₂/km** — evaluar si conviene bajarlo al rango 0,12–0,15 para estar más alineado con el promedio global citado, o dejarlo y documentarlo explícitamente como "parque automotor típico colombiano" en el pie de página (hoy el pie solo dice "carro a gasolina promedio").

---

## 9. Qué NO hacer sin confirmar explícitamente

- No usar ámbar para el bloque de escoria — es navy a propósito (ver §4). Ámbar es solo para advertencias reales.
- No mostrar cantidad de baterías salvadas sin desglosar por posición/vehículo — el KPI "Baterías salvadas" siempre debe traer la nota de cuántas posiciones y vehículos hay detrás.
- No cambiar el supuesto de "la vida se duplica con Battsaver" sin coordinarlo con la calculadora comercial — ambas herramientas deben seguir contando la misma historia de negocio.
- No agregar el impacto de fabricar la batería nueva de reemplazo (minería, fundición primaria) a menos que se pida explícitamente — el modelo actual es deliberadamente conservador y cubre solo el reciclaje de la batería que se deja de desechar.
- No cambiar "tú/tu" de vuelta a "usted/su".
- No tocar los factores de §3 (1,5 kg/kg, 15% escoria, 22 kg/árbol, 0,17 kg/km) sin dejar registro del cambio en esta misma tabla — son supuestos de negocio verificados, no bugs.
