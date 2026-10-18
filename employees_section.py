import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import os

# ==================== إعدادات الملف والبيانات ====================
DATA_FILE = "employees_data.csv"

def load_records():
    """تحميل البيانات من ملف CSV"""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            expected_cols = ["التاريخ", "اسم الموظف", "الرتبة", "الحدث", "رقم السند"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            return pd.DataFrame(columns=["التاريخ", "اسم الموظف", "الرتبة", "الحدث", "رقم السند", "ملاحظات"])
    return pd.DataFrame(columns=["التاريخ", "اسم الموظف", "الرتبة", "الحدث", "رقم السند", "ملاحظات"])

def save_records(df):
    """حفظ البيانات في ملف CSV"""
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# ==================== تبويب: لوحة التحكم (Dashboard) - نسخة 3D ====================
def render_dashboard_tab():
    st.subheader("📈 لوحة التحكم - تقييم الأداء (عرض 3D)")
    
    df = load_records()
    
    if df.empty:
        st.info("📭 مفيش بيانات مسجلة لحد الآن. استخدم تبويب الإعدادات لإضافة بيانات تجريبية.")
        return
    
    df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    
    with st.container(border=True):
        st.markdown("#### 🔍 فلترة البيانات")
        col1, col2 = st.columns(2)
        with col1:
            min_date = df["التاريخ_dt"].min().date() if not df["التاريخ_dt"].isna().all() else date.today()
            date_from = st.date_input("📅 من تاريخ", value=min_date, key="dash_date_from_3d")
        with col2:
            max_date = df["التاريخ_dt"].max().date() if not df["التاريخ_dt"].isna().all() else date.today()
            date_to = st.date_input("📅 إلى تاريخ", value=max_date, key="dash_date_to_3d")

    filtered = df[
        (df["التاريخ_dt"].dt.date >= date_from) &
        (df["التاريخ_dt"].dt.date <= date_to)
    ].copy()
    
    if filtered.empty:
        st.warning("⚠️ مفيش بيانات في الفترة المحددة")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    total_events = len(filtered)
    total_employees = filtered["اسم الموظف"].nunique()
    total_event_types = filtered["الحدث"].nunique()
    days_diff = (date_to - date_from).days
    
    glass_style = """
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    color: white;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    """
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="{glass_style}">
            <div style="font-size: 14px; color: #a0a0a0;">📋 إجمالي الأحداث</div>
            <div style="font-size: 36px; font-weight: bold; background: linear-gradient(90deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total_events}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="{glass_style}">
            <div style="font-size: 14px; color: #a0a0a0;">👥 عدد الموظفين</div>
            <div style="font-size: 36px; font-weight: bold; background: linear-gradient(90deg, #f093fb, #f5576c); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total_employees}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="{glass_style}">
            <div style="font-size: 14px; color: #a0a0a0;">📋 أنواع الأحداث</div>
            <div style="font-size: 36px; font-weight: bold; background: linear-gradient(90deg, #43e97b, #38f9d7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total_event_types}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="{glass_style}">
            <div style="font-size: 14px; color: #a0a0a0;">📅 مدة الفترة</div>
            <div style="font-size: 36px; font-weight: bold; background: linear-gradient(90deg, #fa709a, #fee140); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{days_diff}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### 🏆 تقييم الموظفين (الأفضل والأسوأ)")
        
        emp_stats = filtered.groupby("اسم الموظف").agg({
            "رقم السند": "count",
            "الرتبة": "first"
        }).reset_index()
        emp_stats.columns = ["الاسم", "عدد الأحداث", "الرتبة"]
        
        emp_stats_sorted = emp_stats.sort_values("عدد الأحداث", ascending=True)
        
        if not emp_stats_sorted.empty:
            best_emp = emp_stats_sorted.iloc[0]
            worst_emp = emp_stats_sorted.iloc[-1]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style="background: rgba(17, 153, 142, 0.2); border: 1px solid #11998e; padding: 20px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 0 20px rgba(17, 153, 142, 0.3);">
                    <div style="font-size: 40px;">🏅</div>
                    <div style="font-size: 16px; color: #38ef7d; margin-top: 5px;">⭐ أفضل موظف</div>
                    <div style="font-size: 24px; font-weight: bold; margin: 10px 0;">{best_emp['الاسم']}</div>
                    <div style="font-size: 14px; color: #a0a0a0;">{best_emp['الرتبة']}</div>
                    <div style="font-size: 18px; font-weight: bold; margin-top: 10px; background: #11998e; display: inline-block; padding: 5px 15px; border-radius: 20px;">
                        {best_emp['عدد الأحداث']} أحداث
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"""
                <div style="background: rgba(203, 45, 62, 0.2); border: 1px solid #cb2d3e; padding: 20px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 0 20px rgba(203, 45, 62, 0.3);">
                    <div style="font-size: 40px;">⚠️</div>
                    <div style="font-size: 16px; color: #ef473a; margin-top: 5px;">🚨 يحتاج متابعة</div>
                    <div style="font-size: 24px; font-weight: bold; margin: 10px 0;">{worst_emp['الاسم']}</div>
                    <div style="font-size: 14px; color: #a0a0a0;">{worst_emp['الرتبة']}</div>
                    <div style="font-size: 18px; font-weight: bold; margin-top: 10px; background: #cb2d3e; display: inline-block; padding: 5px 15px; border-radius: 20px;">
                        {worst_emp['عدد الأحداث']} أحداث
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        with st.container(border=True):
            st.markdown("### 📊 أنواع الأحداث (3D)")
            
            event_dist = filtered["الحدث"].value_counts().reset_index()
            event_dist.columns = ["الحدث", "العدد"]
            
            if not event_dist.empty:
                fig_event = go.Figure(data=[
                    go.Bar(
                        x=event_dist["الحدث"],
                        y=event_dist["العدد"],
                        z=[1] * len(event_dist),
                        marker=dict(
                            color=event_dist["العدد"],
                            colorscale=[[0, '#00f2fe'], [1, '#4facfe']],
                            showscale=False,
                        ),
                        text=event_dist["العدد"],
                        textposition='auto',
                    )
                ])
                fig_event.update_layout(
                    scene=dict(
                        xaxis_title="الحدث",
                        yaxis_title="العدد",
                        zaxis_title="",
                        xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)"),
                        yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)"),
                        zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)"),
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_event, use_container_width=True)

    with col_chart2:
        with st.container(border=True):
            st.markdown("### 📈 تطور الأحداث شهرياً (3D)")
            
            monthly = filtered.copy()
            monthly["الشهر"] = monthly["التاريخ_dt"].dt.to_period("M").astype(str)
            monthly_counts = monthly.groupby("الشهر").size().reset_index(name="عدد الأحداث")
            monthly_counts = monthly_counts.sort_values("الشهر")
            
            if not monthly_counts.empty:
                x_vals = list(range(len(monthly_counts)))
                y_vals = [1] * len(monthly_counts)
                z_vals = monthly_counts["عدد الأحداث"].tolist()
                
                fig_line = go.Figure(data=[go.Scatter3d(
                    x=x_vals,
                    y=y_vals,
                    z=z_vals,
                    mode='lines+markers',
                    line=dict(color='#ff4ecd', width=8),
                    marker=dict(size=8, color='#00e5ff', line=dict(color='white', width=1)),
                )])
                
                fig_line.update_layout(
                    scene=dict(
                        xaxis=dict(
                            tickvals=x_vals,
                            ticktext=monthly_counts["الشهر"].tolist(),
                            title="الشهر",
                            backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)"
                        ),
                        yaxis=dict(
                            title="",
                            showticklabels=False,
                            backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)"
                        ),
                        zaxis=dict(
                            title="عدد الأحداث",
                            backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.1)"
                        ),
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_line, use_container_width=True)


# ==================== تبويب: جدول الترتيب والتحذيرات ====================
def render_ranking_tab():
    st.subheader("🏆 جدول الترتيب والتحذيرات")
    
    df = load_records()
    
    if df.empty:
        st.info("📭 مفيش بيانات مسجلة لحد الآن.")
        return
    
    df["التاريخ_dt"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    
    with st.container(border=True):
        st.markdown("#### 🔍 فلترة الفترة")
        col1, col2 = st.columns(2)
        with col1:
            min_date = df["التاريخ_dt"].min().date() if not df["التاريخ_dt"].isna().all() else date.today()
            date_from = st.date_input("📅 من تاريخ", value=min_date, key="rank_date_from")
        with col2:
            max_date = df["التاريخ_dt"].max().date() if not df["التاريخ_dt"].isna().all() else date.today()
            date_to = st.date_input("📅 إلى تاريخ", value=max_date, key="rank_date_to")
    
    filtered = df[
        (df["التاريخ_dt"].dt.date >= date_from) &
        (df["التاريخ_dt"].dt.date <= date_to)
    ].copy()
    
    if filtered.empty:
        st.warning("⚠️ مفيش بيانات في الفترة المحددة")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### 📋 ترتيب الموظفين حسب عدد الأحداث")
        
        ranking = filtered.groupby("اسم الموظف").agg({
            "رقم السند": "count",
            "الرتبة": "first"
        }).reset_index()
        ranking.columns = ["الاسم", "عدد الأحداث", "الرتبة"]
        ranking = ranking.sort_values("عدد الأحداث", ascending=True).reset_index(drop=True)
        ranking.index = ranking.index + 1
        ranking.index.name = "الترتيب"
        
        st.dataframe(ranking, use_container_width=True, height=min(500, 50 + len(ranking) * 38))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        fig_rank = go.Figure(go.Bar(
            x=ranking["عدد الأحداث"],
            y=ranking["الاسم"],
            orientation='h',
            marker=dict(
                color=ranking["عدد الأحداث"],
                colorscale=[[0, '#38ef7d'], [0.5, '#f093fb'], [1, '#ef473a']],
                showscale=False,
            ),
            text=ranking["عدد الأحداث"],
            textposition='outside',
            textfont=dict(size=13, color='white'),
        ))
        fig_rank.update_layout(
            height=max(350, len(ranking) * 45),
            xaxis_title="عدد الأحداث",
            yaxis_title="",
            plot_bgcolor='rgba(10,10,25,0.6)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=13),
            margin=dict(l=40, r=80, t=20, b=40),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_rank, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### 🚨 التحذيرات (الموظفون اللي يحتاجون متابعة)")
        
        threshold = ranking["عدد الأحداث"].mean() + ranking["عدد الأحداث"].std()
        if pd.isna(threshold):
            threshold = ranking["عدد الأحداث"].mean()
        
        warned = ranking[ranking["عدد الأحداث"] >= threshold].sort_values("عدد الأحداث", ascending=False)
        
        if warned.empty:
            st.success("✅ مفيش موظفين تجاوزوا حد التحذير في الفترة دي. كل حاجة تمام!")
        else:
            st.markdown(f"<div style='color:#ff6b6b; font-size:14px; margin-bottom:10px;'>⚠️ حد التحذير: {threshold:.1f} حدث</div>", unsafe_allow_html=True)
            
            for _, row in warned.iterrows():
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(203,45,62,0.85) 0%, rgba(239,71,58,0.85) 100%); padding: 15px 20px; border-radius: 12px; color: white; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(239,71,58,0.3);">
                    <div>
                        <div style="font-size: 18px; font-weight: bold;">⚠️ {row['الاسم']}</div>
                        <div style="font-size: 13px; opacity: 0.9;">{row['الرتبة']}</div>
                    </div>
                    <div style="font-size: 22px; font-weight: bold; background: rgba(0,0,0,0.25); padding: 8px 18px; border-radius: 20px;">
                        {row['عدد الأحداث']} حدث
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### 📝 الإجراءات المقترحة")
        
        if warned.empty:
            st.info("مفيش إجراءات مطلوبة حالياً.")
        else:
            for _, row in warned.iterrows():
                count = row['عدد الأحداث']
                if count >= threshold * 1.5:
                    action = "🚫 إنذار رسمي + خطة تحسين أداء عاجلة"
                elif count >= threshold * 1.2:
                    action = "⚠️ جلسة متابعة مع المدير المباشر"
                else:
                    action = "📌 متابعة دورية وتنبيه شفهي"
                
                st.markdown(f"""
                <div style="background: rgba(30,30,50,0.8); border-right: 4px solid #f5576c; padding: 12px 18px; border-radius: 10px; margin-bottom: 8px; color: white;">
                    <b>{row['الاسم']}</b> ({row['الرتبة']}) — <span style="color:#ffd93d;">{count} حدث</span>
                    <div style="font-size: 13px; opacity: 0.85; margin-top: 4px;">{action}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### 🕐 آخر 10 أحداث مسجلة")
        
        recent = filtered.sort_values("التاريخ_dt", ascending=False).head(10).copy()
        recent["التاريخ"] = recent["التاريخ_dt"].dt.strftime("%Y-%m-%d")
        
        display_cols = ["التاريخ", "اسم الموظف", "الرتبة", "الحدث", "رقم السند"]
        if "ملاحظات" in recent.columns:
            display_cols.append("ملاحظات")
        
        st.dataframe(recent[display_cols].reset_index(drop=True), use_container_width=True, height=min(450, 50 + len(recent) * 38))


# ==================== تبويب: الإعدادات وإضافة البيانات ====================
def render_settings_tab():
    st.subheader("⚙️ الإعدادات وإضافة البيانات")
    
    tab1, tab2, tab3 = st.tabs(["➕ إضافة حدث جديد", "📥 رفع ملف بيانات", "🧪 بيانات تجريبية"])
    
    with tab1:
        with st.form("add_event_form"):
            st.markdown("#### سجل حدث جديد")
            col1, col2 = st.columns(2)
            with col1:
                emp_name = st.text_input("اسم الموظف")
                rank = st.text_input("الرتبة")
                event_date = st.date_input("التاريخ")
            with col2:
                event_type = st.selectbox("الحدث", ["خروجية", "مرضية", "غياب", "تأخير", "جزاء", "مكافأة", "أخرى"])
                sanad_no = st.text_input("رقم السند")
                notes = st.text_area("ملاحظات (اختياري)")
                
            submitted = st.form_submit_button("حفظ الحدث")
            
            if submitted:
                if emp_name and event_type:
                    df = load_records()
                    new_row = pd.DataFrame([{
                        "التاريخ": event_date.strftime("%Y-%m-%d"),
                        "اسم الموظف": emp_name,
                        "الرتبة": rank,
                        "الحدث": event_type,
                        "رقم السند": sanad_no,
                        "ملاحظات": notes
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_records(df)
                    st.success("✅ تم حفظ الحدث بنجاح!")
                else:
                    st.error("⚠️ يرجى إدخال اسم الموظف ونوع الحدث على الأقل.")
                    
    with tab2:
        st.markdown("#### رفع ملف CSV")
        uploaded_file = st.file_uploader("اختر ملف CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                new_df = pd.read_csv(uploaded_file)
                save_records(new_df)
                st.success("✅ تم رفع البيانات بنجاح!")
            except Exception as e:
                st.error(f"⚠️ حدث خطأ: {e}")
                
    with tab3:
        st.markdown("#### إضافة بيانات تجريبية")
        st.info("هذا الخيار سيقوم بإنشاء بيانات وهمية لتجربة لوحة التحكم.")
        if st.button("توليد بيانات تجريبية"):
            import random
            from datetime import timedelta
            
            names = ["أحمد علي", "محمد حسن", "خالد إبراهيم", "سعيد محمود", "يوسف كمال", "عمر فاروق"]
            ranks = ["فني", "عامل", "مشرف", "مدير"]
            events = ["خروجية", "مرضية", "غياب", "تأخير", "جزاء"]
            
            data = []
            for _ in range(50):
                d = date.today() - timedelta(days=random.randint(0, 90))
                data.append({
                    "التاريخ": d.strftime("%Y-%m-%d"),
                    "اسم الموظف": random.choice(names),
                    "الرتبة": random.choice(ranks),
                    "الحدث": random.choice(events),
                    "رقم السند": f"SND-{random.randint(1000, 9999)}",
                    "ملاحظات": ""
                })
            df = pd.DataFrame(data)
            save_records(df)
            st.success("✅ تم توليد 50 حدث تجريبي بنجاح! اذهب للوحة التحكم لرؤيتها.")


# ==================== الدوال الأساسية اللي app.py بيدور عليها ====================
def render_employees_section():
    """الدالة اللي app.py بينادي عليها"""
    st.title("📊 نظام تقييم أداء الموظفين")
    st.markdown("---")
    
    tab_dash, tab_rank, tab_settings = st.tabs(["📈 لوحة التحكم", "🏆 الترتيب والتحذيرات", "⚙️ الإعدادات"])
    
    with tab_dash:
        render_dashboard_tab()
    with tab_rank:
        render_ranking_tab()
    with tab_settings:
        render_settings_tab()

def main():
    """دالة احتياطية لو الملف اتشغل لوحده"""
    render_employees_section()

if __name__ == "__main__":
    main()
