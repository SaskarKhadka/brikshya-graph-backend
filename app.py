import io
import matplotlib.pyplot as plt
import pandas as pd
import flask
import requests
import os
import seaborn as sns
plt.switch_backend('agg')

app = flask.Flask(__name__)


@app.route('/', methods=['GET'])
def say_hi():
    return "<h1>Hi...</h1>"


@app.route('/graph', methods=['GET'])
def get_graph():
    response = requests.get(os.environ.get('END_POINT'), headers={
        'x-auth-token': flask.request.headers['x-auth-token']})
    histories = list(response.json())
    df = pd.DataFrame(histories)
    df_main = pd.DataFrame(df["product"].tolist())
    df_2 = pd.DataFrame(df["_id"])
    df_main["historyId"] = df_2
    df_grouped = (df_main.groupby("name").count())
    df_grouped.reset_index(inplace=True)
    sns.countplot(x='name', data=df_main)
    bytes_image = io.BytesIO()
    plt.savefig(bytes_image, format='png')
    bytes_image.seek(0)
    return flask.send_file(bytes_image,
                           download_name='plot.png',
                           mimetype='image/png')


if __name__ == "__main__":
    app.run(debug=True)
