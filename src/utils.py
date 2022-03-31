import pandas as pd

from .database import crud


def get_house_data(db, date_str):
    def change(x):
        if isinstance(x, str):
            room = x.split("室")[0]
            if len(room) == 1 and room in "12345":
                return int(room)
            return 6
        return 0

    sql = crud.getHouseStatement(db, date_str)
    df = pd.read_sql(sql, db.bind)
    if df.empty:
        return "[]"
    columns = ["经纬度", "小区", "面积", "总价", "均价", "房屋户型", "网址"]
    df.columns = columns
    df.sort_values(by="总价", ascending=False, inplace=True)
    df["经度"] = df["经纬度"].map(lambda x: x.split(",")[0])
    df["纬度"] = df["经纬度"].map(lambda x: x.split(",")[1])
    df["地址"] = df[["经度", "纬度", "小区"]].apply(
        lambda x: "%s,%s,'%s'" % (x["经度"], x["纬度"], x["小区"]), axis=1
    )
    df["信息"] = df[["房屋户型", "面积", "总价"]].apply(
        lambda x: "%s\t%s平米\t%s万" % (x["房屋户型"], x["面积"], x["总价"]), axis=1
    )
    df_group = (
        df.groupby("地址")
        .agg(
            {
                "信息": lambda x: ",".join(map(lambda y: '"%s"' % y, x)),
                "网址": lambda x: ",".join(map(lambda y: '"%s"' % y, x)),
            }
        )
        .reset_index()
    )
    df_house = pd.merge(left=df[["地址", "总价", "房屋户型"]], right=df_group, on="地址")
    df_house["房屋户型"] = df_house["房屋户型"].map(change)
    price_df = df_house.apply(
        lambda x: "[%s,%s,%s,[%s],[%s]]"
        % (x["地址"], x["总价"], x["房屋户型"], x["信息"], x["网址"]),
        axis=1,
    )
    data_str = "[" + ",".join(price_df) + "]"
    return data_str
