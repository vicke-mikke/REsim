# This is active
import streamlit as st

# File Processing Pkgs
import pandas as pd
import numpy as np
import base64
import datetime as dt
from property_module import Property
from myfunc2 import get_table

today = dt.datetime.today()
version = f'{today.year}{today.month}{today.day}'
query_params = st.experimental_get_query_params()
state_tax_table = pd.read_csv('2022PropertyTaxByState.csv')

def read_file(data_file):
    if data_file.type == "text/csv":
        df = pd.read_csv(data_file)
    elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(data_file, sheet_name=0)
    return (df)


def main():    
    # price
    price = int(query_params.get('price', [400])[0])
    price = 1000 * st.sidebar.number_input('Price (K)', value=price, step=1)
    real_value = int(query_params.get('value', [int(price/1000)])[0])
    real_value=1000* st.sidebar.number_input("Market value or ARV (K)", step=1, value=real_value)
    
    # other initial expense
    closing_cost = int(query_params.get('closing', [price*0.03])[0])
    closing_cost = st.sidebar.number_input(f"\$ other than DP such as closing, rehab etc. (reference, 3%_of_price[={price*0.03:.0f}])", value=closing_cost, step=1000)
    closing_cost_pct = closing_cost/price*100
    # Other initial cost (using legacy code...)
    rehab_cost = 0
    rehab_add =real_value-price 
    
    # Loan
    years = int(query_params.get('yr', [30])[0])
    years = st.sidebar.slider("Morgage Length (years)", 0, 30, value=years)
    down_payment_ratio = int(query_params.get('dp', [20])[0])
    down_payment_ratio = 1/100 * st.sidebar.slider("Down Payment (% to the price, If <20% PMI 1%)", 0, 100, value=down_payment_ratio)        
    interest_rate_pct = float(query_params.get('ir', [5.50])[0])
    interest_rate= 1/100 * st.sidebar.slider('Morgage Interest (%)', 2.0, 9.0, step=0.005, value=interest_rate_pct, format="%.3f")
    pmi_percent = float(query_params.get('pmi', [1.0])[0])
    pmi_percent = 1/100 * st.sidebar.slider("PMI Rate (Not relevant if DP >20%)", 0.0, 5.0, value=pmi_percent, step=0.005, format="%.3f")


    # Expenses
    property_state = st.sidebar.selectbox("State (2-alphabet abbreviation)", 
        (i for i in state_tax_table.STATE),
        index=42)
    tax_rate1=state_tax_table.loc[state_tax_table.STATE==property_state,'TaxRate'].values[0]
    tax_ref=tax_rate1*price/12
    tax=int(query_params.get('tax', [tax_ref])[0])
    tax = st.sidebar.number_input(f"Tax (reference: {property_state}'s tax rate ({tax_rate1*100:.2f}%) -> ${tax_ref:.0f}/m)", value=tax)
    tax_rate = tax * 12 / price
    insurance_ref=0.005*price/12
    insurance_value=int(query_params.get('ins', [insurance_ref])[0])
    insurance = st.sidebar.number_input(f"Insurance (ref. Price*0.5%/12 -> ${insurance_ref:.0f}/m)", value=insurance_value)
    insurance_rate = insurance * 12 / price
    hoa=int(query_params.get('hoa', [0])[0])
    hoa=st.sidebar.number_input('HOA (monthly)', step=10, value=hoa)
    
    maintenance_ref=0.005*price/12
    maintenance=int(query_params.get('mnt1', [maintenance_ref])[0])
    maintenance = st.sidebar.number_input(f"Maintenance (ref. Price*0.5%/12-> ${maintenance_ref:.0f}/m)", value=maintenance)
    maintenance_rate = maintenance * 12 / price

    extra_rehab=0
    
    # renting
    rent=int(query_params.get('rent', [price*0.005])[0])
    rent = st.sidebar.slider("Rent (monthly)", 0, rent*4, step=50, value=rent)
    vacancy_pct=int(query_params.get('vcr', [10])[0])
    vacancy_rate = 1/100 * st.sidebar.slider("Vacancy Rate (%)", 0, 100, step=1, value=vacancy_pct)
    op_value = int(query_params.get('op', [rent*0.1])[0])
    op_value = st.sidebar.slider("Renting Expenses (such as management, extra maintenance, etc)", 0, op_value*5, value=op_value, step=1)
    if rent==0:
        op_rate=0
    else:
        op_rate = op_value / rent


    # Future parameters
    appreciation_year=float(query_params.get('apr', [3.0])[0])
    appreciation_year = 1/100 * st.sidebar.slider("Appreciation (%)", 0.0, 10.0, value=appreciation_year, step=0.1)
    inflation_year=float(query_params.get('ifl', [2.5])[0])
    inflation_year = 1/100 * st.sidebar.slider("Inflation (%, affects rental income/cost)", 0.0, 10.0, value=inflation_year, step=0.1)



    b = Property('test', price=price, rehab_cost=rehab_cost, rehab_add=rehab_add, closing_cost_ratio=closing_cost_pct/100)
    b.sim_loan(down_payment_ratio=down_payment_ratio, years=years, 
               interest_rate=interest_rate)
    b.sim_equity(appreciation_year=appreciation_year)
    b.sim_ex(hoa=hoa, tax_rate=tax_rate, insurance_rate=insurance_rate, 
             maintenance_rate=maintenance_rate, inflation_year=inflation_year)
    b.sim_rent(extra_rehab=extra_rehab, rent=rent, vacancy_rate=vacancy_rate, 
               op_rate=op_rate)
    
    # period of interest including cf turning month
    period_list = [1,11,23,35,47,59,95,119,179,239,299,359]
    cf_plus = [p for p,cf in zip(b.period, b.cf) if cf>0]
    if len(cf_plus)>0:
        period_i = min(cf_plus)
        period_list = period_list + [period_i]
        period_list.sort()
    else:
        period_i = 'None'
    
    st.subheader('Number Breakdowns at Start')
    st.markdown(f"""
* Total Initial Payment: **${b.initial_total:,.0f}**
    * Down Payment: ${b.down_payment_ratio*b.price:,.0f}
    * Others (closing cost, rehab etc): ${b.closing_cost_ratio*b.price:,.0f}
* Monthly Morgage Payment: **${b.pay:,.0f}**
* PMI (While Equity < 20% ):  **${b.pmi[0]:,.0f}**
* Net Operating Income: **${b.noi[0]:,.0f}**
    * Income (Rent * (1 - vancancy rate)): **${b.income[0]:.0f}**
    * Operating Expense: **${b.opex[0]:,.0f}**
        * Possessing: ${b.ex[0]:,.0f} (hoa + tax + insurance + maintenance)
        * Renting: ${(b.opex[0]-b.ex[0]):,.0f} (Property management, additional maintenance etc.)
* Cash Flow After Loan: **${b.cf[0]:,.0f}** (NOI - morgage - pmi)
    * Positive Cash Flow at period (month) = {period_i}

                """)

    st.subheader(f'''Comparison: RE vs Stock Market''')
    st.markdown(f"""\
* RE: tg = cash flow + equity gain[property apreciation + paid balance]
* Stock Market: invest_change = monthly capital gain of the initial payment if invested""")
    
    return_year= 1/100 * st.slider("Stock Market Annual Return to compare (%) ", 0.0, 15.0, value=7.5, step=0.1)
    b.sim_invest(return_year=return_year)    
    t = get_table(b)
    st.line_chart(t[['tg','invest_change']])
    
    st.markdown(f"""\
    ##### Cap position (- Initial Capital)
    * RE: Equity at the month + cumsum Cash Flow up to the month
    * Stock Market: Capital at the month""")
    t['RE-Cap'] = t.equity + t.cf.cumsum()
    tt = t.copy()
    tt['Initial Pay'] = b.initial_total
    st.line_chart(tt[['RE-Cap','invest', 'Initial Pay']])
    st.text('Snapshot for capital gain/loss at selected periods (month)')
    
    periods = [i for i in period_list if i <= b.n_pay]
    periods = list(set(periods))
    periods.sort()
    d = t.loc[periods,:].copy()
    st.dataframe(d[['interest_paid', 'balance_change', 'pmi',
                'pvalue_change', 'hoa', 'tax', 'insurance',
                'maintenance', 'ex', 'rent', 'income', 'opex', 'noi', 'cf', 'tg',
                'invest_change', 'invest', 'RE-Cap']].T,  height=500)
    st.markdown('* pvalue_change = property appreciatioon (at the month)')
    
    # st.subheader('All numbers')
    # st.dataframe(t.T, height=800)
    
    # data URL
    URL=f"""[Direct_URL](/?\
price={price/1000:.0f}&\
value={real_value/1000:.0f}&\
dp={down_payment_ratio*100:.0f}&\
closing={closing_cost:.0f}&\
ir={interest_rate*100:.3f}&\
yr={years}&\
pmi={pmi_percent*100:.3f}&\
tax={tax:.0f}&\
ins={insurance:.0f}&\
hoa={hoa}&\
mnt1={maintenance}&\
rent={rent}&\
vcr={vacancy_rate*100:.0f}&\
op={op_value}&\
apr={appreciation_year*100:.1f}&\
ifl={inflation_year*100:.1f})\
"""
    st.subheader("Copy this URL for the quick access for the results")
    st.markdown(URL)


    # data download
    def get_table_download_link(df):
        """Generates a link allowing the data in a given panda dataframe to be downloaded
        in:  dataframe
        out: href string
        """
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
        href = f'<a href="data:file/csv;base64,{b64}"  download="download.csv">Download spreadsheet</a>'
        return href
    
    st.subheader("Spreadsheet download  (Transposed format - rows are the periods)")
    st.markdown(get_table_download_link(t), unsafe_allow_html=True)

# git add app.py;git commit -m "debug";git push -u origin main

if __name__ == '__main__':
    main()