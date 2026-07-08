import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os
import json

# --- CENTRALIZED DB MANAGER (JSON) ---
def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return [] if "company" not in filename else {}
    return [] if "company" not in filename else {}

def save_data(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

COMPANY_FILE = "company_info.json"
CUSTOMERS_FILE = "customers.json"
QUOTATIONS_FILE = "quotations.json"

# --- REPORTLAB PDF GENERATION FUNCTION ---
def generate_pdf_report(q_data, items_list, comp_info):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=18, spaceAfter=2*mm)
    comp_style = ParagraphStyle(name='CompStyle', fontName='Helvetica', fontSize=10, alignment=2, leading=14)
    header_style = ParagraphStyle(name='HeaderStyle', fontName='Helvetica-Bold', fontSize=14, alignment=1, spaceAfter=5*mm)
    meta_style = ParagraphStyle(name='MetaStyle', fontName='Helvetica', fontSize=10, leading=14)
    table_text = ParagraphStyle(name='TableText', fontName='Helvetica', fontSize=9, leading=12)
    table_head = ParagraphStyle(name='TableHead', fontName='Helvetica-Bold', fontSize=10, leading=12)
    
    story = []
    
    # 1. Company Profile Header (Includes Company Registration No)
    comp_name_text = f"<b>{comp_info.get('comp_name', 'SS MARINE TECHNICAL SERVICES')}</b>"
    comp_reg_no = comp_info.get('comp_reg_no', '')
    reg_text = f"<br/>Co. Reg. No: {comp_reg_no}" if comp_reg_no else ""
    comp_addr_text = f"{comp_info.get('comp_address', '').replace('\n', '<br/>')}{reg_text}"
    
    header_table_data = [
        [Paragraph(comp_name_text, title_style), Paragraph(comp_addr_text, comp_style)]
    ]
    header_table = Table(header_table_data, colWidths=[80*mm, 100*mm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(header_table)
    
    story.append(Spacer(1, 2*mm))
    story.append(Table([[""]], colWidths=[180*mm], rowHeights=[0.5*mm], style=[('BACKGROUND', (0,0), (-1,-1), colors.black)]))
    story.append(Spacer(1, 4*mm))
    
    # 2. Document Title
    story.append(Paragraph("<b>QUOTATION</b>", header_style))
    story.append(Spacer(1, 2*mm))
    
    # 3. Metadata block (Left aligned fields as per instruction #4)
    validity_dt = datetime.strptime(q_data['issue_date'], "%d/%m/%Y") + timedelta(days=int(q_data['expiry_days']))
    
    client_block = f"""<b>To:</b><br/>
    <b>{q_data['customer_name']}</b><br/>
    {str(q_data['customer_address']).replace('\n', '<br/>')}<br/><br/>
    <b>Kind Attn:</b> {q_data.get('quote_kind_attn', '')}<br/>
    <b>Ship Name/Job No:</b> {q_data.get('ship_name', 'N.A')}<br/>
    <b>Reference Job:</b> {q_data.get('main_job', 'N.A')}<br/>
    <b>MRS/PR No:</b> {q_data.get('mrs_pr_no', 'N.A')}"""
    
    quote_block = f"""<para align="right">
    <b>Quote No:</b> {q_data['ref_no']}<br/>
    <b>Issue Date:</b> {q_data['issue_date']}<br/>
    <b>Valid Till:</b> {validity_dt.strftime('%d/%m/%Y')}<br/>
    </para>"""
    
    meta_table_data = [
        [Paragraph(client_block, meta_style), Paragraph(quote_block, meta_style)]
    ]
    meta_table = Table(meta_table_data, colWidths=[110*mm, 70*mm])
    meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 5*mm))
    
    # 4. Financial Items Table Grid
    table_headers = [
        Paragraph("<b>S.No.</b>", table_head), Paragraph("<b>SSNo.</b>", table_head),
        Paragraph("<b>Description</b>", table_head), Paragraph("<b>Qty</b>", table_head),
        Paragraph("<b>Unit</b>", table_head), Paragraph("<b>Unit Price</b>", table_head),
        Paragraph("<b>Total Price</b>", table_head)
    ]
    
    report_table_data = [table_headers]
    for row in items_list:
        report_table_data.append([
            Paragraph(str(row['s_no']), table_text),
            Paragraph(str(row['ssn_no']) if row['ssn_no'] != 'None' else '', table_text),
            Paragraph(str(row['job_description']), table_text),
            Paragraph(str(row['qty']), table_text),
            Paragraph(str(row['unit']), table_text),
            Paragraph(f"$ {float(row['unit_price']):,.2f}", table_text),
            Paragraph(f"$ {float(row['total_price']):,.2f}", table_text)
        ])
        
    col_widths = [12*mm, 15*mm, 73*mm, 15*mm, 15*mm, 25*mm, 25*mm]
    pdf_table = Table(report_table_data, colWidths=col_widths, repeatRows=1)
    pdf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),
        ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
    ]))
    story.append(pdf_table)
    
    total_amt_formatted = f"Total Value: $ {float(q_data['grand_total']):,.2f}"
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f"<para align='right'><b>{total_amt_formatted}</b></para>", title_style))
    story.append(Spacer(1, 4*mm))
    
    story.append(Paragraph("<b>Notes / Operational Terms:</b>", table_head))
    notes_found = False
    for row in items_list:
        for n_key in ['notes_1', 'notes_2', 'notes_3', 'notes_4', 'notes_5']:
            if row.get(n_key) and str(row[n_key]).strip() != "None" and str(row[n_key]).strip() != "":
                story.append(Paragraph(f"- {str(row[n_key]).strip()}", meta_style))
                notes_found = True
    if not notes_found:
        story.append(Paragraph("- Standard commercial terms apply.", meta_style))
        
    story.append(Spacer(1, 15*mm))
    sig_left = "-----------------------------------<br/><b>Authorized Signatory / Stamp</b><br/>SS Marine Technical Services"
    sig_right = f"<para align='right'>-----------------------------------<br/><b>Customer Acceptance</b><br/>Sign & Date</para>"
    
    sig_table_data = [
        [Paragraph(sig_left, meta_style), Paragraph(sig_right, meta_style)]
    ]
    sig_table = Table(sig_table_data, colWidths=[90*mm, 90*mm])
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- MAIN APP START ---
st.title("🏭 SS Marine Technical Services - ERP Module")
tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Company Profile", "👥 Customer Directory", "📝 Create Quotation", "📊 Saved Quotations"])

# --- TAB 1: COMPANY PROFILE ---
with tab1:
    st.header("Company Profile Setup")
    comp_info = load_data(COMPANY_FILE)
    
    comp_name = st.text_input("Company Name", value=comp_info.get("comp_name", "SS MARINE TECHNICAL SERVICES PTE LTD"))
    comp_reg_no = st.text_input("Company Reg. No. / ROC Number", value=comp_info.get("comp_reg_no", "200903249W"))
    comp_address = st.text_area("Company Address & Contact Details", value=comp_info.get("comp_address", "No. 10 Buroh Street, #03-35 West Connect Building\nSingapore 627 564\nTel: 9632 3745 Email: ssmarinepteltd@yahoo.com"))
    
    if st.button("Save Company Information", type="primary"):
        save_data(COMPANY_FILE, {"comp_name": comp_name, "comp_reg_no": comp_reg_no, "comp_address": comp_address})
        st.success("Company profile saved locally!")

# --- TAB 2: CUSTOMER DIRECTORY ---
with tab2:
    st.header("Customer Database Management")
    customers = load_data(CUSTOMERS_FILE)
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.subheader("Add New Customer")
        cust_name = st.text_input("Customer/Company Name")
        cust_address = st.text_area("Full Postal Address")
        st.caption("Note: Kind Attn can be optionally left blank here and added per quotation.")
        
        if st.button("Save Customer"):
            if cust_name and cust_address:
                customers.append({"id": str(len(customers) + 1), "name": cust_name, "address": cust_address})
                save_data(CUSTOMERS_FILE, customers)
                st.success(f"Customer '{cust_name}' saved!")
                st.rerun()

    with col_c2:
        st.subheader("Registered Clients")
        if customers:
            st.dataframe(pd.DataFrame(customers), width="stretch")

# --- TAB 3: CREATE QUOTATION ---
with tab3:
    st.header("Generate Sales Quotation")
    customers = load_data(CUSTOMERS_FILE)
    
    if not customers:
        st.warning("Please register a customer first.")
    else:
        all_quotes = load_data(QUOTATIONS_FILE)
        new_quote_no = f"Q-{len(all_quotes) + 1:04d}"
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            quote_no = st.text_input("Quote No", value=new_quote_no)
            issue_date = st.date_input("Issue Date", datetime.now())
            expiry_days = st.number_input("Validity Period (Days)", min_value=1, value=30)
            selected_cust = st.selectbox("Select Target Client", [c['name'] for c in customers])
            cust_details = next(c for c in customers if c['name'] == selected_cust)
            quote_kind_attn = st.text_input("Kind Attn. Name for this specific Quotation")
        with col_m2:
            ship_name = st.text_input("Ship Name / Customer Job No.")
            main_job = st.text_input("Main Job Title")
            mrs_pr_no = st.text_input("MRS / PR No.")
            
        st.markdown("### 🛠️ Line Items (Excel Grid)")
        init_grid = [{
            "S.No.": "1", "SSNo.": "", "Job Description": "", "Qty": 1.0, "Unit": "Pcs", "Unit Price": 0.0,
            "Notes 1": "", "Notes 2": "", "Notes 3": "", "Notes 4": "", "Notes 5": ""
        }]
        df_items_input = st.data_editor(pd.DataFrame(init_grid), num_rows="dynamic", width="stretch", key="quote_grid")
        
        if not df_items_input.empty:
            df_items_input['Qty'] = pd.to_numeric(df_items_input['Qty'], errors='coerce').fillna(0)
            df_items_input['Unit Price'] = pd.to_numeric(df_items_input['Unit Price'], errors='coerce').fillna(0)
            df_items_input['Total'] = df_items_input['Qty'] * df_items_input['Unit Price']
            g_total = df_items_input['Total'].sum()
        else: g_total = 0.0
            
        st.markdown(f"### 💰 **Total Valuation: $ {g_total:,.2f}**")
        
        if st.button("📥 Commit & Save Quotation Record", type="primary"):
            df_grid_cleaned = df_items_input[df_items_input['Job Description'].str.strip() != ""]
            
            table_rows = []
            for idx, r in df_grid_cleaned.iterrows():
                table_rows.append({
                    "SN": str(r.get("S.No.", idx+1)), "SSN": str(r.get("SSNo.", "")),
                    "Description": str(r.get("Job Description", "")), "Qty": float(r.get("Qty", 0)),
                    "Unit": str(r.get("Unit", "Pcs")), "Unit Price": float(r.get("Unit Price", 0)),
                    "Total Price": float(r.get("Total", 0)),
                    "N1": str(r.get("Notes 1", "")), "N2": str(r.get("Notes 2", "")),
                    "N3": str(r.get("Notes 3", "")), "N4": str(r.get("Notes 4", "")), "N5": str(r.get("Notes 5", ""))
                })
                
            new_quotation_record = {
                "ref_no": quote_no, "issue_date": issue_date.strftime("%d/%m/%Y"), "expiry_days": str(expiry_days),
                "customer_name": cust_details['name'], "quote_kind_attn": quote_kind_attn, "customer_address": cust_details['address'],
                "ship_name": ship_name, "main_job": main_job, "mrs_pr_no": mrs_pr_no, "grand_total": float(g_total),
                "table_data": table_rows
            }
            
            all_quotes.append(new_quotation_record)
            save_data(QUOTATIONS_FILE, all_quotes)
            st.success(f"Quotation {quote_no} archived successfully!")
            st.rerun()

# --- TAB 4: ARCHIVES & PDF DOWNLOAD ---
with tab4:
    st.header("Quotation Archives")
    all_quotes = load_data(QUOTATIONS_FILE)
    comp_info = load_data(COMPANY_FILE)
    
    if not all_quotes:
        st.info("No saved records.")
    else:
        df_list = pd.DataFrame(all_quotes)
        st.dataframe(df_list[['ref_no', 'issue_date', 'customer_name', 'main_job', 'grand_total']], width="stretch")
        
        selected_ref = st.selectbox("Choose a Reference Number to Export", df_list['ref_no'].unique())
        if selected_ref:
            q_data = next(q for q in all_quotes if q['ref_no'] == selected_ref)
            
            items_list = []
            for row in q_data['table_data']:
                items_list.append({
                    "s_no": row.get("SN"), "ssn_no": row.get("SSN"), "job_description": row.get("Description"),
                    "qty": row.get("Qty"), "unit": row.get("Unit"), "unit_price": row.get("Unit Price"), "total_price": row.get("Total Price"),
                    "notes_1": row.get("N1"), "notes_2": row.get("N2"), "notes_3": row.get("N3"), "notes_4": row.get("N4"), "notes_5": row.get("N5")
                })
                
            pdf_file = generate_pdf_report(q_data, items_list, comp_info)
            
            st.download_button(
                label="📥 DOWNLOAD PROFESSIONAL QUOTATION (PDF)",
                data=pdf_file,
                file_name=f"Quotation_{selected_ref}.pdf",
                mime="application/pdf",
                type="primary"
            )
            
            st.markdown("---")
            st.subheader("👀 Preview Screen")
            st.write(q_data)