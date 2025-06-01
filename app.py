import streamlit as st
import sqlite3
import datetime
from pathlib import Path

# --- Configuración de la Aplicación ---
DB_PATH = Path(__file__).parent / "asistencia.db"
APP_TITLE = "Registro de Asistencia IPES"
STUDENTS_SETUP = {
    'sofia_sarachaga': {'nombre': 'Sofia Sarachaga'},
    'lailen_flores': {'nombre': 'Lailen Flores'},
    'gabriel_rios': {'nombre': 'Gabriel Rios'},
    'tahirah_husagh': {'nombre': 'Tahirah Husagh'},
    'josue_soler': {'nombre': 'Josue Soler'},
    'nehuen_cerdan': {'nombre': 'Nehuen Cerdan'},
}

# --- Funciones de Base de Datos ---
def init_db():
    """Inicializa la base de datos y las tablas si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabla de estudiantes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            student_id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL
        )
    """)
    # Tabla de asistencias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            fecha TEXT NOT NULL, -- YYYY-MM-DD
            estado TEXT, -- Presente, Ausente, Tarde
            causa TEXT,
            justificada INTEGER, -- 0 para No, 1 para Sí
            UNIQUE(student_id, fecha),
            FOREIGN KEY (student_id) REFERENCES estudiantes (student_id)
        )
    """)
    # Insertar/Actualizar estudiantes desde la configuración
    for student_id, data in STUDENTS_SETUP.items():
        cursor.execute("""
            INSERT INTO estudiantes (student_id, nombre) VALUES (?, ?)
            ON CONFLICT(student_id) DO UPDATE SET nombre=excluded.nombre
        """, (student_id, data['nombre']))
    conn.commit()
    conn.close()

def get_students():
    """Obtiene todos los estudiantes de la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, nombre FROM estudiantes ORDER BY nombre")
    students = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    conn.close()
    return students

def get_attendance(student_id, date_str):
    """Obtiene la asistencia de un estudiante para una fecha específica."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT estado, causa, justificada FROM asistencias
        WHERE student_id = ? AND fecha = ?
    """, (student_id, date_str))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'estado': row[0], 'causa': row[1], 'justificada': bool(row[2])}
    return {'estado': '', 'causa': '', 'justificada': False}

def update_attendance(student_id, date_str, estado, causa, justificada):
    """Actualiza o inserta un registro de asistencia."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    justificada_int = 1 if justificada else 0
    
    # Si el estado no es 'Ausente', limpiar causa y justificada
    if estado != 'Ausente':
        causa = ''
        justificada_int = 0

    cursor.execute("""
        INSERT INTO asistencias (student_id, fecha, estado, causa, justificada)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(student_id, fecha) DO UPDATE SET
            estado=excluded.estado,
            causa=excluded.causa,
            justificada=excluded.justificada
    """, (student_id, date_str, estado, causa, justificada_int))
    conn.commit()
    conn.close()

# --- Funciones de Utilidad de Fechas ---
def get_monday_of_week(date_obj):
    """Devuelve el lunes de la semana de la fecha dada."""
    return date_obj - datetime.timedelta(days=date_obj.weekday())

def get_week_days(monday_date):
    """Devuelve el martes y jueves de la semana dado el lunes."""
    tuesday = monday_date + datetime.timedelta(days=1)
    thursday = monday_date + datetime.timedelta(days=3)
    return tuesday, thursday

# --- Componentes de Streamlit ---
def render_attendance_cell(student_id, date_obj, key_prefix):
    """Renderiza los inputs para una celda de asistencia."""
    date_str = date_obj.strftime("%Y-%m-%d")
    current_attendance = get_attendance(student_id, date_str)

    estado_options = ["", "Presente", "Ausente", "Tarde"]
    estado_actual = current_attendance.get('estado', '')
    
    # Asegurarse que el estado actual esté en las opciones, sino poner vacío
    if estado_actual not in estado_options:
        estado_actual = ""

    estado = st.selectbox(
        "Estado",
        options=estado_options,
        index=estado_options.index(estado_actual), # Usar el índice del estado actual
        key=f"{key_prefix}_estado_{student_id}_{date_str}",
        label_visibility="collapsed"
    )

    causa = current_attendance.get('causa', '')
    justificada = current_attendance.get('justificada', False)

    if estado == 'Ausente':
        causa = st.text_input(
            "Causa",
            value=causa,
            key=f"{key_prefix}_causa_{student_id}_{date_str}",
            placeholder="Causa de inasistencia"
        )
        justificada = st.checkbox(
            "Justificada",
            value=justificada,
            key=f"{key_prefix}_justificada_{student_id}_{date_str}"
        )
    else: # Limpiar visualmente si no es Ausente, aunque la BD se actualiza en save
        causa = ''
        justificada = False
        # No renderizar los campos de causa y justificada

    # Actualizar la base de datos cuando cambie algún valor
    # Esto sucede porque Streamlit re-ejecuta el script en cada interacción
    # y los valores de los widgets son los nuevos
    if (estado != current_attendance.get('estado') or
        (estado == 'Ausente' and (causa != current_attendance.get('causa') or
                                  justificada != current_attendance.get('justificada')))):
        update_attendance(student_id, date_str, estado, causa, justificada)
        # Opcional: st.rerun() para forzar recarga inmediata si hay problemas de UI
        # st.experimental_rerun() # Para versiones anteriores de Streamlit
        # st.rerun() # Para versiones más nuevas

    # Mostrar iconos de estado
    if estado == 'Presente':
        st.markdown(":large_green_circle: Presente")
    elif estado == 'Ausente':
        st.markdown(":red_circle: Ausente")
        if causa:
            st.caption(f"Causa: {causa}")
        st.caption(f"Justificada: {'Sí' if justificada else 'No'}")
    elif estado == 'Tarde':
        st.markdown(":large_yellow_circle: Tarde")
    elif not estado :
        st.caption("Seleccionar estado")


def show_student_detail_dialog(student, week_dates_str):
    """Muestra el diálogo con el detalle de asistencia del estudiante."""
    with st.dialog(f"Detalle de Asistencia: {student['nombre']}", dismissible=True):
        st.subheader(f"Semana del {week_dates_str['tuesday']} al {week_dates_str['thursday']}")
        
        for day_name, date_str in [("Martes", week_dates_str['tuesday']), ("Jueves", week_dates_str['thursday'])]:
            attendance = get_attendance(student['id'], date_str)
            st.markdown(f"--- \n**{day_name} ({datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m')})**")
            
            estado = attendance.get('estado', 'No registrado')
            icon = ""
            if estado == 'Presente': icon = ":large_green_circle:"
            elif estado == 'Ausente': icon = ":red_circle:"
            elif estado == 'Tarde': icon = ":large_yellow_circle:"
            
            st.write(f"Estado: {icon} {estado}")

            if estado == 'Ausente':
                st.write(f"Causa: {attendance.get('causa', 'N/A')}")
                st.write(f"Justificada: {'Sí' if attendance.get('justificada') else 'No'}")
        
        if st.button("Cerrar", key=f"close_detail_{student['id']}"):
            st.session_state.show_detail_dialog = False
            st.rerun()


# --- Aplicación Principal ---
def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()

    st.title(APP_TITLE)
    st.markdown("Prácticas Profesionalizantes IPES - Colegio Técnico Antonio Martín Marte")

    # --- Manejo del estado de la semana ---
    if 'current_monday' not in st.session_state:
        # Martes pasado: 27 de Mayo, 2025. Lunes de esa semana: 26 de Mayo, 2025.
        st.session_state.current_monday = datetime.date(2025, 5, 26)

    # --- Selector de Semana ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Semana Anterior"):
            st.session_state.current_monday -= datetime.timedelta(weeks=1)
            st.rerun()
    with col3:
        if st.button("Semana Siguiente ➡️"):
            st.session_state.current_monday += datetime.timedelta(weeks=1)
            st.rerun()

    current_monday = st.session_state.current_monday
    tuesday_obj, thursday_obj = get_week_days(current_monday)
    
    tuesday_str = tuesday_obj.strftime("%d/%m/%Y")
    thursday_str = thursday_obj.strftime("%d/%m/%Y")

    with col2:
        st.subheader(f"Semana del: {current_monday.strftime('%d/%m/%Y')} al {(current_monday + datetime.timedelta(days=6)).strftime('%d/%m/%Y')}")

    # --- Tabla de Asistencia ---
    students = get_students()
    if not students:
        st.warning("No hay estudiantes registrados. Verifica la configuración inicial.")
        return

    header_cols = st.columns([2, 3, 3, 1]) # Estudiante, Martes, Jueves, Detalle
    header_cols[0].markdown("**Estudiante**")
    header_cols[1].markdown(f"**Martes ({tuesday_obj.strftime('%d/%m')})**")
    header_cols[2].markdown(f"**Jueves ({thursday_obj.strftime('%d/%m')})**")
    header_cols[3].markdown("**Detalle**")
    st.divider()

    for student in students:
        cols = st.columns([2, 3, 3, 1])
        cols[0].markdown(f"##### {student['nombre']}")
        
        with cols[1]:
            render_attendance_cell(student['id'], tuesday_obj, "tue")
        
        with cols[2]:
            render_attendance_cell(student['id'], thursday_obj, "thu")

        with cols[3]:
            if st.button("👁️", key=f"detail_{student['id']}", help="Ver detalle semanal"):
                st.session_state.show_detail_dialog = True
                st.session_state.detail_student_id = student['id']
                st.rerun()
        st.divider()
        
    # --- Lógica del Diálogo de Detalle ---
    if "show_detail_dialog" not in st.session_state:
        st.session_state.show_detail_dialog = False
    if "detail_student_id" not in st.session_state:
        st.session_state.detail_student_id = None

    if st.session_state.show_detail_dialog and st.session_state.detail_student_id:
        selected_student = next((s for s in students if s['id'] == st.session_state.detail_student_id), None)
        if selected_student:
            week_dates_str_for_dialog = {
                'tuesday': tuesday_obj.strftime("%Y-%m-%d"),
                'thursday': thursday_obj.strftime("%Y-%m-%d")
            }
            show_student_detail_dialog(selected_student, week_dates_str_for_dialog)
            
    st.sidebar.info("Los cambios se guardan automáticamente al modificar un campo.")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"ID de Usuario (simulado): `{STUDENTS_SETUP.get('user_simulated_id', 'local_user')}`") # Simulación
    st.sidebar.markdown(f"Base de datos: `{DB_PATH.name}`")


if __name__ == "__main__":
    main()
