from process_data import up_to_date_check, process_raw_data, make_api_call

def get_chart_ready_df():
    df = process_raw_data()

    chart_ready_df = df.groupby(
                        ['Country', 
                        'Population', 
                        'Date', 
                        'ISO-3', 
                        'Multiple_Territories',
                        'Month and Year',
                        'Day']
                    ).agg({
                        'Deaths':'sum',
                        'Deaths per 1M':'sum',
                        'Cases': 'sum',
                        'Cases per 1M' : 'sum',
                        'New Deaths (n)' : 'sum',
                        'New Cases (n)' : 'sum'
#                         'Change in Deaths (pct)' : 'max',
#                         'Change in Cases (pct)' : 'max'
                    }).reset_index()

    chart_ready_df.to_csv('chart_ready.csv', index = False)
    return chart_ready_df



