import streamlit as st

# 1. Állapot (session_state) inicializálása
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None

st.title("📁 Kategórie")

# Példa kategóriák listájára (helyettesítsd a saját listáddal)
categories = ["Konzervy", "Snacks", "Omáčky a koreniny", "Nápoje"]

# ---------------------------------------------------------
# A) HA MÉG NINCS KIVÁLASZTVA KATEGÓRIA
# ---------------------------------------------------------
if st.session_state.selected_category is None:
    st.write("Vyberte kategóriu:")
    
    # Kategóriák megjelenítése 2 oszlopos gomb/kártya hálózatban
    cols = st.columns(2)
    for idx, category_name in enumerate(categories):
        with cols[idx % 2]:
            # Kattintható gomb minden kategóriához
            if st.button(f"📦 {category_name}", key=f"cat_{category_name}", use_container_width=True):
                st.session_state.selected_category = category_name
                st.rerun()  # Oldal újratöltése a kiválasztott kategóriával

# ---------------------------------------------------------
# B) HA MÁR KI VAN VÁLASZTVA EGY KATEGÓRIA
# ---------------------------------------------------------
else:
    # "Vissza a kategóriákhoz" gomb
    if st.button("← Všetky kategórie"):
        st.session_state.selected_category = None
        st.rerun()

    st.subheader(f"Kategória: {st.session_state.selected_category}")
    
    # ITT JELENÍTSD MEG A TERMÉKEKET (Szűrve a kiválasztott kategóriára)
    # Példa szűrés:
    # filtered_products = [p for p in all_products if p['category'] == st.session_state.selected_category]
    
    # Termékek megjelenítése ciklussal...
