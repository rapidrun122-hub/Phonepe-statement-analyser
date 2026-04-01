from flask import Flask, render_template_string, request
import PyPDF2
import re
import os

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
                    return render_template_string(HTML, error="PDF is password protected")

            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            if not text.strip():
                return render_template_string(HTML, error="Unable to read PDF text")

            lines = text.split("\n")

            total_credit = 0
            total_debit = 0
            highest = 0

            for line in lines:
                amounts = re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', line)

                if not amounts:
                    continue

                amount = float(amounts[-1].replace(",", ""))  # take last number

                # Smart detection (better than previous)
                if "upi" in line.lower() or "txn" in line.lower() or "to" in line.lower():
                    total_debit += amount
                else:
                    total_credit += amount

                if amount > highest:
                    highest = amount

            if total_credit == 0 and total_debit == 0:
                return render_template_string(HTML, error="No valid transactions detected")

            result = {
                "credit": round(total_credit, 2),
                "debit": round(total_debit, 2),
                "highest": round(highest, 2)
            }

            return render_template_string(HTML, result=result)

        except Exception as e:
            return render_template_string(HTML, error=str(e))

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
