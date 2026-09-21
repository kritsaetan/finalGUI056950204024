"""
ระบบคำนวณและแดชบอร์ดภาษีเงินได้บุคคลธรรมดา
================================================
- อ่านข้อมูลจาก tax.csv (หรือไฟล์ CSV ที่อัปโหลด / URL บน GitHub)
- คำนวณภาษีอัตราก้าวหน้าตามกฎหมายไทย
- บันทึกผลลัพธ์ลง tax_output.csv โดยอัตโนมัติ
- แสดงผลเป็นแดชบอร์ด: การ์ดสรุป, กราฟเปรียบเทียบ, กราฟกระจาย, ตารางผลลัพธ์

วิธีรันในเครื่อง:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

วิธี deploy ผ่าน GitHub + Streamlit Community Cloud:
    ดูรายละเอียดใน README.md
"""

import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ----------------------------------------------------------------------
# ค่าคงที่ / การตั้งค่าหน้าเพจ
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="แดชบอร์ดภาษีเงินได้บุคคลธรรมดา",
    page_icon="📊",
    layout="wide",
)

INPUT_FILE_DEFAULT = "tax.csv"
OUTPUT_FILE_DEFAULT = "tax_output.csv"

# อัตราภาษีเงินได้บุคคลธรรมดาแบบขั้นบันได (ประเทศไทย)
# (เพดานเงินได้สุทธิ, อัตราภาษีของช่วงนั้น)
TAX_BRACKETS = [
    (150_000, 0.00),
    (300_000, 0.05),
    (500_000, 0.10),
    (750_000, 0.15),
    (1_000_000, 0.20),
    (2_000_000, 0.25),
    (5_000_000, 0.30),
    (float("inf"), 0.35),
]


def calculate_progressive_tax(net_income: float) -> float:
    """คำนวณภาษีเงินได้บุคคลธรรมดาแบบขั้นบันไดจากเงินได้สุทธิ"""
    if net_income <= 0:
        return 0.0

    tax = 0.0
    lower_bound = 0
    for upper_bound, rate in TAX_BRACKETS:
        if net_income > lower_bound:
            taxable_in_bracket = min(net_income, upper_bound) - lower_bound
            tax += taxable_in_bracket * rate
            lower_bound = upper_bound
        else:
            break
    return round(tax, 2)


def classify_status(diff: float) -> str:
    """จัดสถานะ: ขอคืนภาษี / จ่ายเพิ่ม / พอดี"""
    if diff > 0:
        return "จ่ายเพิ่ม"
    elif diff < 0:
        return "ขอคืนภาษี"
    return "พอดี"


@st.cache_data(show_spinner=False)
def load_from_github(raw_url: str) -> pd.DataFrame:
    """โหลดไฟล์ CSV จาก GitHub raw URL"""
    response = requests.get(raw_url, timeout=15)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text))


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """คำนวณภาษีและคอลัมน์ที่เกี่ยวข้องทั้งหมด"""
    required_cols = {"ชื่อ", "รายได้", "ภาษีหัก ณ ที่จ่าย"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"ไฟล์ข้อมูลขาดคอลัมน์: {', '.join(missing)}")

    df = df.copy()
    df["ภาษีคำนวณได้ (บาท)"] = df["รายได้"].apply(calculate_progressive_tax)
    raw_diff = df["ภาษีคำนวณได้ (บาท)"] - df["ภาษีหัก ณ ที่จ่าย"]
    df["สถานะ"] = raw_diff.apply(classify_status)
    df["ส่วนต่างภาษี (บาท)"] = raw_diff.abs()  # แสดงเป็นค่าบวก สถานะบอกทิศทางแล้ว
    return df


def save_output(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False, encoding="utf-8-sig")


# ----------------------------------------------------------------------
# แถบด้านข้าง: เลือกแหล่งข้อมูล
# ----------------------------------------------------------------------
st.sidebar.header("⚙️ แหล่งข้อมูล")
source_option = st.sidebar.radio(
    "เลือกแหล่งข้อมูล",
    ["ไฟล์ในเครื่อง (tax.csv)", "อัปโหลดไฟล์ CSV", "URL บน GitHub (raw)"],
)

df_raw = None
load_error = None

if source_option == "ไฟล์ในเครื่อง (tax.csv)":
    try:
        df_raw = pd.read_csv(INPUT_FILE_DEFAULT)
    except FileNotFoundError:
        load_error = f"ไม่พบไฟล์ {INPUT_FILE_DEFAULT} ในโฟลเดอร์โปรเจกต์"

elif source_option == "อัปโหลดไฟล์ CSV":
    uploaded = st.sidebar.file_uploader("เลือกไฟล์ CSV", type=["csv"])
    if uploaded is not None:
        df_raw = pd.read_csv(uploaded)

elif source_option == "URL บน GitHub (raw)":
    default_url = (
        "https://raw.githubusercontent.com/<username>/<repo>/main/tax.csv"
    )
    github_url = st.sidebar.text_input("GitHub raw URL ของ tax.csv", value=default_url)
    if github_url and not github_url.startswith("http"):
        load_error = "กรุณาใส่ URL ที่ถูกต้อง (ต้องขึ้นต้นด้วย http/https)"
    elif github_url and "<username>" not in github_url:
        try:
            df_raw = load_from_github(github_url)
        except Exception as exc:  # noqa: BLE001
            load_error = f"โหลดข้อมูลจาก GitHub ไม่สำเร็จ: {exc}"

st.sidebar.markdown("---")
auto_save = st.sidebar.checkbox("บันทึกผลลัพธ์ลง tax_output.csv อัตโนมัติ", value=True)

# ----------------------------------------------------------------------
# หัวเรื่อง
# ----------------------------------------------------------------------
st.markdown("## 📊 ระบบคำนวณและแดชบอร์ดภาษีเงินได้บุคคลธรรมดา")
st.caption(
    f"อ่านข้อมูลจาก `{INPUT_FILE_DEFAULT}` คำนวณภาษีอัตราก้าวหน้า "
    f"และบันทึก `{OUTPUT_FILE_DEFAULT}` อัตโนมัติ"
)
st.markdown("---")

if load_error:
    st.error(load_error)
    st.stop()

if df_raw is None:
    st.info("กรุณาเลือกหรืออัปโหลดไฟล์ข้อมูลจากแถบด้านซ้าย")
    st.stop()

try:
    df = process_dataframe(df_raw)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

if auto_save:
    save_output(df, OUTPUT_FILE_DEFAULT)

# ----------------------------------------------------------------------
# การ์ดสรุปตัวเลขหลัก
# ----------------------------------------------------------------------
total_people = len(df)
total_income = df["รายได้"].sum()
total_tax_calc = df["ภาษีคำนวณได้ (บาท)"].sum()
total_withheld = df["ภาษีหัก ณ ที่จ่าย"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("จำนวนบุคคลทั้งหมด", f"{total_people} คน")
col2.metric("รายได้รวมทั้งหมด", f"฿{total_income:,.2f}")
col3.metric("ภาษีคำนวณรวม (Tax)", f"฿{total_tax_calc:,.2f}")
col4.metric("ภาษีหัก ณ ที่จ่ายรวม", f"฿{total_withheld:,.2f}")

st.markdown("---")

# ----------------------------------------------------------------------
# กราฟวิเคราะห์และเปรียบเทียบข้อมูลภาษี
# ----------------------------------------------------------------------
st.markdown("### 📈 กราฟวิเคราะห์และเปรียบเทียบข้อมูลภาษี")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**เปรียบเทียบภาษีหัก ณ ที่จ่าย vs ภาษีคำนวณจริง**")
    bar_df = df.melt(
        id_vars="ชื่อ",
        value_vars=["ภาษีหัก ณ ที่จ่าย", "ภาษีคำนวณได้ (บาท)"],
        var_name="Tax Type",
        value_name="จำนวนเงิน",
    )
    bar_df["Tax Type"] = bar_df["Tax Type"].replace(
        {"ภาษีคำนวณได้ (บาท)": "ภาษีคำนวณจริง"}
    )
    fig_bar = px.bar(
        bar_df,
        x="ชื่อ",
        y="จำนวนเงิน",
        color="Tax Type",
        barmode="group",
        color_discrete_map={
            "ภาษีหัก ณ ที่จ่าย": "#F4A261",
            "ภาษีคำนวณจริง": "#2A9D8F",
        },
        labels={"จำนวนเงิน": "จำนวนเงิน (บาท)", "ชื่อ": "ชื่อ"},
    )
    fig_bar.update_layout(margin=dict(t=10, b=10), height=380)
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.markdown("**ความสัมพันธ์ระหว่างรายได้กับภาษีที่ต้องชำระ**")
    fig_scatter = px.scatter(
        df,
        x="รายได้",
        y="ภาษีคำนวณได้ (บาท)",
        color="ชื่อ",
        size="ภาษีคำนวณได้ (บาท)",
        text="ชื่อ",
        labels={
            "รายได้": "รายได้สุทธิ (บาท)",
            "ภาษีคำนวณได้ (บาท)": "ภาษีคำนวณ (บาท)",
        },
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(margin=dict(t=10, b=10), height=380)
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------------------------
# ตารางแสดงผลลัพธ์การคำนวณภาษี
# ----------------------------------------------------------------------
st.markdown("### 📋 ตารางแสดงผลลัพธ์การคำนวณภาษี")


def highlight_status(val: str) -> str:
    if val == "จ่ายเพิ่ม":
        return "color: #d62728; font-weight: 600;"
    if val == "ขอคืนภาษี":
        return "color: #2ca02c; font-weight: 600;"
    return ""


def highlight_diff_row(row: pd.Series) -> list[str]:
    style = highlight_status(row["สถานะ"])
    return [style if col == "ส่วนต่างภาษี (บาท)" else "" for col in row.index]


display_df = df.rename(
    columns={
        "รายได้": "รายได้ (บาท)",
        "ภาษีหัก ณ ที่จ่าย": "ภาษีหัก ณ ที่จ่าย (บาท)",
    }
)

# pandas >= 2.1 renamed Styler.applymap -> Styler.map (applymap removed in
# pandas 3.0). Use whichever this environment's pandas provides.
_styler = display_df.style
_map_fn = _styler.map if hasattr(_styler, "map") else _styler.applymap

styled = (
    _map_fn(highlight_status, subset=["สถานะ"])
    .apply(highlight_diff_row, axis=1)
    .format(
        {
            "รายได้ (บาท)": "{:,.2f}",
            "ภาษีหัก ณ ที่จ่าย (บาท)": "{:,.2f}",
            "ภาษีคำนวณได้ (บาท)": "{:,.2f}",
            "ส่วนต่างภาษี (บาท)": "{:,.2f}",
        }
    )
)
st.dataframe(styled, use_container_width=True)

st.download_button(
    "⬇️ ดาวน์โหลดผลลัพธ์ (tax_output.csv)",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name=OUTPUT_FILE_DEFAULT,
    mime="text/csv",
)

if auto_save:
    st.caption(f"✅ บันทึกผลลัพธ์ล่าสุดไว้ที่ `{OUTPUT_FILE_DEFAULT}` เรียบร้อยแล้ว")
