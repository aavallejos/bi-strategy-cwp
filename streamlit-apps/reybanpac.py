import streamlit as st

# --- Datos de productos (extraídos de la imagen) ---
productos = {
    "AGROQUÍMICOS - XNHHMY MVUIHEUIPO 400 MK": {
        "precio": 4.73,
        "sugerencias": [
            {"nombre": "AGROQUÍMICOS - XNHHMY SUINUIHEOW 500HMYW", "precio": 7.23},
            {"nombre": "AGROQUÍMICOS - MYISP UWIIPON 60MK HEOUIMYVUUINVUO", "precio": 3.07}
        ]
    },
    "FERTILIZANTES - XVW XOVWVIQUOK BOWO PKUS 250EHE": {
        "precio": 4.47,
        "sugerencias": [
            {"nombre": "FERTILIZANTES - XVW XOVWVIQUOK ZN PKUS (250EHE)", "precio": 4.47},
            {"nombre": "FERTILIZANTES - XVW HMOYKMY SVUIM (200HMYW)", "precio": 6.49}
        ]
    },
    "AGROQUÍMICOS - WOHMY UIBKUINMYUIMYOW 200 HMYW HEOUIMYVUUINVUO": {
        "precio": 3.23,
        "sugerencias": [
            {"nombre": "AGROQUÍMICOS - MYISP UWIIPON 60MK HEOUIMYVUUINVUO", "precio": 3.07},
            {"nombre": "DIVERSIFICADOS - JUIMWUUIS MYOSIXHEIUMYVOUIS 250HEHE", "precio": 0.90}
        ]
    }
}

# --- Estado del carrito ---
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- Información del pedido ---
st.markdown("## 📋 Información del pedido")

col1, col2 = st.columns(2)
with col1:
    punto_venta = st.selectbox("Punto de venta", ["Punto de venta 1", "Punto de venta 2", "Punto de venta 3"], key="punto")
with col2:
    cliente = st.selectbox("Nombre del cliente", ["Cliente 1", "Cliente 2", "Cliente 3"], key="cliente")

col3, col4 = st.columns(2)
with col3:
    tipo_cliente = st.selectbox("Tipo de cliente", ["Categoría 1", "Categoría 2", "Categoría 3"], key="tipo_cliente")
with col4:
    vendedor = st.selectbox("Vendedor", ["Vendedor 1", "Vendedor 2", "Vendedor 3"], key="vendedor")

fecha = st.date_input("Fecha del pedido", key="fecha")

# --- Agregar producto ---
st.markdown("## 📝 Agregar Producto")

col1, col2, col3, col4 = st.columns([3, 1.5, 2, 2])
with col1:
    producto_sel = st.selectbox("Producto", list(productos.keys()))
with col2:
    precio_unitario = productos[producto_sel]["precio"]
    st.markdown(f"<p style='font-size: 18px;'>💲<b>{precio_unitario:.2f}</b></p>", unsafe_allow_html=True)
with col3:
    descuento = st.number_input("Descuento %", min_value=0, max_value=50, value=1)
with col4:
    cantidad = st.number_input("Cantidad", min_value=1, value=3)

if st.button("➕ Agregar al Carrito"):
    st.session_state.carrito.append({
        "producto": producto_sel,
        "precio_base": precio_unitario,
        "descuento": descuento,
        "cantidad": cantidad,
        "sugerencias": productos[producto_sel]["sugerencias"],
        "ajustado": False
    })
    st.success(f"{producto_sel} agregado correctamente.")

# --- Mostrar carrito ---
if st.session_state.carrito:
    st.markdown("## 🛒 Productos Seleccionados")
    total_global = 0
    perdida_total = 0

    for i, item in enumerate(st.session_state.carrito.copy()):
        st.markdown(f"### {item['producto']}")
        precio_desc = item["precio_base"] * (1 - item["descuento"] / 100)
        total = precio_desc * item["cantidad"]
        perdida = (item["precio_base"] - precio_desc) * item["cantidad"]

        total_global += total
        perdida_total += perdida

        colA, colB = st.columns([6, 1])
        with colA:
            color = "red" if perdida > 0 else "green"
            mensaje = f"📉 Pérdida por descuento: ${perdida:.2f}" if perdida > 0 else "✅ Sin pérdida"
            st.markdown(f"""
            <div style="background-color:#f0f2f6;padding:10px;border-radius:10px;">
            <b>Cantidad:</b> {item['cantidad']}<br>
            <b>Precio base:</b> ${item['precio_base']:.2f}<br>
            <b>Descuento:</b> {item['descuento']}%<br>
            <b>Precio con descuento:</b> ${precio_desc:.2f}<br>
            <b>Total:</b> ${total:,.2f}<br>
            <span style="color:{color};font-weight:bold;">{mensaje}</span>
            </div>
            """, unsafe_allow_html=True)
        with colB:
            if st.button("🗑️ Quitar", key=f"remove_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()

        # --- Sugerencias para recuperar pérdida ---
        if item['sugerencias'] and perdida > 0:
            st.markdown(f"**🍍 Sugerencias para {item['producto']} (tabla ajustada para recuperar pérdida):**")
            perdida_por_sugerencia = perdida / len(item['sugerencias'])

            headers = st.columns([3, 2, 2, 2, 2, 2, 1])
            headers[0].markdown("**Producto**")
            headers[1].markdown("**Precio real**")
            headers[2].markdown("**% aplicado**")
            headers[3].markdown("**Diferencia**")
            headers[4].markdown("**Precio nuevo**")
            headers[5].markdown("**Cantidad**")
            headers[6].markdown("")

            for idx, sug in enumerate(item['sugerencias']):
                precio_real = sug['precio']
                precio_nuevo = precio_real + perdida_por_sugerencia
                diferencia = precio_nuevo - precio_real
                pct_aplicado = (diferencia / precio_real) * 100 if precio_real else 0

                fila = st.columns([3, 2, 2, 2, 2, 2, 1])
                fila[0].write(sug['nombre'])
                fila[1].write(f"${precio_real:.2f}")
                fila[2].write(f"{pct_aplicado:.2f}%")
                fila[3].write(f"+${diferencia:.2f}")
                fila[4].write(f"${precio_nuevo:.2f}")
                cantidad_sug = fila[5].number_input(" ", min_value=1, value=1, key=f"cant_sug_{i}_{idx}")
                if fila[6].button("➕", key=f"add_sug_{i}_{idx}"):
                    st.session_state.carrito.append({
                        "producto": sug['nombre'],
                        "precio_base": precio_nuevo,
                        "descuento": 0,
                        "cantidad": cantidad_sug,
                        "sugerencias": [],
                        "ajustado": True
                    })
                    st.success(f"{sug['nombre']} agregado correctamente.")
                    st.rerun()

    st.markdown(f"### 💵 Total Global: `${total_global:,.2f}`")
    ganancia_extra = sum(item['precio_base'] * item['cantidad'] for item in st.session_state.carrito if item.get("ajustado"))
    if ganancia_extra >= perdida_total:
        st.success(f"✅ ¡Pérdida recuperada! Ganancia extra: ${ganancia_extra - perdida_total:,.2f}")
    else:
        st.error(f"📉 Pérdida total por descuentos: ${perdida_total:,.2f}")
        faltante = perdida_total - ganancia_extra
        st.warning(f"⚠️ Aún faltan ${faltante:,.2f} para cubrir la pérdida.")
else:
    st.info("No hay productos agregados aún.")