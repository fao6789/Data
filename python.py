# app_financial_analysis.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_pdf import PdfPages

# Optional: try to import reportlab for nicer PDF layout; fallback handled below
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="📊 Phân Tích Báo Cáo Tài Chính", layout="wide")
st.title("📈 ỨNG DỤNG PHÂN TÍCH BÁO CÁO TÀI CHÍNH DOANH NGHIỆP")
st.markdown("Ứng dụng tự động: tính biến động, tạo báo cáo, biểu đồ và xuất PDF (Công ty ABC – Báo cáo tài chính năm 2025).")

# ----------------------------- #
# Helper: generate main report data & charts
# ----------------------------- #
def prepare_report_data(df):
    """Chuẩn hoá và tính toán các bảng/giá trị cần thiết."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace('\u00a0', ' ', regex=True)

    # Identify year columns
    col_prev = next((c for c in df.columns if "Năm trước" in c), df.columns[1])
    col_next = next((c for c in df.columns if "Năm sau" in c), df.columns[2])

    # Convert numeric
    for c in [col_prev, col_next]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Compute differences
    df["Chênh lệch"] = df[col_next] - df[col_prev]
    df["Tỷ lệ tăng (%)"] = (df["Chênh lệch"] / df[col_prev].replace(0, 1e-9)) * 100

    # quick getter
    def get_val(keyword):
        m = df[df['Chỉ tiêu'].str.contains(keyword, case=False, na=False)]
        return (m[col_prev].values[0], m[col_next].values[0]) if not m.empty else (0, 0)

    ts_total_prev, ts_total_next = get_val("TỔNG CỘNG TÀI SẢN")
    ts_ngan_prev, ts_ngan_next = get_val("TÀI SẢN NGẮN HẠN")
    ts_dai_prev, ts_dai_next = get_val("TÀI SẢN DÀI HẠN")
    no_total_prev, no_total_next = get_val("TỔNG CỘNG NỢ PHẢI TRẢ")
    von_prev, von_next = get_val("VỐN CHỦ SỞ HỮU")

    overview = pd.DataFrame({
        "Chỉ tiêu": [
            "Tổng tài sản", "Tài sản ngắn hạn", "Tài sản dài hạn",
            "Tổng nợ phải trả", "Vốn chủ sở hữu"
        ],
        "Năm trước (N-1)": [ts_total_prev, ts_ngan_prev, ts_dai_prev, no_total_prev, von_prev],
        "Năm sau (N)": [ts_total_next, ts_ngan_next, ts_dai_next, no_total_next, von_next]
    })
    overview["Chênh lệch"] = overview["Năm sau (N)"] - overview["Năm trước (N-1)"]
    overview["Tỷ lệ tăng (%)"] = (overview["Chênh lệch"] / overview["Năm trước (N-1)"].replace(0,1e-9))*100

    # ratios
    debt_ratio_prev = (no_total_prev / ts_total_prev * 100) if ts_total_prev else 0
    debt_ratio_next = (no_total_next / ts_total_next * 100) if ts_total_next else 0
    equity_ratio_prev = (von_prev / ts_total_prev * 100) if ts_total_prev else 0
    equity_ratio_next = (von_next / ts_total_next * 100) if ts_total_next else 0

    # Return everything needed
    return {
        "df_processed": df,
        "overview": overview,
        "ts": {
            "total_prev": ts_total_prev, "total_next": ts_total_next,
            "ngan_prev": ts_ngan_prev, "ngan_next": ts_ngan_next,
            "dai_prev": ts_dai_prev, "dai_next": ts_dai_next
        },
        "liabilities": {"prev": no_total_prev, "next": no_total_next},
        "equity": {"prev": von_prev, "next": von_next},
        "ratios": {
            "debt_prev": debt_ratio_prev, "debt_next": debt_ratio_next,
            "equity_prev": equity_ratio_prev, "equity_next": equity_ratio_next
        },
        "col_prev": col_prev,
        "col_next": col_next
    }

# ----------------------------- #
# Helper: create matplotlib charts and return figures
# ----------------------------- #
def create_charts(report):
    figs = {}

    # Asset bar chart
    fig1, ax1 = plt.subplots(figsize=(6,4))
    categories = ["Tài sản ngắn hạn", "Tài sản dài hạn"]
    prev_vals = [report["ts"]["ngan_prev"], report["ts"]["dai_prev"]]
    next_vals = [report["ts"]["ngan_next"], report["ts"]["dai_next"]]
    x = range(len(categories))
    ax1.bar([i-0.15 for i in x], prev_vals, width=0.3, label=f"Năm trước")
    ax1.bar([i+0.15 for i in x], next_vals, width=0.3, label=f"Năm sau")
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.set_ylabel("Giá trị (VNĐ)")
    ax1.legend()
    ax1.ticklabel_format(axis='y', style='plain')
    fig1.tight_layout()
    figs['assets_bar'] = fig1

    # Capital structure pie charts
    fig2, axes = plt.subplots(1,2, figsize=(8,4))
    axes[0].pie([report["liabilities"]["prev"], report["equity"]["prev"]],
                labels=["Nợ phải trả", "Vốn chủ sở hữu"], autopct='%1.1f%%', startangle=90)
    axes[0].set_title("Năm trước")
    axes[1].pie([report["liabilities"]["next"], report["equity"]["next"]],
                labels=["Nợ phải trả", "Vốn chủ sở hữu"], autopct='%1.1f%%', startangle=90)
    axes[1].set_title("Năm sau")
    fig2.tight_layout()
    figs['capital_pies'] = fig2

    return figs

# ----------------------------- #
# Helper: create PDF bytes (reportlab if available, else matplotlib->PdfPages)
# ----------------------------- #
def build_pdf_bytes(report, title="Công ty ABC – Báo cáo tài chính năm 2025"):
    """
    Return bytes of a PDF that includes:
     - Title
     - Overview table (full)
     - Charts (matplotlib figs)
     - Narratives (text)
    Uses reportlab if installed for nicer formatting; otherwise falls back to matplotlib+PdfPages.
    """
    df_proc = report["df_processed"]
    overview = report["overview"]

    # create charts
    figs = create_charts(report)

    if REPORTLAB_AVAILABLE:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        elements.append(Spacer(1,12))

        # Overview table (convert to list of lists)
        data = [overview.columns.tolist()] + overview.round(0).astype(object).values.tolist()
        # Format numeric cells with thousand separators for display
        # Convert numeric to formatted strings
        header = data[0]
        body = []
        for row in data[1:]:
            new_row = []
            for i, val in enumerate(row):
                if isinstance(val, (int, float)):
                    if header[i] == "Tỷ lệ tăng (%)":
                        new_row.append(f"{val:+.1f}%")
                    elif header[i] == "Chênh lệch":
                        new_row.append(f"{val:+,.0f}")
                    else:
                        new_row.append(f"{val:,.0f}")
                else:
                    new_row.append(str(val))
            body.append(new_row)
        table_data = [header] + body

        t = Table(table_data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d3d3d3')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        elements.append(t)
        elements.append(Spacer(1,12))

        # Narrative summary
        debt_prev = report["ratios"]["debt_prev"]
        debt_next = report["ratios"]["debt_next"]
        narrative = f"""
        <b>Nhận xét tổng quát</b><br/>
        - Doanh nghiệp mở rộng quy mô hoạt động, tăng cả tài sản ngắn hạn và dài hạn.<br/>
        - Cơ cấu tài chính ổn định, tỷ lệ nợ tăng nhẹ ({debt_prev:.1f}% → {debt_next:.1f}%).<br/>
        - Khuyến nghị: theo dõi khoản phải thu và hàng tồn kho để tránh rủi ro dòng tiền.
        """
        elements.append(Paragraph(narrative, styles['Normal']))
        elements.append(Spacer(1,12))

        # Add charts: save matplotlib figs to PNG in-memory and add
        for key in ['assets_bar', 'capital_pies']:
            buf_img = io.BytesIO()
            figs[key].savefig(buf_img, format='PNG', bbox_inches='tight')
            buf_img.seek(0)
            img = Image(buf_img, width=400, height=250)
            elements.append(img)
            elements.append(Spacer(1,12))

        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        return pdf_bytes

    else:
        # Fallback: use matplotlib PdfPages to create PDF pages with figures & table rendered as figure
        buffer = io.BytesIO()
        with PdfPages(buffer) as pdf:
            # Page 1: Title + overview table rendered as matplotlib table
            fig, ax = plt.subplots(figsize=(11.69,8.27))  # A4 landscape in inches
            ax.axis('off')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

            # Render overview as table
            table_df = overview.copy()
            # Format for display
            disp = table_df.copy()
            disp["Năm trước (N-1)"] = disp["Năm trước (N-1)"].map('{:,.0f}'.format)
            disp["Năm sau (N)"] = disp["Năm sau (N)"].map('{:,.0f}'.format)
            disp["Chênh lệch"] = disp["Chênh lệch"].map('{:+,.0f}'.format)
            disp["Tỷ lệ tăng (%)"] = disp["Tỷ lệ tăng (%)"].map('{:+.1f}%'.format)

            table = ax.table(cellText=disp.values, colLabels=disp.columns, loc='center', cellLoc='right')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.4)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 2: Asset bar chart
            pdf.savefig(figs['assets_bar'], bbox_inches='tight')
            plt.close(figs['assets_bar'])

            # Page 3: Capital pies
            pdf.savefig(figs['capital_pies'], bbox_inches='tight')
            plt.close(figs['capital_pies'])

            # Page 4: Narrative as a figure (text block)
            fign, axn = plt.subplots(figsize=(11.69,8.27))
            axn.axis('off')
            debt_prev = report["ratios"]["debt_prev"]
            debt_next = report["ratios"]["debt_next"]
            text = f"""Nhận xét tổng quát

- Doanh nghiệp mở rộng quy mô hoạt động, tăng cả tài sản ngắn hạn và dài hạn.
- Cơ cấu tài chính ổn định, tỷ lệ nợ tăng nhẹ ({debt_prev:.1f}% → {debt_next:.1f}%).
- Khuyến nghị: theo dõi khoản phải thu và hàng tồn kho để tránh rủi ro dòng tiền.
"""
            axn.text(0.02, 0.98, text, va='top', ha='left', fontsize=12, wrap=True)
            pdf.savefig(fign, bbox_inches='tight')
            plt.close(fign)

        buffer.seek(0)
        return buffer.read()

# ----------------------------- #
# Streamlit UI: load file, show report, and PDF download
# ----------------------------- #
uploaded_file = st.file_uploader("📥 Tải lên file Excel (3 cột: Chỉ tiêu | Năm trước | Năm sau)", type=["xlsx", "xls"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ File đã tải thành công!")
        report = prepare_report_data(df)

        # show overview table
        st.subheader("🧾 Tổng quan biến động")
        st.dataframe(report["overview"].style.format({
            "Năm trước (N-1)": "{:,.0f}",
            "Năm sau (N)": "{:,.0f}",
            "Chênh lệch": "{:+,.0f}",
            "Tỷ lệ tăng (%)": "{:+.1f}%"
        }), use_container_width=True)

        # show charts inline (recreate to avoid reusing closed figs)
        figs = create_charts(report)
        st.markdown("### 📊 Biểu đồ cơ cấu tài sản")
        st.pyplot(figs['assets_bar'])
        st.markdown("### 🧮 Biểu đồ cơ cấu nguồn vốn")
        st.pyplot(figs['capital_pies'])

        # narrative and ratios
        st.markdown("### 📊 Cơ cấu & Nhận xét")
        ratio_df = pd.DataFrame({
            "Chỉ tiêu": ["Tỷ lệ nợ / Tổng nguồn vốn", "Tỷ lệ vốn chủ / Tổng nguồn vốn"],
            "Năm (N-1)": [f"{report['ratios']['debt_prev']:.1f}%", f"{report['ratios']['equity_prev']:.1f}%"],
            "Năm (N)": [f"{report['ratios']['debt_next']:.1f}%", f"{report['ratios']['equity_next']:.1f}%"]
        })
        st.dataframe(ratio_df, use_container_width=True)

        st.markdown("### ✅ Nhận xét tổng quát")
        st.write(f"- Doanh nghiệp mở rộng quy mô hoạt động; cơ cấu tài chính ổn định; theo dõi khoản phải thu & hàng tồn kho.")

        # Build PDF bytes
        if st.button("📥 Tải báo cáo PDF (Công ty ABC – Báo cáo tài chính năm 2025)"):
            with st.spinner("Đang tạo PDF..."):
                pdf_bytes = build_pdf_bytes(report, title="Công ty ABC – Báo cáo tài chính năm 2025")
                st.download_button(
                    label="Tải xuống PDF",
                    data=pdf_bytes,
                    file_name="Bao_cao_Tai_Chinh_Company_ABC_2025.pdf",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"❌ Có lỗi xảy ra khi đọc hoặc xử lý file: {e}")
else:
    st.info("📂 Vui lòng tải file Excel để bắt đầu phân tích.")
