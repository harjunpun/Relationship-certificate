import streamlit as st
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Relationship Certificate Generator", page_icon="👨‍👩‍👧‍👦", layout="wide") # Using "wide" layout for the family table!

# 2. SECURITY LOCK & STEALTH MODE
if st.query_params.get("access") != "namaste":
    st.error("🔒 Access Denied / アクセス拒否")
    st.warning("Please use the official link provided to access this tool.")
    st.stop()
    
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 3. APP HEADER
st.title("👨‍👩‍👧‍👦 Relationship Certificate Generator")
st.markdown("Fill out the details below to generate the PDF certificate. / 以下の詳細を入力して、PDF証明書を作成してください。")
st.write("---")

def load_font():
    font_path = "msgothic.ttc" 
    try:
        pdfmetrics.registerFont(TTFont('JapaneseFont', font_path, subfontIndex=0))
        return 'JapaneseFont'
    except Exception as e:
        st.error(f"⚠️ Font Error: Could not load '{font_path}'. Please ensure the font file is uploaded to the server.")
        return 'Helvetica'

def generate_pdf(data, family_data):
    buffer = io.BytesIO()
    font_name = load_font()

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName=font_name, fontSize=16, alignment=1, spaceAfter=15)
    center_style = ParagraphStyle('Center', fontName=font_name, fontSize=11, alignment=1)
    left_style = ParagraphStyle('Left', fontName=font_name, fontSize=10, leading=14)
    cell_style = ParagraphStyle('CellStyle', fontName=font_name, fontSize=10, leading=12)

    def P(text): return Paragraph(text, cell_style)

    # Issued Place & Title
    elements.append(Paragraph(data["Issued Place (発行地)"], center_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("関係者関係証明書 (Relationship certificate)", title_style))

    # Registration Info
    reg_info = f"""
    <b>登録番号 (Registration No.):</b> {data['Registration No. (登録番号)']}<br/>
    <b>登録日 (Registration Date):</b> {data['Registration Date (登録日)']}
    """
    elements.append(Paragraph(reg_info, left_style))
    elements.append(Spacer(1, 15))

    # Body Paragraph
    app_name_text = data["Applicant's Full Name (申請者の氏名)"]
    body_text = f"""
    <b>ご担当者様</b><br/><br/>
    公式記録によると、これは申請者を証明するものです。 ネパール、<b>{data['Permanent Address (永住住所)']}</b>の住民である。<br/>
    <b>{app_name_text}</b> 氏には次のような関係があります。
    """
    elements.append(Paragraph(body_text, left_style))
    elements.append(Spacer(1, 10))

    # Applicant Info Table
    app_table_data = [
        [P("申請者の氏名<br/>(Applicant's Full Name)"), P(f"<b>{app_name_text}</b>")],
        [P("永住住所<br/>(Permanent Address)"), P(data['Permanent Address (永住住所)'])],
        [P("市民権証明書番号<br/>(Citizenship certificate No.)"), P(data["Applicant's Citizenship No. (市民権証明書番号)"])]
    ]
    t_app = Table(app_table_data, colWidths=[180, 335])
    t_app.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_app)
    elements.append(Spacer(1, 15))

    # Family Details Table
    elements.append(Paragraph("<b>家族の詳細 (Family Details)</b>", left_style))
    elements.append(Spacer(1, 5))
    
    fam_table_data = [
        [P("<b>S.No.</b>"), P("<b>名前<br/>(Name)</b>"), P("<b>生年月日<br/>(Date of birth)</b>"), 
         P("<b>情報提供者との関係<br/>(Relation with Informant)</b>"), P("<b>市民権/出生登録番号<br/>(Citizenship/Birth Reg. No.)</b>")]
    ]
    
    # Only add rows that actually have a name filled in
    valid_family_members = [member for member in family_data if member['name'].strip()]
    
    for idx, member in enumerate(valid_family_members):
        fam_table_data.append([
            P(str(idx + 1)), P(member['name']), P(member['dob']), P(member['relation']), P(member['id'])
        ])
        
    t_fam = Table(fam_table_data, colWidths=[35, 120, 80, 100, 180])
    t_fam.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_fam)
    elements.append(Spacer(1, 15))

    # Footer Clause
    elements.append(Paragraph("この証明書は、2012 年地方政府行動法第 12 条 (2) に従って発行されます。この証明書は海外目的でのみ発行されます。", left_style))
    elements.append(Spacer(1, 20))

    # Translator Table
    translator_table_data = [
        [P("翻訳者<br/>(Translator)"), "", P(data["Translator Name (翻訳者の氏名)"])],
        [P("日本の住所<br/>(Address in Japan)"), "", P(data["Address in Japan (日本での住所)"])]
    ]
    t_translator = Table(translator_table_data, colWidths=[110, 140, 265])
    t_translator.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (1,-1), colors.whitesmoke),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 1), (1, 1)),
    ]))
    elements.append(t_translator)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- HELPER FUNCTION FOR DATE DROPDOWNS ---
years = ["Year"] + [str(y) for y in range(2040, 1920, -1)]
months = ["Month"] + [str(m).zfill(2) for m in range(1, 13)]
days = ["Day"] + [str(d).zfill(2) for d in range(1, 32)]

def render_date_dropdowns(label, key_prefix):
    st.write(label)
    col1, col2, col3 = st.columns(3)
    y = col1.selectbox("年 (Year)", years, key=f"{key_prefix}_y")
    m = col2.selectbox("月 (Month)", months, key=f"{key_prefix}_m")
    d = col3.selectbox("日 (Day)", days, key=f"{key_prefix}_d")
    if "Year" not in y and "Month" not in m and "Day" not in d:
        return f"{y}-{m}-{d}"
    return ""

# --- UI FORM ---
st.subheader("Registration Details / 登録情報")
issued_place = st.text_input("Issued Place (発行地)", placeholder="eg.ネパール・ガンダキ州カスキ郡ポカラ市役所")
reg_no = st.text_input("Registration No. (登録番号)")
reg_date = render_date_dropdowns("Registration Date (登録日)", "reg")

st.write("---")

st.subheader("Applicant's Details / 申請者の詳細")
app_name = st.text_input("Applicant's Full Name (申請者の氏名)", placeholder="カタカナで書いてください")
app_address = st.text_input("Permanent Address (永住住所)", placeholder="日本語で書いてください")
app_id = st.text_input("Applicant's Citizenship No. (市民権証明書番号)")

st.write("---")

# --- FAMILY DETAILS TABLE ---
st.subheader("Family Details / 家族の詳細")
st.markdown("Fill in the rows for each family member. Leave unused rows blank.")

# Render Headers
col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
col1.write("**Name (カタカナ)**")
col2.write("**DOB (YYYY-MM-DD)**")
col3.write("**Relation (関係)**")
col4.write("**Citizenship/Birth Reg No.**")

relations_list = ["", "妻 (Wife)", "夫 (Husband)", "息子 (Son)", "娘 (Daughter)", "父 (Father)", "母 (Mother)", "兄/弟 (Brother)", "姉/妹 (Sister)", "本人 (Self)"]
family_data = []

# Render 6 Rows
for i in range(6):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
    f_name = c1.text_input(f"Name {i}", label_visibility="collapsed", placeholder="カタカナで書いてください", key=f"name_{i}")
    f_dob = c2.text_input(f"DOB {i}", label_visibility="collapsed", placeholder="YYYY-MM-DD", key=f"dob_{i}")
    f_rel = c3.selectbox(f"Rel {i}", relations_list, label_visibility="collapsed", key=f"rel_{i}")
    f_id = c4.text_input(f"ID {i}", label_visibility="collapsed", key=f"id_{i}")
    
    family_data.append({"name": f_name, "dob": f_dob, "relation": f_rel, "id": f_id})

st.write("---")

# --- SMART TRANSLATOR LOGIC ---
st.subheader("Translator Details / 翻訳者の詳細")

translator_options = []
# Check the family grid for sons or daughters
for member in family_data:
    if member["relation"] in ["息子 (Son)", "娘 (Daughter)"]:
        if member["name"].strip() and member["name"] not in translator_options:
            translator_options.append(member["name"])

translator_options.append("Other (手動入力)")

translator_choice = st.selectbox("Translator Name (翻訳者の氏名)", translator_options)

if translator_choice == "Other (手動入力)":
    translator_name = st.text_input("Enter the Translator's Full Name / 翻訳者の氏名を入力してください", placeholder="カタカナで書いてください")
else:
    translator_name = translator_choice

address_japan = st.text_input("Address in Japan (日本での住所)", placeholder="日本語で書いてください")

st.write("---")

# --- GENERATE PDF BUTTON ---
if st.button("Generate PDF / PDFを作成", type="primary"):
    user_data = {
        "Issued Place (発行地)": issued_place,
        "Registration No. (登録番号)": reg_no,
        "Registration Date (登録日)": reg_date,
        "Applicant's Full Name (申請者の氏名)": app_name,
        "Permanent Address (永住住所)": app_address,
        "Applicant's Citizenship No. (市民権証明書番号)": app_id,
        "Translator Name (翻訳者の氏名)": translator_name,
        "Address in Japan (日本での住所)": address_japan
    }

    client_name = app_name if app_name else "Client"
    file_name = f"Relationship_Certificate_{client_name}.pdf"
    
    with st.spinner("Generating document... / ドキュメントを作成中..."):
        pdf_buffer = generate_pdf(user_data, family_data)
        
        st.success("Success! Click the button below to download the certificate. / 成功しました！")
        
        st.download_button(
            label="📄 Download PDF",
            data=pdf_buffer,
            file_name=file_name,
            mime="application/pdf"
        )