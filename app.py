import streamlit as st
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="مصاريف تصليح السيارات", page_icon="🚗", layout="wide")

st.markdown("""
<style>
    body, .stApp { direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5, h6, p, label, div { text-align: right; }
    .stTextInput input, .stNumberInput input { text-align: right; }
</style>
""", unsafe_allow_html=True)

EXPENSES_FILE = "expenses.xlsx"
LOOKUPS_FILE = "lookups.xlsx"

def init_files():
    if not os.path.exists(EXPENSES_FILE):
        df = pd.DataFrame(columns=["رقم الفاتورة", "رقم السيارة", "اسم السائق", "التاريخ", "المبلغ (د.ك)", "المشكلة", "نوع المركبة", "موديل المركبة"])
        df.to_excel(EXPENSES_FILE, index=False)
    if not os.path.exists(LOOKUPS_FILE):
        lookups = {
            "أرقام السيارات": ["12345", "67890", "11111", "22222", "33333"],
            "أسماء السائقين": ["أحمد محمد", "علي سالم", "محمد إبراهيم", "خالد يوسف"],
            "أنواع المركبات": ["تريللا", "باص موظفين", "باص عمال", "هاف لوري", "أخرى"],
            "الموديلات": ["تويوتا", "نيسان", "هينو", "مرسيدس", "إيسوزو", "ميتسوبيشي"]
        }
        with pd.ExcelWriter(LOOKUPS_FILE) as writer:
            for name, values in lookups.items():
                pd.DataFrame({name: values}).to_excel(writer, sheet_name=name, index=False)

def load_expenses():
    return pd.read_excel(EXPENSES_FILE)

def load_lookups():
    lookups = {}
    xls = pd.ExcelFile(LOOKUPS_FILE)
    for sheet in xls.sheet_names:
        lookups[sheet] = pd.read_excel(LOOKUPS_FILE, sheet_name=sheet)[sheet].dropna().tolist()
    return lookups

def save_expense(new_row):
    df = load_expenses()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(EXPENSES_FILE, index=False)

def invoice_exists(invoice_no):
    df = load_expenses()
    if df.empty:
        return None
    match = df[df["رقم الفاتورة"].astype(str) == str(invoice_no)]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None

init_files()
lookups = load_lookups()

st.title("🚗 برنامج مصاريف تصليح السيارات")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["➕ إضافة فاتورة", "📋 عرض الفواتير", "📊 التقارير"])

with tab1:
    st.subheader("➕ إضافة فاتورة جديدة")
    with st.form("invoice_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            invoice_no = st.text_input("🔢 رقم الفاتورة *", placeholder="مثال: INV-001")
            car_no = st.selectbox("🚙 رقم السيارة *", ["-- اختر --"] + lookups["أرقام السيارات"])
            driver = st.selectbox("👤 اسم السائق *", ["-- اختر --"] + lookups["أسماء السائقين"])
            inv_date = st.date_input("📅 التاريخ *", value=date.today())
        with col2:
            amount = st.number_input("💰 المبلغ (د.ك) *", min_value=0.0, step=0.500, format="%.3f")
            problem = st.text_area("🔧 المشكلة *", placeholder="وصف المشكلة أو الإصلاح")
            car_type = st.selectbox("🚛 نوع المركبة *", ["-- اختر --"] + lookups["أنواع المركبات"])
            car_model = st.selectbox("🏷️ موديل المركبة *", ["-- اختر --"] + lookups["الموديلات"])
        submitted = st.form_submit_button("💾 حفظ الفاتورة", use_container_width=True)
        if submitted:
            errors = []
            if not invoice_no.strip(): errors.append("رقم الفاتورة مطلوب")
            if car_no == "-- اختر --": errors.append("رقم السيارة مطلوب")
            if driver == "-- اختر --": errors.append("اسم السائق مطلوب")
            if amount <= 0: errors.append("المبلغ لازم يكون أكبر من صفر")
            if not problem.strip(): errors.append("المشكلة مطلوبة")
            if car_type == "-- اختر --": errors.append("نوع المركبة مطلوب")
            if car_model == "-- اختر --": errors.append("موديل المركبة مطلوب")
            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
            else:
                existing = invoice_exists(invoice_no)
                if existing:
                    st.error(f"🚫 رقم الفاتورة ({invoice_no}) مستخدم من قبل!")
                    st.warning("📋 بيانات الفاتورة السابقة:")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.info(f"**رقم السيارة:** {existing['رقم السيارة']}")
                        st.info(f"**اسم السائق:** {existing['اسم السائق']}")
                        st.info(f"**التاريخ:** {existing['التاريخ']}")
                        st.info(f"**المبلغ:** {existing['المبلغ (د.ك)']} د.ك")
                    with col_b:
                        st.info(f"**المشكلة:** {existing['المشكلة']}")
                        st.info(f"**نوع المركبة:** {existing['نوع المركبة']}")
                        st.info(f"**الموديل:** {existing['موديل المركبة']}")
                else:
                    new_row = {"رقم الفاتورة": invoice_no.strip(), "رقم السيارة": car_no, "اسم السائق": driver, "التاريخ": str(inv_date), "المبلغ (د.ك)": amount, "المشكلة": problem.strip(), "نوع المركبة": car_type, "موديل المركبة": car_model}
                    save_expense(new_row)
                    st.success(f"✅ تم حفظ الفاتورة {invoice_no} بنجاح!")
                    st.balloons()

with tab2:
    st.subheader("📋 كل الفواتير المسجلة")
    df = load_expenses()
    if df.empty:
        st.info("📭 مفيش فواتير مسجلة لحد الآن")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("🔍 بحث", "")
        with col2:
            filter_car = st.selectbox("🚙 فلترة بالسيارة", ["الكل"] + lookups["أرقام السيارات"])
        with col3:
            filter_type = st.selectbox("🚛 فلترة بالنوع", ["الكل"] + lookups["أنواع المركبات"])
        filtered = df.copy()
        if search:
            filtered = filtered[filtered.astype(str).apply(lambda r: r.str.contains(search, case=False).any(), axis=1)]
        if filter_car != "الكل":
            filtered = filtered[filtered["رقم السيارة"].astype(str) == filter_car]
        if filter_type != "الكل":
            filtered = filtered[filtered["نوع المركبة"] == filter_type]
        st.markdown(f"**عدد الفواتير: {len(filtered)}**")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📊 التقارير والإحصائيات")
    df = load_expenses()
    if df.empty:
        st.info("📭 مفيش بيانات")
    else:
        df["المبلغ (د.ك)"] = pd.to_numeric(df["المبلغ (د.ك)"], errors="coerce")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 الإجمالي", f"{df['المبلغ (د.ك)'].sum():,.3f} د.ك")
        col2.metric("🧾 عدد الفواتير", len(df))
        col3.metric("🚗 عدد السيارات", df["رقم السيارة"].nunique())
        col4.metric("👤 عدد السائقين", df["اسم السائق"].nunique())
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🚙 المصاريف حسب السيارة")
            st.bar_chart(df.groupby("رقم السيارة")["المبلغ (د.ك)"].sum())
        with col2:
            st.markdown("### 🚛 المصاريف حسب النوع")
            st.bar_chart(df.groupby("نوع المركبة")["المبلغ (د.ك)"].sum())
