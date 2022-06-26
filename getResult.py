import pandas as pd
import pyodbc
import json

# models = ["round_robin", "random", "greedy", "beamsearch1_1", "beamsearch2_1", "beamsearch4_1"]
# episodes = [1]

models = ["greedy"]
episodes = [0, 1]

filename_ = "./scenario.config"
with open(filename_, "r") as json_file:
    _order = json.load(json_file)

for model in models:
    if model == "round_robin":
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=../result/round_robin/log/msc.accdb;'
        )
    if model == "random":
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=../result/random/log/msc.accdb;'
        )
    if model == "greedy":
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=../result/greedy/log/msc.accdb;'
        )
    if model == "beamsearch1_1":
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=../result/beamsearch1_1/log/msc.accdb;'
        )
    if model == "beamsearch2_1":
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=../result/beamsearch2_1/log/msc.accdb;'
        )
    if model == "beamsearch4_1":
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=../result/beamsearch4_1/log/msc.accdb;'
        )
    connection = pyodbc.connect(conn_str)
    cursor = connection.cursor()
    for episode in episodes:
        episode_type = "same"
        episode = episode
        orders = []
        if episode >= 1:
            episode_type = "abc"
        for scenario in range(4):
            for (GDS, Order_Type) in _order[episode_type][episode % 10][scenario]:
                if Order_Type == "STORAGE":
                    orders.append(GDS)
                elif Order_Type == "RETRIEVAL":
                    continue
                else:
                    print("ERROR")


        sql_bcr = "select trayId, startAt from tray where episodeNum={} and (deviceId='C0001' or deviceId='C0026') order by trayId".format(episode)
        df_bcr = pd.read_sql(sql_bcr, connection)
        df_bcr.rename(columns={"startAt": "BCR"}, inplace=True)

        sql_lift = "select trayId, startAt from tray where episodeNum={} and device='DEVICE_TYPE.LIFT' and RIGHT(deviceId,2)='01'".format(episode)
        df_lift = pd.read_sql(sql_lift, connection)
        df_lift.rename(columns={"startAt": "Lift"}, inplace=True)

        sql_lane = "select trayId, LEFT(deviceId,3) as deveId from tray where episodeNum={} and device='DEVICE_TYPE.LIFT' and RIGHT(deviceId,2)='01'".format(episode)
        df_lane = pd.read_sql(sql_lane, connection)
        df_lane.rename(columns={"deviceId": "Lane"}, inplace=True)

        sql_cell = "select trayId, startAt from tray where episodeNum={} and device='DEVICE_TYPE.LIFT' and RIGHT(deviceId,2)='02'".format(episode)
        df_cell = pd.read_sql(sql_cell, connection)
        df_cell.rename(columns={"startAt": "Cell"}, inplace=True)

        sql_retrieval = "select trayId, startAt from tray where episodeNum={} and device='DEVICE_TYPE.RETRIEVAL'".format(episode)
        df_retrieval = pd.read_sql(sql_retrieval, connection)
        df_retrieval.rename(columns={"startAt": "Retrieval"}, inplace=True)

        df = df_bcr

        df = pd.merge(df, df_lift, how="outer", on="trayId")
        df = pd.merge(df, df_cell, how="outer", on="trayId")
        df = pd.merge(df, df_retrieval, how="outer", on="trayId")
        df = pd.merge(df, df_lane, how="outer", on="trayId")
        print(model)
        print(len(orders))
        df["GDS"] = orders

        df.to_csv("../result/{}_eposide_{}.csv".format(model, episode), index=False)