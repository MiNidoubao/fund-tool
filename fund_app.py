import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="基金定投分析", layout="wide")
st.title("📈 基金分析工具 ")

# 输入基金代码
symbol = st.text_input("基金代码", value="012460")

if st.button("开始分析"):
    with st.spinner("正在获取数据..."):
        # 获取数据
        df = ak.fund_open_fund_info_em(symbol=symbol)
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        df.set_index('净值日期', inplace=True)

        # 计算均线
        df['MA20'] = df['单位净值'].rolling(20).mean()
        df['MA60'] = df['单位净值'].rolling(60).mean()

        last_price = df['单位净值'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma60 = df['MA60'].iloc[-1]

        # 计算偏离60日均线幅度
        ma60_deviation = (last_price - ma60) / ma60 * 100

        # ======================
        # 新增：计算最大回撤
        # ======================
        df['累计新高'] = df['单位净值'].cummax()
        df['回撤'] = (df['单位净值'] - df['累计新高']) / df['累计新高'] * 100
        max_drawdown = df['回撤'].min()

        # 定投回测
        monthly_invest = 1000
        df['年月'] = df.index.to_period('M')
        monthly_df = df.groupby('年月').first()
        monthly_df['买入份额'] = monthly_invest / monthly_df['单位净值']
        total_invest = len(monthly_df) * monthly_invest
        total_share = monthly_df['买入份额'].sum()
        current_value = total_share * last_price
        profit = current_value - total_invest
        profit_rate = profit / total_invest * 100

        # 收益率区间判断
        if profit_rate > 5:
            st.warning("⚠️ 定投收益率偏高，可考虑暂停或减仓")
        elif profit_rate < -5:
            st.info("💡 定投收益率偏低，可考虑正常定投或小额加仓")
        else:
            st.success("✅ 定投收益率处于正常区间，按计划执行即可")

        # 趋势判断
        if last_price > ma20 > ma60:
            signal = "多头排列 → 上升趋势，可正常定投"
        elif last_price < ma20 < ma60:
            signal = "空头排列 → 下跌趋势，谨慎定投"
        else:
            signal = "震荡行情 → 趋势不明，正常定投"

        # 加倍定投条件
        if ma60_deviation < -10:
            invest_suggest = f"🟢 **建议加倍定投**（低于60日均线 {ma60_deviation:.2f}%）"
        else:
            invest_suggest = f"🔵 **正常定投**（低于60日均线 {ma60_deviation:.2f}%）"

        # 显示结果
        st.subheader("📊 核心数据")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("当前净值", f"{last_price:.3f}")
        col2.metric("60日均线", f"{ma60:.3f}")
        col3.metric("总投入", f"{total_invest:.0f} 元")
        col4.metric("收益率", f"{profit_rate:.2f} %")
        col5.metric("最大回撤", f"{max_drawdown:.2f} %")

        st.subheader("📌 趋势与操作建议")
        st.success(signal)
        st.info(invest_suggest)

        # 保存记录
        log_data = {
            "时间": [datetime.now().strftime("%Y-%m-%d %H:%M")],
            "代码": [symbol],
            "收益率%": [round(profit_rate,2)],
            "偏离MA60%": [round(ma60_deviation,2)],
            "最大回撤%": [round(max_drawdown,2)],
            "信号": [signal]
        }
        log_df = pd.DataFrame(log_data)
        if os.path.exists("web_log.csv"):
            log_df.to_csv("web_log.csv", mode="a", header=False, index=False, encoding="utf-8-sig")
        else:
            log_df.to_csv("web_log.csv", index=False, encoding="utf-8-sig")

        st.success("✅ 记录已保存")

st.markdown("---")
st.caption("功能：净值/均线/收益率/最大回撤/趋势/定投建议/自动记录")
# ==========================
# 追加新功能（不动原有代码）
# ==========================

if code:
    try:
        # 1. 获取基金基本信息
        fund_info = ak.fund_info_em(symbol=code)
        st.subheader("📊 基金基本信息")
        st.dataframe(fund_info, use_container_width=True)

        # 2. 获取基金经理信息
        manager_info = ak.fund_manager_em(symbol=code)
        st.subheader("👔 基金经理")
        st.dataframe(manager_info, use_container_width=True)

        # 3. 获取基金持仓（重仓股）
        fund_position = ak.fund_portfolio_hold_em(symbol=code)
        st.subheader("📦 最新持仓（重仓股）")
        st.dataframe(fund_position, use_container_width=True)

        # 4. 定投回测功能（你最想要的）
        st.subheader("🧮 定投回测计算器")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", value=pd.to_datetime("2023-01-01"))
        with col2:
            end_date = st.date_input("结束日期", value=pd.to_datetime("today"))

        invest_amount = st.number_input("每次定投金额（元）", value=100, step=100)
        cycle_type = st.selectbox("定投周期", ["每周", "每月"])

        if st.button("开始计算定投收益"):
            # 获取历史净值
            nav_df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期'])
            nav_df = nav_df[(nav_df['净值日期'] >= pd.to_datetime(start_date)) & 
                            (nav_df['净值日期'] <= pd.to_datetime(end_date))]

            # 定投回测逻辑
            if cycle_type == "每周":
                invest_dates = pd.date_range(start=start_date, end=end_date, freq="W-FRI")
            else:
                invest_dates = pd.date_range(start=start_date, end=end_date, freq="M")

            invest_records = []
            total_invest = 0
            total_shares = 0

            for d in invest_dates:
                mask = nav_df['净值日期'] <= d
                if mask.any():
                    price = nav_df.loc[mask.idxmax(), '单位净值']
                    shares = invest_amount / price
                    total_shares += shares
                    total_invest += invest_amount
                    invest_records.append({
                        "日期": d,
                        "净值": price,
                        "投入": invest_amount,
                        "累计投入": total_invest,
                        "持有份额": total_shares
                    })

            # 最终资产
            if len(nav_df) > 0:
                final_nav = nav_df['单位净值'].iloc[-1]
                final_value = total_shares * final_nav
                profit = final_value - total_invest
                profit_rate = profit / total_invest * 100 if total_invest > 0 else 0

                st.success(f"✅ 回测完成")
                st.write(f"累计投入：**{total_invest:.2f} 元**")
                st.write(f"最终资产：**{final_value:.2f} 元**")
                st.write(f"总收益：**{profit:.2f} 元**")
                st.write(f"收益率：**{profit_rate:.2f}%**")

    except Exception as e:
        st.error(f"无法获取数据：{str(e)}")
