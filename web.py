from flask import Flask, render_template, request
import sqlite3
import json
 
app = Flask(__name__)
 
 
@app.route("/data.json")
def data():
    connection = sqlite3.connect("temperature.db")
    cursor = connection.cursor()
    cursor.execute("select strftime('%s', ts)*1000, (temperature * 9/5) + 32 from readings where ts > '2019-01-01'")
    results = cursor.fetchall()
    return json.dumps(results)
 
@app.route("/graph")
def graph():
    return render_template('graph.html')
 
 
if __name__ == '__main__':
    app.run(
    debug=True,
    threaded=True,
    host='0.0.0.0'
)
