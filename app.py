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
    page_icon="🇵🇭",
    layout="wide"
)

EXCEL_FILE = 'Inventory management spreadsheet base.xlsx'
INVOICES_DIR = 'invoices'
LOGO_FILE = 'logo.png'  # Helyezd el a logo.png fájlt a gyökérkönyvtárban

if not os.path.exists(INVOICES_DIR):
    os.makedirs(INVOICES_DIR)

# Segédfüggvény a szöveges árak számmá alakítására (pl. "3.99 €" -> 3.99)
def clean_price(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(',', '.').replace('€', '').strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    if match:
        return float(match.group())
    return 0.0

# --- ADATOK BETÖLTÉSE AZ EXCELBŐL ---
@st.cache_data(ttl=2)
def load_products():
    if not os.path.exists(EXCEL_FILE):
        st.error(f"Súbor '{EXCEL_FILE}' nebol nájdený! / Az Excel fájl nem található.")
        return pd.DataFrame()
    
    xls = pd.ExcelFile(EXCEL_FILE)
    
    sheet_name = 'Current Stock' if 'Current Stock' in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Oszlopnevek tisztítása (soremelések \n és extra szóközök eltávolítása)
    df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
    
    df = df.dropna(subset=['SKU', 'Product Name']).copy()
    df['SKU'] = df['SKU'].astype(str).str.strip()
    
    # 1. Vásárlói ár (Selling Price)
    selling_col = None
    for col in df.columns:
        if 'selling price' in col.lower():
            selling_col = col
            break
            
    if selling_col:
        df['Selling Price (€)'] = df[selling_col].apply(clean_price)
    else:
        df['Selling Price (€)'] = 0.0

    # 2. Beszállítói nettó ár (Suppliers Price (€) / Buying price / Unit Price)
    supplier_col = None
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['supplier', 'buying', 'unit price', 'beszállítói', 'nettó']):
            supplier_col = col
            break
            
    if supplier_col:
        df['Buying Price (€)'] = df[supplier_col].apply(clean_price)
    else:
        df['Buying Price (€)'] = df['Selling Price (€)']

    # 3. Raktárkészlet oszlop kinyerése
    stock_col = None
    for c in df.columns:
        if 'stock' in c.lower() or 'pieces' in c.lower() or 'sklad' in c.lower():
            stock_col = c
            break
            
    if stock_col:
        df['Current Stock'] = pd.to_numeric(df[stock_col], errors='coerce').fillna(0).astype(int)
    else:
        df['Current Stock'] = 0

    return df

@st.cache_data(ttl=2)
def load_sales_log():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()
    xls = pd.ExcelFile(EXCEL_FILE)
    if 'Sales Log' in xls.sheet_names:
        return pd.read_excel(xls, sheet_name='Sales Log')
    return pd.DataFrame()

# Munkamenet állapotok inicializálása
if "cart" not in st.session_state:
    st.session_state.cart = {}

if "page" not in st.session_state:
    st.session_state.page = "shop"

# --- ÉKEZETES BETŰTÍPUS REGISZTRÁLÁSA (PDF) ---
def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ArialCustom', 'C:\\Windows\\Fonts\\arial.ttf'))
        pdfmetrics.registerFont(TTFont('ArialCustom-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
        pdfmetrics.registerFont(TTFont('ArialCustom-Italic', 'C:\\Windows\\Fonts\\ariali.ttf'))
        return 'ArialCustom', 'ArialCustom-Bold', 'ArialCustom-Italic'
    except Exception:
        return 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

# --- AUTOMATA ZÁLOHOVÁ FAKTÚRA (PDF) GENERÁLÁSA ---
def generate_pdf_invoice(szamlaszam, datum, nev, ico, adresa, email, tel, polozky, sum_total):
    pdf_path = os.path.join(INVOICES_DIR, f"faktura_{szamlaszam}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    font_reg, font_bold, font_italic = register_fonts()

    # Logó elhelyezése a PDF számlán (ha létezik a logo.png)
    if os.path.exists(LOGO_FILE):
        try:
            c.drawImage(LOGO_FILE, 450, height - 100, width=90, height=90, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Fejléc
    c.setFont(font_bold, 18)
    c.drawString(50, height - 50, "FILIPINO GOODS")
    c.setFont(font_bold, 12)
    c.drawString(50, height - 68, "ZÁLOHOVÁ FAKTÚRA / DÍJBEKÉRŐ")
    
    c.setFont(font_reg, 10)
    c.drawString(50, height - 88, f"Číslo faktúry / Számlaszám: {szamlaszam}")
    c.drawString(50, height - 103, f"Dátum vystavenia / Kiállítás dátuma: {datum}")

    # Szállító adatai
    c.setFont(font_bold, 11)
    c.drawString(50, height - 135, "Dodávateľ / Szállító:")
    c.setFont(font_reg, 10)
    c.drawString(50, height - 150, "Filipino Goods s.r.o.")
    c.drawString(50, height - 165, "Hlavná 123, 946 34 Bátorove Kosihy")
    c.drawString(50, height - 180, "IČO: 12345678 | DIČ: 2021234567")

    # Vevő adatai
    c.setFont(font_bold, 11)
    c.drawString(300, height - 135, "Odberateľ / Vevő:")
    c.setFont(font_reg, 10)
    c.drawString(300, height - 150, f"Meno/Név: {nev}")
    if ico:
        c.drawString(300, height - 165, f"IČO/DIČ: {ico}")
    c.drawString(300, height - 180, f"Adresa/Cím: {adresa}")
    c.drawString(300, height - 195, f"E-mail: {email}")
    c.drawString(300, height - 210, f"Tel: {tel}")

    # Táblázat fejléce
    c.line(50, height - 230, width - 50, height - 230)
    c.setFont(font_bold, 9)
    c.drawString(50, height - 245, "SKU")
    c.drawString(150, height - 245, "Názov položky / Termék megnevezése")
    c.drawString(350, height - 245, "Množstvo")
    c.drawString(410, height - 245, "Cena/ks (€)")
    c.drawString(480, height - 245, "Spolu (€)")
    c.line(50, height - 255, width - 50, height - 255)

    y = height - 275
    c.setFont(font_reg, 9)
    for p in polozky:
        c.drawString(50, y, str(p['sku']))
        c.drawString(150, y, str(p['nev'])[:35])
        c.drawString(350, y, f"{p['ks']} ks")
        c.drawString(410, y, f"{p['ar']:.2f} €")
        c.drawString(480, y, f"{p['spolu']:.2f} €")
        y -= 20
        if y < 100:
            c.showPage()
            y = height - 50

    c.line(50, y, width - 50, y)
    y -= 25
    c.setFont(font_bold, 12)
    c.drawString(350, y, f"Celkom k úhrade / Összesen: {sum_total:.2f} €")

    c.setFont(font_italic, 9)
    c.drawString(50, 40, "Ďakujeme za Vašu objednávku! / Köszönjük a rendelését! - Filipino Goods")

    c.save()
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        
    return pdf_bytes, pdf_path

# --- EXCEL FRISSÍTÉSE RENDELÉSKOR ---
def process_order_in_excel(cart_items, order_no, customer_info):
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        df_stock = pd.read_excel(xls, sheet_name='Current Stock')
        
        if 'Sales Log' in xls.sheet_names:
            df_sales = pd.read_excel(xls, sheet_name='Sales Log')
        else:
            df_sales = pd.DataFrame(columns=['SKU', 'Product Name', 'Date', 'Quantity Sold', 'Customer Notes / Order No.'])

        new_sales_rows = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        for item in cart_items:
            sku = item['sku']
            qty = item['ks']
            p_name = item['nev']

            mask = df_stock['SKU'].astype(str).str.strip() == sku
            if mask.any():
                if 'Current Stock' in df_stock.columns:
                    df_stock.loc[mask, 'Current Stock'] = df_stock.loc[mask, 'Current Stock'] - qty

            new_sales_rows.append({
                'SKU': sku,
                'Product Name': p_name,
                'Date': now_str,
                'Quantity Sold': qty,
                'Customer Notes / Order No.': f"Obj: #{order_no} | {customer_info}"
            })

        df_new_sales = pd.DataFrame(new_sales_rows)
        df_updated_sales = pd.concat([df_sales, df_new_sales], ignore_index=True)

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
        st.error(f"Hiba történt az Excel frissítése közben: {e}")
        return False


# --- OLDALSÁV / REŽIM & LOGÓ ---
if os.path.exists(LOGO_FILE):
    st.sidebar.image(LOGO_FILE, use_container_width=True)

st.sidebar.title("🇵🇭 Filipino Goods")
mode = st.sidebar.radio("📌 Režim / Mód:", ["🛒 Obchod / Webshop", "⚙️ Admin / Správa"])

df_products = load_products()

# ==========================================
# ADMIN MÓD
# ==========================================
if mode == "⚙️ Admin / Správa":
    st.title("⚙️ Filipino Goods - Administrácia & Faktúry")
    
    tab1, tab2 = st.tabs(["📦 Raktárkészlet & Árak", "📑 Rendelések & Faktúrák"])

    with tab1:
        st.subheader("📊 Raktárkészlet és Árak összehasonlítása")
        if not df_products.empty:
            cols_to_show = ['SKU', 'Product Name', 'Buying Price (€)', 'Selling Price (€)', 'Current Stock']
            available_cols = [c for c in cols_to_show if c in df_products.columns]
            
            admin_df = df_products[available_cols].copy()
            
            rename_dict = {
                'Buying Price (€)': 'Beszállítói Nettó Ár (€)',
                'Selling Price (€)': 'Vásárlói Eladási Ár (€)',
                'Current Stock': 'Raktárkészlet (ks)'
            }
            admin_df = admin_df.rename(columns=rename_dict)
            
            st.dataframe(admin_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("📦 História objednávok / Rendelések előzményei (Sales Log)")
        df_sales = load_sales_log()
        
        if df_sales.empty:
            st.info("Zatiaľ neboli zaznamenané žiadne objednávky. / Még nincsenek eladások.")
        else:
            st.dataframe(df_sales, use_container_width=True)
            
            st.divider()
            st.subheader("📑 Vyhľadanie a stiahnutie faktúry / Számla keresése és letöltése")
            
            invoice_files = [f for f in os.listdir(INVOICES_DIR) if f.endswith('.pdf')]
            
            if not invoice_files:
                st.warning("Žiadne vygenerované faktúry v systéme. / Nincsenek mentett faktúrák.")
            else:
                selected_pdf = st.selectbox("Vyberte faktúru na stiahnutie / Válassza ki a letöltendő számlát:", sorted(invoice_files, reverse=True))
                
                pdf_full_path = os.path.join(INVOICES_DIR, selected_pdf)
                with open(pdf_full_path, "rb") as pdf_file:
                    st.download_button(
                        label=f"📥 Stiahnuť {selected_pdf} / Letöltés",
                        data=pdf_file.read(),
                        file_name=selected_pdf,
                        mime="application/pdf",
                        type="primary"
                    )

# ==========================================
# WEBSHOP MÓD
# ==========================================
else:
    if st.session_state.page == "shop":
        # Fejléc elrendezés logóval
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
            if os.path.exists(LOGO_FILE):
                st.image(LOGO_FILE, width=130)
        with col_title:
            st.title("Filipino Goods")
            st.caption("Authentic Philippine Food and Products / Eredeti filippínó termékek")

        st.divider()

        search_query = st.text_input("🔍 Hľadať produkt / Keresés (SKU cikkszám vagy Terméknév alapján)...", "")

        if search_query:
            filtered_df = df_products[
                df_products['Product Name'].str.contains(search_query, case=False, na=False) |
                df_products['SKU'].str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_df = df_products

        # Termékek kártyái
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            col_idx = idx % 3
            sku = str(row['SKU'])
            p_name = row['Product Name']
            p_price = float(row['Selling Price (€)'])
            p_stock = int(row['Current Stock'])

            with cols[col_idx]:
                st.markdown(f"### {p_name}")
                st.info(f"🔑 **SKU:** `{sku}`")
                st.write(f"💶 **Cena / Ár:** {p_price:.2f} €")
                st.write(f"📦 **Skladom / Raktáron:** {p_stock} ks")
                
                if p_stock > 0:
                    quantity = st.number_input(
                        "Počet / Mennyiség",
                        min_value=1,
                        max_value=p_stock if p_stock > 0 else 999,
                        value=1,
                        key=f"qty_{sku}"
                    )
                    if st.button(f"🛒 Do košíka / Kosárba", key=f"btn_{sku}"):
                        if sku in st.session_state.cart:
                            st.session_state.cart[sku] += quantity
                        else:
                            st.session_state.cart[sku] = quantity
                        st.success(f"Pridané! SKU `{sku}` ({quantity} ks)")
                else:
                    st.error("Vyprodané / Elfogyott")
                st.divider()

        # --- KOSÁR OLDALSÁV (SIDEBAR) ---
        st.sidebar.header("🛒 Váš košík / Kosár")

        if not st.session_state.cart:
            st.sidebar.info("Košík je prázdny. / A kosár üres.")
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
                    st.sidebar.write(f"🔑 SKU: `{sku}`")
                    st.sidebar.write(f"{qty} ks x {p_price:.2f} € = **{total_p:.2f} €**")
                    if st.sidebar.button(f"❌ Odstrániť", key=f"del_{sku}"):
                        del st.session_state.cart[sku]
                        st.rerun()
                    st.sidebar.divider()
                    
            st.sidebar.markdown(f"### **Celkom / Összesen: {grand_total:.2f} €**")
            st.sidebar.write("")
            
            if st.sidebar.button("🛍️ Objednať / Megrendelés", type="primary", use_container_width=True):
                st.session_state.page = "checkout"
                st.rerun()

    elif st.session_state.page == "checkout":
        if st.button("⬅️ Späť do obchodu / Vissza a bolthoz"):
            st.session_state.page = "shop"
            st.rerun()

        st.title("📋 Dokončenie objednávky - Filipino Goods")

        if not st.session_state.cart:
            st.warning("Váš košík je prázdny. / A kosár üres.")
        else:
            st.subheader("🛍️ Zhrnutie objednávky / Rendelés összegzése")
            
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
                    
                    cart_items.append({
                        "sku": sku,
                        "nev": p_name,
                        "ar": p_price,
                        "ks": qty,
                        "spolu": total_p
                    })

            summary_df = pd.DataFrame(cart_items)
            summary_df.columns = ['SKU', 'Názov / Termék', 'Cena/ks (€)', 'Množstvo (ks)', 'Spolu (€)']
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.markdown(f"### **Celková suma / Végösszeg: {grand_total:.2f} €**")

            st.divider()

            st.subheader("📝 Údaje pre doručenie a fakturáciu / Szállítási és számlázási adatok")

            with st.form("checkout_form"):
                col1, col2 = st.columns(2)
                with col1:
                    o_nev = st.text_input("Meno a priezvisko / Názov (Név / Cégnév)*")
                    o_email = st.text_input("E-mail*")
                    o_tel = st.text_input("Telefón / Telefonszám*")
                with col2:
                    o_adresa = st.text_input("Adresa (Utca, házszám, város, irányítószám)*")
                    o_ico = st.text_input("IČO / DIČ (Ak nakupujete na firmu)")

                submit_order = st.form_submit_button(
                    "✅ Odeslať objednávku a vygenerovať faktúru (Rendelés elküldése)",
                    type="primary",
                    use_container_width=True
                )

            if submit_order:
                if not o_nev or not o_adresa or not o_email:
                    st.error("Prosím vyplňte všetky povinné údaje! / Kérjük, töltse ki az összes kötelező mezőt!")
                else:
                    szamlaszam = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    datum = datetime.now().strftime("%Y-%m-%d")
                    customer_info = f"{o_nev}, {o_email}, {o_tel}"

                    success = process_order_in_excel(cart_items, szamlaszam, customer_info)

                    if success:
                        pdf_bytes, pdf_path = generate_pdf_invoice(
                            szamlaszam, datum, o_nev, o_ico, o_adresa, o_email, o_tel, cart_items, grand_total
                        )

                        st.balloons()
                        st.success("🎉 Objednávka bola úspešne prijatá a faktúra bola vygenerovaná! / Rendelés elfogadva!")

                        st.download_button(
                            label="📄 Stiahnuť vygenerovanú faktúru (PDF) / Zálohorá Faktúra letöltése",
                            data=pdf_bytes,
                            file_name=f"faktura_{szamlaszam}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )

                        st.session_state.cart = {}
