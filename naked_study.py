import pandas as pd
from datetime import timedelta


def naked_sell(option_type, exit_condition, complete_contract_df, date_list_datetime):
    made_trade_naked = pd.DataFrame(
        columns=['STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE', 'DTE', 'EXIT_DATE', 'EXIT_LAST_PRICE', 'EXPIRE_DATE',
                 'AMOUNT_REC', 'AMOUNT_BUYBACK', 'PROFIT_PERCENT', 'PROFIT'])
    next_closest_trade = complete_contract_df[0]['QUOTE_DATE'][0]
    exit_date = []
    if option_type.lower() == 'call':
        user_option_type = 'C'
    if option_type.lower() == 'put':
        user_option_type = 'P'

    for row in range(len(complete_contract_df)):
        each_df = complete_contract_df[row]
        # next_closest_trade date must be equal to the first data of each_df because other df within each_df also contains that next_closest trade date.
        if exit_condition == '50':
            if next_closest_trade == each_df['QUOTE_DATE'][0]:
                win_percent = []
                amount_buyback_list = []
                profit_list = []
                # looping through each df in my_df and calculating values
                for rows in range(len(each_df)):
                    amount_received = ((each_df['{}_ASK'.format(user_option_type)][0] + each_df['{}_BID'.format(user_option_type)][0]) / 2).round(3)
                    current_p_ask = each_df['{}_ASK'.format(user_option_type)][rows]
                    current_p_bid = each_df['{}_BID'.format(user_option_type)][rows]
                    amount_buyback = ((current_p_ask + current_p_bid) / 2).round(3)
                    profit = (amount_received - amount_buyback).round(3)
                    profit_percent = (((amount_received - amount_buyback).round(3)) / amount_received) * 100

                    # These are needed to find the correct index of the value that needs to be appended in the made_trade df
                    amount_buyback_list.append(amount_buyback)
                    win_percent.append(profit_percent)
                    profit_list.append(profit)

                # This boolean list is used to find out when to exit the trade. (when the FIRST index of each_df is True)
                boolean_list = [True if x >= 50 else False for x in win_percent]
                if True in boolean_list:
                    # Finds the first index of where each_df is true meaning that index has all the exit values.
                    first_true_index = boolean_list.index(True)
                    exit_date.append(each_df['QUOTE_DATE'][first_true_index])

                    next_date = each_df['QUOTE_DATE'][first_true_index]
                    if next_date > date_list_datetime[-1]:
                        break

                    next_closest_trade = min([y for y in date_list_datetime if y >= next_date],
                                             key=lambda j: abs(j - next_date))

                    single_made_trade_naked = pd.DataFrame([{'TRADE_DATE': each_df['QUOTE_DATE'][0],
                                                             'TRADE_LAST_PRICE': each_df['LAST_PRICE'][0],
                                                             'EXIT_DATE': each_df['QUOTE_DATE'][first_true_index],
                                                             'EXIT_LAST_PRICE': each_df['LAST_PRICE'][first_true_index],
                                                             'STRIKE': each_df['STRIKE'][0],
                                                             'EXPIRE_DATE': each_df['EXPIRE_DATE'][0],
                                                             'DTE': each_df['DTE'][0],
                                                             'AMOUNT_REC': amount_received,
                                                             # warning can be ignored since amount_rec is same in all rows
                                                             'AMOUNT_BUYBACK': amount_buyback_list[first_true_index],
                                                             'PROFIT_PERCENT': win_percent[first_true_index],
                                                             'PROFIT': profit_list[first_true_index]}])

                    made_trade_naked = pd.concat([made_trade_naked, single_made_trade_naked])
                    made_trade_naked = made_trade_naked.reset_index(drop=True)

                else:
                    next_date = each_df['QUOTE_DATE'][0]
                    dte = each_df['DTE'][0]
                    date_expired = next_date + timedelta(days=dte)
                    if date_expired > date_list_datetime[-1]:
                        break

                    next_closest_trade = min([y for y in date_list_datetime if y >= date_expired],
                                             key=lambda j: abs(j - date_expired))

                    single_made_trade_naked = pd.DataFrame([{'TRADE_DATE': each_df['QUOTE_DATE'][0],
                                                             'TRADE_LAST_PRICE': each_df['LAST_PRICE'][0],
                                                             'EXIT_DATE': each_df['QUOTE_DATE'].tail(1).tolist()[0],
                                                             'EXIT_LAST_PRICE': each_df['LAST_PRICE'].tail(1).tolist()[
                                                                 0],
                                                             'STRIKE': each_df['STRIKE'][0],
                                                             'EXPIRE_DATE': each_df['EXPIRE_DATE'][0],
                                                             'DTE': each_df['DTE'][0],
                                                             'AMOUNT_REC': amount_received,
                                                             'AMOUNT_BUYBACK': amount_buyback,
                                                             # warnings is ignored since the value of the variable is always going to be the last index because the exit date is the very last of the index
                                                             'PROFIT_PERCENT': profit_percent,
                                                             'PROFIT': profit}])
                    made_trade_naked = pd.concat([made_trade_naked, single_made_trade_naked])
                    made_trade_naked = made_trade_naked.reset_index(drop=True)

        if exit_condition == 'dte':
            if next_closest_trade == each_df['QUOTE_DATE'][0]:
                amount_received = ((each_df['{}_ASK'.format(user_option_type)][0] +
                                    each_df['{}_BID'.format(user_option_type)][0]) / 2)
                amount_buyback = ((each_df['{}_ASK'.format(user_option_type)].tail(1).tolist()[0] +
                                   each_df['{}_BID'.format(user_option_type)].tail(1).tolist()[0]) / 2)
                profit = (amount_received - amount_buyback).round(3)
                profit_percent = (((amount_received - amount_buyback).round(3)) / amount_received) * 100

                next_date = each_df['QUOTE_DATE'][0]
                dte = each_df['DTE'][0]
                date_expired = next_date + timedelta(days=dte)
                # when date_expired exceeds the last value of date, it will break
                if date_expired > date_list_datetime[-1]:
                    break

                # This will use the date expired and find the next closest trade date in the date list
                next_closest_trade = min([y for y in date_list_datetime if y >= date_expired],
                                         key=lambda j: abs(j - date_expired))

                single_made_trade = pd.DataFrame([{'TRADE_DATE': each_df['QUOTE_DATE'][0],
                                                   'TRADE_LAST_PRICE': each_df['LAST_PRICE'][0],
                                                   'EXIT_DATE': each_df['QUOTE_DATE'].tail(1).tolist()[0],
                                                   'EXIT_LAST_PRICE': each_df['LAST_PRICE'].tail(1).tolist()[0],
                                                   'STRIKE': each_df['STRIKE'][0],
                                                   'EXPIRE_DATE': each_df['EXPIRE_DATE'][0],
                                                   'DTE': each_df['DTE'][0],
                                                   'AMOUNT_REC': amount_received,
                                                   'AMOUNT_BUYBACK': amount_buyback,
                                                   'PROFIT_PERCENT': profit_percent,
                                                   'PROFIT': profit}])
                made_trade_naked = pd.concat([made_trade_naked, single_made_trade])
                made_trade_naked = made_trade_naked.reset_index(drop=True)
    return made_trade_naked
