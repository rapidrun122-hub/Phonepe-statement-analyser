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
.error {
    color: red;
}
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
    error = None

    if request.method == "POST":
        file = request.files.get("file")
        password = request.form.get("password")

        # Save file
        if file and file.filename != "":
            file.save("temp.pdf")

        # Load PDF
        try:
            reader = PdfReader("temp.pdf")
        except:
            return render_template_string(HTML, result=None, error="Please upload a file ❌")

        # Handle password
        if reader.is_encrypted:
            if not password:
                return render_template_string(
                    HTML, result=None,
                    error="🔒 This PDF is password protected. Enter password and click Analyze"
                )

            if reader.decrypt(password) == 0:
                return render_template_string(
                    HTML, result=None,
                    error="❌ Wrong password. Try again"
                )

            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            with open("unlocked.pdf", "wb") as f:
                writer.write(f)

            pdf_path = "unlocked.pdf"
        else:
            pdf_path = "temp.pdf"

        # 🔥 SMART ANALYSIS
        total_credit = 0
        total_debit = 0
        people = {}

        doc = fitz.open(pdf_path)

        for page in doc:
            lines = page.get_text().split("\\n")

            for i in range(len(lines)):
                line = lines[i]

                if "₹" in line:
                    try:
                        amount = float(line.replace("₹", "").replace(",", "").strip())

                        context = ""
                        if i > 0:
                            context += lines[i-1].lower() + " "
                        context += line.lower()
                        if i < len(lines)-1:
                            context += " " + lines[i+1].lower()

                        # Debit detection
                        if any(word in context for word in ["paid", "sent", "debit", "transfer to"]):
                            total_debit += amount

                            name = lines[i-1].replace("Paid to", "").replace("Sent to", "").strip()
                            people[name] = people.get(name, 0) + amount

                        # Credit detection
                        elif any(word in context for word in ["received", "credit", "added"]):
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

    return render_template_string(HTML, result=result, error=error)


if __name__ == "__main__":
    app.run()
