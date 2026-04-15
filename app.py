import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os
import requests

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
# TOKEN DE TELEGRAM (para notificaciones)
# ══════════════════════════════════════════════════════
TELEGRAM_TOKEN = st.secrets.get("telegram", {}).get("token", "")

def enviar_notificacion_telegram(user_id, mensaje):
    """Envía un mensaje al usuario vía el bot de Telegram"""
    if not TELEGRAM_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": user_id, "text": mensaje, "parse_mode": "HTML"}
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Error enviando notificación: {e}")
        return False

# ══════════════════════════════════════════════════════
# ESTILOS CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    * { font-family: 'DM Sans', sans-serif; }

    /* Sidebar */
    div[data-testid="stSidebar"] {
        background: #0F1A2E;
    }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3,
    div[data-testid="stSidebar"] .stMarkdown h4,
    div[data-testid="stSidebar"] .stMarkdown h5 {
        color: #E2E8F0 !important;
    }
    div[data-testid="stSidebar"] .stRadio label p {
        color: #CBD5E1 !important;
        font-size: 0.95rem;
    }

    /* Header */
    .page-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F1A2E;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .page-sub {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }

    /* Metric cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        text-align: center;
        transition: box-shadow 0.2s;
    }
    .kpi-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    .kpi-number {
        font-size: 2.25rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0.25rem 0 0 0;
        font-weight: 600;
    }
    .kpi-accent-blue .kpi-number { color: #2563EB; }
    .kpi-accent-amber .kpi-number { color: #D97706; }
    .kpi-accent-green .kpi-number { color: #059669; }
    .kpi-accent-red .kpi-number { color: #DC2626; }
    .kpi-accent-purple .kpi-number { color: #7C3AED; }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .badge-pendiente { background: #FEF3C7; color: #92400E; }
    .badge-en_proceso { background: #DBEAFE; color: #1E40AF; }
    .badge-resuelto { background: #D1FAE5; color: #065F46; }
    .badge-aprobada { background: #D1FAE5; color: #065F46; }
    .badge-rechazada { background: #FEE2E2; color: #991B1B; }

    /* Cards */
    .report-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: box-shadow 0.2s;
    }
    .report-card:hover {
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .report-title {
        font-size: 1rem;
        font-weight: 600;
        color: #0F1A2E;
        margin: 0 0 0.5rem 0;
    }
    .report-detail {
        font-size: 0.85rem;
        color: #475569;
        margin: 0.2rem 0;
    }
    .report-date {
        font-size: 0.8rem;
        color: #94A3B8;
    }

    /* Emergency card */
    .emergency-card {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 4px solid #DC2626;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .emergency-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #991B1B;
        margin: 0 0 0.35rem 0;
    }
    .emergency-detail {
        font-size: 0.85rem;
        color: #7F1D1D;
        margin: 0.15rem 0;
    }

    /* Activity item */
    .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid #F1F5F9;
    }
    .activity-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .activity-text {
        font-size: 0.85rem;
        color: #334155;
        margin: 0;
    }
    .activity-time {
        font-size: 0.75rem;
        color: #94A3B8;
        margin: 0;
    }

    /* Section heading */
    .section-heading {
        font-size: 1rem;
        font-weight: 700;
        color: #0F1A2E;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
    }

    /* Reservation info */
    .reservation-info {
        background: #F0F9FF;
        border: 1px solid #BAE6FD;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
    }
    .reservation-info p {
        margin: 0.15rem 0;
        font-size: 0.85rem;
        color: #0C4A6E;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🏢 Balcón Real")
    st.markdown("##### Panel de Administración")
    st.markdown("---")

    pagina = st.radio(
        "Navegación",
        ["📊 Dashboard", "🔧 Reportes", "📅 Reservas", "🚨 Emergencias"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### 🤖 Chatbot PLN")
    st.markdown("BETO · 20 intenciones · v5.0")
    st.markdown(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    st.markdown("---")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════
# FUNCIONES DE DATOS
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def obtener_reportes():
    docs = db.collection('reportes_mantenimiento').order_by('fecha_creacion', direction=firestore.Query.DESCENDING).stream()
    reportes = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        reportes.append(data)
    return reportes

@st.cache_data(ttl=30)
def obtener_reservas():
    docs = db.collection('solicitudes_reserva').order_by('fecha_creacion', direction=firestore.Query.DESCENDING).stream()
    reservas = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        reservas.append(data)
    return reservas

@st.cache_data(ttl=30)
def obtener_emergencias():
    docs = db.collection('alertas_emergencia').order_by('fecha', direction=firestore.Query.DESCENDING).stream()
    emergencias = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        emergencias.append(data)
    return emergencias

def actualizar_estado_reporte(doc_id, nuevo_estado, notas=""):
    db.collection('reportes_mantenimiento').document(doc_id).update({
        'estado': nuevo_estado,
        'notas_admin': notas,
        'fecha_actualizacion': datetime.now().isoformat()
    })

def actualizar_estado_reserva(doc_id, nuevo_estado):
    db.collection('solicitudes_reserva').document(doc_id).update({
        'estado': nuevo_estado,
        'fecha_actualizacion': datetime.now().isoformat()
    })

def formatear_fecha(fecha_str):
    """Formatea fecha ISO a formato legible"""
    if not fecha_str:
        return "—"
    try:
        return fecha_str[:16].replace('T', '  ')
    except:
        return str(fecha_str)

EMOJI_TIPO = {
    'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
    'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
    'reporte_seguridad': '🔒', 'reclamo_pago': '💰', 'cancelar_reserva': '❌'
}

# ══════════════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    st.markdown('<p class="page-header">📊 Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Resumen general de gestión — Conjunto Balcón Real</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()
    reservas = obtener_reservas()
    emergencias = obtener_emergencias()

    pendientes_rep = len([r for r in reportes if r.get('estado') == 'pendiente'])
    en_proceso = len([r for r in reportes if r.get('estado') == 'en_proceso'])
    resueltos = len([r for r in reportes if r.get('estado') == 'resuelto'])
    pendientes_res = len([r for r in reservas if r.get('estado') == 'pendiente'])
    emergencias_no_atendidas = len([e for e in emergencias if not e.get('atendida', False)])

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-amber">
            <p class="kpi-number">{pendientes_rep}</p>
            <p class="kpi-label">Reportes Pendientes</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-blue">
            <p class="kpi-number">{en_proceso}</p>
            <p class="kpi-label">En Proceso</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-green">
            <p class="kpi-number">{resueltos}</p>
            <p class="kpi-label">Resueltos</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-purple">
            <p class="kpi-number">{pendientes_res}</p>
            <p class="kpi-label">Reservas Pendientes</p>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-red">
            <p class="kpi-number">{emergencias_no_atendidas}</p>
            <p class="kpi-label">Emergencias Activas</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Dos columnas: Reportes por tipo + Últimas actividades
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<p class="section-heading">🔧 Reportes por Tipo</p>', unsafe_allow_html=True)
        if reportes:
            import pandas as pd
            tipos = {}
            for r in reportes:
                tipo = r.get('tipo', 'sin_tipo').replace('_', ' ').title()
                tipos[tipo] = tipos.get(tipo, 0) + 1
            df_tipos = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad'])
            df_tipos = df_tipos.sort_values('Cantidad', ascending=True)
            st.bar_chart(df_tipos.set_index('Tipo'), horizontal=True)
        else:
            st.info("No hay reportes registrados aún.")

    with col_right:
        st.markdown('<p class="section-heading">📋 Últimas Actividades</p>', unsafe_allow_html=True)
        if reportes:
            for r in reportes[:6]:
                emoji = EMOJI_TIPO.get(r.get('tipo', ''), '📋')
                fecha = formatear_fecha(r.get('fecha_creacion', ''))
                tipo = r.get('tipo', 'N/A').replace('_', ' ').title()
                desc = r.get('descripcion', '')[:70]
                st.markdown(f"""
                <div class="activity-item">
                    <span class="activity-icon">{emoji}</span>
                    <div>
                        <p class="activity-text"><strong>{tipo}</strong> — {desc}...</p>
                        <p class="activity-time">{fecha}</p>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No hay actividad registrada aún.")

    # Emergencias recientes
    if emergencias:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-heading">🚨 Alertas de Emergencia Recientes</p>', unsafe_allow_html=True)
        for e in emergencias[:3]:
            fecha = formatear_fecha(e.get('fecha', ''))
            st.markdown(f"""
            <div class="emergency-card">
                <p class="emergency-title">🚨 {e.get('palabra_clave', 'N/A').upper()}</p>
                <p class="emergency-detail">{e.get('mensaje', 'N/A')[:120]}</p>
                <p class="emergency-detail" style="color:#94A3B8; font-size:0.75rem;">{fecha}</p>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PÁGINA: REPORTES DE MANTENIMIENTO
# ══════════════════════════════════════════════════════
elif pagina == "🔧 Reportes":
    st.markdown('<p class="page-header">🔧 Reportes de Mantenimiento</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Gestione los reportes recibidos por el chatbot</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()

    # Filtros en una fila
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        filtro_estado = st.selectbox("Estado", ["Todos", "pendiente", "en_proceso", "resuelto"])
    with col_f2:
        tipos_unicos = sorted(set(r.get('tipo', '') for r in reportes))
        filtro_tipo = st.selectbox("Tipo", ["Todos"] + tipos_unicos)
    with col_f3:
        buscar = st.text_input("🔍 Buscar en descripción", placeholder="Escriba para buscar...")

    reportes_filtrados = reportes
    if filtro_estado != "Todos":
        reportes_filtrados = [r for r in reportes_filtrados if r.get('estado') == filtro_estado]
    if filtro_tipo != "Todos":
        reportes_filtrados = [r for r in reportes_filtrados if r.get('tipo') == filtro_tipo]
    if buscar:
        reportes_filtrados = [r for r in reportes_filtrados if buscar.lower() in r.get('descripcion', '').lower()]

    st.markdown(f"**{len(reportes_filtrados)}** reportes encontrados")
    st.markdown("---")

    if not reportes_filtrados:
        st.info("No hay reportes con los filtros seleccionados.")

    for i, reporte in enumerate(reportes_filtrados):
        emoji = EMOJI_TIPO.get(reporte.get('tipo', ''), '📋')
        estado = reporte.get('estado', 'pendiente')
        tipo = reporte.get('tipo', 'N/A').replace('_', ' ').title()
        fecha = formatear_fecha(reporte.get('fecha_creacion', ''))

        with st.container():
            st.markdown(f"""
            <div class="report-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <p class="report-title">{emoji} {tipo}</p>
                    <span class="badge badge-{estado}">{estado.replace('_',' ').upper()}</span>
                </div>
                <p class="report-detail">📝 {reporte.get('descripcion', 'Sin descripción')}</p>
                <p class="report-date">📅 {fecha} · 👤 ID: {reporte.get('user_id', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_a:
                nuevo_estado = st.selectbox(
                    "Estado",
                    ["pendiente", "en_proceso", "resuelto"],
                    index=["pendiente", "en_proceso", "resuelto"].index(estado),
                    key=f"est_{reporte['id']}_{i}",
                    label_visibility="collapsed"
                )
            with col_b:
                notas = st.text_input(
                    "Nota",
                    value=reporte.get('notas_admin', ''),
                    placeholder="Agregar nota del administrador...",
                    key=f"nota_{reporte['id']}_{i}",
                    label_visibility="collapsed"
                )
            with col_c:
                if st.button("💾 Guardar", key=f"btn_{reporte['id']}_{i}", use_container_width=True):
                    actualizar_estado_reporte(reporte['id'], nuevo_estado, notas)
                    st.success("✅ Actualizado")
                    st.cache_data.clear()
                    st.rerun()

# ══════════════════════════════════════════════════════
# PÁGINA: RESERVAS
# ══════════════════════════════════════════════════════
elif pagina == "📅 Reservas":
    st.markdown('<p class="page-header">📅 Solicitudes de Reserva</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Apruebe o rechace reservas de áreas comunales — el residente será notificado por Telegram</p>', unsafe_allow_html=True)

    reservas = obtener_reservas()

    # Filtro
    filtro_estado_res = st.selectbox("Filtrar por estado", ["Todos", "pendiente", "aprobada", "rechazada"])
    if filtro_estado_res != "Todos":
        reservas = [r for r in reservas if r.get('estado') == filtro_estado_res]

    st.markdown(f"**{len(reservas)}** solicitudes encontradas")
    st.markdown("---")

    if not reservas:
        st.info("No hay solicitudes de reserva con los filtros seleccionados.")

    for i, reserva in enumerate(reservas):
        estado = reserva.get('estado', 'pendiente')
        area = reserva.get('area', 'Área no especificada')
        torre = reserva.get('torre', 'N/A')
        depto = reserva.get('depto', 'N/A')
        fecha_hora_solicitada = reserva.get('fecha_hora_solicitada', None)
        fecha_creacion = formatear_fecha(reserva.get('fecha_creacion', ''))
        user_id = reserva.get('user_id', '')

        with st.container():
            st.markdown(f"""
            <div class="report-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <p class="report-title">🏢 {area}</p>
                    <span class="badge badge-{estado}">{estado.upper()}</span>
                </div>
                <div class="reservation-info">
                    <p>🏠 <strong>Solicitante:</strong> Torre {torre}, Depto {depto}</p>
                    <p>📅 <strong>Fecha/Hora solicitada:</strong> {fecha_hora_solicitada if fecha_hora_solicitada else 'No especificada'}</p>
                    <p>🕐 <strong>Fecha de solicitud:</strong> {fecha_creacion}</p>
                </div>
            </div>""", unsafe_allow_html=True)

            if estado == 'pendiente':
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                with col_btn1:
                    if st.button("✅ Aprobar", key=f"aprobar_{reserva['id']}_{i}", use_container_width=True):
                        actualizar_estado_reserva(reserva['id'], 'aprobada')
                        # Notificar al usuario por Telegram
                        msg = (f"✅ ¡Su reserva ha sido APROBADA!\n\n"
                               f"📋 Área: {area}\n"
                               f"📅 Fecha/Hora: {fecha_hora_solicitada if fecha_hora_solicitada else 'Por confirmar'}\n\n"
                               f"Recuerde cumplir con las normas de uso de áreas comunales.\n"
                               f"¡Que la disfrute! 😊")
                        if user_id:
                            enviar_notificacion_telegram(user_id, msg)
                        st.success("✅ Aprobada — Notificación enviada al residente")
                        st.cache_data.clear()
                        st.rerun()
                with col_btn2:
                    if st.button("❌ Rechazar", key=f"rechazar_{reserva['id']}_{i}", use_container_width=True):
                        actualizar_estado_reserva(reserva['id'], 'rechazada')
                        # Notificar al usuario por Telegram
                        msg = (f"❌ Su reserva ha sido RECHAZADA.\n\n"
                               f"📋 Área: {area}\n"
                               f"📅 Fecha/Hora: {fecha_hora_solicitada if fecha_hora_solicitada else 'No especificada'}\n\n"
                               f"Puede contactar a la administración para más información\n"
                               f"o solicitar otra fecha.")
                        if user_id:
                            enviar_notificacion_telegram(user_id, msg)
                        st.warning("❌ Rechazada — Notificación enviada al residente")
                        st.cache_data.clear()
                        st.rerun()

# ══════════════════════════════════════════════════════
# PÁGINA: EMERGENCIAS
# ══════════════════════════════════════════════════════
elif pagina == "🚨 Emergencias":
    st.markdown('<p class="page-header">🚨 Alertas de Emergencia</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Alertas detectadas automáticamente por el chatbot — requieren atención inmediata</p>', unsafe_allow_html=True)

    emergencias = obtener_emergencias()

    if not emergencias:
        st.success("✅ No hay alertas de emergencia registradas. Todo en orden.")
    else:
        no_atendidas = [e for e in emergencias if not e.get('atendida', False)]
        atendidas = [e for e in emergencias if e.get('atendida', False)]

        if no_atendidas:
            st.markdown(f'<p class="section-heading">⚠️ Sin atender ({len(no_atendidas)})</p>', unsafe_allow_html=True)
            for i, e in enumerate(no_atendidas):
                fecha = formatear_fecha(e.get('fecha', ''))
                st.markdown(f"""
                <div class="emergency-card">
                    <p class="emergency-title">🚨 {e.get('palabra_clave', 'N/A').upper()}</p>
                    <p class="emergency-detail">📝 {e.get('mensaje', 'N/A')}</p>
                    <p class="emergency-detail">👤 User ID: {e.get('user_id', 'N/A')}</p>
                    <p class="emergency-detail" style="color:#94A3B8; font-size:0.75rem;">📅 {fecha}</p>
                </div>""", unsafe_allow_html=True)

                if st.button(f"✅ Marcar como atendida", key=f"atender_{e['id']}_{i}"):
                    db.collection('alertas_emergencia').document(e['id']).update({
                        'atendida': True,
                        'fecha_atencion': datetime.now().isoformat()
                    })
                    st.success("Marcada como atendida")
                    st.cache_data.clear()
                    st.rerun()

        if atendidas:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(f"📋 Historial de emergencias atendidas ({len(atendidas)})"):
                for e in atendidas:
                    fecha = formatear_fecha(e.get('fecha', ''))
                    st.markdown(f"""
                    <div style="padding:0.5rem 0; border-bottom:1px solid #F1F5F9;">
                        <p style="margin:0; font-size:0.85rem; color:#475569;">
                            ✅ <strong>{e.get('palabra_clave', '').upper()}</strong> — {e.get('mensaje', '')[:80]}...
                            <span style="color:#94A3B8; font-size:0.75rem;"> · {fecha}</span>
                        </p>
                    </div>""", unsafe_allow_html=True)
