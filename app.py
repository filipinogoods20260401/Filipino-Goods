import streamlit as st
import pandas as pd
import datetime

# --- PÁLYA BEÁLLÍTÁSAI ---
st.set_page_config(
    page_title="Filipino Goods - Inventory & Sales System",
    page_icon="📦",
    layout="wide"
)

# --- IN-MEMORY ADATBÁZIS / SAMPLE DATA KÉPZÉS ---
@st.cache_data
def load_initial_data():
    inventory_data = [
        {"SKU": "ABMSG454", "Product Name": "Ajinomoto Brand - MSG Sodium Glutamate 454g", "Category": "Sauces, Condiments & Seasonings", "Supplier": "Heuschen", "Arrival date": "16. 06. 2026", "Starting Stock": 14, "Total Received": 0, "Total Sold": 0, "Current Stock": 14, "Unit Price (€)": 1.89, "Selling Price (€)": 3.99},
        {"SKU": "ARGCB340", "Product Name": "Argentina - Corned Beef 340g", "Category": "Canned Seafood & Meat", "Supplier": "Heuschen", "Arrival date": "16. 06. 2026", "Starting Stock": 16, "Total Received": 0, "Total Sold": 0, "Current Stock": 16, "Unit Price (€)": 5.49, "Selling Price (€)": 7.99},
        {"SKU": "BBCSA90", "Product Name": "Boy Bawang - Corn Snack Garlic 90g", "Category": "Savory Snacks", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 14, "Total Received": 0, "Total Sold": 2, "Current Stock": 12, "Unit Price (€)": 0.74, "Selling Price (€)": 1.49},
        {"SKU": "BBCSG90", "Product Name": "Boy Bawang - Corn Snack Adobo 90g", "Category": "Savory Snacks", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 21, "Total Received": 0, "Total Sold": 0, "Current Stock": 21, "Unit Price (€)": 0.70, "Selling Price (€)": 1.49},
        {"SKU": "BUEPY340", "Product Name": "Buenas - Sweet Purple Yam Ube Spread 340g", "Category": "Preserved Fruits & Sweet Fillings", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 19, "Total Received": 0, "Total Sold": 0, "Current Stock": 19, "Unit Price (€)": 3.26, "Selling Price (€)": 5.99},
        {"SKU": "BUEGB250", "Product Name": "Buenas - Sauteed Shrimp Paste Ginisang Bagoong 250g", "Category": "Sauces, Condiments & Seasonings", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 20, "Total Received": 0, "Total Sold": 1, "Current Stock": 19, "Unit Price (€)": 2.23, "Selling Price (€)": 4.79},
        {"SKU": "BUEKR340", "Product Name": "Buenas - Kaong Palm Fruit Red in Jar 340g", "Category": "Preserved Fruits & Sweet Fillings", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 23, "Total Received": 0, "Total Sold": 0, "Current Stock": 23, "Unit Price (€)": 1.67, "Selling Price (€)": 3.29},
        {"SKU": "BUECW340", "Product Name": "Buenas - Coconut Gel White 340g", "Category": "Preserved Fruits & Sweet Fillings", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 24, "Total Received": 0, "Total Sold": 0, "Current Stock": 24, "Unit Price (€)": 1.26, "Selling Price (€)": 2.89},
        {"SKU": "BUEPC227", "Product Name": "Buenas - Flour Sticks Pancit Canton - Yellow 227g", "Category": "Instant Noodles & Asian Noodles", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 45, "Total Received": 0, "Total Sold": 0, "Current Stock": 45, "Unit Price (€)": 1.33, "Selling Price (€)": 2.79},
        {"SKU": "DPSVV11", "Product Name": "Datu Puti - Soy Sauce & Vinegar Value Pack 1l", "Category": "Sauces, Condiments & Seasonings", "Supplier": "Beagley Copperman", "Arrival date": "15. 05. 2026", "Starting Stock": 6, "Total Received": 0, "Total Sold": 0, "Current Stock": 6, "Unit Price (€)": 4.24, "Selling Price (€)": 6.39}
    ]
    
    sales_data = [
        {"Invoice No": "202608005", "Customer": "Franz Martin Clarin", "Date": "2026-08-13", "Item": "Boy Bawang - Corn Snack Garlic 90g", "Qty": 2, "Unit Price": 1.49, "Total Price": 2.98},
        {"Invoice No": "202608005", "Customer": "Franz Martin Clarin", "Date": "2026-08-13", "Item": "Buenas - Sauteed Shrimp Paste Ginisang Bagoong 250g", "Qty": 1, "Unit Price": 4.79, "Total Price": 4.79}
    ]
    
    return pd.DataFrame(inventory_data), pd.DataFrame(sales_data)

# Munkamenet állapotinicializálása
if 'df_inventory' not in st.session_state or 'df_sales' not in st.session_state:
    st.session_state.df_inventory, st.session_state.df_sales = load_initial_data()

df_inv = st.session_state.df_inventory
df_sales = st.session_state.df_sales

# --- OLDALSÁV (NAVIGATION) ---
st.sidebar.title("🇵🇭 Filipino Goods")
st.sidebar.subheader("Management System")
page = st.sidebar.radio("Navigáció", ["Dashboard", "Készletkezelő (Inventory)", "Új Eladás / Faktúra", "Értékesítési Előzmények"])

# --- 1. DASHBOARD ---
if page == "Dashboard":
    st.title("📊 Vezetői Műszerfal (Dashboard)")
    
    # KPI-k
    total_items = len(df_inv)
    total_stock_value = (df_inv["Current Stock"] * df_inv["Unit Price (€)"]).sum()
    total_sales_val = df_sales["Total Price"].sum() if not df_sales.empty else 0.0
    low_stock_items = len(df_inv[df_inv["Current Stock"] <= 5])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Termékek száma", f"{total_items} db")
    col2.metric("Készletérték (Beszerzés)", f"€{total_stock_value:.2f}")
    col3.metric("Összes Értékesítés", f"€{total_sales_val:.2f}")
    col4.metric("Alacsony készlet (≤ 5)", f"{low_stock_items} db", delta_color="inverse")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📦 Készlet Kategóriánként")
        cat_stock = df_inv.groupby("Category")["Current Stock"].sum().reset_index()
        st.bar_chart(cat_stock.set_index("Category"))
        
    with col_right:
        st.subheader("⚠️ Alacsony Készlet Figyelmeztetések")
        low_stock_df = df_inv[df_inv["Current Stock"] <= 5][["SKU", "Product Name", "Current Stock", "Supplier"]]
        if not low_stock_df.empty:
            st.dataframe(low_stock_df, use_container_width=True, hide_index=True)
        else:
            st.success("Minden termékből megfelelő mennyiség áll rendelkezésre!")

# --- 2. KÉSZLETKEZELŐ ---
elif page == "Készletkezelő (Inventory)":
    st.title("📦 Készletkezelés és Termékek")
    
    # Szűrők
    st.subheader("Szűrés és Keresés")
    col_s1, col_s2 = st.columns([2, 1])
    search_term = col_s1.text_input("Keresés terméknév vagy SKU alapján:", "")
    category_filter = col_s2.selectbox("Kategória szűrő:", ["Összes"] + list(df_inv["Category"].unique()))
    
    filtered_df = df_inv.copy()
    if search_term:
        filtered_df = filtered_df[
            filtered_df["Product Name"].str.contains(search_term, case=False, na=False) |
            filtered_df["SKU"].str.contains(search_term, case=False, na=False)
        ]
    if category_filter != "Összes":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]
        
    # Stock Value számított oszlop frissítése
    filtered_df["Stock Value (€)"] = filtered_df["Current Stock"] * filtered_df["Unit Price (€)"]
    
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("➕ Új Termék Hozzáadása")
    with st.form("add_product_form"):
        f_sku = st.text_input("SKU")
        f_name = st.text_input("Termék neve")
        f_cat = st.selectbox("Kategória", list(df_inv["Category"].unique()))
        f_sup = st.text_input("Beszállító", "Beagley Copperman")
        f_qty = st.number_input("Kezdő Készlet", min_value=0, value=10)
        f_buy_price = st.number_input("Beszerzési Ár (€)", min_value=0.0, value=1.0, step=0.01)
        f_sell_price = st.number_input("Eladási Ár (€)", min_value=0.0, value=2.0, step=0.01)
        
        submitted = st.form_submit_button("Termék Mentése")
        if submitted:
            if f_sku and f_name:
                new_row = {
                    "SKU": f_sku,
                    "Product Name": f_name,
                    "Category": f_cat,
                    "Supplier": f_sup,
                    "Arrival date": datetime.date.today().strftime("%d. %m. %Y"),
                    "Starting Stock": f_qty,
                    "Total Received": 0,
                    "Total Sold": 0,
                    "Current Stock": f_qty,
                    "Unit Price (€)": f_buy_price,
                    "Selling Price (€)": f_sell_price
                }
                st.session_state.df_inventory = pd.concat([st.session_state.df_inventory, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Termék sikeresen hozzáadva: {f_name}")
                st.rerun()
            else:
                st.error("Kérjük, töltse ki az SKU és Terméknév mezőket!")

# --- 3. ÚJ ELADÁS / FAKTÚRA ---
elif page == "Új Eladás / Faktúra":
    st.title("🧾 Új Eladás Rögzítése / Faktúra Generáló")
    
    col_cust1, col_cust2 = st.columns(2)
    inv_num = col_cust1.text_input("Faktúra / Számla száma", f"20260800{len(st.session_state.df_sales)+1}")
    customer_name = col_cust2.text_input("Vevő Neve", "Franz Martin Clarin")
    
    st.subheader("Poloatkok / Tételek kiválasztása")
    
    if "cart" not in st.session_state:
        st.session_state.cart = []
        
    with st.form("add_to_cart_form"):
        c_prod = st.selectbox("Termék kiválasztása", df_inv["Product Name"].tolist())
        c_qty = st.number_input("Mennyiség", min_value=1, value=1)
        add_item = st.form_submit_button("Tétel Hozzáadása a Kosárhoz")
        
        if add_item:
            prod_row = df_inv[df_inv["Product Name"] == c_prod].iloc[0]
            unit_price = prod_row["Selling Price (€)"]
            avail_stock = prod_row["Current Stock"]
            
            if c_qty > avail_stock:
                st.error(f"Nincs elegendő készlet! Elérhető: {avail_stock} db")
            else:
                st.session_state.cart.append({
                    "Product Name": c_prod,
                    "SKU": prod_row["SKU"],
                    "Qty": c_qty,
                    "Unit Price (€)": unit_price,
                    "Total (€)": round(unit_price * c_qty, 2)
                })
                st.success(f"Hozzáadva: {c_prod} ({c_qty} db)")

    # Kosár megjelenítése
    if st.session_state.cart:
        st.subheader("🛒 Jelenlegi Kosár")
        df_cart = pd.DataFrame(st.session_state.cart)
        st.dataframe(df_cart, use_container_width=True, hide_index=True)
        
        grand_total = df_cart["Total (€)"].sum()
        st.markdown(f"### **Végösszeg: €{grand_total:.2f}**")
        
        col_b1, col_b2 = st.columns([1, 4])
        if col_b1.button("Tranzakció Véglegesítése"):
            # Frissítjük a készletet és elmentjük a tranzakciót
            for item in st.session_state.cart:
                # Készlet levonás
                idx = st.session_state.df_inventory[st.session_state.df_inventory["Product Name"] == item["Product Name"]].index[0]
                st.session_state.df_inventory.at[idx, "Current Stock"] -= item["Qty"]
                st.session_state.df_inventory.at[idx, "Total Sold"] += item["Qty"]
                
                # Értékesítési rekord
                new_sale = {
                    "Invoice No": inv_num,
                    "Customer": customer_name,
                    "Date": datetime.date.today().strftime("%Y-%m-%d"),
                    "Item": item["Product Name"],
                    "Qty": item["Qty"],
                    "Unit Price": item["Unit Price (€)"],
                    "Total Price": item["Total (€)"]
                }
                st.session_state.df_sales = pd.concat([st.session_state.df_sales, pd.DataFrame([new_sale])], ignore_index=True)
            
            st.session_state.cart = []
            st.balloons()
            st.success("Sikeres értékesítés! A készlet frissült.")
            st.rerun()
            
        if col_b2.button("Kosár Ürítése"):
            st.session_state.cart = []
            st.rerun()

# --- 4. ÉRTÉKESÍTÉSI ELŐZMÉNYEK ---
elif page == "Értékesítési Előzmények":
    st.title("📋 Értékesítési Előzmények")
    
    if not df_sales.empty:
        st.dataframe(df_sales, use_container_width=True, hide_index=True)
        
        csv_data = df_sales.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Értékesítések Letöltése CSV-ként",
            data=csv_data,
            file_name=f"filipino_goods_sales_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("Még nem található értékesítési rekord.")
