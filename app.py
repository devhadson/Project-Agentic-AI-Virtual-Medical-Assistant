# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Tuple, List
from dotenv import load_dotenv

# Componentes Core de LangChain & OpenAI
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

# ==========================================
# CONFIGURACIÓN GENERAL Y ENTORNO
# ==========================================
st.set_page_config(page_title="Asistente Virtual Médico IA", layout="wide")

def load_configurations() -> None:
    """Inicializa variables de entorno seguras."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ CRÍTICO: La variable 'OPENAI_API_KEY' no está configurada en el entorno.")
        st.stop()

try:
    load_configurations()
except Exception as e:
    st.error(f"Error de inicialización: {e}")
    st.stop()

# Constantes de Negocio Clínico
HORARIOS_REGLAS = """
REGLAS DE HORARIOS DISPONIBLES:
- Lunes a Viernes: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00
- Sábado: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00
- Domingo: 09:00, 11:00, 13:00, 15:00, 17:00
"""

REGLAS_LABORATORIO_MD = """
### 📋 ORDEN DE LABORATORIO: REQUISITOS DE PREPARACIÓN
* **Glucosa Basal:** Requiere un ayuno estricto de 8 a 10 horas. No consuma alimentos ni bebidas (salvo agua pura).
* **Hemoglobina Glicosilada (HbA1c):** No necesita ayuno. Refleja el promedio de azúcar de los últimos 3 meses.
* **Examen de Orina y Perfil Lipídico:** Requieren estrictamente de 8 a 12 horas de ayuno previo.
"""

# ==========================================
# COMPONENTES DE PERSISTENCIA Y HERRAMIENTAS
# ==========================================
@tool
def save_appointment_to_csv(payload_str: str) -> str:
    """Registra y escribe de forma permanente los detalles de la cita del paciente en el archivo citas.csv."""
    try:
        df_citas = pd.read_csv("content/citas.csv")
        nueva_fila = {
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_id": st.session_state["username"],
            "paciente": st.session_state["display_name"],
            "glucosa": st.session_state.get("glucose_level", 0.0),
            "categoria": st.session_state.get("triage_category", "N/A"),
            "detalle_reserva": payload_str
        }
        df_citas = pd.concat([df_citas, pd.DataFrame([nueva_fila])], ignore_index=True)
        df_citas.to_csv("content/citas.csv", index=False)
        return "SISTEMA: Cita grabada con éxito en el registro histórico médico."
    except Exception as e:
        return f"SISTEMA: Error al escribir en base de datos local: {str(e)}"

@tool
def trigger_doctor_emergency_alert(summary_context: str) -> str:
    """Envía un payload de alerta crítica al sistema de guardia médica informando el estado crítico."""
    try:
        df_citas = pd.read_csv("content/citas.csv")
        nueva_fila = {
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_id": st.session_state["username"],
            "paciente": st.session_state["display_name"],
            "glucosa": st.session_state.get("glucose_level", 0.0),
            "categoria": "EMERGENCIA",
            "detalle_reserva": f"NOTIFICACIÓN MÉDICA DISPARADA: {summary_context}"
        }
        df_citas = pd.concat([df_citas, pd.DataFrame([nueva_fila])], ignore_index=True)
        df_citas.to_csv("content/citas.csv", index=False)
        return "EMERGENCIA: Los datos proporcionados están siendo notificados a tu médico, se recomienda llamar a emergencias."
    except Exception as e:
        return f"SISTEMA: Error en persistencia de emergencia: {str(e)}"

# ==========================================
# CONTROL DE ESTADOS DE SESIÓN (STREAMLIT)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "rol" not in st.session_state:
    st.session_state["rol"] = ""
if "display_name" not in st.session_state:
    st.session_state["display_name"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# CSS personalizado
st.markdown("""
<style>
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INTERFAZ DE AUTENTICACIÓN (LOGIN + IMAGEN)
# ==========================================
if not st.session_state["logged_in"]:
    #st.title("🏥 Asistente Virtual Médico IA - Acceso")

    st.markdown("""
    <div class="welcome-card">
        <h1>🏥 Asistente Virtual Médico IA - Acceso</h1>
        <p>Sistema Inteligente de Triaje y Agendamiento</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">Disponible 24/7 • Atención médica inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Acceso al Sistema")

    
    # Estructura de dos columnas: Formulario a la izquierda, Imagen a la derecha
    col_form, col_img = st.columns([1, 1], gap="large")
    
    with col_form:
        st.subheader("Iniciar Sesión")
        with st.form("login_form"):
            username_input = st.text_input("Usuario (DNI para Pacientes / Identificador)").strip()
            password_input = st.text_input("Contraseña", type="password").strip()
            submit_login = st.form_submit_button("Ingresar al Sistema")
            
            if submit_login:
                try:
                    df_users = pd.read_csv("content/usuarios.csv")
                    df_users["username"] = df_users["username"].astype(str)
                    user_record = df_users[(df_users["username"] == username_input) & (df_users["password"] == password_input)]
                    
                    if not user_record.empty:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username_input
                        st.session_state["rol"] = user_record.iloc[0]["rol"]
                        st.session_state["display_name"] = user_record.iloc[0]["display_name"]
                        st.rerun()
                    else:
                        st.error("Credenciales inválidas. Por favor verifique sus datos.")
                except FileNotFoundError:
                    st.error("Archivo base de usuarios no localizado. Ejecute 'generate_data.py' primero.")
    
                    
    with col_img:
        # Renderizado de la imagen conceptual del asistente médico inteligente
        st.image("assets/ai-medicine-robot-600.webp", width=500, caption=" Asistente Virtual Médico IA - Endocrino guiada por Inteligencia Artificial")

    st.markdown("""
    <div class="footer">
        <p>© 2024 Asistente Virtual Médico IA - Powered by LangChain & OpenAI</p>
        <p>Horarios: Lun-Sáb 7:00-19:00 • Dom 9:00-18:00</p>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# ==========================================
# ENTORNO GLOBAL PARA USUARIOS AUTENTICADOS
# ==========================================

# Lógica Determinista de Triaje (Solo aplica a Pacientes)
if st.session_state["rol"] == "paciente" and "triage_category" not in st.session_state:
    try:
        df_pacientes = pd.read_csv("content/dataset04.csv")
        df_pacientes["patient_id"] = df_pacientes["patient_id"].astype(str)
        paciente_row = df_pacientes[df_pacientes["patient_id"] == st.session_state["username"]]
        
        if not paciente_row.empty:
            glucose = float(paciente_row.iloc[0]["glucose_level"])
            st.session_state["glucose_level"] = glucose
            
            if glucose < 70.0:
                st.session_state["triage_category"] = "EMERGENCIA"
                st.session_state["action_message"] = "Llamar a Emergencias"
                st.session_state["chat_history"] = [AIMessage(content=f"Hola {st.session_state['display_name']}, detectamos un nivel de glucosa crítico ({glucose} mg/dL). Por favor, indícame qué síntomas tienes ahora mismo.")]
            elif glucose > 250.0:
                st.session_state["triage_category"] = "URGENCIAS"
                st.session_state["action_message"] = "Solicitar Orden Laboratorio"
            else:
                st.session_state["triage_category"] = "AGENDAR CITA"
                st.session_state["action_message"] = "Felicidades: Agendar tu cita de seguimiento"
                st.session_state["chat_history"] = [AIMessage(content=f"¡Hola {st.session_state['display_name']}! Tu nivel de glucosa está en metas de control diario. Vamos a agendar tu cita de seguimiento. ¿Qué día te convendría asistir (Lunes a Viernes, Sábado o Domingo)?")]
        else:
            st.error("Error: Historial clínico no encontrado para este DNI.")
            st.stop()
    except Exception as e:
        st.error(f"Error en motor de triaje: {e}")
        st.stop()

# ==========================================
# DISEÑO DE LA INTERFAZ: SIDEBAR DERECHO
# ==========================================
with st.sidebar:
    st.image("assets/ai-in-healthcare-icon.png", width=130)
    st.header("⚙️ Panel de Control")
    st.write(f"**Usuario:** {st.session_state['display_name']}")
    st.write(f"**Rol Asignado:** `{st.session_state['rol'].upper()}`")
    
    st.markdown("---")
    
    selected_model = st.selectbox("Modelo Fundacional (LLM)", ["gpt-4o", "gpt-3.5-turbo"])
    selected_temp = st.slider("Temperatura del Sistema", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
    
    # Modificación del Menú: Se activa "Historial" para todos (incluyendo pacientes)
    opciones_menu = ["Triaje / Agendamiento", "Historial"]
    if st.session_state["rol"] in ["enfermera", "médico"]:
        opciones_menu.append("Dashboard")
        
    selected_modulo = st.selectbox("Módulo Activo", opciones_menu)
    
    st.markdown("---")
    if st.button("Cerrar Sesión Segura"):
        st.session_state.clear()
        st.rerun()

# ==========================================
# LOGICA DE RENDERIZADO POR MÓDULOS
# ==========================================
st.title(f"🏥 ASISTENTE VIRTUAL MÉDICO IA")

if selected_modulo == "Triaje / Agendamiento":
    if st.session_state["rol"] != "paciente":
        st.info("El módulo de Triaje y Agendamiento está diseñado exclusivamente para interacción de pacientes en su portal.")
    else:
        st.subheader(f"Portal Clínico de: {st.session_state['display_name']}")
        
        st.info(f"**Nivel de Glucosa Analizado:** {st.session_state['glucose_level']} mg/dL")
        st.success(f"**Resultado del Triaje Determinista:** {st.session_state['action_message']}")
        
        if st.session_state["triage_category"] == "URGENCIAS":
            st.markdown(REGLAS_LABORATORIO_MD)
            st.warning("Su sesión ha finalizado. Por favor diríjase al laboratorio con las indicaciones descritas.")
        else:
            llm = ChatOpenAI(model=selected_model, temperature=selected_temp)
            
            if st.session_state["triage_category"] == "EMERGENCIA":
                tools = [trigger_doctor_emergency_alert]
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", (
                        "Eres un asistente de triaje de Endocrinología en tiempo real.\n"
                        "El paciente está cruzando una HIPOGLUCEMIA GRAVE. Tu tono debe ser calmado, empático y directo.\n"
                        "PROTOCOLO OBLIGATORIO:\n"
                        "Pregunta interactivamente:\n"
                        "1. Síntomas exactos actuales.\n"
                        "2. Frecuencia de ejercicio semanal.\n"
                        "3. Consumo reciente de carbohidratos o alcohol.\n"
                        "Al recopilar los datos, invoca de inmediato la herramienta `trigger_doctor_emergency_alert` y dile al usuario que busque ayuda física."
                    )),
                    MessagesPlaceholder(variable_name="chat_history"),
                ])
            else:
                tools = [save_appointment_to_csv]
                df_medicos = pd.read_csv("content/medicos04.csv")
                medicos_context = df_medicos.to_markdown(index=False)
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", (
                        "Eres el asistente virtual encargado de agendar citas de seguimiento preventivo en Diabetes.\n"
                        f"{HORARIOS_REGLAS}\n"
                        f"MÉDICOS DISPONIBLES:\n{medicos_context}\n\n"
                        "Guía al usuario amablemente a seleccionar un profesional médico de la lista y un horario válido según el día.\n"
                        "Al confirmar los datos, ejecuta obligatoriamente el tool `save_appointment_to_csv` pasándole un string con los detalles finales de la reserva."
                    )),
                    MessagesPlaceholder(variable_name="chat_history"),
                ])
            
            agent_chain = prompt_template | llm.bind_tools(tools)
            
            for msg in st.session_state["chat_history"]:
                role = "assistant" if isinstance(msg, AIMessage) else "user"
                with st.chat_message(role):
                    st.write(msg.content)
            
            if user_input := st.chat_input("Escriba su respuesta aquí..."):
                with st.chat_message("user"):
                    st.write(user_input)
                
                st.session_state["chat_history"].append(HumanMessage(content=user_input))
                
                with st.chat_message("assistant"):
                    with st.spinner("Procesando criterios médicos..."):
                        response = agent_chain.invoke({"chat_history": st.session_state["chat_history"]})
                        output_text = response.content
                        
                        if response.tool_calls:
                            for tool_call in response.tool_calls:
                                if tool_call["name"] == "save_appointment_to_csv":
                                    result_tool = save_appointment_to_csv.invoke(tool_call["args"])
                                    output_text = f"✅ **Cita Procesada Exitosamente.** {result_tool}\n\nEl sistema ha cerrado la agenda."
                                elif tool_call["name"] == "trigger_doctor_emergency_alert":
                                    result_tool = trigger_doctor_emergency_alert.invoke(tool_call["args"])
                                    output_text = f"🚨 **ALERTA ACTIVADA.** {result_tool}"
                        
                        st.write(output_text)
                        st.session_state["chat_history"].append(AIMessage(content=output_text))

elif selected_modulo == "Historial":
    st.subheader("📋 Registro de Citas y Alertas Clínicas")
    try:
        df_citas_view = pd.read_csv("content/citas.csv")
        df_citas_view["patient_id"] = df_citas_view["patient_id"].astype(str)
        
        # Segmentación por Rol de Seguridad
        if st.session_state["rol"] == "paciente":
            st.write("Historial clínico personalizado de sus interacciones del día de hoy:")
            # El paciente solo audita sus propios registros cruzando su DNI de sesión
            df_filtrado = df_citas_view[df_citas_view["patient_id"] == st.session_state["username"]]
            if df_filtrado.empty:
                st.info("Usted no cuenta con registros de citas guardadas ni alertas generadas en esta sesión.")
            else:
                st.dataframe(df_filtrado, use_container_width=True)
        else:
            # Personal médico y de enfermería audita la base de datos completa
            st.write("Vista completa del registro histórico de interacciones (Acceso Médico/Enfermería):")
            if df_citas_view.empty:
                st.info("No existen registros de interacciones reportadas el día de hoy.")
            else:
                st.dataframe(df_citas_view, use_container_width=True)
    except Exception as e:
        st.error(f"Error al abrir los registros persistentes: {e}")

elif selected_modulo == "Dashboard":
    st.subheader("📊 Panel de Control Analítico (Uso Exclusivo Clínico)")
    try:
        df_citas_db = pd.read_csv("content/citas.csv")
        if df_citas_db.empty:
            st.info("Registros insuficientes para el cálculo analítico de métricas.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Intervenciones", len(df_citas_db))
            with col2:
                emergencias_count = len(df_citas_db[df_citas_db["categoria"] == "EMERGENCIA"])
                st.metric("Alertas de Emergencia 🚨", emergencias_count)
            with col3:
                citas_count = len(df_citas_db[df_citas_db["categoria"] == "AGENDAR CITA"])
                st.metric("Citas en Agenda 📅", citas_count)
                
            st.markdown("---")
            st.write("### Distribución de Pacientes Atendidos por Gravedad de Triaje")
            st.bar_chart(df_citas_db["categoria"].value_counts())
    except Exception as e:
        st.error(f"Error al construir las métricas analíticas: {e}")