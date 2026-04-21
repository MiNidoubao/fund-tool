import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="基金定投分析", layout="wide")
st.title("📈 红利低波 定投分析工具（完整版）")

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