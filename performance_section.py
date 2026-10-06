import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import os
import plotly.graph_objects as go

PERF_WORKERS_FILE = "performance_workers.xlsx"
PERF_WAREHOUSES_FILE = "performance_warehouses.xlsx"
PERF_DATA_FILE = "performance_data.xlsx"
PERF_SETTINGS_FILE = "performance_settings.xlsx"

DEFAULT_WORKERS = ["احد", "سيف", "دبيندرا", "اوشيما", "جمساد"]
DEFAULT_WAREHOUSES = ["مخزن صبحان", "مخزن الشويخ", "مخزن الوفرة", "مخزن العبدلي"]

DEFAULT_SETTINGS = {
    "حد التنبيه اليومي (%)": 90,
    "حد التنبيه الشهري (%)": 95,
}

def init_performance_files():
    if not os.path.exists(PERF_WORKERS_FILE):
        pd.DataFrame({"العامل": DEFAULT_WORKERS}).to_excel(PERF_WORKERS_FILE, index=False)
    if not os.path.exists(PERF_WAREHOUSES_FILE):
        pd.DataFrame({"المخزن": DEFAULT_WAREHOUSES}).to_excel(PERF_WAREHOUSES_FILE, index=False)
    if not os.path.exists(PERF_DATA_FILE):
        df = pd.DataFrame(columns=["رقم السجل", "التاريخ", "المخزن", "عدد الأصناف المجرودة", "اسم العامل", "عدد الأخطاء", "الدقة (%)", "ملاحظات"])
        df.to_excel(PERF_DATA_FILE, index=False)
    if not os.path.exists(PERF_SETTINGS_FILE):
        pd.DataFrame([DEFAULT_SETTINGS]).to_excel(PERF_SETTINGS_FILE, index=False)

def load_perf_workers():
    try:
        df = pd.read_excel(PERF_WORKERS_FILE)
        return df["العامل"].dropna().astype(str).tolist()
    except:
        return DEFAULT_WORKERS

def load_perf_warehouses():
    try:
        df = pd.read_excel(PERF_WAREHOUSES_FILE)
        return df["المخزن"].dropna().astype(str).tolist()
    except:
        return DEFAULT_WAREHOUSES

def load_perf_data():
    try:
        return pd.read_excel(PERF_DATA_FILE)
    except:
        return pd.DataFrame()

def load_perf_settings():
    try:
        df = pd.read_excel(PERF_SETTINGS_FILE)
        return df.iloc[0].to_dict()
    except:
        return DEFAULT_SETTINGS

def save_perf_worker(name):
    df = pd.read_excel(PERF_WORKERS_FILE)
    if name not in df["العامل"].astype(str).tolist():
        df = pd.concat([df, pd.DataFrame({"العامل": [name]})], ignore_index=True)
        df.to_excel(PERF_WORKERS_FILE, index=False)
        return True
    return False

def save_perf_warehouse(name):
    df = pd.read_excel(PERF_WAREHOUSES_FILE)
    if name not in df["المخزن"].astype(str).tolist():
        df = pd.concat([df, pd.DataFrame({"المخزن": [name]})], ignore_index=True)
        df.to_excel(PERF_WAREHOUSES_FILE, index=False)
        return True
    return False

def save_perf_data(df):
    df.to_excel(PERF_DATA_FILE, index=False)

def save_perf_settings(settings):
    pd.DataFrame([settings]).to_excel(PERF_SETTINGS_FILE, index=False)

def calculate_accuracy(total_items, errors):
    try:
        total_items = float(total_items)
        errors = float(errors)
        if total_items <= 0:
            return 0.0
        if errors > total_items:
            errors = total_items
        accuracy = ((total_items - errors) / total_items) * 100
        return round(accuracy, 2)
    except:
        return 0.0

def get_next_record_id():
    df = load_perf_data()
    if df.empty:
        return "PERF-0001"
    return f"PERF-{len(df)+1:04d}"

def get_worker_stats(worker_name, date_from=None, date_to=None):
    df = load_perf_data()
    empty = {"count": 0, "avg": 0.0, "max": 0.0, "min": 0.0, "total_errors": 0}
    if df.empty:
        return empty
    df_filtered = df[df["اسم العامل"].astype(str) == str(worker_name)].copy()
    if df_filtered.empty:
        return empty
    if date_from is not None and date_to is not None:
        df_filtered["التاريخ_dt"] = pd.to_datetime(df_filtered["التاريخ"], errors="coerce")
        df_filtered = df_filtered[
            (df_filtered["التاريخ_dt"].dt.date >= date_from) &
            (df_filtered["التاريخ_dt"].dt.date <= date_to)
        ]
    if df_filtered.empty:
        return empty
    df_filtered["الدقة (%)"] = pd.to_numeric(df_filtered["الدقة (%)"], errors="coerce")
    df_filtered["عدد الأخطاء"] = pd.to_numeric(df_filtered["عدد الأخطاء"], errors="coerce")
    return {
        "count": len(df_filtered),
        "avg": round(df_filtered["الدقة (%)"].mean(), 2),
        "max": round(df_filtered["الدقة (%)"].max(), 2),
        "min": round(df_filtered["الدقة (%)"].min(), 2),
        "total_errors": int(df_filtered["عدد الأخطاء"].sum()),
    }

def get_all_workers_ranking(date_from=None, date_to=None):
    workers = load_perf_workers()
    results = []
    for worker in workers:
        stats = get_worker_stats(worker, date_from, date_to)
        if stats["count"] > 0:
            results.append({
                "العامل": worker,
                "عدد الجردات": stats["count"],
                "متوسط الدقة (%)": stats["avg"],
                "أعلى دقة (%)": stats["max"],
                "أقل دقة (%)": stats["min"],
                "إجمالي الأخطاء": stats["total_errors"],
            })
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values("متوسط الدقة (%)", ascending=False).reset_index(drop=True)
        df.insert(0, "الترتيب", range(1, len(df) + 1))
        return df
    return pd.DataFrame()

def render_edit_record_form(record_id):
    form_key = f"edit_perf_{str(record_id).replace(' ', '_').replace('/', '_')}"
    df = load_perf_data()
    match = df[df["رقم السجل"].astype(str) == str(record_id)]
    if match.empty:
        st.error("⚠️ السجل مش موجود")
        if st.button("إغلاق", key=f"close_{form_key}"):
            st.session_state["edit_perf_record"] = None
            st.rerun()
        return
    row = match.iloc[0]
    workers_list = load_perf_workers()
    warehouses_list = load_perf_warehouses()
    st.markdown(f"### ✏️ تعديل السجل: `{record_id}`")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        try:
            cur_date = pd.to_datetime(row["التاريخ"]).date()
        except:
            cur_date = date.today()
        new_date = st.date_input("📅 التاريخ", value=cur_date, key=f"{form_key}_date")
        cur_wh = str(row["المخزن"])
        wh_idx = warehouses_list.index(cur_wh) if cur_wh in warehouses_list else 0
        new_wh = st.selectbox("🏭 المخزن", warehouses_list, index=wh_idx, key=f"{form_key}_wh")
        try:
            cur_items = int(float(row["عدد الأصناف المجرودة"]))
        except:
            cur_items = 0
        new_items = st.number_input("📦 عدد الأصناف المجرودة", min_value=0, step=1, value=cur_items, key=f"{form_key}_items")
    with col2:
        cur_worker = str(row["اسم العامل"])
        w_idx = workers_list.index(cur_worker) if cur_worker in workers_list else 0
        new_worker = st.selectbox("👤 اسم العامل", workers_list, index=w_idx, key=f"{form_key}_worker")
        try:
            cur_errors = int(float(row["عدد الأخطاء"]))
        except:
            cur_errors = 0
        new_errors = st.number_input("❌ عدد الأخطاء", min_value=0, step=1, value=cur_errors, key=f"{form_key}_errors")
        new_accuracy = calculate_accuracy(new_items, new_errors)
        st.metric("📊 الدقة (%)", f"{new_accuracy:.2f}%")
    new_notes = st.text_area("📝 ملاحظات", value=str(row.get("ملاحظات", "")), key=f"{form_key}_notes")
    st.markdown("---")
    if new_errors > new_items:
        st.error(f"🚫 عدد الأخطاء ({new_errors}) أكبر من عدد الأصناف ({new_items})!")
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 حفظ التعديلات", use_container_width=True, type="primary", key=f"{form_key}_save"):
            if new_errors > new_items:
                st.error("⚠️ عدد الأخطاء أكبر من عدد الأصناف")
            else:
                full_df = load_perf_data()
                mask = full_df["رقم السجل"].astype(str) == str(record_id)
                idx = full_df[mask].index[0]
                full_df.loc[idx, "التاريخ"] = str(new_date)
                full_df.loc[idx, "المخزن"] = new_wh
                full_df.loc[idx, "عدد الأصناف المجرودة"] = new_items
                full_df.loc[idx, "اسم العامل"] = new_worker
                full_df.loc[idx, "عدد الأخطاء"] = new_errors
                full_df.loc[idx, "الدقة (%)"] = new_accuracy
                full_df.loc[idx, "ملاحظات"] = new_notes.strip()
                save_perf_data(full_df)
                st.session_state["edit_perf_record"] = None
                st.rerun()
    with col_cancel:
        if st.button("❌ إلغاء", use_container_width=True, key=f"{form_key}_cancel"):
            st.session_state["edit_perf_record"] = None
            st.rerun()

def render_delete_record_form(record_id):
    form_key = f"del_perf_{str(record_id).replace(' ', '_').replace('/', '_')}"
    df = load_perf_data()
    match = df[df["رقم السجل"].astype(str) == str(record_id)]
    if match.empty:
        st.error("⚠️ السجل مش موجود")
        if st.button("إغلاق", key=f"close_{form_key}"):
            st.session_state["delete_perf_record"] = None
            st.rerun()
        return
    row = match.iloc[0]
    st.markdown(f"### 🗑️ حذف السجل: `{record_id}`")
    st.warning(f"⚠️ **هل أنت متأكد من حذف السجل** `{record_id}` **؟**")
    st.markdown(f"**التاريخ:** {row['التاريخ']}")
    st.markdown(f"**العامل:** {row['اسم العامل']}")
    st.markdown(f"**المخزن:** {row['المخزن']}")
    st.markdown(f"**عدد الأصناف:** {row['عدد الأصناف المجرودة']}")
    st.markdown(f"**عدد الأخطاء:** {row['عدد الأخطاء']}")
    st.markdown(f"**الدقة:** {row['الدقة (%)']}%")
    st.markdown("**لا يمكن التراجع عن هذا الإجراء.**")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ نعم، احذف", type="primary", use_container_width=True, key=f"{form_key}_confirm"):
            full_df = load_perf_data()
            full_df = full_df[full_df["رقم السجل"].astype(str) != str(record_id)]
            save_perf_data(full_df)
            st.session_state["delete_perf_record"] = None
            st.rerun()
    with col_no:
        if st.button("❌ إلغاء", use_container_width=True, key=f"{form_key}_cancel"):
            st.session_state["delete_perf_record"] = None
            st.rerun()
            
def render_performance_section():
    init_performance_files()
    
    workers_list = load_perf_workers()
    warehouses_list = load_perf_warehouses()
    
    st.title("📊 مؤشر الأداء القياسي لتقييم العامل")
    st.markdown("### قياس دقة الجرد اليومي للعمال")
    st.markdown("---")
    
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📊 لوحة المعلومات",
        "➕ إدخال جرد يومي",
        "📋 عرض السجلات",
        "📊 التقارير",
        "⚙️ الإعدادات"
    ])
    
    with tab0:
        st.subheader("📊 لوحة معلومات الأداء")
        data = load_perf_data()
        settings = load_perf_settings()
        
        if data.empty:
            st.info("📭 مفيش بيانات مسجلة لحد الآن")
        else:
            data["الدقة (%)"] = pd.to_numeric(data["الدقة (%)"], errors="coerce")
            data["التاريخ_dt"] = pd.to_datetime(data["التاريخ"], errors="coerce")
            
            total_records = len(data)
            total_workers = data["اسم العامل"].nunique()
            avg_accuracy = round(data["الدقة (%)"].mean(), 2)
            total_errors = int(pd.to_numeric(data["عدد الأخطاء"], errors="coerce").sum())
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                    <div style="font-size: 14px;">📋 إجمالي السجلات</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_records}</div>
                    <div style="font-size: 13px;">سجل</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                    <div style="font-size: 14px;">👥 عدد العمال</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_workers}</div>
                    <div style="font-size: 13px;">عامل</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                    <div style="font-size: 14px;">📊 متوسط الدقة</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{avg_accuracy:.2f}%</div>
                    <div style="font-size: 13px;">من كل السجلات</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                    <div style="font-size: 14px;">❌ إجمالي الأخطاء</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_errors}</div>
                    <div style="font-size: 13px;">خطأ</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            
            st.markdown("### 🏆 ترتيب العمال (كل البيانات)")
            ranking = get_all_workers_ranking()
            
            if ranking.empty:
                st.info("📭 مفيش بيانات كافية للترتيب")
            else:
                if len(ranking) >= 3:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        second = ranking.iloc[1]
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%); padding: 20px; border-radius: 15px; text-align: center; color: #333;">
                            <div style="font-size: 40px;">🥈</div>
                            <div style="font-size: 20px; font-weight: bold; margin: 10px 0;">{second['العامل']}</div>
                            <div style="font-size: 24px; font-weight: bold;">{second['متوسط الدقة (%)']:.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        first = ranking.iloc[0]
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); padding: 25px; border-radius: 15px; text-align: center; color: #333;">
                            <div style="font-size: 50px;">🥇</div>
                            <div style="font-size: 24px; font-weight: bold; margin: 10px 0;">{first['العامل']}</div>
                            <div style="font-size: 28px; font-weight: bold;">{first['متوسط الدقة (%)']:.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        third = ranking.iloc[2]
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #cd7f32 0%, #e8a866 100%); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                            <div style="font-size: 40px;">🥉</div>
                            <div style="font-size: 20px; font-weight: bold; margin: 10px 0;">{third['العامل']}</div>
                            <div style="font-size: 24px; font-weight: bold;">{third['متوسط الدقة (%)']:.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(ranking, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### 🚨 التنبيهات")
            
            daily_threshold = float(settings.get("حد التنبيه اليومي (%)", 90))
            monthly_threshold = float(settings.get("حد التنبيه الشهري (%)", 95))
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"#### ⚠️ تنبيهات يومية (أقل من {daily_threshold}%)")
                low_daily = data[data["الدقة (%)"] < daily_threshold].copy()
                if low_daily.empty:
                    st.success(f"✅ مفيش جردات أقل من {daily_threshold}%")
                else:
                    st.dataframe(low_daily[["التاريخ", "اسم العامل", "الدقة (%)"]].sort_values("الدقة (%)").head(10), use_container_width=True, hide_index=True)
            with col2:
                st.markdown(f"#### ⚠️ تنبيهات شهرية (أقل من {monthly_threshold}%)")
                if not ranking.empty:
                    low_monthly = ranking[ranking["متوسط الدقة (%)"] < monthly_threshold]
                    if low_monthly.empty:
                        st.success(f"✅ كل العمال أعلى من {monthly_threshold}%")
                    else:
                        st.dataframe(low_monthly[["الترتيب", "العامل", "متوسط الدقة (%)"]], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 مفيش بيانات")
                    
    with tab1:
        st.subheader("➕ إدخال سجل جرد جديد")
        
        st.markdown("""
        **ملاحظة:** كل سجل = **عامل واحد** بس.
        
        لو عايز تسجل أكثر من عامل في نفس اليوم، سجل عامل واحد، وبعدها التاريخ والمخزن وعدد الأصناف هيفضلوا موجودين عشان تسجل العامل اللي بعده بسرعة.
        """)
        
        st.markdown("---")
        
        if "perf_last_date" not in st.session_state:
            st.session_state["perf_last_date"] = date.today()
        if "perf_last_wh" not in st.session_state:
            st.session_state["perf_last_wh"] = "-- اختر --"
        if "perf_last_items" not in st.session_state:
            st.session_state["perf_last_items"] = 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input(
                "📅 التاريخ *",
                value=st.session_state["perf_last_date"],
                key="new_perf_date"
            )
            
            wh_options = ["-- اختر --"] + warehouses_list
            wh_default_idx = wh_options.index(st.session_state["perf_last_wh"]) if st.session_state["perf_last_wh"] in wh_options else 0
            warehouse = st.selectbox(
                "🏭 المخزن *",
                wh_options,
                index=wh_default_idx,
                key="new_perf_wh"
            )
        
        with col2:
            total_items = st.number_input(
                "📦 عدد الأصناف المجرودة *",
                min_value=0,
                step=1,
                value=st.session_state["perf_last_items"],
                key="new_perf_items"
            )
        
        st.markdown("---")
        st.markdown("### 👤 بيانات العامل")
        
        col1, col2 = st.columns(2)
        
        with col1:
            worker_name = st.selectbox(
                "👤 اسم العامل *",
                ["-- اختر --"] + workers_list,
                key="new_perf_worker_select"
            )
        
        with col2:
            worker_errors = st.number_input(
                "❌ عدد الأخطاء *",
                min_value=0,
                step=1,
                value=0,
                key="new_perf_errors"
            )
        
        if worker_name != "-- اختر --" and total_items > 0:
            accuracy = calculate_accuracy(total_items, worker_errors)
            
            if accuracy >= 95:
                color = "#39ff14"
                icon = "🟢"
            elif accuracy >= 90:
                color = "#ffb400"
                icon = "🟡"
            else:
                color = "#ff1744"
                icon = "🔴"
            
            st.markdown(f"""
            <div style="background: rgba(20,20,40,0.6); border: 2px solid {color}; border-radius: 12px; padding: 15px; text-align: center; margin-top: 10px;">
                <div style="font-size: 16px; color: rgba(255,255,255,0.8);">📊 دقة العامل {worker_name}</div>
                <div style="font-size: 36px; font-weight: bold; color: {color}; margin: 10px 0;">{icon} {accuracy:.2f}%</div>
                <div style="font-size: 13px; color: rgba(255,255,255,0.6);">({total_items} - {worker_errors}) ÷ {total_items} × 100</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        notes = st.text_area("📝 ملاحظات (اختياري)", placeholder="أي تفاصيل إضافية", key="new_perf_notes")
        
        st.markdown("---")
        
        col_btn1, col_btn2 = st.columns([3, 1])
        
        with col_btn1:
            submitted = st.button("💾 حفظ السجل", use_container_width=True, type="primary", key="save_perf_data_btn")
        
        with col_btn2:
            clear_btn = st.button("🔄 تفريغ الخانات", use_container_width=True, key="clear_perf_data_btn")
        
        if clear_btn:
            st.session_state["perf_last_date"] = date.today()
            st.session_state["perf_last_wh"] = "-- اختر --"
            st.session_state["perf_last_items"] = 0
            for k in ["new_perf_worker_select", "new_perf_errors", "new_perf_notes"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.success("✅ تم تفريغ الخانات")
            st.rerun()
        
        if submitted:
            errors_list = []
            if warehouse == "-- اختر --": errors_list.append("المخزن مطلوب")
            if worker_name == "-- اختر --": errors_list.append("اسم العامل مطلوب")
            if total_items <= 0: errors_list.append("عدد الأصناف لازم يكون أكبر من صفر")
            if worker_errors > total_items: errors_list.append(f"عدد الأخطاء ({worker_errors}) أكبر من عدد الأصناف ({total_items})")
            
            if errors_list:
                for err in errors_list:
                    st.error(f"⚠️ {err}")
            else:
                new_id = get_next_record_id()
                accuracy = calculate_accuracy(total_items, worker_errors)
                
                new_row = {
                    "رقم السجل": new_id,
                    "التاريخ": str(entry_date),
                    "المخزن": warehouse,
                    "عدد الأصناف المجرودة": total_items,
                    "اسم العامل": worker_name,
                    "عدد الأخطاء": worker_errors,
                    "الدقة (%)": accuracy,
                    "ملاحظات": notes.strip()
                }
                
                full_df = load_perf_data()
                full_df = pd.concat([full_df, pd.DataFrame([new_row])], ignore_index=True)
                save_perf_data(full_df)
                
                st.session_state["perf_last_date"] = entry_date
                st.session_state["perf_last_wh"] = warehouse
                st.session_state["perf_last_items"] = total_items
                
                for k in ["new_perf_worker_select", "new_perf_errors", "new_perf_notes"]:
                    if k in st.session_state:
                        del st.session_state[k]
                
                st.success(f"✅ تم حفظ السجل **{new_id}** — العامل: {worker_name} — الدقة: {accuracy:.2f}%")
                st.info("💡 التاريخ والمخزن وعدد الأصناف محفوظين — جاهز لإدخال العامل التالي")
                st.balloons()
                st.rerun()
    
    with tab2:
        st.subheader("📋 سجلات الجرد")
        data = load_perf_data()
        
        if data.empty:
            st.info("📭 مفيش سجلات مسجلة لحد الآن")
        else:
            data["التاريخ_dt"] = pd.to_datetime(data["التاريخ"], errors="coerce")
            data["الدقة (%)"] = pd.to_numeric(data["الدقة (%)"], errors="coerce")
            data["عدد الأخطاء"] = pd.to_numeric(data["عدد الأخطاء"], errors="coerce")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                min_date = data["التاريخ_dt"].min().date() if not data["التاريخ_dt"].isna().all() else date.today()
                filter_from = st.date_input("📅 من تاريخ", value=min_date, key="perf_filter_from")
            with col2:
                max_date = data["التاريخ_dt"].max().date() if not data["التاريخ_dt"].isna().all() else date.today()
                filter_to = st.date_input("📅 إلى تاريخ", value=max_date, key="perf_filter_to")
            with col3:
                filter_worker = st.selectbox("👤 العامل", ["الكل"] + workers_list, key="perf_filter_worker")
            with col4:
                filter_wh = st.selectbox("🏭 المخزن", ["الكل"] + warehouses_list, key="perf_filter_wh")
            
            filtered = data.copy()
            filtered = filtered[
                (filtered["التاريخ_dt"].dt.date >= filter_from) &
                (filtered["التاريخ_dt"].dt.date <= filter_to)
            ]
            
            if filter_worker != "الكل":
                filtered = filtered[filtered["اسم العامل"].astype(str) == filter_worker]
            
            if filter_wh != "الكل":
                filtered = filtered[filtered["المخزن"].astype(str) == filter_wh]
            
            if not filtered.empty:
                total_records = len(filtered)
                avg_acc = round(filtered["الدقة (%)"].mean(), 2)
                total_err = int(filtered["عدد الأخطاء"].sum())
                st.markdown(f"**عدد السجلات: {total_records}** | **متوسط الدقة: {avg_acc:.2f}%** | **إجمالي الأخطاء: {total_err}**")
            
            st.markdown("---")
            st.caption("💡 علّم على ☑ في عمود 'اختر' لتعديل أو حذف السجل")
            
            if filtered.empty:
                st.warning("⚠️ مفيش سجلات مطابقة للفلاتر")
            else:
                display_df = filtered.copy()
                display_df["التاريخ"] = display_df["التاريخ_dt"].dt.strftime("%Y-%m-%d")
                display_df = display_df[["رقم السجل", "التاريخ", "المخزن", "عدد الأصناف المجرودة", "اسم العامل", "عدد الأخطاء", "الدقة (%)", "ملاحظات"]].copy()
                display_df = display_df.reset_index(drop=True)
                display_df.insert(0, "اختر", False)
                
                for col in ["رقم السجل", "التاريخ", "المخزن", "اسم العامل", "ملاحظات"]:
                    display_df[col] = display_df[col].astype(str)
                
                edited_df = st.data_editor(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=500,
                    key="perf_data_editor",
                    column_config={
                        "اختر": st.column_config.CheckboxColumn("اختر", default=False, width="small"),
                        "رقم السجل": st.column_config.TextColumn("🔢 السجل", width="small"),
                        "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="small"),
                        "المخزن": st.column_config.TextColumn("🏭 المخزن", width="small"),
                        "عدد الأصناف المجرودة": st.column_config.NumberColumn("📦 الأصناف", width="small"),
                        "اسم العامل": st.column_config.TextColumn("👤 العامل", width="small"),
                        "عدد الأخطاء": st.column_config.NumberColumn("❌ الأخطاء", width="small"),
                        "الدقة (%)": st.column_config.NumberColumn("📊 الدقة %", format="%.2f", width="small"),
                        "ملاحظات": st.column_config.TextColumn("📝 ملاحظات", width="medium"),
                    }
                )
                
                st.markdown("---")
                st.markdown("### 🔧 إجراءات على السجلات المحددة")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
                
                with col_btn1:
                    if st.button("✏️ تعديل المحدد", use_container_width=True, type="primary", key="edit_perf_btn"):
                        selected = edited_df[edited_df["اختر"] == True]
                        if len(selected) == 0:
                            st.warning("⚠️ علّم على سجل أولًا")
                        elif len(selected) > 1:
                            st.error("⚠️ اختار سجل واحد بس")
                        else:
                            st.session_state["edit_perf_record"] = str(selected.iloc[0]["رقم السجل"])
                            st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ حذف المحدد", use_container_width=True, key="delete_perf_btn"):
                        selected = edited_df[edited_df["اختر"] == True]
                        if len(selected) == 0:
                            st.warning("⚠️ علّم على سجل أولًا")
                        elif len(selected) > 1:
                            st.error("⚠️ اختار سجل واحد بس")
                        else:
                            st.session_state["delete_perf_record"] = str(selected.iloc[0]["رقم السجل"])
                            st.rerun()
                
                with col_btn3:
                    st.markdown("💡 **ملاحظة:** لتعديل أو حذف سجل، علّم على ☑ جنبه واضغط الزر المناسب")
                
                if st.session_state.get("edit_perf_record"):
                    st.markdown("---")
                    render_edit_record_form(st.session_state["edit_perf_record"])
                
                if st.session_state.get("delete_perf_record"):
                    st.markdown("---")
                    render_delete_record_form(st.session_state["delete_perf_record"])
                    
    with tab3:
        st.subheader("📊 تقارير وتحليلات الأداء")
        data = load_perf_data()
        
        if data.empty:
            st.info("📭 مفيش بيانات للتقارير")
        else:
            data["التاريخ_dt"] = pd.to_datetime(data["التاريخ"], errors="coerce")
            data["الدقة (%)"] = pd.to_numeric(data["الدقة (%)"], errors="coerce")
            data["عدد الأخطاء"] = pd.to_numeric(data["عدد الأخطاء"], errors="coerce")
            
            st.markdown("### 📅 فلتر الفترة الزمنية")
            col1, col2 = st.columns(2)
            with col1:
                min_date = data["التاريخ_dt"].min().date() if not data["التاريخ_dt"].isna().all() else date.today()
                date_from = st.date_input("من تاريخ", value=min_date, key="rep_perf_from")
            with col2:
                max_date = data["التاريخ_dt"].max().date() if not data["التاريخ_dt"].isna().all() else date.today()
                date_to = st.date_input("إلى تاريخ", value=max_date, key="rep_perf_to")
            
            filtered = data[
                (data["التاريخ_dt"].dt.date >= date_from) &
                (data["التاريخ_dt"].dt.date <= date_to)
            ].copy()
            
            if filtered.empty:
                st.warning("⚠️ مفيش بيانات في الفترة المحددة")
            else:
                st.markdown("---")
                st.markdown("### 💡 ملخص الفترة")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📋 عدد السجلات", len(filtered))
                col2.metric("📊 متوسط الدقة", f"{filtered['الدقة (%)'].mean():.2f}%")
                col3.metric("❌ إجمالي الأخطاء", f"{int(filtered['عدد الأخطاء'].sum())}")
                col4.metric("👥 عدد العمال", filtered["اسم العامل"].nunique())
                
                st.markdown("---")
                st.markdown("### 🏆 ترتيب العمال في الفترة")
                
                ranking = get_all_workers_ranking(date_from, date_to)
                
                if ranking.empty:
                    st.info("📭 مفيش بيانات كافية")
                else:
                    st.dataframe(ranking, use_container_width=True, hide_index=True)
                    
                    fig_rank = go.Figure(go.Bar(
                        x=ranking["العامل"],
                        y=ranking["متوسط الدقة (%)"],
                        marker=dict(
                            color=ranking["متوسط الدقة (%)"],
                            colorscale=[[0, '#ff1744'], [0.5, '#ffb400'], [1, '#39ff14']],
                            showscale=False,
                        ),
                        text=ranking["متوسط الدقة (%)"].apply(lambda x: f"{x:.2f}%"),
                        textposition='outside',
                        textfont=dict(size=14, color='white'),
                        hovertemplate='<b>%{x}</b><br>متوسط الدقة: %{y:.2f}%<extra></extra>'
                    ))
                    fig_rank.update_layout(
                        height=400,
                        xaxis_title="العامل",
                        yaxis_title="متوسط الدقة (%)",
                        plot_bgcolor='rgba(10,10,25,0.6)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', size=13),
                        margin=dict(l=40, r=40, t=40, b=40),
                        xaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)'),
                        yaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)')
                    )
                    st.plotly_chart(fig_rank, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 📈 تطور الأداء خلال الفترة")
                
                top_workers_data = filtered.groupby("اسم العامل").agg({"الدقة (%)": "mean"}).reset_index().sort_values("الدقة (%)", ascending=False).head(5)
                top_workers = top_workers_data["اسم العامل"].tolist()
                
                fig_trend = go.Figure()
                colors = ['#00e5ff', '#ff4ecd', '#39ff14', '#ffb400', '#ff1744']
                
                for idx, worker in enumerate(top_workers):
                    worker_data = filtered[filtered["اسم العامل"].astype(str) == str(worker)].copy()
                    worker_data = worker_data.sort_values("التاريخ_dt")
                    
                    fig_trend.add_trace(go.Scatter(
                        x=worker_data["التاريخ_dt"].dt.strftime("%Y-%m-%d"),
                        y=worker_data["الدقة (%)"],
                        mode='lines+markers',
                        name=worker,
                        line=dict(color=colors[idx % len(colors)], width=3),
                        marker=dict(size=10),
                        hovertemplate=f'<b>{worker}</b><br>%{{x}}<br>الدقة: %{{y:.2f}}%<extra></extra>'
                    ))
                
                fig_trend.update_layout(
                    height=450,
                    xaxis_title="التاريخ",
                    yaxis_title="الدقة (%)",
                    hovermode='closest',
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
                st.plotly_chart(fig_trend, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🏭 متوسط الدقة حسب المخزن")
                
                by_wh = filtered.groupby("المخزن").agg({
                    "الدقة (%)": "mean",
                    "عدد الأخطاء": "sum",
                    "رقم السجل": "count"
                }).round(2).reset_index()
                by_wh.columns = ["المخزن", "متوسط الدقة (%)", "إجمالي الأخطاء", "عدد السجلات"]
                by_wh = by_wh.sort_values("متوسط الدقة (%)", ascending=False)
                
                st.dataframe(by_wh, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("### 📋 تفاصيل الأداء لكل عامل")
                
                selected_worker = st.selectbox("اختار عامل لعرض تفاصيله", workers_list, key="worker_details")
                worker_data = filtered[filtered["اسم العامل"].astype(str) == str(selected_worker)].copy()
                
                if worker_data.empty:
                    st.info(f"📭 مفيش بيانات للعامل {selected_worker}")
                else:
                    stats = get_worker_stats(selected_worker, date_from, date_to)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("📋 عدد الجردات", stats["count"])
                    col2.metric("📊 متوسط الدقة", f"{stats['avg']:.2f}%")
                    col3.metric("🔝 أعلى دقة", f"{stats['max']:.2f}%")
                    col4.metric("🔻 أقل دقة", f"{stats['min']:.2f}%")
                    col5.metric("❌ إجمالي الأخطاء", stats["total_errors"])
                    
                    st.markdown(f"#### 📋 كل جردات {selected_worker}")
                    
                    display_worker = worker_data.copy()
                    display_worker["التاريخ_str"] = display_worker["التاريخ_dt"].dt.strftime("%Y-%m-%d")
                    display_worker = display_worker[["التاريخ_str", "المخزن", "عدد الأصناف المجرودة", "عدد الأخطاء", "الدقة (%)"]].copy()
                    display_worker.columns = ["التاريخ", "المخزن", "عدد الأصناف المجرودة", "عدد الأخطاء", "الدقة (%)"]
                    display_worker = display_worker.sort_values("التاريخ", ascending=False)
                    st.dataframe(display_worker, use_container_width=True, hide_index=True)
                    
    with tab4:
        st.subheader("⚙️ إعدادات قسم مؤشر الأداء")
        
        st.markdown("### 🔔 إعدادات التنبيهات")
        settings = load_perf_settings()
        
        col1, col2 = st.columns(2)
        with col1:
            new_daily = st.number_input(
                "⚠️ حد التنبيه اليومي (%) — لو دقة العامل أقل من",
                min_value=0, max_value=100,
                value=int(settings.get("حد التنبيه اليومي (%)", 90)),
                key="perf_setting_daily"
            )
        with col2:
            new_monthly = st.number_input(
                "⚠️ حد التنبيه الشهري (%) — لو متوسط العامل أقل من",
                min_value=0, max_value=100,
                value=int(settings.get("حد التنبيه الشهري (%)", 95)),
                key="perf_setting_monthly"
            )
        
        if st.button("💾 حفظ إعدادات التنبيهات", key="save_perf_settings_btn"):
            new_settings = {
                "حد التنبيه اليومي (%)": new_daily,
                "حد التنبيه الشهري (%)": new_monthly,
            }
            save_perf_settings(new_settings)
            st.success(f"✅ تم حفظ الإعدادات — يومي: {new_daily}% / شهري: {new_monthly}%")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 👥 إدارة العمال")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_worker = st.text_input("اسم عامل جديد", placeholder="مثال: محمد", key="new_perf_worker")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ إضافة عامل", key="add_perf_worker_btn"):
                if new_worker.strip():
                    if save_perf_worker(new_worker.strip()):
                        st.success(f"✅ تم إضافة: {new_worker}")
                        st.rerun()
                    else:
                        st.warning("⚠️ العامل موجود بالفعل")
                else:
                    st.error("⚠️ اكتب اسم العامل")
        
        workers_current = load_perf_workers()
        st.markdown(f"**عدد العمال: {len(workers_current)}**")
        
        for i, worker in enumerate(workers_current):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"• {worker}")
            with col2:
                if st.button("🗑️", key=f"del_perf_worker_{i}"):
                    df = pd.read_excel(PERF_WORKERS_FILE)
                    df = df[df["العامل"] != worker]
                    df.to_excel(PERF_WORKERS_FILE, index=False)
                    st.success(f"تم حذف: {worker}")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 🏭 إدارة المخازن")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_wh = st.text_input("اسم مخزن جديد", placeholder="مثال: مخزن الجهراء", key="new_perf_wh_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ إضافة مخزن", key="add_perf_wh_btn"):
                if new_wh.strip():
                    if save_perf_warehouse(new_wh.strip()):
                        st.success(f"✅ تم إضافة: {new_wh}")
                        st.rerun()
                    else:
                        st.warning("⚠️ المخزن موجود بالفعل")
                else:
                    st.error("⚠️ اكتب اسم المخزن")
        
        warehouses_current = load_perf_warehouses()
        st.markdown(f"**عدد المخازن: {len(warehouses_current)}**")
        
        for i, wh in enumerate(warehouses_current):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"• {wh}")
            with col2:
                if st.button("🗑️", key=f"del_perf_wh_{i}"):
                    df = pd.read_excel(PERF_WAREHOUSES_FILE)
                    df = df[df["المخزن"] != wh]
                    df.to_excel(PERF_WAREHOUSES_FILE, index=False)
                    st.success(f"تم حذف: {wh}")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ معلومات")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            data = load_perf_data()
            st.metric("📋 إجمالي السجلات", len(data))
        with col2:
            st.metric("👥 عدد العمال", len(load_perf_workers()))
        with col3:
            st.metric("🏭 عدد المخازن", len(load_perf_warehouses()))
                    
