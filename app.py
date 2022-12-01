import io
import matplotlib.pyplot as plt
import pandas as pd
import base64
import flask
import requests
import os
import seaborn as sns
from datetime import datetime, timedelta
plt.switch_backend('agg')

app = flask.Flask(__name__)

MONTHS = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}


def create_bar_plot(data, x, y, x_label, y_label, title='', editLabel=True):
    ax = sns.barplot(data=data, x=data[x], y=data[y])
    if editLabel:
        ax.set_xticklabels(ax.get_xticklabels(), rotation=30,
                           ha='right', fontsize=7)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.locator_params(axis="y", integer=True, tight=True)
    plt.tight_layout()
    max_val = data[y].max()
    max_val = max_val + (5 if max_val % 5 == 0 else max_val % 5)
    plt.ylim(top=max_val)
    plt.ylim(bottom=0)
    bytes_image = io.BytesIO()
    plt.savefig(bytes_image, format='png')
    bytes_image.seek(0)
    return bytes_image


def history_data_prep(user=False):
    response = None
    if (user):
        response = requests.get(os.environ.get('END_POINT_2'))
    else:
        response = requests.get(os.environ.get('END_POINT'), headers={
            'x-auth-token': flask.request.headers['x-auth-token']})
    # response.raise_for_status()
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
        {'total_sold': df_main.groupby("name")['quantity'].sum()}).reset_index().head(10)
    df_grouped.sort_values(by='total_sold', inplace=True, ascending=False)
    bytes_image = create_bar_plot(
        data=df_grouped, x='name', y='total_sold', x_label='Plants', y_label='Total Sold', title='Top 10 most selling')
    b64string = base64.b64encode(bytes_image.read())
    res = {
        "image": b64string.decode('utf8')
    }
    return flask.Response(flask.json.dumps(res),
                          status=200,
                          mimetype='application/json')


def popular_products(user=False):
    df_main = history_data_prep(user)
    df_main['date'] = df_main['date'].str.split("T", expand=True)[0]
    df_grouped = pd.DataFrame(
        {'total_sold': df_main.groupby(["_id", "name"])['quantity'].sum()}).reset_index()
    df_grouped.sort_values(by='total_sold', inplace=True, ascending=False)
    df_grouped['date'] = pd.to_datetime(df_main['date'])
    nepal_date = (datetime.utcnow() + timedelta(hours=5,
                                                minutes=45)).strftime('%Y-%m-%d')
    nepal_date = datetime.strptime(nepal_date, '%Y-%m-%d')
    nepal_date_x_days_ago = nepal_date
    total_popular = 0
    popular = None
    while total_popular < 5:
        nepal_date_x_days_ago = nepal_date_x_days_ago - timedelta(days=7)
        popular = df_grouped[df_grouped['date'] >= nepal_date_x_days_ago]
        total_popular = len(popular.index)

    return popular.head(5)


@ app.route('/graph/popular', methods=['GET'])
def popular_graph():
    response = popular_products()
    bytes_image = create_bar_plot(
        data=response, x='name', y='total_sold', x_label='Plants', y_label='Total Sold', title='Popular Products')
    b64string = base64.b64encode(bytes_image.read())
    res = {
        "image": b64string.decode('utf8')
    }
    return flask.Response(flask.json.dumps(res),
                          status=200,
                          mimetype='application/json')


@ app.route('/popular', methods=['GET'])
def popular_products_details():
    response = popular_products(True)
    response = response.to_json(orient='records')
    return flask.Response(
        response=response,
        status=200,
        mimetype='application/json'
    )


@ app.route('/graph/top10thismonth', methods=['GET'])
def top_this_month():
    df_main = history_data_prep()
    date_df = df_main["date"].str.split("-", expand=True)
    df_main['month_num'] = date_df[1]
    df_main['year_num'] = date_df[0]
    df_main = df_main.astype({'month_num': 'int', 'year_num': 'int'})
    nepal_date = (datetime.utcnow() + timedelta(hours=5,
                                                minutes=45)).strftime('%Y-%m-%d')
    nepal_date = datetime.strptime(nepal_date, '%Y-%m-%d')
    nepal_month = nepal_date.month
    nepal_year = nepal_date.year
    df_main = df_main[df_main['month_num'] == nepal_month]
    df_main = df_main[df_main['year_num'] == nepal_year]
    df_grouped = pd.DataFrame(
        {'total_sold': df_main.groupby(["name"])['quantity'].sum()}).reset_index().head(10)
    df_grouped.sort_values(by='total_sold', inplace=True, ascending=False)
    bytes_image = create_bar_plot(
        data=df_grouped, x='name', y='total_sold', x_label='Plants', y_label='Total Sold', editLabel=True, title=f'Top 10 most selling {MONTHS[nepal_month]}, {nepal_year}')
    b64string = base64.b64encode(bytes_image.read())
    res = {
        "image": b64string.decode('utf8')
    }
    return flask.Response(flask.json.dumps(res),
                          status=200,
                          mimetype='application/json')


@ app.route('/graph/month/<month>', methods=['GET'])
def data_given_month(month):
    month = int(month)
    df_main = history_data_prep()
    df_main['month_num'] = df_main["date"].str.split("-", expand=True)[1]
    df_main = df_main.astype({'month_num': 'int'})
    df_main = df_main[df_main['month_num'] == month]
    df_grouped = pd.DataFrame(
        {'total_sold': df_main.groupby(["name"])['quantity'].sum()}).reset_index()
    df_grouped.sort_values(by='total_sold', inplace=True, ascending=False)
    bytes_image = create_bar_plot(
        data=df_grouped, x='name', y='total_sold', x_label='Plants', y_label='Total Sold', editLabel=True, title=f'Items sold on {MONTHS[month]}')
    b64string = base64.b64encode(bytes_image.read())
    res = {
        "image": b64string.decode('utf8')
    }
    return flask.Response(flask.json.dumps(res),
                          status=200,
                          mimetype='application/json')


@ app.route('/graph/monthlysell', methods=['GET'])
def monthly_sell():
    df_main = history_data_prep()
    date_df = df_main["date"].str.split("-", expand=True)
    df_main['month_num'] = date_df[1]
    df_main = df_main.astype({'month_num': 'int'})
    df_grouped = pd.DataFrame(
        {'total_sold': df_main.groupby("month_num")['quantity'].sum()}).reset_index()
    df_grouped.sort_values(by='month_num', inplace=True)
    df_grouped["months"] = ["Jan", "Feb", "Mar", "Apr", "May",
                            "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
    bytes_image = create_bar_plot(
        data=df_grouped, x='months', y='total_sold', x_label='Months', y_label='Total Sold', editLabel=False, title='Total items sold each month')
    b64string = base64.b64encode(bytes_image.read())
    res = {
        "image": b64string.decode('utf8')
    }
    return flask.Response(flask.json.dumps(res),
                          status=200,
                          mimetype='application/json')


if __name__ == "__main__":
    app.run(debug=True)


# @ app.route('/graph/monthlysell', methods=['GET'])
# def monthly_selling():
#     df_main = history_data_prep()
#     df_main['date'] = pd.to_datetime(df_main['date'])
#     df_main['date'] = df_main['date'].dt.strftime('%b %d,%Y')
#     # date_df[2] = date_df[2].str.split("T", expand=True)[0]
#     df_main['month'] = df_main["date"].str.split(" ", expand=True)[0]
#     # df_main['year'] = date_df[0]
#     # df_main['day'] = date_df[2]
#     # df_main = df_main.astype({'month_num': 'int', 'year': 'int', 'day': 'int'})
#     # df_main = df_main.astype({'month_num': 'int'})
#     df_grouped = pd.DataFrame(
#         {'total_sold': df_main.groupby(["month", "name"])['quantity'].sum()}).reset_index()
#     df_grouped["max"] = df_grouped.groupby(pd.Grouper(key="month"))[
#         "total_sold"].transform("max")
#     df_grouped = df_grouped[df_grouped['total_sold'] == df_grouped['max']]
#     df_grouped.sort_values(by='month', inplace=True)
#     # df_grouped["months"] = ["Jan", "Feb", "Mar", "Apr", "May",
#     #                         "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
#     bytes_image = create_bar_plot(
#         data=df_grouped, x_label='month', y_label='total_sold', editLabel=False)
#     return flask.send_file(bytes_image,
#                            download_name='plot.png',
#                            mimetype='image/png')
