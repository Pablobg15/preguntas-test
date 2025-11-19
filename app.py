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
    # Filtro mínimo + desduplicado por enunciado
    vistas = set()
    limpias = []
    for p in data:
        if not (isinstance(p, dict) and all(k in p for k in ("enunciado", "opciones", "correcta"))):
            continue
        if p["correcta"] not in p["opciones"]:
            continue
        enun = p["enunciado"].strip()
        clave = enun.lower()
        if clave in vistas:
            continue
        vistas.add(clave)
        limpias.append({
            "enunciado": enun,
            "opciones": p["opciones"],
            "correcta": p["correcta"].lower(),
            "simulacro": p.get("simulacro", "")
        })
    return limpias

def preparar_test(preguntas, n, usadas_enunciados):
    """
    Devuelve (lista_preguntas, lista_enunciados_usados_en_este_test)
    evitando repetir enunciados que ya están en usadas_enunciados.
    Si se agotan, reinicia el ciclo.
    """
    # Filtrar preguntas que aún no se han usado
    disponibles = [p for p in preguntas if p["enunciado"] not in usadas_enunciados]

    # Si no queda ninguna disponible, reiniciamos (se permite volver a usarlas)
    if not disponibles:
        usadas_enunciados.clear()
        disponibles = list(preguntas)

    n = min(n, len(disponibles))
    sample = random.sample(disponibles, k=n)

    qlist = []
    usados_este_test = []
    for p in sample:
        opciones = [(k, p["opciones"][k]) for k in ("a", "b", "c", "d") if k in p["opciones"]]
        qlist.append({
            "enunciado": p["enunciado"],
            "opciones": opciones,  # lista (letra, texto)
            "correcta": p["correcta"],
            "simulacro": p.get("simulacro", "")
        })
        usados_este_test.append(p["enunciado"])

    return qlist, usados_este_test

def pinta_pregunta(idx, q, corregir=False):
    st.markdown(f"**Pregunta {idx+1}**{' — _'+q['simulacro']+'_' if q['simulacro'] else ''}")
    st.write(q["enunciado"])

    key = f"resp_{idx}"
    opciones_values = [letra for letra, _ in q["opciones"]]
    opciones_dict = dict(q["opciones"])

    if not corregir:
        # Guardamos la LETRA como valor del radio
        st.radio(
            "Selecciona una opción:",
            options=opciones_values,
            format_func=lambda l: f"{l}) {opciones_dict[l]}",
            key=key,
            label_visibility="collapsed",
        )
    else:
        elegida = st.session_state.get(key, None)
        correcta = q["correcta"]

        if elegida is None:
            st.warning("⚠️ Pregunta sin contestar.")

        for letra in ("a", "b", "c", "d"):
            if letra not in opciones_dict:
                continue
            texto = f"{letra}) {opciones_dict[letra]}"

            if letra == correcta:
                st.markdown(f":green[✅ {texto}]")
            elif elegida == letra:
                st.markdown(f":red[❌ {texto}]")
            else:
                st.markdown(f"◻️ {texto}")

    st.divider()

# ---------------- App ----------------
st.set_page_config(page_title="Preguntas Test", page_icon="📝", layout="wide")
st.title("📝 Preguntas Test")

preguntas_all = cargar_preguntas_dedup()

# Estado inicial
st.session_state.setdefault("fase", "inicio")   # inicio | test | resultado
st.session_state.setdefault("preguntas", [])
st.session_state.setdefault("aciertos", 0)
st.session_state.setdefault("total", 0)
st.session_state.setdefault("usadas_enunciados", [])  # para no repetir entre tests

with st.sidebar:
    st.markdown("### Opciones")
    n = st.number_input("Nº de preguntas", min_value=5, max_value=100,
                        value=NUM_PREGUNTAS_DEFECTO, step=5)
    st.caption(f"Banco actual (únicas): **{len(preguntas_all)}** preguntas")

    if st.session_state.fase == "test":
        respondidas = sum(
            1 for i in range(len(st.session_state.preguntas))
            if st.session_state.get(f"resp_{i}") is not None
        )
        st.progress(respondidas / max(1, len(st.session_state.preguntas)))
        st.caption(f"Respondidas: {respondidas}/{len(st.session_state.preguntas)}")

    if st.button("🔁 Reiniciar todo"):
        st.session_state.clear()
        st.session_state["fase"] = "inicio"
        st.rerun()

# Fase: inicio
if st.session_state.fase == "inicio":
    st.info("Pulsa el botón para generar un test con preguntas aleatorias del JSON (sin repetir entre tests hasta agotarlas).")
    if st.button("▶️ Comenzar test", type="primary"):
        qs, usados = preparar_test(
            preguntas_all, int(n), st.session_state["usadas_enunciados"]
        )
        st.session_state["preguntas"] = qs
        st.session_state["usadas_enunciados"].extend(usados)
        # limpiar respuestas previas
        for i in range(len(qs)):
            st.session_state[f"resp_{i}"] = None
        st.session_state["fase"] = "test"
        st.rerun()

# Fase: test en curso
elif st.session_state.fase == "test":
    st.subheader("Responde y pulsa **Finalizar test** para ver la corrección")
    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=False)

    if st.button("✅ Finalizar test", use_container_width=True, type="primary"):
        aciertos = 0
        total = len(st.session_state.preguntas)
        for i, q in enumerate(st.session_state.preguntas):
            resp = st.session_state.get(f"resp_{i}", None)
            if resp == q["correcta"]:
                aciertos += 1
        st.session_state["aciertos"] = aciertos
        st.session_state["total"] = total
        st.session_state["fase"] = "resultado"
        st.rerun()

# Fase: resultado
elif st.session_state.fase == "resultado":
    # Script para subir arriba del todo al cargar esta fase
    st.markdown(
        "<script>window.scrollTo(0,0);</script>",
        unsafe_allow_html=True
    )

    aciertos = st.session_state["aciertos"]
    total = st.session_state["total"]
    fallos = total - aciertos
    st.success(
        f"🏁 Resultado: **{aciertos}/{total}** correctas — "
        f"**{(aciertos/total*100):.1f}%**  |  ❌ Fallos: **{fallos}**"
    )

    st.subheader("Corrección")
    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=True)

    st.write("---")
    if st.button("🆕 Nuevo test", use_container_width=True):
        qs, usados = preparar_test(
            preguntas_all, int(n), st.session_state["usadas_enunciados"]
        )
        st.session_state["preguntas"] = qs
        st.session_state["usadas_enunciados"].extend(usados)
        for i in range(len(qs)):
            st.session_state[f"resp_{i}"] = None
        st.session_state["fase"] = "test"
        st.rerun()
