# app.py
import json, random, re
from pathlib import Path
import streamlit as st

RUTA_PREGUNTAS = Path(__file__).with_name("preguntas.json")
NUM_PREGUNTAS_DEFECTO = 10

# --------- Configuración de Bloques y Temas ----------
BLOQUES = ["Bloque 1", "Bloque 2", "Bloque 3"]

TEMAS_POR_BLOQUE = {
    "Bloque 1": [
        "Tema 1 - Constitución Española",
        "Tema 2 - Cortes Generales",
        "Tema 3 - Gobierno",
        "Tema 4 - Transparencia",
        "Tema 5 - (sin usar / reservado)",
        "Tema 6 - Fuentes del Derecho",
        "Tema 7 - Igualdad / Discapacidad / Dependencia",
        "Tema 8 - Sociedad de la Información",
        "Tema 9 - Protección de Datos",
    ],
    "Bloque 2": [],
    "Bloque 3": [],
}

NOMBRE_TEMA_B1 = {
    "1": "Tema 1 - Constitución Española",
    "2": "Tema 2 - Cortes Generales",
    "3": "Tema 3 - Gobierno",
    "4": "Tema 4 - Transparencia",
    "5": "Tema 5 - (sin usar / reservado)",
    "6": "Tema 6 - Fuentes del Derecho",
    "7": "Tema 7 - Igualdad / Discapacidad / Dependencia",
    "8": "Tema 8 - Sociedad de la Información",
    "9": "Tema 9 - Protección de Datos",
}

# ---------------- Utilidades ----------------
def norm_letra(x: str) -> str:
    x = str(x).strip().lower()
    if x and x[0] in "abcd":
        return x[0]
    return x

def inferir_bloque_tema(desde: str):
    s = (desde or "").strip()

    m = re.search(r"b\s*([1-3])\s*[-_ ]*\s*t\s*([0-9]+)", s, re.IGNORECASE)
    if m:
        b = m.group(1)
        t = m.group(2)
        bloque = f"Bloque {b}"
        if bloque == "Bloque 1" and t in NOMBRE_TEMA_B1:
            return bloque, NOMBRE_TEMA_B1[t]
        return bloque, f"Tema {t}"

    m = re.search(r"(?:tema|t)\s*([0-9]+)", s, re.IGNORECASE)
    if m:
        t = m.group(1)
        if t in NOMBRE_TEMA_B1:
            return "Bloque 1", NOMBRE_TEMA_B1[t]
        return "Bloque 1", f"Tema {t}"

    return "Bloque 1", "Sin tema"

@st.cache_data
def cargar_preguntas_dedup():
    with open(RUTA_PREGUNTAS, "r", encoding="utf-8") as f:
        data = json.load(f)

    vistas = set()
    limpias = []

    for p in data:
        if not (isinstance(p, dict) and all(k in p for k in ("enunciado", "opciones", "correcta"))):
            continue

        enun = str(p["enunciado"]).strip()
        opciones_raw = p["opciones"]
        if not isinstance(opciones_raw, dict):
            continue

        opciones = {norm_letra(k): str(v).strip() for k, v in opciones_raw.items()}
        correcta = norm_letra(p["correcta"])
        if correcta not in opciones:
            continue

        bloque = str(p.get("bloque", "")).strip()
        tema = str(p.get("tema", "")).strip()
        simulacro = str(p.get("simulacro", "")).strip()

        if not bloque or not tema:
            bloque_inf, tema_inf = inferir_bloque_tema(simulacro)
            bloque = bloque or bloque_inf
            tema = tema or tema_inf

        # Dedup por enunciado + tema + bloque
        clave = (enun.lower(), tema.lower(), bloque.lower())
        if clave in vistas:
            continue
        vistas.add(clave)

        limpias.append({
            "enunciado": enun,
            "opciones": opciones,
            "correcta": correcta,
            "bloque": bloque,
            "tema": tema,
            "simulacro": simulacro or "Sin simulacro",
        })

    return limpias

def preparar_test(preguntas, n, usadas_ids):
    disponibles = [p for p in preguntas if p["enunciado"] not in usadas_ids]
    if not disponibles:
        usadas_ids.clear()
        disponibles = list(preguntas)

    n = min(n, len(disponibles))
    sample = random.sample(disponibles, k=n)

    qlist = []
    usados_este_test = []
    for p in sample:
        opciones = [(k, p["opciones"][k]) for k in ("a", "b", "c", "d") if k in p["opciones"]]
        qlist.append({
            "enunciado": p["enunciado"],
            "opciones": opciones,
            "correcta": p["correcta"],
            "bloque": p["bloque"],
            "tema": p["tema"],
            "simulacro": p["simulacro"],
        })
        usados_este_test.append(p["enunciado"])

    return qlist, usados_este_test

def pinta_pregunta(idx, q, corregir=False):
    st.markdown(f"**Pregunta {idx+1}** — _{q['bloque']} · {q['tema']}_")
    st.write(q["enunciado"])

    key = f"resp_{idx}"
    opciones = dict(q["opciones"])

    if not corregir:
        st.radio(
            "",
            options=list(opciones.keys()),
            format_func=lambda l: f"{l}) {opciones[l]}",
            key=key
        )
    else:
        elegida = st.session_state.get(key, None)
        correcta = q["correcta"]

        if elegida is None:
            st.warning("⚠️ Pregunta sin contestar.")

        for letra, texto in opciones.items():
            linea = f"{letra}) {texto}"
            if letra == correcta:
                st.markdown(f":green[✅ {linea}]")
            elif elegida == letra:
                st.markdown(f":red[❌ {linea}]")
            else:
                st.markdown(f"◻️ {linea}")

    st.divider()

# ---------------- APP ----------------
st.set_page_config(page_title="Preguntas Test", page_icon="📝", layout="wide")
st.title("📝 Preguntas Test")

preguntas_all = cargar_preguntas_dedup()

# Estado global
st.session_state.setdefault("fase", "menu")
st.session_state.setdefault("vista", "Bloques")  # "Bloques" o "Simulacros"

# Bloques/temas
st.session_state.setdefault("bloque_seleccionado", "Bloque 1")
st.session_state.setdefault("temas_seleccionados", [])
st.session_state.setdefault("usadas_por_filtro", {})  # (bloque, tuple(temas) o "__TODOS__")

# Simulacros
st.session_state.setdefault("simulacro_sel", "Todos")
st.session_state.setdefault("usadas_por_simulacro", {})  # simulacro -> usadas

# Test
st.session_state.setdefault("preguntas", [])
st.session_state.setdefault("aciertos", 0)

# Sidebar
with st.sidebar:
    st.markdown("### Opciones")
    n = st.number_input("Nº de preguntas", 5, 100, NUM_PREGUNTAS_DEFECTO, 1)
    st.caption(f"Banco total: **{len(preguntas_all)}** preguntas")

    if st.session_state.fase == "test":
        respondidas = sum(
            1 for i in range(len(st.session_state.preguntas))
            if st.session_state.get(f"resp_{i}") is not None
        )
        st.caption(f"Respondidas: {respondidas}/{len(st.session_state.preguntas)}")
        st.progress(respondidas / max(1, len(st.session_state.preguntas)))

    if st.button("🔁 Reiniciar todo"):
        st.session_state.clear()
        st.session_state["fase"] = "menu"
        st.session_state["vista"] = "Bloques"
        st.rerun()

# Tabs (pestañas)
tab_bloques, tab_sim = st.tabs(["📚 Bloques / Temas", "🧪 Simulacros"])

# ========= VISTA 1: BLOQUES / TEMAS =========
with tab_bloques:
    if st.session_state.fase == "menu":
        st.subheader("Selecciona bloque y temas")

        bloque = st.selectbox(
            "Bloque:",
            BLOQUES,
            index=BLOQUES.index(st.session_state.get("bloque_seleccionado", "Bloque 1"))
        )
        st.session_state["bloque_seleccionado"] = bloque

        temas_bloque = TEMAS_POR_BLOQUE.get(bloque, [])
        temas_sel = st.multiselect(
            "Temas (puedes elegir varios). Si no eliges ninguno, entran TODOS:",
            options=temas_bloque,
            default=st.session_state.get("temas_seleccionados", [])
        )
        st.session_state["temas_seleccionados"] = temas_sel

        st.write("---")

        if st.button("▶️ Comenzar test (Bloques/Temas)", type="primary"):
            preguntas_filtradas = [p for p in preguntas_all if p["bloque"] == bloque]
            if temas_sel:
                preguntas_filtradas = [p for p in preguntas_filtradas if p["tema"] in temas_sel]

            if not preguntas_filtradas:
                st.error("No hay preguntas para ese filtro (bloque/temas).")
            else:
                clave_filtro = (bloque, tuple(sorted(temas_sel)) if temas_sel else ("__TODOS__",))
                usadas = st.session_state["usadas_por_filtro"].get(clave_filtro, [])

                qs, u = preparar_test(preguntas_filtradas, int(n), usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_filtro"][clave_filtro] = usadas + u

                for i in range(len(qs)):
                    st.session_state[f"resp_{i}"] = None

                st.session_state["vista"] = "Bloques"
                st.session_state["fase"] = "test"
                st.rerun()

# ========= VISTA 2: SIMULACROS =========
with tab_sim:
    if st.session_state.fase == "menu":
        st.subheader("Selecciona simulacro")

        sims = sorted({p.get("simulacro", "Sin simulacro") for p in preguntas_all})
        opciones = ["Todos"] + sims

        simulacro = st.selectbox("Simulacro:", opciones, index=opciones.index(st.session_state.get("simulacro_sel", "Todos")))
        st.session_state["simulacro_sel"] = simulacro

        st.write("---")

        if st.button("▶️ Comenzar test (Simulacros)", type="primary"):
            if simulacro == "Todos":
                preguntas_filtradas = list(preguntas_all)
            else:
                preguntas_filtradas = [p for p in preguntas_all if p.get("simulacro") == simulacro]

            if not preguntas_filtradas:
                st.error("No hay preguntas para ese simulacro.")
            else:
                usadas = st.session_state["usadas_por_simulacro"].get(simulacro, [])

                qs, u = preparar_test(preguntas_filtradas, int(n), usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_simulacro"][simulacro] = usadas + u

                for i in range(len(qs)):
                    st.session_state[f"resp_{i}"] = None

                st.session_state["vista"] = "Simulacros"
                st.session_state["fase"] = "test"
                st.rerun()

# ========= TEST =========
if st.session_state.fase == "test":
    if st.session_state["vista"] == "Bloques":
        bloque = st.session_state.get("bloque_seleccionado", "Bloque 1")
        temas_sel = st.session_state.get("temas_seleccionados", [])
        etiqueta = ", ".join(temas_sel) if temas_sel else "Todos los temas"
        st.subheader(f"Test — {bloque} · {etiqueta}")
    else:
        simulacro = st.session_state.get("simulacro_sel", "Todos")
        st.subheader(f"Test — Simulacro: {simulacro}")

    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=False)

    if st.button("✅ Finalizar test", type="primary"):
        aciertos = 0
        for i, q in enumerate(st.session_state.preguntas):
            if st.session_state.get(f"resp_{i}") == q["correcta"]:
                aciertos += 1

        st.session_state["aciertos"] = aciertos
        st.session_state["fase"] = "correccion"
        st.rerun()

# ========= CORRECCIÓN =========
elif st.session_state.fase == "correccion":
    aciertos = st.session_state["aciertos"]
    total = len(st.session_state.preguntas)

    if st.session_state["vista"] == "Bloques":
        bloque = st.session_state.get("bloque_seleccionado", "Bloque 1")
        temas_sel = st.session_state.get("temas_seleccionados", [])
        etiqueta = ", ".join(temas_sel) if temas_sel else "Todos los temas"
        st.subheader(f"Corrección — {bloque} · {etiqueta}")
    else:
        simulacro = st.session_state.get("simulacro_sel", "Todos")
        st.subheader(f"Corrección — Simulacro: {simulacro}")

    st.success(f"Correctas: **{aciertos}/{total}** — {(aciertos/total*100):.1f}%")
    st.write("---")

    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=True)

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🆕 Nuevo test (mismo filtro)", use_container_width=True):
            n = int(n)

            if st.session_state["vista"] == "Bloques":
                bloque = st.session_state.get("bloque_seleccionado", "Bloque 1")
                temas_sel = st.session_state.get("temas_seleccionados", [])

                preguntas_filtradas = [p for p in preguntas_all if p["bloque"] == bloque]
                if temas_sel:
                    preguntas_filtradas = [p for p in preguntas_filtradas if p["tema"] in temas_sel]

                clave_filtro = (bloque, tuple(sorted(temas_sel)) if temas_sel else ("__TODOS__",))
                usadas = st.session_state["usadas_por_filtro"].get(clave_filtro, [])

                qs, u = preparar_test(preguntas_filtradas, n, usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_filtro"][clave_filtro] = usadas + u

            else:
                simulacro = st.session_state.get("simulacro_sel", "Todos")
                if simulacro == "Todos":
                    preguntas_filtradas = list(preguntas_all)
                else:
                    preguntas_filtradas = [p for p in preguntas_all if p.get("simulacro") == simulacro]

                usadas = st.session_state["usadas_por_simulacro"].get(simulacro, [])
                qs, u = preparar_test(preguntas_filtradas, n, usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_simulacro"][simulacro] = usadas + u

            for i in range(len(st.session_state["preguntas"])):
                st.session_state[f"resp_{i}"] = None

            st.session_state["fase"] = "test"
            st.rerun()

    with col2:
        if st.button("🏠 Volver al menú principal", use_container_width=True):
            st.session_state["fase"] = "menu"
            st.rerun()
