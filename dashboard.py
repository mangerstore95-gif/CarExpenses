import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go

def render_dashboard(df, vehicles_df, drivers_list):
    if df.empty:
        st.info("📭 مفيش بيانات لعرضها في لوحة المعلومات")
        return
    
    df = df.copy()
    df["المبلغ (د.ك)"] = pd.to_numeric(df["المبلغ (د.ك)"], errors="coerce")
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    
    # ==================== فلتر الفترة ====================
    st.markdown("### 📅 فلتر الفترة الزمنية")
    
    col1, col2 = st.columns(2)
    with col1:
        min_date = df["التاريخ"].min().date() if not df["التاريخ"].isna().all() else date.today()
        date_from = st.date_input("من تاريخ", value=min_date, key="dash_date_from")
    with col2:
        max_date = df["التاريخ"].max().date() if not df["التاريخ"].isna().all() else date.today()
        date_to = st.date_input("إلى تاريخ", value=max_date, key="dash_date_to")
    
    filtered = df[
        (df["التاريخ"].dt.date >= date_from) & 
        (df["التاريخ"].dt.date <= date_to)
    ].copy()
    
    if filtered.empty:
        st.warning("⚠️ مفيش بيانات في الفترة المحددة")
        return
    
    st.markdown("---")
    
    total_amount = filtered["المبلغ (د.ك)"].sum()
    total_invoices = len(filtered)
    total_cars = filtered["رقم السيارة"].nunique()
    total_drivers = filtered["اسم السائق"].nunique()
    
    # ==================== KPI Cards الجديدة ====================
    # بطاقات دائرية بحلقات مضيئة
    
    col1, col2, col3, col4 = st.columns(4)
    
    def kpi_card(icon, title, value, unit, color, subtitle=""):
        return f"""
        <div style="
            background: linear-gradient(145deg, rgba(30,30,50,0.9), rgba(15,15,30,0.9));
            border: 1px solid {color}40;
            border-radius: 20px;
            padding: 25px 15px;
            text-align: center;
            position: relative;
            box-shadow: 0 0 30px {color}30, inset 0 0 20px {color}10;
            transition: all 0.3s ease;
            height: 100%;
        ">
            <div style="
                width: 70px;
                height: 70px;
                margin: 0 auto 15px;
                border-radius: 50%;
                background: radial-gradient(circle, {color}30, transparent 70%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                border: 2px solid {color};
                box-shadow: 0 0 20px {color}80, inset 0 0 15px {color}40;
            ">{icon}</div>
            <div style="font-size: 14px; color: rgba(255,255,255,0.7); margin-bottom: 10px;">{title}</div>
            <div style="
                font-size: 28px;
                font-weight: 900;
                color: {color};
                text-shadow: 0 0 20px {color};
                margin-bottom: 5px;
            ">{value}</div>
            <div style="font-size: 13px; color: rgba(255,255,255,0.5);">{unit}</div>
            {f'<div style="font-size: 11px; color: {color}; margin-top: 8px;">{subtitle}</div>' if subtitle else ''}
        </div>
        """
    
    with col1:
        st.markdown(kpi_card("💰", "إجمالي المصاريف", f"{total_amount:,.0f}", "دينار كويتي", "#00e5ff"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(kpi_card("🧾", "عدد الفواتير", f"{total_invoices}", "فاتورة", "#ff4ecd"), unsafe_allow_html=True)
    
    with col3:
        st.markdown(kpi_card("🚗", "عدد السيارات", f"{total_cars}", "سيارة", "#39ff14"), unsafe_allow_html=True)
    
    with col4:
        st.markdown(kpi_card("👤", "عدد السائقين", f"{total_drivers}", "سائق", "#ffb400"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==================== 3 أزرار المعلومات ====================
    col1, col2, col3 = st.columns(3)
    
    avg_invoice = total_amount / total_invoices if total_invoices > 0 else 0
    highest = filtered.loc[filtered["المبلغ (د.ك)"].idxmax()]
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(0, 229, 255, 0.1); border-right: 4px solid #00e5ff; 
                    padding: 15px; border-radius: 10px;">
            <div style="font-size: 13px; color: rgba(255,255,255,0.7);">📊 متوسط الفاتورة</div>
            <div style="font-size: 22px; font-weight: bold; color: #00e5ff;">{avg_invoice:,.3f} د.ك</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: rgba(255, 78, 205, 0.1); border-right: 4px solid #ff4ecd; 
                    padding: 15px; border-radius: 10px;">
            <div style="font-size: 13px; color: rgba(255,255,255,0.7);">🔝 أعلى فاتورة</div>
            <div style="font-size: 22px; font-weight: bold; color: #ff4ecd;">{highest['المبلغ (د.ك)']:,.3f} د.ك</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5);">سيارة {highest['رقم السيارة']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        lowest = filtered.loc[filtered["المبلغ (د.ك)"].idxmin()]
        st.markdown(f"""
        <div style="background: rgba(57, 255, 20, 0.1); border-right: 4px solid #39ff14; 
                    padding: 15px; border-radius: 10px;">
            <div style="font-size: 13px; color: rgba(255,255,255,0.7);">🔻 أقل فاتورة</div>
            <div style="font-size: 22px; font-weight: bold; color: #39ff14;">{lowest['المبلغ (د.ك)']:,.3f} د.ك</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5);">سيارة {lowest['رقم السيارة']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== الرسم الخطي ====================
    st.markdown("### 📈 اتجاه المصاريف الشهرية")
    
    monthly = filtered.copy()
    monthly["الشهر"] = monthly["التاريخ"].dt.to_period("M").astype(str)
    monthly_data = monthly.groupby("الشهر")["المبلغ (د.ك)"].sum().reset_index()
    monthly_data = monthly_data.sort_values("الشهر")
    
    if not monthly_data.empty:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=monthly_data["الشهر"],
            y=monthly_data["المبلغ (د.ك)"],
            mode='lines+markers',
            line=dict(color='#00e5ff', width=4, shape='spline'),
            marker=dict(
                size=16, 
                color='#ff4ecd',
                line=dict(color='#00e5ff', width=3),
                symbol='circle'
            ),
            fill='tozeroy',
            fillcolor='rgba(0, 229, 255, 0.15)',
            name='المصاريف',
            hovertemplate='<b>%{x}</b><br>المبلغ: %{y:,.3f} د.ك<extra></extra>'
        ))
        fig_line.update_layout(
            height=400,
            xaxis_title="الشهر",
            yaxis_title="المبلغ (د.ك)",
            hovermode='x unified',
            plot_bgcolor='rgba(10,10,25,0.6)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=13, family='Arial'),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)'),
            yaxis=dict(gridcolor='rgba(0,229,255,0.1)', linecolor='rgba(0,229,255,0.3)')
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== أعلى 5 سيارات وسائقين ====================
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚙 أعلى 5 سيارات")
        top_cars = filtered.groupby("رقم السيارة")["المبلغ (د.ك)"].sum().sort_values(ascending=False).head(5).reset_index()
        
        if not top_cars.empty:
            top_cars["رقم السيارة"] = top_cars["رقم السيارة"].astype(str)
            top_cars = top_cars.sort_values("المبلغ (د.ك)", ascending=True)
            max_val = top_cars["المبلغ (د.ك)"].max()
            
            fig_cars = go.Figure(go.Bar(
                x=top_cars["المبلغ (د.ك)"],
                y=top_cars["رقم السيارة"],
                orientation='h',
                marker=dict(
                    color=top_cars["المبلغ (د.ك)"],
                    colorscale=[
                        [0, '#ff1744'],
                        [0.5, '#ff4ecd'],
                        [1, '#00e5ff']
                    ],
                    showscale=False,
                    line=dict(color='rgba(0,229,255,0.5)', width=2)
                ),
                text=top_cars["المبلغ (د.ك)"].apply(lambda x: f"  {x:,.0f}  "),
                textposition='inside',
                insidetextanchor='end',
                textfont=dict(size=15, color='white', family='Arial Black'),
                hovertemplate='<b>سيارة %{y}</b><br>المبلغ: %{x:,.3f} د.ك<extra></extra>'
            ))
            fig_cars.update_layout(
                height=400,
                xaxis_title="المبلغ (د.ك)",
                yaxis_title="",
                plot_bgcolor='rgba(10,10,25,0.6)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=13),
                margin=dict(l=20, r=40, t=20, b=40),
                xaxis=dict(
                    gridcolor='rgba(0,229,255,0.1)',
                    range=[0, max_val * 1.05],
                    linecolor='rgba(0,229,255,0.3)'
                ),
                yaxis=dict(gridcolor='rgba(0,229,255,0.05)'),
                bargap=0.3
            )
            st.plotly_chart(fig_cars, use_container_width=True)
    
    with col2:
        st.markdown("### 👤 أعلى 5 سائقين")
        top_drivers = filtered.groupby("اسم السائق")["المبلغ (د.ك)"].sum().sort_values(ascending=False).head(5).reset_index()
        
        if not top_drivers.empty:
            top_drivers = top_drivers.sort_values("المبلغ (د.ك)", ascending=True)
            max_val = top_drivers["المبلغ (د.ك)"].max()
            
            fig_drivers = go.Figure(go.Bar(
                x=top_drivers["المبلغ (د.ك)"],
                y=top_drivers["اسم السائق"],
                orientation='h',
                marker=dict(
                    color=top_drivers["المبلغ (د.ك)"],
                    colorscale=[
                        [0, '#39ff14'],
                        [0.5, '#ffb400'],
                        [1, '#ff1744']
                    ],
                    showscale=False,
                    line=dict(color='rgba(57,255,20,0.5)', width=2)
                ),
                text=top_drivers["المبلغ (د.ك)"].apply(lambda x: f"  {x:,.0f}  "),
                textposition='inside',
                insidetextanchor='end',
                textfont=dict(size=15, color='white', family='Arial Black'),
                hovertemplate='<b>%{y}</b><br>المبلغ: %{x:,.3f} د.ك<extra></extra>'
            ))
            fig_drivers.update_layout(
                height=400,
                xaxis_title="المبلغ (د.ك)",
                yaxis_title="",
                plot_bgcolor='rgba(10,10,25,0.6)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=13),
                margin=dict(l=20, r=40, t=20, b=40),
                xaxis=dict(
                    gridcolor='rgba(57,255,20,0.1)',
                    range=[0, max_val * 1.05],
                    linecolor='rgba(57,255,20,0.3)'
                ),
                yaxis=dict(gridcolor='rgba(57,255,20,0.05)'),
                bargap=0.3
            )
            st.plotly_chart(fig_drivers, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== توزيع حسب النوع ====================
    st.markdown("### 🚛 توزيع المصاريف حسب نوع المركبة")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        by_type = filtered.groupby("نوع المركبة")["المبلغ (د.ك)"].sum().reset_index()
        
        if not by_type.empty:
            fig_pie = go.Figure(go.Pie(
                labels=by_type["نوع المركبة"],
                values=by_type["المبلغ (د.ك)"],
                hole=0.6,
                marker=dict(
                    colors=['#00e5ff', '#ff4ecd', '#39ff14', '#ffb400', '#ff1744', '#b388ff', '#18ffff'],
                    line=dict(color='rgba(255,255,255,0.3)', width=3)
                ),
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=13, color='white'),
                hovertemplate='<b>%{label}</b><br>المبلغ: %{value:,.3f} د.ك<br>النسبة: %{percent}<extra></extra>',
                pull=[0.08, 0, 0, 0, 0, 0, 0]
            ))
            fig_pie.update_layout(
                height=450,
                showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=13),
                margin=dict(l=70, r=70, t=70, b=70),
                legend=dict(
                    font=dict(color='white', size=12),
                    bgcolor='rgba(10,10,25,0.6)',
                    bordercolor='rgba(0,229,255,0.3)',
                    borderwidth=1
                )
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("#### 💡 تفاصيل حسب النوع")
        type_summary = filtered.groupby("نوع المركبة").agg({
            "المبلغ (د.ك)": ["sum", "count", "mean"]
        }).round(3)
        type_summary.columns = ["الإجمالي", "عدد الفواتير", "المتوسط"]
        type_summary = type_summary.sort_values("الإجمالي", ascending=False)
        st.dataframe(type_summary, use_container_width=True)
    
    st.markdown("---")
    
    # ==================== مؤشرات ذكية ====================
    st.markdown("### 🧠 مؤشرات ذكية وتحذيرات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚨 سيارات صرفت أعلى من المتوسط")
        car_totals = filtered.groupby("رقم السيارة")["المبلغ (د.ك)"].sum()
        avg_car = car_totals.mean()
        high_cars = car_totals[car_totals > avg_car * 1.5].sort_values(ascending=False)
        
        if not high_cars.empty:
            for car, amount in high_cars.head(5).items():
                pct = ((amount / avg_car) - 1) * 100
                st.markdown(f"""
                <div style="background: rgba(255, 23, 68, 0.15); border-right: 4px solid #ff1744;
                            padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    🚙 سيارة <b style="color:#00e5ff;">{car}</b> — 
                    صرفت <b style="color:#ff1744;">{amount:,.3f}</b> د.ك 
                    (أعلى بـ <b>{pct:.0f}%</b>)
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ كل السيارات في المعدل الطبيعي")
    
    with col2:
        st.markdown("#### ⚠️ سائقين بمعدل صرف عالي")
        driver_totals = filtered.groupby("اسم السائق")["المبلغ (د.ك)"].sum()
        avg_driver = driver_totals.mean()
        high_drivers = driver_totals[driver_totals > avg_driver * 1.5].sort_values(ascending=False)
        
        if not high_drivers.empty:
            for driver, amount in high_drivers.head(5).items():
                pct = ((amount / avg_driver) - 1) * 100
                st.markdown(f"""
                <div style="background: rgba(255, 180, 0, 0.15); border-right: 4px solid #ffb400;
                            padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    👤 <b style="color:#00e5ff;">{driver}</b> — 
                    صرف <b style="color:#ffb400;">{amount:,.3f}</b> د.ك 
                    (أعلى بـ <b>{pct:.0f}%</b>)
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ كل السائقين في المعدل الطبيعي")
    
    st.markdown("---")
    
    # ==================== أبرز الأرقام ====================
    st.markdown("### 📊 أبرز الأرقام")
    
    col1, col2, col3 = st.columns(3)
    
    monthly_series = monthly.groupby("الشهر")["المبلغ (د.ك)"].sum()
    if not monthly_series.empty:
        peak_month = monthly_series.idxmax()
        peak_amount = monthly_series.max()
        avg_month = monthly_series.mean()
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(0,229,255,0.05));
                        border: 1px solid rgba(0,229,255,0.4); border-radius: 15px;
                        padding: 20px; text-align: center; box-shadow: 0 0 30px rgba(0,229,255,0.2);">
                <div style="font-size: 40px;">📈</div>
                <div style="font-size: 14px; color: rgba(255,255,255,0.7); margin: 10px 0;">أعلى شهر صرفًا</div>
                <div style="font-size: 20px; font-weight: bold; color: #00e5ff; text-shadow: 0 0 10px #00e5ff;">{peak_month}</div>
                <div style="font-size: 24px; font-weight: 900; color: white; margin: 10px 0;">{peak_amount:,.3f}</div>
                <div style="font-size: 12px; color: rgba(255,255,255,0.5);">متوسط الشهور: {avg_month:,.3f} د.ك</div>
            </div>
            """, unsafe_allow_html=True)
    
    type_series = filtered.groupby("نوع المركبة")["المبلغ (د.ك)"].sum()
    if not type_series.empty:
        top_type = type_series.idxmax()
        top_type_amount = type_series.max()
        top_type_pct = (top_type_amount / filtered["المبلغ (د.ك)"].sum()) * 100
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(255,78,205,0.15), rgba(255,78,205,0.05));
                        border: 1px solid rgba(255,78,205,0.4); border-radius: 15px;
                        padding: 20px; text-align: center; box-shadow: 0 0 30px rgba(255,78,205,0.2);">
                <div style="font-size: 40px;">🚛</div>
                <div style="font-size: 14px; color: rgba(255,255,255,0.7); margin: 10px 0;">أعلى نوع صرفًا</div>
                <div style="font-size: 20px; font-weight: bold; color: #ff4ecd; text-shadow: 0 0 10px #ff4ecd;">{top_type}</div>
                <div style="font-size: 24px; font-weight: 900; color: white; margin: 10px 0;">{top_type_amount:,.3f}</div>
                <div style="font-size: 12px; color: rgba(255,255,255,0.5);">{top_type_pct:.1f}% من الإجمالي</div>
            </div>
            """, unsafe_allow_html=True)
    
    driver_cars = filtered.groupby("اسم السائق")["رقم السيارة"].nunique()
    if not driver_cars.empty:
        top_driver_div = driver_cars.idxmax()
        top_driver_count = driver_cars.max()
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(57,255,20,0.15), rgba(57,255,20,0.05));
                        border: 1px solid rgba(57,255,20,0.4); border-radius: 15px;
                        padding: 20px; text-align: center; box-shadow: 0 0 30px rgba(57,255,20,0.2);">
                <div style="font-size: 40px;">🔄</div>
                <div style="font-size: 14px; color: rgba(255,255,255,0.7); margin: 10px 0;">أكثر سائق تنوعًا</div>
                <div style="font-size: 20px; font-weight: bold; color: #39ff14; text-shadow: 0 0 10px #39ff14;">{top_driver_div}</div>
                <div style="font-size: 24px; font-weight: 900; color: white; margin: 10px 0;">{top_driver_count} سيارة</div>
                <div style="font-size: 12px; color: rgba(255,255,255,0.5);">مختلفة</div>
            </div>
            """, unsafe_allow_html=True)