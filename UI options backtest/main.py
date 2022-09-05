import pandas as pd
import retrieve_data
import vertical_study
import naked_study


desired_width = 200
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', 20)

# assigning aapl_call/put_df by reading files and converting it to df
# dir_path = 'C:\\Users\\bkim5\\Desktop\\aapl_options_data'
# raw_df = retrieve_data.read_csv_and_convert(dir_path)

# aapl_put_df = retrieve_data.put_df(raw_df)
# aapl_call_df = retrieve_data.call_df(raw_df)

# aapl_put_df['PROB_ITM'] = aapl_put_df['P_DELTA'] * -100
# aapl_call_df['PROB_ITM'] = aapl_call_df['C_DELTA'] * 100

# assigning aapl_call/put_df by reading already made df
aapl_put_df = pd.read_csv('C:\\Users\\bkim5\\Desktop\\aapl_put_df.csv')
aapl_put_df['QUOTE_DATE'] = pd.to_datetime(aapl_put_df['QUOTE_DATE']) # when importing, dates are converted into obj so we convert it back to datetime
aapl_put_df['PROB_ITM'] = aapl_put_df['P_DELTA'] * -100

aapl_call_df = pd.read_csv('C:\\Users\\bkim5\\Desktop\\aapl_call_df.csv')
aapl_call_df['QUOTE_DATE'] = pd.to_datetime(aapl_call_df['QUOTE_DATE'])
aapl_call_df['PROB_ITM'] = aapl_call_df['C_DELTA'] * 100

while True:
    user_input_option_type = input('Which option study would you like to backtest (call / put): ').lower()
    if user_input_option_type == 'call':
        user_option_type_df = aapl_call_df
        break
    elif user_input_option_type == 'put':
        user_option_type_df = aapl_put_df
        break
    else:
        print('wrong input')

condition = True
back_condition = True
while condition:
    try:
        min_user_prob_itm = int(input('Desired minimum prob. ITM percentage: '))
        max_user_prob_itm = int(input('Desired maximum prob. ITM percentage: '))
        min_user_dte = int(input('Desired minimum DTE: '))
        max_user_dte = int(input('Desired maximum DTE: '))
        print('processing data...')

        # The code below will find the trade that meet the users criteria and puts it in a dataframe
        my_trade_condition_df = pd.DataFrame()
        for rows in range(len(user_option_type_df)):
            if (min_user_prob_itm <= user_option_type_df['PROB_ITM'][rows] <= max_user_prob_itm) and (
                    min_user_dte <= user_option_type_df['DTE'][rows] <= max_user_dte):
                trade_row = (user_option_type_df.iloc[[rows]])
                my_trade_condition_df = pd.concat([my_trade_condition_df, trade_row])
        my_trade_condition_df = my_trade_condition_df.reset_index(drop=True)

        if my_trade_condition_df.empty:
            print('Dataframe is empty, input different value')
        else:
            # Deleting any dupe exp date in my trade
            seen_dates = []
            if user_input_option_type == 'put':
                no_dupe_trade = pd.DataFrame(
                    columns=['QUOTE_DATE', 'EXPIRE_DATE', 'LAST_PRICE', 'DTE', 'STRIKE', 'P_ASK', 'P_BID',
                             'P_DELTA', 'P_GAMMA', 'P_VEGA', 'P_THETA', 'P_VOLUME', 'P_IV'])
            if user_input_option_type == 'call':
                no_dupe_trade = pd.DataFrame(
                    columns=['QUOTE_DATE', 'EXPIRE_DATE', 'LAST_PRICE', 'DTE', 'STRIKE', 'C_ASK', 'C_BID',
                             'C_DELTA', 'C_GAMMA', 'C_VEGA', 'C_THETA', 'C_VOLUME', 'C_IV'])

            for row in range(len(my_trade_condition_df)):
                expire_date = my_trade_condition_df['EXPIRE_DATE'][row]
                if expire_date not in seen_dates:
                    seen_dates.append(expire_date)
                    trade_row = my_trade_condition_df.iloc[[row]]
                    no_dupe_trade = pd.concat([no_dupe_trade, trade_row])
                    no_dupe_trade = no_dupe_trade.reset_index(drop=True)
                else:
                    pass

            # only retrieve option contract with full data
            complete_contract_df = []
            incomplete_contract_df = []
            for row in range(len(no_dupe_trade)):
                # These values are needed to find the full historic option data of each of my trade
                expire = no_dupe_trade.iloc[[row]]['EXPIRE_DATE'].tolist()[0]
                strike = no_dupe_trade.iloc[[row]]['STRIKE'].tolist()[0]
                dte = no_dupe_trade.iloc[[row]]['DTE'].tolist()[0]

                input_trade = user_option_type_df.loc[
                    (user_option_type_df['EXPIRE_DATE'] == expire) & (user_option_type_df['STRIKE'] == strike) &
                    (user_option_type_df['DTE'] <= dte)]
                input_trade = input_trade.reset_index(drop=True)

                if (input_trade['DTE'].tail(1).tolist()[0] == 0) or (input_trade['DTE'].tail(1).tolist()[0] == 1) or (
                        input_trade['DTE'].tail(1).tolist()[0] == 2):
                    complete_contract_df.append(input_trade)
                else:
                    incomplete_contract_df.append(input_trade)

            # deletes option contract that does not have full historic data from my trading dataframe
            incomplete_contract_dates = []
            for row in range(len(incomplete_contract_df)):
                incomplete_contract_dates.append(incomplete_contract_df[row]['QUOTE_DATE'][0])

            for row in range(len(no_dupe_trade)):
                if no_dupe_trade['QUOTE_DATE'][row] in incomplete_contract_dates:
                    no_dupe_trade = no_dupe_trade.drop([row])
            no_dupe_trade = no_dupe_trade.reset_index(drop=True)

            date_list_datetime = []
            for row in range(len(no_dupe_trade)):
                dates = no_dupe_trade['QUOTE_DATE'][row]
                date_list_datetime.append(dates)

            while condition:
                user_input_study_type = input(
                    'Which option trade type would you like to simulate (naked / vertical)\n'
                    'Type (back) to input different trade condition\n'
                    'Type (exit) to close: ').lower()
                if user_input_study_type == 'naked':
                    while condition:
                        user_input_exit_condition = input('Enter your exit condition (50 / dte)\n'
                                                          'Type (back) to input different study type\n'
                                                          'Type (exit) to close: ').lower()
                        print('processing data...')
                        if user_input_exit_condition == '50':
                            print(naked_study.naked_sell(user_input_option_type, '50', complete_contract_df, date_list_datetime))
                            condition = False
                        if user_input_exit_condition == 'dte':
                            print(naked_study.naked_sell(user_input_option_type, 'dte', complete_contract_df, date_list_datetime))
                            condition = False
                        if user_input_exit_condition == 'back':
                            back_condition = False
                            break
                        if user_input_exit_condition == 'exit':
                            condition = False
                        else:
                            if condition:  # without this, at the end of the output, it will always print out 'wrong input'
                                print('wrong input')
                if user_input_study_type == 'vertical':
                    while condition:
                        user_input_exit_condition = input('Enter your exit condition (50 / dte)\n'
                                                          'Type (back) to input different study type\n'
                                                          'Type (exit) to close: ').lower()
                        print('processing data...')
                        if user_input_exit_condition == '50':
                            print(vertical_study.vertical_sell(user_input_option_type, '50', no_dupe_trade, date_list_datetime, user_option_type_df))
                            condition = False
                        if user_input_exit_condition == 'dte':
                            print(vertical_study.vertical_sell(user_input_option_type, 'dte', no_dupe_trade, date_list_datetime, user_option_type_df))
                            condition = False
                        if user_input_exit_condition == 'back':
                            back_condition = False
                            break
                        if user_input_exit_condition == 'exit':
                            condition = False
                        else:
                            if condition:
                                print('wrong input')
                if user_input_study_type == 'exit':
                    condition = False
                if user_input_study_type == 'back':
                    break
                else:
                    if condition and back_condition:
                        print('wrong input')
    except ValueError:
        print('Wrong input')

