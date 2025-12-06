from flask import Flask, render_template
app = Flask(__name__)

intro = "Hæ þetta er siða um mig "

afangar = { "1":"vefhonnun",
          "2":"vefhonnun",
          "3":"vefhonnun",
          "4":"vefhonnun", }


vefhonnun = {
    1: "Foritun",
    2: "tonlist",
    3: "föt",
    4: "stæfræði"
}




@app.route('/')
def index():
    # data
    title = "Jinja"
    
   
    # sendum dictionary (user) og breytuna (title) í template
    return render_template('index.html', title=title, intro=intro, afangar=afangar)


@app.route('/siða2/')
def siða2():
    title = "Um áhugamálið mitt"
    return render_template('siða2.html', title=title, intro=intro, vefhonnun=vefhonnun)


# Client error
# This tells Flask that the status code of that page should be 404 which means not found. 
@app.errorhandler(404)
def pagenotfound(error):
    return"<h1>Sorry, page not found</h1>", 404



# Server error
@app.errorhandler(500)
def servernotfound(error):
    return "Server is down!", 500


if __name__ == '__main__':
  app.run(debug=True, use_reloader=True)  
    