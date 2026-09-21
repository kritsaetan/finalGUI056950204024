# ระบบคำนวณและแดชบอร์ดภาษีเงินได้บุคคลธรรมดา

แอป Streamlit ที่อ่านข้อมูลรายได้จาก `tax.csv` คำนวณภาษีเงินได้บุคคลธรรมดา
แบบอัตราก้าวหน้า บันทึกผลลง `tax_output.csv` โดยอัตโนมัติ และแสดงผลเป็น
แดชบอร์ด (การ์ดสรุป, กราฟแท่งเปรียบเทียบ, กราฟกระจาย, ตารางผลลัพธ์)

## ไฟล์ในโปรเจกต์
- `streamlit_app.py` — โค้ดแอปหลัก
- `tax.csv` — ข้อมูลตัวอย่าง (ชื่อ, รายได้, ภาษีหัก ณ ที่จ่าย)
- `requirements.txt` — ไลบรารีที่ต้องติดตั้ง

## รันในเครื่องตัวเอง
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## นำขึ้น GitHub
```bash
git init
git add .
git commit -m "Initial commit: tax dashboard"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

## Deploy บน Streamlit Community Cloud (เชื่อมกับ GitHub)
1. เข้า https://share.streamlit.io/ แล้วล็อกอินด้วยบัญชี GitHub
2. กด **New app** → เลือก repository, branch (`main`), และไฟล์หลัก
   `streamlit_app.py`
3. กด **Deploy** — ทุกครั้งที่ push โค้ดใหม่ขึ้น GitHub แอปจะอัปเดตอัตโนมัติ

## ใช้ข้อมูลจาก GitHub โดยตรง
ในแถบด้านซ้ายของแอป เลือก **"URL บน GitHub (raw)"** แล้วใส่ raw URL ของไฟล์
CSV เช่น:
```
https://raw.githubusercontent.com/<username>/<repo>/main/tax.csv
```

## อัตราภาษีที่ใช้คำนวณ (ขั้นบันได)
| เงินได้สุทธิ (บาท)      | อัตราภาษี |
|--------------------------|-----------|
| 0 – 150,000               | ยกเว้น    |
| 150,001 – 300,000         | 5%        |
| 300,001 – 500,000         | 10%       |
| 500,001 – 750,000         | 15%       |
| 750,001 – 1,000,000       | 20%       |
| 1,000,001 – 2,000,000     | 25%       |
| 2,000,001 – 5,000,000     | 30%       |
| มากกว่า 5,000,000         | 35%       |

> หมายเหตุ: สมมติว่าคอลัมน์ "รายได้" ในไฟล์ CSV เป็นเงินได้สุทธิหลังหักค่าใช้จ่าย
> และค่าลดหย่อนแล้ว หากข้อมูลของคุณเป็นรายได้ก่อนหักค่าใช้จ่าย/ลดหย่อน
> ให้ปรับฟังก์ชัน `calculate_progressive_tax` ใน `streamlit_app.py` เพิ่มเติม
