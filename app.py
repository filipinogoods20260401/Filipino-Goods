from datetime import datetime
import os
import re
import json
import hashlib
import pandas as pd
import streamlit as st

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Filipino Goods - Online Shop",
    page_icon="🇵🇭",
    layout="wide"
)

EXCEL_FILE = 'Inventory management spreadsheet base.xlsx'
INVOICES_DIR = 'invoices'
IMAGES_DIR = 'images'
USERS_FILE = 'users.json'
BANNER_FILE = 'hero_banner.png'
NO_IMAGE_URL = 'https://via.placeholder.com/300x200?text=No+Image'

ADMIN_PASSWORD = "admin"  # ⚠️ Admin jelszó
TIMEOUT_SECONDS = 600    # 10 perc inaktivitás

if not os.path.exists(INVOICES_DIR):
    os.makedirs(INVOICES_DIR)

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# --- FELHASZNÁLÓI ADATBÁZIS KEZELÉSE (JSON) ---
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_product_image(sku):
    sku_str = str(sku).strip()
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        img_path = os.path.join(IMAGES_DIR, f"{sku_str}{ext}")
        if os.path.exists(img_path):
            return img_path
    return NO_IMAGE_URL

# --- NYELVI SZÓTÁR ---
TEXTS = {
    "SK": {
        "nav_home": "🏠 Domov",
        "nav_products": "📦 Produkty",
        "nav_categories": "📂 Kategórie",
        "nav_about": "ℹ️ O nás",
        "nav_policies": "📜 Podmienky",
        "nav_account": "👤 Účet",
        "nav_admin": "⚙️ Admin",
        "welcome_title": "Vitajte v obchode Filipino Goods!",
        "welcome_sub": "Autentické filipínske potraviny a produkty priamo k vám doma.",
        "featured_title": "🔥 Vybrané produkty",
        "all_products": "📦 Všetky produkty",
        "search_ph": "🔍 Hľadať produkt (SKU alebo Názov)...",
        "cart_title": "🛒 Váš košík",
        "cart_empty": "Košík je prázdny.",
        "checkout_btn": "🛍️ Pokladňa",
        "add_to_cart": "🛒 Do košíka",
        "remove": "❌ Odstrániť",
        "stock": "Skladom",
        "out_of_stock": "Vyprodané",
        "price": "Cena",
        "qty": "Množstvo",
        "total": "Spolu",
        "category_select": "Vyberte kategóriu:",
        "cat_all": "Všetky kategórie",
        "about_title": "ℹ️ O obchode Filipino Goods",
        "about_text": "Filipino Goods prináša autentické chute Filipín priamo na Slovensko a do strednej Európy.",
        "contact_info": "📍 Kontakt a adresa",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Slovensko",
        "policies_title": "📜 Obchodné podmienky & Pravidlá",
        "tab_shipping": "🚚 Doručenie",
        "tab_payment": "💳 Platba",
        "tab_privacy": "🔒 GDPR & Súkromie",
        "shipping_text": "- **Kuriér:** 2-4 pracovné dni.\n- **Poštovné:** Od 3.90 €. Pri objednávke nad 50 € je doprava ZADARMO!",
        "payment_text": "- **Bankový prevod:** Na základe vygenerovanej zálohovej faktúry.\n- **Dobierka:** Platba pri prevzatí (+1.50 €).",
        "privacy_text": "Vaše osobné údaje používame výhradne na spracovanie a doručenie vašej objednávky.",
        "checkout_title": "📋 Dokončenie objednávky",
        "submit_order": "✅ Odeslať objednávku",
        "back": "⬅️ Späť",
        "account_title": "👤 Používateľský účet",
        "login_tab": "🔑 Prihlásenie",
        "register_tab": "📝 Registrácia",
        "email_ph": "E-mailová adresa",
        "password_ph": "Heslo",
        "name_ph": "Meno a priezvisko",
        "phone_ph": "Telefónne číslo",
        "address_ph": "Doručovacia adresa (Ulica, Mesto, PSČ)",
        "login_btn": "Prihlásiť sa",
        "register_btn": "Zaregistrovať sa",
        "logout_btn": "🔒 Odhlásiť sa",
        "logged_in_as": "Prihlásený ako:",
        "login_success": "Úspešne prihlásený!",
        "login_error": "Nesprávny e-mail alebo heslo!",
        "reg_success": "Úspešná registrácia! Teraz sa môžete prihlásiť.",
        "reg_exists": "Tento e-mail už je zaregistrovaný!",
        "fill_all_fields": "Prosím, vyplňte všetky povinné polia!",
        "cust_details": "👤 Údaje zákazníka"
    },
    "EN": {
        "nav_home": "🏠 Home",
        "nav_products": "📦 Products",
        "nav_categories": "📂 Categories",
        "nav_about": "ℹ️ About Us",
        "nav_policies": "📜 Policies",
        "nav_account": "👤 Account",
        "nav_admin": "⚙️ Admin",
        "welcome_title": "Welcome to Filipino Goods!",
        "welcome_sub": "Authentic Philippine food and products delivered to your door.",
        "featured_title": "🔥 Featured Products",
        "all_products": "📦 All Products",
        "search_ph": "🔍 Search product (SKU or Name)...",
        "cart_title": "🛒 Your Cart",
        "cart_empty": "Your cart is empty.",
        "checkout_btn": "🛍️ Checkout",
        "add_to_cart": "🛒 Add to Cart",
        "remove": "❌ Remove",
        "stock": "In Stock",
        "out_of_stock": "Out of Stock",
        "price": "Price",
        "qty": "Quantity",
        "total": "Total",
        "category_select": "Select Category:",
        "cat_all": "All Categories",
        "about_title": "ℹ️ About Filipino Goods",
        "about_text": "Filipino Goods brings the authentic flavors of the Philippines directly to Slovakia and Central Europe.",
        "contact_info": "📍 Contact Information",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Slovakia",
        "policies_title": "📜 Terms & Policies",
        "tab_shipping": "🚚 Delivery",
        "tab_payment": "💳 Payment",
        "tab_privacy": "🔒 Privacy & GDPR",
        "shipping_text": "- **Courier Delivery:** 2-4 business days.\n- **Shipping Fee:** From €3.90. FREE shipping on orders over €50!",
        "payment_text": "- **Bank Transfer:** Based on the generated proforma invoice.\n- **Cash on Delivery:** Pay upon delivery (+€1.50).",
        "privacy_text": "We use your personal data exclusively to process and deliver your order.",
        "checkout_title": "📋 Complete Your Order",
        "submit_order": "✅ Place Order",
        "back": "⬅️ Back",
        "account_title": "👤 User Account",
        "login_tab": "🔑 Login",
        "register_tab": "📝 Register",
        "email_ph": "Email Address",
        "password_ph": "Password",
        "name_ph": "Full Name",
        "phone_ph": "Phone Number",
        "address_ph": "Shipping Address (Street, City, ZIP)",
        "login_btn": "Log In",
        "register_btn": "Register",
        "logout_btn": "🔒 Log Out",
        "logged_in_as": "Logged in as:",
        "login_success": "Successfully logged in!",
        "login_error": "Invalid email or password!",
        "reg_success": "Registration successful! You can now log in.",
        "reg_exists": "This email is already registered!",
        "fill_all_fields": "Please fill in all required fields!",
        "cust_details": "👤 Customer Details"
    },
    "HU": {
        "nav_home": "🏠 Főoldal",
        "nav_products": "📦 Termékek",
        "nav_categories": "📂 Kategóriák",
        "nav_about": "ℹ️ Rólunk",
        "nav_policies": "📜 Szabályzatok",
        "nav_account": "👤 Fiókom",
        "nav_admin": "⚙️ Admin",
        "welcome_title": "Üdvözöljük a Filipino Goods webáruházban!",
        "welcome_sub": "Eredeti filippínó élelmiszerek és termékek egyenesen az Ön otthonába.",
        "featured_title": "🔥 Kiemelt Termékek",
        "all_products": "📦 Összes Termék",
        "search_ph": "🔍 Keresés (SKU cikkszám vagy Név alapján)...",
        "cart_title": "🛒 Az Ön Kosara",
        "cart_empty": "A kosár jelenleg üres.",
        "checkout_btn": "🛍️ Megrendelés / Pénztár",
        "add_to_cart": "🛒 Kosárba",
        "remove": "❌ Törlés",
        "stock": "Raktáron",
        "out_of_stock": "Elfogyott",
        "price": "Ár",
        "qty": "Mennyiség",
        "total": "Összesen",
        "category_select": "Válasszon kategóriát:",
        "cat_all": "Összes Kategória",
        "about_title": "ℹ️ A Filipino Goods-ról",
        "about_text": "A Filipino Goods elhozza a Fülöp-szigetek autentikus ízeit Szlovákiába és Közép-Európába.",
        "contact_info": "📍 Kapcsolat és Cím",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Szlovákia",
        "policies_title": "📜 Vásárlási Feltételek & Szabályzatok",
        "tab_shipping": "🚚 Szállítás",
        "tab_payment": "💳 Fizetés",
        "tab_privacy": "🔒 Adatvédelem & GDPR",
        "shipping_text": "- **Futárszolgálat:** 2-4 munkanap.\n- **Szállítási díj:** 3.90 €-tól. 50 € feletti rendelés esetén INGYENES!",
        "payment_text": "- **Banki átutalás:** A kiállított díjbekérő alapján.\n- **Utánvét:** Fizetés átvételkor a futárnál (+1.50 €).",
        "privacy_text": "Személyes adatait kizárólag a megrendelés feldolgozásához és kiszállításához használjuk fel.",
        "checkout_title": "📋 Rendelés Befejezése",
        "submit_order": "✅ Rendelés Elküldése",
        "back": "⬅️ Vissza",
        "account_title": "👤 Felhasználói Fiók",
        "login_tab": "🔑 Bejelentkezés",
        "register_tab": "📝 Regisztráció",
        "email_ph": "E-mail cím",
        "password_ph": "Jelszó",
        "name_ph": "Teljes Név",
        "phone_ph": "Telefonszám",
        "address_ph": "Szállítási Cím (Utca, Város, Irányítószám)",
        "login_btn": "Bejelentkezés",
        "register_btn": "Regisztráció",
        "logout_btn": "🔒 Kijelentkezés",
        "logged_in_as": "Bejelentkezve mint:",
        "login_success": "Sikeres bejelentkezés!",
        "login_error": "Hibás e-mail cím vagy jelszó!",
        "reg_success": "Sikeres regisztráció! Most már bejelentkezhet.",
        "reg_exists": "Ez az e-mail cím már regisztrálva van!",
        "fill_all_fields": "Kérjük, töltse ki az összes kötelező mezőt!",
        "cust_details": "👤 Vásárló Adatai"
    }
}

def clean_price(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(',', '.').replace('€', '').strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    return float(match.group()) if match else 0.0

@st.cache_data(ttl=2)
def load_products():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        sheet_name = 'Current Stock' if 'Current Stock' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
        df = df.dropna(subset=['SKU', 'Product Name']).copy()
        df['SKU'] = df['SKU'].astype(str).str.strip()
        
        selling_col = next((c for c in df.columns if 'selling price' in c.lower()), None)
        df['Selling Price (€)'] = df[selling_col].apply(clean_price) if selling_col else 0.0

        stock_col = next((c for c in df.columns if any(k in c.lower() for k in ['stock', 'pieces', 'sklad'])), None)
        df['Current Stock'] = pd.to_numeric(df[stock_col], errors='coerce').fillna(0).astype(int) if stock_col else 0

        cat_col = next((c for c in df.columns if any(k in c.lower() for k in ['category', 'kategória', 'kategoria', 'type'])), None)
        df['Category'] = df[cat_col].astype(str).str.strip() if cat_col else 'General'

        return df
    except Exception:
        return pd.DataFrame()

# Session State Állapotok Inicializálása
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "page_view" not in st.session_state:
    st.session_state.page_view = "shop"
if "current_page_idx" not in st.session_state:
    st.session_state.current_page_idx = 0
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "lang" not in st.session_state:
    st.session_state.lang = "SK"

df_products = load_products()

# ==========================================
# 1. NYELVVÁLASZTÓ GOMBOK (LEGÜLÜL)
# ==========================================
lang_col1, lang_col2, lang_col3, _ = st.columns([1, 1, 1, 5])

with lang_col1:
    if st.button("🇸🇰 SK", type="primary" if st.session_state.lang == "SK" else "secondary", use_container_width=True):
        st.session_state.lang = "SK"
        st.rerun()

with lang_col2:
    if st.button("🇬🇧 EN", type="primary" if st.session_state.lang == "EN" else "secondary", use_container_width=True):
        st.session_state.lang = "EN"
        st.rerun()

with lang_col3:
    if st.button("🇭🇺 HU", type="primary" if st.session_state.lang == "HU" else "secondary", use_container_width=True):
        st.session_state.lang = "HU"
        st.rerun()

t = TEXTS[st.session_state.lang]

# ==========================================
# 2. HERO BANNER
# ==========================================
if os.path.exists(BANNER_FILE):
    st.image(BANNER_FILE, use_container_width=True)

# ==========================================
# 3. NAVIGÁCIÓS MENÜSÁV
# ==========================================
nav_options = [
    t["nav_home"],
    t["nav_products"],
    t["nav_categories"],
    t["nav_about"],
    t["nav_policies"],
    t["nav_account"],
    t["nav_admin"]
]

selected_page = st.radio(
    "", 
    nav_options, 
    index=st.session_state.current_page_idx, 
    horizontal=True
)

st.session_state.current_page_idx = nav_options.index(selected_page)
st.divider()

def display_product_grid(products_df):
    if products_df.empty:
        st.info("Žiadne produkty neboli nájdené.")
        return

    cols = st.columns(3)
    for idx, row in products_df.reset_index(drop=True).iterrows():
        col_idx = idx % 3
        sku = str(row['SKU'])
        p_name = row['Product Name']
        p_price = float(row['Selling Price (€)'])
        p_stock = int(row['Current Stock'])
        img_src = get_product_image(sku)

        with cols[col_idx]:
            st.image(img_src, use_container_width=True)
            st.markdown(f"### {p_name}")
            st.info(f"🔑 **SKU:** `{sku}`")
            st.write(f"💶 **{t['price']}:** {p_price:.2f} €")
            st.write(f"📦 **{t['stock']}:** {p_stock} ks")
            
            if p_stock > 0:
                quantity = st.number_input(
                    t['qty'],
                    min_value=1,
                    max_value=p_stock,
                    value=1,
                    key=f"qty_{sku}"
                )
                if st.button(t['add_to_cart'], key=f"btn_{sku}"):
                    st.session_state.cart[sku] = st.session_state.cart.get(sku, 0) + quantity
                    st.success(f"Pridané! ({quantity}x)")
            else:
                st.error(t['out_of_stock'])
            st.divider()

def display_cart_section():
    with st.expander(f"🛒 {t['cart_title']} ({sum(st.session_state.cart.values())} termék)", expanded=bool(st.session_state.cart)):
        if not st.session_state.cart:
            st.info(t['cart_empty'])
        else:
            grand_total = 0.0
            for sku, qty in list(st.session_state.cart.items()):
                prod_match = df_products[df_products['SKU'] == sku]
                if not prod_match.empty:
                    p_row = prod_match.iloc[0]
                    p_name = p_row['Product Name']
                    p_price = float(p_row['Selling Price (€)'])
                    total_p = p_price * qty
                    grand_total += total_p
                    
                    c_del, c_txt, c_tot = st.columns([1, 4, 2])
                    with c_del:
                        if st.button("❌", key=f"del_{sku}"):
                            del st.session_state.cart[sku]
                            st.rerun()
                    with c_txt:
                        st.write(f"**{p_name}** ({qty}x {p_price:.2f} €)")
                    with c_tot:
                        st.write(f"**{total_p:.2f} €**")

            st.markdown(f"### **{t['total']}: {grand_total:.2f} €**")
            if st.button(t['checkout_btn'], type="primary", use_container_width=True):
                st.session_state.page_view = "checkout"
                st.rerun()

# ==========================================
# OLDALAK MEGJELENÍTÉSE
# ==========================================

if st.session_state.page_view == "checkout":
    if st.button(t['back']):
        st.session_state.page_view = "shop"
        st.rerun()

    st.title(t['checkout_title'])

    if not st.session_state.cart:
        st.warning(t['cart_empty'])
    else:
        cart_items = []
        grand_total = 0.0
        for sku, qty in st.session_state.cart.items():
            prod_match = df_products[df_products['SKU'] == sku]
            if not prod_match.empty:
                p_row = prod_match.iloc[0]
                p_name = p_row['Product Name']
                p_price = float(p_row['Selling Price (€)'])
                total_p = p_price * qty
                grand_total += total_p
                cart_items.append({"SKU": sku, "Názov/Name": p_name, "Cena/Price (€)": p_price, "Ks/Qty": qty, "Spolu/Total (€)": total_p})

        summary_df = pd.DataFrame(cart_items)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.markdown(f"### **{t['total']}: {grand_total:.2f} €**")

        st.divider()
        st.subheader(t["cust_details"])

        u_info = st.session_state.current_user if st.session_state.user_logged_in else {}

        with st.form("checkout_form"):
            c_name = st.text_input(t["name_ph"], value=u_info.get("name", ""))
            c_email = st.text_input(t["email_ph"], value=u_info.get("email", ""))
            c_phone = st.text_input(t["phone_ph"], value=u_info.get("phone", ""))
            c_address = st.text_area(t["address_ph"], value=u_info.get("address", ""))
            
            submit_order_btn = st.form_submit_button(t["submit_order"], type="primary", use_container_width=True)
            
            if submit_order_btn:
                if not c_name or not c_email or not c_address:
                    st.error(t["fill_all_fields"])
                else:
                    st.success("🎉 Ďakujeme za objednávku! / Köszönjük a rendelést!")
                    st.session_state.cart = {}

else:
    # 1. 🏠 HOME
    if selected_page == t["nav_home"]:
        btn_col1, btn_col2, _ = st.columns([1, 1, 2])
        with btn_col1:
            if st.button("🛍️ SHOP NOW", type="primary", use_container_width=True):
                st.session_state.current_page_idx = 1
                st.rerun()
        with btn_col2:
            if st.button("🤍 OUR STORY", use_container_width=True):
                st.session_state.current_page_idx = 3
                st.rerun()

        st.divider()

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.success("🚚 **Gyors Szállítás**\n\n2-4 munkanapon belül, 50 € felett ingyenes!")
        with col_b2:
            st.info("💯 **100% Autentikus**\n\nKözvetlenül a legnépszerűbb márkáktól.")
        with col_b3:
            st.warning("💳 **Biztonságos Fizetés**\n\nBanki átutalás vagy utánvét.")

        st.divider()
        st.subheader(t["featured_title"])
        display_product_grid(df_products.head(6))
        display_cart_section()

    # 2. 📦 PRODUCTS
    elif selected_page == t["nav_products"]:
        st.title(t["all_products"])
        search_query = st.text_input(t["search_ph"], "")
        filtered_df = df_products[
            df_products['Product Name'].str.contains(search_query, case=False, na=False) |
            df_products['SKU'].str.contains(search_query, case=False, na=False)
        ] if search_query and not df_products.empty else df_products

        display_product_grid(filtered_df)
        display_cart_section()

    # 3. 📂 CATEGORIES
    elif selected_page == t["nav_categories"]:
        st.title(t["nav_categories"])
        cats = [t["cat_all"]] + (sorted(list(df_products['Category'].unique())) if not df_products.empty else [])
        selected_cat = st.selectbox(t["category_select"], cats)
        filtered_df = df_products if selected_cat == t["cat_all"] else df_products[df_products['Category'] == selected_cat]
        display_product_grid(filtered_df)
        display_cart_section()

    # 4. ℹ️ ABOUT US
    elif selected_page == t["nav_about"]:
        st.title(t["about_title"])
        st.write(t["about_text"])
        st.subheader(t["contact_info"])
        st.write(f"- 📍 {t['address']}\n- 📧 info@filipinogoods.sk\n- 📞 +421 900 123 456")
        display_cart_section()

    # 5. 📜 POLICIES
    elif selected_page == t["nav_policies"]:
        st.title(t["policies_title"])
        tab1, tab2, tab3 = st.tabs([t["tab_shipping"], t["tab_payment"], t["tab_privacy"]])
        with tab1:
            st.markdown(t["shipping_text"])
        with tab2:
            st.markdown(t["payment_text"])
        with tab3:
            st.markdown(t["privacy_text"])
        display_cart_section()

    # 6. 👤 ACCOUNT (BEJELENTKEZÉS ÉS REGISZTRÁCIÓ)
    elif selected_page == t["nav_account"]:
        st.title(t["account_title"])
        
        users_db = load_users()

        if st.session_state.user_logged_in and st.session_state.current_user:
            u = st.session_state.current_user
            st.success(f"{t['logged_in_as']} **{u['name']}** ({u['email']})")
            st.write(f"📞 **{t['phone_ph']}:** {u.get('phone', '-')}")
            st.write(f"🏠 **{t['address_ph']}:** {u.get('address', '-')}")

            if st.button(t["logout_btn"]):
                st.session_state.user_logged_in = False
                st.session_state.current_user = None
                st.rerun()

        else:
            auth_tab1, auth_tab2 = st.tabs([t["login_tab"], t["register_tab"]])

            with auth_tab1:
                st.subheader(t["login_tab"])
                l_email = st.text_input(t["email_ph"], key="login_email").lower().strip()
                l_pass = st.text_input(t["password_ph"], type="password", key="login_pass")

                if st.button(t["login_btn"], type="primary"):
                    if l_email in users_db and users_db[l_email]["password"] == hash_password(l_pass):
                        st.session_state.user_logged_in = True
                        st.session_state.current_user = users_db[l_email]
                        st.success(t["login_success"])
                        st.rerun()
                    else:
                        st.error(t["login_error"])

            with auth_tab2:
                st.subheader(t["register_tab"])
                r_name = st.text_input(t["name_ph"], key="reg_name")
                r_email = st.text_input(t["email_ph"], key="reg_email").lower().strip()
                r_pass = st.text_input(t["password_ph"], type="password", key="reg_pass")
                r_phone = st.text_input(t["phone_ph"], key="reg_phone")
                r_address = st.text_area(t["address_ph"], key="reg_address")

                if st.button(t["register_btn"], type="primary"):
                    if not r_name or not r_email or not r_pass:
                        st.error(t["fill_all_fields"])
                    elif r_email in users_db:
                        st.warning(t["reg_exists"])
                    else:
                        users_db[r_email] = {
                            "name": r_name,
                            "email": r_email,
                            "password": hash_password(r_pass),
                            "phone": r_phone,
                            "address": r_address
                        }
                        save_users(users_db)
                        st.success(t["reg_success"])

    # 7. ⚙️ ADMIN
    elif selected_page == t["nav_admin"]:
        st.title("⚙️ Adminisztrációs Felület")

        if st.session_state.admin_logged_in:
            if "last_activity" in st.session_state:
                elapsed_time = (datetime.now() - st.session_state.last_activity).total_seconds()
                if elapsed_time > TIMEOUT_SECONDS:
                    st.session_state.admin_logged_in = False
                    st.warning("⚠️ Munkamenet inaktivitás miatt lejárt (10 perc). Kérjük, jelentkezzen be újra!")
                    st.rerun()

        if st.session_state.admin_logged_in:
            st.session_state.last_activity = datetime.now()

            col_adm1, col_adm2 = st.columns([4, 1])
            with col_adm1:
                st.write("Üdvözöljük az Adminisztrációs felületen!")
            with col_adm2:
                if st.button("🔒 Kijelentkezés"):
                    st.session_state.admin_logged_in = False
                    st.rerun()

            st.divider()
            st.dataframe(df_products, use_container_width=True)

        else:
            st.subheader("🔐 Admin Bejelentkezés")
            input_pwd = st.text_input("Adja meg az admin jelszót:", type="password")
            
            if st.button("Bejelentkezés", type="primary"):
                if input_pwd == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.session_state.last_activity = datetime.now()
                    st.success("Sikeres bejelentkezés!")
                    st.rerun()
                else:
                    st.error("Hibás jelszó!")
