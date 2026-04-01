from flask import Flask, render_template_string, request
import PyPDF2
import re

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PhonePe Statement Analyzer</title>
</head>
<body style="font-family: Arial; text-align: center; margin-top: 50px;">

    <h2>Upload PhonePe Statement</h2>

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required><br><br>

        <input type="password" name="password" placeholder="Enter PDF Password (if any)"><br><br>

        <button type="submit">Analyze</button>
    </form>

    <br>

    {% if result %}
        <h3>Result</h3>
        <p>Total Credit: ₹{{result.credit}}</p>
        <p>Total Debit: ₹{{result.debit}}</p>
        <p>Highest Transaction: ₹{{result.highest}}</p>
    {% endif %}

    {% if error %}
        <p style="color:red;">{{error}}</p>
    {% endif %}

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files.get("file")
        password = request.form.get("password")

        if not file:
            return render_template_string(HTML, error="No file uploaded")

        try:
            reader = PyPDF2.PdfReader(file)

            # Handle password
            if reader.is_encrypted:
                if password:
                    reader.decrypt(password)
                else:
                    return render_template_string(HTML, error="PDF is password protected. Enter password.")

            text = ""

            for page in reader.pages:
                text += page.extract_text()

            # Extract amounts like 123.45 or 1,234.56
           lines = text.split("\n")

amounts = []

for line in lines:
    match = re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', line)
    for m in match:
        try:
            amounts.append(float(m.replace(",", "")))
        except:
            pass

            if not amounts:
                return render_template_string(HTML, error="No transactions found")

            total_credit = sum(a for a in amounts if a > 0)
            total_debit = sum(a for a in amounts if a < 0)
            highest = max(amounts)

            result = {
                "credit": round(total_credit, 2),
                "debit": round(abs(total_debit), 2),
                "highest": round(highest, 2)
            }

            return render_template_string(HTML, result=result)

        except Exception as e:
            return render_template_string(HTML, error=str(e))

    return render_template_string(HTML)

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
