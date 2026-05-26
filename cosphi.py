import streamlit as st
from fpdf import FPDF
import base64
from datetime import datetime

# Configuración para usar en móvil (sin sidebar y vista adaptable)
st.set_page_config(
    page_title="Medición cos φ",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Pequeño ajuste CSS para mejorar visualización en pantallas pequeñas
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔌 Factor de potencia (cos φ)")
st.markdown("Mide a partir de las vueltas del disco (analógico) o pulsos LED (digital).")

# ---------- ENTRADAS ----------
tipo_medidor = st.selectbox("Tipo de medidor", ["Analógico (disco)", "Digital (LED)"])
unidad_cte = "rev/kWh" if tipo_medidor.startswith("Analógico") else "imp/kWh"

constante_medidor = st.number_input(
    f"Constante del medidor ({unidad_cte})",
    min_value=1.0, value=800.0, step=10.0
)
vueltas = st.number_input("Nº de vueltas / pulsos contados", min_value=1, value=10)
tiempo_segundos = st.number_input(
    "Tiempo de medición (segundos)", min_value=0.1, value=60.0, step=1.0
)

st.markdown("---")
st.subheader("Parámetros eléctricos de la carga")
col_v, col_i = st.columns(2)
with col_v:
    voltaje = st.number_input("Tensión (V)", min_value=0.1, value=230.0, step=1.0)
with col_i:
    corriente = st.number_input("Corriente (A)", min_value=0.0, value=5.0, step=0.1)

# ---------- CÁLCULO ----------
calcular = st.button("Calcular cos φ", type="primary")

if "resultados" not in st.session_state:
    st.session_state.resultados = None

if calcular:
    if tiempo_segundos <= 0:
        st.error("El tiempo debe ser > 0")
    elif voltaje <= 0:
        st.error("La tensión debe ser > 0")
    elif corriente <= 0:
        st.warning("Corriente cero → sin carga. cos φ indefinido.")
    else:
        P = (3600.0 * vueltas) / (constante_medidor * tiempo_segundos)
        S = voltaje * corriente
        if S == 0:
            st.warning("Potencia aparente cero. No se puede calcular cos φ.")
        else:
            factor_potencia = P / S
            # Guardar resultados en la sesión para generar el informe después
            st.session_state.resultados = {
                "tipo_medidor": tipo_medidor,
                "constante": constante_medidor,
                "unidad": unidad_cte,
                "vueltas": vueltas,
                "tiempo": tiempo_segundos,
                "voltaje": voltaje,
                "corriente": corriente,
                "P": P,
                "S": S,
                "cos_phi": factor_potencia
            }

            st.success("Resultados")
            col1, col2, col3 = st.columns(3)
            col1.metric("Potencia activa (P)", f"{P:.2f} W")
            col2.metric("Potencia aparente (S)", f"{S:.2f} VA")
            col3.metric("Factor de potencia", f"{factor_potencia:.4f}")

            if factor_potencia > 1.0:
                st.warning("⚠️ cos φ > 1: valor no físico. Revise los datos.")
            elif factor_potencia < 0.0:
                st.warning("⚠️ cos φ negativo. Posible error en dirección.")
            else:
                tipo_carga = "resistiva pura" if factor_potencia > 0.99 else (
                    "inductiva o capacitiva" if factor_potencia < 0.95 else "casi resistiva"
                )
                st.info(f"📊 Tipo de carga: {tipo_carga}")

# ---------- GENERACIÓN DEL INFORME PDF ----------
if st.session_state.resultados is not None:
    st.markdown("---")
    st.subheader("📄 Informe")
    if st.button("Generar informe PDF"):
        datos = st.session_state.resultados
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Informe de medición de factor de potencia", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Datos ingresados", ln=True)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 7, f"Tipo de medidor: {datos['tipo_medidor']}", ln=True)
        pdf.cell(0, 7, f"Constante: {datos['constante']} {datos['unidad']}", ln=True)
        pdf.cell(0, 7, f"Vueltas / pulsos: {datos['vueltas']}", ln=True)
        pdf.cell(0, 7, f"Tiempo de medición: {datos['tiempo']:.1f} s", ln=True)
        pdf.cell(0, 7, f"Tensión: {datos['voltaje']:.1f} V", ln=True)
        pdf.cell(0, 7, f"Corriente: {datos['corriente']:.2f} A", ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Resultados", ln=True)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 7, f"Potencia activa (P): {datos['P']:.2f} W", ln=True)
        pdf.cell(0, 7, f"Potencia aparente (S): {datos['S']:.2f} VA", ln=True)
        pdf.cell(0, 7, f"Factor de potencia (cos φ): {datos['cos_phi']:.4f}", ln=True)
        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(0, 6, "Nota: Medición monofásica. Para trifásica usar S = √3·V_L·I_L.")

        # Descarga directa
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="informe_cos_phi.pdf">📥 Haz clic aquí para descargar el PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("Informe PDF generado correctamente.")

st.markdown("---")
st.caption("💡 Para usar como app Android: publique en Streamlit Cloud y agregue a la pantalla de inicio.")
