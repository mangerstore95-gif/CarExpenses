import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ==================== الملفات ====================
BATCHES_FILE = "batches.xlsx"
ISSUES_FILE = "issues.xlsx"
MATERIALS_FILE = "materials.xlsx"
WAREHOUSES_FILE = "warehouses.xlsx"
MATERIALS_SETTINGS_FILE = "materials_settings.xlsx"

# ==================== دوال التحميل ====================
def load_batches():
    try:
        return pd.read_excel(BATCHES_FILE)
    except:
        return pd.DataFrame()

def load_issues():
    try:
        return pd.read_excel(ISSUES_FILE)
    except:
        return pd.DataFrame()

def load_materials():
    try:
        df = pd.read_excel(MATERIALS_FILE)
        return df["الصنف"].dropna().astype(str).tolist()
    except:
        return []

def load_warehouses():
    try:
        df = pd.read_excel(WAREHOUSES_FILE)
        return df["المخزن"].dropna().astype(str).tolist()
    except:
        return []

def load_materials_settings():
    try:
        df = pd.read_excel(MATERIALS_SETTINGS_FILE)
        return df.iloc[0].to_dict()
    except:
        return {}

# ==================== دوال الحفظ ====================
def save_batches(df):
    df.to_excel(BATCHES_FILE, index=False)

def save_issues(df):
    df.to_excel(ISSUES_FILE, index=False)

def save_materials_list(materials):
    pd.DataFrame({"الصنف": materials}).to_excel(MATERIALS_FILE, index=False)

def save_warehouses_list(warehouses):
    pd.DataFrame({"المخزن": warehouses}).to_excel(WAREHOUSES_FILE, index=False)

def save_settings(settings):
    pd.DataFrame([settings]).to_excel(MATERIALS_SETTINGS_FILE, index=False)

# ==================== دوال الحساب ====================
def get_batches_with_remaining(batches_df):
    """يرجع الدفعات مع الكمية المتبقية محسوبة"""
    if batches_df.empty:
        return batches_df
    
    issues_df = load_issues()
    batches_df = batches_df.copy()
    batches_df["الكمية الكلية (كجم)"] = pd.to_numeric(batches_df["الكمية الكلية (كجم)"], errors="coerce")
    
    if issues_df.empty:
        batches_df["الكمية المصروفة (كجم)"] = 0
    else:
        issues_df["الكمية المصروفة (كجم)"] = pd.to_numeric(issues_df["الكمية المصروفة (كجم)"], errors="coerce")
        issued = issues_df.groupby("رقم الدفعة")["الكمية المصروفة (كجم)"].sum()
        batches_df["الكمية المصروفة (كجم)"] = batches_df["رقم الدفعة"].map(issued).fillna(0)
    
    batches_df["الكمية المتبقية (كجم)"] = batches_df["الكمية الكلية (كجم)"] - batches_df["الكمية المصروفة (كجم)"]
    return batches_df

def get_issued_for_batch(batch_no):
    """يرجع إجمالي الكمية المصروفة لدفعة"""
    issues = load_issues()
    if issues.empty:
        return 0
    issues["الكمية المصروفة (كجم)"] = pd.to_numeric(issues["الكمية المصروفة (كجم)"], errors="coerce")
    total = issues[issues["رقم الدفعة"].astype(str) == str(batch_no)]["الكمية المصروفة (كجم)"].sum()
    return float(total) if pd.notna(total) else 0

# ==================== نافذة تعديل الدفعة ====================
@st.dialog("✏️ تعديل دفعة", width="large")
def edit_batch_dialog(batch_no):
    batches = load_batches()
    match = batches[batches["رقم الدفعة"].astype(str) == str(batch_no)]
    
    if match.empty:
        st.error("⚠️ الدفعة مش موجودة")
        if st.button("إغلاق"):
            st.session_state["edit_batch"] = None
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
        # الصنف
        current_mat = str(row["الصنف"])
        mat_idx = materials_list.index(current_mat) if current_mat in materials_list else 0
        new_mat = st.selectbox("🏷️ الصنف", materials_list, index=mat_idx, key="edit_batch_mat")
        
        # المخزن
        current_wh = str(row["المخزن"])
        wh_idx = warehouses_list.index(current_wh) if current_wh in warehouses_list else 0
        new_wh = st.selectbox("🏭 المخزن", warehouses_list, index=wh_idx, key="edit_batch_wh")
        
        # التواريخ
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
    
    # تحذير لو الكمية الجديدة أقل من المصروفة
    if new_total < issued_qty:
        st.error(f"🚫 الكمية الجديدة ({new_total:,.0f}) أقل من المصروفة ({issued_qty:,.0f})! لازم تكون أكبر أو تساويها.")
    
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 حفظ التعديلات", use_container_width=True, type="primary"):
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
                
                save_batches(full_df)
                st.success(f"✅ تم تحديث الدفعة {batch_no}")
                st.session_state["edit_batch"] = None
                st.rerun()
    
    with col_cancel:
        if st.button("❌ إلغاء", use_container_width=True):
            st.session_state["edit_batch"] = None
            st.rerun()

# ==================== نافذة تأكيد حذف الدفعة ====================
@st.dialog("🗑️ تأكيد الحذف")
def delete_batch_dialog(batch_no):
    batches = load_batches()
    match = batches[batches["رقم الدفعة"].astype(str) == str(batch_no)]
    
    if match.empty:
        st.error("⚠️ الدفعة مش موجودة")
        if st.button("إغلاق"):
            st.session_state["delete_batch"] = None
            st.rerun()
        return
    
    row = match.iloc[0]
    issued_qty = get_issued_for_batch(batch_no)
    
    if issued_qty > 0:
        st.error(f"🚫 **لا يمكن حذف هذه الدفعة!**")
        st.warning(f"فيها **{issued_qty:,.0f} كجم** مصروفة. لازم تحذف سندات الصرف الأول.")
        
        # نعرض سندات الصرف المرتبطة
        issues = load_issues()
        related = issues[issues["رقم الدفعة"].astype(str) == str(batch_no)]
        
        if not related.empty:
            st.markdown("**سندات الصرف المرتبطة:**")
            st.dataframe(related[["رقم الصرف", "التاريخ", "الكمية المصروفة (كجم)", "الجهة/الطلب"]], use_container_width=True, hide_index=True)
        
        if st.button("إغلاق", use_container_width=True):
            st.session_state["delete_batch"] = None
            st.rerun()
    else:
        st.warning(f"⚠️ **هل أنت متأكد من حذف الدفعة** `{batch_no}` **؟**")
        st.markdown(f"**الصنف:** {row['الصنف']}")
        st.markdown(f"**المخزن:** {row['المخزن']}")
        st.markdown(f"**الكمية الكلية:** {row['الكمية الكلية (كجم)']:,.0f} كجم")
        st.markdown("**لا يمكن التراجع عن هذا الإجراء.**")
        
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ نعم، احذف", type="primary", use_container_width=True):
                full_df = load_batches()
                full_df = full_df[full_df["رقم الدفعة"].astype(str) != str(batch_no)]
                save_batches(full_df)
                st.success(f"✅ تم حذف الدفعة {batch_no}")
                st.session_state["delete_batch"] = None
                st.rerun()
        with col_no:
            if st.button("❌ إلغاء", use_container_width=True):
                st.session_state["delete_batch"] = None
                st.rerun()