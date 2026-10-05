import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import io

from dashboard import render_dashboard

st.set_page_config(page_title="إدارة مخازن مصنع القطامى", page_icon="🏭", layout="wide")

st.markdown("""
<style>
    body, .stApp { direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5, h6, p, label, div { text-align: right; }
    .stTextInput input, .stNumberInput input { text-align: right; }
    [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    @media print { .stApp { background: white !important; } }
</style>
""", unsafe_allow_html=True)

EXPENSES_FILE = "expenses.xlsx"
VEHICLES_FILE = "vehicles.xlsx"
DRIVERS_FILE = "drivers.xlsx"

DEFAULT_DRIVERS = ["مرزوق", "عبدالحميد", "شامير", "محمود", "ياسر", "منور", "أكرم", "حفصل", 
                   "عاطف", "على", "سيد", "عبده", "عبدالله", "خالد", "عبدالعظيم", "أسامة", "ثامر"]

DEFAULT_VEHICLES = [
    {"الرقم": "97403", "الموديل": "1993", "النوع": "تيريلا"},
    {"الرقم": "57637", "الموديل": "2002", "النوع": "تيريلا"},
    {"الرقم": "35573", "الموديل": "2006", "النوع": "تيريلا"},
    {"الرقم": "30062", "الموديل": "2008", "النوع": "تيريلا"},
    {"الرقم": "55201", "الموديل": "2010", "النوع": "تيريلا"},
    {"الرقم": "55224", "الموديل": "2010", "النوع": "تيريلا"},
    {"الرقم": "60276", "الموديل": "2013", "النوع": "تيريلا"},
    {"الرقم": "57588", "الموديل": "2014", "النوع": "تيريلا"},
    {"الرقم": "38247", "الموديل": "2023", "النوع": "هاف لوري"},
    {"الرقم": "14115", "الموديل": "2017", "النوع": "هاف لوري"},
    {"الرقم": "61306", "الموديل": "2017", "النوع": "هاف لوري"},
    {"الرقم": "36497", "الموديل": "2017", "النوع": "هاف لوري"},
    {"الرقم": "37024", "الموديل": "2014", "النوع": "هاف لوري"},
    {"الرقم": "46802", "الموديل": "2014", "النوع": "هاف لوري"},
    {"الرقم": "94395", "الموديل": "2021", "النوع": "باص فورد"},
    {"الرقم": "55688", "الموديل": "2016", "النوع": "باص العمال"},
    {"الرقم": "51000", "الموديل": "2022", "النوع": "باص الموظفين"},
    {"الرقم": "67103", "الموديل": "2023", "النوع": "باص الفك والتركيب"},
    {"الرقم": "63167", "الموديل": "2016", "النوع": "باص الفوتن"},
    {"الرقم": "96836", "الموديل": "2012", "النوع": "باص الدليكا"},
    {"الرقم": "23927", "الموديل": "5 طن", "النوع": "رافعة"},
    {"الرقم": "15157", "الموديل": "3 طن", "النوع": "رافعة"},
    {"الرقم": "30343", "الموديل": "3.5 طن", "النوع": "رافعة"},
    {"الرقم": "30341", "الموديل": "7 طن", "النوع": "رافعة"},
]

def init_files():
    if not os.path.exists(EXPENSES_FILE):
        df = pd.DataFrame(columns=["رقم الفاتورة", "رقم السيارة", "اسم السائق", "التاريخ", 
                                    "المبلغ (د.ك)", "المشكلة", "نوع المركبة", "سنة الصنع"])
        df.to_excel(EXPENSES_FILE, index=False)
    if not os.path.exists(VEHICLES_FILE):
        pd.DataFrame(DEFAULT_VEHICLES).to_excel(VEHICLES_FILE, index=False)
    if not os.path.exists(DRIVERS_FILE):
        pd.DataFrame({"السائقين": DEFAULT_DRIVERS}).to_excel(DRIVERS_FILE, index=False)

def load_vehicles():
    try:
        df = pd.read_excel(VEHICLES_FILE)
        df["الرقم"] = df["الرقم"].astype(str)
        return df
    except:
        df = pd.DataFrame(DEFAULT_VEHICLES)
        df.to_excel(VEHICLES_FILE, index=False)
        return df

def load_drivers():
    try:
        df = pd.read_excel(DRIVERS_FILE)
        return df["السائقين"].dropna().astype(str).tolist()
    except:
        return DEFAULT_DRIVERS

def save_drivers(drivers):
    pd.DataFrame({"السائقين": drivers}).to_excel(DRIVERS_FILE, index=False)

def save_vehicles(df):
    df.to_excel(VEHICLES_FILE, index=False)

def load_expenses():
    try:
        return pd.read_excel(EXPENSES_FILE)
    except:
        return pd.DataFrame()

def save_expense(new_row):
    df = load_expenses()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(EXPENSES_FILE, index=False)

def save_all_expenses(df):
    df.to_excel(EXPENSES_FILE, index=False)

def invoice_exists(invoice_no):
    df = load_expenses()
    if df.empty:
        return None
    match = df[df["رقم الفاتورة"].astype(str) == str(invoice_no)]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None

def get_vehicle_info(car_no):
    df = load_vehicles()
    match = df[df["الرقم"].astype(str) == str(car_no)]
    if not match.empty:
        row = match.iloc[0]
        return row["النوع"], row["الموديل"]
    return None, None

def to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='الفواتير')
        workbook = writer.book
        worksheet = writer.sheets['الفواتير']
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        cell_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 18, cell_format)
        worksheet.right_to_left()
    return output.getvalue()

@st.dialog("✏️ تعديل الفاتورة", width="large")
def edit_invoice_dialog(inv_no):
    full_df = load_expenses()
    match = full_df[full_df["رقم الفاتورة"].astype(str) == str(inv_no)]
    if match.empty:
        st.error("⚠️ الفاتورة مش موجودة")
        if st.button("إغلاق"):
            st.session_state["edit_invoice"] = None
            st.rerun()
        return
    row_to_edit = match.iloc[0]
    vehicles_df_local = load_vehicles()
    drivers_list_local = load_drivers()
    car_list = vehicles_df_local["الرقم"].astype(str).tolist()
    current_car = str(row_to_edit['رقم السيارة'])
    car_idx = car_list.index(current_car) if current_car in car_list else 0
    current_driver = str(row_to_edit['اسم السائق'])
    driver_idx = drivers_list_local.index(current_driver) if current_driver in drivers_list_local else 0
    try:
        current_date = pd.to_datetime(row_to_edit['التاريخ']).date()
    except:
        current_date = date.today()
    try:
        current_amount = float(row_to_edit['المبلغ (د.ك)'])
    except:
        current_amount = 0.0
    st.markdown(f"**رقم الفاتورة:** `{inv_no}`")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        new_car = st.selectbox("🚙 رقم السيارة", car_list, index=car_idx, key="edit_car")
        new_driver = st.selectbox("👤 اسم السائق", drivers_list_local, index=driver_idx, key="edit_driver")
        new_date = st.date_input("📅 التاريخ", value=current_date, key="edit_date")
    with col2:
        new_amount = st.number_input("💰 المبلغ (د.ك)", min_value=0.0, step=0.500, format="%.3f", value=current_amount, key="edit_amount")
        new_problem = st.text_area("🔧 المشكلة", value=str(row_to_edit['المشكلة']), key="edit_problem")
    new_type, new_year = get_vehicle_info(new_car)
    if new_type:
        st.info(f"🚛 نوع المركبة: **{new_type}** | 📅 سنة الصنع: **{new_year}**")
    st.markdown("---")
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 حفظ التعديلات", use_container_width=True, type="primary", key="save_edit_dialog"):
            full_df = load_expenses()
            mask = full_df["رقم الفاتورة"].astype(str) == str(inv_no)
            full_df.loc[mask, "رقم السيارة"] = new_car
            full_df.loc[mask, "اسم السائق"] = new_driver
            full_df.loc[mask, "التاريخ"] = str(new_date)
            full_df.loc[mask, "المبلغ (د.ك)"] = new_amount
            full_df.loc[mask, "المشكلة"] = new_problem
            full_df.loc[mask, "نوع المركبة"] = new_type if new_type else ""
            full_df.loc[mask, "سنة الصنع"] = new_year if new_year else ""
            full_df.to_excel(EXPENSES_FILE, index=False)
            st.session_state["edit_invoice"] = None
            st.rerun()
    with col_cancel:
        if st.button("❌ إلغاء", use_container_width=True, key="cancel_edit_dialog"):
            st.session_state["edit_invoice"] = None
            st.rerun()

@st.dialog("🗑️ تأكيد الحذف")
def delete_invoice_dialog(inv_no):
    st.warning(f"⚠️ **هل أنت متأكد من حذف الفاتورة:** `{inv_no}` ؟")
    st.markdown("**لا يمكن التراجع عن هذا الإجراء.**")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ نعم، احذف", type="primary", use_container_width=True, key="confirm_del_dialog"):
            full_df = load_expenses()
            full_df = full_df[full_df["رقم الفاتورة"].astype(str) != str(inv_no)]
            full_df.to_excel(EXPENSES_FILE, index=False)
            st.session_state["delete_invoice"] = None
            st.rerun()
    with col_no:
        if st.button("❌ إلغاء", use_container_width=True, key="cancel_del_dialog"):
            st.session_state["delete_invoice"] = None
            st.rerun()

init_files()
vehicles_df = load_vehicles()
drivers_list = load_drivers()

with st.sidebar:
    st.markdown("## 🏭 إدارة مخازن")
    st.markdown("### مصنع القطامى للمواد العزلة")
    st.markdown("---")
    st.markdown("### 📋 الأقسام")
    st.markdown("🚗 **مصاريف صيانة السيارات**")
    st.markdown("---")
    st.markdown("### ℹ️ عن البرنامج")
    st.markdown("**الإصدار:** 1.0")

st.title("🏭 إدارة مخازن مصنع القطامى للمواد العزلة")
st.markdown("### 🚗 قسم مصاريف صيانة السيارات")
st.markdown("---")

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "📊 لوحة المعلومات", 
    "➕ إضافة فاتورة", 
    "📋 عرض الفواتير", 
    "📊 التقارير", 
    "⚙️ الإعدادات"
])

# ==================== تبويب 0: لوحة المعلومات ====================
with tab0:
    df_dash = load_expenses()
    render_dashboard(df_dash, vehicles_df, drivers_list)

# ==================== تبويب 1: إضافة فاتورة ====================
with tab1:
    st.subheader("➕ إضافة فاتورة جديدة")
    col1, col2 = st.columns(2)
    with col1:
        invoice_no = st.text_input("🔢 رقم الفاتورة *", placeholder="مثال: INV-001", key="inv_no")
        car_no = st.selectbox("🚙 رقم السيارة *", ["-- اختر --"] + vehicles_df["الرقم"].astype(str).tolist(), key="car_sel")
        driver = st.selectbox("👤 اسم السائق *", ["-- اختر --"] + drivers_list, key="driver_sel")
        inv_date = st.date_input("📅 التاريخ *", value=date.today(), key="inv_date")
    with col2:
        amount = st.number_input("💰 المبلغ (د.ك) *", min_value=0.0, step=0.500, format="%.3f", key="amt")
        problem = st.text_area("🔧 المشكلة *", placeholder="وصف المشكلة أو الإصلاح", key="prob")
        if car_no != "-- اختر --":
            car_type, car_year = get_vehicle_info(car_no)
            if car_type:
                st.success(f"🚛 **نوع المركبة:** {car_type}")
                st.info(f"📅 **سنة الصنع:** {car_year}")
                st.session_state["auto_car_type"] = car_type
                st.session_state["auto_car_year"] = car_year
        else:
            st.warning("⏳ اختر رقم السيارة لعرض بياناتها تلقائيًا")
            st.session_state["auto_car_type"] = None
            st.session_state["auto_car_year"] = None
    st.markdown("---")
    submitted = st.button("💾 حفظ الفاتورة", use_container_width=True, type="primary")
    if submitted:
        errors = []
        if not invoice_no.strip(): errors.append("رقم الفاتورة مطلوب")
        if car_no == "-- اختر --": errors.append("رقم السيارة مطلوب")
        if driver == "-- اختر --": errors.append("اسم السائق مطلوب")
        if amount <= 0: errors.append("المبلغ لازم يكون أكبر من صفر")
        if not problem.strip(): errors.append("المشكلة مطلوبة")
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
                    st.info(f"**رقم السيارة:** {existing.get('رقم السيارة', '-')}")
                    st.info(f"**اسم السائق:** {existing.get('اسم السائق', '-')}")
                    st.info(f"**التاريخ:** {existing.get('التاريخ', '-')}")
                    st.info(f"**المبلغ:** {existing.get('المبلغ (د.ك)', '-')} د.ك")
                with col_b:
                    st.info(f"**المشكلة:** {existing.get('المشكلة', '-')}")
                    st.info(f"**نوع المركبة:** {existing.get('نوع المركبة', '-')}")
                    st.info(f"**سنة الصنع:** {existing.get('سنة الصنع', '-')}")
            else:
                car_type = st.session_state.get("auto_car_type")
                car_year = st.session_state.get("auto_car_year")
                new_row = {
                    "رقم الفاتورة": invoice_no.strip(),
                    "رقم السيارة": car_no,
                    "اسم السائق": driver,
                    "التاريخ": str(inv_date),
                    "المبلغ (د.ك)": amount,
                    "المشكلة": problem.strip(),
                    "نوع المركبة": car_type if car_type else "",
                    "سنة الصنع": car_year if car_year else ""
                }
                save_expense(new_row)
                st.success(f"✅ تم حفظ الفاتورة {invoice_no} بنجاح!")
                st.balloons()
# ==================== تبويب 2: عرض الفواتير ====================
with tab2:
    st.subheader("📋 كل الفواتير المسجلة")
    df = load_expenses()
    if df.empty:
        st.info("📭 مفيش فواتير مسجلة لحد الآن")
    else:
        df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
        
        # ==================== الفلاتر ====================
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            min_date = df["التاريخ_dt"].min().date() if not df["التاريخ_dt"].isna().all() else date.today()
            date_from = st.date_input("📅 من تاريخ", value=min_date, key="list_date_from")
        with col2:
            max_date = df["التاريخ_dt"].max().date() if not df["التاريخ_dt"].isna().all() else date.today()
            date_to = st.date_input("📅 إلى تاريخ", value=max_date, key="list_date_to")
        with col3:
            filter_car = st.selectbox("🚙 السيارة", ["الكل"] + sorted(vehicles_df["الرقم"].astype(str).tolist()), key="filter_car_tab2")
        with col4:
            filter_type = st.selectbox("🚛 النوع", ["الكل"] + sorted(vehicles_df["النوع"].unique().tolist()), key="filter_type_tab2")
        
        search = st.text_input("🔍 بحث", "", key="search_tab2")
        
        filtered = df.copy()
        filtered = filtered[
            (filtered["التاريخ_dt"].dt.date >= date_from) & 
            (filtered["التاريخ_dt"].dt.date <= date_to)
        ]
        if search:
            filtered = filtered[filtered.astype(str).apply(lambda r: r.str.contains(search, case=False).any(), axis=1)]
        if filter_car != "الكل":
            filtered = filtered[filtered["رقم السيارة"].astype(str) == filter_car]
        if filter_type != "الكل":
            filtered = filtered[filtered["نوع المركبة"] == filter_type]
        
        filtered_display = filtered.drop(columns=["التاريخ_dt"], errors="ignore").reset_index(drop=True)
        total_amount = pd.to_numeric(filtered_display["المبلغ (د.ك)"], errors="coerce").sum()
        
        # ==================== الملخص ====================
        st.markdown(f"""
        ### 📊 ملخص النتائج
        🔢 **عدد الفواتير:** {len(filtered_display)} &nbsp;&nbsp;|&nbsp;&nbsp; 
        💰 **إجمالي المصاريف:** {total_amount:,.3f} د.ك &nbsp;&nbsp;|&nbsp;&nbsp; 
        📅 **الفترة:** من {date_from} إلى {date_to}
        """)
        
        col_a, col_b, col_c = st.columns([1, 1, 4])
        with col_a:
            if not filtered_display.empty:
                excel_data = to_excel_bytes(filtered_display)
                st.download_button(
                    label="📥 تصدير Excel",
                    data=excel_data,
                    file_name=f"فواتير_{date_from}_{date_to}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        with col_b:
            if st.button("🖨️ طباعة", use_container_width=True):
                st.info("💡 اضغط Ctrl+P من الكيبورد، واختار 'Save as PDF'")
        
        st.markdown("---")
        
        # ==================== الجدول التفاعلي ====================
        if filtered_display.empty:
            st.warning("⚠️ مفيش فواتير مطابقة للفلاتر")
        else:
            st.markdown(f"### 📋 الفواتير ({len(filtered_display)})")
            st.caption("💡 علّم على ☑ في عمود 'اختر' لتعديل أو حذف الفاتورة. وتقدر تعدّل أي خلية مباشرة.")
            
            # نضيف عمود "اختر"
            df_editor = filtered_display.copy()
            df_editor.insert(0, "اختر", False)
            
            # الجدول التفاعلي
            edited_df = st.data_editor(
                df_editor,
                use_container_width=True,
                hide_index=True,
                height=500,
                key="invoices_editor",
                column_config={
                    "اختر": st.column_config.CheckboxColumn(
                        "اختر",
                        help="علّم لتعديل أو حذف الفاتورة",
                        default=False,
                        width="small"
                    ),
                    "رقم الفاتورة": st.column_config.TextColumn("🔢 رقم الفاتورة", width="small"),
                    "رقم السيارة": st.column_config.TextColumn("🚙 رقم السيارة", width="small"),
                    "اسم السائق": st.column_config.TextColumn("👤 السائق", width="small"),
                    "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="small"),
                    "المبلغ (د.ك)": st.column_config.NumberColumn("💰 المبلغ (د.ك)", format="%.3f", width="small"),
                    "المشكلة": st.column_config.TextColumn("🔧 المشكلة", width="medium"),
                    "نوع المركبة": st.column_config.TextColumn("🚛 النوع", width="small"),
                    "سنة الصنع": st.column_config.TextColumn("📅 الصنع", width="small"),
                }
            )
            
            # ==================== الأزرار ====================
            st.markdown("---")
            st.markdown("### 🔧 إجراءات على الفواتير المحددة")
            
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 3])
            
            with col_btn1:
                if st.button("✏️ تعديل المحدد", use_container_width=True, type="primary"):
                    selected = edited_df[edited_df["اختر"] == True]
                    if len(selected) == 0:
                        st.warning("⚠️ علّم على فاتورة أولًا")
                    elif len(selected) > 1:
                        st.error("⚠️ اختار فاتورة واحدة بس")
                    else:
                        inv_no = str(selected.iloc[0]["رقم الفاتورة"])
                        st.session_state["edit_invoice"] = inv_no
                        st.rerun()
            
            with col_btn2:
                if st.button("🗑️ حذف المحدد", use_container_width=True):
                    selected = edited_df[edited_df["اختر"] == True]
                    if len(selected) == 0:
                        st.warning("⚠️ علّم على فاتورة أولًا")
                    elif len(selected) > 1:
                        st.error("⚠️ اختار فاتورة واحدة بس")
                    else:
                        inv_no = str(selected.iloc[0]["رقم الفاتورة"])
                        st.session_state["delete_invoice"] = inv_no
                        st.rerun()
            
            with col_btn3:
                if st.button("💾 حفظ التعديلات", use_container_width=True):
                    original = filtered_display.copy()
                    edited = edited_df.drop(columns=["اختر"]).copy()
                    
                    # نقارن القيم
                    changed_count = 0
                    full_df = load_expenses()
                    
                    for i in range(len(edited)):
                        inv_no = str(edited.iloc[i]["رقم الفاتورة"])
                        mask = full_df["رقم الفاتورة"].astype(str) == inv_no
                        if not mask.any():
                            continue
                        idx = full_df[mask].index[0]
                        
                        for col in edited.columns:
                            new_val = edited.iloc[i][col]
                            old_val = full_df.loc[idx, col]
                            
                            if col == "المبلغ (د.ك)":
                                try:
                                    if float(new_val) != float(old_val):
                                        full_df.loc[idx, col] = float(new_val)
                                        changed_count += 1
                                except:
                                    pass
                            else:
                                if str(new_val) != str(old_val):
                                    full_df.loc[idx, col] = new_val
                                    changed_count += 1
                    
                    if changed_count > 0:
                        save_all_expenses(full_df)
                        st.success(f"✅ تم حفظ {changed_count} تعديل!")
                        st.rerun()
                    else:
                        st.info("ℹ️ مفيش تعديلات جديدة")
            
            with col_btn4:
                st.markdown("💡 **ملاحظة:** لتعديل عدة فواتير في نفس الوقت، عدّل الخلايا مباشرة ثم اضغط 'حفظ التعديلات'")

# ==================== النوافذ المنبثقة ====================
if st.session_state.get("edit_invoice"):
    edit_invoice_dialog(st.session_state["edit_invoice"])
if st.session_state.get("delete_invoice"):
    delete_invoice_dialog(st.session_state["delete_invoice"])

# ==================== تبويب 3: التقارير ====================
with tab3:
    st.subheader("📊 التقارير والتحليل المتقدم")
    df = load_expenses()
    if df.empty:
        st.info("📭 مفيش بيانات")
    else:
        df["المبلغ (د.ك)"] = pd.to_numeric(df["المبلغ (د.ك)"], errors="coerce")
        df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
        
        st.markdown("### 🔍 الفلاتر")
        col1, col2, col3 = st.columns(3)
        with col1:
            min_date = df["التاريخ"].min().date() if not df["التاريخ"].isna().all() else date.today()
            date_from = st.date_input("📅 من تاريخ", value=min_date, key="report_date_from")
        with col2:
            max_date = df["التاريخ"].max().date() if not df["التاريخ"].isna().all() else date.today()
            date_to = st.date_input("📅 إلى تاريخ", value=max_date, key="report_date_to")
        with col3:
            filter_car = st.selectbox("🚙 السيارة", ["الكل"] + sorted(vehicles_df["الرقم"].astype(str).tolist()), key="report_car")
        
        col1, col2 = st.columns(2)
        with col1:
            filter_driver = st.selectbox("👤 السائق", ["الكل"] + sorted(drivers_list), key="report_driver")
        with col2:
            filter_type = st.selectbox("🚛 النوع", ["الكل"] + sorted(vehicles_df["النوع"].unique().tolist()), key="report_type")
        
        filtered = df.copy()
        filtered = filtered[
            (filtered["التاريخ"].dt.date >= date_from) & 
            (filtered["التاريخ"].dt.date <= date_to)
        ]
        if filter_car != "الكل":
            filtered = filtered[filtered["رقم السيارة"].astype(str) == filter_car]
        if filter_driver != "الكل":
            filtered = filtered[filtered["اسم السائق"] == filter_driver]
        if filter_type != "الكل":
            filtered = filtered[filtered["نوع المركبة"] == filter_type]
        
        st.markdown("---")
        st.markdown("### 💡 ملخص سريع")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 إجمالي المبالغ", f"{filtered['المبلغ (د.ك)'].sum():,.3f} د.ك")
        col2.metric("🧾 عدد الفواتير", len(filtered))
        col3.metric("🚗 عدد السيارات", filtered["رقم السيارة"].nunique())
        col4.metric("👤 عدد السائقين", filtered["اسم السائق"].nunique())
        
        col_a, col_b, col_c = st.columns([1, 1, 4])
        with col_a:
            if not filtered.empty:
                excel_data = to_excel_bytes(filtered)
                st.download_button(
                    label="📥 تصدير Excel",
                    data=excel_data,
                    file_name=f"تقرير_{date_from}_{date_to}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="export_filtered"
                )
        with col_b:
            if st.button("🖨️ طباعة", use_container_width=True, key="print_filtered"):
                st.info("💡 اضغط Ctrl+P من الكيبورد، واختار 'Save as PDF'")
        
        st.markdown("---")
        
        if filtered.empty:
            st.warning("⚠️ مفيش فواتير في الفترة المحددة")
        else:
            st.markdown(f"### 📋 الفواتير ({len(filtered)})")
            display_df = filtered.copy()
            display_df["التاريخ"] = display_df["التاريخ"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### 📊 التحليل البياني")
            
            by_car = filtered.groupby("رقم السيارة")["المبلغ (د.ك)"].sum().sort_values(ascending=False)
            if not by_car.empty:
                st.markdown("#### 🚙 المصاريف حسب السيارة")
                st.bar_chart(by_car)
            
            by_driver = filtered.groupby("اسم السائق")["المبلغ (د.ك)"].sum().sort_values(ascending=False)
            if not by_driver.empty:
                st.markdown("#### 👤 المصاريف حسب السائق")
                st.bar_chart(by_driver)
            
            filtered_month = filtered.copy()
            filtered_month["الشهر"] = filtered_month["التاريخ"].dt.to_period("M").astype(str)
            by_month = filtered_month.groupby("الشهر")["المبلغ (د.ك)"].sum().sort_index()
            if not by_month.empty:
                st.markdown("#### 📅 المصاريف حسب الشهر")
                st.bar_chart(by_month)
            
            st.markdown("---")
            st.markdown("### 🔍 تحليل السائقين على السيارات")
            st.markdown("*يساعد في معرفة هل السائق بيحافظ على السيارة أم لا*")
            
            pivot = filtered.pivot_table(
                index="اسم السائق", columns="رقم السيارة",
                values="المبلغ (د.ك)", aggfunc="sum", fill_value=0
            )
            if not pivot.empty:
                st.markdown("#### 💰 إجمالي المصاريف (سائق × سيارة)")
                st.dataframe(pivot, use_container_width=True)
                
                st.markdown("#### 🧾 عدد الفواتير (سائق × سيارة)")
                pivot_count = filtered.pivot_table(
                    index="اسم السائق", columns="رقم السيارة",
                    values="المبلغ (د.ك)", aggfunc="count", fill_value=0
                )
                st.dataframe(pivot_count, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🏆 ترتيب السائقين")
            
            driver_stats = filtered.groupby("اسم السائق").agg({
                "المبلغ (د.ك)": ["sum", "count", "mean"],
                "رقم السيارة": "nunique"
            }).round(3)
            driver_stats.columns = ["إجمالي المصاريف", "عدد الفواتير", "متوسط الفاتورة", "عدد السيارات"]
            driver_stats = driver_stats.sort_values("إجمالي المصاريف", ascending=False)
            st.dataframe(driver_stats, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🏆 ترتيب السيارات")
            
            car_stats = filtered.groupby("رقم السيارة").agg({
                "المبلغ (د.ك)": ["sum", "count", "mean"],
                "اسم السائق": "nunique"
            }).round(3)
            car_stats.columns = ["إجمالي المصاريف", "عدد الفواتير", "متوسط الفاتورة", "عدد السائقين"]
            car_stats = car_stats.sort_values("إجمالي المصاريف", ascending=False)
            st.dataframe(car_stats, use_container_width=True)

# ==================== تبويب 4: الإعدادات ====================
with tab4:
    st.subheader("⚙️ الإعدادات")
    st.markdown("---")
    
    st.markdown("### 👤 إدارة السائقين")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_driver = st.text_input("اسم سائق جديد", key="new_driver", placeholder="اكتب الاسم هنا")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ إضافة سائق", key="add_driver"):
            drivers_list_curr = load_drivers()
            if new_driver.strip() and new_driver.strip() not in drivers_list_curr:
                drivers_list_curr.append(new_driver.strip())
                save_drivers(drivers_list_curr)
                st.success(f"✅ تم إضافة: {new_driver}")
                st.rerun()
            elif new_driver.strip() in drivers_list_curr:
                st.warning("⚠️ موجود بالفعل")
            else:
                st.error("⚠️ اكتب الاسم أولًا")
    
    drivers_list_curr = load_drivers()
    for i, driver in enumerate(drivers_list_curr):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"• {driver}")
        with col2:
            if st.button("🗑️ حذف", key=f"del_driver_{i}"):
                drivers_list_curr.remove(driver)
                save_drivers(drivers_list_curr)
                st.success(f"تم حذف: {driver}")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🚙 إدارة المركبات")
    
    with st.expander("➕ إضافة مركبة جديدة"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_car_no = st.text_input("رقم السيارة", key="new_car_no")
        with col2:
            new_car_year = st.text_input("الموديل (سنة/طن)", key="new_car_year")
        with col3:
            new_car_type = st.text_input("النوع", key="new_car_type")
        
        if st.button("➕ إضافة المركبة", key="add_vehicle"):
            if new_car_no.strip() and new_car_year.strip() and new_car_type.strip():
                vehicles_df_curr = load_vehicles()
                if new_car_no.strip() in vehicles_df_curr["الرقم"].astype(str).tolist():
                    st.warning("⚠️ الرقم موجود بالفعل")
                else:
                    new_row = pd.DataFrame([{
                        "الرقم": new_car_no.strip(),
                        "الموديل": new_car_year.strip(),
                        "النوع": new_car_type.strip()
                    }])
                    vehicles_df_curr = pd.concat([vehicles_df_curr, new_row], ignore_index=True)
                    save_vehicles(vehicles_df_curr)
                    st.success(f"✅ تم إضافة السيارة: {new_car_no}")
                    st.rerun()
            else:
                st.error("⚠️ املأ كل الحقول")
    
    vehicles_df_curr = load_vehicles()
    st.markdown(f"**عدد المركبات: {len(vehicles_df_curr)}**")
    
    for i, row in vehicles_df_curr.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
        with col1:
            st.markdown(f"🚙 **{row['الرقم']}**")
        with col2:
            st.markdown(f"📅 {row['الموديل']}")
        with col3:
            st.markdown(f"🚛 {row['النوع']}")
        with col4:
            if st.button("🗑️", key=f"del_veh_{i}"):
                vehicles_df_curr = vehicles_df_curr.drop(i).reset_index(drop=True)
                save_vehicles(vehicles_df_curr)
                st.success(f"تم حذف: {row['الرقم']}")
                st.rerun()
