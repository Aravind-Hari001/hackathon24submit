from flask import Flask, request, render_template
import io
import json
import re
import PyPDF2

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with io.BytesIO(pdf_file.read()) as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text:
                    text += page_text
                else:
                    print(f"Warning: No text extracted from page {page_num}")
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

def extract_information(text):
    data = {
        "CustomerRequirements": {
            "CarType": None,
            "FuelType": None,
            "Color": None,
            "DistanceTravelled": None,
            "MakeYear": None,
            "TransmissionType": None
        },
        "CompanyPoliciesDiscussed": {
            "FreeRCTransfer": None,
            "5DayMoneyBackGuarantee": None,
            "FreeRSAForOneYear": None,
            "ReturnPolicy": None
        },
        "CustomerObjections": {
            "RefurbishmentQuality": None,
            "CarIssues": None,
            "PriceIssues": None,
            "CustomerExperienceIssues": {
                "LongWaitTime": None,
                "SalespersonBehavior": None
            }
        }
    }

    patterns = {
        "CarType": r"(suv|sedan|hatchback|coupe|convertible)",
        "FuelType": r"(petrol|diesel|electric|hybrid)",
        "Color": r"(red|blue|white|black|silver|grey)",
        "DistanceTravelled": r"(\d+\s*(km|miles))",
        "MakeYear": r"(year\s*\d{4}|manufactured\s*\d{4})",
        "TransmissionType": r"(manual|automatic|cvt|dual-clutch)",
        "FreeRCTransfer": r"free rc transfer",
        "5DayMoneyBackGuarantee": r"5[-\s]day money back guarantee",
        "FreeRSAForOneYear": r"free rsa for one year",
        "ReturnPolicy": r"return policy",
        "RefurbishmentQuality": r"refurbishment quality",
        "CarIssues": r"(car issue|engine problem|mechanical issue)",
        "PriceIssues": r"(price issue|cost|expensive|overpriced)",
        "LongWaitTime": r"long wait|delay",
        "SalespersonBehavior": r"salesperson behavior|salesperson attitude"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            if key in data["CustomerRequirements"]:
                data["CustomerRequirements"][key] = match.group()
            elif key in data["CompanyPoliciesDiscussed"]:
                data["CompanyPoliciesDiscussed"][key] = match.group()
            elif key in data["CustomerObjections"]:
                if key in ["LongWaitTime", "SalespersonBehavior"]:
                    data["CustomerObjections"]["CustomerExperienceIssues"][key] = match.group()
                else:
                    data["CustomerObjections"][key] = match.group()

    return data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        combined_text = ""

        files = request.files.getlist('files')
        for file in files:
            if allowed_file(file.filename):
                if file.filename.endswith('.pdf'):
                    combined_text += extract_text_from_pdf(file)
                elif file.filename.endswith('.txt'):
                    combined_text += file.read().decode('utf-8')

        textarea_input = request.form.get('textarea_input')
        if textarea_input:
            combined_text += textarea_input

        combined_text = clean_text(combined_text)

        json_data = extract_information(combined_text)
        json_output = json.dumps(json_data, indent=4)

        return render_template('result.html', text_output=json_output)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
