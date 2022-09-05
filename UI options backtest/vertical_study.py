import pandas as pd
from datetime import timedelta


def vertical_sell(option_type, exit_condition, no_dupe_trade, date_list_datetime, full_option_type_df):
    if option_type == 'call':
        user_option_type = 'C'
    if option_type == 'put':
        user_option_type = 'P'

    # creating a df for vertical measurement
    my_vertical = []
    for row in range(len(no_dupe_trade)):
        latest_expire = no_dupe_trade.iloc[[row]]['EXPIRE_DATE'].tolist()[0]
        latest_quote_date = no_dupe_trade.iloc[[row]]['QUOTE_DATE'].tolist()[0]
        latest_dte = no_dupe_trade.iloc[[row]]['DTE'].tolist()[0]
        f_trade_df = full_option_type_df.loc[
            (full_option_type_df['EXPIRE_DATE'] == latest_expire) & (full_option_type_df['QUOTE_DATE'] == latest_quote_date) & (
                    full_option_type_df['DTE'] <= latest_dte)]
        f_trade_df = f_trade_df.loc[f_trade_df['PROB_ITM'] <= no_dupe_trade['PROB_ITM'][row]].sort_values(by='PROB_ITM',
                                                                                                        ascending=False)
        f_trade_df = f_trade_df.reset_index(drop=True)
        my_vertical.append(f_trade_df)

    made_trade_vertical = pd.DataFrame(columns=['SOLD_STRIKE', 'BOUGHT_STRIKE', 'TRADE_DATE', 'TRADE_LAST_PRICE',
                                                'DTE', 'EXIT_DATE', 'EXIT_LAST_PRICE', 'EXPIRE_DATE', 'AMOUNT_REC',
                                                'AMOUNT_RISKED', 'AMOUNT_BUYBACK', 'PROFIT', 'PROFIT_PERCENT'])
    #next_closest_trade = my_vertical[0]['QUOTE_DATE'][0]
    next_closest_trade = no_dupe_trade['QUOTE_DATE'][0]
    optimized_spread_list = []  # this can be returned also for data study collection

    for trade in range(len(my_vertical)):
        spread = my_vertical[trade]
        if len(spread) == 1:
            continue
        if option_type == 'put':
            if ((spread['STRIKE'][0]) - (spread['STRIKE'].tail(1).tolist()[0])) < 5:
                continue
        if option_type == 'call':
            if ((spread['STRIKE'].tail(1).tolist()[0]) - (spread['STRIKE'][0])) < 5:
                continue
        optimized_spread = pd.DataFrame(
            columns=['QUOTE_DATE', 'DTE', 'EXPIRE_DATE', 'STRIKE', 'WIDTH', 'NET_CREDIT', 'BUYING_POWER', 'POP_%',
                     'ROC', 'MARGINAL_COST'])
        # creates a dataframe that gives optimal trade width
        for i in range(1, len(spread)):
            if option_type == 'call':  # Strike increases as PROB_ITM decreases. (we always buy lower PROB_ITM for our short leg)
                width = spread['STRIKE'][i] - spread['STRIKE'][0]
                narrow_width = spread['STRIKE'][i - 1] - spread['STRIKE'][0]
            if option_type == 'put':  # Strike decreases as PROB_ITM decreases
                width = spread['STRIKE'][0] - spread['STRIKE'][i]
                narrow_width = spread['STRIKE'][0] - spread['STRIKE'][i - 1]

            credit = ((spread['{}_ASK'.format(user_option_type)][0] + spread['{}_BID'.format(user_option_type)][0]) / 2).round(2)

            bought = ((spread['{}_ASK'.format(user_option_type)][i] + spread['{}_BID'.format(user_option_type)][i]) / 2).round(2)
            net_credit = credit - bought
            buying_power = (width - net_credit).round(2)

            roc = (net_credit / buying_power).round(3)
            pop = ((((net_credit / width) * 100) - 100) * -1).round(3)

            narrow_bought = ((spread['{}_ASK'.format(user_option_type)][i - 1] + spread['{}_BID'.format(user_option_type)][i - 1]) / 2).round(2)
            narrow_net_credit = credit - narrow_bought
            narrow_buying_power = (narrow_width - narrow_net_credit).round(2)

            if (narrow_buying_power != 0) & (narrow_net_credit != 0):
                narrow_roc = (narrow_net_credit / narrow_buying_power).round(3)
                marginal_cost = roc / narrow_roc
            else:
                marginal_cost = 0

            single_optimized_spread = pd.DataFrame([{'QUOTE_DATE': spread['QUOTE_DATE'][i],
                                                     'DTE': spread['DTE'][i],
                                                     'EXPIRE_DATE': spread['EXPIRE_DATE'][i],
                                                     'STRIKE': spread['STRIKE'][i],
                                                     'WIDTH': width,
                                                     'NET_CREDIT': net_credit,
                                                     'BUYING_POWER': buying_power,
                                                     'ROC': roc,
                                                     'POP_%': pop,
                                                     'MARGINAL_COST': marginal_cost}])
            optimized_spread = pd.concat([optimized_spread, single_optimized_spread])
            optimized_spread = optimized_spread.reset_index(drop=True)
        optimized_spread_list.append(optimized_spread)

        # filters the data between width 5-10 and finds the highest margin cost value
        highest_margin_cost = max(optimized_spread.loc[optimized_spread['WIDTH'].between(5, 10)]['MARGINAL_COST'])
        highest_margin_strike = \
        optimized_spread.loc[optimized_spread['MARGINAL_COST'] == highest_margin_cost]['STRIKE'].tolist()[0]

        # the very first row of our spread is where we are selling our option
        sold = spread.iloc[[0]]
        latest_expire_sold = sold['EXPIRE_DATE'].tolist()[0]
        latest_strike_sold = sold['STRIKE'].tolist()[0]
        latest_dte_sold = sold['DTE'].tolist()[0]
        sold_df = full_option_type_df.loc[
            (full_option_type_df['EXPIRE_DATE'] == latest_expire_sold) & (full_option_type_df['STRIKE'] == latest_strike_sold) & (
                    full_option_type_df['DTE'] <= latest_dte_sold)]
        sold_df = sold_df.reset_index(drop=True)

        # the highest margin strike we determined is where we are buying our option
        bought = spread.loc[spread['STRIKE'] == highest_margin_strike]
        latest_expire_bought = bought['EXPIRE_DATE'].tolist()[0]
        latest_strike_bought = bought['STRIKE'].tolist()[0]
        latest_dte_bought = bought['DTE'].tolist()[0]
        bought_df = full_option_type_df.loc[
            (full_option_type_df['EXPIRE_DATE'] == latest_expire_bought) & (full_option_type_df['STRIKE'] == latest_strike_bought) & (
                    full_option_type_df['DTE'] <= latest_dte_bought)]
        bought_df = bought_df.reset_index(drop=True)

        if option_type == 'call':
            spread_width = (bought_df['STRIKE'][0]) - (sold_df['STRIKE'][0])  # for dispaying data in df
        if option_type == 'put':
            spread_width = (sold_df['STRIKE'][0]) - (bought_df['STRIKE'][0])

        if exit_condition == '50':
            if next_closest_trade == sold_df['QUOTE_DATE'][0]:
                buy_mid_list = []
                sell_mid_list = []
                win_percent = []
                profit_list = []
                buy_back = []
                for row in range(len(sold_df)):
                    buy_ask = bought_df['{}_ASK'.format(user_option_type)][row]
                    buy_bid = bought_df['{}_BID'.format(user_option_type)][row]

                    sell_ask = sold_df['{}_ASK'.format(user_option_type)][row]
                    sell_bid = sold_df['{}_BID'.format(user_option_type)][row]

                    buy_mid = ((buy_ask + buy_bid) / 2).round(2)
                    sell_mid = ((sell_ask + sell_bid) / 2).round(2)

                    buy_mid_list.append(buy_mid)
                    sell_mid_list.append(sell_mid)

                    initial_credit = (sell_mid_list[0] - buy_mid_list[0]).round(2)
                    exit_buy_back = (sell_mid - buy_mid).round(2)

                    if exit_buy_back < 0:
                        exit_buy_back = 0

                    if exit_buy_back > spread_width:
                        exit_buy_back = spread_width

                    profit = (initial_credit - exit_buy_back).round(2)
                    profit_percentage = (profit / initial_credit) * 100

                    buy_back.append(exit_buy_back)
                    win_percent.append(profit_percentage)
                    profit_list.append(profit)

                boolean_list = [True if x >= 50 else False for x in win_percent]
                if True in boolean_list:
                    # first_true_index very important
                    first_true_index = boolean_list.index(True)

                    exit_date = sold_df['QUOTE_DATE'][first_true_index]
                    if exit_date > date_list_datetime[-1]:
                        break
                    next_closest_trade = min([y for y in date_list_datetime if y >= exit_date],
                                             key=lambda j: abs(j - exit_date))
                    single_made_trade_vertical = pd.DataFrame([{'SOLD_STRIKE': sold_df['STRIKE'][0],
                                                                'BOUGHT_STRIKE': bought_df['STRIKE'][0],
                                                                'TRADE_DATE': sold_df['QUOTE_DATE'][0],
                                                                'TRADE_LAST_PRICE': sold_df['LAST_PRICE'][0],
                                                                'EXIT_DATE': sold_df['QUOTE_DATE'][first_true_index],
                                                                'EXIT_LAST_PRICE': sold_df['LAST_PRICE'][first_true_index],
                                                                'EXPIRE_DATE': sold_df['EXPIRE_DATE'][0],
                                                                'DTE': sold_df['DTE'][0],
                                                                'AMOUNT_REC': initial_credit,
                                                                'AMOUNT_RISKED': spread_width,
                                                                'AMOUNT_BUYBACK': buy_back[first_true_index],
                                                                'PROFIT': profit_list[first_true_index],
                                                                'PROFIT_PERCENT': win_percent[first_true_index]}])

                    made_trade_vertical = pd.concat([made_trade_vertical, single_made_trade_vertical])
                    made_trade_vertical = made_trade_vertical.reset_index(drop=True)

                else:
                    current_date = sold_df['QUOTE_DATE'][0]
                    dte = sold_df['DTE'][0]
                    exit_date = current_date + timedelta(days=dte)
                    if exit_date > date_list_datetime[-1]:
                        break
                    next_closest_trade = min([y for y in date_list_datetime if y >= exit_date],
                                             key=lambda j: abs(j - exit_date))

                    single_made_trade_vertical = pd.DataFrame([{'SOLD_STRIKE': sold_df['STRIKE'][0],
                                                                'BOUGHT_STRIKE': bought_df['STRIKE'][0],
                                                                'TRADE_DATE': sold_df['QUOTE_DATE'][0],
                                                                'TRADE_LAST_PRICE': sold_df['LAST_PRICE'][0],
                                                                'EXIT_DATE': sold_df['QUOTE_DATE'].tail(1).tolist()[0],
                                                                'EXIT_LAST_PRICE': sold_df['LAST_PRICE'].tail(1).tolist()[0],
                                                                'EXPIRE_DATE': sold_df['EXPIRE_DATE'][0],
                                                                'DTE': sold_df['DTE'][0],
                                                                'AMOUNT_REC': initial_credit,
                                                                'AMOUNT_RISKED': spread_width,
                                                                'AMOUNT_BUYBACK': exit_buy_back,
                                                                'PROFIT': profit,
                                                                'PROFIT_PERCENT': profit_percentage}])
                    made_trade_vertical = pd.concat([made_trade_vertical, single_made_trade_vertical])
                    made_trade_vertical = made_trade_vertical.reset_index(drop=True)

        if exit_condition == 'dte':
            if next_closest_trade == sold_df['QUOTE_DATE'][0]:
                buy_mid_list = []
                sell_mid_list = []
                # loops through the sold_df and lists all the data we need and we pick the data we need to store it
                # in df by using the first true index
                for row in range(len(sold_df)):
                    buy_ask = bought_df['{}_ASK'.format(user_option_type)][row]
                    buy_bid = bought_df['{}_BID'.format(user_option_type)][row]

                    sell_ask = sold_df['{}_ASK'.format(user_option_type)][row]
                    sell_bid = sold_df['{}_BID'.format(user_option_type)][row]

                    buy_mid = ((buy_ask + buy_bid) / 2).round(2)
                    sell_mid = ((sell_ask + sell_bid) / 2).round(2)

                    buy_mid_list.append(buy_mid)
                    sell_mid_list.append(sell_mid)

                initial_credit = (sell_mid_list[0] - buy_mid_list[0]).round(2)
                exit_buy_back = (sell_mid_list[-1] - buy_mid_list[-1]).round(2)

                # sometimes data that is given has such wide bid ask spread that it doesn't make sense to get mid price since it will not be filled
                # this code is used so the basic rules of options doesnt break
                if exit_buy_back < 0:
                    exit_buy_back = 0

                if exit_buy_back > spread_width:
                    exit_buy_back = spread_width

                profit = (initial_credit - exit_buy_back).round(2)
                profit_percentage = (profit / initial_credit) * 100

                next_date = sold_df['QUOTE_DATE'][0]
                dte = sold_df['DTE'][0]
                exit_date = next_date + timedelta(days=dte)
                if exit_date > date_list_datetime[-1]:
                    break
                next_closest_trade = min([y for y in date_list_datetime if y >= exit_date],
                                     key=lambda j: abs(j - exit_date))

                single_made_trade_vertical = pd.DataFrame([{'SOLD_STRIKE': sold_df['STRIKE'][0],
                                                            'BOUGHT_STRIKE': bought_df['STRIKE'][0],
                                                            'TRADE_DATE': sold_df['QUOTE_DATE'][0],
                                                            'TRADE_LAST_PRICE': sold_df['LAST_PRICE'][0],
                                                            'EXIT_DATE': sold_df['QUOTE_DATE'].tail(1).tolist()[0],
                                                            'EXIT_LAST_PRICE': sold_df['LAST_PRICE'].tail(1).tolist()[0],
                                                            'EXPIRE_DATE': sold_df['EXPIRE_DATE'][0],
                                                            'DTE': sold_df['DTE'][0],
                                                            'AMOUNT_REC': initial_credit,
                                                            'AMOUNT_RISKED': spread_width,
                                                            'AMOUNT_BUYBACK': exit_buy_back,
                                                            'PROFIT': profit,
                                                            'PROFIT_PERCENT': profit_percentage}])
                made_trade_vertical = pd.concat([made_trade_vertical, single_made_trade_vertical])
                made_trade_vertical = made_trade_vertical.reset_index(drop=True)
    return made_trade_vertical
