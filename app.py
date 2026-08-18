import streamlit as st
import pandas as pd
import os
import json
import urllib.request
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import stripe

# Stripe API kulcs betöltése
stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "")

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Filipino Goods",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    div[data-testid="stHorizontalBlock"] button {
        white-space: nowrap !important;
        word-break: normal !important;
        padding: 4px 10px !important;
        font-size: 13px !important;
        min-height: 40px !important;
    }
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 8px;
        }
        div[data-testid="stHorizontalBlock"] > div {
            flex: 0 0 auto !important;
            width: auto !important;
        }
    }
</style>
""", unsafe_allow_html=True)

ORDERS_FILE = "orders.json"
SETTINGS_FILE = "settings.json"
USERS_FILE = "users.json"
ADMIN_EMAIL = "jenoladanyi@filipinogoods.sk"

# --- ADAT- ÉS BEÁLLÍTÁSKEZELÉS ---
def load_settings():
    default_settings = {
        "iban": "SK89 0000 0000 1234 5678",
        "swift": "SUBASKBX",
        "company_name": "Saját Cég s.r.o.",
        "company_address": "Mestská 12, 946 03 Kolárovo",
        "ico": "12345678",
        "dic": "2021234567",
        "ic_dph": "",
        "register_info": "Zapísaný v OR Okresného súdu Nitra, oddiel: Sro, vložka č. 12345/N",
        "is_dph_payer": False
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_settings.update(data)
                return default_settings
        except Exception:
            return default_settings
    return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

def save_order(order_data):
    orders = load_orders()
    orders.append(order_data)
    save_orders(orders)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# --- UNICODE BETŰTÍPUSOK LETÖLTÉSE ÉS BEÁLLÍTÁSA ---
def setup_pdf_fonts():
    font_regular = "DejaVuSans.ttf"
    if not os.path.exists(font_regular):
        try:
            urllib.request.urlretrieve(
                "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf", 
                font_regular
            )
        except Exception:
            pass
    if os.path.exists(font_regular):
        pdfmetrics.registerFont(TTFont("DejaVu", font_regular))

setup_pdf_fonts()

# --- FAKTÚRA GENERÁLÓ FÜGGVÉNY ---
def generate_pdf_invoice(order):
    settings = load_settings()
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    font_name = "DejaVu" if "DejaVu" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    
    p.setFont(font_name, 13)
    p.drawString(50, 750, f"FAKTÚRA - DAŇOVÝ DOKLAD č. {order['id']}")
    
    p.setFont(font_name, 8)
    p.drawString(350, 755, f"Dátum vyhotovenia (Kiállítás): {order['date']}")
    p.drawString(350, 742, f"Dátum dodania (Teljesítés): {order['date']}")
    
    p.setFont(font_name, 9)
    p.drawString(50, 715, "DODÁVATEĽ (Eladó):")
    p.drawString(320, 715, "ODBERATEĽ (Vevő):")
    
    p.setFont(font_name, 8)
    p.drawString(50, 700, f"{settings['company_name']}")
    p.drawString(50, 688, f"{settings['company_address']}")
    p.drawString(50, 676, f"IČO: {settings['ico']} | DIČ: {settings['dic']}")
    if settings.get('ic_dph'):
        p.drawString(50, 664, f"IČ DPH: {settings['ic_dph']}")
    else:
        p.drawString(50, 664, "Dodávateľ nie je platiteľom DPH")
    
    reg_text = str(settings.get('register_info', ''))
    p.drawString(50, 652, reg_text[:45])
    if len(reg_text) > 45:
        p.drawString(50, 642, reg_text[45:90])
    
    p.drawString(320, 700, f"{order['name']}")
    p.drawString(320, 688, f"{order['address']}")
    p.drawString(320, 676, f"{order['city']}, {order['zip']}")
    p.drawString(320, 664, f"E-mail: {order['email']}")
    p.drawString(320, 652, f"Tel: {order['phone']}")
    
    p.line(50, 630, 550, 630)
    
    p.setFont(font_name, 8)
    p.drawString(50, 615, f"Spôsob úhrady (Fizetés): {order['payment']}")
    p.drawString(320, 615, f"IBAN: {settings['iban']}")
    p.drawString(320, 603, f"SWIFT/BIC: {settings['swift']}")
    p.drawString(320, 591, f"Variabilný symbol: {order['id']}")
    
    p.line(50, 580, 550, 580)
    
    y = 560
    p.setFont(font_name, 8.5)
    p.drawString(50, y, "Názov položky (Termék neve)")
    p.drawString(280, y, "Množstvo")
    p.drawString(350, y, "J.cena")
    
    if settings.get('is_dph_payer'):
        p.drawString(420, y, "DPH %")
        p.drawString(480, y, "Spolu s DPH")
    else:
        p.drawString(480, y, "Spolu (Összesen)")
        
    y -= 10
    p.line(50, y, 550, y)
    
    y -= 15
    p.setFont(font_name, 8)
    for item in order['items']:
        p.drawString(50, y, str(item['name'])[:35])
        p.drawString(280, y, f"{item['qty']} ks")
        unit_price = item['subtotal'] / item['qty'] if item['qty'] > 0 else 0
        p.drawString(350, y, f"{unit_price:.2f} €")
        
        if settings.get('is_dph_payer'):
            p.drawString(420, y, "20%")
            p.drawString(480, y, f"{item['subtotal']:.2f} €")
        else:
            p.drawString(480, y, f"{item['subtotal']:.2f} €")
        y -= 15
        
    p.line(50, y, 550, y)
    
    y -= 25
    p.setFont(font_name, 10)
    
    if settings.get('is_dph_payer'):
        netto = order['total'] / 1.20
        dph_val = order['total'] - netto
        p.drawString(300, y, f"Základ dane (Adóalap): {netto:.2f} €")
        y -= 15
        p.drawString(300, y, f"DPH 20%: {dph_val:.2f} €")
        y -= 15
        p.drawString(300, y, f"CELKOM K ÚHRADE: {order['total']:.2f} EUR")
    else:
        p.drawString(300, y, f"CELKOM K ÚHRADE: {order['total']:.2f} EUR")
        y -= 20
        p.setFont(font_name, 7.5)
        p.drawString(50, y, "Nie sme platiteľom DPH podľa § 4 zákona č. 222/2004 Z. z. o dani z pridanej hodnoty.")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- NYELVI SZÓTÁR ---
TEXTS = {
    "SK": {
        "lang_label": "Jazyk:", "nav_home": "Domov", "nav_products": "Produkty", "nav_categories": "Kategórie",
        "nav_about": "O nás", "nav_policies": "Podmienky", "nav_terms": "Podmienky", "nav_admin": "Admin",
        "welcome_title": "Vitajte v obchode Filipino Goods!", "welcome_sub": "Autentické filipínske potraviny a produkty.",
        "featured_title": "Vybrané produkty", "all_products": "Všetky produkty", "search_ph": "Hľadať produkt...",
        "cart_title": "Váš košík", "cart_empty": "Košík je prázdny.", "checkout_btn": "Pokladňa",
        "add_to_cart": "Do košíka", "remove": "Odstrániť", "stock": "Skladom", "out_of_stock": "Vypredané",
        "price": "Cena", "qty": "Množstvo", "total": "Spolu", "category_select": "Vyberte kategóriu:",
        "cat_all": "Všetky kategórie", "about_title": "O obchode Filipino Goods",
        "about_text": "Filipino Goods prináša autentické chute Filipín.", "contact_info": "Kontakt a adresa",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy", "policies_title": "Obchodné podmienky",
        "tab_shipping": "Doručenie", "tab_payment": "Platba", "tab_privacy": "GDPR",
        "shipping_text": "- **Kuriér:** 2-4 dni.", "payment_text": "- **Bankový prevod** / Dobierka",
        "privacy_text": "Osobné údaje chránime.", "checkout_title": "Dokončenie objednávky",
        "submit_order": "Odoslať", "back": "Späť", "added_to_cart": "Pridané!", "clear_cart": "Vyprázdniť",
        "no_products_found": "Nenašli sa produkty.", "order_summary": "Súhrn", "customer_info": "Údaje",
        "full_name": "Meno", "email": "E-mail", "phone": "Telefón", "street_address": "Ulica", "city": "Mesto",
        "zip_code": "PSČ", "country": "Krajina", "payment_method": "Platba", "pay_bank": "Prevod",
        "pay_cod": "Dobierka", "order_notes": "Poznámka", "order_success": "Objednávka odoslaná!",
        "order_error": "Vyplňte polia!", "admin_title": "Admin Správa", "stock_updated": "Sklad aktualizovaný.",
        "login_title": "Prihlásenie / Registrácia", "tab_login": "Prihlásenie", "tab_register": "Registrácia",
        "login_success": "Vitajte", "login_error": "Nesprávne údaje!", "logout_user": "Odhlásiť sa"
    },
    "EN": {
        "lang_label": "Language:", "nav_home": "Home", "nav_products": "Products", "nav_categories": "Categories",
        "nav_about": "About Us", "nav_policies": "Policies", "nav_terms": "Policies", "nav_admin": "Admin",
        "welcome_title": "Welcome to Filipino Goods!", "welcome_sub": "Authentic Philippine goods.",
        "featured_title": "Featured Products", "all_products": "All Products", "search_ph": "Search...",
        "cart_title": "Your Cart", "cart_empty": "Your cart is empty.", "checkout_btn": "Checkout",
        "add_to_cart": "Add to Cart", "remove": "Remove", "stock": "In Stock", "out_of_stock": "Out of Stock",
        "price": "Price", "qty": "Quantity", "total": "Total", "category_select": "Select Category:",
        "cat_all": "All Categories", "about_title": "About Filipino Goods",
        "about_text": "Authentic tastes of Philippines.", "contact_info": "Contact",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy", "policies_title": "Terms & Policies",
        "tab_shipping": "Delivery", "tab_payment": "Payment", "tab_privacy": "Privacy",
        "shipping_text": "- **Courier:** 2-4 days.", "payment_text": "- **Bank Transfer**",
        "privacy_text": "We respect privacy.", "checkout_title": "Checkout",
        "submit_order": "Place Order", "back": "Back", "added_to_cart": "Added!", "clear_cart": "Clear Cart",
        "no_products_found": "No products found.", "order_summary": "Order Summary", "customer_info": "Customer Info",
        "full_name": "Full Name", "email": "Email", "phone": "Phone", "street_address": "Address", "city": "City",
        "zip_code": "ZIP", "country": "Country", "payment_method": "Payment", "pay_bank": "Bank Transfer",
        "pay_cod": "COD", "order_notes": "Notes", "order_success": "Order placed!",
        "order_error": "Fill required fields!", "admin_title": "Admin Dashboard", "stock_updated": "Stock updated.",
        "login_title": "Login / Register", "tab_login": "Login", "tab_register": "Register",
        "login_success": "Welcome", "login_error": "Invalid credentials!", "logout_user": "Logout"
    },
    "HU": {
        "lang_label": "Nyelv:", "nav_home": "Főoldal", "nav_products": "Termékek", "nav_categories": "Kategóriák",
        "nav_about": "Rólunk", "nav_policies": "Szabályzatok", "nav_terms": "Szabályzatok", "nav_admin": "Admin",
        "welcome_title": "Üdvözöljük a Filipino Goods webáruházban!", "welcome_sub": "Eredeti filippínó élelmiszerek.",
        "featured_title": "Kiemelt Termékek", "all_products": "Összes Termék", "search_ph": "Keresés...",
        "cart_title": "Kosár", "cart_empty": "A kosár üres.", "checkout_btn": "Pénztár",
        "add_to_cart": "Kosárba", "remove": "Törlés", "stock": "Raktáron", "out_of_stock": "Elfogyott",
        "price": "Ár", "qty": "Mennyiség", "total": "Összesen", "category_select": "Kategória:",
        "cat_all": "Összes Kategória", "about_title": "A Filipino Goods-ról",
        "about_text": "Fülöp-szigeteki élelmiszerek.", "contact_info": "Kapcsolat",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy", "policies_title": "Szabályzatok",
        "tab_shipping": "Szállítás", "tab_payment": "Fizetés", "tab_privacy": "Adatvédelem",
        "shipping_text": "- **Futár:** 2-4 nap.", "payment_text": "- **Banki átutalás**",
        "privacy_text": "Adatvédelem.", "checkout_title": "Megrendelés",
        "submit_order": "Rendelés", "back": "Vissza", "added_to_cart": "Hozzáadva!", "clear_cart": "Ürítés",
        "no_products_found": "Nincs találat.", "order_summary": "Összegzés", "customer_info": "Vásárló adatai",
        "full_name": "Név", "email": "E-mail", "phone": "Telefon", "street_address": "Cím", "city": "Város",
        "zip_code": "Irányítószám", "country": "Ország", "payment_method": "Fizetés", "pay_bank": "Átutalás",
        "pay_cod": "Utánvét", "order_notes": "Megjegyzés", "order_success": "Sikeres rendelés!",
        "order_error": "Töltse ki a mezőket!", "admin_title": "Adminisztráció", "stock_updated": "Raktár frissítve.",
        "login_title": "Bejelentkezés / Regisztráció", "tab_login": "Bejelentkezés", "tab_register": "Regisztráció",
        "login_success": "Üdvözöljük", "login_error": "Hibás adatok!", "logout_user": "Kijelentkezés"
    }
}

# --- SESSION STATE INICIALIZÁLÁS ---
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "SK"
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

t = TEXTS[st.session_state.selected_lang]

# --- ADATOK BETÖLTÉSE ---
@st.cache_data
def load_products():
    file_path = "Inventory management spreadsheet base.xlsx"
    if not os.path.exists(file_path):
        file_path = "products.xlsx"

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        column_mapping = {
            "Selling Price": "Selling Price (€)",
            "Price": "Selling Price (€)",
            "Price (€)": "Selling Price (€)",
            "Ár": "Selling Price (€)",
            "Stock": "Current Stock",
            "Quantity": "Current Stock",
            "Készlet": "Current Stock",
            "Name": "Product Name",
            "Terméknév": "Product Name"
        }
        return df.rename(columns=column_mapping)
    return pd.DataFrame(columns=["SKU", "Product Name", "Selling Price (€)", "Current Stock", "Category"])

products_df = load_products()

@st.cache_data(ttl=3600)
def get_eur_huf_rate():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return float(data["rates"]["HUF"])
    except Exception:
        return 400.0

def get_product_image(sku):
    extensions = [".jpg", ".png", ".jpeg", ".webp"]
    for ext in extensions:
        img_path = os.path.join("images", f"{sku}{ext}")
        if os.path.exists(img_path):
            return img_path
    return "https://via.placeholder.com/200?text=No+Image"

# --- KOSÁR ÉS PENZTÁR OLDAL ---
def render_checkout_page():
    st.divider()
    st.title("🛒 Kosár és Fizetés / Košík a Platba")

    if not st.session_state.cart:
        st.warning("A kosár jelenleg üres. / Váš košík je prázdny.")
        if st.button("⬅️ Vissza a vásárláshoz", key="btn_back_empty_cart"):
            st.session_state.show_checkout = False
            st.session_state.page = "home"
            st.session_state.current_page = "home"
            st.rerun()
    else:
        if "delete_sku" in st.session_state:
            sku_to_del = st.session_state.delete_sku
            if sku_to_del in st.session_state.cart:
                del st.session_state.cart[sku_to_del]
            del st.session_state.delete_sku
            st.rerun()

        eur_huf = get_eur_huf_rate()
        cart_total = 0.0
        
        st.subheader("Tételek a kosárban:")
        for sku, qty in list(st.session_state.cart.items()):
            prod = products_df[products_df["SKU"].astype(str) == str(sku)]
            if not prod.empty:
                p_name = prod.iloc[0]["Product Name"]
                p_price = float(prod.iloc[0]["Selling Price (€)"])
                subtotal = p_price * qty
                cart_total += subtotal
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{p_name}** (SKU: {sku})")
                with col2:
                    st.write(f"{qty} ks x {p_price:.2f} €")
                with col3:
                    st.write(f"**{subtotal:.2f} €**")
                with col4:
                    if st.button("🗑️", key=f"del_{sku}"):
                        st.session_state.delete_sku = sku
                        st.rerun()

        st.divider()
        st.markdown(f"### **Összesen: {cart_total:.2f} €**")
        st.caption(f"≈ {cart_total * eur_huf:,.0f} HUF")
        st.divider()

        u = st.session_state.user or {}
        with st.form("checkout_form"):
            st.subheader("🚚 Szállítási adatok")
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Név *", value=u.get("name", ""))
                email = st.text_input("E-mail *", value=u.get("email_key", ""))
                phone = st.text_input("Telefonszám *", value=u.get("phone", ""))
            with col_b:
                address = st.text_input("Utca, házszám *", value=u.get("address", ""))
                city = st.text_input("Város *", value=u.get("city", ""))
                zip_code = st.text_input("Irányítószám *", value=u.get("zip", ""))
            
            payment_method = st.radio("Fizetési mód:", ["💳 Online bankkártya (Stripe)", "🏦 Banki átutalás", "🚚 Utánvét (+1.50 €)"])
            notes = st.text_area("Megjegyzés")
            submit = st.form_submit_button("Rendelés véglegesítése ➔", type="primary", use_container_width=True)

            if submit:
                if not (name and email and phone and address and city and zip_code):
                    st.error("Minden kötelező mezőt töltsön ki!")
                else:
                    is_cod = "Utánvét" in payment_method
                    final_total = cart_total + (1.50 if is_cod else 0.0)
                    
                    # Rendelés adatszerkezet elmentése
                    order_id = f"ORD-{len(load_orders()) + 1001}"
                    order_items = []
                    for sku, qty in st.session_state.cart.items():
                        prod = products_df[products_df["SKU"].astype(str) == str(sku)]
                        if not prod.empty:
                            order_items.append({
                                "sku": str(sku),
                                "name": str(prod.iloc[0]["Product Name"]),
                                "qty": int(qty),
                                "price": float(prod.iloc[0]["Selling Price (€)"])
                            })

                    new_order = {
                        "id": order_id,
                        "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                        "customer": {
                            "name": name, "email": email, "phone": phone,
                            "address": address, "city": city, "zip": zip_code
                        },
                        "items": order_items,
                        "total_price": final_total,
                        "payment_method": payment_method,
                        "status": "Új",
                        "notes": notes
                    }
                    save_order(new_order)
                    st.session_state.cart = {}
                    st.success("Sikeres megrendelés!")
                    st.rerun()

# --- TERMÉKEK RÁCS MEGJELENÍTŐ ---
def display_product_grid(df_to_show):
    available_products = df_to_show[df_to_show['Current Stock'] > 0] if 'Current Stock' in df_to_show.columns else df_to_show
    if available_products.empty:
        st.info(t["no_products_found"])
        return

    cols = st.columns(3)
    for idx, row in available_products.reset_index().iterrows():
        with cols[idx % 3]:
            st.image(get_product_image(row.get("SKU", "")), use_container_width=True)
            st.markdown(f"**{row.get('Product Name', 'Termék')}**")
            p_price = row.get('Selling Price (€)', 0)
            st.write(f"Ár: **{p_price:.2f} €**")
            qty = st.number_input("Db", min_value=1, max_value=int(row.get('Current Stock', 10)), key=f"qty_{row.get('SKU', idx)}")
            if st.button("Kosárba", key=f"add_{row.get('SKU', idx)}"):
                sku = str(row.get("SKU"))
                st.session_state.cart[sku] = st.session_state.cart.get(sku, 0) + qty
                st.success("Hozzáadva!")
                st.rerun()

# --- FEJLÉC ÉS NAVIGÁCIÓ ---
cart_count = sum(st.session_state.cart.values())
cart_label = f"🛒 {t.get('cart_title', 'Kosár')} ({cart_count})"
pages = [
    ("home", t.get("nav_home", "Főoldal")),
    ("products", t.get("nav_products", "Termékek")),
    ("categories", t.get("nav_categories", "Kategóriák")),
    ("cart", cart_label),
    ("about", t.get("nav_about", "Rólunk")),
    ("terms", t.get("nav_terms", "Szabályzatok")),
    ("admin", "Admin")
]

menu_col, lang_col = st.columns([8, 2])
with menu_col:
    nav_cols = st.columns(len(pages))
    for idx, (page_key, page_label) in enumerate(pages):
        with nav_cols[idx]:
            if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.session_state.current_page = page_key
                st.rerun()

with lang_col:
    lang_options = {"SK": "🇸🇰 SK", "EN": "🇬🇧 EN", "HU": "🇭🇺 HU"}
    selected_lang = st.selectbox("Nyelv", list(lang_options.keys()), format_func=lambda x: lang_options[x], label_visibility="collapsed")
    if selected_lang != st.session_state.selected_lang:
        st.session_state.selected_lang = selected_lang
        st.rerun()

st.divider()

# --- SIDEBAR (BEJELENTKEZÉS ÉS REGISZTRÁCIÓ) ---
with st.sidebar:
    if st.session_state.user:
        st.write(f"👋 Üdvözlünk, **{st.session_state.user.get('name', 'Felhasználó')}**!")
        if st.session_state.admin_logged_in:
            st.info("🔑 Admin jogosultság aktiválva")
        if st.button(t["logout_user"], key="user_logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.admin_logged_in = False
            st.rerun()
    else:
        with st.expander(f"👤 {t['login_title']}"):
            tab_log, tab_reg = st.tabs([t["tab_login"], t["tab_register"]])
            with tab_log:
                l_email = st.text_input("E-mail", key="log_email")
                l_pass = st.text_input("Jelszó", type="password", key="log_pass")
                if st.button("Bejelentkezés", key="btn_login"):
                    users = load_users()
                    if l_email in users and users[l_email]["password"] == l_pass:
                        st.session_state.user = users[l_email]
                        if l_email == ADMIN_EMAIL:
                            st.session_state.admin_logged_in = True
                        st.success("Sikeres bejelentkezés!")
                        st.rerun()
                    else:
                        st.error("Hibás e-mail vagy jelszó!")
            with tab_reg:
                r_name = st.text_input("Név", key="reg_name")
                r_email = st.text_input("E-mail", key="reg_email")
                r_pass = st.text_input("Jelszó", type="password", key="reg_pass")
                r_phone = st.text_input("Telefon", key="reg_phone")
                r_addr = st.text_input("Cím", key="reg_addr")
                r_city = st.text_input("Város", key="reg_city")
                r_zip = st.text_input("Irányítószám", key="reg_zip")
                if st.button("Regisztráció", key="btn_reg"):
                    if r_email and r_pass and r_name:
                        users = load_users()
                        users[r_email] = {
                            "name": r_name, "email_key": r_email, "password": r_pass,
                            "phone": r_phone, "address": r_addr, "city": r_city, "zip": r_zip
                        }
                        save_users(users)
                        st.success("Regisztráció sikeres! Most bejelentkezhetsz.")
                    else:
                        st.error("Töltsd ki a kötelező mezőket!")

# --- OLDALAK MEGJELENÍTÉSE ---
current_p = st.session_state.get("page", "home").lower()

if current_p == "cart":
    render_checkout_page()
elif current_p == "products":
    st.title("📦 Termékek")
    display_product_grid(products_df)
elif current_p == "categories":
    st.title("🏷️ Kategóriák")
    if "Category" in products_df.columns:
        cats = products_df["Category"].dropna().unique()
        selected_cat = st.selectbox("Válassz kategóriát:", cats)
        display_product_grid(products_df[products_df["Category"] == selected_cat])
elif current_p == "about":
    st.title(f"ℹ️ {t['about_title']}")
    st.write(t["about_text"])
elif current_p == "terms":
    st.title(f"📜 {t['policies_title']}")
    st.markdown(t["shipping_text"])
elif current_p == "admin":
    st.title(f"⚙️ {t['admin_title']}")
    if not st.session_state.user or not st.session_state.admin_logged_in:
        st.warning("⚠️ Ehhez az oldalhoz adminisztrátori bejelentkezés szükséges! Jelentkezz be az admin e-mail címeddel az oldalsávban.")
    else:
        st.success(f"🔑 Adminisztrátorként bejelentkezve: {st.session_state.user['email_key']}")
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["📦 Raktárkészlet", "🛒 Rendelések", "🧾 Számlák", "⚙️ Banki adatok"])
        
        with admin_tab1:
            edited_df = st.data_editor(products_df, use_container_width=True)
            if st.button("💾 Mentés"):
                edited_df.to_excel("products.xlsx", index=False)
                st.success("Frissítve!")
        
        with admin_tab2:
            orders = load_orders()
            st.json(orders)
            
        with admin_tab3:
            orders = load_orders()
            approved = [o for o in orders if o.get("status") == "Jóváhagyva"]
            if not approved:
                st.info("Nincs jóváhagyott rendelés.")
            for idx, ord_item in enumerate(approved):
                pdf_buf = generate_pdf_invoice(ord_item)
                st.download_button(f"Számla letöltése ({ord_item['id']})", pdf_buf, f"Invoice_{ord_item['id']}.pdf", "application/pdf", key=f"dl_{idx}")
                
        with admin_tab4:
            curr = load_settings()
            with st.form("set_form"):
                iban = st.text_input("IBAN", value=curr.get("iban", ""))
                swift = st.text_input("SWIFT", value=curr.get("swift", ""))
                if st.form_submit_button("Mentés"):
                    curr.update({"iban": iban, "swift": swift})
                    save_settings(curr)
                    st.success("Elmentve!")
else:
    st.title(f"🏠 {t['welcome_title']}")
    st.write(t["welcome_sub"])
    display_product_grid(products_df)
