from flask import Flask, render_template
import scrape_mars
import pymongo

# create instance of Flask app
app = Flask(__name__)

client = pymongo.MongoClient("mongodb://localhost:27017/mars_db")
db = client.get_database()


# create route that renders index.html template
@app.route("/")
def index():
    mars_data = db.mars_facts.find_one()
    # mars_data = mars_dict
    return render_template("index.html", mars_data = mars_data)

@app.route("/hemisphere")
def hemisphere():
    mars_data = db.mars_facts.find_one()
    return render_template("hemisphere.html", mars_data = mars_data)

@app.route("/scrape")
def scrape():
    scrape_mars.scrape()
    return "New Data Scrapped"

if __name__ == "__main__":
    app.run(debug=True)