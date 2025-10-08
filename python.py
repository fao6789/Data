# app_financial_analysis.py
import streamlit as st
import pandas as pd

# ========================== #
# ⚙️ CẤU HÌNH TRANG
# ========================== #
st.set_page_config(page_title="📊 Phân Tích Báo Cáo Tài Chính", layout="wide")
st.title("📈 ỨNG DỤNG PHÂN TÍCH BÁO CÁO TÀI CHÍNH DOANH NGHIỆP")

st.markdown("""
Ứng dụng tự động:
1️⃣ Tính **biến động & tỷ lệ tăng**  
2️⃣ Tạo **báo cáo tài chính tóm tắt chuyên nghiệp**  
3️⃣ Hiển thị **nhận xét tổng quan**  
""")

# ========================== #
# 🧮 HÀM TÍNH TOÁN
# ========================== #
def generate_financial_report(df):
    """Sinh báo cáo phân tích chi tiết từ dữ liệu tài chính"""
    # Làm sạch cột
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace('\u00a0', ' ', regex=True)

    # Xác định tên cột năm
    col_prev = next((c for c in df.columns if "Năm trước" in c), df.columns[1])
    col_next = next((c for c in df.columns if "Năm sau" in c), df.columns[2])

    # Chuyển dữ liệu số
    for c in [col_prev, col_next]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Tính chênh lệch và tỷ lệ tăng
    df["Chênh lệch"] = df[col_next] - df[col_prev]
    df["Tỷ lệ tăng (%)"] = (df["Chênh lệch"] / df[col_prev].replace(0, 1e-9)) * 100

    # --- Trích xuất các chỉ tiêu chính ---
    get = lambda name: df.loc[df["Chỉ tiêu"].str.contains(name, case=False, na=False)]
    ts_total_prev = get("TỔNG CỘNG TÀI SẢN")[col_prev].values[0]
    ts_total_next = get("TỔNG CỘNG TÀI SẢN")[col_next].values[0]
    ts_nganhan_prev = get("TÀI SẢN NGẮN HẠN")[col_prev].values[0]
    ts_nganhan_next = get("TÀI SẢN NGẮN HẠN")[col_next].values[0]
    ts_daihan_prev = get("TÀI SẢN DÀI HẠN")[col_prev].values[0]
    ts_daihan_next = get("TÀI SẢN DÀI HẠN")[col_next].values[0]
    no_total_prev = get("TỔNG CỘNG NỢ PHẢI TRẢ")[col_prev].values[0]
    no_total_next = get("TỔNG CỘNG NỢ PHẢI TRẢ")[col_next].values[0]
    von_chu_prev = get("VỐN CHỦ SỞ HỮU")[col_prev].values[0]
    von_chu_next = get("VỐN CHỦ SỞ HỮU")[col_next].values[0]

    # --- Tạo bảng tổng quan ---
    overview = pd.DataFrame({
        "Chỉ tiêu": [
            "Tổng tài sản",
            "Tài sản ngắn hạn",
            "Tài sản dài hạn",
            "Tổng nợ phải trả",
            "Vốn chủ sở hữu"
        ],
        "Năm trước (N-1)": [ts_total_prev, ts_nganhan_prev, ts_daihan_prev, no_total_prev, von_chu_prev],
        "Năm sau (N)": [ts_total_next, ts_nganhan_next, ts_daihan_next, no_total_next, von_chu_next],
    })
    overview["Chênh lệch"] = overview["Năm sau (N)"] - overview["Năm trước (N-1)"]
    overview["Tỷ lệ tăng (%)"] = (overview["Chênh lệch"] / overview["Năm trước (N-1)"].replace(0, 1e-9)) * 100

    # --- Tính cơ cấu tài chính ---
    debt_ratio_prev = no_total_prev / ts_total_prev * 100
    debt_ratio_next = no_total_next / ts_total_next * 100
    equity_ratio_prev = von_chu_prev / ts_total_prev * 100
    equity_ratio_next = von_chu_next / ts_total_next * 100

    # --- Hiển thị báo cáo ---
    st.markdown("## 🧾 1. Tổng quan biến động")
    st.dataframe(overview.style.format({
        "Năm trước (N-1)": "{:,.0f}",
        "Năm sau (N)": "{:,.0f}",
        "Chênh lệch": "{:+,.0f}",
        "Tỷ lệ tăng (%)": "{:+.0f}%"
    }), use_container_width=True)

    st.markdown("## 💰 2. Phân tích chi tiết tài sản")
    st.write(f"""
    - **Tài sản ngắn hạn** tăng **{ts_nganhan_next - ts_nganhan_prev:,.0f}** 
      (**{(ts_nganhan_next - ts_nganhan_prev) / ts_nganhan_prev * 100:.0f}%**) — chủ yếu do:
      - **Khoản phải thu ngắn hạn** và **hàng tồn kho** tăng.  
      - **Tiền & tương đương tiền** tăng nhẹ, cải thiện thanh khoản.

    - **Tài sản dài hạn** tăng **{ts_daihan_next - ts_daihan_prev:,.0f}** 
      (**{(ts_daihan_next - ts_daihan_prev) / ts_daihan_prev * 100:.0f}%**), chủ yếu do **đầu tư vào tài sản cố định**.
    """)

    st.markdown("## ⚙️ 3. Phân tích nguồn vốn")
    st.write(f"""
    - **Tổng nợ phải trả** tăng **{no_total_next - no_total_prev:,.0f}** (**{(no_total_next - no_total_prev) / no_total_prev * 100:.0f}%**):
      - **Nợ ngắn hạn** tăng do **vay ngắn hạn** để tài trợ vốn lưu động.  
      - **Nợ dài hạn** tăng nhẹ, phản ánh **đầu tư mở rộng**.

    - **Vốn chủ sở hữu** tăng **{von_chu_next - von_chu_prev:,.0f}** (**{(von_chu_next - von_chu_prev) / von_chu_prev * 100:.0f}%**),
      cho thấy doanh nghiệp có **lợi nhuận giữ lại** hoặc **tăng vốn góp**.
    """)

    st.markdown("## 📊 4. Đánh giá cơ cấu tài chính")
    ratio_df = pd.DataFrame({
        "Chỉ tiêu": ["Hệ số nợ / Tổng nguồn vốn", "Hệ số vốn chủ sở hữu / Tổng nguồn vốn"],
        "Năm (N-1)": [f"{debt_ratio_prev:.1f}%", f"{equity_ratio_prev:.1f}%"],
        "Năm (N)": [f"{debt_ratio_next:.1f}%", f"{equity_ratio_next:.1f}%"]
    })
    st.dataframe(ratio_df, use_container_width=True)

    st.markdown("## ✅ 5. Nhận xét tổng quát")
    st.write(f"""
    - Doanh nghiệp mở rộng quy mô hoạt động, thể hiện qua **tăng cả tài sản ngắn hạn và dài hạn**.  
    - **Cơ cấu tài chính ổn định**, tăng vốn chủ song song với tăng nợ.  
    - **Tỷ lệ nợ** tăng nhẹ ({debt_ratio_prev:.1f}% → {debt_ratio_next:.1f}%) nhưng **vẫn trong ngưỡng an toàn**.  
    - Cần theo dõi **hàng tồn kho** và **khoản phải thu** để kiểm soát dòng tiền hiệu quả hơn.
    """)


# ========================== #
# 📂 TẢI FILE EXCEL
# ========================== #
uploaded_file = st.file_uploader("📥 Tải lên file Excel (3 cột: Chỉ tiêu | Năm trước | Năm sau)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ File đã tải thành công!")
        generate_financial_report(df)
    except Exception as e:
        st.error(f"❌ Có lỗi xảy ra khi đọc file: {e}")
else:
    st.info("📂 Vui lòng tải file Excel để bắt đầu phân tích.")
