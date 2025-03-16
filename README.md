# Aplicación de Gestión de Actividades Policiales

Esta aplicación permite gestionar actividades formativas para la Policía Local, incluyendo la asignación de agentes a cursos y actividades.

## Características

- **Gestión de Actividades**: Crear, editar y eliminar actividades formativas
- **Gestión de Cursos**: Administrar los cursos disponibles
- **Gestión de Agentes**: Administrar los agentes y monitores
- **Asignación de Agentes**: Asignar agentes a actividades específicas
- **Visualización de Datos**: Ver las actividades con sus participantes

## Tecnologías

- **Frontend**: Streamlit
- **Backend**: Python
- **Base de Datos**: SQLite

## Instalación

1. Clonar el repositorio:
```
git clone https://github.com/javialvarezdrive/gestionPLV.git
```

2. Instalar dependencias:
```
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```
streamlit run app.py
```

## Estructura del Proyecto

- `app.py`: Punto de entrada de la aplicación
- `src/database/`: Módulos para interactuar con la base de datos
- `src/views/`: Interfaces de usuario para las diferentes secciones
- `data/`: Archivos de base de datos

## Licencia

Este proyecto es propiedad de la Policía Local de Vigo.
