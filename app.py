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
# ESTILOS CSS (diseño original preservado)
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card-green {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card-red {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card-teal {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card-dark {
        background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-number {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0;
    }
    .status-pendiente {
        background-color: #FFF3CD;
        color: #856404;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-en_proceso {
        background-color: #CCE5FF;
        color: #004085;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-resuelto {
        background-color: #D4EDDA;
        color: #155724;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-aprobada {
        background-color: #D4EDDA;
        color: #155724;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-rechazada {
        background-color: #F8D7DA;
        color: #721C24;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A5F 0%, #2D5F8B 100%);
    }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3 {
        color: white !important;
    }
    .progress-bg {
        background: #E5E7EB;
        border-radius: 100px;
        height: 10px;
        width: 100%;
    }
    .progress-fill {
        border-radius: 100px;
        height: 10px;
    }
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
        ["📊 Dashboard", "🔧 Reportes de Mantenimiento", "📅 Reservas", "🚨 Emergencias"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### Chatbot PLN v5.0")
    st.markdown("BETO · 20 intenciones · 83% acc")

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

def fmt_fecha(f):
    if not f: return "—"
    try: return f[:16].replace('T', ' ')
    except: return str(f)

def calcular_tiempo_resolucion(reportes):
    tiempos = []
    for r in reportes:
        if r.get('estado') == 'resuelto' and r.get('fecha_creacion') and r.get('fecha_actualizacion'):
            try:
                creacion = datetime.fromisoformat(r['fecha_creacion'])
                actualizacion = datetime.fromisoformat(r['fecha_actualizacion'])
                diff = (actualizacion - creacion).total_seconds() / 3600
                if diff > 0: tiempos.append(diff)
            except: pass
    return sum(tiempos) / len(tiempos) if tiempos else 0

def mensajes_hoy(reportes, reservas, emergencias):
    hoy = datetime.now().strftime('%Y-%m-%d')
    count = 0
    for r in reportes:
        if r.get('fecha_creacion', '').startswith(hoy): count += 1
    for r in reservas:
        if r.get('fecha_creacion', '').startswith(hoy): count += 1
    for e in emergencias:
        if e.get('fecha', '').startswith(hoy): count += 1
    return count

def exportar_reportes_excel(reportes):
    rows = []
    for r in reportes:
        rows.append({
            'Tipo': r.get('tipo', '').replace('_', ' ').title(),
            'Descripción': r.get('descripcion', ''),
            'Estado': r.get('estado', ''),
            'Torre': r.get('torre', ''),
            'Depto': r.get('depto', ''),
            'Notas Admin': r.get('notas_admin', ''),
            'Fecha Creación': fmt_fecha(r.get('fecha_creacion', '')),
            'Última Actualización': fmt_fecha(r.get('fecha_actualizacion', '')),
        })
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer

# ══════════════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 Dashboard General</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Vista general del estado de gestión del conjunto Balcón Real</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()
    reservas = obtener_reservas()
    emergencias = obtener_emergencias()

    total = len(reportes)
    pendientes_rep = len([r for r in reportes if r.get('estado') == 'pendiente'])
    en_proceso = len([r for r in reportes if r.get('estado') == 'en_proceso'])
    resueltos = len([r for r in reportes if r.get('estado') == 'resuelto'])
    pendientes_res = len([r for r in reservas if r.get('estado') == 'pendiente'])
    hoy = mensajes_hoy(reportes, reservas, emergencias)

    # Métricas principales
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-number">{total}</p>
            <p class="metric-label">Total Reportes</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card-orange">
            <p class="metric-number">{pendientes_rep}</p>
            <p class="metric-label">Pendientes</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card-green">
            <p class="metric-number">{en_proceso}</p>
            <p class="metric-label">En Proceso</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card-teal">
            <p class="metric-number">{resueltos}</p>
            <p class="metric-label">Resueltos</p>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card-red">
            <p class="metric-number">{pendientes_res}</p>
            <p class="metric-label">Reservas Pend.</p>
        </div>""", unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
        <div class="metric-card-dark">
            <p class="metric-number">{hoy}</p>
            <p class="metric-label">Mensajes Hoy</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Tasa de resolución + Tiempo promedio
    tasa = (resueltos / total * 100) if total > 0 else 0
    tiempo_prom = calcular_tiempo_resolucion(reportes)

    col_tasa, col_tiempo = st.columns(2)
    with col_tasa:
        st.markdown("#### Tasa de Resolución")
        color = "#28a745" if tasa >= 70 else "#ffc107" if tasa >= 40 else "#dc3545"
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:1rem; margin-top:0.5rem;">
            <div class="progress-bg" style="flex:1;">
                <div class="progress-fill" style="width:{min(tasa,100)}%; background:{color};"></div>
            </div>
            <span style="font-weight:800; font-size:1.5rem; color:{color};">{tasa:.0f}%</span>
        </div>
        <p style="font-size:0.85rem; color:#888; margin-top:0.3rem;">{resueltos} de {total} reportes resueltos</p>
        """, unsafe_allow_html=True)

    with col_tiempo:
        st.markdown("#### ⏱️ Tiempo Promedio de Resolución")
        if tiempo_prom > 0:
            if tiempo_prom < 1: tiempo_txt = f"{tiempo_prom*60:.0f} minutos"
            elif tiempo_prom < 24: tiempo_txt = f"{tiempo_prom:.1f} horas"
            else: tiempo_txt = f"{tiempo_prom/24:.1f} días"
            st.markdown(f"<p style='font-size:2rem; font-weight:800; color:#1E3A5F; margin:0.5rem 0 0 0;'>{tiempo_txt}</p>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.85rem; color:#888;'>Desde creación hasta resolución</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#888;'>Sin datos de resolución aún</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🔧 Reportes por Tipo")
        if reportes:
            tipos = {}
            for r in reportes:
                tipo = r.get('tipo', 'sin_tipo').replace('_', ' ').title()
                tipos[tipo] = tipos.get(tipo, 0) + 1
            df_tipos = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad']).sort_values('Cantidad', ascending=False)
            st.bar_chart(df_tipos.set_index('Tipo'))
        else:
            st.info("No hay reportes registrados aún.")

    with col_right:
        st.markdown("#### 📈 Estado de Reportes")
        if reportes:
            df_estados = pd.DataFrame({
                'Estado': ['Pendiente', 'En proceso', 'Resuelto'],
                'Cantidad': [pendientes_rep, en_proceso, resueltos]
            })
            st.bar_chart(df_estados.set_index('Estado'))
        else:
            st.info("No hay datos aún.")

    st.markdown("---")

    # Top 3 + Actividad reciente
    col_top, col_actividad = st.columns(2)

    with col_top:
        st.markdown("#### 🏆 Top 3 Problemas Más Frecuentes")
        if reportes:
            tipos = {}
            for r in reportes:
                tipo = r.get('tipo', 'otro').replace('_', ' ').title()
                tipos[tipo] = tipos.get(tipo, 0) + 1
            top3 = sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:3]
            medals = ["🥇", "🥈", "🥉"]
            for idx, (tipo, count) in enumerate(top3):
                pct = count / total * 100 if total > 0 else 0
                st.markdown(f"{medals[idx]} **{tipo}** — {count} reportes ({pct:.0f}%)")
        else:
            st.info("Sin datos")

    with col_actividad:
        st.markdown("#### 📋 Últimas Actividades")
        if reportes:
            tipo_emoji = {
                'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
                'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
                'reporte_seguridad': '🔒', 'reclamo_pago': '💰'
            }
            for r in reportes[:5]:
                emoji = tipo_emoji.get(r.get('tipo', ''), '📋')
                fecha = fmt_fecha(r.get('fecha_creacion', ''))
                st.markdown(f"{emoji} **{r.get('tipo', 'N/A').replace('_',' ').title()}** — {fecha}")
                st.markdown(f"  _{r.get('descripcion', '')[:80]}..._")
                st.markdown("")
        else:
            st.info("No hay actividad registrada aún.")

    # Emergencias
    if emergencias:
        st.markdown("---")
        st.markdown("#### 🚨 Alertas de Emergencia Recientes")
        for e in emergencias[:3]:
            st.error(f"**{e.get('palabra_clave', '')}** — {e.get('mensaje', '')[:100]} — {fmt_fecha(e.get('fecha', ''))}")

# ══════════════════════════════════════════════════════
# PÁGINA: REPORTES DE MANTENIMIENTO
# ══════════════════════════════════════════════════════
elif pagina == "🔧 Reportes de Mantenimiento":
    st.markdown('<p class="main-header">🔧 Reportes de Mantenimiento</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestione los reportes recibidos por el chatbot</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()

    # Filtros
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos"] + sorted(set(r.get('tipo', '') for r in reportes)))
    with col_f2:
        torres_unicas = sorted(set(str(r.get('torre', '')) for r in reportes if r.get('torre') and str(r.get('torre')) != 'None'))
        filtro_torre = st.selectbox("Filtrar por torre", ["Todas"] + torres_unicas)
    with col_f3:
        buscar = st.text_input("🔍 Buscar en descripción", placeholder="Escriba para buscar...")

    # Aplicar filtros
    reportes_f = reportes
    if filtro_tipo != "Todos":
        reportes_f = [r for r in reportes_f if r.get('tipo') == filtro_tipo]
    if filtro_torre != "Todas":
        reportes_f = [r for r in reportes_f if str(r.get('torre', '')) == filtro_torre]
    if buscar:
        reportes_f = [r for r in reportes_f if buscar.lower() in r.get('descripcion', '').lower()]

    # Contador + Exportar
    col_count, col_export = st.columns([3, 1])
    with col_count:
        st.markdown(f"**{len(reportes_f)} reportes encontrados**")
    with col_export:
        if reportes_f:
            excel_data = exportar_reportes_excel(reportes_f)
            st.download_button("📥 Exportar Excel", data=excel_data,
                file_name=f"reportes_balcon_real_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

    # Pestañas por estado
    tab_pend, tab_proc, tab_res = st.tabs(["⏳ Pendientes", "🔄 En Proceso", "✅ Resueltos"])

    def mostrar_reportes(lista, tab_key):
        if not lista:
            st.info("No hay reportes en esta categoría.")
            return

        tipo_emoji = {
            'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
            'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
            'reporte_seguridad': '🔒', 'reclamo_pago': '💰'
        }

        for i, reporte in enumerate(lista):
            emoji = tipo_emoji.get(reporte.get('tipo', ''), '📋')
            estado = reporte.get('estado', 'pendiente')
            estado_class = f"status-{estado}"

            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {emoji} {reporte.get('tipo', 'N/A').replace('_', ' ').title()}")
                    st.markdown(f"📝 **Descripción:** {reporte.get('descripcion', 'Sin descripción')}")

                    torre = reporte.get('torre', 'N/A')
                    depto = reporte.get('depto', 'N/A')
                    if torre and torre != 'None' and depto and depto != 'None':
                        st.markdown(f"🏠 **Ubicación:** Torre {torre}, Depto {depto}")

                    fecha = fmt_fecha(reporte.get('fecha_creacion', ''))
                    st.markdown(f"📅 **Fecha:** {fecha}")

                    if reporte.get('notas_admin'):
                        st.markdown(f"💬 **Notas admin:** {reporte.get('notas_admin')}")

                with col2:
                    st.markdown(f'<span class="{estado_class}">{estado.upper()}</span>', unsafe_allow_html=True)

                    nuevo_estado = st.selectbox(
                        "Cambiar estado",
                        ["pendiente", "en_proceso", "resuelto"],
                        index=["pendiente", "en_proceso", "resuelto"].index(estado),
                        key=f"estado_{tab_key}_{reporte['id']}_{i}"
                    )

                    notas = st.text_input("Agregar nota", value=reporte.get('notas_admin', ''), key=f"nota_{tab_key}_{reporte['id']}_{i}")

                    if st.button("💾 Guardar", key=f"btn_{tab_key}_{reporte['id']}_{i}"):
                        actualizar_estado_reporte(reporte['id'], nuevo_estado, notas)
                        st.success("✅ Actualizado")
                        st.cache_data.clear()
                        st.rerun()

                st.markdown("---")

    with tab_pend:
        mostrar_reportes([r for r in reportes_f if r.get('estado') == 'pendiente'], 'pend')
    with tab_proc:
        mostrar_reportes([r for r in reportes_f if r.get('estado') == 'en_proceso'], 'proc')
    with tab_res:
        mostrar_reportes([r for r in reportes_f if r.get('estado') == 'resuelto'], 'res')

# ══════════════════════════════════════════════════════
# PÁGINA: RESERVAS
# ══════════════════════════════════════════════════════
elif pagina == "📅 Reservas":
    st.markdown('<p class="main-header">📅 Solicitudes de Reserva</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Apruebe o rechace las solicitudes de reserva — el residente será notificado por Telegram</p>', unsafe_allow_html=True)

    reservas = obtener_reservas()

    # Pestañas por estado
    tab_pend, tab_apr, tab_rech = st.tabs(["⏳ Pendientes", "✅ Aprobadas", "❌ Rechazadas"])

    def mostrar_reservas(lista, tab_key, mostrar_botones=False):
        if not lista:
            st.info("No hay solicitudes en esta categoría.")
            return

        for i, reserva in enumerate(lista):
            estado = reserva.get('estado', 'pendiente')
            estado_class = f"status-{estado}"
            area = reserva.get('area', 'Área no especificada')
            torre = reserva.get('torre', 'N/A')
            depto = reserva.get('depto', 'N/A')
            fecha_hora = reserva.get('fecha_hora_solicitada', None)
            fecha_creacion = fmt_fecha(reserva.get('fecha_creacion', ''))
            user_id = reserva.get('user_id', '')

            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### 🏢 {area}")
                    st.markdown(f"🏠 **Solicitante:** Torre {torre}, Depto {depto}")
                    st.markdown(f"📅 **Fecha/Hora solicitada:** {fecha_hora if fecha_hora else 'No especificada'}")
                    st.markdown(f"🕐 **Fecha de solicitud:** {fecha_creacion}")

                with col2:
                    st.markdown(f'<span class="{estado_class}">{estado.upper()}</span>', unsafe_allow_html=True)

                    if mostrar_botones:
                        if st.button("✅ Aprobar", key=f"aprobar_{tab_key}_{reserva['id']}_{i}", use_container_width=True):
                            actualizar_estado_reserva(reserva['id'], 'aprobada')
                            msg = (f"✅ Su reserva ha sido APROBADA.\n\n"
                                   f"Área: {area}\n"
                                   f"Fecha/Hora: {fecha_hora if fecha_hora else 'Por confirmar'}\n\n"
                                   f"Recuerde cumplir con las normas de uso de áreas comunales.")
                            if user_id: enviar_notificacion_telegram(user_id, msg)
                            st.success("✅ Aprobada — Notificación enviada")
                            st.cache_data.clear()
                            st.rerun()

                        if st.button("❌ Rechazar", key=f"rechazar_{tab_key}_{reserva['id']}_{i}", use_container_width=True):
                            actualizar_estado_reserva(reserva['id'], 'rechazada')
                            msg = (f"❌ Su reserva ha sido RECHAZADA.\n\n"
                                   f"Área: {area}\n"
                                   f"Fecha/Hora: {fecha_hora if fecha_hora else 'No especificada'}\n\n"
                                   f"Contacte a la administración para más información.")
                            if user_id: enviar_notificacion_telegram(user_id, msg)
                            st.warning("❌ Rechazada — Notificación enviada")
                            st.cache_data.clear()
                            st.rerun()

                st.markdown("---")

    with tab_pend:
        mostrar_reservas([r for r in reservas if r.get('estado') == 'pendiente'], 'pend', mostrar_botones=True)
    with tab_apr:
        mostrar_reservas([r for r in reservas if r.get('estado') == 'aprobada'], 'apr')
    with tab_rech:
        mostrar_reservas([r for r in reservas if r.get('estado') == 'rechazada'], 'rech')

# ══════════════════════════════════════════════════════
# PÁGINA: EMERGENCIAS
# ══════════════════════════════════════════════════════
elif pagina == "🚨 Emergencias":
    st.markdown('<p class="main-header">🚨 Alertas de Emergencia</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Alertas detectadas automáticamente por el chatbot</p>', unsafe_allow_html=True)

    emergencias = obtener_emergencias()

    if not emergencias:
        st.success("✅ No hay alertas de emergencia registradas.")
    else:
        no_atendidas = [e for e in emergencias if not e.get('atendida', False)]
        atendidas = [e for e in emergencias if e.get('atendida', False)]

        tab_activas, tab_historial = st.tabs([f"🔴 Activas ({len(no_atendidas)})", f"📋 Historial ({len(atendidas)})"])

        with tab_activas:
            if not no_atendidas:
                st.success("✅ Todas las emergencias han sido atendidas.")

            for i, e in enumerate(no_atendidas):
                with st.container():
                    st.error(f"""
                    **🚨 EMERGENCIA: {e.get('palabra_clave', 'N/A').upper()}**

                    📝 Mensaje: {e.get('mensaje', 'N/A')}

                    📅 Fecha: {fmt_fecha(e.get('fecha', ''))}

                    👤 User ID: {e.get('user_id', 'N/A')}
                    """)

                    if st.button("✅ Marcar como atendida", key=f"atender_{e['id']}_{i}"):
                        db.collection('alertas_emergencia').document(e['id']).update({
                            'atendida': True,
                            'fecha_atencion': datetime.now().isoformat()
                        })
                        st.success("Marcada como atendida")
                        st.cache_data.clear()
                        st.rerun()

                    st.markdown("---")

        with tab_historial:
            if not atendidas:
                st.info("No hay emergencias en el historial.")

            for e in atendidas:
                st.markdown(f"✅ **{e.get('palabra_clave', '').upper()}** — {e.get('mensaje', '')[:80]}... — {fmt_fecha(e.get('fecha', ''))}")
                st.markdown("")
