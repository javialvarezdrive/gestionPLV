import streamlit as st
import pandas as pd
from src.database import database

def cursos_page():
    # Mensaje de éxito global
    if 'curso_success_message' in st.session_state:
        st.success(st.session_state.curso_success_message)
        # Limpiar el mensaje después de mostrarlo
        del st.session_state.curso_success_message
    
    # Crear dos columnas
    col1, col2 = st.columns([2, 1])
    
    # Obtener cursos
    conn = database.get_connection()
    cursos = database.select_all_cursos(conn)
    
    # Columna 1: Lista de Cursos
    with col1:
        st.subheader("Lista de Cursos")
        
        if not cursos:
            st.warning("No hay cursos registrados")
        else:
            # Crear DataFrame
            df = pd.DataFrame(cursos)
            
            # Eliminar columna ID para mostrar
            df_display = df[['nombre']]
            
            # Añadir columna de estado
            df_display['estado'] = df['visible'].apply(lambda x: "✅ Visible" if x else "❌ Oculto")
            
            # Mostrar tabla
            st.dataframe(df_display)
    
    # Columna 2: Añadir Curso y Acciones (Ocultar/Eliminar)
    with col2:
        # Añadir Curso
        st.subheader("Añadir Curso")
        
        # Formulario para añadir curso
        with st.form("form_add_curso"):
            # Campo para el nombre del curso
            nombre = st.text_input("Nombre del Curso")
            
            # Botón para enviar
            submit_button = st.form_submit_button("Añadir Curso")
            
            if submit_button:
                if nombre:
                    # Crear curso
                    curso = {
                        'nombre': nombre,
                        'visible': True
                    }
                    
                    # Insertar curso
                    result = database.insert_curso(conn, curso)
                    
                    if result:
                        st.session_state.curso_success_message = f"✅ Curso '{nombre}' añadido con éxito"
                        st.rerun()
                    else:
                        st.error("Error al añadir el curso. Es posible que ya exista un curso con ese nombre.")
                else:
                    st.error("Por favor, ingresa un nombre para el curso")
        
        # Acciones (Ocultar/Eliminar)
        st.subheader("Acciones")
        
        if cursos:
            # Crear opciones para el selectbox
            curso_options = [(str(c['id']), c['nombre']) for c in cursos]
            curso_ids = [c[0] for c in curso_options]
            curso_nombres = [c[1] for c in curso_options]
            
            # Seleccionar curso
            curso_index = st.selectbox("Seleccionar Curso", range(len(curso_options)), 
                                      format_func=lambda i: curso_nombres[i] if i < len(curso_nombres) else "")
            
            if curso_index < len(curso_ids):
                curso_id = int(curso_ids[curso_index])
                curso_seleccionado = next((c for c in cursos if c['id'] == curso_id), None)
                
                if curso_seleccionado:
                    # Mostrar estado actual
                    estado_actual = "Visible" if curso_seleccionado['visible'] else "Oculto"
                    st.info(f"Estado actual: {estado_actual}")
                    
                    # Botón para cambiar visibilidad
                    nuevo_estado = not curso_seleccionado['visible']
                    accion = "Mostrar" if nuevo_estado else "Ocultar"
                    if st.button(f"{accion} Curso"):
                        result = database.toggle_curso_visibility(conn, curso_id, nuevo_estado)
                        if result:
                            st.session_state.curso_success_message = f"✅ Curso '{curso_seleccionado['nombre']}' ahora está {'visible' if nuevo_estado else 'oculto'}"
                            st.rerun()
                        else:
                            st.error(f"Error al {accion.lower()} el curso")
                    
                    # Botón para eliminar curso
                    st.write("---")
                    if st.button("Eliminar Curso"):
                        # Verificar si tiene actividades antes de eliminar
                        result = database.delete_curso(conn, curso_id)
                        if result:
                            st.session_state.curso_success_message = f"🗑️ Curso '{curso_seleccionado['nombre']}' eliminado con éxito"
                            st.rerun()
                        else:
                            st.error("No se puede eliminar el curso porque tiene actividades programadas")
    
    conn.close()
