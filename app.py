# app.py
import json, random
from pathlib import Path
import streamlit as st

RUTA_PREGUNTAS = Path(__file__).with_name("preguntas.json")
NUM_PREGUNTAS_DEFECTO = 30

# ---------------- Utilidades ----------------
@st.cache_data
def cargar_preguntas():
    with open(RUTA_PREGUNTAS, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Filtro mínimo de sanidad
    limpias = []
    for p in data:
        if all(k in p for k in ("enunciado", "opciones", "correcta")) and p["correcta"] in p["opciones"]:
            limpias.append(p)
    return limpias

def preparar_test(preguntas, n=30):
    sample = random.sample(preguntas, k=min(n, len(preguntas)))
    # Normalizamos las opciones a lista ordenada de tuplas (letra, texto)
    qlist = []
    for p in sample:
        opciones = [(k, p["opciones"][k]) for k in ("a","b","c","d") if k in p["opciones"]]
        qlist.append({
            "enunciado": p["enunciado"],
            "opciones": opciones,  # lista de (letra, texto)
            "correcta": p["correcta"],
            "simulacro": p.get("simulacro","")
        })
    return qlist

def pinta_pregunta(idx, q, corregir=False):
    st.markdown(f"**Pregunta {idx+1}**{' — _'+q['simulacro']+'_' if q['simulacro'] else ''}")
    st.write(q["enunciado"])

    key = f"resp_{idx}"
    opciones_values = [letra for letra, _ in q["opciones"]]          # valores reales del radio (a/b/c/d)
    opciones_dict   = dict(q["opciones"])                            # para lookup rápido letra -> texto
    respuesta = st.session_state.get(key, None)

    if not corregir:
        # Guardamos SIEMPRE la letra como valor del radio
        _ = st.radio(
            "Selecciona una opción:",
            options=opciones_values,
            index=(opciones_values.index(respuesta) if respuesta in opciones_values else None),
            format_func=lambda l: f"{l}) {opciones_dict[l]}",
            key=key,
            label_visibility="collapsed",
        )
    else:
        # Corrección: mostrar SIEMPRE todas las opciones con marcas y colores
        elegida = st.session_state.get(key, None)
        correcta = q["correcta"]

        if elegida is None:
            st.warning("⚠️ Pregunta sin contestar.")
        for letra in ("a","b","c","d"):
            if letra not in opciones_dict:
                continue
            texto = f"{letra}) {opciones_dict[letra]}"
            if letra == correcta and elegida == correcta:
                # ACIERTO -> correcta seleccionada
                st.markdown(f":green[✅ {texto}]")
            elif letra == correcta and elegida != correcta:
                # Mostrar la correcta (no seleccionada) en verde
                st.markdown(f":green[✅ {texto}]")
            elif elegida == letra and elegida != correcta:
                # Selección incorrecta en rojo
                st.markdown(f":red[❌ {texto}]")
            else:
                # Otras opciones neutras
                st.markdown(f"◻️ {texto}")

    st.divider()

# ---------------- App ----------------
st.set_page_config(page_title="Preguntas Test", page_icon="📝", layout="wide")
st.title("📝 Preguntas Test")

preguntas_all = cargar_preguntas()

# Estado inicial
if "fase" not in st.session_state:
    st.session_state.fase = "inicio"   # inicio | test | resultado
if "preguntas" not in st.session_state:
    st.session_state.preguntas = []
if "aciertos" not in st.session_state:
    st.session_state.aciertos = 0
if "total" not in st.session_state:
    st.session_state.total = 0

with st.sidebar:
    st.markdown("### Opciones")
    n = st.number_input("Nº de preguntas", min_value=5, max_value=100, value=NUM_PREGUNTAS_DEFECTO, step=5)
    st.caption(f"Banco actual: **{len(preguntas_all)}** preguntas")
    # indicador rápido durante el test
    if st.session_state.fase == "test":
        respondidas = sum(1 for i in range(len(st.session_state.preguntas)) if st.session_state.get(f"resp_{i}", None) is not None)
        st.progress(respondidas / max(1, len(st.session_state.preguntas)))
        st.caption(f"Respondidas: {respondidas}/{len(st.session_state.preguntas)}")
    if st.button("🔁 Reiniciar"):
        st.session_state.clear()
        st.session_state.fase = "inicio"

# Fase: inicio
if st.session_state.fase == "inicio":
    st.info("Pulsa el botón para generar un test con preguntas aleatorias del JSON.")
    if st.button("▶️ Comenzar test", type="primary"):
        st.session_state.preguntas = preparar_test(preguntas_all, n=int(n))
        # Limpiar respuestas previas
        for i in range(len(st.session_state.preguntas)):
            st.session_state[f"resp_{i}"] = None
        st.session_state.fase = "test"

# Fase: test en curso
elif st.session_state.fase == "test":
    st.subheader("Responde y pulsa **Finalizar test** para ver la corrección")
    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=False)

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("✅ Finalizar test", use_container_width=True, type="primary"):
            # Corregir
            aciertos = 0
            total = len(st.session_state.preguntas)
            for i, q in enumerate(st.session_state.preguntas):
                resp = st.session_state.get(f"resp_{i}", None)
                if resp == q["correcta"]:
                    aciertos += 1
            st.session_state.aciertos = aciertos
            st.session_state.total = total
            st.session_state.fase = "resultado"
    with col2:
        if st.button("↩️ Volver a empezar", use_container_width=True):
            st.session_state.clear()
            st.session_state.fase = "inicio"

# Fase: resultado
elif st.session_state.fase == "resultado":
    aciertos = st.session_state.aciertos
    total = st.session_state.total
    fallos = total - aciertos
    st.success(f"🏁 Resultado: **{aciertos}/{total}** correctas — **{(aciertos/total*100):.1f}%**  |  ❌ Fallos: **{fallos}**")

    st.subheader("Corrección")
    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=True)

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🆕 Nuevo test", use_container_width=True):
            st.session_state.fase = "inicio"
    with col2:
        if st.button("🔁 Repetir (nuevas aleatorias)", use_container_width=True):
            st.session_state.preguntas = preparar_test(preguntas_all, n=int(n))
            for i in range(len(st.session_state.preguntas)):
                st.session_state[f"resp_{i}"] = None
            st.session_state.fase = "test"
