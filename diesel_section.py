import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import plotly.graph_objects as go

# ==================== الملفات ====================
DIESEL_REFUELS_FILE = "diesel_refuels.xlsx"
DIESEL_ODOMETER_FILE = "diesel_odometer.xlsx"
DIESEL_SETTINGS_FILE = "diesel_settings.xlsx"

# ==================== الإعدادات الافتراضية ====================
DEFAULT_MONTHLY_AVG = 5.0  # كم/لتر

# ==================== دوال التهيئة ====================
def init_diesel_files():
    if not os.path.exists(DIESEL_REFUELS_FILE):
        df = pd.DataFrame(columns=[
            "الشهر", "رقم السيارة", "الموديل", "النوع",
            "اسم السائق", "الكمية (لتر)", "تاريخ التعبئة"
        ])
        df.to_excel(DIESEL_REFUELS_FILE, index=False)
    
    if not os.path.exists(DIESEL_ODOMETER_FILE):
        df = pd.DataFrame(columns=[
            "الشهر", "رقم السيارة", "قراءة بداية الشهر", "قراءة نهاية الشهر"
        ])
        df.to_excel(DIESEL_ODOMETER_FILE, index=False)
    
    if not os.path.exists(DIESEL_SETTINGS_FILE):
        settings = {
            "المعدل الطبيعي العام (كم/لتر)": DEFAULT_MONTHLY_AVG,
        }
        pd.DataFrame([settings]).to_excel(DIESEL_SETTINGS_FILE, index=False)

# ==================== دوال التحميل ====================
def load_refuels():
    try:
        return pd.read_excel(DIESEL_REFUELS_FILE)
    except:
        return pd.DataFrame()

def load_odometer():
    try:
        return pd.read_excel(DIESEL_ODOMETER_FILE)
    except:
        return pd.DataFrame()

def load_diesel_settings():
    try:
        df = pd.read_excel(DIESEL_SETTINGS_FILE)
        return df.iloc[0].to_dict()
    except:
        return {"المعدل الطبيعي العام (كم/لتر)": DEFAULT_MONTHLY_AVG}

def load_vehicles():
    try:
        df = pd.read_excel("vehicles.xlsx")
        df["الرقم"] = df["الرقم"].astype(str)
        return df
    except:
        return pd.DataFrame()

def load_drivers():
    try:
        df = pd.read_excel("drivers.xlsx")
        return df["السائقين"].dropna().astype(str).tolist()
    except:
        return []

def get_vehicle_info(car_no):
    df = load_vehicles()
    if df.empty:
        return None, None
    match = df[df["الرقم"].astype(str) == str(car_no)]
    if not match.empty:
        row = match.iloc[0]
        return row["الموديل"], row["النوع"]
    return None, None

# ==================== دوال الحفظ ====================
def save_refuels(df):
    df.to_excel(DIESEL_REFUELS_FILE, index=False)

def save_odometer(df):
    df.to_excel(DIESEL_ODOMETER_FILE, index=False)

def save_diesel_settings(settings):
    pd.DataFrame([settings]).to_excel(DIESEL_SETTINGS_FILE, index=False)

# ==================== دوال مساعدة ====================
def get_available_months():
    """يرجع قائمة الشهور المتاحة"""
    today = date.today()
    months = []
    for i in range(-12, 4):
        m = today.month + i
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        months.append(f"{y}-{m:02d}")
    months.reverse()
    return months

def get_refuels_for_month(month):
    """يرجع كل تعبئات شهر معين"""
    df = load_refuels()
    if df.empty:
        return pd.DataFrame()
    return df[df["الشهر"].astype(str) == str(month)].copy()

def get_odometer_for_month(month):
    """يرجع قراءات العدّاد لشهر معين"""
    df = load_odometer()
    if df.empty:
        return pd.DataFrame()
    return df[df["الشهر"].astype(str) == str(month)].copy()

def get_vehicle_total_liters(month, vehicle_no):
    """إجمالي اللترات لسيارة في شهر"""
    refuels = get_refuels_for_month(month)
    if refuels.empty:
        return 0.0
    refuels["الكمية (لتر)"] = pd.to_numeric(refuels["الكمية (لتر)"], errors="coerce")
    total = refuels[refuels["رقم السيارة"].astype(str) == str(vehicle_no)]["الكمية (لتر)"].sum()
    return float(total) if pd.notna(total) else 0.0

def get_vehicle_odometer(month, vehicle_no):
    """يرجع قراءات العدّاد لسيارة"""
    odo = get_odometer_for_month(month)
    if odo.empty:
        return 0.0, 0.0
    match = odo[odo["رقم السيارة"].astype(str) == str(vehicle_no)]
    if match.empty:
        return 0.0, 0.0
    row = match.iloc[0]
    try:
        start = float(row["قراءة بداية الشهر"])
    except:
        start = 0.0
    try:
        end = float(row["قراءة نهاية الشهر"])
    except:
        end = 0.0
    return start, end

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
    """يرجع المعدل الطبيعي لسيارة"""
    key = f"معدل {vehicle_no}"
    if key in settings and pd.notna(settings[key]):
        return float(settings[key])
    return float(settings.get("المعدل الطبيعي العام (كم/لتر)", DEFAULT_MONTHLY_AVG))

def get_record_status(efficiency, natural):
    """يرجع حالة السند"""
    if efficiency <= 0 or natural <= 0:
        return "⚪ غير محدد"
    ratio = efficiency / natural
    if ratio >= 0.9:
        return "✅ طبيعي"
    elif ratio >= 0.75:
        return "🟡 مقبول"
    else:
        return "🔴 غير طبيعي"

def build_summary_table(month):
    """يبني جدول ملخص لكل السيارات في شهر"""
    refuels = get_refuels_for_month(month)
    
    if refuels.empty:
        return pd.DataFrame()
    
    refuels["الكمية (لتر)"] = pd.to_numeric(refuels["الكمية (لتر)"], errors="coerce")
    
    settings = load_diesel_settings()
    
    # تجميع حسب السيارة
    vehicles_in_month = refuels["رقم السيارة"].astype(str).unique().tolist()
    
    results = []
    for vno in vehicles_in_month:
        total_liters = refuels[refuels["رقم السيارة"].astype(str) == vno]["الكمية (لتر)"].sum()
        
        start_odo, end_odo = get_vehicle_odometer(month, vno)
        distance = max(0, end_odo - start_odo)
        
        efficiency = calculate_efficiency(distance, total_liters)
        natural = get_vehicle_avg(vno, settings)
        status = get_record_status(efficiency, natural)
        
        model, vtype = get_vehicle_info(vno)
        
        results.append({
            "رقم السيارة": vno,
            "الموديل": model if model else "",
            "إجمالي اللترات": round(total_liters, 2),
            "قراءة بداية": start_odo,
            "قراءة نهاية": end_odo,
            "المسافة (كم)": round(distance, 2),
            "المعدل الفعلي": efficiency,
            "المعدل الطبيعي": natural,
            "الحالة": status,
        })
    
    if results:
        df = pd.DataFrame(results)
        return df.sort_values("رقم السيارة")
    return pd.DataFrame()

# ==================== تبويب: لوحة المعلومات ====================
def render_diesel_dashboard():
    st.subheader("📊 لوحة معلومات الديزل")
    
    refuels = load_refuels()
    
    if refuels.empty:
        st.info("📭 مفيش بيانات مسجلة لحد الآن. ابدأ من تبويب '📅 السند الشهري'")
        return
    
    refuels["الكمية (لتر)"] = pd.to_numeric(refuels["الكمية (لتر)"], errors="coerce")
    
    total_refuels = len(refuels)
    total_liters = refuels["الكمية (لتر)"].sum()
    total_vehicles = refuels["رقم السيارة"].nunique()
    total_months = refuels["الشهر"].nunique()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">⛽ إجمالي التعبئات</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_refuels}</div>
            <div style="font-size: 13px;">تعبئة</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">💰 إجمالي اللترات</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_liters:,.0f}</div>
            <div style="font-size: 13px;">لتر</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">🚙 عدد السيارات</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_vehicles}</div>
            <div style="font-size: 13px;">سيارة</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 14px;">📅 عدد الشهور</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_months}</div>
            <div style="font-size: 13px;">شهر</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # ==================== أعلى 5 سيارات استهلاكًا ====================
    st.markdown("### 🏆 أعلى 5 سيارات استهلاكًا")
    
    by_vehicle = refuels.groupby("رقم السيارة")["الكمية (لتر)"].sum().sort_values(ascending=False).head(5).reset_index()
    
    if not by_vehicle.empty:
        fig = go.Figure(go.Bar(
            x=by_vehicle["رقم السيارة"].astype(str),
            y=by_vehicle["الكمية (لتر)"],
            marker=dict(
                color=by_vehicle["الكمية (لتر)"],
                colorscale=[[0, '#ffb400'], [1, '#ff1744']],
                showscale=False
            ),
            text=by_vehicle["الكمية (لتر)"].apply(lambda x: f"{x:,.0f}"),
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
    
    # ==================== إجمالي اللترات لكل شهر ====================
    st.markdown("### 📅 إجمالي اللترات لكل شهر")
    
    by_month = refuels.groupby("الشهر")["الكمية (لتر)"].sum().sort_index().reset_index()
    
    if not by_month.empty:
        fig_month = go.Figure(go.Bar(
            x=by_month["الشهر"].astype(str),
            y=by_month["الكمية (لتر)"],
            marker=dict(
                color=by_month["الكمية (لتر)"],
                colorscale=[[0, '#39ff14'], [1, '#00e5ff']],
                showscale=False
            ),
            text=by_month["الكمية (لتر)"].apply(lambda x: f"{x:,.0f}"),
            textposition='outside',
            textfont=dict(size=12, color='white'),
            hovertemplate='<b>%{x}</b><br>اللترات: %{y:,.0f}<extra></extra>'
        ))
        fig_month.update_layout(
            height=350,
            xaxis_title="الشهر",
            yaxis_title="إجمالي اللترات",
            plot_bgcolor='rgba(10,10,25,0.6)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=13),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)'),
            yaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)')
        )
        st.plotly_chart(fig_month, use_container_width=True)

# ==================== تبويب: السند الشهري ====================
def render_monthly_record(vehicles_df, drivers_list):
    st.subheader("📅 السند الشهري")
    
    st.markdown("**السند الشهري = جدول تعبئات + قراءات العدّاد لشهر معين**")
    st.markdown("---")
    
    # اختيار الشهر
    month_options = get_available_months()
    today = date.today()
    default_month = f"{today.year}-{today.month:02d}"
    default_idx = month_options.index(default_month) if default_month in month_options else 0
    
    selected_month = st.selectbox("📅 اختار الشهر *", month_options, index=default_idx, key="diesel_month_selector")
    
    st.markdown(f"### 📅 سند شهر: `{selected_month}`")
    st.markdown("---")
    
    # التبويبات الداخلية
    inner_tab1, inner_tab2 = st.tabs(["⛽ التعبئات اليومية", "📏 قراءات العدّاد"])
    
    # ==================== تبويب 1: التعبئات اليومية ====================
    with inner_tab1:
        st.markdown("### ➕ إضافة تعبئة جديدة")
        
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            vehicle_list = vehicles_df["الرقم"].astype(str).tolist() if not vehicles_df.empty else []
            new_vehicle = st.selectbox("🚙 رقم السيارة *", ["-- اختر --"] + vehicle_list, key="new_refuel_vehicle")
        
        with col2:
            new_driver = st.selectbox("👤 اسم السائق *", ["-- اختر --"] + drivers_list, key="new_refuel_driver")
        
        with col3:
            new_liters = st.number_input("⛽ الكمية (لتر) *", min_value=0.0, step=5.0, value=0.0, key="new_refuel_liters")
        
        with col4:
            new_date = st.date_input("📅 تاريخ التعبئة *", value=date.today(), key="new_refuel_date")
        
        # عرض بيانات السيارة
        if new_vehicle != "-- اختر --":
            model, vtype = get_vehicle_info(new_vehicle)
            if model:
                st.info(f"🚛 **الموديل:** {model} | **النوع:** {vtype}")
        
        if st.button("➕ إضافة التعبئة", use_container_width=True, type="primary", key="add_refuel_btn"):
            errors = []
            if new_vehicle == "-- اختر --": errors.append("رقم السيارة مطلوب")
            if new_driver == "-- اختر --": errors.append("اسم السائق مطلوب")
            if new_liters <= 0: errors.append("الكمية لازم تكون أكبر من صفر")
            
            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
            else:
                model, vtype = get_vehicle_info(new_vehicle)
                
                new_row = {
                    "الشهر": selected_month,
                    "رقم السيارة": new_vehicle,
                    "الموديل": model if model else "",
                    "النوع": vtype if vtype else "",
                    "اسم السائق": new_driver,
                    "الكمية (لتر)": new_liters,
                    "تاريخ التعبئة": str(new_date)
                }
                
                full_df = load_refuels()
                full_df = pd.concat([full_df, pd.DataFrame([new_row])], ignore_index=True)
                save_refuels(full_df)
                
                st.success(f"✅ تم إضافة تعبئة: {new_vehicle} — {new_liters} لتر")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 تعبئات الشهر")
        
        month_refuels = get_refuels_for_month(selected_month)
        
        if month_refuels.empty:
            st.info("📭 مفيش تعبئات مسجلة للشهر ده")
        else:
            month_refuels = month_refuels.reset_index(drop=True)
            month_refuels["الكمية (لتر)"] = pd.to_numeric(month_refuels["الكمية (لتر)"], errors="coerce")
            
            st.markdown(f"**عدد التعبئات: {len(month_refuels)}**")
            
            # عرض الجدول
            for i, row in month_refuels.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 2, 1.5, 2, 0.8])
                with col1:
                    st.markdown(f"🚙 **{row['رقم السيارة']}**")
                with col2:
                    st.markdown(f"👤 {row['اسم السائق']}")
                with col3:
                    st.markdown(f"⛽ **{row['الكمية (لتر)']:.0f} لتر**")
                with col4:
                    st.markdown(f"📅 {row['تاريخ التعبئة']}")
                with col5:
                    st.markdown(f"🏷️ {row['الموديل']}")
                with col6:
                    if st.button("🗑️", key=f"del_refuel_{selected_month}_{i}"):
                        # نحذف السطر من الملف الأصلي
                        full_df = load_refuels()
                        mask = (
                            (full_df["الشهر"].astype(str) == str(selected_month)) &
                            (full_df["رقم السيارة"].astype(str) == str(row["رقم السيارة"])) &
                            (full_df["اسم السائق"].astype(str) == str(row["اسم السائق"])) &
                            (pd.to_numeric(full_df["الكمية (لتر)"], errors="coerce") == float(row["الكمية (لتر)"])) &
                            (full_df["تاريخ التعبئة"].astype(str) == str(row["تاريخ التعبئة"]))
                        )
                        idx_to_del = full_df[mask].index
                        if len(idx_to_del) > 0:
                            full_df = full_df.drop(idx_to_del[0]).reset_index(drop=True)
                            save_refuels(full_df)
                            st.success("✅ تم حذف التعبئة")
                            st.rerun()
            
            st.markdown("---")
            total = month_refuels["الكمية (لتر)"].sum()
            st.markdown(f"### 💰 إجمالي اللترات للشهر: **{total:,.0f} لتر**")

    # ==================== تبويب 2: قراءات العدّاد ====================
    with inner_tab2:
        st.markdown("### 📏 قراءات العدّاد")
        st.caption("سجل قراءة العداد في بداية ونهاية الشهر لكل سيارة عندها تعبئات")
        
        # نجيب السيارات اللي عندها تعبئات في الشهر ده
        month_refuels = get_refuels_for_month(selected_month)
        
        if month_refuels.empty:
            st.warning("⚠️ مفيش تعبئات مسجلة للشهر ده — سجل تعبئات الأول")
        else:
            vehicles_in_month = sorted(month_refuels["رقم السيارة"].astype(str).unique().tolist())
            
            st.markdown(f"**عدد السيارات: {len(vehicles_in_month)}**")
            st.markdown("---")
            
            # نجهز البيانات الحالية
            odo_df = get_odometer_for_month(selected_month)
            
            # لكل سيارة: صف بالإدخال
            updated_odos = {}
            
            for vno in vehicles_in_month:
                # نجيب القراءات الحالية
                cur_start, cur_end = get_vehicle_odometer(selected_month, vno)
                
                model, vtype = get_vehicle_info(vno)
                
                st.markdown(f"#### 🚙 سيارة {vno} — {model} ({vtype})")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_start = st.number_input(
                        "🔢 قراءة بداية الشهر (كم)",
                        min_value=0.0,
                        step=100.0,
                        value=float(cur_start),
                        key=f"odo_start_{selected_month}_{vno}"
                    )
                
                with col2:
                    new_end = st.number_input(
                        "🔢 قراءة نهاية الشهر (كم)",
                        min_value=0.0,
                        step=100.0,
                        value=float(cur_end),
                        key=f"odo_end_{selected_month}_{vno}"
                    )
                
                with col3:
                    distance = max(0, new_end - new_start)
                    total_liters = get_vehicle_total_liters(selected_month, vno)
                    efficiency = calculate_efficiency(distance, total_liters)
                    
                    st.metric("📏 المسافة", f"{distance:,.0f} كم")
                    st.caption(f"⛽ {total_liters:,.0f} لتر | 📊 {efficiency:.2f} كم/لتر" if efficiency > 0 else f"⛽ {total_liters:,.0f} لتر")
                
                updated_odos[vno] = {"start": new_start, "end": new_end}
                st.markdown("---")
            
            # زر الحفظ
            if st.button("💾 حفظ كل القراءات", use_container_width=True, type="primary", key="save_all_odos"):
                full_odo = load_odometer()
                
                # نشيل قراءات الشهر ده (لو موجودة) ونحط الجديد
                full_odo = full_odo[full_odo["الشهر"].astype(str) != str(selected_month)]
                
                new_rows = []
                for vno, vals in updated_odos.items():
                    new_rows.append({
                        "الشهر": selected_month,
                        "رقم السيارة": vno,
                        "قراءة بداية الشهر": vals["start"],
                        "قراءة نهاية الشهر": vals["end"]
                    })
                
                if new_rows:
                    full_odo = pd.concat([full_odo, pd.DataFrame(new_rows)], ignore_index=True)
                    save_odometer(full_odo)
                    st.success(f"✅ تم حفظ قراءات {len(new_rows)} سيارة")
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 ملخص الشهر")
    
    summary = build_summary_table(selected_month)
    
    if summary.empty:
        st.info("📭 مفيش بيانات لعرضها — سجل تعبئات وقراءات أولاً")
    else:
        # جدول الملخص
        display_summary = summary.copy()
        display_summary.columns = ["رقم السيارة", "الموديل", "إجمالي اللترات", "بداية", "نهاية", "المسافة (كم)", "المعدل الفعلي", "المعدل الطبيعي", "الحالة"]
        st.dataframe(display_summary, use_container_width=True, hide_index=True)
        
        # تنبيهات
        abnormal = summary[summary["الحالة"].str.contains("غير طبيعي", na=False)]
        
        if not abnormal.empty:
            st.error(f"🚨 **{len(abnormal)} سيارة** استهلاكها غير طبيعي في شهر {selected_month}")
            for i, row in abnormal.iterrows():
                eff = row["المعدل الفعلي"]
                nat = row["المعدل الطبيعي"]
                pct = ((eff / nat) - 1) * 100 if nat > 0 else 0
                
                st.markdown(f"""
                <div style="background: rgba(255, 23, 68, 0.15); border-right: 4px solid #ff1744; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    🚙 <b>{row['رقم السيارة']}</b> — {row['الموديل']}
                    <br>
                    📊 الفعلي: <b style="color:#ff1744;">{eff:.2f} كم/لتر</b> | الطبيعي: {nat:.2f} | الفرق: <b>{pct:.1f}%</b>
                </div>
                """, unsafe_allow_html=True)
        else:
            if not summary.empty:
                st.success(f"✅ كل السيارات استهلاكها طبيعي في شهر {selected_month}")

# ==================== تبويب: عرض الشهور ====================
def render_months_list():
    st.subheader("📋 كل الشهور المسجلة")
    
    refuels = load_refuels()
    
    if refuels.empty:
        st.info("📭 مفيش شهور مسجلة لحد الآن")
        return
    
    refuels["الكمية (لتر)"] = pd.to_numeric(refuels["الكمية (لتر)"], errors="coerce")
    
    # تجميع حسب الشهر
    months_summary = refuels.groupby("الشهر").agg({
        "الكمية (لتر)": "sum",
        "رقم السيارة": "nunique",
        "اسم السائق": "nunique",
    }).reset_index()
    months_summary.columns = ["الشهر", "إجمالي اللترات", "عدد السيارات", "عدد السائقين"]
    
    # نضيف عدد التعبئات
    counts = refuels.groupby("الشهر").size().reset_index(name="عدد التعبئات")
    months_summary = months_summary.merge(counts, on="الشهر")
    
    months_summary = months_summary.sort_values("الشهر", ascending=False)
    
    st.markdown(f"**عدد الشهور: {len(months_summary)}**")
    st.markdown("---")
    
    for i, row in months_summary.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        
        with col1:
            st.markdown(f"📅 **{row['الشهر']}**")
        with col2:
            st.markdown(f"⛽ {row['إجمالي اللترات']:,.0f} لتر")
        with col3:
            st.markdown(f"🚙 {row['عدد السيارات']} سيارة")
        with col4:
            st.markdown(f"📋 {row['عدد التعبئات']} تعبئة")
        with col5:
            if st.button("🗑️ حذف الشهر", key=f"del_month_{row['الشهر']}"):
                # نحذف كل تعبئات وقراءات الشهر
                full_df = load_refuels()
                full_df = full_df[full_df["الشهر"].astype(str) != str(row["الشهر"])]
                save_refuels(full_df)
                
                odo_df = load_odometer()
                odo_df = odo_df[odo_df["الشهر"].astype(str) != str(row["الشهر"])]
                save_odometer(odo_df)
                
                st.success(f"✅ تم حذف شهر {row['الشهر']}")
                st.rerun()
        
        st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)

# ==================== تبويب: التقارير ====================
def render_diesel_reports():
    st.subheader("📊 تقارير وتحليلات الديزل")
    
    refuels = load_refuels()
    
    if refuels.empty:
        st.info("📭 مفيش بيانات للتقارير")
        return
    
    refuels["الكمية (لتر)"] = pd.to_numeric(refuels["الكمية (لتر)"], errors="coerce")
    
    st.markdown("### 📊 ملخص عام")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 عدد التعبئات", len(refuels))
    col2.metric("⛽ إجمالي اللترات", f"{refuels['الكمية (لتر)'].sum():,.0f} لتر")
    col3.metric("🚙 عدد السيارات", refuels["رقم السيارة"].nunique())
    col4.metric("👤 عدد السائقين", refuels["اسم السائق"].nunique())
    
    st.markdown("---")
    
    # ==================== تقرير 1: استهلاك كل سيارة ====================
    st.markdown("### 🚙 تقرير مفصل لكل سيارة")
    
    settings = load_diesel_settings()
    
    by_vehicle = refuels.groupby("رقم السيارة").agg({
        "الكمية (لتر)": "sum",
        "الشهر": "nunique",
        "اسم السائق": "nunique",
    }).reset_index()
    by_vehicle.columns = ["رقم السيارة", "إجمالي اللترات", "عدد الشهور", "عدد السائقين"]
    
    # نحسب متوسط المعدل لكل سيارة من السندات
    eff_list = []
    for vno in by_vehicle["رقم السيارة"].astype(str):
        # نجيب كل الشهور للسيارة ده
        months = refuels[refuels["رقم السيارة"].astype(str) == vno]["الشهر"].unique()
        effs = []
        for month in months:
            total_liters = get_vehicle_total_liters(month, vno)
            start, end = get_vehicle_odometer(month, vno)
            dist = max(0, end - start)
            if total_liters > 0 and dist > 0:
                effs.append(calculate_efficiency(dist, total_liters))
        
        if effs:
            avg_eff = sum(effs) / len(effs)
            eff_list.append(round(avg_eff, 2))
        else:
            eff_list.append(0.0)
    
    by_vehicle["متوسط المعدل الفعلي"] = eff_list
    by_vehicle["المعدل الطبيعي"] = by_vehicle["رقم السيارة"].astype(str).apply(
        lambda v: get_vehicle_avg(v, settings)
    )
    by_vehicle["الحالة"] = by_vehicle.apply(
        lambda r: get_record_status(r["متوسط المعدل الفعلي"], r["المعدل الطبيعي"]), axis=1
    )
    
    by_vehicle = by_vehicle.sort_values("إجمالي اللترات", ascending=False)
    
    st.dataframe(by_vehicle, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ==================== تقرير 2: إجمالي اللترات لكل شهر ====================
    st.markdown("### 📅 إجمالي اللترات لكل شهر")
    
    by_month = refuels.groupby("الشهر")["الكمية (لتر)"].sum().sort_index().reset_index()
    by_month.columns = ["الشهر", "إجمالي اللترات"]
    
    st.dataframe(by_month, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ==================== تقرير 3: تفاصيل السائقين ====================
    st.markdown("### 👤 إجمالي اللترات لكل سائق")
    
    by_driver = refuels.groupby("اسم السائق").agg({
        "الكمية (لتر)": "sum",
        "رقم السيارة": "nunique",
        "الشهر": "nunique",
    }).reset_index()
    by_driver.columns = ["اسم السائق", "إجمالي اللترات", "عدد السيارات", "عدد الشهور"]
    by_driver = by_driver.sort_values("إجمالي اللترات", ascending=False)
    
    st.dataframe(by_driver, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ==================== رسم بياني ====================
    st.markdown("### 📊 مقارنة المعدلات (الفعلي vs الطبيعي)")
    
    if not by_vehicle.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='الفعلي',
            x=by_vehicle["رقم السيارة"].astype(str),
            y=by_vehicle["متوسط المعدل الفعلي"],
            marker_color='#00e5ff',
            text=by_vehicle["متوسط المعدل الفعلي"].apply(lambda x: f"{x:.2f}" if x > 0 else "—"),
            textposition='outside',
            textfont=dict(size=11, color='white')
        ))
        
        fig.add_trace(go.Bar(
            name='الطبيعي',
            x=by_vehicle["رقم السيارة"].astype(str),
            y=by_vehicle["المعدل الطبيعي"],
            marker_color='#39ff14',
            text=by_vehicle["المعدل الطبيعي"].apply(lambda x: f"{x:.2f}"),
            textposition='outside',
            textfont=dict(size=11, color='white')
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
def render_diesel_settings_tab(vehicles_df):
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
    
    # ==================== معدلات مخصصة ====================
    st.markdown("### 🚙 معدلات مخصصة لكل سيارة")
    st.caption("حدد معدل خاص لسيارة معينة. لو مش محدد، هيتطبق المعدل العام.")
    
    if vehicles_df.empty:
        st.warning("⚠️ مفيش سيارات مسجلة")
    else:
        vehicle_list = vehicles_df["الرقم"].astype(str).tolist()
        
        col1, col2 = st.columns([2, 2])
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
    st.markdown("### ℹ️ معلومات")
    
    refuels = load_refuels()
    odo = load_odometer()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 عدد التعبئات", len(refuels))
    col2.metric("📅 عدد الشهور", refuels["الشهر"].nunique() if not refuels.empty else 0)
    col3.metric("🚙 عدد السيارات", refuels["رقم السيارة"].nunique() if not refuels.empty else 0)

# ==================== دالة القسم الرئيسية ====================
def render_diesel_section():
    init_diesel_files()
    
    vehicles_df = load_vehicles()
    drivers_list = load_drivers()
    
    st.title("⛽ قسم تعبئة الديزل")
    st.markdown("### متابعة استهلاك السيارات ومقارنتها بالمعدل الطبيعي")
    st.markdown("---")
    
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📊 لوحة المعلومات",
        "📅 السند الشهري",
        "📋 عرض الشهور",
        "📊 التقارير",
        "⚙️ الإعدادات"
    ])
    
    with tab0:
        render_diesel_dashboard()
    
    with tab1:
        render_monthly_record(vehicles_df, drivers_list)
    
    with tab2:
        render_months_list()
    
    with tab3:
        render_diesel_reports()
    
    with tab4:
        render_diesel_settings_tab(vehicles_df)

# ==================== نهاية القسم ====================
