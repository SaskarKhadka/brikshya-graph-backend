import io
import matplotlib.pyplot as plt
import pandas as pd
import flask
import requests
import os
import seaborn as sns
from datetime import datetime, timedelta
plt.switch_backend('agg')

app = flask.Flask(__name__)


def create_bar_plot(data, x_label, y_label, editLabel=True):
    ax = sns.barplot(data=data, x=x_label, y=y_label)
    if editLabel:
        ax.set_xticklabels(ax.get_xticklabels(), rotation=30,
                           ha='right', fontsize=7)
    plt.tight_layout()
    bytes_image = io.BytesIO()
    plt.savefig(bytes_image, format='png')
    bytes_image.seek(0)
    return bytes_image


def history_data_prep():
    response = requests.get(os.environ.get('END_POINT'), headers={
        'x-auth-token': flask.request.headers['x-auth-token']})
    histories = list(response.json())
    df = pd.DataFrame(histories)
    df_main = pd.DataFrame(df["product"].tolist())
    df_main["quantity"] = pd.DataFrame(df["quantity"].tolist())
    df_main["date"] = df["date"]
    df_main["order_id"] = df["orderId"]
    return df_main


@app.route('/', methods=['GET'])
def say_hi():
    return "<h1>Hi...</h1>"


# calculate overall statistics
@app.route('/history/details', methods=['GET'])
def total_earnings():
    df_main = history_data_prep()
    df_main["total_amount"] = df_main["quantity"] * df_main["price"]
    total_earnings = df_main["total_amount"].sum().item()
    total_orders = len(df_main.groupby("order_id")["order_id"])
    response = {
        "total_earnings": total_earnings,
        "total_orders": total_orders
    }

    return flask.Response(
        response=flask.json.dumps(response),
        status=200,
        mimetype='application/json'
    )


@app.route('/graph/top10mostselling', methods=['GET'])
def top10mostselling():
    df_main = history_data_prep()
    df_grouped = pd.DataFrame(
        {'total sold': df_main.groupby("name")['quantity'].sum()}).reset_index().head(10)
    df_grouped.sort_values(by='total sold', inplace=True, ascending=False)
    bytes_image = create_bar_plot(
        data=df_grouped, x_label='name', y_label='total sold')
    return flask.send_file(bytes_image,
                           download_name='plot.png',
                           mimetype='image/png')


@app.route('/popular', methods=['GET'])
def popular_products():
    df_main = history_data_prep()
    df_main['date'] = df_main['date'].str.split("T", expand=True)[0]
    df_grouped = pd.DataFrame(
        {'total sold': df_main.groupby(["_id", "name"])['quantity'].sum()}).reset_index()
    df_grouped.sort_values(by='total sold', inplace=True, ascending=False)
    df_grouped['date'] = pd.to_datetime(df_main['date'])
    nepal_date = (datetime.utcnow() + timedelta(hours=5,
                  minutes=45)).strftime('%Y-%m-%d')
    nepal_date = datetime.strptime(nepal_date, '%Y-%m-%d')
    nepal_date_x_days_ago = nepal_date
    total_popular = 0
    popular = None
    while total_popular < 7:
        nepal_date_x_days_ago = nepal_date_x_days_ago - timedelta(days=7)
        popular = df_grouped[df_grouped['date'] >= nepal_date_x_days_ago]
        total_popular = len(popular.index)

    response = popular.head(7).to_json(orient='records')

    return flask.Response(
        response=response,
        status=200,
        mimetype='application/json'
    )


@app.route('/graph/monthlysell', methods=['GET'])
def monthlySelling():
    df_main = history_data_prep()
    date_df = df_main["date"].str.split("-", expand=True)
    # date_df[2] = date_df[2].str.split("T", expand=True)[0]
    df_main['month_num'] = date_df[1]
    # df_main['year'] = date_df[0]
    # df_main['day'] = date_df[2]
    # df_main = df_main.astype({'month_num': 'int', 'year': 'int', 'day': 'int'})
    df_main = df_main.astype({'month_num': 'int'})
    df_grouped = pd.DataFrame(
        {'total sold': df_main.groupby("month_num")['quantity'].sum()}).reset_index()
    df_grouped.sort_values(by='month_num', inplace=True)
    df_grouped["months"] = ["Jan", "Feb", "Mar", "Apr", "May",
                            "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
    bytes_image = create_bar_plot(
        data=df_grouped, x_label='months', y_label='total sold', editLabel=False)
    return flask.send_file(bytes_image,
                           download_name='plot.png',
                           mimetype='image/png')


if __name__ == "__main__":
    app.run(debug=True)
