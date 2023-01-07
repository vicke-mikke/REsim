import pandas as pd
from myfunc1 import calc_compunded_value,calc_loan

class Property:
    def __init__(self, name, price, rehab_cost, rehab_add, closing_cost_ratio=0.03):
        self.name = name
        self.price = price
        self.rehab_cost = rehab_cost
        self.rehab_add = rehab_add
        self.closing_cost_ratio = closing_cost_ratio
        self.initial_cost = price * closing_cost_ratio + rehab_cost
    
    def sim_loan(self, down_payment_ratio, years, interest_rate, pmi_pct):
        self.years = years
        self.interest_rate = interest_rate
        self.n_pay = years * 12
        self.period = range(self.n_pay)
        self.down_payment_ratio = down_payment_ratio
        self.initial_total = self.initial_cost + self.price * down_payment_ratio

        principal = self.price * (1 - down_payment_ratio)
        r = interest_rate/12
        t = calc_loan(principal, self.n_pay, r)
        self.pay = t['pay']
        self.interest_paid = t['interest_paid']
        self.balance_change = t['balance_change']
        self.end_balance = t['end_balance']
        # PMI
        balance80 = (self.price + self.rehab_add) * 0.8
        self.pmi = [b * pmi_pct/12 if b > balance80
                    else 0 for b in self.end_balance]
            
    def sim_equity(self, appreciation_year):
        self.appreciation_year = appreciation_year
        r = (1 + appreciation_year)**(1/12) - 1
        t = calc_compunded_value(self.price + self.rehab_add, r, self.n_pay)
        self.property_value = t['value']
        self.pvalue_change = t['value_change']
        self.equity = [x-y for x,y in zip(self.property_value,self.end_balance)]
    
    def sim_ex(self, hoa, tax_rate, insurance_rate, maintenance_rate,
               inflation_year):
        self.inflation_year = inflation_year
        r = (1 + inflation_year)**(1/12) - 1
        self.hoa = calc_compunded_value(hoa, r, self.n_pay)['value']
        self.tax = [pv * tax_rate/12 for pv in self.property_value]
        self.insurance = [pv * insurance_rate/12 for pv in self.property_value]
        self.maintenance = [pv * maintenance_rate/12 for pv in self.property_value]
        self.ex = [sum(i) for i in zip(self.hoa, self.tax, self.insurance, 
                                       self.maintenance)]
    
    def sim_rent(self, extra_rehab, rent, vacancy_rate=0.9, op_rate=0.15):
        self.extra_rehab = extra_rehab
        r = (1 + self.inflation_year)**(1/12) - 1
        self.rent = calc_compunded_value(rent, r, self.n_pay)['value']
        self.income = [rent * (1-vacancy_rate) for rent in self.rent]
        self.opex = [rent*op_rate + ex for rent,ex in zip(self.rent, self.ex)]
        self.noi = [income - opex for income,opex in zip(self.income, self.opex)]
        self.cf = [noi - self.pay - pmi for noi,pmi in zip(self.noi, self.pmi)]
        self.tg = [sum(i) for i in zip(self.cf, self.balance_change, 
                                       self.pvalue_change)]
    
    def sim_invest(self, return_year, vs_rent=True):
        self.return_year = return_year
        r = (1 + return_year)**(1/12) - 1
        if vs_rent:
            invest_seed = self.initial_total+ self.extra_rehab
        else:
            invest_seed = self.initial_total
        t = calc_compunded_value(invest_seed, r, self.n_pay)

        self.invest = t['value']
        self.invest_change = t['value_change']

