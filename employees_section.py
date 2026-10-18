import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import plotly.graph_objects as go

# ==================== الملفات ====================
EMPLOYEES_FILE = "employees.xlsx"
EVENTS_FILE = "employee_events.xlsx"
RECORDS_FILE = "employee_records.xlsx"

# ==================== البيانات الافتراضية ====================
DEFAULT_DRIVERS = [
    "مرزوق", "عبدالحميد", "شامير", "محمود", "ياسر", "منور", "أكرم", "حفصل", 
    "عاطف", "على", "سيد", "عبده", "عبدالله", "خالد", "عبدالعظيم", "أسامة", "ثامر"
]

DEFAULT_WORKERS = [
    {"الاسم": "احد", "الرتبة": "سوبر فايزر العمالة"},
    {"الاسم": "سيف", "الرتبة": "نائب السوبر فايزر"},
    {"الاسم": "دبيندرا", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "محمد قاسم على", "الرتبة": "عامل عادي"},
    {"الاسم": "محمد سليمان", "الرتبة": "عامل عادي"},
    {"الاسم": "نجيم مسلمانى", "الرتبة": "عامل عادي"},
    {"الاسم": "ام دى سراج", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "عوض", "الرتبة": "عامل عادي"},
    {"الاسم": "سيد منصور", "الرتبة": "عامل عادي"},
    {"الاسم": "بابو", "الرتبة": "عامل عادي"},
    {"الاسم": "جيما حسين", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "تافيجول", "الرتبة": "عامل عادي"},
    {"الاسم": "سافروالدين", "الرتبة": "عامل عادي"},
    {"الاسم": "جمساد مياه", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "اوشيما", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "احكم", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "ام دى ماهفوج", "الرتبة": "عامل عادي"},
    {"الاسم": "نسيم خان", "الرتبة": "عامل عادي"},
    {"الاسم": "ام دى اجيبول", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "ام دى بصير على", "الرتبة": "عامل عادي"},
    {"الاسم": "شهادات حسين", "الرتبة": "عامل من الدرجة أ"},
    {"الاسم": "صديق لطيف", "الرتبة": "عامل عادي"},
    {"الاسم": "اجاى ساه", "الرتبة": "عامل عادي"},
]

DEFAULT_EVENTS = [
    "مرضية", "غياب", "خروجيه",
    "التحدث باسلوب غير لائق مع زميله",
    "التحدث باسلوب غير لائق مع مسؤله",
    "التحدث باسلوب غير لائق مع العميل",
    "دعم سياره", "خطا تحميل",
    "عدم الالتزام بالعمل", "اهمال فالسياره",
]

# ==================== دوال التهيئة ====================
def init_employees_files():
    if not os.path.exists(EMPLOYEES_FILE):
        all_employees = []
        for d in DEFAULT_DRIVERS:
            all_employees.append({"الاسم": d, "الرتبة": "سائق"})
        for w in DEFAULT_WORKERS:
            all_employees.append({"الاسم": w["الاسم"], "الرتبة": w["الرتبة"]})
        pd.DataFrame(all_employees).to_excel(EMPLOYEES_FILE, index=False)
    
    if not os.path.exists(EVENTS_FILE):
        pd.DataFrame({"الحدث": DEFAULT_EVENTS}).to_excel(EVENTS_FILE, index=False)
    
    if not os.path.exists(RECORDS_FILE):
        df = pd.DataFrame(columns=[
            "رقم السند", "التاريخ", "اسم الموظف", "الرتبة", "الحدث", "ملاحظات", "الإجراء المتخذ"
        ])
        df.to_excel(RECORDS_FILE, index=False)

# ==================== دوال التحميل ====================
def load_employees():
    try:
        return pd.read_excel(EMPLOYEES_FILE)
    except:
        return pd.DataFrame()

def load_events():
    try:
        df = pd.read_excel(EVENTS_FILE)
        return df["الحدث"].dropna().astype(str).tolist()
    except:
        return DEFAULT_EVENTS

def load_records():
    try:
        return pd.read_excel(RECORDS_FILE)
    except:
        return pd.DataFrame()

# ==================== دوال الحفظ ====================
def save_employees(df):
    df.to_excel(EMPLOYEES_FILE, index=False)

def save_events(events):
    pd.DataFrame({"الحدث": events}).to_excel(EVENTS_FILE, index=False)

def save_records(df):
    df.to_excel(RECORDS_FILE, index=False)

# ==================== دوال مساعدة ====================
def get_next_record_id():
    df = load_records()
    if df.empty:
        return "EMP-0001"
    return f"EMP-{len(df)+1:04d}"

def get_employee_rank(name):
    df = load_employees()
    if df.empty:
        return ""
    match = df[df["الاسم"].astype(str) == str(name)]
    if not match.empty:
        return str(match.iloc[0]["الرتبة"])
    return ""

def get_employee_records(emp_name, date_from=None, date_to=None):
    df = load_records()
    if df.empty:
        return pd.DataFrame()
    filtered = df[df["اسم الموظف"].astype(str) == str(emp_name)].copy()
    if filtered.empty:
        return pd.DataFrame()
    if date_from is not None and date_to is not None:
        filtered["التاريخ_dt"] = pd.to_datetime(filtered["التاريخ"], errors="coerce")
        filtered = filtered[
            (filtered["التاريخ_dt"].dt.date >= date_from) &
            (filtered["التاريخ_dt"].dt.date <= date_to)
        ]
    return filtered

def get_employee_stats(emp_name, date_from=None, date_to=None):
    records = get_employee_records(emp_name, date_from, date_to)
    if records.empty:
        return {"count": 0, "events_breakdown": {}}
    breakdown = records["الحدث"].value_counts().to_dict()
    return {"count": len(records), "events_breakdown": breakdown}

def get_all_employees_stats(date_from=None, date_to=None):
    df = load_records()
    employees = load_employees()
    if df.empty or employees.empty:
        return pd.DataFrame()
    if date_from is not None and date_to is not None:
        df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
        df = df[
            (df["التاريخ_dt"].dt.date >= date_from) &
            (df["التاريخ_dt"].dt.date <= date_to)
        ]
    results = []
    for _, emp in employees.iterrows():
        name = str(emp["الاسم"])
        rank = str(emp["الرتبة"])
        emp_records = df[df["اسم الموظف"].astype(str) == name]
        count = len(emp_records)
        if count > 0:
            results.append({"الاسم": name, "الرتبة": rank, "عدد الأحداث": count})
    if results:
        return pd.DataFrame(results).sort_values("عدد الأحداث", ascending=False)
    return pd.DataFrame()

def get_event_stats(date_from=None, date_to=None):
    df = load_records()
    if df.empty:
        return pd.DataFrame()
    if date_from is not None and date_to is not None:
        df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
        df = df[
            (df["التاريخ_dt"].dt.date >= date_from) &
            (df["التاريخ_dt"].dt.date <= date_to)
        ]
    if df.empty:
        return pd.DataFrame()
    counts = df["الحدث"].value_counts().reset_index()
    counts.columns = ["الحدث", "عدد المرات"]
    return counts.sort_values("عدد المرات", ascending=False)
    
# ==================== دالة فورم التعديل (تحت الجدول) ====================
def render_edit_form_inline(record_id):
    df = load_records()
    match = df[df["رقم السند"].astype(str) == str(record_id)]
    
    if match.empty:
        st.error("⚠️ السند مش موجود")
        if st.button("❌ إغلاق", key="close_edit_inline_empty"):
            st.session_state["edit_employee_record"] = None
            st.rerun()
        return
    
    row = match.iloc[0]
    employees_df = load_employees()
    events_list = load_events()
    employee_names = employees_df["الاسم"].astype(str).tolist() if not employees_df.empty else []
    
    st.markdown(f"### ✏️ تعديل السند: `{record_id}`")
    st.markdown("---")
    
    cur_date = row.get("التاريخ", str(date.today()))
    try:
        cur_date_parsed = pd.to_datetime(cur_date).date()
    except:
        cur_date_parsed = date.today()
    
    cur_emp = str(row.get("اسم الموظف", ""))
    cur_event = str(row.get("الحدث", ""))
    
    col1, col2 = st.columns(2)
    with col1:
        new_date = st.date_input("📅 التاريخ", value=cur_date_parsed, key=f"edit_date_inline_{record_id}")
        emp_idx = employee_names.index(cur_emp) if cur_emp in employee_names else 0
        new_emp = st.selectbox("👤 اسم الموظف", employee_names, index=emp_idx, key=f"edit_emp_inline_{record_id}")
        rank = get_employee_rank(new_emp)
        st.info(f"**الرتبة الوظيفية:** {rank}")
    with col2:
        ev_options = ["-- اختر --"] + events_list
        ev_idx = ev_options.index(cur_event) if cur_event in ev_options else 0
        new_event = st.selectbox("📋 الحدث", ev_options, index=ev_idx, key=f"edit_event_inline_{record_id}")
    
    new_notes = st.text_area("📝 ملاحظات", value=str(row.get("ملاحظات", "")), key=f"edit_notes_inline_{record_id}")
    new_action = st.text_area("⚖️ الإجراء المتخذ", value=str(row.get("الإجراء المتخذ", "")), key=f"edit_action_inline_{record_id}")
    
    st.markdown("---")
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 حفظ التعديلات", use_container_width=True, type="primary", key=f"save_inline_{record_id}"):
            if new_event == "-- اختر --":
                st.error("⚠️ الحدث مطلوب")
            else:
                full_df = load_records()
                mask = full_df["رقم السند"].astype(str) == str(record_id)
                idx = full_df[mask].index[0]
                full_df.loc[idx, "التاريخ"] = str(new_date)
                full_df.loc[idx, "اسم الموظف"] = new_emp
                full_df.loc[idx, "الرتبة"] = rank
                full_df.loc[idx, "الحدث"] = new_event
                full_df.loc[idx, "ملاحظات"] = new_notes.strip()
                full_df.loc[idx, "الإجراء المتخذ"] = new_action.strip()
                save_records(full_df)
                st.session_state["edit_employee_record"] = None
                st.success(f"✅ تم تحديث السند {record_id}")
                st.rerun()
    
    with col_cancel:
        if st.button("❌ إلغاء", use_container_width=True, key=f"cancel_inline_{record_id}"):
            st.session_state["edit_employee_record"] = None
            st.rerun()

# ==================== دالة فورم الحذف (تحت الجدول) ====================
def render_delete_form_inline(record_id):
    df = load_records()
    match = df[df["رقم السند"].astype(str) == str(record_id)]
    
    if match.empty:
        st.error("⚠️ السند مش موجود")
        if st.button("❌ إغلاق", key="close_del_inline_empty"):
            st.session_state["delete_employee_record"] = None
            st.rerun()
        return
    
    row = match.iloc[0]
    
    st.markdown(f"### 🗑️ حذف السند: `{record_id}`")
    st.warning(f"⚠️ **هل أنت متأكد من حذف السند** `{record_id}` **؟**")
    st.markdown(f"**التاريخ:** {row.get('التاريخ', '-')}")
    st.markdown(f"**الموظف:** {row.get('اسم الموظف', '-')}")
    st.markdown(f"**الحدث:** {row.get('الحدث', '-')}")
    st.markdown("**لا يمكن التراجع عن هذا الإجراء.**")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ نعم، احذف", type="primary", use_container_width=True, key=f"confirm_del_inline_{record_id}"):
            full_df = load_records()
            full_df = full_df[full_df["رقم السند"].astype(str) != str(record_id)]
            save_records(full_df)
            st.session_state["delete_employee_record"] = None
            st.success(f"✅ تم حذف السند {record_id}")
            st.rerun()
    with col_no:
        if st.button("❌ إلغاء", use_container_width=True, key=f"cancel_del_inline_{record_id}"):
            st.session_state["delete_employee_record"] = None
            st.rerun()

# ==================== تبويب: إضافة سند ====================
def render_add_record_tab():
    st.subheader("➕ إضافة سند جديد")
    employees_df = load_employees()
    events_list = load_events()
    
    if employees_df.empty:
        st.warning("⚠️ مفيش موظفين مسجلين. روح للإعدادات ضيف موظفين الأول")
        return
    
    employee_names = employees_df["الاسم"].astype(str).tolist()
    
    col1, col2 = st.columns(2)
    with col1:
        record_date = st.date_input("📅 التاريخ *", value=date.today(), key="new_emp_record_date")
        selected_emp = st.selectbox("👤 اسم الموظف *", ["-- اختر --"] + employee_names, key="new_emp_record_employee")
        if selected_emp != "-- اختر --":
            rank = get_employee_rank(selected_emp)
            st.info(f"**الرتبة الوظيفية:** {rank}")
    with col2:
        selected_event = st.selectbox("📋 الحدث *", ["-- اختر --"] + events_list, key="new_emp_record_event")
    
    notes = st.text_area("📝 ملاحظات", placeholder="أي تفاصيل إضافية", key="new_emp_record_notes")
    action = st.text_area("⚖️ الإجراء المتخذ", placeholder="مثال: إنذار شفهي، خصم يوم...", key="new_emp_record_action")
    
    st.markdown("---")
    submitted = st.button("💾 حفظ السند", use_container_width=True, type="primary", key="save_new_emp_record")
    
    if submitted:
        errors = []
        if selected_emp == "-- اختر --": errors.append("الموظف مطلوب")
        if selected_event == "-- اختر --": errors.append("الحدث مطلوب")
        
        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            rank = get_employee_rank(selected_emp)
            new_id = get_next_record_id()
            new_row = {
                "رقم السند": new_id,
                "التاريخ": str(record_date),
                "اسم الموظف": selected_emp,
                "الرتبة": rank,
                "الحدث": selected_event,
                "ملاحظات": notes.strip(),
                "الإجراء المتخذ": action.strip(),
            }
            full_df = load_records()
            full_df = pd.concat([full_df, pd.DataFrame([new_row])], ignore_index=True)
            save_records(full_df)
            st.success(f"✅ تم حفظ السند **{new_id}** — {selected_emp} — {selected_event}")
            st.balloons()
            st.rerun()

# ==================== تبويب: عرض السندات ====================
def render_records_tab():
    st.subheader("📋 كل السندات المسجلة")
    
    df = load_records()
    
    if df.empty:
        st.info("📭 مفيش سندات مسجلة لحد الآن")
        return
    
    df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    
    employees_df = load_employees()
    employee_names = employees_df["الاسم"].astype(str).tolist() if not employees_df.empty else []
    events_list = load_events()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_date = df["التاريخ_dt"].min().date() if not df["التاريخ_dt"].isna().all() else date.today()
        date_from = st.date_input("📅 من تاريخ", value=min_date, key="emp_records_date_from")
    with col2:
        max_date = df["التاريخ_dt"].max().date() if not df["التاريخ_dt"].isna().all() else date.today()
        date_to = st.date_input("📅 إلى تاريخ", value=max_date, key="emp_records_date_to")
    with col3:
        filter_emp = st.selectbox("👤 الموظف", ["الكل"] + employee_names, key="emp_records_filter_emp")
    with col4:
        filter_event = st.selectbox("📋 الحدث", ["الكل"] + events_list, key="emp_records_filter_event")
    
    filtered = df.copy()
    filtered = filtered[
        (filtered["التاريخ_dt"].dt.date >= date_from) & 
        (filtered["التاريخ_dt"].dt.date <= date_to)
    ]
    if filter_emp != "الكل":
        filtered = filtered[filtered["اسم الموظف"].astype(str) == filter_emp]
    if filter_event != "الكل":
        filtered = filtered[filtered["الحدث"].astype(str) == filter_event]
    
    st.markdown(f"**عدد السندات: {len(filtered)}**")
    st.markdown("---")
    
    if filtered.empty:
        st.warning("⚠️ مفيش سندات مطابقة للفلاتر")
    else:
        filtered_display = filtered.drop(columns=["التاريخ_dt"], errors="ignore").reset_index(drop=True)
        st.caption("💡 علّم على ☑ في عمود 'اختر' لتعديل أو حذف السند")
        
        df_editor = filtered_display.copy()
        for col in df_editor.columns:
            df_editor[col] = df_editor[col].astype(str)
        df_editor.insert(0, "اختر", False)
        
        edited_df = st.data_editor(
            df_editor,
            use_container_width=True,
            hide_index=True,
            height=450,
            key="emp_records_editor",
            column_config={
                "اختر": st.column_config.CheckboxColumn("اختر", default=False, width="small"),
                "رقم السند": st.column_config.TextColumn("🔢 السند", width="small"),
                "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="small"),
                "اسم الموظف": st.column_config.TextColumn("👤 الموظف", width="small"),
                "الرتبة": st.column_config.TextColumn("🏷️ الرتبة", width="small"),
                "الحدث": st.column_config.TextColumn("📋 الحدث", width="medium"),
                "ملاحظات": st.column_config.TextColumn("📝 ملاحظات", width="medium"),
                "الإجراء المتخذ": st.column_config.TextColumn("⚖️ الإجراء", width="medium"),
            }
        )
        
        st.markdown("---")
        st.markdown("### 🔧 إجراءات")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
        
        with col_btn1:
            if st.button("✏️ تعديل المحدد", use_container_width=True, type="primary", key="edit_emp_record_btn"):
                selected = edited_df[edited_df["اختر"] == True]
                if len(selected) == 0:
                    st.warning("⚠️ علّم على سند أولًا")
                elif len(selected) > 1:
                    st.error("⚠️ اختار سند واحد بس")
                else:
                    rec_id = str(selected.iloc[0]["رقم السند"])
                    st.session_state["edit_employee_record"] = rec_id
                    st.rerun()
        
        with col_btn2:
            if st.button("🗑️ حذف المحدد", use_container_width=True, key="delete_emp_record_btn"):
                selected = edited_df[edited_df["اختر"] == True]
                if len(selected) == 0:
                    st.warning("⚠️ علّم على سند أولًا")
                elif len(selected) > 1:
                    st.error("⚠️ اختار سند واحد بس")
                else:
                    rec_id = str(selected.iloc[0]["رقم السند"])
                    st.session_state["delete_employee_record"] = rec_id
                    st.rerun()
        
        with col_btn3:
            st.markdown("💡 **ملاحظة:** الفورم بيظهر تحت الجدول")
        
        # ==================== الفورمات تظهر هنا تحت الجدول ====================
        if st.session_state.get("edit_employee_record"):
            st.markdown("---")
            render_edit_form_inline(st.session_state["edit_employee_record"])
        
        if st.session_state.get("delete_employee_record"):
            st.markdown("---")
            render_delete_form_inline(st.session_state["delete_employee_record"])
            
# ==================== تبويب: البحث عن موظف ====================
def render_search_tab():
    st.subheader("🔍 البحث عن موظف")
    
    employees_df = load_employees()
    if employees_df.empty:
        st.warning("⚠️ مفيش موظفين مسجلين")
        return
    
    employee_names = employees_df["الاسم"].astype(str).tolist()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_emp = st.selectbox("👤 اختار الموظف *", ["-- اختر --"] + employee_names, key="search_emp_select")
    with col2:
        search_from = st.date_input("📅 من تاريخ", value=date(date.today().year, 1, 1), key="search_emp_from")
    with col3:
        search_to = st.date_input("📅 إلى تاريخ", value=date.today(), key="search_emp_to")
    
    if selected_emp == "-- اختر --":
        st.info("💡 اختار موظف لعرض بياناته")
        return
    
    st.markdown("---")
    rank = get_employee_rank(selected_emp)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px;">
        <div style="font-size: 14px;">👤 الموظف</div>
        <div style="font-size: 28px; font-weight: bold; margin: 8px 0;">{selected_emp}</div>
        <div style="font-size: 16px;">🏷️ {rank}</div>
    </div>
    """, unsafe_allow_html=True)
    
    stats = get_employee_stats(selected_emp, search_from, search_to)
    
    st.markdown(f"### 📊 إحصائيات من {search_from} إلى {search_to}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📋 إجمالي الأحداث", stats["count"])
    with col2:
        st.metric("📅 الفترة", f"{(search_to - search_from).days} يوم")
    
    if stats["events_breakdown"]:
        st.markdown("---")
        st.markdown("### 📋 تفصيل الأحداث")
        sorted_breakdown = sorted(stats["events_breakdown"].items(), key=lambda x: x[1], reverse=True)
        for event, count in sorted_breakdown:
            st.markdown(f"""
            <div style="background: rgba(20,20,40,0.6); border-right: 4px solid #00e5ff; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                <span style="font-size: 16px;">📋 <b>{event}</b></span>
                <span style="float: left; font-size: 18px; color: #00e5ff; font-weight: bold;">{count}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📋 كل سجلات الموظف")
    
    emp_records = get_employee_records(selected_emp, search_from, search_to)
    
    if emp_records.empty:
        st.info("📭 مفيش سجلات للموظف في الفترة المحددة")
    else:
        display_cols = ["رقم السند", "التاريخ", "الحدث", "ملاحظات", "الإجراء المتخذ"]
        st.dataframe(emp_records[display_cols], use_container_width=True, hide_index=True)

# ==================== تبويب: التقارير ====================
def render_reports_tab():
    st.subheader("📊 التقارير والإحصائيات")
    
    df = load_records()
    if df.empty:
        st.info("📭 مفيش بيانات للتقارير")
        return
    
    df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    
    st.markdown("### 📅 فلتر الفترة")
    col1, col2 = st.columns(2)
    with col1:
        min_date = df["التاريخ_dt"].min().date() if not df["التاريخ_dt"].isna().all() else date.today()
        date_from = st.date_input("من تاريخ", value=min_date, key="reports_date_from")
    with col2:
        max_date = df["التاريخ_dt"].max().date() if not df["التاريخ_dt"].isna().all() else date.today()
        date_to = st.date_input("إلى تاريخ", value=max_date, key="reports_date_to")
    
    filtered = df[
        (df["التاريخ_dt"].dt.date >= date_from) &
        (df["التاريخ_dt"].dt.date <= date_to)
    ]
    
    if filtered.empty:
        st.warning("⚠️ مفيش بيانات في الفترة المحددة")
        return
    
    st.markdown("---")
    st.markdown("### 💡 ملخص الفترة")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 عدد السندات", len(filtered))
    col2.metric("👥 عدد الموظفين", filtered["اسم الموظف"].nunique())
    col3.metric("📋 عدد الأحداث", filtered["الحدث"].nunique())
    col4.metric("📅 الفترة", f"{(date_to - date_from).days} يوم")
    
    st.markdown("---")
    st.markdown("### 📊 إحصائيات الأحداث")
    event_stats = get_event_stats(date_from, date_to)
    
    if not event_stats.empty:
        fig = go.Figure(go.Bar(
            x=event_stats["عدد المرات"],
            y=event_stats["الحدث"],
            orientation='h',
            marker=dict(
                color=event_stats["عدد المرات"],
                colorscale=[[0, '#667eea'], [1, '#ff1744']],
                showscale=False,
            ),
            text=event_stats["عدد المرات"],
            textposition='outside',
            textfont=dict(size=13, color='white'),
            hovertemplate='<b>%{y}</b><br>عدد المرات: %{x}<extra></extra>'
        ))
        fig.update_layout(
            height=max(400, len(event_stats) * 45),
            xaxis_title="عدد المرات",
            yaxis_title="",
            plot_bgcolor='rgba(10,10,25,0.6)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=13),
            margin=dict(l=20, r=60, t=20, b=40),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 👥 إحصائيات الموظفين (الأكثر أحداث)")
    emp_stats = get_all_employees_stats(date_from, date_to)
    if not emp_stats.empty:
        st.dataframe(emp_stats, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🏷️ إحصائيات حسب الرتبة الوظيفية")
    by_rank = filtered.groupby("الرتبة").size().reset_index(name="عدد الأحداث")
    by_rank = by_rank.sort_values("عدد الأحداث", ascending=False)
    if not by_rank.empty:
        st.dataframe(by_rank, use_container_width=True, hide_index=True)

# ==================== تبويب: الإعدادات ====================
def render_settings_tab():
    st.subheader("⚙️ الإعدادات")
    
    # إدارة الموظفين
    st.markdown("### 👥 إدارة الموظفين")
    employees_df = load_employees()
    
    if not employees_df.empty:
        st.markdown(f"**عدد الموظفين: {len(employees_df)}**")
        ranks = employees_df["الرتبة"].value_counts().to_dict()
        for rank, count in ranks.items():
            st.markdown(f"- 🏷️ **{rank}**: {count} موظف")
        
        st.markdown("---")
        search_emp = st.text_input("🔍 بحث بالاسم", "", key="settings_search_emp")
        filtered_emps = employees_df.copy()
        if search_emp:
            filtered_emps = filtered_emps[filtered_emps["الاسم"].astype(str).str.contains(search_emp, case=False)]
        
        st.markdown(f"### 📋 قائمة الموظفين ({len(filtered_emps)})")
        for i, row in filtered_emps.iterrows():
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                st.markdown(f"👤 **{row['الاسم']}**")
            with col2:
                st.markdown(f"🏷️ {row['الرتبة']}")
            with col3:
                if st.button("🗑️", key=f"del_emp_{i}"):
                    full_df = load_employees()
                    full_df = full_df[full_df["الاسم"].astype(str) != str(row["الاسم"])]
                    save_employees(full_df)
                    st.success(f"تم حذف: {row['الاسم']}")
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### ➕ إضافة موظف جديد")
    col1, col2 = st.columns([2, 2])
    with col1:
        new_emp_name = st.text_input("اسم الموظف", placeholder="مثال: محمد أحمد", key="settings_new_emp")
    with col2:
        new_emp_rank = st.text_input("الرتبة الوظيفية", placeholder="مثال: سائق / عامل عادي", key="settings_new_rank")
    
    if st.button("➕ إضافة الموظف", key="settings_add_emp", use_container_width=True, type="primary"):
        if new_emp_name.strip() and new_emp_rank.strip():
            full_df = load_employees()
            if new_emp_name.strip() in full_df["الاسم"].astype(str).tolist():
                st.warning(f"⚠️ الموظف {new_emp_name} موجود بالفعل")
            else:
                new_row = pd.DataFrame([{"الاسم": new_emp_name.strip(), "الرتبة": new_emp_rank.strip()}])
                full_df = pd.concat([full_df, new_row], ignore_index=True)
                save_employees(full_df)
                st.success(f"✅ تم إضافة الموظف: {new_emp_name}")
                st.rerun()
        else:
            st.error("⚠️ املأ الاسم والرتبة")
    
    st.markdown("---")
    st.markdown("### 📋 إدارة الأحداث (القائمة المنسدلة)")
    
    events_list = load_events()
    st.markdown(f"**عدد الأحداث: {len(events_list)}**")
    
    for i, ev in enumerate(events_list):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"📋 {ev}")
        with col2:
            if st.button("🗑️", key=f"del_event_{i}"):
                events_list.remove(ev)
                save_events(events_list)
                st.success(f"تم حذف: {ev}")
                st.rerun()
    
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_event_name = st.text_input("حدث جديد", placeholder="مثال: تأخر متكرر", key="settings_new_event")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ إضافة حدث", key="settings_add_event"):
            if new_event_name.strip():
                events_list = load_events()
                if new_event_name.strip() in events_list:
                    st.warning("⚠️ الحدث موجود بالفعل")
                else:
                    events_list.append(new_event_name.strip())
                    save_events(events_list)
                    st.success(f"✅ تم إضافة: {new_event_name}")
                    st.rerun()
            else:
                st.error("⚠️ اكتب اسم الحدث")
    
    st.markdown("---")
    st.markdown("### ℹ️ معلومات")
    records = load_records()
    employees = load_employees()
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 عدد الموظفين", len(employees))
    col2.metric("📋 عدد الأحداث", len(load_events()))
    col3.metric("📝 عدد السندات", len(records))

# ==================== دالة القسم الرئيسية ====================
def render_employees_section():
    init_employees_files()
    
    st.title("👥 قسم تقييم موظفين المخزن")
    st.markdown("### متابعة سلوك وأداء الموظفين")
    st.markdown("---")
    
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "➕ إضافة سند",
        "📋 عرض السندات",
        "🔍 البحث عن موظف",
        "📊 التقارير",
        "⚙️ الإعدادات"
    ])
    
    with tab0:
        render_add_record_tab()
    
    with tab1:
        render_records_tab()
    
    with tab2:
        render_search_tab()
    
    with tab3:
        render_reports_tab()
    
    with tab4:
        render_settings_tab()

# ==================== نهاية القسم ====================
