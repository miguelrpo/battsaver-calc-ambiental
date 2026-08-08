#!/usr/bin/env python3
"""
Verificación de invariantes de la Calculadora Ambiental Battsaver.

Comprueba de una pasada todo lo que las auditorías de agosto 2026 establecieron
como innegociable (ver CLAUDE.md §8.bis):

  · la cadena de cálculo cierra con los operandos que muestra
  · el modelo no se desvía de la matemática exacta
  · una misma magnitud no aparece con dos valores distintos en la página
  · las tasas del breakdown reconcilian con los totales de su tarjeta
  · las entradas hostiles quedan saneadas
  · la accesibilidad estructural sigue en pie

Existe porque tres regresiones se colaron entre rondas de revisión manual, y las
tres eran de esta clase. Correrlo antes de cada entrega cuesta un minuto.

    pip install playwright
    python3 verificar.py

Sale con código 1 si algún invariante falla, para poder engancharlo a un hook.
"""
import itertools
import os
import re
import sys

from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
CALC = "file://" + os.path.join(AQUI, "Calculadora_Ambiental_Battsaver_v1.html")
# La calculadora comercial vive en su propio repo; si está al lado, se verifica
# además que ambas cuenten la misma historia para el mismo cliente.
COMERCIAL = os.path.join(os.path.dirname(AQUI), "Calculadora-Battsaver", "Calculadora_Battsaver.html")

# Chromium de Playwright. Si el entorno ya lo resuelve solo, dejar en None.
CHROME = os.environ.get("CHROME_PATH") or None

# Modelo de referencia, calculado aquí de forma INDEPENDIENTE del HTML: si el
# código de la calculadora tuviera un error, este archivo no debe heredarlo.
KG = {0: 12, 1: 20, 2: 20}   # peso de batería de referencia por SKU
EF_CO2 = 0.40                # kg CO2e por kg de batería
EXT = 2                      # extensión de vida con Battsaver

resultados = []


def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok))
    print(("OK    · " if ok else "FALLA · ") + nombre + (f" — {detalle}" if detalle else ""))


def num(s):
    """Primera cifra en formato es-CO de una cadena, con sus decimales."""
    s = s.replace("\xa0", " ").strip()
    m = re.match(r"^-?\d[\d.]*(?:,\d+)?", s)
    if not m:
        return None, 0
    t = m.group(0)
    return float(t.replace(".", "").replace(",", ".")), (len(t.split(",")[1]) if "," in t else 0)


def cierra(filas):
    """¿Cada operación mostrada da el resultado mostrado?"""
    n, malos = 0, []
    for r in filas:
        r = r.replace("\xa0", " ")
        if "=" not in r or "÷" in r or "(" in r:
            continue
        lhs, rhs = r.rsplit("=", 1)
        res, dec = num(rhs)
        partes = lhs.split("×")
        if res is None or len(partes) < 2:
            continue
        vals = [num(x)[0] for x in partes]
        if any(v is None for v in vals):
            continue
        prod = 1.0
        for v in vals:
            prod *= v
        n += 1
        if abs(prod - res) > 0.5 * 10 ** (-dec) + max(1, abs(res)) * 1e-9:
            malos.append(r.strip())
    return n, malos


def poner(pg, sel, v):
    pg.eval_on_selector(sel, "(el,v)=>{el.value=v;el.dispatchEvent(new Event('input'))}", v)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
    errores = []
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(CALC)
    pg.eval_on_selector("#metodologia", "e=>e.open=true")

    ops = malos = casos = discrepa = 0
    desvios = []
    for sku, veh, vida, anios in itertools.product(
            range(3), [1, 2, 7, 20, 53, 209, 5000], [1, 1.5, 2.5, 3.5, 4], [1, 3, 5, 9, 10]):
        pg.eval_on_selector_all("#sku button", "(e,i)=>e[i].click()", sku)
        poner(pg, "#veh", veh); poner(pg, "#life", vida); poner(pg, "#years", anios)
        casos += 1

        pasos = pg.eval_on_selector_all("#mSteps .sr", "e=>e.map(x=>x.textContent)")
        n, bad = cierra(pasos)
        ops += n; malos += len(bad)

        # el modelo redondea a la precisión que muestra, pero no debe distorsionar
        exacto = veh * ((1 - 1 / EXT) / vida) * anios * KG[sku] * EF_CO2
        mostrado, _ = num(pasos[4].rsplit("=", 1)[1])
        if exacto > 0 and mostrado and abs(mostrado - exacto) / exacto > 0.01:
            desvios.append((sku, veh, vida, anios, round(exacto, 3), mostrado))

        # la tarjeta y la cadena tienen que imprimir el mismo número
        kpi = pg.inner_text("#kKg")
        kg_kpi, _ = num(kpi)
        if " t" in kpi:
            kg_kpi *= 1000
        kg_cadena, _ = num(pasos[3].rsplit("=", 1)[1])
        if kg_kpi and kg_cadena and abs(kg_kpi - kg_cadena) > max(kg_cadena, 1) * 0.006:
            discrepa += 1

    check("la cadena cierra con los operandos que muestra", malos == 0,
          f"{ops} operaciones en {casos} escenarios, {malos} descuadres")
    check("el modelo no se desvía >1% de la matemática exacta", not desvios,
          f"{len(desvios)} desviaciones")
    check("la tarjeta y la cadena imprimen el mismo número", discrepa == 0,
          f"{discrepa} discrepancias en {casos} escenarios")

    # las tasas unitarias del breakdown deben reconciliar con el hero de su tarjeta
    fallos = 0
    for sku in range(3):
        pg.eval_on_selector_all("#sku button", "(e,i)=>e[i].click()", sku)
        poner(pg, "#veh", 20); poner(pg, "#life", 2.5); poner(pg, "#years", 5)
        filas = pg.eval_on_selector_all("#breakdown .r", "e=>e.map(x=>x.textContent)")
        bat, _ = num(pg.inner_text("#kBatt"))
        co2_unit, _ = num(filas[1])
        hero_txt = pg.inner_text("#heroCo2")
        hero, _ = num(hero_txt)
        if "tonelada" in hero_txt:
            hero *= 1000
        if abs(bat * co2_unit - hero) > max(hero, 1) * 0.02:
            fallos += 1
    check("las tasas del breakdown reconcilian con el hero", fallos == 0, f"{fallos} fallos en 3 SKUs")

    # entradas hostiles: el campo nunca debe mostrar algo distinto de lo que calcula
    sucias = []
    for crudo in ["", "0", "-5", "1e9", "abc", "3.7", "999999999999"]:
        poner(pg, "#veh", crudo)
        pg.dispatch_event("#veh", "blur")
        campo = pg.input_value("#veh")
        if campo and (not campo.isdigit() or not 1 <= int(campo) <= 1000000):
            sucias.append((crudo, campo))
    check("las entradas hostiles quedan saneadas", not sucias, str(sucias))

    a11y = {
        "h1": pg.eval_on_selector_all("h1", "e=>e.length") == 1,
        "labels": pg.eval_on_selector_all("#veh,#life,#years", "e=>e.every(x=>x.labels&&x.labels.length)"),
        "radiogroup": pg.eval_on_selector_all("[role=radiogroup]", "e=>e.length") >= 1,
        "roving tabindex": pg.eval_on_selector_all("#sku button", "e=>e.filter(x=>x.tabIndex===0).length") == 1,
        "aria-live": pg.eval_on_selector_all("[aria-live]", "e=>e.length") >= 2,
        "meta description": pg.eval_on_selector_all("meta[name=description]", "e=>e.length") == 1,
    }
    check("accesibilidad estructural", all(a11y.values()),
          "falta: " + ", ".join(k for k, v in a11y.items() if not v) if not all(a11y.values()) else "")

    # el anexo técnico tiene que viajar en el PDF: es lo que se queda el cliente
    pg.emulate_media(media="print")
    pg.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    alto = pg.eval_on_selector("#mSteps", "e=>e.getBoundingClientRect().height")
    check("la metodología viaja en el PDF", alto > 100, f"cadena de {round(alto)}px")
    pg.emulate_media(media="screen")
    pg.close()

    # responsive: 320px es donde WCAG 1.4.10 mide el reflow
    desborda = []
    for w, h in [(1440, 900), (1024, 650), (390, 844), (320, 800)]:
        q = b.new_page(viewport={"width": w, "height": h})
        q.on("pageerror", lambda e: errores.append(str(e)))
        q.goto(CALC)
        q.eval_on_selector("#metodologia", "e=>e.open=true")
        q.wait_for_timeout(250)
        if q.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1"):
            desborda.append(w)
        q.close()
    check("sin desbordamiento horizontal (incluye 320px, WCAG 1.4.10)", not desborda, str(desborda))
    check("sin errores de página", not errores, str(errores[:3]))

    # coherencia con la calculadora comercial, si está al lado
    if os.path.exists(COMERCIAL):
        q = b.new_page()
        q.goto(CALC)
        q.eval_on_selector_all("#sku button", "e=>e[2].click()")          # camión 24V
        q.eval_on_selector_all("#battPerVeh button", "e=>e[1].click()")   # doble batería
        poner(q, "#veh", 30); poner(q, "#life", 2.5); poner(q, "#years", 5)
        q.wait_for_timeout(150)
        amb, _ = num(q.inner_text("#kBatt"))
        q.goto("file://" + COMERCIAL)
        q.eval_on_selector_all("#channel button", "e=>e[0].click()")
        poner(q, "#veh", 30); poner(q, "#life", 2.5)
        q.wait_for_timeout(150)
        com, _ = num(q.eval_on_selector_all("#breakdown .r", "e=>e.map(x=>x.textContent)")[-1])
        # la comercial cuenta 1 batería por vehículo y lo declara en `assumpt`;
        # aquí son 2. La divergencia tiene que ser exactamente ese factor.
        check("la divergencia con la calculadora comercial es exactamente ×2 (doble batería)",
              abs(amb - com * 5 * 2) < 0.05,
              f"ambiental {amb} vs comercial {com}/año × 5 años × 2 baterías")
        q.close()

    b.close()

fallan = [n for n, ok in resultados if not ok]
print("\n" + "=" * 70)
print(f"{len(resultados) - len(fallan)}/{len(resultados)} invariantes OK")
if fallan:
    print("FALLAN: " + " · ".join(fallan))
sys.exit(1 if fallan else 0)
