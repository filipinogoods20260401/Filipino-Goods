import streamlit as st
import pandas as pd
import os

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Filipino Goods",
    page_icon="🇵🇭",
    layout="wide"
)

# --- NYELVI SZÓTÁR ---
TEXTS = {
    "SK": {
        "lang_label": "Jazyk:",
        "nav_home": "Domov",
        "nav_products": "Produkty",
        "nav_categories": "Kategórie",
        "nav_about": "O nás",
        "nav_policies": "Podmienky",
        "nav_admin": "Admin",
        "welcome_title": "Vitajte v obchode Filipino Goods!",
        "welcome_sub": "Autentické filipínske potraviny a produkty priamo k vám doma.",
        "featured_title": "Vybrané produkty",
        "all_products": "Všetky produkty",
        "search_ph": "Hľadať produkt (SKU alebo Názov)...",
        "cart_title": "Váš košík",
        "cart_empty": "Košík je prázdny.",
        "checkout_btn": "Pokladňa",
        "add_to_cart": "Do košíka",
        "remove": "Odstrániť",
        "stock": "Skladom",
        "out_of_stock": "Vypredané",
        "price": "Cena",
        "qty": "Množstvo",
        "total": "Spolu",
        "category_select": "Vyberte kategóriu:",
        "cat_all": "Všetky kategórie",
        "about_title": "O obchode Filipino Goods",
        "about_text": "Filipino Goods prináša autentické chute Filipín priamo na Slovensko a do strednej Európy.",
        "contact_info": "Kontakt a adresa",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Slovensko",
        "policies_title": "Obchodné podmienky & Pravidlá",
        "tab_shipping": "Doručenie",
        "tab_payment": "Platba",
        "tab_privacy": "GDPR & Súkromie",
        "shipping_text": "- **Kuriér:** 2-4 pracovné dni.\n- **Poštovné:** Od 3.90 €. Pri objednávke nad 50 € je doprava ZADARMO!",
        "payment_text": "- **Bankový prevod:** Na základe vygenerovanej zálohovej faktúry.\n- **Dobierka:** Platba pri prevzatí (+1.50 €).",
        "privacy_text": "Vaše osobné údaje používame výhradne na spracovanie a doručenie vašej objednávky.",
        "checkout_title": "Dokončenie objednávky",
        "submit_order": "Odoslať objednávku",
        "back": "Späť",
        "added_to_cart": "Pridané do košíka!",
        "clear_cart": "Vyprázdniť košík",
        "no_products_found": "Nenašli sa žiadne produkty.",
        "order_summary": "Súhrn objednávky",
        "customer_info": "Údaje zákazníka",
        "full_name": "Meno a Priezvisko",
        "email": "E-mailová adresa",
        "phone": "Telefónne číslo",
        "street_address": "Ulica a číslo domu",
        "city": "Mesto",
        "zip_code": "PSČ",
        "country": "Krajina",
        "payment_method": "Spôsob platby",
        "pay_bank": "Bankový prevod",
        "pay_cod": "Dobierka (+1.50 €)",
        "order_notes": "Poznámka k objednávke (voliteľné)",
        "order_success": "Ďakujeme! Vaša objednávka bola úspešne odoslaná.",
        "order_error": "Prosím, vyplňte všetky povinné polia!",
        "admin_title": "Admin Správa",
        "admin_login": "Prihlásenie správcu",
        "enter_password": "Zadajte administrátorské heslo:",
        "password": "Heslo",
        "login_btn": "Prihlásiť sa",
        "logout_btn": "Odhlásiť sa",
        "stock_updated": "Skladové zásoby boli aktualizované.",
        "feature_shipping_title": "Rýchle doručenie",
        "feature_shipping_desc": "Do 2-4 pracovných dní, nad 50 € zadarmo!",
        "feature_authentic_title": "100% Autentické",
        "feature_authentic_desc": "Priamo od najobľúbenejších značiek.",
        "feature_payment_title": "Bezpečná platba",
        "feature_payment_desc": "Bankový prevod alebo dobierka."
    },
    "EN": {
        "lang_label": "Language:",
        "nav_home": "Home",
        "nav_products": "Products",
        "nav_categories": "Categories",
        "nav_about": "About Us",
        "nav_policies": "Policies",
        "nav_admin": "Admin",
        "welcome_title": "Welcome to Filipino Goods!",
        "welcome_sub": "Authentic Philippine food and products delivered to your door.",
        "featured_title": "Featured Products",
        "all_products": "All Products",
        "search_ph": "Search product (SKU or Name)...",
        "cart_title": "Your Cart",
        "cart_empty": "Your cart is empty.",
        "checkout_btn": "Checkout",
        "add_to_cart": "Add to Cart",
        "remove": "Remove",
        "stock": "In Stock",
        "out_of_stock": "Out of Stock",
        "price": "Price",
        "qty": "Quantity",
        "total": "Total",
        "category_select": "Select Category:",
        "cat_all": "All Categories",
        "about_title": "About Filipino Goods",
        "about_text": "Filipino Goods brings the authentic flavors of the Philippines directly to Slovakia and Central Europe.",
        "contact_info": "Contact Information",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Slovakia",
        "policies_title": "Terms & Policies",
        "tab_shipping": "Delivery",
        "tab_payment": "Payment",
        "tab_privacy": "Privacy & GDPR",
        "shipping_text": "- **Courier Delivery:** 2-4 business days.\n- **Shipping Fee:** From €3.90. FREE shipping on orders over €50!",
        "payment_text": "- **Bank Transfer:** Based on the generated proforma invoice.\n- **Cash on Delivery:** Pay upon delivery (+€1.50).",
        "privacy_text": "We use your personal data exclusively to process and deliver your order.",
        "checkout_title": "Complete Your Order",
        "submit_order": "Place Order",
        "back": "Back",
        "added_to_cart": "Added to cart!",
        "clear_cart": "Clear Cart",
        "no_products_found": "No products found.",
        "order_summary": "Order Summary",
        "customer_info": "Customer Information",
        "full_name": "Full Name",
        "email": "Email Address",
        "phone": "Phone Number",
        "street_address": "Street Address",
        "city": "City",
        "zip_code": "ZIP / Postal Code",
        "country": "Country",
        "payment_method": "Payment Method",
        "pay_bank": "Bank Transfer",
        "pay_cod": "Cash on Delivery (+€1.50)",
        "order_notes": "Order Notes (optional)",
        "order_success": "Thank you! Your order has been placed successfully.",
        "order_error": "Please fill in all required fields!",
        "admin_title": "Admin Dashboard",
        "admin_login": "Admin Login",
        "enter_password": "Enter admin password:",
        "password": "Password",
        "login_btn": "Login",
        "logout_btn": "Logout",
        "stock_updated": "Stock level updated.",
        "feature_shipping_title": "Fast Shipping",
        "feature_shipping_desc": "Within 2-4 business days, FREE over €50!",
        "feature_authentic_title": "100% Authentic",
        "feature_authentic_desc": "Directly from the most popular brands.",
        "feature_payment_title": "Secure Payment",
        "feature_payment_desc": "Bank transfer or cash on delivery."
    },
    "HU": {
        "lang_label": "Nyelv:",
        "nav_home": "Főoldal",
        "nav_products": "Termékek",
        "nav_categories": "Kategóriák",
        "nav_about": "Rólunk",
        "nav_policies": "Szabályzatok",
        "nav_admin": "Admin",
        "welcome_title": "Üdvözöljük a Filipino Goods webáruházban!",
        "welcome_sub": "Eredeti filippínó élelmiszerek és termékek egyenesen az Ön otthonába.",
        "featured_title": "Kiemelt Termékek",
        "all_products": "Összes Termék",
        "search_ph": "Keresés (SKU cikkszám vagy Név alapján)...",
        "cart_title": "Az Ön Kosara",
        "cart_empty": "A kosár jelenleg üres.",
        "checkout_btn": "Megrendelés / Pénztár",
        "add_to_cart": "Kosárba",
        "remove": "Törlés",
        "stock": "Raktáron",
        "out_of_stock": "Elfogyott",
        "price": "Ár",
        "qty": "Mennyiség",
        "total": "Összesen",
        "category_select": "Válasszon kategóriát:",
        "cat_all": "Összes Kategória",
        "about_title": "A Filipino Goods-ról",
        "about_text": "A Filipino Goods elhozza a Fülöp-szigetek autentikus ízeit Szlovákiába és Közép-Európába.",
        "contact_info": "Kapcsolat és Cím",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Szlovákia",
        "policies_title": "Vásárlási Feltételek & Szabályzatok",
        "tab_shipping": "Szállítás",
        "tab_payment": "Fizetés",
        "tab_privacy": "Adatvédelem & GDPR",
        "shipping_text": "- **Futárszolgálat:** 2-4 munkanap.\n- **Szállítási díj:** 3.90 €-tól. 50 € feletti rendelés esetén INGYENES!",
        "payment_text": "- **Banki átutalás:** A kiállított díjbekérő alapján.\n- **Utánvét:** Fizetés átvételkor a futárnál (+1.50 €).",
        "privacy_text": "Személyes adatait kizárólag a megrendelés feldolgozásához és kiszállításához használjuk fel.",
        "checkout_title": "Rendelés Befejezése",
        "submit_order": "Rendelés Elküldése",
        "back": "Vissza",
        "added_to_cart": "Kosárba helyezve!",
        "clear_cart": "Kosár ürítése",
        "no_products_found": "Nincs megjeleníthető termék.",
        "order_summary": "Rendelés Összegzése",
        "customer_info": "Vásárlói Adatok",
        "full_name": "Teljes Név",
        "email": "E-mail Cím",
        "phone": "Telefonszám",
        "street_address": "Utca, házszám",
        "city": "Település / Város",
        "zip_code": "Irányítószám",
        "country": "Ország",
        "payment_method": "Fizetési Mód",
        "pay_bank": "Banki átutalás",
        "pay_cod": "Utánvét (+1.50 €)",
        "order_notes": "Megjegyzés a rendeléshez (opcionális)",
        "order_success": "Köszönjük! A rendelését sikeresen rögzítettük.",
        "order_error": "Kérjük, töltse ki az összes kötelező mezőt!",
        "admin_title": "Adminisztrációs Felület",
        "admin_login": "Admin Bejelentkezés",
        "enter_password": "Adja meg az admin jelszót:",
        "password": "Jelszó",
        "login_btn": "Bejelentkezés",
        "logout_btn": "Kijelentkezés",
        "stock_updated": "Raktárkészlet frissítve.",
        "feature_shipping_title": "Gyors Szállítás",
        "feature_shipping_desc": "2-4 munkanapon belül, 50 € felett ingyenes!",
        "feature_authentic_title": "100% Autentikus",
        "feature_authentic_desc": "Közvetlenül a legnépszerűbb márkáktól.",
        "feature_payment_title": "Biztonságos Fizetés",
        "feature_payment_desc": "Banki átutalás vagy utánvét."
    }
}

# --- SESSION STATE INICIALIZÁLÁS ---
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "SK"

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

t = TEXTS[st.session_state.selected_lang]

# --- ADATOK BETÖLTÉSE ---
@st.cache_data
def load_products():
    file_path = "products.xlsx"
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        return df
    else:
        # Helyettesítő adatok, ha nincs meg a fájl
        data = {
            "SKU": ["ABMSG454", "ARGCB340", "BBCSA90", "BBCSB90", "BUEPY340"],
            "Product Name": ["Ajinomoto Brand - MSG 454g", "Argentina - Corned Beef 340g", "Boy Bawang - Garlic 90g", "Boy Bawang - Adobo 90g", "Buenas - Sweet Purple Yam Ube 340g"],
            "Selling Price (€)": [3.99, 7.99, 1.49, 1.49, 5.99],
            "Current Stock": [14, 16, 14, 21, 19],
            "Category": ["Spices", "Canned", "Snacks", "Snacks", "Sweets"]
        }
        return pd.DataFrame(data)

products_df = load_products()

def get_product_image(sku):
    extensions = [".jpg", ".png", ".jpeg", ".webp"]
    for ext in extensions:
        img_path = os.path.join("images", f"{sku}{ext}")
        if os.path.exists(img_path):
            return img_path
    return "https://via.placeholder.com/200?text=No+Image"

# --- RÁCS MEGJELENÍTŐ FÜGGVÉNY ---
def display_product_grid(df_to_show):
    available_products = df_to_show[df_to_show['Current Stock'] > 0]

    if available_products.empty:
        st.info(t["no_products_found"])
        return

    # Globális CSS a képekhez és mezőkhöz
    st.markdown(
        """
        <style>
        [data-testid="stImage"] img {
            height: 200px !important;
            width: 100% !important;
            object-fit: contain !important;
        }
        div[data-testid="stNumberInput"] {
            max-width: 70px !important;
            min-width: 65px !important;
        }
        div[data-testid="stButton"] > button {
            padding-left: 8px !important;
            padding-right: 8px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    products_list = available_products.reset_index(drop=True)
    
    # Soronként 5 termék
    for i in range(0, len(products_list), 5):
        cols = st.columns(5)
        row_chunk = products_list.iloc[i:i+5]
        
        for col_idx, (_, row) in enumerate(row_chunk.iterrows()):
            with cols[col_idx]:
                sku = str(row['SKU'])
                p_name = row['Product Name']
                p_price = float(row['Selling Price (€)'])
                p_stock = int(row['Current Stock'])
                img_src = get_product_image(sku)

                st.image(img_src, use_container_width=True)
                
                st.markdown(
                    f"""
                    <div style="height: 65px; overflow-y: auto; margin-bottom: 8px; font-size: 0.9rem; font-weight: bold; line-height: 1.2;">
                        {p_name}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                st.caption(f"SKU: `{sku}`")
                st.write(f"**{t['price']}:** {p_price:.2f} €")
                st.write(f"**{t['stock']}:** {p_stock} ks")
                
                q_col, b_col = st.columns([1, 2.2])
                with q_col:
                    quantity = st.number_input(
                        t['qty'],
                        min_value=1,
                        max_value=p_stock,
                        value=1,
                        key=f"qty_{sku}_{i}_{col_idx}",
                        label_visibility="collapsed"
                    )
                with b_col:
                    if st.button(t['add_to_cart'], key=f"btn_{sku}_{i}_{col_idx}", use_container_width=False):
                        st.session_state.cart[sku] = st.session_state.cart.get(sku, 0) + quantity
                        st.toast(f"✅ {t['added_to_cart']} ({quantity}x {p_name})")
                        st.rerun()

        st.divider()

# --- FEJLÉC & NAVIGÁCIÓ (ZÁSZLÓKKAL) ---
nav_cols = st.columns([1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1, 0.8, 0.8, 0.8])

pages = [
    ("Home", t["nav_home"]),
    ("Products", t["nav_products"]),
    ("Categories", t["nav_categories"]),
    ("About", t["nav_about"]),
    ("Policies", t["nav_policies"]),
    ("Admin", t["nav_admin"])
]

for idx, (page_key, page_label) in enumerate(pages):
    with nav_cols[idx]:
        is_active = (st.session_state.current_page == page_key)
        if st.button(page_label, key=f"nav_{page_key}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.current_page = page_key
            st.rerun()

with nav_cols[6]:
    st.markdown(f"<div style='text-align: right; padding-top: 6px; font-weight: bold;'>{t['lang_label']}</div>", unsafe_allow_html=True)

languages = [
    ("SK", "https://flagcdn.com/24x18/sk.png", "SK"),
    ("EN", "https://flagcdn.com/24x18/gb.png", "EN"),
    ("HU", "https://flagcdn.com/24x18/hu.png", "HU")
]

for l_idx, (code, img_url, label) in enumerate(languages):
    with nav_cols[7 + l_idx]:
        is_lang_active = (st.session_state.selected_lang == code)
        button_label = f"![{label}]({img_url}) {label}"
        
        if st.button(button_label, key=f"lang_btn_{code}", type="primary" if is_lang_active else "secondary", use_container_width=True):
            if st.session_state.selected_lang != code:
                st.session_state.selected_lang = code
                st.rerun()

st.divider()

# --- OLDALAK RENDERELÉSE ---

# 1. FŐOLDAL (HOME)
if st.session_state.current_page == "Home":
    st.title(t["welcome_title"])
    st.subheader(t["welcome_sub"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"🚚 **{t['feature_shipping_title']}**\n\n{t['feature_shipping_desc']}")
    with col2:
        st.info(f"💯 **{t['feature_authentic_title']}**\n\n{t['feature_authentic_desc']}")
    with col3:
        st.warning(f"💳 **{t['feature_payment_title']}**\n\n{t['feature_payment_desc']}")

    st.divider()
    st.subheader(f"🌟 {t['featured_title']}")
    display_product_grid(products_df.head(10))

# 2. TERMÉKEK (PRODUCTS)
elif st.session_state.current_page == "Products":
    st.title(t["all_products"])
    
    search_term = st.text_input(t["search_ph"], "")
    filtered_df = products_df
    if search_term:
        filtered_df = products_df[
            products_df["Product Name"].str.contains(search_term, case=False, na=False) |
            products_df["SKU"].str.contains(search_term, case=False, na=False)
        ]
    
    display_product_grid(filtered_df)

# 3. KATEGÓRIÁK (CATEGORIES)
elif st.session_state.current_page == "Categories":
    st.title(t["nav_categories"])
    
    categories = [t["cat_all"]] + list(products_df["Category"].dropna().unique())
    selected_cat = st.selectbox(t["category_select"], categories)
    
    if selected_cat == t["cat_all"]:
        display_product_grid(products_df)
    else:
        filtered_df = products_df[products_df["Category"] == selected_cat]
        display_product_grid(filtered_df)

# 4. RÓLUNK (ABOUT)
elif st.session_state.current_page == "About":
    st.title(t["about_title"])
    st.write(t["about_text"])
    st.subheader(t["contact_info"])
    st.write(f"📍 **{t['address']}**")

# 5. FELTÉTELEK (POLICIES)
elif st.session_state.current_page == "Policies":
    st.title(t["policies_title"])
    
    tab1, tab2, tab3 = st.tabs([t["tab_shipping"], t["tab_payment"], t["tab_privacy"]])
    with tab1:
        st.markdown(t["shipping_text"])
    with tab2:
        st.markdown(t["payment_text"])
    with tab3:
        st.markdown(t["privacy_text"])

# 6. ADMIN
elif st.session_state.current_page == "Admin":
    st.title(f"⚙️ {t['admin_title']}")
    
    if not st.session_state.admin_logged_in:
        st.subheader(f"🔐 {t['admin_login']}")
        admin_password = st.text_input(t["enter_password"], type="password")
        
        if st.button(t["login_btn"], type="primary"):
            if admin_password == "admin123":  # Állítsd be a kívánt jelszót!
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Helytelen jelszó / Incorrect password / Nesprávne heslo!")
    else:
        if st.button(t["logout_btn"]):
            st.session_state.admin_logged_in = False
            st.rerun()
            
        st.write("Skladové zásoby a správa produktov:")
        st.dataframe(products_df)
        else:
            st.subheader("🔐 Bejelentkezés")
            input_pwd = st.text_input("Adja meg az admin jelszót:", type="password")
        
        if st.button("Bejelentkezés", type="primary"):
            if input_pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.session_state.last_activity = datetime.now()
                st.success("Sikeres bejelentkezés!")                    st.rerun()
            else:
                st.error("Hibás jelszó!")
