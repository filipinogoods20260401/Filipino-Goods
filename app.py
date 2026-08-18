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
import stripe  # <-- Stripe modul importálása

# Stripe API kulcs betöltése a beállított Secrets-ből
stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "")

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Filipino Goods",
    page_icon="🇵🇭",
    layout="wide",
    initial_sidebar_state="collapsed" # Mobilon alapból csukja be az oldalsávot
)

st.markdown("""
<style>
    /* Menü gombok törésmentesítése és egységesítése */
    div[data-testid="stHorizontalBlock"] button {
        white-space: nowrap !important;
        word-break: normal !important;
        padding: 4px 10px !important;
        font-size: 13px !important;
        min-height: 40px !important;
    }
    
    /* Mobilon gördíthető gombsor */
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

# --- ORDERS ADATBÁZIS & FAKTÚRA GENERÁLÓ ---
ORDERS_FILE = "orders.json"
SETTINGS_FILE = "settings.json"

# --- BANKI ÉS CÉGADATOK KEZELÉSE ---
def load_settings():
    default_settings = {
        "iban": "SK89 0000 0000 1234 5678",
        "swift": "SUBASKBX",
        "company_name": "Saját Cég s.r.o.",
        "company_address": "Mestská 12, 946 03 Kolárovo",
        "ico": "12345678",
        "dic": "2021234567",
        "ic_dph": "",  # Ha nem ÁFA fizető, hagyd üresen
        "register_info": "Zapísaný v OR Okresného súdu Nitra, oddiel: Sro, vložka č. 12345/N",
        "is_dph_payer": False  # True esetén ÁFA fizető
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
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_order(order_data):
    orders = load_orders()
    orders.append(order_data)
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

# --- UNICODE BETŰTÍPUSOK BEÁLLÍTÁSA ---
def setup_pdf_fonts():
    font_regular = "DejaVuSans.ttf"
    font_bold = "DejaVuSans-Bold.ttf"
    font_italic = "DejaVuSans-Oblique.ttf"
    
    # Ha helyileg még nem léteznek a betűtípusok, letöltjük őket
    if not os.path.exists(font_regular):
        urllib.request.urlretrieve(
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf", 
            font_regular
        )
    if not os.path.exists(font_bold):
        urllib.request.urlretrieve(
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf", 
            font_bold
        )
    if not os.path.exists(font_italic):
        urllib.request.urlretrieve(
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Oblique.ttf", 
            font_italic
        )

# --- UNICODE BETŰTÍPUS BEÁLLÍTÁSA (HELYI FÁJLBÓL) ---
def setup_pdf_fonts():
    font_path = "DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))
    else:
        print("A DejaVuSans.ttf fájl nem található, alapértelmezett betűtípus használata.")

setup_pdf_fonts()

# --- FAKTÚRA GENERÁLÓ FÜGGVÉNY ---
def generate_pdf_invoice(order):
    settings = load_settings()
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    font_name = "DejaVu" if "DejaVu" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    
    # 1. FEJLÉC ÉS SZÁMLASZÁM
    p.setFont(font_name, 13)
    p.drawString(50, 750, f"FAKTÚRA - DAŇOVÝ DOKLAD č. {order['id']}")
    
    # Dátumok (jobbra igazítva)
    p.setFont(font_name, 8)
    p.drawString(350, 755, f"Dátum vyhotovenia (Kiállítás): {order['date']}")
    p.drawString(350, 742, f"Dátum dodania (Teljesítés): {order['date']}")
    
    # 2. ELADÓ ÉS VEVŐ ADATAI
    p.setFont(font_name, 9)
    p.drawString(50, 715, "DODÁVATEĽ (Eladó):")
    p.drawString(320, 715, "ODBERATEĽ (Vevő):")
    
    p.setFont(font_name, 8)
    # Eladó adatai (X = 50)
    p.drawString(50, 700, f"{settings['company_name']}")
    p.drawString(50, 688, f"{settings['company_address']}")
    p.drawString(50, 676, f"IČO: {settings['ico']} | DIČ: {settings['dic']}")
    if settings.get('ic_dph'):
        p.drawString(50, 664, f"IČ DPH: {settings['ic_dph']}")
    else:
        p.drawString(50, 664, "Dodávateľ nie je platiteľom DPH")
    
    # Hosszú cégbejegyzési szöveg levágása / törése
    reg_text = str(settings.get('register_info', ''))
    p.drawString(50, 652, reg_text[:45])
    if len(reg_text) > 45:
        p.drawString(50, 642, reg_text[45:90])
    
    # Vevő adatai (X = 320 - több hely az eladónak)
    p.drawString(320, 700, f"{order['name']}")
    p.drawString(320, 688, f"{order['address']}")
    p.drawString(320, 676, f"{order['city']}, {order['zip']}")
    p.drawString(320, 664, f"E-mail: {order['email']}")
    p.drawString(320, 652, f"Tel: {order['phone']}")
    
    p.line(50, 630, 550, 630)
    
    # 3. FIZETÉSI ADATOK
    p.setFont(font_name, 8)
    p.drawString(50, 615, f"Spôsob úhrady (Fizetés): {order['payment']}")
    p.drawString(320, 615, f"IBAN: {settings['iban']}")
    p.drawString(320, 603, f"SWIFT/BIC: {settings['swift']}")
    p.drawString(320, 591, f"Variabilný symbol: {order['id']}")
    
    p.line(50, 580, 550, 580)
    
    # 4. TÉTELEK TÁBLÁZATA
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
    
    # 5. ÖSSZESÍTÉS ÉS ZÁRADÉKOK
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
        "lang_label": "Jazyk:",
        "nav_home": "Domov",
        "nav_products": "Produkty",
        "nav_categories": "Kategórie",
        "nav_about": "O nás",
        "nav_policies": "Podmienky",
        "nav_terms": "Podmienky",
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
        "feature_payment_desc": "Bankový prevod alebo dobierka.",
        "login_title": "Prihlásenie / Registrácia",
        "tab_login": "Prihlásenie",
        "tab_register": "Registrácia",
        "reg_success": "Úspešná registrácia! Teraz sa môžete prihlásiť.",
        "login_success": "Vitajte späť,",
        "login_error": "Nesprávny e-mail alebo heslo!",
        "user_exists": "S týmto e-mailom už existuje účet!",
        "logout_user": "Odhlásiť sa",
        "autofill_notice": "Vaše údaje boli automaticky vyplnené z účtu."
    },
    "EN": {
        "lang_label": "Language:",
        "nav_home": "Home",
        "nav_products": "Products",
        "nav_categories": "Categories",
        "nav_about": "About Us",
        "nav_policies": "Policies",
        "nav_terms": "Policies",
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
        "feature_payment_desc": "Bank transfer or cash on delivery.",
        "login_title": "Customer Login / Register",
        "tab_login": "Login",
        "tab_register": "Register",
        "reg_success": "Registration successful! You can now log in.",
        "login_success": "Welcome back,",
        "login_error": "Incorrect email or password!",
        "user_exists": "An account with this email already exists!",
        "logout_user": "Logout",
        "autofill_notice": "Your billing details were automatically filled from your profile."
    },
    "HU": {
        "lang_label": "Nyelv:",
        "nav_home": "Főoldal",
        "nav_products": "Termékek",
        "nav_categories": "Kategóriák",
        "nav_about": "Rólunk",
        "nav_policies": "Szabályzatok",
        "nav_terms": "Szabályzatok",
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
        "feature_payment_desc": "Banki átutalás vagy utánvét.",
        "login_title": "Vásárlói Bejelentkezés / Regisztráció",
        "tab_login": "Bejelentkezés",
        "tab_register": "Regisztráció",
        "reg_success": "Sikeres regisztráció! Most már bejelentkezhetsz.",
        "login_success": "Üdvözlünk újra,",
        "login_error": "Helytelen e-mail cím vagy jelszó!",
        "user_exists": "Ezzel az e-mail címmel már regisztráltak!",
        "logout_user": "Kijelentkezés",
        "autofill_notice": "A vásárlói adataidat automatikusan kitöltöttük a fiókodból."
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

# Megadod az admin e-mail címedet
ADMIN_EMAIL = "jenoladanyi@filipinogoods.sk"

if "user" not in st.session_state:
    st.session_state.user = None

t = TEXTS[st.session_state.selected_lang]

# --- ADATOK BETÖLTÉSE ---
@st.cache_data
def load_products():
    file_path = "Inventory management spreadsheet base.xlsx"
    if not os.path.exists(file_path):
        file_path = "products.xlsx"

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
    df = df.rename(columns=column_mapping)
    return df

products_df = load_products()

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

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

# --- CHECKOUT / KOSÁR FÜGGVÉNY ---
def render_checkout_page():
    st.divider()
    st.title("🛒 Kosár és Fizetés / Košík a Platba")

    if not st.session_state.cart:
        st.warning("A kosár jelenleg üres. / Váš košík je prázdny.")
        if st.button("⬅️ Vissza a vásárláshoz / Späť do obchodu", key="btn_back_empty_cart"):
            st.session_state.show_checkout = False
            st.session_state.page = "home"
            st.session_state.current_page = "home"
            st.rerun()
    else:
        # Tétel törlése a kosárból (ha a törlés gombra kattintottak)
        if "delete_sku" in st.session_state:
            sku_to_delete = st.session_state.delete_sku
            if sku_to_delete in st.session_state.cart:
                del st.session_state.cart[sku_to_delete]
            del st.session_state.delete_sku
            st.rerun()

        # Kosár elemeinek összeállítása és végösszeg számítása
        cart_total = 0.0
        order_items = []
        
        for sku, qty in list(st.session_state.cart.items()):
            product_row = products_df[products_df["SKU"].astype(str) == str(sku)]
            if not product_row.empty:
                p_name = product_row.iloc[0]["Product Name"]
                p_price = float(product_row.iloc[0]["Selling Price (€)"])
                subtotal = p_price * qty
                cart_total += subtotal
                order_items.append({
                    "sku": str(sku),
                    "name": p_name,
                    "qty": qty,
                    "subtotal": subtotal,
                    "price": p_price
                })

        eur_huf = get_eur_huf_rate()
        cart_huf = cart_total * eur_huf

        st.subheader("📋 Rendelés áttekintése / Prehľad objednávky")

        # Tételek kirajzolása törlés gombbal
        for item in order_items:
            sku = item['sku']
            col_name, col_qty, col_price, col_del = st.columns([4, 2, 2, 1])
            
            with col_name:
                st.write(f"**{item['name']}**  \n*(SKU: `{sku}`)*")
                
            with col_qty:
                st.write(f"{item['qty']} ks × {item['price']:.2f} €")
                
            with col_price:
                st.write(f"**{item['subtotal']:.2f} €**")
                
            with col_del:
                if st.button("🗑️", key=f"del_{sku}"):
                    st.session_state.delete_sku = sku
                    st.rerun()

            st.divider()

        st.markdown(f"### **Összesen / Spolu: {cart_total:.2f} €**")
        st.caption(f"≈ {cart_huf:,.0f} HUF".replace(",", " "))
        st.caption(f"*(1 EUR = {eur_huf:.2f} HUF)*")
        st.divider()

        u = st.session_state.user or {}

        with st.form("checkout_form"):
            st.subheader("🚚 Szállítási adatok (Kizárólag Szlovákia)")
            
            if st.session_state.user:
                st.info("Adatait automatikusan kitöltöttük a fiókjából.")

            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Név / Meno a Priezvisko *", value=u.get("name", ""))
                email = st.text_input("E-mail *", value=u.get("email_key", ""))
                phone = st.text_input("Telefonszám / Telefónne číslo *", value=u.get("phone", ""))
            with col_b:
                address = st.text_input("Utca, házszám / Ulica a číslo *", value=u.get("address", ""))
                city = st.text_input("Város / Mesto *", value=u.get("city", ""))
                zip_code = st.text_input("Irányítószám / PSČ *", value=u.get("zip", ""))

            st.selectbox("Ország / Krajina", ["Slovensko"], disabled=True)

            st.subheader("💳 Fizetési mód / Platobná metóda")
            payment_method = st.radio(
                "Válasszon fizetési opciót:",
                [
                    "💳 Online bankkártya (Stripe)",
                    "🏦 Banki átutalás (SEPA / Díjmentes)",
                    "🚚 Utánvét (+1.50 €)"
                ],
                key="checkout_payment_radio"
            )

            notes = st.text_area("Megjegyzés a rendeléshez / Poznámka", key="checkout_notes")
            submit = st.form_submit_button("Rendelés véglegesítése és fizetés ➔", type="primary", use_container_width=True)

            if submit:
                if not (name and email and phone and address and city and zip_code):
                    st.error("Kérjük, töltse ki az összes kötelező mezőt! / Prosím, vyplňte všetky povinné polia!")
                else:
                    is_cod = "Utánvét" in payment_method
                    cod_fee = 1.50 if is_cod else 0.0
                    final_total = cart_total + cod_fee
                    final_huf = final_total * eur_huf

                    # Készlet levonása
                    for sku, qty in st.session_state.cart.items():
                        idx = products_df[products_df["SKU"].astype(str) == str(sku)].index
                        if not idx.empty:
                            products_df.loc[idx, "Current Stock"] -= qty

                    try:
                        file_path = "Inventory management spreadsheet base.xlsx"
                        if not os.path.exists(file_path):
                            file_path = "products.xlsx"
                        products_df.to_excel(file_path, index=False)
                        st.cache_data.clear()
                    except Exception:
                        pass

                    # Rendelés elmentése
                    new_order = {
                        "id": f"ORD-{len(load_orders()) + 1001}",
                        "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "city": city,
                        "zip": zip_code,
                        "payment": payment_method,
                        "total": final_total,
                        "items": order_items
                    }
                    save_order(new_order)

                    # Kosár kiürítése sikeres rendelés után
                    st.session_state.cart = {}

                    st.success("A rendelés sikeresen rögzítve! / Objednávka bola úspešne vytvorená!")
                    st.divider()
                    st.subheader("💳 Fizetési információk / Informácie k platbe")

                    if "Online bankkártya" in payment_method:
                        try:
                            line_items = []
                            for item in order_items:
                                line_items.append({
                                    'price_data': {
                                        'currency': 'eur',
                                        'product_data': {
                                            'name': item['name'],
                                        },
                                        'unit_amount': int(round(item['price'] * 100)),
                                    },
                                    'quantity': item['qty'],
                                })

                            # Ha van utánvéti díj, hozzáadjuk a Stripe tételekhez is
                            if cod_fee > 0:
                                line_items.append({
                                    'price_data': {
                                        'currency': 'eur',
                                        'product_data': {'name': 'Utánvét kezelési díj / Poplatok za dobierku'},
                                        'unit_amount': int(round(cod_fee * 100)),
                                    },
                                    'quantity': 1,
                                })

                            YOUR_DOMAIN = "https://filipinogoods.streamlit.app"

                            checkout_session = stripe.checkout.Session.create(
                                payment_method_types=['card'],
                                line_items=line_items,
                                mode='payment',
                                customer_email=email,
                                success_url=f"{YOUR_DOMAIN}/?payment=success",
                                cancel_url=f"{YOUR_DOMAIN}/?payment=cancel",
                            )

                            st.info(f"Fizetendő összeg: **{final_total:.2f} €** (≈ **{final_huf:,.0f} HUF**)")
                            st.link_button(
                                "🔒 Kattintson ide a biztonságos Stripe bankkártyás fizetéshez ➔", 
                                checkout_session.url, 
                                type="primary", 
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Hiba történt a Stripe fizetés indítása során: {e}")

                    elif "Banki átutalás" in payment_method:
                        bank_info = load_bank_details()
                        st.warning(
                            f"🏦 **Utaláshoz szükséges adatok / Údaje pre platbu:**\n\n"
                            f"- **Fizetendő összeg / Suma:** {final_total:.2f} € (≈ {final_huf:,.0f} HUF)\n"
                            f"- **IBAN:** {bank_info['iban']}\n"
                            f"- **SWIFT/BIC:** {bank_info['swift']}\n"
                            f"- **Közlemény / Variabilný symbol:** {email}\n\n"
                            f"*Magyarországi számláról indított átutalás esetén kérjük, EUR alapon (SEPA) küldje az összeget.*"
                        )
                    else:
                        st.info(f"🚚 A rendelés összegét (**{final_total:.2f} €** / ≈ **{final_huf:,.0f} HUF**) a futárnak tudja kifizetni átvételkor készpénzzel vagy kártyával.")

        if st.button("⬅️ Vissza a vásárláshoz", key="btn_back_checkout_bottom"):
            st.session_state.show_checkout = False
            st.session_state.page = "home"
            st.session_state.current_page = "home"
            st.rerun()

# --- RÁCS MEGJELENÍTŐ FÜGGVÉNY ---
def display_product_grid(df_to_show):
    available_products = df_to_show[df_to_show['Current Stock'] > 0]

    if available_products.empty:
        st.info(t["no_products_found"])
        return

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
    eur_huf = get_eur_huf_rate()
    
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
                p_huf = p_price * eur_huf

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
                st.caption(f"≈ {p_huf:,.0f} HUF".replace(",", " "))
                st.caption(f"*(1 EUR = {eur_huf:.2f} HUF)*")
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

# --- FELSŐ NAVIGÁCIÓS SÁV ---
cart_count = sum(st.session_state.cart.values()) if st.session_state.get("cart") else 0
cart_label = f"🛒 {t.get('cart_title', 'Kosár')} ({cart_count})" if cart_count > 0 else f"🛒 {t.get('cart_title', 'Kosár')}"

pages = [
    ("home", t.get("nav_home", "Főoldal")),
    ("products", t.get("nav_products", "Termékek")),
    ("categories", t.get("nav_categories", "Kategóriák")),
    ("cart", cart_label),
    ("about", t.get("nav_about", "Rólunk")),
    ("terms", t.get("nav_terms", "Szabályzatok")),
    ("admin", "Admin")
]

# CSS: Megakadályozza a szavak elvágását, és mobilon görgethetővé teszi a menüt
st.markdown("""
<style>
    div[data-testid="column"] button {
        white-space: nowrap !important;
        word-break: normal !important;
        padding: 6px 12px !important;
    }
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 10px;
        }
        div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) > div {
            flex: 0 0 auto !important;
            min-width: max-content !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Két fő rész: Navigációs gombok (balra) + Nyelvválasztó (jobbra)
menu_col, lang_col = st.columns([8, 2])

with menu_col:
    nav_cols = st.columns(len(pages))
    for idx, (page_key, page_label) in enumerate(pages):
        with nav_cols[idx]:
            is_active = (st.session_state.get("current_page") == page_key or st.session_state.get("page") == page_key)
            
            btn_type = "secondary"
            if is_active or (page_key == "cart" and cart_count > 0) or page_key == "admin":
                btn_type = "primary"

            if st.button(page_label, key=f"nav_{page_key}", type=btn_type, use_container_width=True):
                st.session_state.page = page_key
                st.session_state.current_page = page_key
                st.session_state.show_checkout = (page_key == "cart")
                st.rerun()

with lang_col:
    lang_options = {"SK": "🇸🇰 SK", "EN": "🇬🇧 EN", "HU": "🇭🇺 HU"}
    current_lang = st.session_state.get("selected_lang", "SK")
    
    selected_lang_code = st.selectbox(
        label=t.get("lang_label", "Nyelv:"),
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(current_lang) if current_lang in lang_options else 0,
        key="lang_select_box",
        label_visibility="collapsed"
    )
    
    if selected_lang_code != current_lang:
        st.session_state.selected_lang = selected_lang_code
        st.rerun()

st.divider()

# --- OLDALAK RENDERELÉSE ---
current_p = st.session_state.get("page", st.session_state.get("current_page", "home")).lower()

# 1. KOSÁR / CHECKOUT OLDAL
if current_p == "cart" or st.session_state.get("show_checkout", False):
    render_checkout_page()

# 2. FŐOLDAL
elif current_p == "home":
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

# 3. TERMÉKEK OLDAL
elif current_p == "products":
    st.title(f"🛍️ {t.get('nav_products', 'Termékek')}")
    display_product_grid(products_df)

# 4. KATEGÓRIÁK OLDAL
elif current_p == "categories":
    st.title(f"📁 {t.get('nav_categories', 'Kategóriák')}")

    # Egyedi kategóriák kigyűjtése
    raw_categories = sorted(products_df["Category"].dropna().unique().tolist())
    all_label = t.get("cat_all", "Všetky")

    # Kategória kiválasztás tárolása session_state-ben
    if "selected_cat" not in st.session_state:
        st.session_state.selected_cat = all_label

    # Kategória képek hozzárendelése (ha külön nevet használsz a fájloknál)
    category_images = {
        all_label: "images/cat_all.png",
    }

    # Kategóriák listája (az "Összes" opcióval az elején)
    cat_list = [all_label] + raw_categories

    # Oszlopok száma soronként (4 kategória kártya egy sorban)
    cols_per_row = 4
    for i in range(0, len(cat_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, cat_name in enumerate(cat_list[i:i + cols_per_row]):
            with cols[j]:
                # Automatikusan megkeresi a képet az images/ mappában a kategória neve alapján
                img_path = category_images.get(cat_name)
                if not img_path or not os.path.exists(img_path):
                    img_path = get_product_image(cat_name)

                st.image(img_path, use_container_width=True)
                
                # Gomb a kategória kiválasztásához
                is_active = (st.session_state.selected_cat == cat_name)
                btn_type = "primary" if is_active else "secondary"
                if st.button(cat_name, key=f"cat_btn_{i}_{j}", type=btn_type, use_container_width=True):
                    st.session_state.selected_cat = cat_name
                    st.rerun()

    st.divider()

    # Termékek szűrése és megjelenítése
    if st.session_state.selected_cat == all_label:
        display_product_grid(products_df)
    else:
        filtered_df = products_df[products_df["Category"] == st.session_state.selected_cat]
        display_product_grid(filtered_df)

# 5. RÓLUNK OLDAL
elif current_p == "about":
    st.title(f"ℹ️ {t.get('about_title', 'Rólunk')}")
    st.write(t["about_text"])
    st.divider()
    st.subheader(f"📍 {t['contact_info']}")
    st.write(f"**📍 Adresa / Cím:** {t['address']}")
    st.write("**✉️ E-mail:** jenoladanyi@filipinogoods.sk")
    st.write("**📞 Telefón / Telefon:** +421 908 813 657")

# 6. SZABÁLYZATOK OLDAL
elif current_p == "terms":
    st.title(f"📜 {t.get('policies_title', 'Szabályzatok')}")
    tab1, tab2, tab3 = st.tabs([t["tab_shipping"], t["tab_payment"], t["tab_privacy"]])
    with tab1:
        st.markdown(t["shipping_text"])
    with tab2:
        st.markdown(t["payment_text"])
    with tab3:
        st.markdown(t["privacy_text"])

# 7. ADMIN OLDAL
elif current_p == "admin":
    st.title(f"⚙️ {t['admin_title']}")

    # Ha nincs bejelentkezve VAGY nem admin az e-mail címe
    if not st.session_state.user or not st.session_state.admin_logged_in:
        st.warning("⚠️ Ehhez az oldalhoz adminisztrátori bejelentkezés szükséges! Kérjük, jelentkezz be az oldalsávban az admin e-mail címeddel.")
    else:
        st.success(f"🔑 Adminisztrátorként bejelentkezve: {st.session_state.user['email_key']}")
        st.divider()
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "📦 Raktárkészlet", 
            "🛒 Rendelések", 
            "🧾 Számlák (Faktúrák)", 
            "⚙️ Banki adatok"
        ])

        with admin_tab1:
                st.subheader("📊 Raktárkészlet kezelése")
                edited_df = st.data_editor(
                    products_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="admin_data_editor"
                )
                if st.button("💾 Módosítások mentése", type="primary", key="save_admin_changes"):
                    try:
                        file_path = "Inventory management spreadsheet base.xlsx"
                        if not os.path.exists(file_path):
                            file_path = "products.xlsx"
                        edited_df.to_excel(file_path, index=False)
                        st.session_state.products_df = edited_df
                        st.cache_data.clear()
                        st.success(t["stock_updated"])
                    except Exception as e:
                        st.error(f"Hiba a mentés során: {e}")
    
        # ------------------- 2. RENDELÉSEK FÜL -------------------
        with admin_tab2:
            st.subheader("🛒 Beérkezett rendelések kezelése")
            orders = load_orders()
            
            if not orders:
                st.info("Nincsenek beérkezett rendelések.")
            else:
                for idx, order in enumerate(orders):
                    # Státusz lekérése (alapértelmezetten 'Új')
                    status = order.get("status", "Új")
                    
                    with st.expander(f"📦 {order.get('id', f'ORD-{idx}')} - {order.get('customer', {}).get('name', 'N/A')} ({order.get('date', '')}) - Status: {status}"):
                        st.write(f"**Vevő:** {order.get('customer', {}).get('name')} ({order.get('customer', {}).get('email')}, {order.get('customer', {}).get('phone')})")
                        st.write(f"**Cím:** {order.get('customer', {}).get('address')}, {order.get('customer', {}).get('city')} {order.get('customer', {}).get('zip')}")
                        st.write(f"**Fizetés:** {order.get('payment_method', 'N/A')}")
                        
                        st.write("**Tételek:**")
                        for item in order.get("items", []):
                            st.write(f"- {item.get('name')} (SKU: {item.get('sku')}) - {item.get('qty')} ks x {item.get('price')} €")
                        
                        col_stat, col_del = st.columns([2, 1])
                        
                        with col_stat:
                            # Státusz módosítása
                            new_status = st.selectbox(
                                "Rendelés státusza:",
                                ["Új", "Jóváhagyva", "Elutasítva / Törölve"],
                                index=["Új", "Jóváhagyva", "Elutasítva / Törölve"].index(status) if status in ["Új", "Jóváhagyva", "Elutasítva / Törölve"] else 0,
                                key=f"status_select_{idx}"
                            )
                            if new_status != status:
                                order["status"] = new_status
                                save_order(orders)
                                st.success(f"Státusz frissítve: {new_status}")
                                st.rerun()

                        with col_del:
                            # Rendelés végleges törlése
                            if st.button("🗑️ Rendelés törlése", key=f"del_order_{idx}", type="primary"):
                                orders.pop(idx)
                                save_order(orders)
                                st.success("Rendelés sikeresen törölve!")
                                st.rerun()

        # ------------------- 3. SZÁMLÁK FÜL -------------------
        with admin_tab3:
            st.subheader("🧾 Jóváhagyott rendelések számlái")
            orders = load_orders()
            
            # Csak a jóváhagyott rendelések kiszűrése
            approved_orders = [o for o in orders if o.get("status") == "Jóváhagyva"]
            
            if not approved_orders:
                st.info("Jelenleg nincs jóváhagyott rendelés, amelyhez számla állna rendelkezésre. (A 'Rendelések' fülön állítsd a státuszt 'Jóváhagyva' állapotra!)")
            else:
                for idx, order in enumerate(approved_orders):
                    with st.expander(f"📄 Számla: {order.get('id', f'ORD-{idx}')} - {order.get('customer', {}).get('name', 'N/A')} ({order.get('total_price', 0)} €)"):
                        st.write(f"**Kiállítás dátuma:** {order.get('date')}")
                        st.write(f"**Vevő:** {order.get('customer', {}).get('name')}")
                        st.write(f"**Végösszeg:** {order.get('total_price', 0)} €")
                        
                        # Számla / PDF letöltési opció
                        # (A meglévő PDF generáló függvényed hívható meg itt)
                        if st.button("📄 Faktúra / Számla letöltése (PDF)", key=f"inv_btn_{idx}"):
                            st.info("Számla generálása folyamatban...")
    
            # ÚJ FÜL A BANKI ADATOK SZERKESZTÉSÉHEZ:
        with admin_tab4:
                st.subheader("⚙️ Cég- és Banki adatok (Faktúra beállítások)")
                current_settings = load_settings()
                
                with st.form("company_settings_form"):
                    st.markdown("**Cég adatai (Eladó / Dodávateľ)**")
                    c_name = st.text_input("Cégnév / Név", value=current_settings.get("company_name", ""))
                    c_addr = st.text_input("Székhely / Lakcím", value=current_settings.get("company_address", ""))
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        c_ico = st.text_input("IČO", value=current_settings.get("ico", ""))
                        c_dic = st.text_input("DIČ", value=current_settings.get("dic", ""))
                    with col_c2:
                        is_dph = st.checkbox("ÁFA fizető? (Platiteľ DPH)", value=current_settings.get("is_dph_payer", False))
                        c_ic_dph = st.text_input("IČ DPH (ha ÁFA fizető)", value=current_settings.get("ic_dph", ""))
                    
                    c_reg = st.text_area("Cégbírósági bejegyzés / Nyilvántartás", value=current_settings.get("register_info", ""))
                    
                    st.divider()
                    st.markdown("**Banki adatok**")
                    new_iban = st.text_input("IBAN számlaszám", value=current_settings.get("iban", ""))
                    new_swift = st.text_input("SWIFT / BIC kód", value=current_settings.get("swift", ""))
                    
                    save_settings_btn = st.form_submit_button("💾 Beállítások mentése", type="primary")
                    
                    if save_settings_btn:
                        updated_settings = {
                            "company_name": c_name,
                            "company_address": c_addr,
                            "ico": c_ico,
                            "dic": c_dic,
                            "ic_dph": c_ic_dph,
                            "is_dph_payer": is_dph,
                            "register_info": c_reg,
                            "iban": new_iban,
                            "swift": new_swift
                        }
                        save_settings(updated_settings)
                        st.success("A cég- és banki adatok sikeresen frissültek!")
                        st.rerun()
                    
# --- BEJELENTKEZÉS ÉS PROFIL (OLDALSÁV / SIDEBAR) ---
with st.sidebar:
    users = load_users()
    
    if st.session_state.user:
        st.success(f"👋 {t['login_success']} **{st.session_state.user['name']}**!")
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
                if st.button(t["login_btn"], key="btn_login_submit", use_container_width=True):
                    if l_email in users and users[l_email]["password"] == l_pass:
                        st.session_state.user = users[l_email]
                        st.session_state.user["email_key"] = l_email
                        
                        # AUTOMATIKUS ADMIN AZONOSÍTÁS
                        if l_email.lower().strip() == ADMIN_EMAIL.lower().strip():
                            st.session_state.admin_logged_in = True
                        else:
                            st.session_state.admin_logged_in = False
                            
                        st.rerun()
                    else:
                        st.error(t["login_error"])
            
            with tab_reg:
                with st.form("register_form"):
                    reg_name = st.text_input(f"{t['full_name']} *")
                    reg_email = st.text_input(f"{t['email']} *")
                    reg_password = st.text_input("Jelszó / Heslo *", type="password")
                    reg_phone = st.text_input(f"{t['phone']} *")
                    reg_address = st.text_input(f"{t['street_address']} *")
                    reg_city = st.text_input(f"{t['city']} *")
                    reg_zip = st.text_input(f"{t['zip_code']} *")
                    
                    reg_country = "Slovensko" 
                    
                    reg_submit = st.form_submit_button("Registrácia", type="primary", use_container_width=True)
                    
                    if reg_submit:
                        if not all([reg_name, reg_email, reg_password, reg_phone, reg_address, reg_city, reg_zip]):
                            st.error("Prosím, vyplňte všetky povinné polia!")
                        else:
                            st.session_state.user = {
                                "name": reg_name,
                                "email_key": reg_email,
                                "phone": reg_phone,
                                "address": reg_address,
                                "city": reg_city,
                                "zip": reg_zip,
                                "country": reg_country
                            }
                            st.success("Úspešná registrácia!")
                            st.rerun()
