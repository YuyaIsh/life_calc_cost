import streamlit as st
import psycopg2
import datetime
import pandas as pd

persons = ["雄也","枚"]

def main():
    db = ConnectDB()
    month = datetime.datetime.now().month
    df_current_month,df_pre_month = db.select_data(month)


    st.subheader("生活費計算")

    tab_input, tab_result, tab_edit = st.tabs(["入力", "計算結果", "データ編集"])



    # データ登録
    with tab_input:
        col_date,col_item,col_price,col_person = st.columns(4)
        with col_date:
            date = st.date_input("日付")
        with col_item:
            bought_item = st.text_input("買ったもの")
        with col_price:
            price = st.text_input("価格")
        with col_person:
            paid_person = st.radio("払った人",persons,horizontal=True)

        if st.button("登録"):
            if price == "":
                st.warning("価格を入力してください。")
            else:
                try:
                    db.insert_data(date,bought_item,price,paid_person)
                except Exception as e:
                    st.error(f"データ登録に失敗しました。\n{e}")
                else:
                    st.experimental_rerun()
                st.success("データ登録に成功しました。")



    # 結果表示
    with tab_result:
        st.subheader(f"＜{month}月＞")
        result_calc_n_display(df_current_month)
        st.text("")
        st.subheader(f"＜{month-1}月＞")
        result_calc_n_display(df_pre_month)


        # ログ確認&削除
    with tab_edit:
        df_concat = pd.concat([df_current_month, df_pre_month])
        df_concat = df_concat.sort_values("日付")
        col_delete,col_df = st.columns(2)

        with col_delete:
            try:
                id = st.number_input("削除するidを入力",df_concat["id"].min(),df_concat["id"].max(),value=df_concat["id"].max())
                st.subheader(f"{df_concat[df_concat['id']==id].iat[0,2]}")
                if st.button("削除"):
                    db.delete_data(id)
                    st.experimental_rerun()
            except:
                pass

        with col_df:
            st.dataframe(df_concat.iloc[::-1],height=250)

class ConnectDB:
    def __init__(self):
        ip = st.secrets["host"]
        port = st.secrets["port"]
        dbname = st.secrets["dbname"]
        user = st.secrets["user"]
        pw = st.secrets["password"]
        self.db_info = f"host={ip} port={port} dbname={dbname} user={user} password={pw}"

        # dbname = "life_cost"
        # user = "postgres"
        # pw = "yu0712"
        # self.db_info = f"dbname={dbname} user={user} password={pw}"

    def insert_data(self,date,bought_item,price,paid_person):
        sql = f"""
            INSERT INTO pay_log (pay_log_id,date,bought_items,price,person)
            VALUES (nextval(\'pay_log_id_seq\'),\'{date}\',\'{bought_item}\',{price},\'{paid_person}\')
            """
        with psycopg2.connect(self.db_info) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

    def select_data(self,month):
        colnames =["id","日付","買い物","値段","人"]

        sql1 = f"""
            SELECT * FROM pay_log
            where extract(month from date) = \'{month}\'
            """
        with psycopg2.connect(self.db_info) as conn:
            with conn.cursor() as cur:
                cur.execute(sql1)
                data = list(cur.fetchall())  # 一行1タプルとしてリスト化
        df_current_month = pd.DataFrame(data,columns=colnames)  # データをデータフレーム化

        sql2 = f"""
            SELECT * FROM pay_log
            where extract(month from date) = \'{month-1}\'
            """
        with psycopg2.connect(self.db_info) as conn:
            with conn.cursor() as cur:
                cur.execute(sql2)
                data = list(cur.fetchall())  # 一行1タプルとしてリスト化
        df_pre_month = pd.DataFrame(data,columns=colnames)  # データをデータフレーム化

        return df_current_month,df_pre_month

    def delete_data(self,id):
        sql = f"""
            DELETE FROM pay_log
            WHERE pay_log_id = {id}
            """
        with psycopg2.connect(self.db_info) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

def result_calc_n_display(df):
    df_sum = df[["値段","人"]].groupby("人").sum()  # 各自の合計金額を計算

    total_payments = []
    for i in range(2):
        try:
            total_payments.append(df_sum.at[persons[i],"値段"])
        except KeyError:
            total_payments.append(0)

    st.subheader(f"{persons[0]}:{total_payments[0]}円 {persons[1]}:{total_payments[1]}円")  #各自の合計金額

    calculated_price = abs(total_payments[0]-total_payments[1])  # 差額算出

    # 計算結果表示
    if total_payments[0] > total_payments[1]:
        st.subheader(f" {persons[1]}が{calculated_price}円支払う","result")
    elif total_payments[0] < total_payments[1]:
        st.subheader(f" {persons[0]}が{calculated_price}円支払う","result")
    else:
        st.subheader(" 支払額は同じ")


main()