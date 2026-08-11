import streamlit as st
import pandas as pd
import plotly.express as px
import glob

st.set_page_config(page_title="RedCuidado - Analytics Dashboard", layout="wide")
st.title("RedCuidado - Dashboard de Analítica (Big Data)")

# Cargar datos desde los CSVs exportados
@st.cache_data
def load_data():
    users = pd.read_csv("csv_export/users/data.csv")
    courses = pd.read_csv("csv_export/courses/data.csv")
    enrollments = pd.read_csv("csv_export/enrollments/data.csv")
    tests = pd.read_csv("csv_export/test_results/data.csv")
    return users, courses, enrollments, tests

try:
    users, courses, enrollments, tests = load_data()

    # Cálculo de KPIs
    colab_activos = users[users['is_active'] == True].shape[0] if 'is_active' in users else len(users)
    total_cursos = len(courses)
    cursos_completados = enrollments[enrollments['is_completed'] == True].shape[0] if 'is_completed' in enrollments else 0

    total_inscripciones = len(enrollments)
    tasa_finalizacion = round((cursos_completados / total_inscripciones * 100), 2) if total_inscripciones > 0 else 0
    puntaje_promedio = round(tests['score'].mean(), 2) if 'score' in tests and not tests.empty else 0

    # Mostrar KPIs en tarjetas superiores
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Colaboradores Activos", colab_activos)
    kpi2.metric("Cursos Totales", total_cursos)
    kpi3.metric("Cursos Completados", cursos_completados)
    kpi4.metric("Tasa Finalización", f"{tasa_finalizacion}%")
    kpi5.metric("Puntaje Promedio", puntaje_promedio)

    st.markdown("---")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribución de Puntajes en Evaluaciones")
        fig_hist = px.histogram(tests, x="score", nbins=10, title="Distribución de Notas", color_discrete_sequence=['#2E86C1'])
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.subheader("Estado de Inscripciones")
        fig_pie = px.pie(enrollments, names="is_completed", title="Completados vs En Progreso", 
                         color_discrete_sequence=['#27AE60', '#E74C3C'])
        st.plotly_chart(fig_pie, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos. Asegúrate de haber ejecutado Ansible primero: {e}")
