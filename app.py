import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os

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
# ESTILOS CSS
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
    st.markdown("##### Chatbot PLN v3.0")
    st.markdown("BETO · 20 intenciones · 81% acc")
    
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

# ══════════════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 Dashboard General</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Vista general del estado de gestión del conjunto Balcón Real</p>', unsafe_allow_html=True)
    
    reportes = obtener_reportes()
    reservas = obtener_reservas()
    emergencias = obtener_emergencias()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    pendientes_rep = len([r for r in reportes if r.get('estado') == 'pendiente'])
    en_proceso = len([r for r in reportes if r.get('estado') == 'en_proceso'])
    resueltos = len([r for r in reportes if r.get('estado') == 'resuelto'])
    pendientes_res = len([r for r in reservas if r.get('estado') == 'pendiente'])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-number">{pendientes_rep}</p>
            <p class="metric-label">Reportes Pendientes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card-orange">
            <p class="metric-number">{en_proceso}</p>
            <p class="metric-label">En Proceso</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card-green">
            <p class="metric-number">{resueltos}</p>
            <p class="metric-label">Resueltos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card-red">
            <p class="metric-number">{pendientes_res}</p>
            <p class="metric-label">Reservas Pendientes</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Reportes por tipo
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🔧 Reportes por Tipo")
        if reportes:
            tipos = {}
            for r in reportes:
                tipo = r.get('tipo', 'sin_tipo')
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            import pandas as pd
            df_tipos = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad'])
            st.bar_chart(df_tipos.set_index('Tipo'))
        else:
            st.info("No hay reportes registrados aún.")
    
    with col_right:
        st.markdown("#### 📅 Últimas Actividades")
        if reportes:
            for r in reportes[:5]:
                tipo_emoji = {
                    'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
                    'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
                    'reporte_seguridad': '🔒', 'reclamo_pago': '💰'
                }.get(r.get('tipo', ''), '📋')
                
                fecha = r.get('fecha_creacion', '')[:16].replace('T', ' ')
                st.markdown(f"{tipo_emoji} **{r.get('tipo', 'N/A')}** — {fecha}")
                st.markdown(f"  _{r.get('descripcion', '')[:80]}..._")
                st.markdown("")
        else:
            st.info("No hay actividad registrada aún.")
    
    # Emergencias
    if emergencias:
        st.markdown("---")
        st.markdown("#### 🚨 Alertas de Emergencia Recientes")
        for e in emergencias[:3]:
            st.error(f"**{e.get('palabra_clave', '')}** — {e.get('mensaje', '')[:100]} — {e.get('fecha', '')[:16]}")

# ══════════════════════════════════════════════════════
# PÁGINA: REPORTES DE MANTENIMIENTO
# ══════════════════════════════════════════════════════
elif pagina == "🔧 Reportes de Mantenimiento":
    st.markdown('<p class="main-header">🔧 Reportes de Mantenimiento</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestione los reportes recibidos por el chatbot</p>', unsafe_allow_html=True)
    
    reportes = obtener_reportes()
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_estado = st.selectbox("Filtrar por estado", ["Todos", "pendiente", "en_proceso", "resuelto"])
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos"] + list(set(r.get('tipo', '') for r in reportes)))
    
    # Aplicar filtros
    reportes_filtrados = reportes
    if filtro_estado != "Todos":
        reportes_filtrados = [r for r in reportes_filtrados if r.get('estado') == filtro_estado]
    if filtro_tipo != "Todos":
        reportes_filtrados = [r for r in reportes_filtrados if r.get('tipo') == filtro_tipo]
    
    st.markdown(f"**{len(reportes_filtrados)} reportes encontrados**")
    st.markdown("---")
    
    if not reportes_filtrados:
        st.info("No hay reportes con los filtros seleccionados.")
    
    for i, reporte in enumerate(reportes_filtrados):
        tipo_emoji = {
            'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
            'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
            'reporte_seguridad': '🔒', 'reclamo_pago': '💰'
        }.get(reporte.get('tipo', ''), '📋')
        
        estado = reporte.get('estado', 'pendiente')
        estado_class = f"status-{estado}"
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {tipo_emoji} {reporte.get('tipo', 'N/A').replace('_', ' ').title()}")
                st.markdown(f"📝 **Descripción:** {reporte.get('descripcion', 'Sin descripción')}")
                
                torre = reporte.get('torre', 'N/A')
                depto = reporte.get('depto', 'N/A')
                if torre and torre != 'None' and depto and depto != 'None':
                    st.markdown(f"🏠 **Ubicación:** Torre {torre}, Depto {depto}")
                
                fecha = reporte.get('fecha_creacion', '')[:16].replace('T', ' ')
                st.markdown(f"📅 **Fecha:** {fecha}")
                
                if reporte.get('notas_admin'):
                    st.markdown(f"💬 **Notas admin:** {reporte.get('notas_admin')}")
            
            with col2:
                st.markdown(f'<span class="{estado_class}">{estado.upper()}</span>', unsafe_allow_html=True)
                
                nuevo_estado = st.selectbox(
                    "Cambiar estado",
                    ["pendiente", "en_proceso", "resuelto"],
                    index=["pendiente", "en_proceso", "resuelto"].index(estado),
                    key=f"estado_{reporte['id']}_{i}"
                )
                
                notas = st.text_input("Agregar nota", value=reporte.get('notas_admin', ''), key=f"nota_{reporte['id']}_{i}")
                
                if st.button("💾 Guardar", key=f"btn_{reporte['id']}_{i}"):
                    actualizar_estado_reporte(reporte['id'], nuevo_estado, notas)
                    st.success("✅ Actualizado")
                    st.cache_data.clear()
                    st.rerun()
            
            st.markdown("---")

# ══════════════════════════════════════════════════════
# PÁGINA: RESERVAS
# ══════════════════════════════════════════════════════
elif pagina == "📅 Reservas":
    st.markdown('<p class="main-header">📅 Solicitudes de Reserva</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Apruebe o rechace las solicitudes de reserva de áreas comunales</p>', unsafe_allow_html=True)
    
    reservas = obtener_reservas()
    
    # Filtro
    filtro_estado_res = st.selectbox("Filtrar por estado", ["Todos", "pendiente", "aprobada", "rechazada"])
    
    if filtro_estado_res != "Todos":
        reservas = [r for r in reservas if r.get('estado') == filtro_estado_res]
    
    st.markdown(f"**{len(reservas)} solicitudes encontradas**")
    st.markdown("---")
    
    if not reservas:
        st.info("No hay solicitudes de reserva con los filtros seleccionados.")
    
    for i, reserva in enumerate(reservas):
        estado = reserva.get('estado', 'pendiente')
        estado_class = f"status-{estado}"
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🏢 {reserva.get('area', 'Área no especificada')}")
                st.markdown(f"🏠 **Solicitante:** Torre {reserva.get('torre', 'N/A')}, Depto {reserva.get('depto', 'N/A')}")
                
                fecha = reserva.get('fecha_creacion', '')[:16].replace('T', ' ')
                st.markdown(f"📅 **Fecha solicitud:** {fecha}")
            
            with col2:
                st.markdown(f'<span class="{estado_class}">{estado.upper()}</span>', unsafe_allow_html=True)
                
                if estado == 'pendiente':
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✅ Aprobar", key=f"aprobar_{reserva['id']}_{i}"):
                            actualizar_estado_reserva(reserva['id'], 'aprobada')
                            st.success("✅ Aprobada")
                            st.cache_data.clear()
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Rechazar", key=f"rechazar_{reserva['id']}_{i}"):
                            actualizar_estado_reserva(reserva['id'], 'rechazada')
                            st.warning("❌ Rechazada")
                            st.cache_data.clear()
                            st.rerun()
            
            st.markdown("---")

# ══════════════════════════════════════════════════════
# PÁGINA: EMERGENCIAS
# ══════════════════════════════════════════════════════
elif pagina == "🚨 Emergencias":
    st.markdown('<p class="main-header">🚨 Alertas de Emergencia</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Alertas detectadas automáticamente por el chatbot</p>', unsafe_allow_html=True)
    
    emergencias = obtener_emergencias()
    
    if not emergencias:
        st.success("✅ No hay alertas de emergencia registradas.")
    
    for e in emergencias:
        with st.container():
            st.error(f"""
            **🚨 EMERGENCIA: {e.get('palabra_clave', 'N/A').upper()}**
            
            📝 Mensaje: {e.get('mensaje', 'N/A')}
            
            📅 Fecha: {e.get('fecha', '')[:16].replace('T', ' ')}
            
            👤 User ID: {e.get('user_id', 'N/A')}
            """)
            st.markdown("---")
