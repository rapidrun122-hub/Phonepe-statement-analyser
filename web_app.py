from flask import Flask, request, render_template_string
import fitz
from pypdf import PdfReader, PdfWriter

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
    <input type="file" name="file" required><br><br>

    <input type="password" name="password" placeholder="Enter PDF password (if any)"><br><br>

    <p style="font-size:12px;color:gray;">
    🔒 Password is your registered PhonePe mobile number
    </p><br>

    <button type="submit">Analyze</button>
</form>

{% if result %}
<hr>
<h3>Result</h3>
<p>💰 Credit: {{result.credit}}</p>
<p>💸 Debit: {{result.debit}}</p>
<p>📉 Spent: {{result.spent}}</p>
<p>👤 Top: {{result.person}}</p>
<p>💵 Amount: {{result.amount}}</p>
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
        password = request.form.get("password")

        file.save("temp.pdf")

        # 🔓 Handle password protected PDF
        reader = PdfReader("temp.pdf")

        if reader.is_encrypted:
            if not password:
                return "This PDF is password protected ❌ Enter password"

            if reader.decrypt(password) == 0:
                return "Wrong password ❌"

            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            with open("unlocked.pdf", "wb") as f:
                writer.write(f)

            pdf_path = "unlocked.pdf"
        else:
            pdf_path = "temp.pdf"

        # 📄 Read PDF using fitz
        total_credit = 0
        total_debit = 0
        people = {}

        doc = fitz.open(pdf_path)

        for page in doc:
            lines = page.get_text().split("\\n")

            for i in range(len(lines)):
                try:
                    if "DEBIT" in lines[i]:
                        amount = float(lines[i+1].replace("₹","").replace(",",""))
                        name = lines[i+2].replace("Paid to","").strip()

                        total_debit += amount
                        people[name] = people.get(name, 0) + amount

                    elif "CREDIT" in lines[i]:
                        amount = float(lines[i+1].replace("₹","").replace(",",""))
                        total_credit += amount

                except:
                    continue

        doc.close()

        top = max(people, key=people.get) if people else "None"

        result = {
            "credit": round(total_credit, 2),
            "debit": round(total_debit, 2),
            "spent": round(total_debit, 2),
            "person": top,
            "amount": round(people.get(top, 0), 2)
        }

    return render_template_string(HTML, result=result)


if __name__ == "__main__":
    app.run()
