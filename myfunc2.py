import pandas as pd

def round_list(num_list):
    return ([round(i) for i in num_list])

def get_table(p):
    """Take property class and return the pay schedule table"""
    df_dict={}
    for k, v in p.__dict__.items():
        try:
            len(v)
            if len(v) == p.n_pay:
                df_dict[k] = round_list(getattr(p, k))
        except TypeError:
            pass
    return(pd.DataFrame(data=df_dict))