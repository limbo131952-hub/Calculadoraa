from datetime import datetime
import io
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Precios y Proveedores", page_icon="🧮", layout="wide"
)

# --- SISTEMA DE SEGURIDAD (CONTRASEÑA) ---
CLAVE_ACCESO = (
    "CLIENTE2026"  # <-- Cambia esto por la clave que le darás a tu cliente
)

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if not st.session_state.autenticado:
  st.title("🔒 Acceso Restringido")
  st.write("Ingresa tu licencia o clave de acceso para abrir el sistema.")
  clave_ingresada = st.text_input("Contraseña:", type="password")
  if st.button("Ingresar", type="primary"):
    if clave_ingresada == CLAVE_ACCESO:
      st.session_state.autenticado = True
      st.rerun()
    else:
      st.error("❌ Contraseña incorrecta. Contacta al proveedor del software.")
  st.stop()  # Detiene el programa aquí si no pone la clave correcta

# --- APLICACIÓN PRINCIPAL (SOLO SE VE SI PONE LA CLAVE) ---
st.title("🧮 Sistema de Precios y Base de Datos de Proveedores")

if "bd_productos" not in st.session_state:
  st.session_state.bd_productos = []

# --- BARRA LATERAL: CONFIGURACIÓN DE CAPITAL Y GASTOS FIJOS ---
st.sidebar.header("⚙️ Gastos Fijos y Capital")
capital_invertido = st.sidebar.number_input(
    "Capital Invertido ($)", min_value=1.0, value=7000.0, step=100.0
)
alquiler_local = st.sidebar.number_input(
    "Alquiler del Local ($/mes)", min_value=0.0, value=300.0, step=10.0
)
sueldo_colaboradora = st.sidebar.number_input(
    "Sueldos ($/mes)", min_value=0.0, value=400.0, step=10.0
)
pago_luz = st.sidebar.number_input(
    "Pago de Luz ($/mes)", min_value=0.0, value=100.0, step=5.0
)
transporte = st.sidebar.number_input(
    "Transporte ($/mes)", min_value=0.0, value=100.0, step=5.0
)
suministros = st.sidebar.number_input(
    "Suministros de Oficina ($/mes)", min_value=0.0, value=50.0, step=5.0
)

total_gastos_fijos = (
    sueldo_colaboradora
    + pago_luz
    + transporte
    + suministros
    + alquiler_local
)
factor_gasto_fijo = total_gastos_fijos / capital_invertido
porcentaje_gasto_fijo = factor_gasto_fijo * 100

st.sidebar.markdown("---")
st.sidebar.info(
    f"**Total Gastos Fijos:** ${total_gastos_fijos:,.2f}/mes\n\n**Recargo Fijo"
    f" por Producto:** {porcentaje_gasto_fijo:.2f}%"
)

if st.sidebar.button("Cerrar Sesión"):
  st.session_state.autenticado = False
  st.rerun()

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs([
    "➕ Calcular y Guardar",
    "🔍 Comparar Proveedores",
    "📥 Base de Datos (Excel)",
])

with tab1:
  st.subheader("Ingresar y Guardar Producto")
  col1, col2 = st.columns(2)

  with col1:
    nombre_producto = st.text_input("1. Nombre del Producto").strip()
    proveedor = st.text_input("2. Nombre del PROVEEDOR").strip()
  with col2:
    costo_proveedor = st.number_input(
        "3. Costo unitario del proveedor ($)",
        min_value=0.0,
        format="%.2f",
        step=0.50,
    )
    margen_ganancia_pct = st.number_input(
        "4. Porcentaje de ganancia neta deseada (%)",
        min_value=0.0,
        value=30.0,
        step=1.0,
    )

  if st.button("Calcular Precio y Guardar", type="primary"):
    if not nombre_producto or not proveedor or costo_proveedor <= 0:
      st.warning(
          "⚠️ Por favor completa el nombre del producto, el proveedor y un"
          " costo mayor a $0."
      )
    else:
      IVA_ECUADOR = 0.15
      gasto_fijo_asignado = costo_proveedor * factor_gasto_fijo
      costo_real_unitario = costo_proveedor + gasto_fijo_asignado
      ganancia_neta_unitaria = costo_real_unitario * (margen_ganancia_pct / 100)
      precio_sin_iva = costo_real_unitario + ganancia_neta_unitaria
      valor_iva = precio_sin_iva * IVA_ECUADOR
      precio_final_publico = precio_sin_iva + valor_iva

      st.success(
          f"✅ FICHA DE PRECIO: {nombre_producto.upper()}"
          f" ({proveedor.upper()})"
      )

      m1, m2, m3, m4 = st.columns(4)
      m1.metric("Costo Proveedor", f"${costo_proveedor:,.2f}")
      m2.metric(
          f"Costo Real (+{porcentaje_gasto_fijo:.1f}% fijo)",
          f"${costo_real_unitario:,.2f}",
      )
      m3.metric(
          f"Ganancia Neta ({margen_ganancia_pct:.0f}%)",
          f"${ganancia_neta_unitaria:,.2f}",
      )
      m4.metric("PVP FINAL (Inc. IVA 15%)", f"${precio_final_publico:,.2f}")

      with st.expander("Ver desglose detallado de impuestos"):
        st.write(f"- **Gasto fijo asignado:** ${gasto_fijo_asignado:,.2f}")
        st.write(f"- **Subtotal (Antes de IVA):** ${precio_sin_iva:,.2f}")
        st.write(f"- **IVA Ecuador (15%):** ${valor_iva:,.2f}")

      fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
      st.session_state.bd_productos.append({
          "Fecha": fecha_hoy,
          "Producto": nombre_producto,
          "Proveedor": proveedor,
          "Costo_Proveedor": round(costo_proveedor, 2),
          "Gasto_Fijo_Asignado": round(gasto_fijo_asignado, 2),
          "Costo_Real_Total": round(costo_real_unitario, 2),
          "Margen_Pct": round(margen_ganancia_pct, 2),
          "Ganancia_Neta_Libre": round(ganancia_neta_unitaria, 2),
          "Subtotal_Sin_IVA": round(precio_sin_iva, 2),
          "IVA_15_Pct": round(valor_iva, 2),
          "PVP_Final": round(precio_final_publico, 2),
      })

with tab2:
  st.subheader("Comparativa de Proveedores")
  if not st.session_state.bd_productos:
    st.info(
        "Aún no tienes productos guardados. Registra productos en la primera"
        " pestaña para compararlos."
    )
  else:
    busqueda = st.text_input(
        "Escribe el nombre del producto a comparar:"
    ).strip()
    if busqueda:
      df_todos = pd.DataFrame(st.session_state.bd_productos)
      resultados = df_todos[
          df_todos["Producto"].str.contains(busqueda, case=False, na=False)
      ]

      if resultados.empty:
        st.warning(f"No se encontraron registros para '{busqueda}'.")
      else:
        resultados_ordenados = resultados.sort_values(by="Costo_Real_Total")
        mejor = resultados_ordenados.iloc[0]

        st.success(
            f"🏆 MEJOR OPCIÓN: **{mejor['Proveedor']}** | Costo Real:"
            f" **${mejor['Costo_Real_Total']:.2f}** | PVP Final:"
            f" **${mejor['PVP_Final']:.2f}**"
        )
        st.dataframe(
            resultados_ordenados[[
                "Proveedor",
                "Producto",
                "Costo_Proveedor",
                "Costo_Real_Total",
                "Ganancia_Neta_Libre",
                "PVP_Final",
            ]],
            use_container_width=True,
        )

with tab3:
  st.subheader("Historial Completo de Proveedores")
  if not st.session_state.bd_productos:
    st.info("No hay registros guardados todavía.")
  else:
    df_bd = pd.DataFrame(st.session_state.bd_productos)
    st.dataframe(df_bd, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
      df_bd.to_excel(writer, index=False, sheet_name="Proveedores")

    st.download_button(
        label="📥 Descargar Base de Datos en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="base_datos_proveedores.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
