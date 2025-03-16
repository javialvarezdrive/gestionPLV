import streamlit as st
import pandas as pd
from src.database import database

def agentes_page():
    # Crear pestañas
    tab1, tab2, tab3 = st.tabs(["Ver Agentes", "Añadir Agente", "Editar Agente"])
    
    # Mensaje de éxito global (fuera de las pestañas)
    if 'agente_success_message' in st.session_state:
        st.success(st.session_state.agente_success_message)
        # Limpiar el mensaje después de mostrarlo
        del st.session_state.agente_success_message
    
    # Pestaña Ver Agentes
    with tab1:
        st.subheader("Lista de Agentes")
        
        # Obtener agentes
        conn = database.get_connection()
        agentes = database.select_all_agentes(conn)
        conn.close()
        
        if not agentes:
            st.warning("No hay agentes registrados")
        else:
            # Crear DataFrame
            df = pd.DataFrame(agentes)
            
            # Convertir columnas booleanas a texto para mejor visualización
            df['monitor'] = df['monitor'].apply(lambda x: "✅" if x else "❌")
            df['activo'] = df['activo'].apply(lambda x: "✅" if x else "❌")
            
            # Mostrar tabla
            st.dataframe(df)
    
    # Pestaña Añadir Agente
    with tab2:
        st.subheader("Añadir Nuevo Agente")
        
        # Formulario para añadir agente
        with st.form("form_add_agente"):
            # Campos del formulario
            nip = st.text_input("NIP")
            nombre = st.text_input("Nombre")
            apellido1 = st.text_input("Primer Apellido")
            apellido2 = st.text_input("Segundo Apellido")
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            seccion = st.text_input("Sección")
            grupo = st.text_input("Grupo")
            es_monitor = st.checkbox("¿Es monitor?")
            activo = st.checkbox("¿Está activo?", value=True)
            
            # Botón para enviar
            submit_button = st.form_submit_button("Añadir Agente")
            
            if submit_button:
                if nip and nombre and apellido1:
                    # Crear agente
                    agente = {
                        'nip': str(nip),  # Convertir a string para evitar problemas de tipo
                        'nombre': nombre,
                        'apellido1': apellido1,
                        'apellido2': apellido2,
                        'email': email,
                        'telefono': telefono,
                        'seccion': seccion,
                        'grupo': grupo,
                        'monitor': es_monitor,
                        'activo': activo
                    }
                    
                    # Insertar agente
                    conn = database.get_connection()
                    result = database.insert_agente(conn, agente)
                    conn.close()
                    
                    if result:
                        # Guardar mensaje de éxito en session_state para mostrarlo después de rerun
                        st.session_state.agente_success_message = f"✅ Agente {nombre} {apellido1} (NIP: {nip}) añadido con éxito. El agente ha sido registrado en la base de datos y está disponible para ser asignado a actividades."
                        st.rerun()
                    else:
                        st.error("Error al añadir el agente. Es posible que el NIP ya exista.")
                else:
                    st.error("Por favor, completa los campos obligatorios (NIP, Nombre y Primer Apellido)")
    
    # Pestaña Editar Agente
    with tab3:
        st.subheader("Editar Agente")
        
        # Obtener agentes
        conn = database.get_connection()
        agentes = database.select_all_agentes(conn)
        
        if not agentes:
            st.warning("No hay agentes para editar")
        else:
            # Crear opciones para el selectbox
            agente_options = [(a['nip'], f"{a['nombre']} {a['apellido1']}") for a in agentes]
            agente_nips = [str(a[0]) for a in agente_options]  # Asegurar que son strings
            agente_nombres = [a[1] for a in agente_options]
            
            # Seleccionar agente
            agente_index = st.selectbox("Seleccionar Agente", range(len(agente_options)), format_func=lambda i: agente_nombres[i] if i < len(agente_nombres) else "")
            
            if agente_index < len(agente_nips):
                agente_nip = agente_nips[agente_index]
                
                # Obtener datos del agente seleccionado
                agente_seleccionado = next((a for a in agentes if a['nip'] == agente_nip), None)
                
                if agente_seleccionado:
                    # Formulario para editar agente
                    with st.form("form_edit_agente"):
                        # Campos del formulario
                        nombre = st.text_input("Nombre", value=agente_seleccionado['nombre'])
                        apellido1 = st.text_input("Primer Apellido", value=agente_seleccionado['apellido1'])
                        apellido2 = st.text_input("Segundo Apellido", value=agente_seleccionado['apellido2'] or "")
                        email = st.text_input("Email", value=agente_seleccionado['email'] or "")
                        telefono = st.text_input("Teléfono", value=agente_seleccionado['telefono'] or "")
                        seccion = st.text_input("Sección", value=agente_seleccionado['seccion'] or "")
                        grupo = st.text_input("Grupo", value=agente_seleccionado['grupo'] or "")
                        es_monitor = st.checkbox("¿Es monitor?", value=agente_seleccionado['monitor'])
                        activo = st.checkbox("¿Está activo?", value=agente_seleccionado['activo'])
                        
                        # Botón para enviar
                        submit_button = st.form_submit_button("Actualizar Agente")
                        
                        if submit_button:
                            if nombre and apellido1:
                                # Crear agente actualizado
                                agente_actualizado = {
                                    'nombre': nombre,
                                    'apellido1': apellido1,
                                    'apellido2': apellido2,
                                    'email': email,
                                    'telefono': telefono,
                                    'seccion': seccion,
                                    'grupo': grupo,
                                    'monitor': es_monitor,
                                    'activo': activo
                                }
                                
                                # Actualizar agente
                                result = database.update_agente(conn, agente_nip, agente_actualizado)
                                
                                if result:
                                    # Guardar mensaje de éxito en session_state para mostrarlo después de rerun
                                    monitor_status = "activado" if es_monitor else "desactivado"
                                    activo_status = "activo" if activo else "inactivo"
                                    st.session_state.agente_success_message = f"✅ Agente {nombre} {apellido1} (NIP: {agente_nip}) actualizado con éxito. Estado: {activo_status}, Monitor: {monitor_status}."
                                    st.rerun()
                                else:
                                    st.error("Error al actualizar el agente")
                            else:
                                st.error("Por favor, completa los campos obligatorios (Nombre y Primer Apellido)")
                    
                    # Botón para eliminar agente
                    if st.button("Eliminar Agente"):
                        # Confirmar eliminación
                        if st.checkbox("¿Estás seguro de que deseas eliminar este agente?"):
                            # Eliminar agente
                            result = database.delete_agente(conn, agente_nip)
                            
                            if result:
                                # Guardar mensaje de éxito en session_state para mostrarlo después de rerun
                                st.session_state.agente_success_message = f"🗑️ Agente {agente_seleccionado['nombre']} {agente_seleccionado['apellido1']} (NIP: {agente_nip}) eliminado con éxito."
                                st.rerun()
                            else:
                                st.error("No se puede eliminar el agente porque está asignado a actividades")
        
        conn.close()
