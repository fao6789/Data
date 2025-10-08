# app_financial_analysis.py

import streamlit as st
import pandas as pd
from google import genai
from google.genai.errors import APIError

# ========================== #
# ⚙️ CẤU HÌNH TRANG
# ========================== #
st.set_page_config(
    page_title="📊 Phân Tích Báo Cáo Tài Chính",
    layout="wide",
)
st.title("📈 ỨNG DỤNG PHÂN TÍCH BÁO CÁO TÀI CHÍNH DOANH NGHIỆP")

st.markdown("""
Ứng dụng hỗ trợ:
1️⃣ Tính **tốc độ tăng trưởng**  
2️⃣ Tính **tỷ trọng tài sản**  
3️⃣ Tính **chỉ số thanh toán hiện hành**  
4️⃣ Nhận xét **AI tự động (Gemini)**  
""")


# ========================== #
# 🧮 HÀM XỬ LÝ DỮ LIỆU
# ========================== #
def process_financial_data(df):
    """Tính toán tốc độ tăng trưởng và tỷ trọng."""
    
    numeric_cols = ['Năm trước', 'Năm sau']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1️⃣ Tốc độ tăng trưởng
    df['Tốc độ tăng trưởng (%)'] = (
        (df['Năm sau'] - df['Năm trước']) / df['Năm trước'].replace(0, 1e-9)
    ) * 100

    # 2️⃣ Tỷ trọng theo tổng tài sản
    tong_tai_san_row = df[df['Chỉ tiêu'].str.contains('TỔNG CỘNG TÀI SẢN', case=False, na=False)]
    if tong_tai_san_row.empty:
        raise ValueError("Không tìm thấy chỉ tiêu 'TỔNG CỘNG TÀI SẢN' trong file.")

    tong_ts_truoc = tong_tai_san_row['Năm trước'].iloc[0]
    tong_ts_sau = tong_tai_san_row['Năm sau'].iloc[0]

    divisor_N_1 = tong_ts_truoc if tong_ts_truoc != 0 else 1e-9
    divisor_N = tong_ts_sau if tong_ts_sau != 0 else 1e-9

    df['Tỷ trọng Năm trước (%)'] = (df['Năm trước'] / divisor_N_1) * 100
    df['Tỷ trọng Năm sau (%)'] = (df['Năm sau'] / divisor_N) * 100

    return df


# ========================== #
# 🤖 GỌI API GEMINI
# ========================== #
def get_ai_analysis(data_for_ai, api_key):
    """Phân tích dữ liệu tài chính bằng Gemini AI."""
    try:
        client = genai.Client(api_key=api_key)
        model_name = 'gemini-2.5-flash'

        prompt = f"""
        Bạn là chuyên gia phân tích tài chính. 
        Hãy viết 3-4 đoạn nhận xét chuyên nghiệp (không quá 250 từ) 
        về tình hình tài chính của doanh nghiệp dưới đây, 
        tập trung vào:
        - Tốc độ tăng trưởng tài sản & nợ.
        - Thay đổi cơ cấu tài sản.
        - Khả năng thanh toán hiện hành.

        Dữ liệu phân tích:
        {data_for_ai}

        Viết bằng tiếng Việt, giọng văn khách quan.
        """

        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text

    except APIError as e:
        return f"❌ Lỗi gọi Gemini API: {e}"
    except KeyError:
        return "⚠️ Không tìm thấy khóa 'GEMINI_API_KEY' trong Streamlit Secrets."
    except Exception as e:
        return f"⚠️ Đã xảy ra lỗi không xác định: {e}"


# ========================== #
# 📂 TẢI FILE
# ========================== #
uploaded_file = st.file_uploader(
    "📥 1. Tải lên file Excel Báo cáo Tài chính (3 cột: Chỉ tiêu | Năm trước | Năm sau)",
    type=['xlsx', 'xls']
)

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file)
        st.success("✅ File đã được tải lên thành công!")
        # Chuẩn hóa tên cột để tránh lỗi 'Năm sau (N)'
        df.columns = df.columns.str.strip()  # loại bỏ khoảng trắng đầu/cuối
        df.columns = df.columns.str.replace('\u00a0', ' ', regex=True)  # thay ký tự khoảng trắng đặc biệt


        # Chuẩn hóa cột
        if len(df_raw.columns) >= 3:
            df_raw = df_raw.iloc[:, :3]
            df_raw.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
        else:
            st.error("❌ File không hợp lệ: cần ít nhất 3 cột (Chỉ tiêu, Năm trước, Năm sau).")
            st.stop()

        # Xử lý dữ liệu
        df_processed = process_financial_data(df_raw.copy())

        # ========================== #
        # 🧾 2. HIỂN THỊ KẾT QUẢ
        # ========================== #
        st.subheader("📊 2. Phân tích Tăng trưởng & Cơ cấu Tài sản")
        # --- Phân tích tài chính cơ bản ---
        st.subheader("📊 Phân tích tài chính tự động")
        
        try:
            # Tìm tên cột phù hợp nhất (phòng khi file Excel khác nhau)
            col_prev = next((c for c in df.columns if "Năm trước" in c), None)
            col_next = next((c for c in df.columns if "Năm sau" in c), None)
        
            if not col_prev or not col_next:
                st.error("Không tìm thấy cột 'Năm trước' hoặc 'Năm sau' trong file Excel.")
            else:
                def get_value(keyword):
                    match = df[df['Chỉ tiêu'].str.contains(keyword, case=False, na=False)]
                    if not match.empty:
                        return float(match[col_next].values[0])
                    return None
        
                total_assets = get_value("TỔNG CỘNG TÀI SẢN")
                total_liabilities = get_value("TỔNG CỘNG NỢ PHẢI TRẢ")
                total_equity = get_value("VỐN CHỦ SỞ HỮU")
                current_assets = get_value("A. TÀI SẢN NGẮN HẠN")
                current_liabilities = get_value("C. NỢ NGẮN HẠN")
                inventory = get_value("Hàng tồn kho")
        
                if all(v is not None for v in [total_assets, total_liabilities, total_equity, current_assets, current_liabilities]):
                    debt_equity_ratio = total_liabilities / total_equity
                    debt_ratio = total_liabilities / total_assets
                    current_ratio = current_assets / current_liabilities
                    quick_ratio = (current_assets - (inventory or 0)) / current_liabilities
        
                    prev_assets = float(df.loc[df['Chỉ tiêu'].str.contains("TỔNG CỘNG TÀI SẢN"), col_prev].values[0])
                    growth_assets = (total_assets - prev_assets) / prev_assets * 100
        
                    st.write("**Tỷ lệ nợ / vốn chủ sở hữu:** ", f"{debt_equity_ratio:.2f}")
                    st.write("**Hệ số nợ (Debt Ratio):** ", f"{debt_ratio:.2f}")
                    st.write("**Hệ số thanh toán hiện hành (Current Ratio):** ", f"{current_ratio:.2f}")
                    st.write("**Hệ số thanh toán nhanh (Quick Ratio):** ", f"{quick_ratio:.2f}")
                    st.write("**Tăng trưởng tổng tài sản:** ", f"{growth_assets:.2f}%")
                else:
                    st.warning("Không đủ dữ liệu để phân tích tài chính.")
        except Exception as e:
            st.error(f"Lỗi khi phân tích tài chính: {e}")

        

        # Tạo style với fallback nếu matplotlib chưa cài
        style_format = {
            'Năm trước': '{:,.0f}',
            'Năm sau': '{:,.0f}',
            'Tốc độ tăng trưởng (%)': '{:.2f}%',
            'Tỷ trọng Năm trước (%)': '{:.2f}%',
            'Tỷ trọng Năm sau (%)': '{:.2f}%'
        }
        
        try:
            import matplotlib  # chỉ để kiểm tra xem matplotlib có sẵn không
            styled_df = df_processed.style.format(style_format).background_gradient(
                subset=['Tốc độ tăng trưởng (%)'],
                cmap='RdYlGn'
            )
        except Exception:
            # Nếu không có matplotlib, hiển thị bảng bình thường và cảnh báo nhẹ
            styled_df = df_processed.style.format(style_format)
            st.warning("Matplotlib chưa được cài — tạm thời không hiển thị gradient. "
                       "Để bật màu sắc, cài `matplotlib` (pip install matplotlib) hoặc thêm nó vào requirements.txt.")


        st.dataframe(styled_df, use_container_width=True)
        # --- Phân tích tài chính cơ bản ---
        st.subheader("📊 Phân tích tài chính tự động")
        
        try:
            # Lấy các chỉ tiêu cần thiết từ dữ liệu
            def get_value(keyword):
                match = df_processed[df_processed['Chỉ tiêu'].str.contains(keyword, case=False, na=False)]
                if not match.empty:
                    return float(match['Năm sau (N)'].values[0])
                return None
        
            total_assets = get_value("TỔNG CỘNG TÀI SẢN")
            total_liabilities = get_value("TỔNG CỘNG NỢ PHẢI TRẢ")
            total_equity = get_value("VỐN CHỦ SỞ HỮU")
            current_assets = get_value("A. TÀI SẢN NGẮN HẠN")
            current_liabilities = get_value("C. NỢ NGẮN HẠN")
            inventory = get_value("Hàng tồn kho")
        
            if all(v is not None for v in [total_assets, total_liabilities, total_equity, current_assets, current_liabilities]):
                debt_equity_ratio = total_liabilities / total_equity
                debt_ratio = total_liabilities / total_assets
                current_ratio = current_assets / current_liabilities
                quick_ratio = (current_assets - (inventory or 0)) / current_liabilities
                growth_assets = (total_assets - float(df_processed.loc[df_processed['Chỉ tiêu'].str.contains("TỔNG CỘNG TÀI SẢN"), 'Năm trước (N-1)'].values[0])) / \
                                 float(df_processed.loc[df_processed['Chỉ tiêu'].str.contains("TỔNG CỘNG TÀI SẢN"), 'Năm trước (N-1)'].values[0]) * 100
        
                st.write("**Tỷ lệ nợ / vốn chủ sở hữu:** ", f"{debt_equity_ratio:.2f}")
                st.write("**Hệ số nợ (Debt Ratio):** ", f"{debt_ratio:.2f}")
                st.write("**Hệ số thanh toán hiện hành (Current Ratio):** ", f"{current_ratio:.2f}")
                st.write("**Hệ số thanh toán nhanh (Quick Ratio):** ", f"{quick_ratio:.2f}")
                st.write("**Tăng trưởng tổng tài sản:** ", f"{growth_assets:.2f}%")
        
            else:
                st.warning("Không đủ dữ liệu để phân tích tài chính.")
        except Exception as e:
            st.error(f"Lỗi khi phân tích tài chính: {e}")


        # ========================== #
        # 📈 3. CHỈ SỐ TÀI CHÍNH
        # ========================== #
        st.subheader("📈 3. Chỉ số Thanh toán Hiện hành")

        try:
            tsnh_n = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Năm sau'].iloc[0]
            tsnh_n_1 = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Năm trước'].iloc[0]

            no_ngan_han_n = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)]['Năm sau'].iloc[0]
            no_ngan_han_n_1 = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)]['Năm trước'].iloc[0]

        except IndexError:
            st.warning("⚠️ Không tìm thấy 'TÀI SẢN NGẮN HẠN' hoặc 'NỢ NGẮN HẠN'. Vui lòng nhập thủ công.")
            tsnh_n = st.number_input("Tài sản ngắn hạn (Năm sau)", min_value=0.0)
            tsnh_n_1 = st.number_input("Tài sản ngắn hạn (Năm trước)", min_value=0.0)
            no_ngan_han_n = st.number_input("Nợ ngắn hạn (Năm sau)", min_value=0.0)
            no_ngan_han_n_1 = st.number_input("Nợ ngắn hạn (Năm trước)", min_value=0.0)

        thanh_toan_hien_hanh_N = tsnh_n / (no_ngan_han_n or 1e-9)
        thanh_toan_hien_hanh_N_1 = tsnh_n_1 / (no_ngan_han_n_1 or 1e-9)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Thanh toán hiện hành (Năm trước)", f"{thanh_toan_hien_hanh_N_1:.2f} lần")
        with col2:
            st.metric("Thanh toán hiện hành (Năm sau)", f"{thanh_toan_hien_hanh_N:.2f} lần",
                      delta=f"{thanh_toan_hien_hanh_N - thanh_toan_hien_hanh_N_1:.2f}")

        # ========================== #
        # 🤖 4. PHÂN TÍCH BẰNG AI
        # ========================== #
        st.subheader("🤖 4. Nhận xét Tình hình Tài chính (AI)")

        data_for_ai = pd.DataFrame({
            'Chỉ tiêu': [
                'Toàn bộ bảng phân tích',
                'Tăng trưởng Tài sản ngắn hạn (%)',
                'Thanh toán hiện hành (N-1)',
                'Thanh toán hiện hành (N)',
            ],
            'Giá trị': [
                df_processed.to_markdown(index=False),
                f"{df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Tốc độ tăng trưởng (%)'].iloc[0]:.2f}%",
                f"{thanh_toan_hien_hanh_N_1:.2f}",
                f"{thanh_toan_hien_hanh_N:.2f}",
            ]
        }).to_markdown(index=False)

        api_key = st.secrets.get("GEMINI_API_KEY")

        if st.button("🚀 Gửi dữ liệu cho Gemini AI"):
            if api_key:
                with st.spinner("Đang phân tích dữ liệu..."):
                    ai_result = get_ai_analysis(data_for_ai, api_key)
                    st.markdown("### 🧠 Phân tích từ Gemini AI:")
                    st.write(ai_result)
                    st.download_button("💾 Tải kết quả AI", ai_result, "phan_tich_tai_chinh_AI.txt")
            else:
                st.error("❌ Thiếu khóa API. Vui lòng thêm 'GEMINI_API_KEY' vào Streamlit Secrets.")

    except ValueError as ve:
        st.error(f"Lỗi cấu trúc dữ liệu: {ve}")
    except Exception as e:
        st.error(f"Có lỗi xảy ra: {e}. Vui lòng kiểm tra file đầu vào.")

else:
    st.info("📂 Vui lòng tải file Excel để bắt đầu phân tích.")
