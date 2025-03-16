import streamlit as st
import pandas as pd
from src.database import database
from datetime import datetime, timedelta

def actividades_page():
    """Página para gestionar actividades."""
    st.title("Gestión de Actividades")
    
    # Inicializar variables de estado si no existen
    if 'confirmar_eliminacion' not in st.session_state:
        st.session_state.confirmar_eliminacion = False
    if 'actividad_a_eliminar' not in st.session_state:
        st.session_state.actividad_a_eliminar = None
        
    # Función para activar la confirmación
    def solicitar_confirmacion(actividad_id):
        st.session_state.confirmar_eliminacion = True
        st.session_state.actividad_a_eliminar = actividad_id
        
    # Función para cancelar la eliminación
    def cancelar_eliminacion():
        st.session_state.confirmar_eliminacion = False
        st.session_state.actividad_a_eliminar = None
        
    # Función para confirmar la eliminación
    def confirmar_eliminacion():
        conn = database.get_connection()
        actividad_id = st.session_state.actividad_a_eliminar
        result = database.delete_actividad(conn, actividad_id)
        conn.close()
        
        if result:
            st.session_state.confirmar_eliminacion = False
            st.session_state.actividad_a_eliminar = None
            st.success(f"Actividad {actividad_id} eliminada correctamente")
            st.rerun()
        else:
            st.error("Error al eliminar la actividad.")
    
    # Crear pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Ver Actividades", "Añadir Actividad", "Asignar Agentes", "Editar Actividad"])
    
    # Pestaña Ver Actividades
    with tab1:
        st.subheader("Lista de Actividades")
        
        # Obtener actividades con agentes
        conn = database.get_connection()
        actividades = database.select_actividades_con_agentes(conn)
        conn.close()
        
        if not actividades:
            st.warning("No hay actividades registradas")
        else:
            # Crear DataFrame
            df = pd.DataFrame(actividades)
            
            # Ordenar por fecha (ascendente)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.sort_values('fecha')
            
            # Formatear fecha para mostrar
            df['fecha'] = df['fecha'].dt.strftime('%d/%m/%Y')
            
            # Mostrar tabla
            st.dataframe(df)
    
    # Pestaña Añadir Actividad
    with tab2:
        st.subheader("Añadir Nueva Actividad")
        
        # Formulario para añadir actividad
        with st.form("form_add_actividad"):
            # Obtener datos necesarios
            conn = database.get_connection()
            monitores = database.select_monitores(conn)
            cursos = database.select_visible_cursos(conn)
            turnos = database.select_turnos(conn)
            
            # Verificar si hay cursos y monitores
            if not cursos:
                st.warning("No hay cursos visibles registrados. Por favor, añade cursos primero.")
                st.form_submit_button("Añadir Actividad", disabled=True)
            elif not monitores:
                st.warning("No hay monitores registrados. Por favor, añade agentes con rol de monitor primero.")
                st.form_submit_button("Añadir Actividad", disabled=True)
            else:
                # Campos del formulario
                fecha = st.date_input("Fecha", value=datetime.now())
                
                # Opciones de turno
                turno = st.selectbox("Turno", turnos)
                
                # Opciones de curso
                curso_options = [(str(c['id']), c['nombre']) for c in cursos]
                curso_ids = [c[0] for c in curso_options]
                curso_nombres = [c[1] for c in curso_options]
                curso_index = st.selectbox("Curso", range(len(curso_options)), format_func=lambda i: curso_nombres[i] if i < len(curso_nombres) else "")
                
                # Opciones de monitor
                monitor_nips = [m[0] for m in monitores]
                monitor_nombres = [m[1] for m in monitores]
                monitor_index = st.selectbox("Monitor", range(len(monitores)), format_func=lambda i: monitor_nombres[i] if i < len(monitor_nombres) else "")
                
                # Botón para enviar
                submit_button = st.form_submit_button("Añadir Actividad")
                
                if submit_button:
                    if curso_index < len(curso_ids) and monitor_index < len(monitor_nips):
                        # Crear actividad
                        fecha_str = fecha.strftime('%Y-%m-%d')
                        curso_id = int(curso_ids[curso_index])
                        monitor_nip = monitor_nips[monitor_index]
                        
                        # Insertar actividad
                        actividad_id = database.insert_actividad(conn, (fecha_str, turno, monitor_nip, curso_id))
                        conn.close()
                        
                        if actividad_id:
                            st.success(f"Actividad añadida con éxito para el curso '{curso_nombres[curso_index]}' el día {fecha_str}")
                            st.rerun()
                        else:
                            st.error("Error al añadir la actividad. Es posible que ya exista una actividad para este curso, fecha y turno.")
    
    # Pestaña Asignar Agentes
    with tab3:
        st.subheader("Asignar Agentes a Actividades")
        
        # Obtener actividades
        conn = database.get_connection()
        actividades = database.select_actividades_ordenadas_por_fecha(conn)
        
        if not actividades:
            st.warning("No hay actividades registradas. Por favor, añade actividades primero.")
        else:
            # Crear opciones para el selectbox
            actividad_options = [(str(a['id']), f"{a['curso_nombre']} - {a['fecha']} ({a['turno']})") for a in actividades]
            actividad_ids = [int(a[0]) for a in actividad_options]
            actividad_nombres = [a[1] for a in actividad_options]
            
            # Seleccionar actividad
            actividad_index = st.selectbox("Seleccionar Actividad", range(len(actividad_options)), 
                                          format_func=lambda i: actividad_nombres[i] if i < len(actividad_nombres) else "")
            
            if actividad_index < len(actividad_ids):
                actividad_id = actividad_ids[actividad_index]
                
                # Obtener agentes
                agentes = database.select_all_agentes(conn)
                
                if not agentes:
                    st.warning("No hay agentes registrados. Por favor, añade agentes primero.")
                else:
                    # Filtrar solo agentes activos
                    agentes_activos = [a for a in agentes if a['activo']]
                    
                    if not agentes_activos:
                        st.warning("No hay agentes activos disponibles.")
                    else:
                        # Crear opciones para el selectbox
                        agente_options = [(a['nip'], f"{a['nombre']} {a['apellido1']}") for a in agentes_activos]
                        agente_nips = [a[0] for a in agente_options]
                        agente_nombres = [a[1] for a in agente_options]
                        
                        # Seleccionar agente
                        agente_index = st.selectbox("Seleccionar Agente", range(len(agente_options)), 
                                                    format_func=lambda i: agente_nombres[i] if i < len(agente_nombres) else "")
                        
                        if agente_index < len(agente_nips):
                            agente_nip = agente_nips[agente_index]
                            
                            # Botón para asignar
                            if st.button("Asignar Agente a Actividad"):
                                # Asignar agente a actividad
                                result = database.insert_agente_actividad(conn, actividad_id, agente_nip)
                                
                                if result:
                                    st.success(f"Agente {agente_nombres[agente_index]} asignado con éxito a la actividad")
                                    st.rerun()
                                else:
                                    st.error("Error al asignar el agente. Es posible que ya esté asignado a esta actividad.")
        
        conn.close()

    # Pestaña Editar Actividad
    with tab4:
        st.subheader("Editar Actividad")
        
        # Obtener datos necesarios
        conn = database.get_connection()
        actividades = database.select_actividades_ordenadas_por_fecha(conn)
        monitores = database.select_monitores(conn)
        cursos = database.select_visible_cursos(conn)
        turnos = database.select_turnos(conn)
        
        if not actividades:
            st.warning("No hay actividades registradas para editar")
        else:
            # Crear opciones para el selectbox
            actividad_options = [(str(a['id']), f"{a['curso_nombre']} - {a['fecha']} - {a['turno']}") for a in actividades]
            actividad_ids = [a[0] for a in actividad_options]
            actividad_nombres = [a[1] for a in actividad_options]
            
            # Seleccionar actividad
            actividad_index = st.selectbox("Seleccionar Actividad", range(len(actividad_options)), 
                                          format_func=lambda i: actividad_nombres[i] if i < len(actividad_nombres) else "")
            
            if actividad_index < len(actividad_ids):
                actividad_id = int(actividad_ids[actividad_index])
                actividad = next((a for a in actividades if a['id'] == actividad_id), None)
                
                if actividad:
                    # Formulario para editar actividad
                    with st.form(key="editar_actividad_form"):
                        # Mostrar datos actuales
                        st.write(f"Editando: {actividad['curso_nombre']} - {actividad['fecha']} - {actividad['turno']}")
                        
                        # Campos para editar
                        fecha_actual = datetime.strptime(actividad['fecha'], '%Y-%m-%d')
                        fecha = st.date_input("Fecha", value=fecha_actual)
                        fecha_str = fecha.strftime('%Y-%m-%d')
                        
                        # Opciones de turno
                        turno_index = turnos.index(actividad['turno']) if actividad['turno'] in turnos else 0
                        turno = st.selectbox("Turno", turnos, index=turno_index)
                        
                        # Opciones de curso
                        curso_ids = [str(c['id']) for c in cursos]
                        curso_nombres = [c['nombre'] for c in cursos]
                        
                        # Encontrar el índice del curso actual
                        try:
                            curso_index = next((i for i, c in enumerate(cursos) if c['id'] == actividad['curso_id']), 0)
                        except:
                            curso_index = 0
                        
                        curso_seleccionado = st.selectbox("Curso", range(len(curso_ids)), 
                                                        format_func=lambda i: curso_nombres[i] if i < len(curso_nombres) else "",
                                                        index=curso_index)
                        
                        if curso_seleccionado < len(curso_ids):
                            curso_id = int(curso_ids[curso_seleccionado])
                            
                            # Opciones de monitor
                            monitor_nips = [m[0] for m in monitores]
                            monitor_nombres = [m[1] for m in monitores]
                            
                            # Encontrar el índice del monitor actual
                            try:
                                monitor_index = monitor_nips.index(actividad['monitor_nip'])
                            except:
                                monitor_index = 0
                            
                            monitor_seleccionado = st.selectbox("Monitor", range(len(monitor_nips)), 
                                                              format_func=lambda i: monitor_nombres[i] if i < len(monitor_nombres) else "",
                                                              index=monitor_index)
                            
                            if monitor_seleccionado < len(monitor_nips):
                                monitor_nip = monitor_nips[monitor_seleccionado]
                                
                                # Campo para notas
                                notas = st.text_area("Notas", value=actividad.get('notas', ''))
                                
                                # Botón de envío del formulario
                                submit_button = st.form_submit_button("Actualizar Actividad")
                                
                                if submit_button:
                                    # Crear objeto actividad actualizada
                                    actividad_actualizada = {
                                        'fecha': fecha,
                                        'turno': turno,
                                        'monitor_nip': monitor_nip,
                                        'curso_id': curso_id,
                                        'notas': notas
                                    }
                                    
                                    # Actualizar actividad
                                    result = database.update_actividad(conn, actividad_id, actividad_actualizada)
                                    
                                    if result:
                                        st.success(f"Actividad {actividad_id} actualizada correctamente")
                                    else:
                                        st.error("Error al actualizar la actividad. Verifica que no exista otra actividad con la misma fecha, turno y curso.")
                    
                    # Botón para eliminar (fuera del formulario)
                    if st.button("Eliminar Actividad", key="eliminar_actividad", type="primary", help="Eliminar esta actividad permanentemente", on_click=solicitar_confirmacion, args=(actividad_id,)):
                        pass  # La acción se maneja en el callback
                    
                    # Mostrar confirmación si está activada
                    if st.session_state.confirmar_eliminacion and st.session_state.actividad_a_eliminar == actividad_id:
                        st.warning("¿Estás seguro de que deseas eliminar esta actividad? Esta acción no se puede deshacer.")
                        
                        # Botones de confirmación
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            st.button("Sí, eliminar", key="confirmar_eliminar", on_click=confirmar_eliminacion)
                        
                        with col_confirm2:
                            st.button("Cancelar", key="cancelar_eliminar", on_click=cancelar_eliminacion)
    
    conn.close()
actividades_page()
