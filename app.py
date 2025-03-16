import streamlit as st
import os
import sqlite3
from src.database import database
from src.views import actividades_view, cursos_view, agentes_view

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Cursos y Actividades",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar la base de datos si no existe
if not os.path.exists("database.db"):
    database.init_database()

# Conectar a la base de datos
conn = database.get_connection()

# Actualizar la estructura de la base de datos si es necesario
database.update_database_structure(conn)
conn.close()

# Título principal
st.title("👮 Gestión de Cursos y Actividades")

# Menú de navegación en la barra lateral
st.sidebar.title("Navegación")
menu_options = ["Actividades", "Estadísticas", "Cursos", "Agentes"]
selected_option = st.sidebar.radio("Selecciona una sección:", menu_options)

# Mostrar la vista correspondiente según la opción seleccionada
if selected_option == "Actividades":
    actividades_view.actividades_page()
elif selected_option == "Estadísticas":
    st.header("Estadísticas")
    
    # Obtener estadísticas
    conn = database.get_connection()
    total_agentes = database.get_total_agentes(conn)
    total_monitores = database.get_total_monitores(conn)
    total_cursos = database.get_total_cursos(conn)
    total_actividades = database.get_total_actividades(conn)
    
    # Mostrar estadísticas en columnas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Agentes", total_agentes)
    with col2:
        st.metric("Total de Monitores", total_monitores)
    with col3:
        st.metric("Total de Cursos", total_cursos)
    with col4:
        st.metric("Total de Actividades", total_actividades)
    
    # Mostrar gráficos de distribución de actividades por curso
    st.subheader("Distribución de Actividades por Curso")
    actividades_por_curso = database.get_actividades_por_curso(conn)
    conn.close()
    
    if actividades_por_curso:
        st.bar_chart(actividades_por_curso)
    else:
        st.info("No hay datos suficientes para mostrar estadísticas.")
elif selected_option == "Cursos":
    cursos_view.cursos_page()
elif selected_option == "Agentes":
    agentes_view.agentes_page()
