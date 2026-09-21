# finalGUI056950204024
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="ระบบคำนวณและแดชบอร์ดภาษี", layout="wide")

st.title("📊 ระบบคำนวณและแดชบอร์ดภาษีเงินได้บุคคลธรรมดา")
st.caption("อ่านข้อมูลจาก tax.csv คำนวณภาษีอัตราก้าวหน้า และบันทึก tax_output.csv อัตโนมัติ")

# 2. ฟังก์ชันคำนวณภาษีเงินได้บุคคลธรรมดาแบบขั้นบันได
def calculate_progressive_tax(income):
    if income <= 150000:
        return 0.0
    elif income <= 300000:
        return (income - 150000) * 0.05
    elif income <= 500000:
        return 7500 + (income - 300000) * 0.10
    elif income <= 750000:
        return 27500 + (income - 500000) * 0.15
    elif income <= 1000000:
        return 65000 + (income - 750000) * 0.20
    elif income <= 2000000:
        return 115000 + (income - 1000000) * 0.25
    elif income <= 5000000:
        return 365000 + (income - 2000000) * 0.30
    else:
        return 1265000 + (income - 5000000) * 0.35

# 3. อ่านไฟล์ tax.csv
try:
    df = pd.read_csv('tax.csv', encoding='utf-8-sig')

    # แปลงคอลัมน์ income และ withholding_tax ให้เป็นตัวเลขเพื่อนำไปคำนวณ
    df['income_num'] = df['income'].astype(str).str.replace(',', '').str.strip().astype(float)
    df['w_tax_num'] = df['withholding_tax'].astype(str).str.replace(',', '').str.strip().astype(float)

    # คำนวณภาษีตามจริงจากรายได้ในไฟล์
    df['tax_num'] = df['income_num'].apply(calculate_progressive_tax)

    # คำนวณสถานะและส่วนต่างภาษี
    df['diff_num'] = df['tax_num'] - df['w_tax_num']
    df['สถานะ'] = df['diff_num'].apply(lambda x: 'จ่ายเพิ่ม' if x > 0 else ('ขอคืนภาษี' if x < 0 else 'พอดี'))
    df['ส่วนต่างภาษี (บาท)'] = df['diff_num'].abs()

    # บันทึกผลการคำนวณลงไฟล์ tax_output.csv อัตโนมัติ
    df_output = df.copy()
    df_output['tax'] = df_output['tax_num'].map('{:,.2f}'.format)
    df_output[['name', 'income', 'withholding_tax', 'tax']].to_csv('tax_output.csv', index=False, encoding='utf-8-sig')

    # --- ส่วนที่ 1: ตัวเลขสรุปภาพรวม (Metrics) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("จำนวนบุคคลทั้งหมด", f"{len(df)} คน")
    col2.metric("รายได้รวมทั้งหมด", f"฿{df['income_num'].sum():,.2f}")
    col3.metric("ภาษีคำนวณรวม (Tax)", f"฿{df['tax_num'].sum():,.2f}")
    col4.metric("ภาษีหัก ณ ที่จ่ายรวม", f"฿{df['w_tax_num'].sum():,.2f}")

    st.divider()

    # --- ส่วนที่ 2: กราฟวิเคราะห์ ---
    st.subheader("📈 กราฟวิเคราะห์และเปรียบเทียบข้อมูลภาษี")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("**เปรียบเทียบภาษีหัก ณ ที่จ่าย vs ภาษีคำนวณจริง**")
        fig_bar = go.Figure(data=[
            go.Bar(name='ภาษีหัก ณ ที่จ่าย', x=df['name'], y=df['w_tax_num'], marker_color='#F28E2B'),
            go.Bar(name='ภาษีคำนวณตามจริง', x=df['name'], y=df['tax_num'], marker_color='#4E79A7')
        ])
        fig_bar.update_layout(barmode='group', xasis_title="ชื่อ", yaxis_title="จำนวนเงิน (บาท)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with g_col2:
        st.markdown("**ความสัมพันธ์ระหว่างรายได้กับภาษีที่ต้องชำระ**")
        fig_scatter = px.scatter(
            df, 
            x="income_num", 
            y="tax_num", 
            color="name", 
            size="income_num",
            text="name",
            labels={"income_num": "รายได้สุทธิ (บาท)", "tax_num": "ภาษีคำนวณ (บาท)"}
        )
        fig_scatter.update_traces(textposition='top center')
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # --- ส่วนที่ 3: ตารางสรุปผล ---
    st.subheader("📋 ตารางแสดงผลลัพธ์การคำนวณภาษี")

    df_display = pd.DataFrame({
        "ชื่อ": df['name'],
        "รายได้ (บาท)": df['income_num'].map('{:,.2f}'.format),
        "ภาษีหัก ณ ที่จ่าย (บาท)": df['w_tax_num'].map('{:,.2f}'.format),
        "ภาษีคำนวณได้ (บาท)": df['tax_num'].map('{:,.2f}'.format),
        "สถานะ": df['สถานะ'],
        "ส่วนต่างภาษี (บาท)": df['ส่วนต่างภาษี (บาท)'].map('{:,.2f}'.format)
    })

    st.dataframe(df_display, use_container_width=True)

except FileNotFoundError:
    st.error("❌ ไม่พบไฟล์ `tax.csv` กรุณาตรวจสอบว่ามีไฟล์ `tax.csv` อยู่ในโฟลเดอร์เดียวกันหรือไม่")
