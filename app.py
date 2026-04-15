import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
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
# CSS COMPACTO Y PROFESIONAL
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'DM Sans', sans-serif; }

    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #1E3A5F 0%, #2D5F8B 100%); }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3,
    div[data-testid="stSidebar"] .stMarkdown h4,
    div[data-testid="stSidebar"] .stMarkdown h5 {
        color: white !important;
    }

    .page-title { font-size: 1.4rem; font-weight: 700; color: #1E3A5F; margin-bottom: 0.15rem; }
    .page-subtitle { font-size: 0.85rem; color: #666; margin-bottom: 1rem; }

    .kpi-box {
        background: #fff; border: 1px solid #E5E7EB; border-radius: 8px;
        padding: 0.8rem 1rem; text-align: center;
    }
    .kpi-num { font-size: 1.6rem; font-weight: 700; margin: 0; line-height: 1.2; }
    .kpi-label { font-size: 0.7rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.04em; margin: 0.15rem 0 0 0; font-weight: 600; }

    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 100px;
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
    }
    .badge-pendiente { background: #FEF3C7; color: #92400E; }
    .badge-en_proceso { background: #DBEAFE; color: #1E40AF; }
    .badge-resuelto { background: #D1FAE5; color: #065F46; }
    .badge-aprobada { background: #D1FAE5; color: #065F46; }
    .badge-rechazada { background: #FEE2E2; color: #991B1B; }

    .item-card {
        background: #fff; border: 1px solid #E5E7EB; border-radius: 8px;
        padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem;
    }
    .item-title { font-weight: 600; color: #1E3A5F; margin: 0 0 0.3rem 0; font-size: 0.9rem; }
    .item-detail { color: #475569; margin: 0.1rem 0; font-size: 0.8rem; }
    .item-meta { color: #9CA3AF; font-size: 0.72rem; }

    .emergency-card {
        background: #FEF2F2; border-left: 3px solid #DC2626; border-radius: 6px;
        padding: 0.6rem 0.8rem; margin-bottom: 0.4rem; font-size: 0.8rem;
    }

    .progress-bar-bg { background: #E5E7EB; border-radius: 100px; height: 8px; width: 100%; }
    .progress-bar-fill { background: #059669; border-radius: 100px; height: 8px; }

    .reservation-detail {
        background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 6px;
        padding: 0.5rem 0.75rem; margin: 0.3rem 0; font-size: 0.8rem; color: #0C4A6E;
    }

    .section-title { font-size: 0.95rem; font-weight: 700; color: #1E3A5F; margin-bottom: 0.6rem; padding-bottom: 0.3rem; border-bottom: 2px solid #E5E7EB; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## Balcón Real")
    st.markdown("##### Panel de Administración")
    st.markdown("---")

    pagina = st.radio(
        "Navegación",
        ["Dashboard", "Reportes", "Reservas", "Emergencias"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("##### Chatbot PLN v5.0")
    st.markdown("BETO · 20 intenciones")

    st.markdown("---")
    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════
# FUNCIONES DE DATOS
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
    try: return f[:16].replace('T', '  ')
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

EMOJI_TIPO = {
    'reporte_daño': '🔨', 'reporte_fuga': '💧', 'reporte_electrico': '⚡',
    'solicitud_mantenimiento': '🔧', 'queja_convivencia': '📢',
    'reporte_seguridad': '🔒', 'reclamo_pago': '💰', 'cancelar_reserva': '❌'
}

# ══════════════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════════════
if pagina == "Dashboard":
    st.markdown('<p class="page-title">Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Resumen de gestión — Conjunto Balcón Real</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()
    reservas = obtener_reservas()
    emergencias = obtener_emergencias()

    total = len(reportes)
    pendientes = len([r for r in reportes if r.get('estado') == 'pendiente'])
    en_proceso = len([r for r in reportes if r.get('estado') == 'en_proceso'])
    resueltos = len([r for r in reportes if r.get('estado') == 'resuelto'])
    pendientes_res = len([r for r in reservas if r.get('estado') == 'pendiente'])
    hoy = mensajes_hoy(reportes, reservas, emergencias)
    tiempo_prom = calcular_tiempo_resolucion(reportes)
    tasa_resolucion = (resueltos / total * 100) if total > 0 else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f'<div class="kpi-box"><p class="kpi-num" style="color:#2563EB">{total}</p><p class="kpi-label">Total Reportes</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-box"><p class="kpi-num" style="color:#D97706">{pendientes}</p><p class="kpi-label">Pendientes</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-box"><p class="kpi-num" style="color:#2563EB">{en_proceso}</p><p class="kpi-label">En Proceso</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-box"><p class="kpi-num" style="color:#059669">{resueltos}</p><p class="kpi-label">Resueltos</p></div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="kpi-box"><p class="kpi-num" style="color:#7C3AED">{pendientes_res}</p><p class="kpi-label">Reservas Pend.</p></div>', unsafe_allow_html=True)
    with c6:
        st.markdown(f'<div class="kpi-box"><p class="kpi-num" style="color:#0891B2">{hoy}</p><p class="kpi-label">Mensajes Hoy</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_tasa, col_tiempo = st.columns(2)
    with col_tasa:
        st.markdown('<p class="section-title">Tasa de Resolución</p>', unsafe_allow_html=True)
        fill_width = min(tasa_resolucion, 100)
        color = "#059669" if tasa_resolucion >= 70 else "#D97706" if tasa_resolucion >= 40 else "#DC2626"
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.75rem;">
            <div class="progress-bar-bg" style="flex:1;">
                <div class="progress-bar-fill" style="width:{fill_width}%; background:{color};"></div>
            </div>
            <span style="font-weight:700; font-size:1.1rem; color:{color};">{tasa_resolucion:.0f}%</span>
        </div>
        <p style="font-size:0.75rem; color:#9CA3AF; margin-top:0.25rem;">{resueltos} de {total} reportes resueltos</p>
        """, unsafe_allow_html=True)
    with col_tiempo:
        st.markdown('<p class="section-title">Tiempo Promedio de Resolución</p>', unsafe_allow_html=True)
        if tiempo_prom > 0:
            if tiempo_prom < 1: tiempo_txt = f"{tiempo_prom*60:.0f} minutos"
            elif tiempo_prom < 24: tiempo_txt = f"{tiempo_prom:.1f} horas"
            else: tiempo_txt = f"{tiempo_prom/24:.1f} días"
            st.markdown(f'<p style="font-size:1.3rem; font-weight:700; color:#1E3A5F; margin:0;">{tiempo_txt}</p>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.75rem; color:#9CA3AF;">Desde creación hasta resolución</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-size:0.85rem; color:#9CA3AF;">Sin datos de resolución aún</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown('<p class="section-title">Reportes por Tipo</p>', unsafe_allow_html=True)
        if reportes:
            tipos = {}
            for r in reportes:
                tipo = r.get('tipo', 'otro').replace('_', ' ').title()
                tipos[tipo] = tipos.get(tipo, 0) + 1
            df_tipos = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad']).sort_values('Cantidad', ascending=False)
            st.bar_chart(df_tipos.set_index('Tipo'), height=250)
        else:
            st.info("Sin datos")
    with col_g2:
        st.markdown('<p class="section-title">Estado de Reportes</p>', unsafe_allow_html=True)
        if reportes:
            df_estados = pd.DataFrame({'Estado': ['Pendiente', 'En proceso', 'Resuelto'], 'Cantidad': [pendientes, en_proceso, resueltos]})
            st.bar_chart(df_estados.set_index('Estado'), height=250)
        else:
            st.info("Sin datos")

    st.markdown("<br>", unsafe_allow_html=True)
    col_top, col_actividad = st.columns(2)
    with col_top:
        st.markdown('<p class="section-title">Top 3 Problemas Más Frecuentes</p>', unsafe_allow_html=True)
        if reportes:
            tipos = {}
            for r in reportes:
                tipo = r.get('tipo', 'otro').replace('_', ' ').title()
                tipos[tipo] = tipos.get(tipo, 0) + 1
            top3 = sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:3]
            for idx, (tipo, count) in enumerate(top3):
                medal = ["🥇", "🥈", "🥉"][idx]
                pct = count / total * 100 if total > 0 else 0
                st.markdown(f'<div style="display:flex; justify-content:space-between; padding:0.35rem 0; border-bottom:1px solid #F1F5F9;"><span style="font-size:0.85rem;">{medal} {tipo}</span><span style="font-size:0.8rem; color:#6B7280;">{count} ({pct:.0f}%)</span></div>', unsafe_allow_html=True)
    with col_actividad:
        st.markdown('<p class="section-title">Actividad Reciente</p>', unsafe_allow_html=True)
        if reportes:
            for r in reportes[:5]:
                emoji = EMOJI_TIPO.get(r.get('tipo', ''), '·')
                tipo = r.get('tipo', '').replace('_', ' ').title()
                fecha = fmt_fecha(r.get('fecha_creacion', ''))
                desc = r.get('descripcion', '')[:60]
                st.markdown(f'<div style="padding:0.3rem 0; border-bottom:1px solid #F1F5F9; font-size:0.8rem;"><span style="color:#1E3A5F; font-weight:600;">{emoji} {tipo}</span><span style="color:#9CA3AF;"> · {fecha}</span><br><span style="color:#6B7280;">{desc}</span></div>', unsafe_allow_html=True)

    if emergencias:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-title">Alertas de Emergencia Recientes</p>', unsafe_allow_html=True)
        for e in emergencias[:3]:
            st.markdown(f'<div class="emergency-card"><strong style="color:#991B1B;">{e.get("palabra_clave", "").upper()}</strong><span style="color:#9CA3AF; font-size:0.72rem;"> · {fmt_fecha(e.get("fecha", ""))}</span><br><span style="color:#7F1D1D; font-size:0.78rem;">{e.get("mensaje", "")[:100]}</span></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PÁGINA: REPORTES
# ══════════════════════════════════════════════════════
elif pagina == "Reportes":
    st.markdown('<p class="page-title">Reportes de Mantenimiento</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Gestione los reportes recibidos por el chatbot</p>', unsafe_allow_html=True)

    reportes = obtener_reportes()

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        tipos_unicos = sorted(set(r.get('tipo', '') for r in reportes))
        filtro_tipo = st.selectbox("Tipo", ["Todos"] + tipos_unicos, key="rep_tipo")
    with col_f2:
        torres_unicas = sorted(set(str(r.get('torre', '')) for r in reportes if r.get('torre') and str(r.get('torre')) != 'None'))
        filtro_torre = st.selectbox("Torre", ["Todas"] + torres_unicas, key="rep_torre")
    with col_f3:
        buscar = st.text_input("Buscar", placeholder="Buscar en descripción...", key="rep_buscar")

    reportes_f = reportes
    if filtro_tipo != "Todos":
        reportes_f = [r for r in reportes_f if r.get('tipo') == filtro_tipo]
    if filtro_torre != "Todas":
        reportes_f = [r for r in reportes_f if str(r.get('torre', '')) == filtro_torre]
    if buscar:
        reportes_f = [r for r in reportes_f if buscar.lower() in r.get('descripcion', '').lower()]

    col_count, col_export = st.columns([3, 1])
    with col_count:
        st.markdown(f"**{len(reportes_f)}** reportes encontrados")
    with col_export:
        if reportes_f:
            excel_data = exportar_reportes_excel(reportes_f)
            st.download_button("Exportar Excel", data=excel_data, file_name=f"reportes_balcon_real_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    tab_pend, tab_proc, tab_res = st.tabs(["Pendientes", "En Proceso", "Resueltos"])

    def mostrar_reportes(lista, tab_key):
        if not lista:
            st.info("No hay reportes en esta categoría.")
            return
        for i, r in enumerate(lista):
            emoji = EMOJI_TIPO.get(r.get('tipo', ''), '·')
            tipo = r.get('tipo', '').replace('_', ' ').title()
            estado = r.get('estado', 'pendiente')
            fecha = fmt_fecha(r.get('fecha_creacion', ''))
            torre = r.get('torre', '')
            depto = r.get('depto', '')
            ubicacion = f"Torre {torre}, Depto {depto}" if torre and str(torre) != 'None' else ""

            st.markdown(f"""<div class="item-card"><div style="display:flex; justify-content:space-between; align-items:center;"><p class="item-title">{emoji} {tipo}</p><span class="badge badge-{estado}">{estado.replace('_',' ')}</span></div><p class="item-detail">{r.get('descripcion', '')}</p><p class="item-meta">{fecha}{(' · ' + ubicacion) if ubicacion else ''} · ID: {r.get('user_id', 'N/A')}</p>{f'<p class="item-detail" style="color:#2563EB;">Nota: {r.get("notas_admin")}</p>' if r.get('notas_admin') else ''}</div>""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                nuevo = st.selectbox("Estado", ["pendiente", "en_proceso", "resuelto"], index=["pendiente", "en_proceso", "resuelto"].index(estado), key=f"e_{tab_key}_{r['id']}_{i}", label_visibility="collapsed")
            with c2:
                nota = st.text_input("Nota", value=r.get('notas_admin', ''), placeholder="Agregar nota...", key=f"n_{tab_key}_{r['id']}_{i}", label_visibility="collapsed")
            with c3:
                if st.button("Guardar", key=f"b_{tab_key}_{r['id']}_{i}", use_container_width=True):
                    actualizar_estado_reporte(r['id'], nuevo, nota)
                    st.success("Actualizado")
                    st.cache_data.clear()
                    st.rerun()

    with tab_pend:
        mostrar_reportes([r for r in reportes_f if r.get('estado') == 'pendiente'], 'pend')
    with tab_proc:
        mostrar_reportes([r for r in reportes_f if r.get('estado') == 'en_proceso'], 'proc')
    with tab_res:
        mostrar_reportes([r for r in reportes_f if r.get('estado') == 'resuelto'], 'res')

# ══════════════════════════════════════════════════════
# PÁGINA: RESERVAS
# ══════════════════════════════════════════════════════
elif pagina == "Reservas":
    st.markdown('<p class="page-title">Solicitudes de Reserva</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Apruebe o rechace reservas — el residente será notificado por Telegram</p>', unsafe_allow_html=True)

    reservas = obtener_reservas()
    tab_pend, tab_apr, tab_rech = st.tabs(["Pendientes", "Aprobadas", "Rechazadas"])

    def mostrar_reservas(lista, tab_key, mostrar_botones=False):
        if not lista:
            st.info("No hay reservas en esta categoría.")
            return
        for i, r in enumerate(lista):
            estado = r.get('estado', 'pendiente')
            area = r.get('area', 'No especificada')
            torre = r.get('torre', 'N/A')
            depto = r.get('depto', 'N/A')
            fecha_hora = r.get('fecha_hora_solicitada', None)
            fecha_creacion = fmt_fecha(r.get('fecha_creacion', ''))
            user_id = r.get('user_id', '')

            st.markdown(f"""<div class="item-card"><div style="display:flex; justify-content:space-between; align-items:center;"><p class="item-title">{area}</p><span class="badge badge-{estado}">{estado}</span></div><div class="reservation-detail"><strong>Solicitante:</strong> Torre {torre}, Depto {depto}<br><strong>Fecha/Hora solicitada:</strong> {fecha_hora if fecha_hora else 'No especificada'}<br><strong>Fecha de solicitud:</strong> {fecha_creacion}</div></div>""", unsafe_allow_html=True)

            if mostrar_botones:
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if st.button("Aprobar", key=f"apr_{tab_key}_{r['id']}_{i}", use_container_width=True):
                        actualizar_estado_reserva(r['id'], 'aprobada')
                        msg = f"Su reserva ha sido APROBADA.\n\nArea: {area}\nFecha/Hora: {fecha_hora if fecha_hora else 'Por confirmar'}\n\nRecuerde cumplir con las normas de uso."
                        if user_id: enviar_notificacion_telegram(user_id, msg)
                        st.success("Aprobada — Notificación enviada")
                        st.cache_data.clear()
                        st.rerun()
                with c2:
                    if st.button("Rechazar", key=f"rech_{tab_key}_{r['id']}_{i}", use_container_width=True):
                        actualizar_estado_reserva(r['id'], 'rechazada')
                        msg = f"Su reserva ha sido RECHAZADA.\n\nArea: {area}\nFecha/Hora: {fecha_hora if fecha_hora else 'No especificada'}\n\nContacte a la administración para más información."
                        if user_id: enviar_notificacion_telegram(user_id, msg)
                        st.warning("Rechazada — Notificación enviada")
                        st.cache_data.clear()
                        st.rerun()

    with tab_pend:
        mostrar_reservas([r for r in reservas if r.get('estado') == 'pendiente'], 'pend', mostrar_botones=True)
    with tab_apr:
        mostrar_reservas([r for r in reservas if r.get('estado') == 'aprobada'], 'apr')
    with tab_rech:
        mostrar_reservas([r for r in reservas if r.get('estado') == 'rechazada'], 'rech')

# ══════════════════════════════════════════════════════
# PÁGINA: EMERGENCIAS
# ══════════════════════════════════════════════════════
elif pagina == "Emergencias":
    st.markdown('<p class="page-title">Alertas de Emergencia</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Alertas detectadas automáticamente por el chatbot</p>', unsafe_allow_html=True)

    emergencias = obtener_emergencias()

    if not emergencias:
        st.success("No hay alertas de emergencia registradas.")
    else:
        no_atendidas = [e for e in emergencias if not e.get('atendida', False)]
        atendidas = [e for e in emergencias if e.get('atendida', False)]

        tab_activas, tab_historial = st.tabs([f"Activas ({len(no_atendidas)})", f"Historial ({len(atendidas)})"])

        with tab_activas:
            if not no_atendidas:
                st.success("Todas las emergencias han sido atendidas.")
            for i, e in enumerate(no_atendidas):
                fecha = fmt_fecha(e.get('fecha', ''))
                st.markdown(f'<div class="emergency-card"><strong style="color:#991B1B;">{e.get("palabra_clave", "").upper()}</strong><span style="color:#9CA3AF; font-size:0.72rem;"> · {fecha}</span><br><span style="color:#7F1D1D; font-size:0.8rem;">{e.get("mensaje", "")}</span><br><span style="color:#9CA3AF; font-size:0.72rem;">User ID: {e.get("user_id", "N/A")}</span></div>', unsafe_allow_html=True)
                if st.button("Marcar como atendida", key=f"at_{e['id']}_{i}"):
                    db.collection('alertas_emergencia').document(e['id']).update({'atendida': True, 'fecha_atencion': datetime.now().isoformat()})
                    st.success("Marcada como atendida")
                    st.cache_data.clear()
                    st.rerun()

        with tab_historial:
            if not atendidas:
                st.info("No hay emergencias en el historial.")
            for e in atendidas:
                fecha = fmt_fecha(e.get('fecha', ''))
                st.markdown(f'<div style="padding:0.35rem 0; border-bottom:1px solid #F1F5F9; font-size:0.8rem;"><strong style="color:#065F46;">{e.get("palabra_clave", "").upper()}</strong><span style="color:#9CA3AF; font-size:0.72rem;"> · {fecha}</span><br><span style="color:#6B7280;">{e.get("mensaje", "")[:80]}</span></div>', unsafe_allow_html=True)
