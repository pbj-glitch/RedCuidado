import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(
    page_title="RedCuidado - Analytics Dashboard",
    page_icon="",
    layout="wide"
)

# Estilos CSS personalizados para mejorar legibilidad de KPIs
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #1f77b4;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-title { font-size: 14px; color: #6c757d; font-weight: bold; }
    .metric-value { font-size: 26px; color: #1f2937; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("RedCuidado - Dashboard de Analítica & Big Data")
st.markdown("Plataforma de monitoreo e inteligencia de negocios integrada con **AWS S3 + Athena**.")
st.markdown("---")

@st.cache_data
def load_data():
    users = pd.read_csv("csv_export/users/data.csv")
    courses = pd.read_csv("csv_export/courses/data.csv")
    enrollments = pd.read_csv("csv_export/enrollments/data.csv")
    tests = pd.read_csv("csv_export/test_results/data.csv")
    return users, courses, enrollments, tests

try:
    users, courses, enrollments, tests = load_data()

    # --- CÁLCULO DE LOS 5 KPIs REQUERIDOS ---
    colab_activos = users[users['is_active'] == True].shape[0] if 'is_active' in users else len(users)
    total_cursos = len(courses)
    cursos_completados = enrollments[enrollments['is_completed'] == True].shape[0] if 'is_completed' in enrollments else 0
    
    total_inscripciones = len(enrollments)
    tasa_finalizacion = round((cursos_completados / total_inscripciones * 100), 1) if total_inscripciones > 0 else 0
    puntaje_promedio = round(tests['score'].mean(), 1) if 'score' in tests and not tests.empty else 0

    # --- TARJETAS SUPERIORES DE KPIs ---
    k1, k2, k3, k4, k5 = st.columns(5)
    
    with k1:
        st.markdown(f'<div class="metric-card"><div class="metric-title"> Colaboradores Activos</div><div class="metric-value">{colab_activos:,}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="metric-card"><div class="metric-title"> Cursos Totales</div><div class="metric-value">{total_cursos}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="metric-card"><div class="metric-title"> Cursos Completados</div><div class="metric-value">{cursos_completados:,}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="metric-card"><div class="metric-title"> Tasa Finalización</div><div class="metric-value">{tasa_finalizacion}%</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="metric-card"><div class="metric-title"> Puntaje Promedio</div><div class="metric-value">{puntaje_promedio} / 100</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SECCIÓN DE GRÁFICOS INTERACTIVOS ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Estado General de Inscripciones")
        df_status = enrollments['is_completed'].value_counts().reset_index()
        df_status.columns = ['Estado', 'Cantidad']
        df_status['Estado'] = df_status['Estado'].map({True: 'Completado', False: 'En Progreso'})
        
        fig_pie = px.pie(
            df_status, 
            values='Cantidad', 
            names='Estado', 
            hole=0.4,
            color='Estado',
            color_discrete_map={'Completado': '#2ecc71', 'En Progreso': '#e74c3c'}
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Distribución de Puntajes en Evaluaciones")
        fig_hist = px.histogram(
            tests, 
            x="score", 
            nbins=15, 
            labels={'score': 'Calificación (0 - 100)'},
            color_discrete_sequence=['#3498db']
        )
        fig_hist.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="Aprobación (70)")
        fig_hist.update_layout(yaxis_title="Número de Evaluaciones")
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # --- TABLA DE DETALLE INTERACTIVA ---
    st.subheader("Explorador de Cursos y Métricas")
    if 'title' in courses.columns and 'id' in courses.columns:
        merged_data = enrollments.merge(courses, left_on='course_id', right_on='id')
        course_summary = merged_data.groupby('title').agg(
            Inscritos=('id_x', 'count'),
            Completados=('is_completed', lambda x: x.sum())
        ).reset_index()
        course_summary['% Finalización'] = round((course_summary['Completados'] / course_summary['Inscritos']) * 100, 1)
        
        st.dataframe(course_summary, use_container_width=True)

except Exception as e:
    st.error(f"No se encontraron datos para mostrar. Asegúrate de haber ejecutado Ansible previamente: {e}")
