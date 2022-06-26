import pyodbc
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=./log/msc.accdb;'
)
connection = pyodbc.connect(conn_str)
cursor = connection.cursor()

sql = "ALTER TABLE state ADD {} {} NULL"
lane_column = {
    "distanceToLane": "Real",
    "numTrayMovingForLane": "int",
    "numTrayAsgnToLane": "int",
    "numTray_InStation": "int",
    "numTray_OutStation": "int",
    "waitingTime_InLift": "Real",
    "waitingTime_OutLift": "float"
}
floor_column = {
    "numTray_InBuffer": "int",
    "numTray_OutBuffer": "int",
    "waitingTime_Shuttle": "Real",
    "numCommand_Shuttle": "int"
}
for lane in range(1, 5):
    for key in lane_column:
        _sql = sql.format(key + "_{}".format(lane), lane_column[key])
        cursor.execute(_sql)
    for floor in range(1, 5):
        for key in floor_column:
            _sql = sql.format(key + "_{}_{}".format(lane, floor), floor_column[key])
            cursor.execute(_sql)

cursor.commit()