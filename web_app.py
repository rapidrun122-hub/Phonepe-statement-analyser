from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

# Simple UI (no separate HTML file needed)
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Statement Analyzer</title>
</head>
<body>
    <h2>Upload PhonePe Statement</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Analyze</button>
    </form>

    {% if result %}
        <h3>Results:</h3>
        <p>Total Credit: {{ result.credit }}</p>
        <p>Total Debit: {{ result.debit }}</p>
        <p>Highest Transaction: {{ result.highest }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        file = request.files["file"]

        if file:
            content = file.read().decode("utf-8").splitlines()

            total_credit = 0
            total_debit = 0
            highest = 0

            for line in content:
                parts = line.split(",")

                for item in parts:
                    item = item.strip()

                    if item.replace(".", "", 1).isdigit():
                        amount = float(item)

                        if amount > highest:
                            highest = amount

                        if "credit" in line.lower():
                            total_credit += amount
                        else:
                            total_debit += amount

            result = {
                "credit": round(total_credit, 2),
                "debit": round(total_debit, 2),
                "highest": round(highest, 2)
            }

    return render_template_string(HTML, result=result)


# 🔥 IMPORTANT FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
