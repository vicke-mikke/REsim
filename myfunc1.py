
def calc_compunded_value(principal, r, n):
    v = [principal * (1+r)**i for i in range(n)]
    v_1 = [principal] + v[:-1]
    v_change = [x - y for x,y in zip(v, v_1)]
    return({'value_change':v_change, 'value':v})

def calc_loan(principal, n_pay, interest_rate):
    P = principal
    n = n_pay
    r = interest_rate
    pay = (P * r * (1+r)**n) / ((1+r)**n - 1)
    
    # amortization
    balance = P
    balance_change = []
    end_balance = []
    interest_paid = []
    for i in range(n):
        interest = balance * r
        paid = pay - interest
        # update
        balance = balance - (paid) 
        # add list
        balance_change.append(paid)
        interest_paid.append(interest)
        end_balance.append(balance)
    return ({'pay':pay, 'interest_paid':interest_paid,
             'balance_change':balance_change,
             'end_balance':end_balance})