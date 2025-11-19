# app.py
import json, random
from pathlib import Path
import streamlit as st

RUTA_PREGUNTAS = Path(__file__).with_name("preguntas.json")
NUM_PREGUNTAS_DEFECTO = 30

# ---------------- Utilidades ----------------
@st.cache_data
def cargar_preguntas_dedup():
    with open(RUTA_PREGUNTAS, "r", encoding="utf-8") as f:
        data = json.load(f)

    vistas = set()
    limpias = []
    for p in data:
        if not (isinstance(p, dict) and all(k in p for k in ("enunciado","opciones","correcta"))):
            continue
        if p["correcta"] not in p["opciones"]:
            continue

        enun = p["enunciado"].strip()
        tema = p.get("simulacro", "").strip() or "Sin tema"
        clave = (enun.lower(), tema.lower())

        if clave in vistas:
            continue
        vistas.add(clave)

        limpias.append({
            "enunciado": enun,
            "opciones": p["opciones"],
            "correcta": p["correcta"].lower(),
            "simulacro": tema
        })
    return limpias


def preparar_test(preguntas, n, usadas):
    disponibles = [p for p in preguntas if p["enunciado"] not in usadas]

    if not disponibles:
        usadas.clear()
        disponibles = list(preguntas)

    n = min(n, len(disponibles))
    sample = random.sample(disponibles, k=n)

    qlist = []
    usados_este_test = []

    for p in sample:
        opciones = [(k, p["opciones"][k]) for k in ("a","b","c","d") if k in p["opciones"]]
        qlist.append({
            "enunciado": p["enunciado"],
            "opciones": opciones,
            "correcta": p["correcta"],
            "simulacro": p["simulacro"]
        })
        usados_este_test.append(p["enunciado"])

    return qlist, usados_este_test


def pinta_pregunta(idx, q, corregir=False):
    st.markdown(f"**Pregunta {idx+1}** — _{q['simulacro']}_")
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

# Estado
st.session_state.setdefault("fase", "menu")
st.session_state.setdefault("tema_seleccionado", "Todos los temas")
st.session_state.setdefault("preguntas", [])
st.session_state.setdefault("aciertos", 0)
st.session_state.setdefault("usadas_por_tema", {})

# Sidebar
with st.sidebar:
    st.markdown("### Opciones")
    n = st.number_input("Nº de preguntas", 5, 100, NUM_PREGUNTAS_DEFECTO, 5)
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
        st.rerun()

# -------- MENÚ PRINCIPAL --------
if st.session_state.fase == "menu":
    st.subheader("Selecciona un tema")

    temas = sorted({p["simulacro"] for p in preguntas_all})
    opciones_temas = ["Todos los temas"] + temas

    tema = st.selectbox("Tema:", opciones_temas)
    st.session_state["tema_seleccionado"] = tema

    st.write("---")

    if st.button("▶️ Comenzar test", type="primary"):
        if tema == "Todos los temas":
            preguntas_tema = preguntas_all
        else:
            preguntas_tema = [p for p in preguntas_all if p["simulacro"] == tema]

        if not preguntas_tema:
            st.error("No hay preguntas para ese tema.")
        else:
            usadas = st.session_state["usadas_por_tema"].get(tema, [])

            qs, u = preparar_test(preguntas_tema, int(n), usadas)
            st.session_state["preguntas"] = qs
            st.session_state["usadas_por_tema"][tema] = usadas + u

            for i in range(len(qs)):
                st.session_state[f"resp_{i}"] = None

            st.session_state["fase"] = "test"
            st.rerun()

# -------- TEST --------
elif st.session_state.fase == "test":
    tema = st.session_state["tema_seleccionado"]
    st.subheader(f"Test — Tema: {tema}")

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

# -------- CORRECCIÓN DIRECTA --------
elif st.session_state.fase == "correccion":
    tema = st.session_state["tema_seleccionado"]
    aciertos = st.session_state["aciertos"]
    total = len(st.session_state.preguntas)

    st.subheader(f"Corrección — Tema: {tema}")
    st.success(f"Correctas: **{aciertos}/{total}** — {(aciertos/total*100):.1f}%")

    st.write("---")

    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=True)

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🆕 Nuevo test (mismo tema)", use_container_width=True):
            tema = st.session_state["tema_seleccionado"]

            if tema == "Todos los temas":
                preguntas_tema = preguntas_all
            else:
                preguntas_tema = [p for p in preguntas_all if p["simulacro"] == tema]

            usadas = st.session_state["usadas_por_tema"].get(tema, [])
            qs, u = preparar_test(preguntas_tema, int(n), usadas)
            st.session_state["preguntas"] = qs
            st.session_state["usadas_por_tema"][tema] = usadas + u

            for i in range(len(qs)):
                st.session_state[f"resp_{i}"] = None

            st.session_state["fase"] = "test"
            st.rerun()

    with col2:
        if st.button("🏠 Volver al menú principal", use_container_width=True):
            st.session_state["fase"] = "menu"
            st.rerun()
