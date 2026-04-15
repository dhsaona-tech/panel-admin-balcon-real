import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os
import requests
import pandas as pd
import io

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Panel Admin — Balcón Real",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════
# CONEXIÓN A FIREBASE
# ══════════════════════════════════════════════════════
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred_dict = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
            "universe_domain": st.secrets["firebase"]["universe_domain"],
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ══════════════════════════════════════════════════════
# TELEGRAM NOTIFICACIONES
# ══════════════════════════════════════════════════════
TELEGRAM_TOKEN = st.secrets.get("telegram", {}).get("token", "")

def enviar_notificacion_telegram(user_id, mensaje):
    if not TELEGRAM_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": user_id, "text": mensaje}
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except:
        return False

# ══════════════════════════════════════════════════════
# ESTILOS CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .metric-card-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.2rem; border-radius: 10px; color: white;
        text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .metric-card-green {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.2rem; border-radius: 10px; color: white;
        text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .metric-card-teal {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        padding: 1.2rem; border-radius: 10px; color: white;
        text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .metric-card-red {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1.2rem; border-radius: 10px; color: white;
        text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .metric-card-dark {
        background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
        padding: 1.2rem; border-radius: 10px; color: white;
        text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .metric-number { font-size: 2rem; font-weight: 800; margin: 0; }
    .metric-label { font-size: 0.8rem; opacity: 0.9; margin: 0; }

    /* List-style item rows */
    .list-item {
        background: #fff;
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }
    .list-item:hover { border-color: #CBD5E1; }
    .list-icon { font-size: 1.3rem; flex-shrink: 0; margin-top: 2px; }
    .list-body { flex: 1; min-width: 0; }
    .list-title { font-weight: 600; color: #1E3A5F; font-size: 0.9rem; margin: 0; }
    .list-desc { color: #475569; font-size: 0.82rem; margin: 0.15rem 0 0 0; }
    .list-meta { color: #94A3B8; font-size: 0.75rem; margin: 0.2rem 0 0 0; }

    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 100px;
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.03em; white-space: nowrap;
    }
    .badge-pendiente { background: #FEF3C7; color: #92400E; }
    .badge-en_proceso { background: #DBEAFE; color: #1E40AF; }
    .badge-resuelto { background: #D1FAE5; color: #065F46; }
    .badge-aprobada { background: #D1FAE5; color: #065F46; }
    .badge-rechazada { background: #FEE2E2; color: #991B1B; }

    .progress-bg { background: #E5E7EB; border-radius: 100px; height: 10px; width: 100%; }
    .progress-fill { border-radius: 100px; height: 10px; }

    .reservation-box {
        background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 6px;
        padding: 0.5rem 0.75rem; margin: 0.3rem 0; font-size: 0.82rem; color: #0C4A6E;
    }

    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #1E3A5F 0%, #2D5F8B 100%); }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3 { color: white !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🏢 Balcón Real")
    st.markdown("### Panel de Administración")
    st.markdown("---")

    pagina = st.radio(
        "Navegación",
        ["📊 Dashboard", "🔧 Reportes", "📅 Reservas", "🚨 Emergencias"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### Chatbot PLN v5.0")
    st.markdown("BETO · 20 intenciones · 83% acc")

    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════
# FUNCIONES
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def obtener_reportes():
    docs = db.collection('reportes_mantenimiento').order_by('fecha_creacion', direction=firestore.Query.DESCENDING).stream()
    return [{'id': doc.id, **doc.to_dict()} for doc in docs]

@st.cache_data(ttl=30)
def obtener_reservas():
    docs = db.collection('solicitudes_reserva').order_by('fecha_creacion', direction=firestore.Query.DESCENDING).stream()
    return [{'id': doc.id, **doc.to_dict()} for doc in docs]

@st.cache_data(ttl=30)
def obtener_emergencias():
    docs = db.collection('alertas_emergencia').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
    return [{'id': doc.id, **doc.to_dict()} for doc in docs]

def actualizar_estado_reporte(doc_id, nuevo_estado, notas=""):
    db.collection('reportes_mantenimiento').document(doc_id).update({
        'estado': nuevo_estado, 'notas_admin': notas,
        'fecha_actualizacion': datetime.now().isoformat()
    })

def actualizar_estado_reserva(doc_id, nuevo_estado):
    db.collection('solicitudes_reserva').document(doc_id).update({
        'estado': nuevo_estado, 'fecha_actualizacion': datetime.now().isoformat()
    })

def fmt_fecha(f):
    if not f: return "—"
    try: return f[:16].replace('T', ' ')
    except: return str(f)

def calcular_tiempo_resolucion(reportes):
    tiempos = []
    for r in reportes:
        if r.get('estado') == 'resuelto' and r.get('fecha_creacion') and r.get('fecha_actualizacion'):
            try:
                c = datetime.fromisoformat(r['fecha_creacion'])
                a = datetime.fromisoformat(r['fecha_actualizacion'])
                diff = (a - c).total_seconds() / 3600
                if diff > 0: tiempos.append(diff)
            except: pass
    return sum(tiempos) / len(tiempos) if tiempos else 0

def mensajes_hoy(reportes, reservas, emergencias):
    hoy = datetime.now().strftime('%Y-%m-%d')
    return sum(1 for r in reportes if r.get('fecha_creacion','').startswith(hoy)) + \
           sum(1 for r in reservas if r.get('fecha_creacion','').startswith(hoy)) + \
           sum(1 for e in emergencias if e.get('fecha','').startswith(hoy))

def exportar_reportes_excel(reportes):
    rows = [{
        'Tipo': r.get('tipo','').replace('_',' ').title(),
        'Descripción': r.get('descripcion',''),
        'Estado': r.get('estado',''),
        'Torre': r.get('torre',''),
        'Depto': r.get('depto',''),
        'Notas Admin': r.get('notas_admin',''),
        'Fecha Creación': fmt_fecha(r.get('fecha_creacion','')),
        'Última Actualización': fmt_fecha(r.get('fecha_actualizacion','')),
    } for r in reportes]
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine='openpyxl')
    buf.seek(0)
    return buf

EMOJI_TIPO = {
    'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
    'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
    'reporte_seguridad': '🔒', 'reclamo_pago': '💰', 'cancelar_reserva': '❌'
}

# ══════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 Dashboard General</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Vista general del conjunto Balcón Real</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()
    reservas = obtener_reservas()
    emergencias = obtener_emergencias()

    total = len(reportes)
    pendientes = len([r for r in reportes if r.get('estado') == 'pendiente'])
    en_proceso = len([r for r in reportes if r.get('estado') == 'en_proceso'])
    resueltos = len([r for r in reportes if r.get('estado') == 'resuelto'])
    pend_res = len([r for r in reservas if r.get('estado') == 'pendiente'])
    hoy = mensajes_hoy(reportes, reservas, emergencias)
    tasa = (resueltos / total * 100) if total > 0 else 0
    tiempo_prom = calcular_tiempo_resolucion(reportes)

    # KPIs
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f'<div class="metric-card"><p class="metric-number">{total}</p><p class="metric-label">Total Reportes</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card-orange"><p class="metric-number">{pendientes}</p><p class="metric-label">Pendientes</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card-green"><p class="metric-number">{en_proceso}</p><p class="metric-label">En Proceso</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card-teal"><p class="metric-number">{resueltos}</p><p class="metric-label">Resueltos</p></div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="metric-card-red"><p class="metric-number">{pend_res}</p><p class="metric-label">Reservas Pend.</p></div>', unsafe_allow_html=True)
    with c6:
        st.markdown(f'<div class="metric-card-dark"><p class="metric-number">{hoy}</p><p class="metric-label">Mensajes Hoy</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Tasa + Tiempo
    ct, cti = st.columns(2)
    with ct:
        st.markdown("#### Tasa de Resolución")
        color = "#28a745" if tasa >= 70 else "#ffc107" if tasa >= 40 else "#dc3545"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;margin-top:0.5rem;">
            <div class="progress-bg" style="flex:1;"><div class="progress-fill" style="width:{min(tasa,100)}%;background:{color};"></div></div>
            <span style="font-weight:800;font-size:1.4rem;color:{color};">{tasa:.0f}%</span>
        </div>
        <p style="font-size:0.82rem;color:#888;margin-top:0.3rem;">{resueltos} de {total} reportes resueltos</p>
        """, unsafe_allow_html=True)
    with cti:
        st.markdown("#### ⏱️ Tiempo Prom. de Resolución")
        if tiempo_prom > 0:
            if tiempo_prom < 1: tt = f"{tiempo_prom*60:.0f} minutos"
            elif tiempo_prom < 24: tt = f"{tiempo_prom:.1f} horas"
            else: tt = f"{tiempo_prom/24:.1f} días"
            st.markdown(f"<p style='font-size:1.8rem;font-weight:800;color:#1E3A5F;margin:0.5rem 0 0;'>{tt}</p>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.82rem;color:#888;'>Desde creación hasta resolución</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#888;'>Sin datos aún</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("#### Reportes por Tipo")
        if reportes:
            tipos = {}
            for r in reportes:
                t = r.get('tipo','otro').replace('_',' ').title()
                tipos[t] = tipos.get(t, 0) + 1
            df_t = pd.DataFrame(list(tipos.items()), columns=['Tipo','Cantidad']).sort_values('Cantidad', ascending=False)
            st.bar_chart(df_t.set_index('Tipo'))
    with cg2:
        st.markdown("#### Estado de Reportes")
        if reportes:
            st.bar_chart(pd.DataFrame({'Estado':['Pendiente','En proceso','Resuelto'],'Cantidad':[pendientes,en_proceso,resueltos]}).set_index('Estado'))

    st.markdown("---")

    # Top 3 + Actividad
    ctop, cact = st.columns(2)
    with ctop:
        st.markdown("#### 🏆 Top 3 Problemas")
        if reportes:
            tipos = {}
            for r in reportes:
                t = r.get('tipo','otro').replace('_',' ').title()
                tipos[t] = tipos.get(t, 0) + 1
            medals = ["🥇","🥈","🥉"]
            for idx, (tipo, cnt) in enumerate(sorted(tipos.items(), key=lambda x:x[1], reverse=True)[:3]):
                st.markdown(f"{medals[idx]} **{tipo}** — {cnt} reportes ({cnt/total*100:.0f}%)")
    with cact:
        st.markdown("#### Actividad Reciente")
        for r in reportes[:5]:
            em = EMOJI_TIPO.get(r.get('tipo',''), '📋')
            st.markdown(f"{em} **{r.get('tipo','').replace('_',' ').title()}** · {fmt_fecha(r.get('fecha_creacion',''))}")
            st.caption(f"{r.get('descripcion','')[:80]}")

    if emergencias:
        st.markdown("---")
        st.markdown("#### 🚨 Emergencias Recientes")
        for e in emergencias[:3]:
            st.error(f"**{e.get('palabra_clave','')}** — {e.get('mensaje','')[:100]} — {fmt_fecha(e.get('fecha',''))}")

# ══════════════════════════════════════════════════════
# REPORTES
# ══════════════════════════════════════════════════════
elif pagina == "🔧 Reportes":
    st.markdown('<p class="main-header">🔧 Reportes de Mantenimiento</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestione los reportes recibidos por el chatbot</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()

    # Filtros
    cf1, cf2, cf3 = st.columns([1,1,1])
    with cf1:
        filtro_tipo = st.selectbox("Tipo", ["Todos"] + sorted(set(r.get('tipo','') for r in reportes)))
    with cf2:
        torres = sorted(set(str(r.get('torre','')) for r in reportes if r.get('torre') and str(r.get('torre'))!='None'))
        filtro_torre = st.selectbox("Torre", ["Todas"] + torres)
    with cf3:
        buscar = st.text_input("🔍 Buscar", placeholder="Buscar en descripción...")

    rep_f = reportes
    if filtro_tipo != "Todos": rep_f = [r for r in rep_f if r.get('tipo') == filtro_tipo]
    if filtro_torre != "Todas": rep_f = [r for r in rep_f if str(r.get('torre','')) == filtro_torre]
    if buscar: rep_f = [r for r in rep_f if buscar.lower() in r.get('descripcion','').lower()]

    cc, ce = st.columns([3,1])
    with cc:
        st.markdown(f"**{len(rep_f)}** reportes encontrados")
    with ce:
        if rep_f:
            st.download_button("📥 Exportar Excel", data=exportar_reportes_excel(rep_f),
                file_name=f"reportes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    tab_p, tab_e, tab_r = st.tabs(["⏳ Pendientes", "🔄 En Proceso", "✅ Resueltos"])

    def mostrar_reportes(lista, tk):
        if not lista:
            st.info("No hay reportes en esta categoría.")
            return
        for i, r in enumerate(lista):
            em = EMOJI_TIPO.get(r.get('tipo',''), '📋')
            tipo = r.get('tipo','').replace('_',' ').title()
            estado = r.get('estado','pendiente')
            fecha = fmt_fecha(r.get('fecha_creacion',''))
            torre = r.get('torre','')
            depto = r.get('depto','')
            ubic = f" · Torre {torre}, Depto {depto}" if torre and str(torre)!='None' else ""

            st.markdown(f"""
            <div class="list-item">
                <span class="list-icon">{em}</span>
                <div class="list-body">
                    <p class="list-title">{tipo} <span class="badge badge-{estado}">{estado.replace('_',' ')}</span></p>
                    <p class="list-desc">{r.get('descripcion','Sin descripción')}</p>
                    <p class="list-meta">📅 {fecha}{ubic} · 👤 {r.get('user_id','N/A')}</p>
                    {"<p class='list-desc' style='color:#2563EB;'>💬 " + r.get('notas_admin','') + "</p>" if r.get('notas_admin') else ""}
                </div>
            </div>""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1,2,1])
            with c1:
                nuevo = st.selectbox("Estado", ["pendiente","en_proceso","resuelto"],
                    index=["pendiente","en_proceso","resuelto"].index(estado),
                    key=f"e_{tk}_{r['id']}_{i}", label_visibility="collapsed")
            with c2:
                nota = st.text_input("Nota", value=r.get('notas_admin',''),
                    placeholder="Agregar nota...", key=f"n_{tk}_{r['id']}_{i}", label_visibility="collapsed")
            with c3:
                if st.button("💾 Guardar", key=f"b_{tk}_{r['id']}_{i}", use_container_width=True):
                    actualizar_estado_reporte(r['id'], nuevo, nota)
                    st.success("✅ Actualizado")
                    st.cache_data.clear()
                    st.rerun()

    with tab_p: mostrar_reportes([r for r in rep_f if r.get('estado')=='pendiente'], 'p')
    with tab_e: mostrar_reportes([r for r in rep_f if r.get('estado')=='en_proceso'], 'e')
    with tab_r: mostrar_reportes([r for r in rep_f if r.get('estado')=='resuelto'], 'r')

# ══════════════════════════════════════════════════════
# RESERVAS
# ══════════════════════════════════════════════════════
elif pagina == "📅 Reservas":
    st.markdown('<p class="main-header">📅 Solicitudes de Reserva</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Apruebe o rechace reservas — el residente será notificado por Telegram</p>', unsafe_allow_html=True)

    reservas = obtener_reservas()
    tab_p, tab_a, tab_r = st.tabs(["⏳ Pendientes", "✅ Aprobadas", "❌ Rechazadas"])

    def mostrar_reservas(lista, tk, botones=False):
        if not lista:
            st.info("No hay reservas en esta categoría.")
            return
        for i, r in enumerate(lista):
            estado = r.get('estado','pendiente')
            area = r.get('area','No especificada')
            torre = r.get('torre','N/A')
            depto = r.get('depto','N/A')
            fh = r.get('fecha_hora_solicitada', None)
            fc = fmt_fecha(r.get('fecha_creacion',''))
            uid = r.get('user_id','')

            st.markdown(f"""
            <div class="list-item">
                <span class="list-icon">🏢</span>
                <div class="list-body">
                    <p class="list-title">{area} <span class="badge badge-{estado}">{estado}</span></p>
                    <div class="reservation-box">
                        🏠 Torre {torre}, Depto {depto}<br>
                        📅 Fecha/Hora: <strong>{fh if fh else 'No especificada'}</strong><br>
                        🕐 Solicitud: {fc}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            if botones:
                c1, c2, c3 = st.columns([1,1,2])
                with c1:
                    if st.button("✅ Aprobar", key=f"ap_{tk}_{r['id']}_{i}", use_container_width=True):
                        actualizar_estado_reserva(r['id'], 'aprobada')
                        msg = f"✅ Su reserva ha sido APROBADA.\n\nÁrea: {area}\nFecha/Hora: {fh if fh else 'Por confirmar'}\n\nRecuerde cumplir con las normas de uso."
                        if uid: enviar_notificacion_telegram(uid, msg)
                        st.success("✅ Aprobada — Notificación enviada")
                        st.cache_data.clear()
                        st.rerun()
                with c2:
                    if st.button("❌ Rechazar", key=f"re_{tk}_{r['id']}_{i}", use_container_width=True):
                        actualizar_estado_reserva(r['id'], 'rechazada')
                        msg = f"❌ Su reserva ha sido RECHAZADA.\n\nÁrea: {area}\nFecha/Hora: {fh if fh else 'No especificada'}\n\nContacte a la administración para más información."
                        if uid: enviar_notificacion_telegram(uid, msg)
                        st.warning("❌ Rechazada — Notificación enviada")
                        st.cache_data.clear()
                        st.rerun()

    with tab_p: mostrar_reservas([r for r in reservas if r.get('estado')=='pendiente'], 'p', botones=True)
    with tab_a: mostrar_reservas([r for r in reservas if r.get('estado')=='aprobada'], 'a')
    with tab_r: mostrar_reservas([r for r in reservas if r.get('estado')=='rechazada'], 'r')

# ══════════════════════════════════════════════════════
# EMERGENCIAS
# ══════════════════════════════════════════════════════
elif pagina == "🚨 Emergencias":
    st.markdown('<p class="main-header">🚨 Alertas de Emergencia</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Alertas detectadas automáticamente por el chatbot</p>', unsafe_allow_html=True)

    emergencias = obtener_emergencias()

    if not emergencias:
        st.success("✅ No hay alertas de emergencia registradas.")
    else:
        no_at = [e for e in emergencias if not e.get('atendida', False)]
        at = [e for e in emergencias if e.get('atendida', False)]

        tab_act, tab_hist = st.tabs([f"🔴 Activas ({len(no_at)})", f"📋 Historial ({len(at)})"])

        with tab_act:
            if not no_at:
                st.success("✅ Todas las emergencias han sido atendidas.")
            for i, e in enumerate(no_at):
                st.error(f"**🚨 {e.get('palabra_clave','').upper()}**\n\n"
                         f"📝 {e.get('mensaje','N/A')}\n\n"
                         f"📅 {fmt_fecha(e.get('fecha',''))} · 👤 {e.get('user_id','N/A')}")
                if st.button("✅ Marcar como atendida", key=f"at_{e['id']}_{i}"):
                    db.collection('alertas_emergencia').document(e['id']).update({
                        'atendida': True, 'fecha_atencion': datetime.now().isoformat()
                    })
                    st.success("Marcada como atendida")
                    st.cache_data.clear()
                    st.rerun()
                st.markdown("---")

        with tab_hist:
            if not at:
                st.info("No hay emergencias en el historial.")
            for e in at:
                st.markdown(f"✅ **{e.get('palabra_clave','').upper()}** — {e.get('mensaje','')[:80]}... · {fmt_fecha(e.get('fecha',''))}")
