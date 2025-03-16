import sqlite3
import os
import pandas as pd
from datetime import datetime

def get_connection():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    return conn

def init_database():
    """Inicializa la base de datos con las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de agentes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agentes (
        nip TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido1 TEXT NOT NULL,
        apellido2 TEXT,
        email TEXT,
        telefono TEXT,
        seccion TEXT,
        grupo TEXT,
        monitor INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1,
        fecha_incorporacion TEXT
    )
    ''')
    
    # Tabla de cursos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        visible INTEGER DEFAULT 1
    )
    ''')
    
    # Tabla de turnos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turnos (
        nombre TEXT PRIMARY KEY
    )
    ''')
    
    # Tabla de actividades
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actividades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        turno TEXT NOT NULL,
        monitor_nip TEXT NOT NULL,
        curso_id INTEGER NOT NULL,
        curso_nombre TEXT NOT NULL,
        monitor_nombre TEXT NOT NULL,
        notas TEXT,
        FOREIGN KEY (monitor_nip) REFERENCES agentes (nip),
        FOREIGN KEY (curso_id) REFERENCES cursos (id),
        FOREIGN KEY (turno) REFERENCES turnos (nombre)
    )
    ''')
    
    # Tabla de relación agentes-actividades
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agentes_actividades (
        actividad_id INTEGER NOT NULL,
        agente_nip TEXT NOT NULL,
        PRIMARY KEY (actividad_id, agente_nip),
        FOREIGN KEY (actividad_id) REFERENCES actividades (id),
        FOREIGN KEY (agente_nip) REFERENCES agentes (nip)
    )
    ''')
    
    # Insertar turnos predeterminados
    turnos_default = [
        ('Mañana',),
        ('Tarde',),
        ('Noche',)
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO turnos (nombre) VALUES (?)', turnos_default)
    
    conn.commit()
    conn.close()

# Funciones para agentes
def select_all_agentes(conn=None):
    """Selecciona todos los agentes de la base de datos."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    cursor.execute('''
    SELECT nip, nombre, apellido1, apellido2, email, telefono, seccion, grupo, monitor, activo, fecha_incorporacion
    FROM agentes
    ORDER BY apellido1, nombre
    ''')
    agentes = cursor.fetchall()
    
    # Convertir a lista de diccionarios
    result = []
    for agente in agentes:
        result.append({
            'nip': str(agente['nip']),  # Convertir a string para evitar problemas de tipo
            'nombre': agente['nombre'],
            'apellido1': agente['apellido1'],
            'apellido2': agente['apellido2'],
            'email': agente['email'],
            'telefono': agente['telefono'],
            'seccion': agente['seccion'],
            'grupo': agente['grupo'],
            'monitor': bool(agente['monitor']),
            'activo': bool(agente['activo']),
            'fecha_incorporacion': agente['fecha_incorporacion']
        })
    
    if close_conn:
        conn.close()
    
    return result

def select_monitores(conn=None):
    """Selecciona los agentes que son monitores."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    cursor.execute('''
    SELECT nip, nombre, apellido1
    FROM agentes
    WHERE monitor = 1 AND activo = 1
    ORDER BY apellido1, nombre
    ''')
    monitores = cursor.fetchall()
    
    # Convertir a lista de tuplas (nip, nombre_completo)
    result = []
    for monitor in monitores:
        result.append((
            str(monitor['nip']),  # Convertir a string para evitar problemas de tipo
            f"{monitor['nombre']} {monitor['apellido1']}"
        ))
    
    if close_conn:
        conn.close()
    
    return result

def insert_agente(conn, agente):
    """Inserta un nuevo agente en la base de datos."""
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO agentes (nip, nombre, apellido1, apellido2, email, telefono, seccion, grupo, monitor, activo, fecha_incorporacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            agente['nip'],
            agente['nombre'],
            agente['apellido1'],
            agente['apellido2'],
            agente['email'],
            agente['telefono'],
            agente['seccion'],
            agente['grupo'],
            1 if agente['monitor'] else 0,
            1 if agente['activo'] else 0,
            agente.get('fecha_incorporacion', datetime.now().strftime('%Y-%m-%d'))
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # NIP duplicado
        return False

def update_agente(conn, nip, agente):
    """Actualiza un agente existente en la base de datos."""
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE agentes
        SET nombre=?, apellido1=?, apellido2=?, email=?, telefono=?, seccion=?, grupo=?, monitor=?, activo=?
        WHERE nip=?
        ''', (
            agente['nombre'],
            agente['apellido1'],
            agente['apellido2'],
            agente['email'],
            agente['telefono'],
            agente['seccion'],
            agente['grupo'],
            1 if agente['monitor'] else 0,
            1 if agente['activo'] else 0,
            nip
        ))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        return False

def delete_agente(conn, nip):
    """Elimina un agente de la base de datos si no tiene actividades asociadas."""
    cursor = conn.cursor()
    
    # Verificar si el agente es monitor en alguna actividad
    cursor.execute('SELECT COUNT(*) FROM actividades WHERE monitor_nip=?', (nip,))
    count_monitor = cursor.fetchone()[0]
    
    # Verificar si el agente está asignado a alguna actividad
    cursor.execute('SELECT COUNT(*) FROM agentes_actividades WHERE agente_nip=?', (nip,))
    count_actividades = cursor.fetchone()[0]
    
    if count_monitor > 0 or count_actividades > 0:
        return False  # No se puede eliminar porque tiene actividades asociadas
    
    cursor.execute('DELETE FROM agentes WHERE nip=?', (nip,))
    conn.commit()
    return cursor.rowcount > 0

# Funciones para cursos
def select_all_cursos(conn=None):
    """Selecciona todos los cursos de la base de datos."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    
    # Verificar si la columna 'visible' existe
    cursor.execute("PRAGMA table_info(cursos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'visible' in columns:
        cursor.execute('SELECT id, nombre, visible FROM cursos ORDER BY nombre')
        cursos = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        result = []
        for curso in cursos:
            result.append({
                'id': int(curso['id']),  # Convertir a int estándar
                'nombre': curso['nombre'],
                'visible': bool(curso['visible'])
            })
    else:
        # Si la columna no existe, usar la estructura antigua
        cursor.execute('SELECT id, nombre FROM cursos ORDER BY nombre')
        cursos = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        result = []
        for curso in cursos:
            result.append({
                'id': int(curso['id']),  # Convertir a int estándar
                'nombre': curso['nombre'],
                'visible': True  # Por defecto, todos los cursos son visibles
            })
    
    if close_conn:
        conn.close()
    return result

def insert_curso(conn, curso):
    """Inserta un nuevo curso en la base de datos."""
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO cursos (nombre, visible) VALUES (?, ?)', 
                      (curso['nombre'], 1 if curso.get('visible', True) else 0))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Error de integridad (nombre duplicado)
        return None

def update_curso(conn, curso_id, curso):
    """Actualiza un curso existente en la base de datos."""
    cursor = conn.cursor()
    cursor.execute('UPDATE cursos SET nombre=? WHERE id=?', (curso['nombre'], curso_id))
    conn.commit()
    return cursor.rowcount > 0

def delete_curso(conn, curso_id):
    """Elimina un curso de la base de datos."""
    # Verificar si el curso tiene actividades
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM actividades WHERE curso_id = ?', (curso_id,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        return False  # No se puede eliminar si tiene actividades
    
    cursor.execute('DELETE FROM cursos WHERE id=?', (curso_id,))
    conn.commit()
    return cursor.rowcount > 0

def toggle_curso_visibility(conn, curso_id, visible):
    """Cambia la visibilidad de un curso."""
    # Verificar si la columna 'visible' existe
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(cursos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'visible' not in columns:
        # Añadir columna 'visible' si no existe
        update_database_structure(conn)
    
    cursor.execute('UPDATE cursos SET visible=? WHERE id=?', (1 if visible else 0, curso_id))
    conn.commit()
    return cursor.rowcount > 0

def select_visible_cursos(conn):
    """Selecciona solo los cursos visibles de la base de datos."""
    cursor = conn.cursor()
    
    # Verificar si la columna 'visible' existe
    cursor.execute("PRAGMA table_info(cursos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'visible' in columns:
        cursor.execute('SELECT id, nombre FROM cursos WHERE visible = 1 ORDER BY nombre')
    else:
        # Si la columna no existe, seleccionar todos los cursos
        cursor.execute('SELECT id, nombre FROM cursos ORDER BY nombre')
    
    cursos = cursor.fetchall()
    
    # Convertir a lista de diccionarios
    result = []
    for curso in cursos:
        result.append({
            'id': int(curso['id']),  # Convertir a int estándar
            'nombre': curso['nombre']
        })
    
    return result

def update_database_structure(conn):
    """Actualiza la estructura de la base de datos para añadir nuevas columnas."""
    cursor = conn.cursor()
    
    # Verificar si la columna 'visible' existe en la tabla cursos
    cursor.execute("PRAGMA table_info(cursos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'visible' not in columns:
        # Añadir columna 'visible' a la tabla cursos
        cursor.execute('ALTER TABLE cursos ADD COLUMN visible BOOLEAN DEFAULT 1')
        conn.commit()
        print("Columna 'visible' añadida a la tabla cursos")
    
    return True

# Funciones para turnos
def select_turnos(conn=None):
    """Selecciona todos los turnos de la base de datos."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    cursor.execute('SELECT nombre FROM turnos ORDER BY nombre')
    turnos = cursor.fetchall()
    
    # Convertir a lista de strings
    result = [turno['nombre'] for turno in turnos]
    
    if close_conn:
        conn.close()
    
    return result

# Funciones para actividades
def select_all_actividades(conn=None):
    """Selecciona todas las actividades de la base de datos."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, fecha, turno, monitor_nip, curso_id, curso_nombre, monitor_nombre, notas
    FROM actividades
    ORDER BY fecha, turno
    ''')
    actividades = cursor.fetchall()
    
    # Convertir a lista de diccionarios
    result = []
    for actividad in actividades:
        result.append({
            'id': int(actividad['id']),  # Convertir a int estándar
            'fecha': actividad['fecha'],
            'turno': actividad['turno'],
            'monitor_nip': str(actividad['monitor_nip']),  # Convertir a string
            'curso_id': int(actividad['curso_id']),  # Convertir a int estándar
            'curso_nombre': actividad['curso_nombre'],
            'monitor_nombre': actividad['monitor_nombre'],
            'notas': actividad['notas']
        })
    
    if close_conn:
        conn.close()
    
    return result

def select_actividades(conn=None):
    """Selecciona todas las actividades de la base de datos."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, a.fecha, a.turno, a.monitor_nip, a.curso_id, a.curso_nombre, a.monitor_nombre, a.notas
        FROM actividades a
        ORDER BY a.id
    ''')
    actividades = cursor.fetchall()
    
    # Convertir a lista de diccionarios
    result = []
    for actividad in actividades:
        result.append({
            'id': int(actividad['id']),  # Convertir a int estándar
            'fecha': actividad['fecha'],
            'turno': actividad['turno'],
            'monitor_nip': actividad['monitor_nip'],
            'curso_id': int(actividad['curso_id']),  # Convertir a int estándar
            'curso_nombre': actividad['curso_nombre'],
            'monitor_nombre': actividad['monitor_nombre'],
            'notas': actividad['notas']
        })
    
    if close_conn:
        conn.close()
    return result

def select_actividades_ordenadas_por_fecha(conn=None):
    """Selecciona todas las actividades de la base de datos ordenadas por fecha en orden ascendente."""
    # Primero obtenemos las actividades normalmente
    actividades = select_actividades(conn)
    
    # Luego las ordenamos por fecha
    actividades.sort(key=lambda x: x['fecha'])
    
    return actividades

def insert_actividad(conn, actividad):
    """Inserta una nueva actividad en la base de datos."""
    fecha_str, turno_str, monitor_nip_str, curso_id_int = actividad
    
    cursor = conn.cursor()
    
    # Verificar si la actividad ya existe
    cursor.execute('''
    SELECT COUNT(*) FROM actividades 
    WHERE fecha=? AND turno=? AND curso_id=?
    ''', (fecha_str, turno_str, curso_id_int))
    count = cursor.fetchone()[0]
    
    if count > 0:
        return None  # La actividad ya existe
    
    # Obtener nombre del curso
    cursor.execute('SELECT nombre FROM cursos WHERE id=?', (curso_id_int,))
    curso = cursor.fetchone()
    if not curso:
        return None  # El curso no existe
    curso_nombre = curso['nombre']
    
    # Obtener nombre del monitor
    cursor.execute('SELECT nombre, apellido1 FROM agentes WHERE nip=?', (monitor_nip_str,))
    monitor = cursor.fetchone()
    if not monitor:
        return None  # El monitor no existe
    monitor_nombre = f"{monitor['nombre']} {monitor['apellido1']}"
    
    try:
        cursor.execute('''
        INSERT INTO actividades (fecha, turno, monitor_nip, curso_id, curso_nombre, monitor_nombre, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            fecha_str,
            turno_str,
            monitor_nip_str,
            curso_id_int,
            curso_nombre,
            monitor_nombre,
            ''
        ))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        return None

def select_actividades_con_agentes(conn=None):
    """Selecciona todas las actividades con sus agentes asignados."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    cursor = conn.cursor()
    
    # Obtener todas las actividades
    actividades = select_all_actividades(conn)
    
    # Para cada actividad, obtener los agentes asignados
    result = []
    for actividad in actividades:
        actividad_id = actividad['id']
        
        # Obtener agentes asignados a esta actividad
        cursor.execute('''
        SELECT aa.agente_nip, a.nombre, a.apellido1
        FROM agentes_actividades aa
        JOIN agentes a ON aa.agente_nip = a.nip
        WHERE aa.actividad_id = ?
        ''', (actividad_id,))
        
        agentes = cursor.fetchall()
        agentes_str = '; '.join([f"{a['agente_nip']}, {a['nombre']} {a['apellido1']}" for a in agentes])
        
        # Crear registro para esta actividad
        registro = {
            'id': actividad_id,
            'fecha': actividad['fecha'],
            'turno': actividad['turno'],
            'curso': actividad['curso_nombre'],
            'monitor': actividad['monitor_nombre'],
            'agentes': agentes_str
        }
        
        result.append(registro)
    
    if close_conn:
        conn.close()
    
    return result

def insert_agente_actividad(conn, actividad_id, agente_nip):
    """Asigna un agente a una actividad."""
    cursor = conn.cursor()
    
    try:
        # Verificar si ya existe la asignación
        cursor.execute('''
        SELECT COUNT(*) FROM agentes_actividades
        WHERE actividad_id=? AND agente_nip=?
        ''', (actividad_id, agente_nip))
        count = cursor.fetchone()[0]
        
        if count > 0:
            return False  # La asignación ya existe
        
        cursor.execute('''
        INSERT INTO agentes_actividades (actividad_id, agente_nip)
        VALUES (?, ?)
        ''', (actividad_id, agente_nip))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def update_actividad(conn, actividad_id, actividad_actualizada):
    """Actualiza una actividad existente en la base de datos."""
    cursor = conn.cursor()
    
    try:
        # Obtener información del curso y monitor para los nombres
        cursor.execute('SELECT nombre FROM cursos WHERE id = ?', (actividad_actualizada['curso_id'],))
        curso = cursor.fetchone()
        if not curso:
            return False
        
        cursor.execute('SELECT nombre, apellido1 FROM agentes WHERE nip = ?', (actividad_actualizada['monitor_nip'],))
        monitor = cursor.fetchone()
        if not monitor:
            return False
        
        # Verificar si ya existe otra actividad con la misma fecha, turno y curso (que no sea la que estamos editando)
        cursor.execute('''
            SELECT id FROM actividades 
            WHERE fecha = ? AND turno = ? AND curso_id = ? AND id != ?
        ''', (
            actividad_actualizada['fecha'], 
            actividad_actualizada['turno'], 
            actividad_actualizada['curso_id'],
            actividad_id
        ))
        
        if cursor.fetchone():
            # Ya existe otra actividad con esa fecha, turno y curso
            return False
        
        # Actualizar la actividad
        cursor.execute('''
            UPDATE actividades 
            SET fecha = ?, turno = ?, monitor_nip = ?, curso_id = ?, 
                curso_nombre = ?, monitor_nombre = ?, notas = ?
            WHERE id = ?
        ''', (
            actividad_actualizada['fecha'],
            actividad_actualizada['turno'],
            actividad_actualizada['monitor_nip'],
            actividad_actualizada['curso_id'],
            curso['nombre'],
            f"{monitor['nombre']} {monitor['apellido1']}",
            actividad_actualizada.get('notas', ''),
            actividad_id
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar actividad: {e}")
        conn.rollback()
        return False

def delete_actividad(conn, actividad_id):
    """Elimina una actividad de la base de datos."""
    cursor = conn.cursor()
    
    try:
        # Primero verificamos si hay agentes asignados a esta actividad
        cursor.execute('SELECT COUNT(*) FROM agentes_actividades WHERE actividad_id = ?', (actividad_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Primero eliminamos las asignaciones de agentes a esta actividad
            cursor.execute('DELETE FROM agentes_actividades WHERE actividad_id = ?', (actividad_id,))
        
        # Luego eliminamos la actividad
        cursor.execute('DELETE FROM actividades WHERE id = ?', (actividad_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al eliminar actividad: {e}")
        conn.rollback()
        return False

# Funciones para estadísticas
def get_total_agentes(conn):
    """Obtiene el número total de agentes."""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM agentes WHERE activo=1')
    return cursor.fetchone()[0]

def get_total_monitores(conn):
    """Obtiene el número total de monitores."""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM agentes WHERE monitor=1 AND activo=1')
    return cursor.fetchone()[0]

def get_total_cursos(conn):
    """Obtiene el número total de cursos."""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM cursos')
    return cursor.fetchone()[0]

def get_total_actividades(conn):
    """Obtiene el número total de actividades."""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM actividades')
    return cursor.fetchone()[0]

def get_actividades_por_curso(conn):
    """Obtiene la distribución de actividades por curso."""
    cursor = conn.cursor()
    cursor.execute('''
    SELECT curso_nombre, COUNT(*) as cantidad
    FROM actividades
    GROUP BY curso_nombre
    ORDER BY cantidad DESC
    LIMIT 10
    ''')
    
    result = {}
    for row in cursor.fetchall():
        result[row['curso_nombre']] = row['cantidad']
    
    return result
