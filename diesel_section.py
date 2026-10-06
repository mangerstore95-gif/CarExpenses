import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import plotly.graph_objects as go

# ==================== الملفات ====================
DIESEL_RECORDS_FILE = "diesel_records.xlsx"
DIESEL_SETTINGS_FILE = "diesel_settings.xlsx"

# ==================== الإعدادات الافتراضية ====================
DEFAULT_MONTHLY_AVG = 5.0  # كم/لتر لكل السيارات

# ==================== دوال التهيئة ====================
def init_diesel_files():
    if not os.path.exists(DIESEL_RECORDS_FILE):
        df = pd.DataFrame(columns=[
            "رقم السند", "الشهر", "رقم السيارة", "الموديل", "سنة الصنع",
            "قراءة بداية الشهر", "قراءة نهاية الشهر", "المسافة (كم)",
            "إجمالي اللترات", "المعدل الفعلي (كم/لتر)", "المعدل الطبيعي (كم/لتر)",
            "الحالة", "ملاحظات"
        ])
        df.to_excel(DIESEL_RECORDS_FILE, index=False)
    
    if not os.path.exists(DIESEL_SETTINGS_FILE):
        settings = {
            "المعدل الطبيعي العام (كم/لتر)": DEFAULT_MONTHLY_AVG,
        }
        pd.DataFrame([settings]).to_excel(DIESEL_SETTINGS_FILE, index=False)

# ==================== دوال التحميل ====================
def load_diesel_records():
    try:
        return pd.read_excel(DIESEL_RECORDS_FILE)
    except:
        return pd.DataFrame()

def load_diesel_settings():
    try:
        df = pd.read_excel(DIESEL_SETTINGS_FILE)
        return df.iloc[0].to_dict()
    except:
        return {"المعدل الطبيعي العام (كم/لتر)": DEFAULT_MONTHLY_AVG}

def load_vehicles():
    """يقرا المركبات من ملف vehicles.xlsx (نفس ملف قسم الصيانة)"""
    try:
        df = pd.read_excel("vehicles.xlsx")
        df["الرقم"] = df["الرقم"].astype(str)
        return df
    except:
        return pd.DataFrame()

def load_drivers():
    """يقرا السائقين من ملف drivers.xlsx"""
    try:
        df = pd.read_excel("drivers.xlsx")
        return df["السائقين"].dropna().astype(str).tolist()
    except:
        return []

def get_vehicle_info(car_no):
    """يرجع الموديل والسنة لسيارة"""
    df = load_vehicles()
    if df.empty:
        return None, None
    match = df[df["الرقم"].astype(str) == str(car_no)]
    if not match.empty:
        row = match.iloc[0]
        return row["الموديل"], row["النوع"]
    return None, None

# ==================== دوال الحفظ ====================
def save_diesel_records(df):
    df.to_excel(DIESEL_RECORDS_FILE, index=False)

def save_diesel_settings(settings):
    pd.DataFrame([settings]).to_excel(DIESEL_SETTINGS_FILE, index=False)

def get_next_diesel_id():
    """يرجع رقم السند التالي"""
    df = load_diesel_records()
    if df.empty:
        return "DZL-0001"
    return f"DZL-{len(df)+1:04d}"

def get_records_file():
    """ملف التعبئات اليومية لكل سند"""
    return "diesel_refuels.xlsx"

def init_refuels_file():
    if not os.path.exists(get_records_file()):
        df = pd.DataFrame(columns=[
            "رقم السند", "التاريخ", "اسم السائق", "عدد اللترات"
        ])
        df.to_excel(get_records_file(), index=False)

def load_refuels():
    init_refuels_file()
    try:
        return pd.read_excel(get_records_file())
    except:
        return pd.DataFrame()

def save_refuels(df):
    df.to_excel(get_records_file(), index=False)

def get_refuels_for_record(record_id):
    """يرجع كل التعبئات لسند معين"""
    df = load_refuels()
    if df.empty:
        return pd.DataFrame()
    return df[df["رقم السند"].astype(str) == str(record_id)].copy()

def get_total_liters(record_id):
    """إجمالي اللترات لسند"""
    refuels = get_refuels_for_record(record_id)
    if refuels.empty:
        return 0.0
    return float(pd.to_numeric(refuels["عدد اللترات"], errors="coerce").sum())

def calculate_efficiency(distance, total_liters):
    """يحسب المعدل كم/لتر"""
    try:
        distance = float(distance)
        total_liters = float(total_liters)
        if total_liters <= 0:
            return 0.0
        return round(distance / total_liters, 2)
    except:
        return 0.0

def get_vehicle_avg(vehicle_no, settings):
    """يرجع المعدل الطبيعي لسيارة (من الإعدادات أو العام)"""
    key = f"معدل {vehicle_no}"
    if key in settings and pd.notna(settings[key]):
        return float(settings[key])
    return float(settings.get("المعدل الطبيعي العام (كم/لتر)", DEFAULT_MONTHLY_AVG))

def get_record_status(efficiency, natural):
    """يرجع حالة السند: طبيعي / غير طبيعي"""
    if efficiency <= 0 or natural <= 0:
        return "⚪ غير محدد"
    
    ratio = efficiency / natural
    if ratio >= 0.9:
        return "✅ طبيعي"
    elif ratio >= 0.75:
        return "🟡 مقبول"
    else:
        return "🔴 غير طبيعي"

# ==================== فورم فتح سند شهري جديد ====================
def render_new_record_form(vehicles_df, drivers_list):
    st.subheader("➕ فتح سند شهري جديد")
    
    st.markdown("""
    **ملاحظة:** كل سند = شهر واحد لسيارة واحدة.
    
    1. اختار السيارة والشهر
    2. سجل التعبئات اليومية
    3. سجل قراءات العدّاد (بداية ونهاية الشهر)
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # الشهر
        today = date.today()
        month_options = []
        for i in range(-6, 7):
            m = today.month + i
            y = today.year
            while m < 1:
                m += 12
                y -= 1
            while m > 12:
                m -= 12
                y += 1
            month_options.append(f"{y}-{m:02d}")
        
        month_options.reverse()
        default_month = f"{today.year}-{today.month:02d}"
        default_idx = month_options.index(default_month) if default_month in month_options else len(month_options) - 1
        
        selected_month = st.selectbox("📅 الشهر *", month_options, index=default_idx, key="new_dzl_month")
    
    with col2:
        # السيارة
        vehicle_list = vehicles_df["الرقم"].astype(str).tolist() if not vehicles_df.empty else []
        selected_vehicle = st.selectbox("🚙 رقم السيارة *", ["-- اختر --"] + vehicle_list, key="new_dzl_vehicle")
    
    with col3:
        # الموديل والسنة (تلقائي)
        if selected_vehicle != "-- اختر --":
            model, vtype = get_vehicle_info(selected_vehicle)
            if model:
                st.markdown(f"**📅 الموديل:** {model}")
                st.markdown(f"**🚛 النوع:** {vtype}")
    
    st.markdown("---")
    
    # التحقق من وجود سند مسبق
    existing_records = load_diesel_records()
    if not existing_records.empty and selected_vehicle != "-- اختر --":
        existing = existing_records[
            (existing_records["الشهر"].astype(str) == selected_month) &
            (existing_records["رقم السيارة"].astype(str) == selected_vehicle)
        ]
        if not existing.empty:
            st.warning(f"⚠️ **يوجد سند بالفعل للسيارة {selected_vehicle} في شهر {selected_month}**")
            st.info("💡 روح لتبويب '📋 عرض السندات' لتعديله")
            return
    
    # ملاحظات
    notes = st.text_area("📝 ملاحظات (اختياري)", key="new_dzl_notes")
    
    st.markdown("---")
    
    submitted = st.button("✅ فتح السند", use_container_width=True, type="primary", key="open_dzl_record_btn")
    
    if submitted:
        errors = []
        if selected_vehicle == "-- اختر --":
            errors.append("رقم السيارة مطلوب")
        
        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            model, vtype = get_vehicle_info(selected_vehicle)
            new_id = get_next_diesel_id()
            
            new_record = {
                "رقم السند": new_id,
                "الشهر": selected_month,
                "رقم السيارة": selected_vehicle,
                "الموديل": model if model else "",
                "سنة الصنع": vtype if vtype else "",
                "قراءة بداية الشهر": 0,
                "قراءة نهاية الشهر": 0,
                "المسافة (كم)": 0,
                "إجمالي اللترات": 0,
                "المعدل الفعلي (كم/لتر)": 0,
                "المعدل الطبيعي (كم/لتر)": 0,
                "الحالة": "⚪ غير محدد",
                "ملاحظات": notes.strip()
            }
            
            full_df = load_diesel_records()
            full_df = pd.concat([full_df, pd.DataFrame([new_record])], ignore_index=True)
            save_diesel_records(full_df)
            
            st.success(f"✅ تم فتح السند **{new_id}** — {selected_vehicle} — {selected_month}")
            st.info("💡 روح لتبويب '📋 عرض السندات' عشان تسجل التعبئات والقراءات")
            st.balloons()
            st.rerun()

# ==================== تبويب داخل السند (تفاصيل السند المفتوح) ====================
def render_record_details(record_id, vehicles_df, drivers_list):
    """يعرض تفاصيل السند مع التبويبات الداخلية"""
    
    records = load_diesel_records()
    match = records[records["رقم السند"].astype(str) == str(record_id)]
    
    if match.empty:
        st.error("⚠️ السند مش موجود")
        return
    
    record = match.iloc[0]
    
    st.markdown(f"## 📅 السند الشهري: `{record_id}`")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"**📅 الشهر:** {record['الشهر']}")
    with col2:
        st.markdown(f"**🚙 السيارة:** {record['رقم السيارة']}")
    with col3:
        st.markdown(f"**🏷️ الموديل:** {record['الموديل']}")
    with col4:
        st.markdown(f"**🚛 النوع:** {record['سنة الصنع']}")
    
    st.markdown("---")
    
    # التبويبات الداخلية
    sub_tab1, sub_tab2 = st.tabs(["⛽ التعبئات اليومية", "📏 قراءات العدّاد"])
    
    # ==================== تبويب 1: التعبئات ====================
    with sub_tab1:
        st.markdown("### ⛽ تسجيل تعبئة جديدة")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            refuel_date = st.date_input("📅 التاريخ *", value=date.today(), key=f"refuel_date_{record_id}")
        
        with col2:
            refuel_driver = st.selectbox("👤 اسم السائق *", ["-- اختر --"] + drivers_list, key=f"refuel_driver_{record_id}")
        
        with col3:
            refuel_liters = st.number_input("⛽ عدد اللترات *", min_value=0.0, step=5.0, value=0.0, key=f"refuel_liters_{record_id}")
        
        if st.button("➕ إضافة التعبئة", use_container_width=True, type="primary", key=f"add_refuel_{record_id}"):
            errors = []
            if refuel_driver == "-- اختر --":
                errors.append("اسم السائق مطلوب")
            if refuel_liters <= 0:
                errors.append("عدد اللترات لازم يكون أكبر من صفر")
            
            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
            else:
                new_refuel = {
                    "رقم السند": record_id,
                    "التاريخ": str(refuel_date),
                    "اسم السائق": refuel_driver,
                    "عدد اللترات": refuel_liters
                }
                
                refuels_df = load_refuels()
                refuels_df = pd.concat([refuels_df, pd.DataFrame([new_refuel])], ignore_index=True)
                save_refuels(refuels_df)
                
                st.success(f"✅ تم إضافة تعبئة: {refuel_liters} لتر")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 التعبئات المسجلة")
        
        refuels = get_refuels_for_record(record_id)
        
        if refuels.empty:
            st.info("📭 مفيش تعبئات مسجلة لحد الآن")
        else:
            refuels["عدد اللترات"] = pd.to_numeric(refuels["عدد اللترات"], errors="coerce")
            
            # الجدول
            display_df = refuels.copy().reset_index(drop=True)
            
            for i, row in display_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
                with col1:
                    st.markdown(f"📅 {row['التاريخ']}")
                with col2:
                    st.markdown(f"👤 {row['اسم السائق']}")
                with col3:
                    st.markdown(f"⛽ {row['عدد اللترات']:.0f} لتر")
                with col4:
                    st.markdown("")
                with col5:
                    if st.button("🗑️", key=f"del_refuel_{record_id}_{i}"):
                        # نحذف السطر
                        refuels_df = load_refuels()
                        mask = (
                            (refuels_df["رقم السند"].astype(str) == str(record_id)) &
                            (refuels_df["التاريخ"].astype(str) == str(row["التاريخ"])) &
                            (refuels_df["اسم السائق"].astype(str) == str(row["اسم السائق"])) &
                            (pd.to_numeric(refuels_df["عدد اللترات"], errors="coerce") == float(row["عدد اللترات"]))
                        )
                        idx_to_del = refuels_df[mask].index
                        if len(idx_to_del) > 0:
                            refuels_df = refuels_df.drop(idx_to_del[0]).reset_index(drop=True)
                            save_refuels(refuels_df)
                            st.success("✅ تم حذف التعبئة")
                            st.rerun()
            
            st.markdown("---")
            
            total = refuels["عدد اللترات"].sum()
            st.markdown(f"### 💰 إجمالي اللترات: **{total:,.0f} لتر**")
            
            # نحفظ الإجمالي في السند
            full_df = load_diesel_records()
            mask = full_df["رقم السند"].astype(str) == str(record_id)
            if mask.any():
                idx = full_df[mask].index[0]
                full_df.loc[idx, "إجمالي اللترات"] = total
                save_diesel_records(full_df)

    # ==================== تبويب 2: قراءات العدّاد ====================
    with sub_tab2:
        st.markdown("### 📏 قراءات العدّاد")
        st.caption("سجل قراءة العداد في بداية الشهر ونهايته")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                start_val = float(record["قراءة بداية الشهر"])
            except:
                start_val = 0.0
            new_start = st.number_input(
                "🔢 قراءة بداية الشهر (كم)",
                min_value=0.0,
                step=100.0,
                value=start_val,
                key=f"start_odo_{record_id}"
            )
        
        with col2:
            try:
                end_val = float(record["قراءة نهاية الشهر"])
            except:
                end_val = 0.0
            new_end = st.number_input(
                "🔢 قراءة نهاية الشهر (كم)",
                min_value=0.0,
                step=100.0,
                value=end_val,
                key=f"end_odo_{record_id}"
            )
        
        # المسافة
        distance = max(0, new_end - new_start)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; text-align: center; color: white; margin: 15px 0;">
            <div style="font-size: 14px;">📏 المسافة المقطوعة</div>
            <div style="font-size: 36px; font-weight: bold; margin: 10px 0;">{distance:,.0f}</div>
            <div style="font-size: 13px;">كم</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 حفظ القراءات", use_container_width=True, type="primary", key=f"save_odo_{record_id}"):
            if new_end < new_start:
                st.error("⚠️ قراءة نهاية الشهر لازم تكون أكبر من البداية")
            elif new_end == new_start:
                st.error("⚠️ المسافة صفر — تأكد من القراءات")
            else:
                settings = load_diesel_settings()
                total_liters = get_total_liters(record_id)
                efficiency = calculate_efficiency(distance, total_liters)
                natural = get_vehicle_avg(record["رقم السيارة"], settings)
                status = get_record_status(efficiency, natural)
                
                full_df = load_diesel_records()
                mask = full_df["رقم السند"].astype(str) == str(record_id)
                idx = full_df[mask].index[0]
                
                full_df.loc[idx, "قراءة بداية الشهر"] = new_start
                full_df.loc[idx, "قراءة نهاية الشهر"] = new_end
                full_df.loc[idx, "المسافة (كم)"] = distance
                full_df.loc[idx, "إجمالي اللترات"] = total_liters
                full_df.loc[idx, "المعدل الفعلي (كم/لتر)"] = efficiency
                full_df.loc[idx, "المعدل الطبيعي (كم/لتر)"] = natural
                full_df.loc[idx, "الحالة"] = status
                
                save_diesel_records(full_df)
                st.success(f"✅ تم حفظ القراءات — المعدل الفعلي: {efficiency:.2f} كم/لتر")
                st.rerun()
        
        st.markdown("---")
        
        # عرض الملخص
        st.markdown("### 📊 ملخص السند")
        
        settings = load_diesel_settings()
        total_liters = get_total_liters(record_id)
        
        records = load_diesel_records()
        match2 = records[records["رقم السند"].astype(str) == str(record_id)]
        if not match2.empty:
            rec = match2.iloc[0]
            
            try:
                dist = float(rec["المسافة (كم)"])
            except:
                dist = 0.0
            
            efficiency = calculate_efficiency(dist, total_liters)
            natural = get_vehicle_avg(rec["رقم السيارة"], settings)
            status = get_record_status(efficiency, natural)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("⛽ إجمالي اللترات", f"{total_liters:,.0f} لتر")
            col2.metric("📏 المسافة", f"{dist:,.0f} كم")
            col3.metric("📊 المعدل الفعلي", f"{efficiency:.2f} كم/لتر" if efficiency > 0 else "—")
            
            col1, col2 = st.columns(2)
            col1.metric("🎯 المعدل الطبيعي", f"{natural:.2f} كم/لتر")
            col2.metric("📊 الحالة", status)
            
            # تنبيه لو غير طبيعي
            if efficiency > 0 and natural > 0:
                ratio = efficiency / natural
                if ratio < 0.75:
                    st.error(f"🚨 **تحذير!** استهلاك السيارة {rec['رقم السيارة']} غير طبيعي — الفعلي {efficiency:.2f} كم/لتر vs الطبيعي {natural:.2f} كم/لتر")
                elif ratio < 0.9:
                    st.warning(f"⚠️ استهلاك أقل من الطبيعي بقليل — الفعلي {efficiency:.2f} vs الطبيعي {natural:.2f}")
                else:
                    st.success(f"✅ استهلاك طبيعي — الفعلي {efficiency:.2f} كم/لتر")

# ==================== تبويب: عرض السندات ====================
def render_records_table(vehicles_df, drivers_list):
    st.subheader("📋 كل السندات الشهرية")
    
    records = load_diesel_records()
    
    if records.empty:
        st.info("📭 مفيش سندات مسجلة لحد الآن")
        return
    
    # تحديث الإجماليات
    records["إجمالي اللترات"] = records.apply(
        lambda r: get_total_liters(r["رقم السند"]), axis=1
    )
    
    settings = load_diesel_settings()
    records["المعدل الطبيعي (كم/لتر)"] = records["رقم السيارة"].apply(
        lambda v: get_vehicle_avg(v, settings)
    )
    
    records["المعدل الفعلي (كم/لتر)"] = records.apply(
        lambda r: calculate_efficiency(r["المسافة (كم)"], r["إجمالي اللترات"]), axis=1
    )
    
    records["الحالة"] = records.apply(
        lambda r: get_record_status(r["المعدل الفعلي (كم/لتر)"], r["المعدل الطبيعي (كم/لتر)"]), axis=1
    )
    
    # فلاتر
    col1, col2 = st.columns(2)
    with col1:
        filter_month = st.selectbox(
            "📅 فلترة بالشهر",
            ["الكل"] + sorted(records["الشهر"].astype(str).unique().tolist()),
            key="diesel_filter_month"
        )
    with col2:
        filter_vehicle = st.selectbox(
            "🚙 فلترة بالسيارة",
            ["الكل"] + sorted(records["رقم السيارة"].astype(str).unique().tolist()),
            key="diesel_filter_vehicle"
        )
    
    filtered = records.copy()
    if filter_month != "الكل":
        filtered = filtered[filtered["الشهر"].astype(str) == filter_month]
    if filter_vehicle != "الكل":
        filtered = filtered[filtered["رقم السيارة"].astype(str) == filter_vehicle]
    
    filtered = filtered.reset_index(drop=True)
    
    st.markdown(f"**عدد السندات: {len(filtered)}**")
    st.markdown("---")
    
    # ==================== عرض السندات ====================
    for i, row in filtered.iterrows():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
            
            with col1:
                st.markdown(f"**📅 {row['الشهر']}**")
            with col2:
                st.markdown(f"🚙 {row['رقم السيارة']}")
            with col3:
                st.markdown(f"⛽ {row['إجمالي اللترات']:,.0f} لتر")
            with col4:
                st.markdown(f"📏 {row['المسافة (كم)']:,.0f} كم")
            with col5:
                eff = row['المعدل الفعلي (كم/لتر)']
                nat = row['المعدل الطبيعي (كم/لتر)']
                if eff > 0:
                    st.markdown(f"📊 {eff:.2f} / {nat:.2f}")
                else:
                    st.markdown(f"📊 — / {nat:.2f}")
            with col6:
                if st.button("📂", key=f"open_dzl_{i}", help="فتح السند"):
                    st.session_state["open_diesel_record"] = str(row["رقم السند"])
                    st.rerun()
            
            st.markdown(f"**{row['الحالة']}**")
            st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== إجراءات ====================
    st.markdown("### 🔧 إجراءات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        all_ids = filtered["رقم السند"].astype(str).tolist()
        if all_ids:
            selected = st.selectbox("اختر سند", ["-- اختر --"] + all_ids, key="diesel_actions_select")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📂 فتح", use_container_width=True, type="primary"):
                    if selected != "-- اختر --":
                        st.session_state["open_diesel_record"] = selected
                        st.rerun()
            with col_b:
                if st.button("🗑️ حذف", use_container_width=True):
                    if selected != "-- اختر --":
                        # نحذف السند
                        full_df = load_diesel_records()
                        full_df = full_df[full_df["رقم السند"].astype(str) != selected]
                        save_diesel_records(full_df)
                        
                        # نحذف كل التعبئات المرتبطة
                        refuels_df = load_refuels()
                        refuels_df = refuels_df[refuels_df["رقم السند"].astype(str) != selected]
                        save_refuels(refuels_df)
                        
                        st.success(f"✅ تم حذف السند {selected} وكل تعبئاته")
                        st.rerun()

# ==================== تبويب: لوحة المعلومات ====================
def render_diesel_dashboard():
    st.subheader("📊 لوحة معلومات الديزل")
    
    records = load_diesel_records()
    
    if records.empty:
        st.info("📭 مفيش سندات مسجلة لحد الآن. ابدأ بفتح سند شهري من تبويب '➕ فتح سند شهري جديد'")
        return
    
    # نحدث الإجماليات
    settings = load_diesel_settings()
    
    records["إجمالي اللترات"] = records.apply(
        lambda r: get_total_liters(r["رقم السند"]), axis=1
    )
    
    records["المعدل الفعلي (كم/لتر)"] = records.apply(
        lambda r: calculate_efficiency(r["المسافة (كم)"], r["إجمالي اللترات"]), axis=1
    )
    
    records["المعدل الطبيعي (كم/لتر)"] = records["رقم السيارة"].apply(
        lambda v: get_vehicle_avg(v, settings)
    )
    
    records["الحالة"] = records.apply(
        lambda r: get_record_status(r["المعدل الفعلي (كم/لتر)"], r["المعدل الطبيعي (كم/لتر)"]), axis=1
    )
    
    # ==================== KPI Cards ====================
    total_records = len(records)
    total_liters = records["إجمالي اللترات"].sum()
    total_distance = pd.to_numeric(records["المسافة (كم)"], errors="coerce").sum()
    avg_efficiency = records[records["المعدل الفعلي (كم/لتر)"] > 0]["المعدل الفعلي (كم/لتر)"].mean()
    
    if pd.isna(avg_efficiency):
        avg_efficiency = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">📋 إجمالي السندات</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_records}</div>
            <div style="font-size: 13px;">سند</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">⛽ إجمالي اللترات</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_liters:,.0f}</div>
            <div style="font-size: 13px;">لتر</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">📏 إجمالي المسافة</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_distance:,.0f}</div>
            <div style="font-size: 13px;">كم</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">📊 متوسط المعدل</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{avg_efficiency:.2f}</div>
            <div style="font-size: 13px;">كم/لتر</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # ==================== تنبيهات ====================
    st.markdown("### 🚨 تنبيهات الاستهلاك")
    
    abnormal = records[records["الحالة"].str.contains("غير طبيعي", na=False)]
    
    if abnormal.empty:
        st.success("✅ كل السيارات استهلاكها طبيعي")
    else:
        st.error(f"🚨 **{len(abnormal)} سيارة** استهلاكها غير طبيعي")
        
        for i, row in abnormal.iterrows():
            eff = row["المعدل الفعلي (كم/لتر)"]
            nat = row["المعدل الطبيعي (كم/لتر)"]
            pct = ((eff / nat) - 1) * 100 if nat > 0 else 0
            
            st.markdown(f"""
            <div style="background: rgba(255, 23, 68, 0.15); border-right: 4px solid #ff1744; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                🚙 <b>{row['رقم السيارة']}</b> — {row['الموديل']} — شهر <b>{row['الشهر']}</b>
                <br>
                📊 المعدل الفعلي: <b style="color:#ff1744;">{eff:.2f} كم/لتر</b> | الطبيعي: {nat:.2f} | الفرق: <b>{pct:.1f}%</b>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== أعلى 5 استهلاكًا ====================
    st.markdown("### 📊 أعلى 5 سيارات استهلاكًا (لتر)")
    
    top_consumers = records.groupby("رقم السيارة").agg({
        "إجمالي اللترات": "sum",
        "المسافة (كم)": "sum"
    }).reset_index().sort_values("إجمالي اللترات", ascending=False).head(5)
    
    if not top_consumers.empty:
        fig = go.Figure(go.Bar(
            x=top_consumers["رقم السيارة"].astype(str),
            y=top_consumers["إجمالي اللترات"],
            marker=dict(
                color=top_consumers["إجمالي اللترات"],
                colorscale=[[0, '#ffb400'], [1, '#ff1744']],
                showscale=False
            ),
            text=top_consumers["إجمالي اللترات"].apply(lambda x: f"{x:,.0f}"),
            textposition='outside',
            textfont=dict(size=14, color='white'),
            hovertemplate='<b>سيارة %{x}</b><br>اللترات: %{y:,.0f}<extra></extra>'
        ))
        fig.update_layout(
            height=350,
            xaxis_title="رقم السيارة",
            yaxis_title="إجمالي اللترات",
            plot_bgcolor='rgba(10,10,25,0.6)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=13),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)'),
            yaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== آخر السندات ====================
    st.markdown("### 📋 آخر 10 سندات")
    
    recent = records.tail(10).iloc[::-1].copy()
    display_cols = ["رقم السند", "الشهر", "رقم السيارة", "إجمالي اللترات", "المسافة (كم)", "المعدل الفعلي (كم/لتر)", "المعدل الطبيعي (كم/لتر)", "الحالة"]
    st.dataframe(recent[display_cols], use_container_width=True, hide_index=True)

# ==================== تبويب: التقارير ====================
def render_diesel_reports():
    st.subheader("📊 تقارير وتحليلات الديزل")
    
    records = load_diesel_records()
    
    if records.empty:
        st.info("📭 مفيش بيانات للتقارير")
        return
    
    settings = load_diesel_settings()
    
    records["إجمالي اللترات"] = records.apply(
        lambda r: get_total_liters(r["رقم السند"]), axis=1
    )
    records["المعدل الفعلي (كم/لتر)"] = records.apply(
        lambda r: calculate_efficiency(r["المسافة (كم)"], r["إجمالي اللترات"]), axis=1
    )
    records["المعدل الطبيعي (كم/لتر)"] = records["رقم السيارة"].apply(
        lambda v: get_vehicle_avg(v, settings)
    )
    records["الحالة"] = records.apply(
        lambda r: get_record_status(r["المعدل الفعلي (كم/لتر)"], r["المعدل الطبيعي (كم/لتر)"]), axis=1
    )
    
    st.markdown("### 📊 ملخص عام")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 إجمالي السندات", len(records))
    col2.metric("⛽ إجمالي اللترات", f"{records['إجمالي اللترات'].sum():,.0f} لتر")
    col3.metric("📏 إجمالي المسافة", f"{pd.to_numeric(records['المسافة (كم)'], errors='coerce').sum():,.0f} كم")
    
    avg_eff = records[records["المعدل الفعلي (كم/لتر)"] > 0]["المعدل الفعلي (كم/لتر)"].mean()
    col4.metric("📊 متوسط المعدل", f"{avg_eff:.2f} كم/لتر" if pd.notna(avg_eff) else "—")
    
    st.markdown("---")
    
    st.markdown("### 🚙 تقرير مفصل لكل سيارة")
    
    by_vehicle = records.groupby("رقم السيارة").agg({
        "إجمالي اللترات": "sum",
        "المسافة (كم)": "sum",
        "المعدل الفعلي (كم/لتر)": "mean",
        "المعدل الطبيعي (كم/لتر)": "first",
        "رقم السند": "count"
    }).round(2).reset_index()
    
    by_vehicle.columns = ["رقم السيارة", "إجمالي اللترات", "إجمالي المسافة (كم)", "متوسط المعدل الفعلي", "المعدل الطبيعي", "عدد السندات"]
    by_vehicle = by_vehicle.sort_values("إجمالي اللترات", ascending=False)
    
    st.dataframe(by_vehicle, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 مقارنة المعدلات (الفعلي vs الطبيعي)")
    
    if not by_vehicle.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='الفعلي',
            x=by_vehicle["رقم السيارة"].astype(str),
            y=by_vehicle["متوسط المعدل الفعلي"],
            marker_color='#00e5ff',
            text=by_vehicle["متوسط المعدل الفعلي"].apply(lambda x: f"{x:.2f}"),
            textposition='outside',
            textfont=dict(size=12, color='white')
        ))
        
        fig.add_trace(go.Bar(
            name='الطبيعي',
            x=by_vehicle["رقم السيارة"].astype(str),
            y=by_vehicle["المعدل الطبيعي"],
            marker_color='#39ff14',
            text=by_vehicle["المعدل الطبيعي"].apply(lambda x: f"{x:.2f}"),
            textposition='outside',
            textfont=dict(size=12, color='white')
        ))
        
        fig.update_layout(
            height=450,
            barmode='group',
            xaxis_title="رقم السيارة",
            yaxis_title="كم/لتر",
            plot_bgcolor='rgba(10,10,25,0.6)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=13),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)'),
            yaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)'),
            legend=dict(
                font=dict(color='white'),
                bgcolor='rgba(10,10,25,0.6)',
                bordercolor='rgba(0,229,255,0.3)',
                borderwidth=1
            )
        )
        st.plotly_chart(fig, use_container_width=True)

# ==================== تبويب: الإعدادات ====================
def render_diesel_settings(vehicles_df):
    st.subheader("⚙️ إعدادات الديزل")
    
    settings = load_diesel_settings()
    
    # ==================== المعدل العام ====================
    st.markdown("### 🎯 المعدل الطبيعي العام")
    st.caption("القيمة دي هتطبق على كل السيارات إلا لو فيه معدل مخصص")
    
    general_avg = st.number_input(
        "المعدل العام (كم/لتر)",
        min_value=0.1,
        max_value=50.0,
        step=0.1,
        value=float(settings.get("المعدل الطبيعي العام (كم/لتر)", 5.0)),
        key="diesel_general_avg"
    )
    
    if st.button("💾 حفظ المعدل العام", key="save_general_avg"):
        settings["المعدل الطبيعي العام (كم/لتر)"] = general_avg
        save_diesel_settings(settings)
        st.success(f"✅ تم حفظ المعدل العام: {general_avg} كم/لتر")
        st.rerun()
    
    st.markdown("---")
    
    # ==================== معدلات مخصصة لكل سيارة ====================
    st.markdown("### 🚙 معدلات مخصصة لكل سيارة")
    st.caption("حدد معدل خاص لسيارة معينة. لو مش محدد، هيتطبق المعدل العام.")
    
    if vehicles_df.empty:
        st.warning("⚠️ مفيش سيارات مسجلة")
    else:
        vehicle_list = vehicles_df["الرقم"].astype(str).tolist()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_car = st.selectbox("🚙 اختار سيارة", ["-- اختر --"] + vehicle_list, key="diesel_custom_car")
        
        with col2:
            custom_avg = st.number_input(
                "المعدل (كم/لتر)",
                min_value=0.1,
                max_value=50.0,
                step=0.1,
                value=5.0,
                key="diesel_custom_avg"
            )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 حفظ المعدل المخصص", use_container_width=True, type="primary", key="save_custom_avg"):
                if selected_car == "-- اختر --":
                    st.error("⚠️ اختار سيارة أولاً")
                else:
                    key = f"معدل {selected_car}"
                    settings[key] = custom_avg
                    save_diesel_settings(settings)
                    st.success(f"✅ تم حفظ معدل السيارة {selected_car}: {custom_avg} كم/لتر")
                    st.rerun()
        
        with col_btn2:
            if st.button("🗑️ حذف المعدل المخصص", use_container_width=True, key="del_custom_avg"):
                if selected_car == "-- اختر --":
                    st.error("⚠️ اختار سيارة أولاً")
                else:
                    key = f"معدل {selected_car}"
                    if key in settings:
                        del settings[key]
                        save_diesel_settings(settings)
                        st.success(f"✅ تم حذف المعدل المخصص للسيارة {selected_car}")
                        st.rerun()
                    else:
                        st.warning("⚠️ مفيش معدل مخصص للسيارة دي")
        
        st.markdown("---")
        st.markdown("### 📋 قائمة المعدلات المخصصة")
        
        custom_keys = [k for k in settings.keys() if k.startswith("معدل ")]
        
        if not custom_keys:
            st.info("📭 مفيش معدلات مخصصة — كل السيارات بتستخدم المعدل العام")
        else:
            for key in custom_keys:
                vehicle_no = key.replace("معدل ", "")
                avg = settings[key]
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"🚙 **{vehicle_no}**")
                with col2:
                    st.markdown(f"📊 {avg} كم/لتر")
                with col3:
                    if st.button("🗑️", key=f"del_custom_{vehicle_no}"):
                        del settings[key]
                        save_diesel_settings(settings)
                        st.success(f"تم حذف معدل {vehicle_no}")
                        st.rerun()
    
    st.markdown("---")
    
    # ==================== معلومات ====================
    st.markdown("### ℹ️ معلومات")
    
    records = load_diesel_records()
    refuels = load_refuels()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 عدد السندات", len(records))
    col2.metric("⛽ عدد التعبئات", len(refuels))
    col3.metric("🚙 عدد السيارات", len(vehicles_df) if not vehicles_df.empty else 0)

# ==================== دالة القسم الرئيسية ====================
def render_diesel_section():
    init_diesel_files()
    
    vehicles_df = load_vehicles()
    drivers_list = load_drivers()
    
    st.title("⛽ قسم تعبئة الديزل")
    st.markdown("### متابعة استهلاك السيارات ومقارنتها بالمعدل الطبيعي")
    st.markdown("---")
    
    # ==================== عرض تفاصيل سند مفتوح ====================
    if st.session_state.get("open_diesel_record"):
        record_id = st.session_state["open_diesel_record"]
        
        col1, col2 = st.columns([5, 1])
        with col2:
            if st.button("⬅️ رجوع", use_container_width=True):
                st.session_state["open_diesel_record"] = None
                st.rerun()
        
        st.markdown("---")
        
        render_record_details(record_id, vehicles_df, drivers_list)
        
        return
    
    # ==================== التبويبات الرئيسية ====================
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📊 لوحة المعلومات",
        "➕ فتح سند شهري جديد",
        "📋 عرض السندات",
        "📊 التقارير",
        "⚙️ الإعدادات"
    ])
    
    with tab0:
        render_diesel_dashboard()
    
    with tab1:
        render_new_record_form(vehicles_df, drivers_list)
    
    with tab2:
        render_records_table(vehicles_df, drivers_list)
    
    with tab3:
        render_diesel_reports()
    
    with tab4:
        render_diesel_settings(vehicles_df)

# ==================== نهاية القسم ====================