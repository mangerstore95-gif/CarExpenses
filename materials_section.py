import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import os

from materials_edit import (
    get_batches_with_remaining,
    get_issued_for_batch,
    load_batches,
    load_issues,
    load_materials,
    load_warehouses,
    load_materials_settings
)

# ==================== الملفات ====================
MATERIALS_FILE = "materials.xlsx"
WAREHOUSES_FILE = "warehouses.xlsx"
BATCHES_FILE = "batches.xlsx"
ISSUES_FILE = "issues.xlsx"
MATERIALS_SETTINGS_FILE = "materials_settings.xlsx"

# ==================== البيانات الافتراضية ====================
DEFAULT_MATERIALS = [
    "EPS :GF-SA", "EPS : H-MS", "EPS : H-SA", "EPS : E-SA", "EPS : E-SB",
    "EPS : H-S", "EPS : H-SB", "EPS R.200", "EPS R.300", "EPS R.400",
    "EPS F 205", "EPS F 105", "EPS:B-103", "EPS : EUROCELL 200RL", "EPS : EUROCELL 150R",
]

DEFAULT_WAREHOUSES = ["مخزن صبحان", "مخزن الشويخ", "مخزن الوفرة", "مخزن العبدلي"]

DEFAULT_SETTINGS = {
    "مدة التنبيه (يوم)": 30,
    "مدة التحذير الأقصى (يوم)": 7,
}

# ==================== دوال تهيئة الملفات ====================
def init_materials_files():
    if not os.path.exists(MATERIALS_FILE):
        pd.DataFrame({"الصنف": DEFAULT_MATERIALS}).to_excel(MATERIALS_FILE, index=False)
    if not os.path.exists(WAREHOUSES_FILE):
        pd.DataFrame({"المخزن": DEFAULT_WAREHOUSES}).to_excel(WAREHOUSES_FILE, index=False)
    if not os.path.exists(BATCHES_FILE):
        df = pd.DataFrame(columns=[
            "رقم الدفعة", "الصنف", "المخزن", "تاريخ الإنتاج", "تاريخ الانتهاء",
            "تاريخ الوصول", "الوزن/عبوة (كجم)", "عدد العبوات", 
            "الكمية الكلية (كجم)", "الكمية المتبقية (كجم)", "ملاحظات"
        ])
        df.to_excel(BATCHES_FILE, index=False)
    if not os.path.exists(ISSUES_FILE):
        df = pd.DataFrame(columns=[
            "رقم الصرف", "التاريخ", "رقم الدفعة", "الصنف", "المخزن",
            "الكمية المصروفة (كجم)", "الجهة/الطلب", "ملاحظات"
        ])
        df.to_excel(ISSUES_FILE, index=False)
    if not os.path.exists(MATERIALS_SETTINGS_FILE):
        pd.DataFrame([DEFAULT_SETTINGS]).to_excel(MATERIALS_SETTINGS_FILE, index=False)

# ==================== دوال الحفظ المحلية ====================
def save_material(name):
    df = pd.read_excel(MATERIALS_FILE)
    if name not in df["الصنف"].astype(str).tolist():
        df = pd.concat([df, pd.DataFrame({"الصنف": [name]})], ignore_index=True)
        df.to_excel(MATERIALS_FILE, index=False)
        return True
    return False

def save_warehouse(name):
    df = pd.read_excel(WAREHOUSES_FILE)
    if name not in df["المخزن"].astype(str).tolist():
        df = pd.concat([df, pd.DataFrame({"المخزن": [name]})], ignore_index=True)
        df.to_excel(WAREHOUSES_FILE, index=False)
        return True
    return False

def save_batch(batch_data):
    df = load_batches()
    df = pd.concat([df, pd.DataFrame([batch_data])], ignore_index=True)
    df.to_excel(BATCHES_FILE, index=False)

def save_issue(issue_data):
    df = load_issues()
    df = pd.concat([df, pd.DataFrame([issue_data])], ignore_index=True)
    df.to_excel(ISSUES_FILE, index=False)

def save_materials_settings(settings):
    pd.DataFrame([settings]).to_excel(MATERIALS_SETTINGS_FILE, index=False)

# ==================== دوال الحساب ====================
def get_expiry_status(expiry_date, warning_days=30, critical_days=7):
    try:
        exp = pd.to_datetime(expiry_date).date()
        today = date.today()
        days_left = (exp - today).days
        if days_left < 0:
            return "منتهي", days_left, "🔴"
        elif days_left <= critical_days:
            return "تحذير عاجل", days_left, "🟠"
        elif days_left <= warning_days:
            return "قريب الانتهاء", days_left, "🟡"
        else:
            return "صالح", days_left, "🟢"
    except:
        return "غير محدد", None, "⚪"

def get_total_stock_by_material():
    batches = load_batches()
    if batches.empty:
        return pd.DataFrame()
    batches = get_batches_with_remaining(batches)
    batches = batches[batches["الكمية المتبقية (كجم)"] > 0]
    total = batches.groupby("الصنف")["الكمية المتبقية (كجم)"].sum().reset_index()
    total.columns = ["الصنف", "الإجمالي (كجم)"]
    return total.sort_values("الإجمالي (كجم)", ascending=False)

def get_stock_by_warehouse():
    batches = load_batches()
    if batches.empty:
        return pd.DataFrame()
    batches = get_batches_with_remaining(batches)
    batches = batches[batches["الكمية المتبقية (كجم)"] > 0]
    total = batches.groupby("المخزن")["الكمية المتبقية (كجم)"].sum().reset_index()
    total.columns = ["المخزن", "الإجمالي (كجم)"]
    return total.sort_values("الإجمالي (كجم)", ascending=False)

def get_expiring_batches():
    batches = load_batches()
    if batches.empty:
        return pd.DataFrame()
    settings = load_materials_settings()
    warning_days = int(settings.get("مدة التنبيه (يوم)", 30))
    critical_days = int(settings.get("مدة التحذير الأقصى (يوم)", 7))
    batches = get_batches_with_remaining(batches)
    batches = batches[batches["الكمية المتبقية (كجم)"] > 0]
    results = []
    for idx, row in batches.iterrows():
        status, days_left, icon = get_expiry_status(row["تاريخ الانتهاء"], warning_days, critical_days)
        if status in ["قريب الانتهاء", "تحذير عاجل", "منتهي"]:
            results.append({
                "الحالة": f"{icon} {status}",
                "رقم الدفعة": row["رقم الدفعة"],
                "الصنف": row["الصنف"],
                "المخزن": row["المخزن"],
                "تاريخ الانتهاء": row["تاريخ الانتهاء"],
                "أيام متبقية": days_left,
                "الكمية المتبقية (كجم)": row["الكمية المتبقية (كجم)"],
            })
    if results:
        df = pd.DataFrame(results)
        return df.sort_values("أيام متبقية")
    return pd.DataFrame()

# ==================== نافذة تعديل الدفعة ====================
@st.dialog("✏️ تعديل دفعة", width="large")
def edit_batch_dialog_local(batch_no):
    batches = load_batches()
    match = batches[batches["رقم الدفعة"].astype(str) == str(batch_no)]
    
    if match.empty:
        st.error("⚠️ الدفعة مش موجودة")
        if st.button("إغلاق"):
            st.session_state["edit_batch"] = None
            st.query_params.clear()
            st.rerun()
        return
    
    row = match.iloc[0]
    materials_list = load_materials()
    warehouses_list = load_warehouses()
    issued_qty = get_issued_for_batch(batch_no)
    
    st.markdown(f"**رقم الدفعة:** `{batch_no}`")
    st.info(f"📊 الكمية المصروفة من الدفعة دي: **{issued_qty:,.0f} كجم**")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        current_mat = str(row["الصنف"])
        mat_idx = materials_list.index(current_mat) if current_mat in materials_list else 0
        new_mat = st.selectbox("🏷️ الصنف", materials_list, index=mat_idx, key="edit_batch_mat")
        
        current_wh = str(row["المخزن"])
        wh_idx = warehouses_list.index(current_wh) if current_wh in warehouses_list else 0
        new_wh = st.selectbox("🏭 المخزن", warehouses_list, index=wh_idx, key="edit_batch_wh")
        
        try:
            current_prod = pd.to_datetime(row["تاريخ الإنتاج"]).date()
        except:
            current_prod = date.today()
        new_prod = st.date_input("🏭 تاريخ الإنتاج", value=current_prod, key="edit_batch_prod")
        
        try:
            current_exp = pd.to_datetime(row["تاريخ الانتهاء"]).date()
        except:
            current_exp = date.today()
        new_exp = st.date_input("⏰ تاريخ الانتهاء", value=current_exp, key="edit_batch_exp")
    
    with col2:
        try:
            current_arr = pd.to_datetime(row["تاريخ الوصول"]).date()
        except:
            current_arr = date.today()
        new_arr = st.date_input("📅 تاريخ الوصول", value=current_arr, key="edit_batch_arr")
        
        try:
            current_weight = float(row["الوزن/عبوة (كجم)"])
        except:
            current_weight = 750.0
        new_weight = st.number_input("⚖️ الوزن/عبوة (كجم)", min_value=0.0, step=10.0, value=current_weight, key="edit_batch_weight")
        
        try:
            current_bags = int(row["عدد العبوات"])
        except:
            current_bags = 0
        new_bags = st.number_input("📦 عدد العبوات", min_value=0, step=1, value=current_bags, key="edit_batch_bags")
        
        new_total = new_weight * new_bags
        st.metric("📊 الكمية الكلية الجديدة", f"{new_total:,.0f} كجم")
    
    new_notes = st.text_area("📝 ملاحظات", value=str(row.get("ملاحظات", "")), key="edit_batch_notes")
    
    st.markdown("---")
    
    if new_total < issued_qty:
        st.error(f"🚫 الكمية الجديدة ({new_total:,.0f}) أقل من المصروفة ({issued_qty:,.0f})!")
    
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 حفظ التعديلات", use_container_width=True, type="primary", key="save_edit_batch_btn"):
            if new_total < issued_qty:
                st.error("⚠️ الكمية الجديدة أقل من المصروفة")
            else:
                full_df = load_batches()
                mask = full_df["رقم الدفعة"].astype(str) == str(batch_no)
                idx = full_df[mask].index[0]
                full_df.loc[idx, "الصنف"] = new_mat
                full_df.loc[idx, "المخزن"] = new_wh
                full_df.loc[idx, "تاريخ الإنتاج"] = str(new_prod)
                full_df.loc[idx, "تاريخ الانتهاء"] = str(new_exp)
                full_df.loc[idx, "تاريخ الوصول"] = str(new_arr)
                full_df.loc[idx, "الوزن/عبوة (كجم)"] = new_weight
                full_df.loc[idx, "عدد العبوات"] = new_bags
                full_df.loc[idx, "الكمية الكلية (كجم)"] = new_total
                full_df.loc[idx, "الكمية المتبقية (كجم)"] = new_total - issued_qty
                full_df.loc[idx, "ملاحظات"] = new_notes.strip()
                full_df.to_excel(BATCHES_FILE, index=False)
                st.session_state["edit_batch"] = None
                st.query_params.clear()
                st.success(f"✅ تم تحديث الدفعة {batch_no}")
                st.rerun()
    
    with col_cancel:
        if st.button("❌ إلغاء", use_container_width=True, key="cancel_edit_batch_btn"):
            st.session_state["edit_batch"] = None
            st.query_params.clear()
            st.rerun()

# ==================== نافذة تأكيد حذف الدفعة ====================
@st.dialog("🗑️ تأكيد الحذف")
def delete_batch_dialog_local(batch_no):
    batches = load_batches()
    match = batches[batches["رقم الدفعة"].astype(str) == str(batch_no)]
    
    if match.empty:
        st.error("⚠️ الدفعة مش موجودة")
        if st.button("إغلاق"):
            st.session_state["delete_batch"] = None
            st.query_params.clear()
            st.rerun()
        return
    
    row = match.iloc[0]
    issued_qty = get_issued_for_batch(batch_no)
    
    if issued_qty > 0:
        st.error(f"🚫 **لا يمكن حذف هذه الدفعة!**")
        st.warning(f"فيها **{issued_qty:,.0f} كجم** مصروفة. لازم تحذف سندات الصرف الأول.")
        issues = load_issues()
        related = issues[issues["رقم الدفعة"].astype(str) == str(batch_no)]
        if not related.empty:
            st.markdown("**سندات الصرف المرتبطة:**")
            st.dataframe(related[["رقم الصرف", "التاريخ", "الكمية المصروفة (كجم)", "الجهة/الطلب"]], use_container_width=True, hide_index=True)
        if st.button("إغلاق", use_container_width=True):
            st.session_state["delete_batch"] = None
            st.query_params.clear()
            st.rerun()
    else:
        st.warning(f"⚠️ **هل أنت متأكد من حذف الدفعة** `{batch_no}` **؟**")
        st.markdown(f"**الصنف:** {row['الصنف']}")
        st.markdown(f"**المخزن:** {row['المخزن']}")
        st.markdown(f"**الكمية الكلية:** {row['الكمية الكلية (كجم)']:,.0f} كجم")
        st.markdown("**لا يمكن التراجع عن هذا الإجراء.**")
        
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ نعم، احذف", type="primary", use_container_width=True, key="confirm_del_batch_btn"):
                full_df = load_batches()
                full_df = full_df[full_df["رقم الدفعة"].astype(str) != str(batch_no)]
                full_df.to_excel(BATCHES_FILE, index=False)
                st.session_state["delete_batch"] = None
                st.query_params.clear()
                st.success(f"✅ تم حذف الدفعة {batch_no}")
                st.rerun()
        with col_no:
            if st.button("❌ إلغاء", use_container_width=True, key="cancel_del_batch_btn"):
                st.session_state["delete_batch"] = None
                st.query_params.clear()
                st.rerun()
                
# ==================== دالة القسم الرئيسية ====================
def render_materials_section():
    init_materials_files()
    
    materials_list = load_materials()
    warehouses_list = load_warehouses()
    
    st.title("📦 قسم صلاحية المواد الخام")
    st.markdown("### إدارة دفعات المواد الخام وتنبيهات الصلاحية")
    st.markdown("---")
    
    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 لوحة المعلومات",
        "➕ استلام مواد",
        "📤 صرف مواد",
        "📋 عرض المخزون",
        "📊 التقارير",
        "⚙️ الإعدادات"
    ])
    
    # ==================== تبويب 0: لوحة المعلومات ====================
    with tab0:
        st.subheader("📊 لوحة معلومات المواد الخام")
        
        batches = load_batches()
        
        if batches.empty:
            st.info("📭 مفيش دفعات مسجلة لحد الآن")
        else:
            batches_with_rem = get_batches_with_remaining(batches)
            batches_active = batches_with_rem[batches_with_rem["الكمية المتبقية (كجم)"] > 0]
            
            total_weight = batches_active["الكمية المتبقية (كجم)"].sum()
            total_batches = len(batches_active)
            total_materials = batches_active["الصنف"].nunique()
            total_warehouses = batches_active["المخزن"].nunique()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(102,126,234,0.4);">
                    <div style="font-size: 14px;">⚖️ إجمالي الرصيد</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_weight:,.0f}</div>
                    <div style="font-size: 13px;">كجم</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(245,87,108,0.4);">
                    <div style="font-size: 14px;">📦 عدد الدفعات النشطة</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_batches}</div>
                    <div style="font-size: 13px;">دفعة</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(79,172,254,0.4);">
                    <div style="font-size: 14px;">🏷️ عدد الأصناف</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_materials}</div>
                    <div style="font-size: 13px;">صنف</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(67,233,123,0.4);">
                    <div style="font-size: 14px;">🏭 عدد المخازن</div>
                    <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{total_warehouses}</div>
                    <div style="font-size: 13px;">مخزن</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            
            st.markdown("### 🚨 تنبيهات الصلاحية")
            
            expiring = get_expiring_batches()
            
            if expiring.empty:
                st.success("✅ كل الدفعات سارية — مفيش تنبيهات")
            else:
                settings = load_materials_settings()
                warning_days = int(settings.get("مدة التنبيه (يوم)", 30))
                critical_days = int(settings.get("مدة التحذير الأقصى (يوم)", 7))
                
                st.markdown(f"**عدد الدفعات اللي محتاجة انتباه: {len(expiring)}** (فترة التحذير: {warning_days} يوم)")
                
                for idx, row in expiring.iterrows():
                    days = row["أيام متبقية"]
                    
                    if days < 0:
                        bg = "rgba(255, 23, 68, 0.2)"
                        border = "#ff1744"
                        icon = "🔴"
                        text = f"**منتهية منذ {abs(days)} يوم**"
                    elif days <= critical_days:
                        bg = "rgba(255, 152, 0, 0.2)"
                        border = "#ff9800"
                        icon = "🟠"
                        text = f"**هتنتهي خلال {days} يوم**"
                    else:
                        bg = "rgba(255, 235, 59, 0.2)"
                        border = "#ffeb3b"
                        icon = "🟡"
                        text = f"**هتنتهي خلال {days} يوم**"
                    
                    st.markdown(f"""
                    <div style="background: {bg}; border-right: 4px solid {border}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                {icon} <b style="color:white;">{row['الصنف']}</b> — دفعة <b style="color:#00e5ff;">{row['رقم الدفعة']}</b>
                                <br>
                                <span style="font-size: 12px; color: rgba(255,255,255,0.7);">🏭 {row['المخزن']} | 📅 ينتهي: {row['تاريخ الانتهاء']}</span>
                            </div>
                            <div style="text-align: center;">
                                {text}
                                <br>
                                <span style="font-size: 14px; color: #00e5ff;">{row['الكمية المتبقية (كجم)']:,.0f} كجم</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("### 📦 إجمالي الأرصدة حسب الصنف")
            total_stock = get_total_stock_by_material()
            if not total_stock.empty:
                st.dataframe(total_stock, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            st.markdown("### 🏭 الرصيد حسب المخزن")
            stock_wh = get_stock_by_warehouse()
            if not stock_wh.empty:
                st.dataframe(stock_wh, use_container_width=True, hide_index=True)
    
    # ==================== تبويب 1: استلام مواد ====================
    with tab1:
        st.subheader("➕ استلام دفعة مواد خام جديدة")
        
        batches = load_batches()
        if batches.empty:
            next_batch_num = "BATCH-0001"
        else:
            next_batch_num = f"BATCH-{len(batches)+1:04d}"
        
        col1, col2 = st.columns(2)
        
        with col1:
            batch_no = st.text_input("🔢 رقم الدفعة *", value=next_batch_num, key="mat_batch_no")
            material = st.selectbox("🏷️ الصنف *", ["-- اختر --"] + materials_list, key="mat_material")
            warehouse = st.selectbox("🏭 المخزن *", ["-- اختر --"] + warehouses_list, key="mat_warehouse")
        
        with col2:
            arrival_date = st.date_input("📅 تاريخ الوصول *", value=date.today(), key="mat_arrival")
            prod_date = st.date_input("🏭 تاريخ الإنتاج *", value=date.today(), key="mat_prod")
            expiry_date = st.date_input("⏰ تاريخ الانتهاء *", value=date.today() + timedelta(days=180), key="mat_expiry")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            weight_per_bag = st.number_input("⚖️ الوزن/عبوة (كجم) *", min_value=0.0, step=10.0, value=750.0, key="mat_weight")
        with col2:
            bags_count = st.number_input("📦 عدد العبوات *", min_value=0, step=1, value=0, key="mat_bags")
        with col3:
            total_weight = weight_per_bag * bags_count
            st.metric("📊 الكمية الكلية", f"{total_weight:,.0f} كجم")
        
        notes = st.text_area("📝 ملاحظات", placeholder="أي تفاصيل إضافية", key="mat_notes")
        
        st.markdown("---")
        
        submitted = st.button("💾 حفظ الدفعة", use_container_width=True, type="primary", key="save_batch_btn")
        
        if submitted:
            errors = []
            if not batch_no.strip(): errors.append("رقم الدفعة مطلوب")
            if material == "-- اختر --": errors.append("الصنف مطلوب")
            if warehouse == "-- اختر --": errors.append("المخزن مطلوب")
            if weight_per_bag <= 0: errors.append("الوزن لازم يكون أكبر من صفر")
            if bags_count <= 0: errors.append("عدد العبوات لازم يكون أكبر من صفر")
            
            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
            else:
                existing = batches[batches["رقم الدفعة"].astype(str) == batch_no.strip()] if not batches.empty else pd.DataFrame()
                if not existing.empty:
                    st.error(f"🚫 رقم الدفعة ({batch_no}) مستخدم من قبل!")
                else:
                    batch_data = {
                        "رقم الدفعة": batch_no.strip(),
                        "الصنف": material,
                        "المخزن": warehouse,
                        "تاريخ الإنتاج": str(prod_date),
                        "تاريخ الانتهاء": str(expiry_date),
                        "تاريخ الوصول": str(arrival_date),
                        "الوزن/عبوة (كجم)": weight_per_bag,
                        "عدد العبوات": bags_count,
                        "الكمية الكلية (كجم)": total_weight,
                        "الكمية المتبقية (كجم)": total_weight,
                        "ملاحظات": notes.strip()
                    }
                    save_batch(batch_data)
                    st.success(f"✅ تم حفظ الدفعة {batch_no} — {total_weight:,.0f} كجم")
                    st.balloons()
                    
    # ==================== تبويب 2: صرف مواد ====================
    with tab2:
        st.subheader("📤 صرف مواد خام من المخزون")
        
        batches = load_batches()
        
        if batches.empty:
            st.info("📭 مفيش دفعات مسجلة. ابدأ باستلام مواد أولًا")
        else:
            batches_with_rem = get_batches_with_remaining(batches)
            available = batches_with_rem[batches_with_rem["الكمية المتبقية (كجم)"] > 0]
            
            if available.empty:
                st.warning("⚠️ مفيش أرصدة متاحة للصرف")
            else:
                issues_df = load_issues()
                next_issue_no = f"ISSUE-{len(issues_df)+1:04d}"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    issue_no = st.text_input("🔢 رقم الصرف *", value=next_issue_no, key="mat_issue_no")
                    issue_date = st.date_input("📅 تاريخ الصرف *", value=date.today(), key="mat_issue_date")
                
                with col2:
                    batch_options = []
                    for idx, row in available.iterrows():
                        label = f"{row['رقم الدفعة']} | {row['الصنف']} | {row['المخزن']} | متبقي: {row['الكمية المتبقية (كجم)']:,.0f} كجم"
                        batch_options.append(label)
                    
                    selected_batch = st.selectbox("📦 اختار الدفعة *", ["-- اختر --"] + batch_options, key="mat_issue_batch")
                
                selected_batch_row = None
                if selected_batch != "-- اختر --":
                    batch_no_selected = selected_batch.split(" | ")[0].strip()
                    selected_batch_row = available[available["رقم الدفعة"].astype(str) == batch_no_selected].iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📦 الكمية المتاحة", f"{selected_batch_row['الكمية المتبقية (كجم)']:,.0f} كجم")
                    with col2:
                        st.metric("🏭 المخزن", selected_batch_row['المخزن'])
                    with col3:
                        status, days_left, icon = get_expiry_status(selected_batch_row["تاريخ الانتهاء"])
                        st.metric(f"{icon} حالة الصلاحية", status, f"{days_left} يوم" if days_left is not None else "")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    issue_qty = st.number_input("⚖️ الكمية المصروفة (كجم) *", min_value=0.0, step=50.0, value=0.0, key="mat_issue_qty")
                with col2:
                    issued_to = st.text_input("🎯 الجهة/الطلب *", placeholder="مثال: خط إنتاج A", key="mat_issued_to")
                
                issue_notes = st.text_area("📝 ملاحظات", placeholder="أي تفاصيل إضافية", key="mat_issue_notes")
                
                st.markdown("---")
                
                submitted_issue = st.button("💾 حفظ الصرف", use_container_width=True, type="primary", key="save_issue_btn")
                
                if submitted_issue:
                    errors = []
                    if not issue_no.strip(): errors.append("رقم الصرف مطلوب")
                    if selected_batch == "-- اختر --": errors.append("الدفعة مطلوبة")
                    if issue_qty <= 0: errors.append("الكمية لازم تكون أكبر من صفر")
                    if not issued_to.strip(): errors.append("الجهة/الطلب مطلوب")
                    
                    if selected_batch_row is not None and issue_qty > selected_batch_row["الكمية المتبقية (كجم)"]:
                        errors.append(f"⚠️ الكمية المطلوبة ({issue_qty:,.0f}) أكبر من المتاح ({selected_batch_row['الكمية المتبقية (كجم)']:,.0f})")
                    
                    if errors:
                        for err in errors:
                            st.error(f"⚠️ {err}")
                    else:
                        issue_data = {
                            "رقم الصرف": issue_no.strip(),
                            "التاريخ": str(issue_date),
                            "رقم الدفعة": selected_batch_row["رقم الدفعة"],
                            "الصنف": selected_batch_row["الصنف"],
                            "المخزن": selected_batch_row["المخزن"],
                            "الكمية المصروفة (كجم)": issue_qty,
                            "الجهة/الطلب": issued_to.strip(),
                            "ملاحظات": issue_notes.strip()
                        }
                        save_issue(issue_data)
                        st.success(f"✅ تم صرف {issue_qty:,.0f} كجم")
                        st.balloons()
            
            st.markdown("---")
            st.markdown("### 📋 سجل عمليات الصرف")
            
            issues = load_issues()
            
            if issues.empty:
                st.info("📭 مفيش عمليات صرف مسجلة")
            else:
                st.caption("💡 علّم على ☑ في عمود 'اختر' لتعديل أو حذف سند الصرف")
                
                df_issues = issues.copy()
                df_issues["الكمية المصروفة (كجم)"] = pd.to_numeric(df_issues["الكمية المصروفة (كجم)"], errors="coerce")
                df_issues.insert(0, "اختر", False)
                
                display_cols = ["اختر", "رقم الصرف", "التاريخ", "رقم الدفعة", "الصنف", "المخزن", "الكمية المصروفة (كجم)", "الجهة/الطلب", "ملاحظات"]
                df_display = df_issues[display_cols].copy()
                
                for col in df_display.columns:
                    if col not in ["اختر", "الكمية المصروفة (كجم)"]:
                        df_display[col] = df_display[col].astype(str)
                
                edited_issues = st.data_editor(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    height=400,
                    key="issues_editor",
                    column_config={
                        "اختر": st.column_config.CheckboxColumn("اختر", default=False, width="small"),
                        "رقم الصرف": st.column_config.TextColumn("🔢 رقم الصرف", width="small"),
                        "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="small"),
                        "رقم الدفعة": st.column_config.TextColumn("📦 الدفعة", width="small"),
                        "الصنف": st.column_config.TextColumn("🏷️ الصنف", width="medium"),
                        "المخزن": st.column_config.TextColumn("🏭 المخزن", width="small"),
                        "الكمية المصروفة (كجم)": st.column_config.NumberColumn("⚖️ الكمية", format="%.0f", width="small"),
                        "الجهة/الطلب": st.column_config.TextColumn("🎯 الجهة", width="medium"),
                        "ملاحظات": st.column_config.TextColumn("📝 ملاحظات", width="medium"),
                    }
                )
                
                st.markdown("---")
                st.markdown("### 🔧 إجراءات على سندات الصرف")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
                
                with col_btn1:
                    if st.button("✏️ تعديل السند المحدد", use_container_width=True, type="primary", key="edit_issue_btn"):
                        selected = edited_issues[edited_issues["اختر"] == True]
                        if len(selected) == 0:
                            st.warning("⚠️ علّم على سند أولًا")
                        elif len(selected) > 1:
                            st.error("⚠️ اختار سند واحد بس")
                        else:
                            issue_no_sel = str(selected.iloc[0]["رقم الصرف"])
                            st.session_state["edit_issue"] = issue_no_sel
                            st.query_params["edit_issue"] = issue_no_sel
                            st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ حذف السند المحدد", use_container_width=True, key="delete_issue_btn"):
                        selected = edited_issues[edited_issues["اختر"] == True]
                        if len(selected) == 0:
                            st.warning("⚠️ علّم على سند أولًا")
                        elif len(selected) > 1:
                            st.error("⚠️ اختار سند واحد بس")
                        else:
                            issue_no_sel = str(selected.iloc[0]["رقم الصرف"])
                            st.session_state["delete_issue"] = issue_no_sel
                            st.query_params["delete_issue"] = issue_no_sel
                            st.rerun()
                
                with col_btn3:
                    st.markdown(f"**إجمالي المصروف:** {df_issues['الكمية المصروفة (كجم)'].sum():,.0f} كجم من **{len(df_issues)}** سند")

    # ==================== تبويب 3: عرض المخزون ====================
    with tab3:
        st.subheader("📋 عرض المخزون الحالي")
        
        batches = load_batches()
        
        if batches.empty:
            st.info("📭 مفيش دفعات مسجلة")
        else:
            batches_with_rem = get_batches_with_remaining(batches)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                filter_mat = st.selectbox("🏷️ الصنف", ["الكل"] + materials_list, key="stock_filter_mat")
            with col2:
                filter_wh = st.selectbox("🏭 المخزن", ["الكل"] + warehouses_list, key="stock_filter_wh")
            with col3:
                show_zero = st.checkbox("عرض الأصناف اللي رصيدها صفر", value=False, key="stock_show_zero")
            with col4:
                show_expired = st.checkbox("عرض المنتهية فقط", value=False, key="stock_show_expired")
            
            filtered = batches_with_rem.copy()
            
            if not show_zero:
                filtered = filtered[filtered["الكمية المتبقية (كجم)"] > 0]
            
            if filter_mat != "الكل":
                filtered = filtered[filtered["الصنف"] == filter_mat]
            
            if filter_wh != "الكل":
                filtered = filtered[filtered["المخزن"] == filter_wh]
            
            settings = load_materials_settings()
            warning_days = int(settings.get("مدة التنبيه (يوم)", 30))
            critical_days = int(settings.get("مدة التحذير الأقصى (يوم)", 7))
            
            statuses = []
            days_left_list = []
            for idx, row in filtered.iterrows():
                status, days_left, icon = get_expiry_status(row["تاريخ الانتهاء"], warning_days, critical_days)
                statuses.append(f"{icon} {status}")
                days_left_list.append(days_left)
            
            filtered["حالة الصلاحية"] = statuses
            filtered["أيام متبقية"] = days_left_list
            
            if show_expired:
                filtered = filtered[filtered["حالة الصلاحية"].str.contains("منتهي")]
            
            st.markdown(f"**عدد الدفعات: {len(filtered)}**")
            st.caption("💡 علّم على ☑ في عمود 'اختر' لتعديل أو حذف الدفعة")
            
            if filtered.empty:
                st.warning("⚠️ مفيش نتائج مطابقة للفلاتر")
            else:
                df_editor = filtered.copy()
                df_editor.insert(0, "اختر", False)
                
                display_cols = ["اختر", "رقم الدفعة", "الصنف", "المخزن", "تاريخ الانتهاء", "أيام متبقية", "حالة الصلاحية", "الكمية الكلية (كجم)", "الكمية المصروفة (كجم)", "الكمية المتبقية (كجم)", "تاريخ الوصول"]
                df_display = df_editor[display_cols].copy()
                
                for col in df_display.columns:
                    if col not in ["اختر", "الكمية الكلية (كجم)", "الكمية المصروفة (كجم)", "الكمية المتبقية (كجم)", "أيام متبقية"]:
                        df_display[col] = df_display[col].astype(str)
                
                edited_df = st.data_editor(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    height=500,
                    key="stock_editor",
                    column_config={
                        "اختر": st.column_config.CheckboxColumn("اختر", default=False, width="small"),
                        "رقم الدفعة": st.column_config.TextColumn("🔢 رقم الدفعة", width="small"),
                        "الصنف": st.column_config.TextColumn("🏷️ الصنف", width="medium"),
                        "المخزن": st.column_config.TextColumn("🏭 المخزن", width="small"),
                        "تاريخ الانتهاء": st.column_config.TextColumn("⏰ الانتهاء", width="small"),
                        "أيام متبقية": st.column_config.NumberColumn("⏳ أيام", width="small"),
                        "حالة الصلاحية": st.column_config.TextColumn("📊 الحالة", width="small"),
                        "الكمية الكلية (كجم)": st.column_config.NumberColumn("📦 الكلية", format="%.0f", width="small"),
                        "الكمية المصروفة (كجم)": st.column_config.NumberColumn("📤 المصروفة", format="%.0f", width="small"),
                        "الكمية المتبقية (كجم)": st.column_config.NumberColumn("✅ المتبقية", format="%.0f", width="small"),
                        "تاريخ الوصول": st.column_config.TextColumn("📅 الوصول", width="small"),
                    }
                )
                
                st.markdown("---")
                st.markdown("### 🔧 إجراءات على الدفعات المحددة")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
                
                with col_btn1:
                    if st.button("✏️ تعديل المحدد", use_container_width=True, type="primary", key="edit_batch_btn"):
                        selected = edited_df[edited_df["اختر"] == True]
                        if len(selected) == 0:
                            st.warning("⚠️ علّم على دفعة أولًا")
                        elif len(selected) > 1:
                            st.error("⚠️ اختار دفعة واحدة بس")
                        else:
                            batch_no_sel = str(selected.iloc[0]["رقم الدفعة"])
                            st.session_state["edit_batch"] = batch_no_sel
                            st.query_params["edit_batch"] = batch_no_sel
                            st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ حذف المحدد", use_container_width=True, key="delete_batch_btn"):
                        selected = edited_df[edited_df["اختر"] == True]
                        if len(selected) == 0:
                            st.warning("⚠️ علّم على دفعة أولًا")
                        elif len(selected) > 1:
                            st.error("⚠️ اختار دفعة واحدة بس")
                        else:
                            batch_no_sel = str(selected.iloc[0]["رقم الدفعة"])
                            st.session_state["delete_batch"] = batch_no_sel
                            st.query_params["delete_batch"] = batch_no_sel
                            st.rerun()
                
                with col_btn3:
                    st.markdown("💡 **ملاحظة:** لتعديل أو حذف دفعة، علّم على ☑ جنبها واضغط الزر المناسب")
                
                total = filtered["الكمية المتبقية (كجم)"].sum()
                st.markdown("---")
                st.markdown(f"### 💰 إجمالي الرصيد المعروض: **{total:,.0f} كجم**")
                
    # ==================== تبويب 4: التقارير ====================
    with tab4:
        st.subheader("📊 تقارير المواد الخام")
        
        batches = load_batches()
        
        if batches.empty:
            st.info("📭 مفيش بيانات للتقارير")
        else:
            st.markdown("### 📦 الرصيد الحالي لكل صنف")
            total_stock = get_total_stock_by_material()
            if not total_stock.empty:
                st.dataframe(total_stock, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            st.markdown("### 🏭 الرصيد الحالي لكل مخزن")
            stock_wh = get_stock_by_warehouse()
            if not stock_wh.empty:
                st.dataframe(stock_wh, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            st.markdown("### ⚠️ الدفعات اللي قربت تنتهي أو منتهية")
            expiring = get_expiring_batches()
            if expiring.empty:
                st.success("✅ كل الدفعات سارية")
            else:
                st.dataframe(expiring, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            st.markdown("### 📤 حركة الصرف")
            issues = load_issues()
            
            if issues.empty:
                st.info("📭 مفيش عمليات صرف مسجلة")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    filter_issue_mat = st.selectbox("🏷️ الصنف", ["الكل"] + materials_list, key="issue_filter_mat")
                with col2:
                    filter_issue_wh = st.selectbox("🏭 المخزن", ["الكل"] + warehouses_list, key="issue_filter_wh")
                
                filtered_issues = issues.copy()
                if filter_issue_mat != "الكل":
                    filtered_issues = filtered_issues[filtered_issues["الصنف"] == filter_issue_mat]
                if filter_issue_wh != "الكل":
                    filtered_issues = filtered_issues[filtered_issues["المخزن"] == filter_issue_wh]
                
                filtered_issues["الكمية المصروفة (كجم)"] = pd.to_numeric(filtered_issues["الكمية المصروفة (كجم)"], errors="coerce")
                total_issued = filtered_issues["الكمية المصروفة (كجم)"].sum()
                
                st.markdown(f"**عدد عمليات الصرف: {len(filtered_issues)} | إجمالي المصروف: {total_issued:,.0f} كجم**")
                st.dataframe(filtered_issues, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            st.markdown("### 📊 إجمالي المصروف لكل صنف")
            issues = load_issues()
            if not issues.empty:
                issues["الكمية المصروفة (كجم)"] = pd.to_numeric(issues["الكمية المصروفة (كجم)"], errors="coerce")
                by_mat = issues.groupby("الصنف")["الكمية المصروفة (كجم)"].sum().reset_index()
                by_mat.columns = ["الصنف", "إجمالي المصروف (كجم)"]
                by_mat = by_mat.sort_values("إجمالي المصروف (كجم)", ascending=False)
                st.dataframe(by_mat, use_container_width=True, hide_index=True)

    # ==================== تبويب 5: الإعدادات ====================
    with tab5:
        st.subheader("⚙️ إعدادات قسم المواد الخام")
        
        st.markdown("### 🔔 إعدادات التنبيهات")
        
        settings = load_materials_settings()
        
        col1, col2 = st.columns(2)
        with col1:
            new_warning = st.number_input(
                "📅 مدة التنبيه (يوم) — قبل الانتهاء بـ", 
                min_value=1, max_value=365, 
                value=int(settings.get("مدة التنبيه (يوم)", 30)),
                key="settings_warning"
            )
        with col2:
            new_critical = st.number_input(
                "🚨 مدة التحذير العاجل (يوم)", 
                min_value=1, max_value=90, 
                value=int(settings.get("مدة التحذير الأقصى (يوم)", 7)),
                key="settings_critical"
            )
        
        if st.button("💾 حفظ إعدادات التنبيه", key="save_settings_btn"):
            new_settings = {
                "مدة التنبيه (يوم)": new_warning,
                "مدة التحذير الأقصى (يوم)": new_critical,
            }
            save_materials_settings(new_settings)
            st.success(f"✅ تم حفظ الإعدادات — التنبيه: {new_warning} يوم / التحذير العاجل: {new_critical} يوم")
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 🏷️ إدارة الأصناف")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_material = st.text_input("اسم صنف جديد", placeholder="مثال: EPS : NEW-01", key="new_material_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ إضافة صنف", key="add_material_btn"):
                if new_material.strip():
                    if save_material(new_material.strip()):
                        st.success(f"✅ تم إضافة: {new_material}")
                        st.rerun()
                    else:
                        st.warning("⚠️ الصنف موجود بالفعل")
                else:
                    st.error("⚠️ اكتب اسم الصنف")
        
        materials_current = load_materials()
        st.markdown(f"**عدد الأصناف: {len(materials_current)}**")
        
        for i, mat in enumerate(materials_current):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"• {mat}")
            with col2:
                if st.button("🗑️", key=f"del_mat_{i}"):
                    df = pd.read_excel(MATERIALS_FILE)
                    df = df[df["الصنف"] != mat]
                    df.to_excel(MATERIALS_FILE, index=False)
                    st.success(f"تم حذف: {mat}")
                    st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 🏭 إدارة المخازن")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_wh = st.text_input("اسم مخزن جديد", placeholder="مثال: مخزن الجهراء", key="new_wh_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ إضافة مخزن", key="add_wh_btn"):
                if new_wh.strip():
                    if save_warehouse(new_wh.strip()):
                        st.success(f"✅ تم إضافة: {new_wh}")
                        st.rerun()
                    else:
                        st.warning("⚠️ المخزن موجود بالفعل")
                else:
                    st.error("⚠️ اكتب اسم المخزن")
        
        warehouses_current = load_warehouses()
        st.markdown(f"**عدد المخازن: {len(warehouses_current)}**")
        
        for i, wh in enumerate(warehouses_current):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"• {wh}")
            with col2:
                if st.button("🗑️", key=f"del_wh_{i}"):
                    df = pd.read_excel(WAREHOUSES_FILE)
                    df = df[df["المخزن"] != wh]
                    df.to_excel(WAREHOUSES_FILE, index=False)
                    st.success(f"تم حذف: {wh}")
                    st.rerun()
        
        st.markdown("---")
        
        st.markdown("### ℹ️ معلومات")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            batches = load_batches()
            st.metric("📦 إجمالي الدفعات المسجلة", len(batches))
        with col2:
            issues = load_issues()
            st.metric("📤 إجمالي عمليات الصرف", len(issues))
        with col3:
            st.metric("📅 تاريخ اليوم", date.today().strftime("%Y-%m-%d"))

# ==================== النوافذ المنبثقة ====================
# نستخدم query_params بدل session_state — أضمن في Streamlit
edit_batch_param = st.query_params.get("edit_batch")
delete_batch_param = st.query_params.get("delete_batch")

if edit_batch_param:
    edit_batch_dialog_local(edit_batch_param)
elif st.session_state.get("edit_batch"):
    edit_batch_dialog_local(st.session_state["edit_batch"])

if delete_batch_param:
    delete_batch_dialog_local(delete_batch_param)
elif st.session_state.get("delete_batch"):
    delete_batch_dialog_local(st.session_state["delete_batch"])
