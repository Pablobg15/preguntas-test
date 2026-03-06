import json, random, re
from pathlib import Path
import streamlit as st

# ===== RUTAS (TRES + PRÁCTICA EN TRES ARCHIVOS) =====
RUTA_PREGUNTAS_BLOQUES = Path(__file__).with_name("preguntas.json")
RUTA_PREGUNTAS_SIMULACRO = Path(__file__).with_name("preguntas-simulacro.json")

# Práctica: Bloque 1 + Bloque 2 + Bloque 3 en archivos distintos
RUTA_PRACTICA_B1 = Path(__file__).with_name("preguntas_bloque1_practica.json")
RUTA_PRACTICA_B2 = Path(__file__).with_name("Bloque2_Completo.json")
RUTA_PRACTICA_B3 = Path(__file__).with_name("Bloque3.json")

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
    "Bloque 2": [
        "Tema 1 - Informática básica",
        "Tema 2 - Periféricos",
        "Tema 3 - Estructuras de datos",
        "Tema 4 - Sistemas Operativos",
        "Tema 5 - SGBD",
    ],
    "Bloque 3": [
        "Tema 1 - Modelo ER",
        "Tema 2 - Diseño de Bases de Datos",
        "Tema 3 - Lenguajes de Programación",
        "Tema 4 - SQL",
        "Tema 5 - Programación Orientada a Objetos",
        "Tema 6 - Arquitectura Java EE/Jakarta EE y plataforma .NET",
        "Tema 7 - Arquitecturas y Servicios Web",
        "Tema 8 - Aplicaciones Web",
        "Tema 9 - Accesibilidad",
        "Tema 10 - Metodologías"
    ],
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

NOMBRE_TEMA_B2 = {
    "1": "Tema 1 - Informática básica",
    "2": "Tema 2 - Periféricos",
    "3": "Tema 3 - Estructuras de datos",
    "4": "Tema 4 - Sistemas Operativos",
    "5": "Tema 5 - SGBD",
}

NOMBRE_TEMA_B3 = {
    "1": "Tema 1 - Modelo ER",
    "2": "Tema 2 - Diseño de Bases de Datos",
    "3": "Tema 3 - Lenguajes de Programación",
    "4": "Tema 4 - SQL",
    "5": "Tema 5 - Programación Orientada a Objetos",
    "6": "Tema 6 - Arquitectura Java EE/Jakarta EE y plataforma .NET",
    "7": "Tema 7 - Arquitecturas y Servicios Web",
    "8": "Tema 8 - Aplicaciones Web",
    "9": "Tema 9 - Accesibilidad",
    "10": "Tema 10 - Metodologías",
}

# ---------------- Utilidades ----------------
def norm_letra(x: str) -> str:
    x = str(x).strip().lower()
    if x and x[0] in "abcd":
        return x[0]
    return x

def limpiar_basura_pdf(txt: str) -> str:
    if not txt:
        return txt
    txt = re.sub(r"\s+PABLO\s+ARELLANO.*?$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s+www\.\S+.*?$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s+Página\s+\d+.*?$", "", txt, flags=re.IGNORECASE)
    return txt.strip()

def normalizar_bloque(bloque: str) -> str:
    """Acepta 'bloque1', 'BLOQUE 1', 'b1', etc. y devuelve 'Bloque X'."""
    s = (bloque or "").strip().lower()
    m = re.search(r"([1-3])", s)
    return f"Bloque {m.group(1)}" if m else (bloque or "").strip()

def inferir_bloque_tema(desde: str):
    s = (desde or "").strip()

    m = re.search(r"b\s*([1-3])\s*[-_ ]*\s*t\s*([0-9]+)", s, re.IGNORECASE)
    if m:
        b = m.group(1)
        t = m.group(2)
        bloque = f"Bloque {b}"
        if bloque == "Bloque 1" and t in NOMBRE_TEMA_B1:
            return bloque, NOMBRE_TEMA_B1[t]
        if bloque == "Bloque 2" and t in NOMBRE_TEMA_B2:
            return bloque, NOMBRE_TEMA_B2[t]
        if bloque == "Bloque 3" and t in NOMBRE_TEMA_B3:
            return bloque, NOMBRE_TEMA_B3[t]
        return bloque, f"Tema {t}"

    m = re.search(r"(?:tema|t)\s*([0-9]+)", s, re.IGNORECASE)
    if m:
        t = m.group(1)
        if t in NOMBRE_TEMA_B1:
            return "Bloque 1", NOMBRE_TEMA_B1[t]
        if t in NOMBRE_TEMA_B2:
            return "Bloque 2", NOMBRE_TEMA_B2[t]
        if t in NOMBRE_TEMA_B3:
            return "Bloque 3", NOMBRE_TEMA_B3[t]
        return "Bloque 1", f"Tema {t}"

    return "Bloque 1", "Sin tema"

def normalizar_tema(bloque: str, tema: str) -> str:
    """Convierte 'Tema 3', 'Tema 3 - ...' a nombre oficial del selector según bloque."""
    t = (tema or "").strip()
    m = re.match(r"^Tema\s*([0-9]+)", t, flags=re.IGNORECASE)
    if m:
        num = m.group(1)
        if bloque == "Bloque 1" and num in NOMBRE_TEMA_B1:
            return NOMBRE_TEMA_B1[num]
        if bloque == "Bloque 2" and num in NOMBRE_TEMA_B2:
            return NOMBRE_TEMA_B2[num]
        if bloque == "Bloque 3" and num in NOMBRE_TEMA_B3:
            return NOMBRE_TEMA_B3[num]
    return t

def cargar_preguntas_dedup_desde_ruta(ruta: Path, modo: str):
    """
    modo:
      - "bloques": espera bloque/tema en el JSON
      - "simulacros": espera simulacro (y si falta bloque/tema los infiere)
    """
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    vistas = set()
    limpias = []

    for p in data:
        if not (isinstance(p, dict) and all(k in p for k in ("enunciado", "opciones", "correcta"))):
            continue

        enun = limpiar_basura_pdf(str(p["enunciado"]).strip())

        opciones_raw = p["opciones"]
        if not isinstance(opciones_raw, dict):
            continue

        opciones = {norm_letra(k): limpiar_basura_pdf(str(v).strip()) for k, v in opciones_raw.items()}
        correcta = norm_letra(p["correcta"])

        if correcta not in opciones:
            continue

        bloque = normalizar_bloque(str(p.get("bloque", "")).strip())
        tema = str(p.get("tema", "")).strip()
        simulacro = str(p.get("simulacro", "")).strip()

        if modo == "simulacros":
            if not bloque or not tema:
                b_inf, t_inf = inferir_bloque_tema(simulacro)
                bloque = bloque or b_inf
                tema = tema or t_inf
            simulacro = simulacro or "Sin simulacro"
        else:
            simulacro = simulacro or "Sin simulacro"

        # Normaliza tema para que coincida con el selector (Bloque 1/2/3)
        if bloque in ("Bloque 1", "Bloque 2", "Bloque 3"):
            tema = normalizar_tema(bloque, tema)

        # Dedup robusto: incluye opciones+correcta
        op_key = tuple((k, opciones.get(k, "")) for k in ("a", "b", "c", "d"))
        clave = (enun.lower(), tema.lower(), bloque.lower(), modo, op_key, correcta)
        if clave in vistas:
            continue
        vistas.add(clave)

        limpias.append({
            "enunciado": enun,
            "opciones": opciones,
            "correcta": correcta,
            "bloque": bloque,
            "tema": tema if tema else "Sin tema",
            "simulacro": simulacro,
        })

    return limpias

# --------- Carga con cache sensible a cambios (mtime) ---------
@st.cache_data
def cargar_banco_bloques(_mtime: float):
    return cargar_preguntas_dedup_desde_ruta(RUTA_PREGUNTAS_BLOQUES, modo="bloques")

@st.cache_data
def cargar_banco_simulacros(_mtime: float):
    return cargar_preguntas_dedup_desde_ruta(RUTA_PREGUNTAS_SIMULACRO, modo="simulacros")

@st.cache_data
def cargar_banco_practica(_mtime1: float, _mtime2: float, _mtime3: float):
    preguntas = []

    if RUTA_PRACTICA_B1.exists():
        preguntas += cargar_preguntas_dedup_desde_ruta(RUTA_PRACTICA_B1, modo="bloques")

    if RUTA_PRACTICA_B2.exists():
        preguntas += cargar_preguntas_dedup_desde_ruta(RUTA_PRACTICA_B2, modo="bloques")

    if RUTA_PRACTICA_B3.exists():
        preguntas += cargar_preguntas_dedup_desde_ruta(RUTA_PRACTICA_B3, modo="bloques")

    return preguntas

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

# Carga bancos con mtime para invalidar caché si cambian los JSON
mtime_bloques = RUTA_PREGUNTAS_BLOQUES.stat().st_mtime if RUTA_PREGUNTAS_BLOQUES.exists() else 0.0
mtime_sim = RUTA_PREGUNTAS_SIMULACRO.stat().st_mtime if RUTA_PREGUNTAS_SIMULACRO.exists() else 0.0

mtime_pr1 = RUTA_PRACTICA_B1.stat().st_mtime if RUTA_PRACTICA_B1.exists() else 0.0
mtime_pr2 = RUTA_PRACTICA_B2.stat().st_mtime if RUTA_PRACTICA_B2.exists() else 0.0
mtime_pr3 = RUTA_PRACTICA_B3.stat().st_mtime if RUTA_PRACTICA_B3.exists() else 0.0

preguntas_bloques = cargar_banco_bloques(mtime_bloques)
preguntas_simulacros = cargar_banco_simulacros(mtime_sim)
preguntas_practica = cargar_banco_practica(mtime_pr1, mtime_pr2, mtime_pr3)

# Estado global
st.session_state.setdefault("fase", "menu")              # "menu" | "test" | "correccion"
st.session_state.setdefault("vista", "Practica")         # "Bloques" | "Practica" | "Simulacros"
st.session_state.setdefault("modo_ui", "🛠️ Práctica")    # selector UI persistente

# Bloques/temas (vista Bloques)
st.session_state.setdefault("bloque_seleccionado", "Bloque 1")
st.session_state.setdefault("temas_bloques_sel", [])
st.session_state.setdefault("usadas_por_filtro", {})     # (bloque, temas) -> usadas

# Práctica (multi-bloque)
st.session_state.setdefault("bloques_practica_seleccionados", ["Bloque 1"])
st.session_state.setdefault("temas_practica_sel", [])
st.session_state.setdefault("usadas_por_practica", {})   # (bloques_tuple, temas_tuple) -> usadas

# Simulacros
st.session_state.setdefault("simulacro_sel", "Todos")
st.session_state.setdefault("usadas_por_simulacro", {})  # simulacro -> usadas

# Test
st.session_state.setdefault("preguntas", [])
st.session_state.setdefault("aciertos", 0)

# Filtros usados (para repetir exactamente)
st.session_state.setdefault("ultimo_filtro_practica", {"bloques": ["Bloque 1"], "temas": []})
st.session_state.setdefault("ultimo_filtro_bloques", {"bloque": "Bloque 1", "temas": []})
st.session_state.setdefault("ultimo_filtro_simulacros", {"simulacro": "Todos"})

# Sidebar
with st.sidebar:
    st.markdown("### Opciones")

    bloquear = st.session_state.fase != "menu"
    modo = st.radio(
        "Vista",
        ["🛠️ Práctica", "📚 Bloques / Temas", "🧪 Simulacros"],
        index=["🛠️ Práctica", "📚 Bloques / Temas", "🧪 Simulacros"].index(
            st.session_state.get("modo_ui", "🛠️ Práctica")
        ),
        key="modo_ui",
        disabled=bloquear
    )
    if bloquear:
        st.caption("🔒 Termina el test o vuelve al menú para cambiar de vista.")

    if modo == "🛠️ Práctica":
        st.session_state["vista"] = "Practica"
    elif modo == "📚 Bloques / Temas":
        st.session_state["vista"] = "Bloques"
    else:
        st.session_state["vista"] = "Simulacros"

    n = st.number_input(
        "Nº de preguntas",
        min_value=1,
        value=NUM_PREGUNTAS_DEFECTO,
        step=1,
        format="%d"
    )

    st.caption(f"Banco Bloques: **{len(preguntas_bloques)}**")
    st.caption(f"Banco Práctica: **{len(preguntas_practica)}**")
    st.caption(f"Banco Simulacros: **{len(preguntas_simulacros)}**")

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
        st.session_state["vista"] = "Practica"
        st.session_state["modo_ui"] = "🛠️ Práctica"
        st.rerun()

# ========== MENÚ ==========
if st.session_state.fase == "menu":
    vista = st.session_state["vista"]

    # ===== PRACTICA (multi-bloque) =====
    if vista == "Practica":
        st.subheader("🛠️ Práctica — Selecciona bloques y temas")

        if not (RUTA_PRACTICA_B1.exists() or RUTA_PRACTICA_B2.exists() or RUTA_PRACTICA_B3.exists()):
            st.warning("No encuentro los archivos de práctica en la carpeta del proyecto.")
            st.caption(f"- {RUTA_PRACTICA_B1.name}")
            st.caption(f"- {RUTA_PRACTICA_B2.name}")
            st.caption(f"- {RUTA_PRACTICA_B3.name}")
            st.stop()

        bloques_sel = st.multiselect(
            "Bloques (Práctica):",
            options=BLOQUES,
            default=st.session_state.get("bloques_practica_seleccionados", ["Bloque 1"]),
            key="bloques_practica_seleccionados",
        )

        if not bloques_sel:
            st.info("Selecciona al menos un bloque para poder empezar el test.")
            st.stop()

        # Opciones de temas con prefijo de bloque para evitar ambigüedades
        temas_opciones = []
        for b in bloques_sel:
            for t in TEMAS_POR_BLOQUE.get(b, []):
                temas_opciones.append(f"{b} · {t}")

        temas_sel_etiquetas = st.multiselect(
            "Temas de práctica (puedes elegir varios). Si no eliges ninguno, entran TODOS los temas de los bloques seleccionados:",
            options=temas_opciones,
            default=st.session_state.get("temas_practica_sel", []),
            key="temas_practica_sel",
        )

        st.write("---")

        if st.button("▶️ Comenzar test (Práctica)", type="primary"):
            preguntas_filtradas = [p for p in preguntas_practica if p["bloque"] in set(bloques_sel)]

            if temas_sel_etiquetas:
                permitidos = set()
                for x in temas_sel_etiquetas:
                    b, t = x.split(" · ", 1)
                    permitidos.add((b.strip(), t.strip()))
                preguntas_filtradas = [
                    p for p in preguntas_filtradas
                    if (p["bloque"], p["tema"]) in permitidos
                ]

            if not preguntas_filtradas:
                st.error("No hay preguntas de práctica para esos bloques/temas.")
            else:
                st.session_state["ultimo_filtro_practica"] = {
                    "bloques": list(bloques_sel),
                    "temas": list(temas_sel_etiquetas),
                }

                clave = (
                    tuple(sorted(bloques_sel)),
                    tuple(sorted(temas_sel_etiquetas)) if temas_sel_etiquetas else ("__TODOS__",),
                )
                usadas = st.session_state["usadas_por_practica"].get(clave, [])

                qs, u = preparar_test(preguntas_filtradas, int(n), usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_practica"][clave] = usadas + u

                for i in range(len(qs)):
                    st.session_state[f"resp_{i}"] = None

                st.session_state["fase"] = "test"
                st.rerun()

    # ===== BLOQUES / TEMAS =====
    elif vista == "Bloques":
        st.subheader("📚 Bloques / Temas — Selecciona bloque y temas")

        bloque = st.selectbox(
            "Bloque:",
            BLOQUES,
            index=BLOQUES.index(st.session_state.get("bloque_seleccionado", "Bloque 1")),
            key="bloque_seleccionado"
        )

        temas_bloque = TEMAS_POR_BLOQUE.get(bloque, [])
        temas_sel = st.multiselect(
            "Temas (puedes elegir varios). Si no eliges ninguno, entran TODOS:",
            options=temas_bloque,
            default=st.session_state.get("temas_bloques_sel", []),
            key="temas_bloques_sel"
        )

        st.write("---")

        if st.button("▶️ Comenzar test (Bloques/Temas)", type="primary"):
            preguntas_filtradas = [p for p in preguntas_bloques if p["bloque"] == bloque]
            if temas_sel:
                preguntas_filtradas = [p for p in preguntas_filtradas if p["tema"] in temas_sel]

            if not preguntas_filtradas:
                st.error("No hay preguntas para ese filtro (bloque/temas).")
            else:
                st.session_state["ultimo_filtro_bloques"] = {"bloque": bloque, "temas": list(temas_sel)}

                clave_filtro = (bloque, tuple(sorted(temas_sel)) if temas_sel else ("__TODOS__",))
                usadas = st.session_state["usadas_por_filtro"].get(clave_filtro, [])

                qs, u = preparar_test(preguntas_filtradas, int(n), usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_filtro"][clave_filtro] = usadas + u

                for i in range(len(qs)):
                    st.session_state[f"resp_{i}"] = None

                st.session_state["fase"] = "test"
                st.rerun()

    # ===== SIMULACROS =====
    else:
        st.subheader("🧪 Simulacros — Selecciona simulacro")

        sims = sorted({p.get("simulacro", "Sin simulacro") for p in preguntas_simulacros})
        opciones = ["Todos"] + sims

        simulacro = st.selectbox(
            "Simulacro:",
            opciones,
            index=opciones.index(st.session_state.get("simulacro_sel", "Todos")),
            key="simulacro_sel"
        )

        st.write("---")

        if st.button("▶️ Comenzar test (Simulacros)", type="primary"):
            if simulacro == "Todos":
                preguntas_filtradas = list(preguntas_simulacros)
            else:
                preguntas_filtradas = [p for p in preguntas_simulacros if p.get("simulacro") == simulacro]

            if not preguntas_filtradas:
                st.error("No hay preguntas para ese simulacro.")
            else:
                st.session_state["ultimo_filtro_simulacros"] = {"simulacro": simulacro}

                usadas = st.session_state["usadas_por_simulacro"].get(simulacro, [])

                qs, u = preparar_test(preguntas_filtradas, int(n), usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_simulacro"][simulacro] = usadas + u

                for i in range(len(qs)):
                    st.session_state[f"resp_{i}"] = None

                st.session_state["fase"] = "test"
                st.rerun()

# ========== TEST ==========
elif st.session_state.fase == "test":
    vista = st.session_state["vista"]

    if vista == "Bloques":
        f = st.session_state.get("ultimo_filtro_bloques", {"bloque": "Bloque 1", "temas": []})
        bloque = f.get("bloque", "Bloque 1")
        temas_sel = f.get("temas", [])
        etiqueta = ", ".join(temas_sel) if temas_sel else "Todos los temas"
        st.subheader(f"Test — {bloque} · {etiqueta}")

    elif vista == "Practica":
        f = st.session_state.get("ultimo_filtro_practica", {"bloques": ["Bloque 1"], "temas": []})
        bloques_pr = f.get("bloques", ["Bloque 1"])
        temas_sel = f.get("temas", [])
        etiqueta_b = ", ".join(bloques_pr)
        etiqueta_t = ", ".join(temas_sel) if temas_sel else "Todos los temas"
        st.subheader(f"Test — Práctica · {etiqueta_b} · {etiqueta_t}")

    else:
        f = st.session_state.get("ultimo_filtro_simulacros", {"simulacro": "Todos"})
        simulacro = f.get("simulacro", "Todos")
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

# ========== CORRECCIÓN ==========
elif st.session_state.fase == "correccion":
    aciertos = st.session_state["aciertos"]
    total = len(st.session_state.preguntas)
    vista = st.session_state["vista"]

    if vista == "Bloques":
        f = st.session_state.get("ultimo_filtro_bloques", {"bloque": "Bloque 1", "temas": []})
        bloque = f.get("bloque", "Bloque 1")
        temas_sel = f.get("temas", [])
        etiqueta = ", ".join(temas_sel) if temas_sel else "Todos los temas"
        st.subheader(f"Corrección — {bloque} · {etiqueta}")

    elif vista == "Practica":
        f = st.session_state.get("ultimo_filtro_practica", {"bloques": ["Bloque 1"], "temas": []})
        bloques_pr = f.get("bloques", ["Bloque 1"])
        temas_sel = f.get("temas", [])
        etiqueta_b = ", ".join(bloques_pr)
        etiqueta_t = ", ".join(temas_sel) if temas_sel else "Todos los temas"
        st.subheader(f"Corrección — Práctica · {etiqueta_b} · {etiqueta_t}")

    else:
        f = st.session_state.get("ultimo_filtro_simulacros", {"simulacro": "Todos"})
        simulacro = f.get("simulacro", "Todos")
        st.subheader(f"Corrección — Simulacro: {simulacro}")

    st.success(f"Correctas: **{aciertos}/{total}** — {(aciertos/total*100):.1f}%")
    st.write("---")

    for i, q in enumerate(st.session_state.preguntas):
        pinta_pregunta(i, q, corregir=True)

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🆕 Nuevo test (mismo filtro)", use_container_width=True):
            n_int = int(n)

            if vista == "Bloques":
                f = st.session_state.get("ultimo_filtro_bloques", {"bloque": "Bloque 1", "temas": []})
                bloque = f.get("bloque", "Bloque 1")
                temas_sel = f.get("temas", [])

                preguntas_filtradas = [p for p in preguntas_bloques if p["bloque"] == bloque]
                if temas_sel:
                    preguntas_filtradas = [p for p in preguntas_filtradas if p["tema"] in temas_sel]

                clave_filtro = (bloque, tuple(sorted(temas_sel)) if temas_sel else ("__TODOS__",))
                usadas = st.session_state["usadas_por_filtro"].get(clave_filtro, [])

                qs, u = preparar_test(preguntas_filtradas, n_int, usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_filtro"][clave_filtro] = usadas + u

            elif vista == "Practica":
                f = st.session_state.get("ultimo_filtro_practica", {"bloques": ["Bloque 1"], "temas": []})
                bloques_pr = f.get("bloques", ["Bloque 1"])
                temas_sel_etiquetas = f.get("temas", [])

                preguntas_filtradas = [p for p in preguntas_practica if p["bloque"] in set(bloques_pr)]

                if temas_sel_etiquetas:
                    permitidos = set()
                    for x in temas_sel_etiquetas:
                        b, t = x.split(" · ", 1)
                        permitidos.add((b.strip(), t.strip()))
                    preguntas_filtradas = [
                        p for p in preguntas_filtradas
                        if (p["bloque"], p["tema"]) in permitidos
                    ]

                clave = (
                    tuple(sorted(bloques_pr)),
                    tuple(sorted(temas_sel_etiquetas)) if temas_sel_etiquetas else ("__TODOS__",),
                )
                usadas = st.session_state["usadas_por_practica"].get(clave, [])

                qs, u = preparar_test(preguntas_filtradas, n_int, usadas)
                st.session_state["preguntas"] = qs
                st.session_state["usadas_por_practica"][clave] = usadas + u

            else:
                f = st.session_state.get("ultimo_filtro_simulacros", {"simulacro": "Todos"})
                simulacro = f.get("simulacro", "Todos")

                if simulacro == "Todos":
                    preguntas_filtradas = list(preguntas_simulacros)
                else:
                    preguntas_filtradas = [p for p in preguntas_simulacros if p.get("simulacro") == simulacro]

                usadas = st.session_state["usadas_por_simulacro"].get(simulacro, [])
                qs, u = preparar_test(preguntas_filtradas, n_int, usadas)
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