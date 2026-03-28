from flask import Flask, request, render_template_string
import fitz

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PhonePe Analyzer</title>
<style>
body {
    font-family: Arial;
    background: #f5f5f5;
    text-align: center;
}
.container {
    background: white;
    padding: 20px;
    margin: 50px auto;
    width: 90%;
    max-width: 400px;
    border-radius: 10px;
    box-shadow: 0px 0px 10px gray;
}
button {
    padding: 10px;
    background: #673ab7;
    color: white;
    border: none;
    border-radius: 5px;
}
</style>
</head>
<body>

<div class="container">
<h2>📊 PhonePe Analyzer</h2>

<form method="post" enctype="multipart/form-data">
    <input type="file" name="file"><br><br>
    <button type="submit">Analyze</button>
</form>

{% if result %}
<hr>
<h3>Result</h3>
<p>💰 Credit: {{result.credit}}</p>
<p>💸 Debit: {{result.debit}}</p>
<p>🔥 Spent: {{result.spent}}</p>
<p>👤 Top: {{result.person}}</p>
<p>🏆 Amount: {{result.amount}}</p>
{% endif %}

</div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        file = request.files["file"]
        file.save("temp.pdf")

        total_credit = 0
        total_debit = 0
        people = {}

        doc = fitz.open("temp.pdf")

        for page in doc:
            lines = page.get_text().split("\n")

            for i in range(len(lines)):
                try:
                    if lines[i].strip() == "DEBIT":
                        amount = float(lines[i+1].replace("₹","").replace(",",""))
                        name = lines[i+2].replace("Paid to","").strip()

                        total_debit += amount
                        people[name] = people.get(name,0) + amount

                    elif lines[i].strip() == "CREDIT":
                        amount = float(lines[i+1].replace("₹","").replace(",",""))
                        total_credit += amount

                except:
                    continue

        doc.close()

        top = max(people, key=people.get) if people else "None"

        result = {
            "credit": round(total_credit,2),
            "debit": round(total_debit,2),
            "spent": round(total_debit,2),
            "person": top,
            "amount": round(people.get(top,0),2)
        }

    return render_template_string(HTML, result=result)

app.run(host="0.0.0.0", port=5000, debug=True)