from flask import Flask, request, render_template_string
import pdfplumber
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PhonePe Analyzer</title>
<style>
body {font-family: Arial; background:#f5f5f5; text-align:center;}
.container {
    background:white; padding:20px; margin:50px auto;
    width:90%; max-width:400px; border-radius:10px;
    box-shadow:0px 0px 10px gray;
}
button {
    padding:10px; background:#673ab7; color:white;
    border:none; border-radius:5px;
}
.error {color:red;}
</style>
</head>
<body>

<div class="container">
<h2>📊 PhonePe Analyzer</h2>

{% if error %}
<p class="error">{{error}}</p>
{% endif %}

<form method="post" enctype="multipart/form-data">
<input type="file" name="file"><br><br>
<input type="password" name="password" placeholder="Enter PDF password"><br><br>

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

@app.route("/", methods=["GET","POST"])
def home():
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("file")
        password = request.form.get("password")

        if file and file.filename != "":
            file.save("temp.pdf")

        try:
            reader = PdfReader("temp.pdf")
        except:
            return render_template_string(HTML, error="Upload file ❌")

        if reader.is_encrypted:
            if not password:
                return render_template_string(HTML, error="Enter password 🔒")

            if reader.decrypt(password) == 0:
                return render_template_string(HTML, error="Wrong password ❌")

            writer = PdfWriter()
            for p in reader.pages:
                writer.add_page(p)

            with open("unlocked.pdf","wb") as f:
                writer.write(f)

            pdf_path = "unlocked.pdf"
        else:
            pdf_path = "temp.pdf"

        total_credit = 0
        total_debit = 0
        people = {}

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for i in range(len(lines)):
                    if "₹" in lines[i]:
                        try:
                            amount = float(lines[i].replace("₹","").replace(",","").strip())

                            context = lines[i].lower()

                            if "paid" in context or "sent" in context:
                                total_debit += amount
                            elif "received" in context:
                                total_credit += amount

                        except:
                            continue

        result = {
            "credit": round(total_credit,2),
            "debit": round(total_debit,2),
            "spent": round(total_debit,2),
            "person": "N/A",
            "amount": 0
        }

    return render_template_string(HTML, result=result, error=error)

if __name__ == "__main__":
    app.run()
