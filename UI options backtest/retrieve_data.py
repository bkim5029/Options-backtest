import pandas as pd
import os


dtype_dict = {'[QUOTE_UNIXTIME]': 'int64', ' [QUOTE_READTIME]': 'object', ' [QUOTE_DATE]': 'object',
              ' [QUOTE_TIME_HOURS]': 'float64', ' [UNDERLYING_LAST]': 'float64', ' [EXPIRE_DATE]': 'object',
              ' [EXPIRE_UNIX]': 'int64', ' [DTE]': 'float64', ' [C_DELTA]': 'float64', ' [C_GAMMA]': 'float64',
              ' [C_VEGA]': 'float64', ' [C_THETA]': 'float64', ' [C_RHO]': 'float64', ' [C_IV]': 'float64',
              ' [C_VOLUME]': 'float64', ' [C_LAST]': 'float64', ' [C_SIZE]': 'object', ' [C_BID]': 'float64',
              ' [C_ASK]': 'float64', ' [STRIKE]': 'float64', ' [P_BID]': 'float64', ' [P_ASK]': 'float64',
              ' [P_SIZE]': 'object', ' [P_LAST]': 'float64', ' [P_DELTA]': 'float64', ' [P_GAMMA]': 'float64',
              ' [P_VEGA]': 'float64', ' [P_THETA]': 'float64', ' [P_RHO]': 'float64',  ' [P_IV]': 'float64',
              ' [P_VOLUME]': 'float64', ' [STRIKE_DISTANCE]': 'float64', ' [STRIKE_DISTANCE_PCT]': 'float64'
             }


# Collects data from each file, make it into df and combine it all together into one
def read_csv_and_convert(dir_path):
    list_of_dataframes = []
    # only collect the data that is in another folder within the path. If it is a file, skip.
    for path in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, path)):
            pass
        else:
            folder_path = os.path.join(dir_path, path)
            for file in os.listdir(folder_path):
                dataframe = pd.read_csv(os.path.join(folder_path, file))
                dataframe = dataframe.replace(' ',0)
                dataframe = dataframe.astype(dtype_dict)
                list_of_dataframes.append(dataframe)

    dataframe = list_of_dataframes[0]
    for dataframe_index in range(1, len(list_of_dataframes)):
        dataframe = pd.concat([dataframe, list_of_dataframes[dataframe_index]])

    dataframe[' [EXPIRE_DATE]'] = dataframe[' [EXPIRE_DATE]'].str.strip()
    dataframe[' [QUOTE_DATE]'] = pd.to_datetime(dataframe[' [QUOTE_DATE]'])
    dataframe = dataframe.sort_values(by=' [QUOTE_DATE]')
    dataframe = dataframe.reset_index(drop=True)
    return dataframe


def put_df(dataframe):
    dataframe = dataframe[[' [QUOTE_DATE]', ' [EXPIRE_DATE]',
                           ' [UNDERLYING_LAST]', ' [DTE]',
                           ' [STRIKE]', ' [P_ASK]',
                           ' [P_BID]', ' [P_DELTA]',
                           ' [P_GAMMA]', ' [P_VEGA]',
                           ' [P_THETA]', ' [P_VOLUME]',
                           ' [P_IV]']]

    dataframe = dataframe.rename(columns={' [QUOTE_DATE]': 'QUOTE_DATE',
                                          ' [EXPIRE_DATE]': 'EXPIRE_DATE',
                                          ' [UNDERLYING_LAST]': 'LAST_PRICE',
                                          ' [DTE]': 'DTE',
                                          ' [STRIKE]': 'STRIKE',
                                          ' [P_ASK]': 'P_ASK',
                                          ' [P_BID]': 'P_BID',
                                          ' [P_DELTA]': 'P_DELTA',
                                          ' [P_GAMMA]': 'P_GAMMA',
                                          ' [P_VEGA]': 'P_VEGA',
                                          ' [P_THETA]': 'P_THETA',
                                          ' [P_VOLUME]': 'P_VOLUME',
                                          ' [P_IV]': 'P_IV'
                                          })
    return dataframe


def call_df(dataframe):
    dataframe = dataframe[[' [QUOTE_DATE]', ' [EXPIRE_DATE]',
                           ' [UNDERLYING_LAST]', ' [DTE]',
                           ' [STRIKE]', ' [C_ASK]',
                           ' [C_BID]', ' [C_DELTA]',
                           ' [C_GAMMA]', ' [C_VEGA]',
                           ' [C_THETA]', ' [C_VOLUME]',
                           ' [C_IV]']]

    dataframe = dataframe.rename(columns={' [QUOTE_DATE]': 'QUOTE_DATE',
                                          ' [EXPIRE_DATE]': 'EXPIRE_DATE',
                                          ' [UNDERLYING_LAST]': 'LAST_PRICE',
                                          ' [DTE]': 'DTE',
                                          ' [STRIKE]': 'STRIKE',
                                          ' [C_ASK]': 'C_ASK',
                                          ' [C_BID]': 'C_BID',
                                          ' [C_DELTA]': 'C_DELTA',
                                          ' [C_GAMMA]': 'C_GAMMA',
                                          ' [C_VEGA]': 'C_VEGA',
                                          ' [C_THETA]': 'C_THETA',
                                          ' [C_VOLUME]': 'C_VOLUME',
                                          ' [C_IV]': 'C_IV'
                                          })
    return dataframe



