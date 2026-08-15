from datetime import datetime
import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st

# --- OLDAL BEÁLLÍTÁSA ---
st.set_page_config(
    page_title="Filipino Goods Webshop & Admin",
    page_icon="🛒",
    layout="wide"
)

EXCEL_FILE = 'Inventory management spreadsheet base.xlsx'
INVOICES_DIR = 'invoices'

# Számlák mappájának létrehozása, ha nem létezik
if not os.path.exists(INVOICES_DIR):
    os.makedirs(INVOICES_DIR)

# --- ADATOK BETÖLTÉSE AZ EXCELBŐL ---
@st.cache_data(ttl=2)
def load_products():
    if not os.path.exists(EXCEL_FILE):
        st.error(f"Súbor '{EXCEL_FILE}' nebol nájdený! / Az Excel fájl nem található.")
        return pd.DataFrame()
    df = pd.read_excel(EXCEL_FILE, sheet_name='Current Stock')
    df = df.dropna(subset=['SKU', 'Product Name']).copy()
    df['SKU'] = df['SKU'].astype(str).str.strip()
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
    st.session_state.page = "shop"  # "shop" vagy "checkout"

# --- ÉKEZETES BETŰTÍPUS REGISZTRÁLÁSA (PDF) ---
def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ArialCustom', 'C:\\Windows\\Fonts\\arial.ttf'))
        pdfmetrics.registerFont(TTFont('ArialCustom-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
        pdfmetrics.registerFont(TTFont('ArialCustom-Italic', 'C:\\Windows\\Fonts\\ariali.ttf'))
        return 'ArialCustom', 'ArialCustom-Bold', 'ArialCustom-Italic'
    except Exception:
        # Ha nem érhető el az Arial ttf fájl, fallback
        return 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

# --- AUTOMATA ZÁLOHOVÁ FAKTÚRA (PDF) GENERÁLÁSA ---
def generate_pdf_invoice(szamlaszam, datum, nev, ico, adresa, email, tel, polozky, sum_total):
    pdf_path = os.path.join(INVOICES_DIR, f"faktura_{szamlaszam}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    font_reg, font_bold, font_italic = register_fonts()

    # Fejléc
    c.setFont(font_bold, 16)
    c.drawString(50, height - 50, "ZÁLOHOVÁ FAKTÚRA / DÍJBEKÉRŐ")
    
    c.setFont(font_reg, 10)
    c.drawString(50, height - 70, f"Číslo faktúry / Számlaszám: {szamlaszam}")
    c.drawString(50, height - 85, f"Dátum vystavenia / Kiállítás dátuma: {datum}")

    # Szállító adatai
    c.setFont(font_bold, 11)
    c.drawString(50, height - 120, "Dodávateľ / Szállító:")
    c.setFont(font_reg, 10)
    c.drawString(50, height - 135, "Slovenský Raktár s.r.o.")
    c.drawString(50, height - 150, "Hlavná 123, 946 34 Bátorove Kosihy")
    c.drawString(50, height - 165, "IČO: 12345678 | DIČ: 2021234567")

    # Vevő adatai
    c.setFont(font_bold, 11)
    c.drawString(300, height - 120, "Odberateľ / Vevő:")
    c.setFont(font_reg, 10)
    c.drawString(300, height - 135, f"Meno/Név: {nev}")
    if ico:
        c.drawString(300, height - 150, f"IČO/DIČ: {ico}")
    c.drawString(300, height - 165, f"Adresa/Cím: {adresa}")
    c.drawString(300, height - 180, f"E-mail: {email}")
    c.drawString(300, height - 195, f"Tel: {tel}")

    # Táblázat fejléce
    c.line(50, height - 220, width - 50, height - 220)
    c.setFont(font_bold, 9)
    c.drawString(50, height - 235, "SKU")
    c.drawString(150, height - 235, "Názov položky / Termék megnevezése")
    c.drawString(350, height - 235, "Množstvo")
    c.drawString(410, height - 235, "Cena/ks (€)")
    c.drawString(480, height - 235, "Spolu (€)")
    c.line(50, height - 245, width - 50, height - 245)

    y = height - 265
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
    c.drawString(50, 40, "Ďakujeme za Vašu objednávku! / Köszönjük a rendelését!")

    c.save()
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        
    return pdf_bytes, pdf_path

# --- EXCEL FRISSÍTÉSE RENDELÉSKOR (KÉSZLET-LEVONÁS & SALES LOG) ---
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


# --- NÉZET VÁLASZTÓ AZ OLDALSÁVBAN (WEBÁRUHÁZ / ADMIN) ---
mode = st.sidebar.radio("📌 Režim / Mód:", ["🛒 Obchod / Webshop", "⚙️ Admin / Správa"])

if mode == "⚙️ Admin / Správa":
    st.title("⚙️ Administrácia & Faktúry / Adminisztráció & Számlák")
    
    st.subheader("📦 História objednávok / Rendelések előzményei (Sales Log)")
    df_sales = load_sales_log()
    
    if df_sales.empty:
        st.info("Zatiaľ neboli zaznamenané žiadne objednávky. / Még nincsenek eladások.")
    else:
        st.dataframe(df_sales, use_container_width=True)
        
        st.divider()
        st.subheader("📑 Vyhľadanie a stiahnutie faktúry / Számla keresése és letöltése")
        
        # Mappában lévő elmentett PDF faktúrák kilistázása
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

else:
    # ADATOK BETÖLTÉSE
    df_products = load_products()

    # ==========================================
    # 1. OLDAL: BOLT NÉZET (SHOP)
    # ==========================================
    if st.session_state.page == "shop":
        st.title("🛒 Ázijský & Filipínsky Tovar / Webshop")

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
            p_price = float(row['Unit Price (€)'])
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
                        max_value=p_stock,
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
                    p_price = float(p_row['Unit Price (€)'])
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
            
            # --- OBJEDNAŤ GOMB A KOSÁR ALJÁN ---
            if st.sidebar.button("🛍️ Objednať / Megrendelés", type="primary", use_container_width=True):
                st.session_state.page = "checkout"
                st.rerun()

    # ==========================================
    # 2. OLDAL: PÉNZTÁR & ADATOK KITÖLTÉSE (CHECKOUT)
    # ==========================================
    elif st.session_state.page == "checkout":
        
        if st.button("⬅️ Späť do obchodu / Vissza a bolthoz"):
            st.session_state.page = "shop"
            st.rerun()

        st.title("📋 Dokončenie objednávky / Rendelés véglegesítése")

        if not st.session_state.cart:
            st.warning("Váš košík je prázdny. / A kosár üres.")
        else:
            # Rendelés összegzése
            st.subheader("🛍️ Zhrnutie objednávky / Rendelés összegzése")
            
            cart_items = []
            grand_total = 0.0
            
            for sku, qty in st.session_state.cart.items():
                prod_match = df_products[df_products['SKU'] == sku]
                if not prod_match.empty:
                    p_row = prod_match.iloc[0]
                    p_name = p_row['Product Name']
                    p_price = float(p_row['Unit Price (€)'])
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

            # Szállítási adatok űrlapja
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

                    # 1. Készlet levonása és Sales Log rögzítése az Excelben
                    success = process_order_in_excel(cart_items, szamlaszam, customer_info)

                    if success:
                        # 2. PDF Faktúra generálása és mentése
                        pdf_bytes, pdf_path = generate_pdf_invoice(
                            szamlaszam, datum, o_nev, o_ico, o_adresa, o_email, o_tel, cart_items, grand_total
                        )

                        st.balloons()
                        st.success("🎉 Objednávka bola úspešne prijatá a faktúra bola vygenerovaná! / Rendelés elfogadva!")

                        # 3. Vevői letöltési gomb
                        st.download_button(
                            label="📄 Stiahnuť vygenerovanú faktúru (PDF) / Zálohorá Faktúra letöltése",
                            data=pdf_bytes,
                            file_name=f"faktura_{szamlaszam}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )

                        # Kosár ürítése rendelés végén
                        st.session_state.cart = {}