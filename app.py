from datetime import datetime
import os
import re
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Filipino Goods - Online Shop",
    page_icon="logo.png" if os.path.exists("logo.png") else "🇵🇭",
    layout="wide"
)

EXCEL_FILE = 'Inventory management spreadsheet base.xlsx'
INVOICES_DIR = 'invoices'
IMAGES_DIR = 'images'
LOGO_FILE = 'logo.png'
BANNER_FILE = 'hero_banner.png'
NO_IMAGE_URL = 'https://via.placeholder.com/300x200?text=No+Image'

if not os.path.exists(INVOICES_DIR):
    os.makedirs(INVOICES_DIR)

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# --- SEGÉDFÜGGVÉNY A TERMÉKKÉP MEGKERESÉSÉRE ---
def get_product_image(sku):
    sku_str = str(sku).strip()
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        img_path = os.path.join(IMAGES_DIR, f"{sku_str}{ext}")
        if os.path.exists(img_path):
            return img_path
    return NO_IMAGE_URL

# --- NYELVI SZÓTÁR (SK / EN / HU) ---
TEXTS = {
    "SK": {
        "nav_home": "🏠 Domov",
        "nav_products": "📦 Produkty",
        "nav_categories": "📂 Kategórie",
        "nav_about": "ℹ️ O nás",
        "nav_policies": "📜 Podmienky",
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
        "about_text": "Filipino Goods prináša autentické chute Filipín priamo na Slovensko a do strednej Európy. Ponúkame široký výber najobľúbenejších značiek, omáčok, sladkostí a nápojov.",
        "contact_info": "📍 Kontakt a adresa",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Slovensko",
        "policies_title": "📜 Obchodné podmienky & Pravidlá",
        "tab_shipping": "🚚 Doručenie",
        "tab_payment": "💳 Platba",
        "tab_privacy": "🔒 GDPR & Súkromie",
        "shipping_text": "- **Kuriér:** 2-4 pracovné dni.\n- **Poštovné:** Od 3.90 €. Pri objednávke nad 50 € je doprava ZADARMO!\n- **Osobný odber:** Bátorove Kosihy (po dohode).",
        "payment_text": "- **Bankový prevod:** Na základe vygenerovanej zálohovej faktúry.\n- **Dobierka:** Platba pri prevzatí (+1.50 €).",
        "privacy_text": "Vaše osobné údaje používame výhradne na spracovanie a doručenie vašej objednávky.",
        "checkout_title": "📋 Dokončenie objednávky",
        "customer_details": "📝 Údaje pre doručenie a fakturáciu",
        "name": "Meno a priezvisko / Názov firmy*",
        "email": "E-mail*",
        "phone": "Telefón*",
        "address_label": "Adresa (Ulica, PSČ, Mesto)*",
        "ico": "IČO / DIČ (voliteľné)",
        "submit_order": "✅ Odeslať objednávku",
        "success_msg": "🎉 Objednávka bola úspešne prijatá!",
        "download_inv": "📄 Stiahnuť faktúru (PDF)",
        "back": "⬅️ Späť"
    },
    "EN": {
        "nav_home": "🏠 Home",
        "nav_products": "📦 Products",
        "nav_categories": "📂 Categories",
        "nav_about": "ℹ️ About Us",
        "nav_policies": "📜 Policies",
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
        "about_text": "Filipino Goods brings the authentic flavors of the Philippines directly to Slovakia and Central Europe. We offer a wide selection of top brands, sauces, sweets, and beverages.",
        "contact_info": "📍 Contact Information",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Slovakia",
        "policies_title": "📜 Terms & Policies",
        "tab_shipping": "🚚 Delivery",
        "tab_payment": "💳 Payment",
        "tab_privacy": "🔒 Privacy & GDPR",
        "shipping_text": "- **Courier Delivery:** 2-4 business days.\n- **Shipping Fee:** From €3.90. FREE shipping on orders over €50!\n- **Personal Pickup:** Bátorove Kosihy (by appointment).",
        "payment_text": "- **Bank Transfer:** Based on the generated proforma invoice.\n- **Cash on Delivery:** Pay upon delivery (+€1.50).",
        "privacy_text": "We use your personal data exclusively to process and deliver your order.",
        "checkout_title": "📋 Complete Your Order",
        "customer_details": "📝 Delivery & Billing Address",
        "name": "Full Name / Company Name*",
        "email": "E-mail*",
        "phone": "Phone*",
        "address_label": "Address (Street, ZIP, City)*",
        "ico": "Company ID / Tax ID (optional)",
        "submit_order": "✅ Place Order",
        "success_msg": "🎉 Order successfully placed!",
        "download_inv": "📄 Download Invoice (PDF)",
        "back": "⬅️ Back"
    },
    "HU": {
        "nav_home": "🏠 Főoldal",
        "nav_products": "📦 Termékek",
        "nav_categories": "📂 Kategóriák",
        "nav_about": "ℹ️ Rólunk",
        "nav_policies": "📜 Szabályzatok",
        "nav_admin": "⚙️ Adminisztráció",
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
        "about_text": "A Filipino Goods elhozza a Fülöp-szigetek autentikus ízeit Szlovákiába és Közép-Európába. Kínálatunkban megtalálhatóak a legnépszerűbb márkák, szószok, édességek és hűsítő italok.",
        "contact_info": "📍 Kapcsolat és Cím",
        "address": "Hlavná 123, 946 34 Bátorove Kosihy, Szlovákia",
        "policies_title": "📜 Vásárlási Feltételek & Szabályzatok",
        "tab_shipping": "🚚 Szállítás",
        "tab_payment": "💳 Fizetés",
        "tab_privacy": "🔒 Adatvédelem & GDPR",
        "shipping_text": "- **Futárszolgálat:** 2-4 munkanap.\n- **Szállítási díj:** 3.90 €-tól. 50 € feletti rendelés esetén INGYENES!\n- **Személyes átvétel:** Bátorove Kosihy (egyeztetés alapján).",
        "payment_text": "- **Banki átutalás:** A kiállított díjbekérő alapján.\n- **Utánvét:** Fizetés átvételkor a futárnál (+1.50 €).",
        "privacy_text": "Személyes adatait kizárólag a megrendelés feldolgozásához és kiszállításához használjuk fel.",
        "checkout_title": "📋 Rendelés Befejezése",
        "customer_details": "📝 Szállítási és Számlázási Adatok",
        "name": "Név / Cégnév*",
        "email": "E-mail*",
        "phone": "Telefonszám*",
        "address_label": "Cím (Utca, házszám, irányítószám, város)*",
        "ico": "Cégszám / Adószám (opcionális)",
        "submit_order": "✅ Rendelés Elküldése",
        "success_msg": "🎉 Rendelését sikeresen rögzítettük!",
        "download_inv": "📄 Díjbekérő / Számla letöltése (PDF)",
        "back": "⬅️ Vissza"
    }
}

# --- ÁR TISZTÍTÁS ---
def clean_price(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(',', '.').replace('€', '').strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    return float(match.group()) if match else 0.0

# --- EXCEL ADATOK BETÖLTÉSE ---
@st.cache_data(ttl=2)
def load_products():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()
    xls = pd.ExcelFile(EXCEL_FILE)
    sheet_name = 'Current Stock' if 'Current Stock' in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
    df = df.dropna(subset=['SKU', 'Product Name']).copy()
    df['SKU'] = df['SKU'].astype(str).str.strip()
    
    selling_col = next((c for c in df.columns if 'selling price' in c.lower()), None)
    df['Selling Price (€)'] = df[selling_col].apply(clean_price) if selling_col else 0.0

    supplier_col = next((c for c in df.columns if any(k in c.lower() for k in ['supplier', 'buying', 'unit price', 'beszállítói', 'nettó'])), None)
    df['Buying Price (€)'] = df[supplier_col].apply(clean_price) if supplier_col else df['Selling Price (€)']

    stock_col = next((c for c in df.columns if any(k in c.lower() for k in ['stock', 'pieces', 'sklad'])), None)
    df['Current Stock'] = pd.to_numeric(df[stock_col], errors='coerce').fillna(0).astype(int) if stock_col else 0

    cat_col = next((c for c in df.columns if any(k in c.lower() for k in ['category', 'kategória', 'kategoria', 'type'])), None)
    df['Category'] = df[cat_col].astype(str).str.strip() if cat_col else 'General'

    return df

@st.cache_data(ttl=2)
def load_sales_log():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()
    xls = pd.ExcelFile(EXCEL_FILE)
    return pd.read_excel(xls, sheet_name='Sales Log') if 'Sales Log' in xls.sheet_names else pd.DataFrame()

# Session States
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "page_view" not in st.session_state:
    st.session_state.page_view = "shop"
if "current_nav" not in st.session_state:
    st.session_state.current_nav = None

# --- SIDEBAR NYELVVÁLASZTÓ ---
if os.path.exists(LOGO_FILE):
    st.sidebar.image(LOGO_FILE, use_container_width=True)

lang_choice = st.sidebar.selectbox("🌐 Language / Nyelv / Jazyk:", ["🇸🇰 Slovenčina", "🇬🇧 English", "🇭🇺 Magyar"])

lang_code = "SK"
if "English" in lang_choice:
    lang_code = "EN"
elif "Magyar" in lang_choice:
    lang_code = "HU"

t = TEXTS[lang_code]

# NAVIGÁCIÓS MENÜ
nav_options = [
    t["nav_home"],
    t["nav_products"],
    t["nav_categories"],
    t["nav_about"],
    t["nav_policies"],
    t["nav_admin"]
]

if st.session_state.current_nav not in nav_options:
    st.session_state.current_nav = t["nav_home"]

page = st.sidebar.radio("📌 Navigation:", nav_options, index=nav_options.index(st.session_state.current_nav), key="nav_radio")
st.session_state.current_nav = page

df_products = load_products()

# --- TERMÉKEK MEGJELENÍTÉSE RÁCSBAN (KÉPEKKEL) ---
def display_product_grid(products_df):
    if products_df.empty:
        st.info("No products found.")
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
                    st.success(f"Added! ({quantity}x)")
            else:
                st.error(t['out_of_stock'])
            st.divider()

# --- SIDEBAR KOSÁR ---
def display_sidebar_cart():
    st.sidebar.divider()
    st.sidebar.header(t['cart_title'])

    if not st.session_state.cart:
        st.sidebar.info(t['cart_empty'])
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
                
                st.sidebar.write(f"**{p_name}**")
                st.sidebar.write(f"{qty} ks x {p_price:.2f} € = **{total_p:.2f} €**")
                if st.sidebar.button(t['remove'], key=f"del_{sku}"):
                    del st.session_state.cart[sku]
                    st.rerun()
                st.sidebar.divider()
                
        st.sidebar.markdown(f"### **{t['total']}: {grand_total:.2f} €**")
        if st.sidebar.button(t['checkout_btn'], type="primary", use_container_width=True):
            st.session_state.page_view = "checkout"
            st.rerun()

# --- PDF GENERÁLÁS ---
def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ArialCustom', 'C:\\Windows\\Fonts\\arial.ttf'))
        pdfmetrics.registerFont(TTFont('ArialCustom-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
        return 'ArialCustom', 'ArialCustom-Bold'
    except Exception:
        return 'Helvetica', 'Helvetica-Bold'

def generate_pdf_invoice(szamlaszam, datum, nev, ico, adresa, email, tel, polozky, sum_total):
    pdf_path = os.path.join(INVOICES_DIR, f"faktura_{szamlaszam}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    font_reg, font_bold = register_fonts()

    if os.path.exists(LOGO_FILE):
        try:
            c.drawImage(LOGO_FILE, 450, height - 100, width=90, height=90, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFont(font_bold, 18)
    c.drawString(50, height - 50, "FILIPINO GOODS")
    c.setFont(font_bold, 12)
    c.drawString(50, height - 68, "FAKTÚRA / INVOICE / SZÁMLA")
    
    c.setFont(font_reg, 10)
    c.drawString(50, height - 88, f"No: {szamlaszam} | Date: {datum}")

    c.setFont(font_bold, 11)
    c.drawString(50, height - 125, "Supplier / Dodávateľ / Szállító:")
    c.setFont(font_reg, 10)
    c.drawString(50, height - 140, "Filipino Goods s.r.o.")
    c.drawString(50, height - 155, "Hlavná 123, 946 34 Bátorove Kosihy")

    c.setFont(font_bold, 11)
    c.drawString(300, height - 125, "Customer / Odberateľ / Vevő:")
    c.setFont(font_reg, 10)
    c.drawString(300, height - 140, f"Name: {nev}")
    if ico:
        c.drawString(300, height - 155, f"ID: {ico}")
    c.drawString(300, height - 170, f"Address: {adresa}")
    c.drawString(300, height - 185, f"Email: {email}")

    c.line(50, height - 205, width - 50, height - 205)
    c.setFont(font_bold, 9)
    c.drawString(50, height - 220, "SKU")
    c.drawString(150, height - 220, "Item / Položka / Termék")
    c.drawString(350, height - 220, "Qty")
    c.drawString(410, height - 220, "Price (€)")
    c.drawString(480, height - 220, "Total (€)")
    c.line(50, height - 230, width - 50, height - 230)

    y = height - 250
    c.setFont(font_reg, 9)
    for p in polozky:
        c.drawString(50, y, str(p['sku']))
        c.drawString(150, y, str(p['nev'])[:35])
        c.drawString(350, y, f"{p['ks']} ks")
        c.drawString(410, y, f"{p['ar']:.2f} €")
        c.drawString(480, y, f"{p['spolu']:.2f} €")
        y -= 20

    c.line(50, y, width - 50, y)
    y -= 25
    c.setFont(font_bold, 12)
    c.drawString(350, y, f"Total: {sum_total:.2f} €")
    c.save()
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    return pdf_bytes, pdf_path

def process_order_in_excel(cart_items, order_no, customer_info):
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        df_stock = pd.read_excel(xls, sheet_name='Current Stock')
        df_sales = pd.read_excel(xls, sheet_name='Sales Log') if 'Sales Log' in xls.sheet_names else pd.DataFrame()

        new_sales_rows = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        for item in cart_items:
            sku = item['sku']
            qty = item['ks']
            p_name = item['nev']

            mask = df_stock['SKU'].astype(str).str.strip() == sku
            if mask.any() and 'Current Stock' in df_stock.columns:
                df_stock.loc[mask, 'Current Stock'] = df_stock.loc[mask, 'Current Stock'] - qty

            new_sales_rows.append({
                'SKU': sku,
                'Product Name': p_name,
                'Date': now_str,
                'Quantity Sold': qty,
                'Customer Notes / Order No.': f"Obj: #{order_no} | {customer_info}"
            })

        df_updated_sales = pd.concat([df_sales, pd.DataFrame(new_sales_rows)], ignore_index=True)

        sheet_data = {}
        for sheet in xls.sheet_names:
            if sheet == 'Current Stock':
                sheet_data[sheet] = df_stock
            elif sheet == 'Sales Log':
                sheet_data[sheet] = df_updated_sales
            else:
                sheet_data[sheet] = pd.read_excel(xls, sheet_name=sheet)

        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            for sheet_name, df_sheet in sheet_data.items():
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)

        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return False

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
                cart_items.append({"sku": sku, "nev": p_name, "ar": p_price, "ks": qty, "spolu": total_p})

        summary_df = pd.DataFrame(cart_items)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.markdown(f"### **{t['total']}: {grand_total:.2f} €**")
        st.divider()

        st.subheader(t['customer_details'])
        with st.form("checkout_form"):
            col1, col2 = st.columns(2)
            with col1:
                o_nev = st.text_input(t['name'])
                o_email = st.text_input(t['email'])
                o_tel = st.text_input(t['phone'])
            with col2:
                o_adresa = st.text_input(t['address_label'])
                o_ico = st.text_input(t['ico'])

            submit_order = st.form_submit_button(t['submit_order'], type="primary", use_container_width=True)

        if submit_order:
            if not o_nev or not o_adresa or not o_email:
                st.error("Please fill in all required fields!")
            else:
                szamlaszam = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
                datum = datetime.now().strftime("%Y-%m-%d")
                customer_info = f"{o_nev}, {o_email}, {o_tel}"

                if process_order_in_excel(cart_items, szamlaszam, customer_info):
                    pdf_bytes, pdf_path = generate_pdf_invoice(
                        szamlaszam, datum, o_nev, o_ico, o_adresa, o_email, o_tel, cart_items, grand_total
                    )
                    st.balloons()
                    st.success(t['success_msg'])
                    st.download_button(
                        label=t['download_inv'],
                        data=pdf_bytes,
                        file_name=f"faktura_{szamlaszam}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                    st.session_state.cart = {}

else:
    # 1. 🏠 HOME (FŐOLDAL)
    if page == t["nav_home"]:
        if os.path.exists(BANNER_FILE):
            # CSS: Egyedi gombok a képre pozicionálva
            st.markdown(
                """
                <style>
                .banner-wrapper {
                    position: relative;
                    width: 100%;
                    display: inline-block;
                }
                .banner-img {
                    width: 100%;
                    height: auto;
                    display: block;
                }
                .btn-overlay-shop {
                    position: absolute;
                    top: 46%;
                    left: 5.8%;
                    width: 12.3%;
                    height: 7%;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    z-index: 99;
                }
                .btn-overlay-story {
                    position: absolute;
                    top: 56.2%;
                    left: 5.8%;
                    width: 12.3%;
                    height: 7%;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    z-index: 99;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Megjelenítjük a képet és fölé tesszük a láthatatlan, kattintható mezőket
            st.markdown(
                f"""
                <div class="banner-wrapper">
                    <img src="app/static/{BANNER_FILE}" class="banner-img" onerror="this.src='{BANNER_FILE}';">
                </div>
                """,
                unsafe_allow_html=True
            )

            # Streamlit gombok elhelyezése a kép alatt látható és kattintható formában
            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                if st.button("🛍️ SHOP NOW (Katalógus)", type="primary", use_container_width=True):
                    st.session_state.current_nav = t["nav_products"]
                    st.rerun()
            with c2:
                if st.button("🤍 OUR STORY (Rólunk)", use_container_width=True):
                    st.session_state.current_nav = t["nav_about"]
                    st.rerun()

        else:
            st.title(t["welcome_title"])
            st.caption(t["welcome_sub"])

        st.divider()

        # Vásárlási előnyök (Ikonsor)
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.success("🚚 **Gyors Szállítás**\n\n2-4 munkanapon belül, 50 € felett ingyenes!")
        with col_b2:
            st.info("💯 **100% Autentikus**\n\nKözvetlenül a legnépszerűbb márkáktól.")
        with col_b3:
            st.warning("💳 **Biztonságos Fizetés**\n\nBanki átutalás vagy utánvét.")

        st.divider()

        # Kiemelt Termékek
        st.subheader(t["featured_title"])
        display_product_grid(df_products.head(6))
        display_sidebar_cart()

    # 2. 📦 PRODUCTS
    elif page == t["nav_products"]:
        st.title(t["all_products"])
        search_query = st.text_input(t["search_ph"], "")
        filtered_df = df_products[
            df_products['Product Name'].str.contains(search_query, case=False, na=False) |
            df_products['SKU'].str.contains(search_query, case=False, na=False)
        ] if search_query else df_products

        display_product_grid(filtered_df)
        display_sidebar_cart()

    # 3. 📂 CATEGORIES
    elif page == t["nav_categories"]:
        st.title(t["nav_categories"])
        cats = [t["cat_all"]] + sorted(list(df_products['Category'].unique()))
        selected_cat = st.selectbox(t["category_select"], cats)
        filtered_df = df_products if selected_cat == t["cat_all"] else df_products[df_products['Category'] == selected_cat]
        display_product_grid(filtered_df)
        display_sidebar_cart()

    # 4. ℹ️ ABOUT US
    elif page == t["nav_about"]:
        st.title(t["about_title"])
        st.write(t["about_text"])
        st.subheader(t["contact_info"])
        st.write(f"- 📍 {t['address']}\n- 📧 info@filipinogoods.sk\n- 📞 +421 900 123 456")
        display_sidebar_cart()

    # 5. 📜 POLICIES
    elif page == t["nav_policies"]:
        st.title(t["policies_title"])
        tab1, tab2, tab3 = st.tabs([t["tab_shipping"], t["tab_payment"], t["tab_privacy"]])
        with tab1:
            st.markdown(t["shipping_text"])
        with tab2:
            st.markdown(t["payment_text"])
        with tab3:
            st.markdown(t["privacy_text"])
        display_sidebar_cart()

    # 6. ⚙️ ADMIN
    elif page == t["nav_admin"]:
        st.title("⚙️ Admin Dashboard")
        tab1, tab2 = st.tabs(["📦 Stock & Prices", "📑 Orders & Invoices"])
        with tab1:
            st.dataframe(df_products, use_container_width=True)
        with tab2:
            df_sales = load_sales_log()
            st.dataframe(df_sales, use_container_width=True)
            invoice_files = [f for f in os.listdir(INVOICES_DIR) if f.endswith('.pdf')]
            if invoice_files:
                selected_pdf = st.selectbox("Download Invoice:", sorted(invoice_files, reverse=True))
                with open(os.path.join(INVOICES_DIR, selected_pdf), "rb") as pdf_file:
                    st.download_button("📥 Download PDF", data=pdf_file.read(), file_name=selected_pdf, mime="application/pdf")
