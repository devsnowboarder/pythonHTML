from flask import Flask, render_template, request
import json
import pprint

app = Flask(__name__)


def get_standard_deduction(age):
    """Calculates standard deduction based on age."""
    base_deduction = 16100
    if age >= 65:
        # Applies senior bonuses only if age is 65 or older
        base_deduction += 6000 + 2050
    return base_deduction


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('form.html')

    if request.method == 'POST':
        # 1. Safely parse inputs, converting to numbers immediately
        try:
            user_name = request.form.get('first_name', 'Guest')
            user_age = int(request.form.get('age', 0))
            yearly_income = float(request.form.get('income', 0))
            social_security = float(request.form.get('ssn_income', 0))
        except ValueError:
            return "Invalid form input. Please enter valid numbers.", 400

        tax_fields = {
            "Name": "user_name",
            "Age": "user_age",
            "Initial Income": "initial_income",
            "Income_part1": "income_part1",
            "Social Security tax": "social_security_tax",
            "Adjusted Gross Income": "adjusted_gross_income",
            "Combined Income": "combined_income",
            "Total Deduction": "total_deduction",
            "Federal Taxable Income": "federal_taxable_income",
            "Federal Tax": "federal_tax"
        }

        tier1_under_64_taxable = 12400 * .10
        tier1_base = 12400
        tier2_base = 50400
        # 2. Initialize default values to prevent UnboundLocalError crashes
        # social_security_tax = 0.0
        combined_income = yearly_income
        total_deduction = get_standard_deduction(user_age)
        # federal_taxable_income = 0.0
        # federal_tax = 0.0
        social_security_tax = social_security / 2

        # 3. Base calculations
        initial_income = yearly_income + social_security
        income_part1 = yearly_income
        provisional_income = yearly_income + (social_security / 2)
        adjusted_gross_income = provisional_income  # Default fallback

        # 4. Tax logic routing
        if provisional_income <= 40000:
            federal_tax = 0.0
            adjusted_gross_income = initial_income
            combined_income = initial_income
            federal_taxable_income = max(0, adjusted_gross_income - total_deduction)

        elif provisional_income <= 74000 and user_age >= 65 and social_security != 0:
            social_security_tax = social_security / 2
            combined_income = yearly_income + social_security_tax
            tier1 = 4500
            tier2 = (combined_income - 34000) * 0.85
            print(" Tier 2 ", tier2)
            taxable_social_security = tier1 + tier2
            print(" Taxable social Security ", taxable_social_security)
            if taxable_social_security > 34000:
                taxable_social_security = 33595  # max social security tax by IRS

            adjusted_gross_income = yearly_income + taxable_social_security
            print(" Adjust income ", adjusted_gross_income)
            federal_taxable_income = adjusted_gross_income - total_deduction
            print(" federal Taxable income ", federal_taxable_income)
            first_part = tier1_base * 0.10  # IRS first part standard
            if federal_taxable_income < 59000:
                second_part = (federal_taxable_income - tier1_base) * 0.12
                federal_tax = first_part + second_part  # final taxes user have to pay
            else:
                second_part = (tier2_base - 12401) * .12
                # final taxes user have to pay
                federal_tax = ((federal_taxable_income - tier2_base)) * .22 + first_part + second_part
        elif provisional_income < 60000 and user_age <= 64 and social_security > 0:

            combined_income = social_security_tax + yearly_income
            initial_federal_tax = 4500 + (combined_income - 34000) * 0.85
            adjusted_gross_income = yearly_income + initial_federal_tax
            federal_taxable_income = adjusted_gross_income - total_deduction
            tier2_tax = (federal_taxable_income - tier1_base) * 0.12
            federal_tax = 1240 + tier2_tax
            print(" Federal Tax income ", federal_taxable_income)
        elif provisional_income >= 60000 and user_age <= 64 and social_security > 0:
            # csocial_security_tax = social_security / 2
            # (combined income -34000) * .85
            # since 33,400 will be  greater than 30,600
            # IRS Max is 30,600
            # 30600 *.85
            adjusted_gross_income = yearly_income + 30600  # 30600 is set by IRS
            federal_taxable_income = adjusted_gross_income - total_deduction
            # 5400 is set by IRS
            # 50400 set by IRS
            tier2_tax = (54000 - tier1_base) * 0.12
            tier3 = (federal_taxable_income - 50400) * .22
            federal_tax = tier1_under_64_taxable + tier2_tax + tier3

        else:  # zero social security , 401K income from 401k
            # Fallback for inputs that don't meet any of the strict criteria above
            print(" Social Security  = 0")

            print(" Fed Deduction ", total_deduction)

            federal_taxable_income = yearly_income - total_deduction
            print(" Federal Taxable ", federal_taxable_income)

            tier1 = tier1_base * .10
            if yearly_income > 74000:
                tier2 = (50400 - 12400) * .12
                print(" Tier 2 ", tier2)
                tier3 = (federal_taxable_income - 50401) * .22
                print(" Tier 3 ", tier3)
                federal_tax = tier1 + tier2 + tier3  # 900 is phase-out  for now
            else:
                tier2 = (federal_taxable_income - 12401) * .12
                federal_tax = tier1 + tier2
        print(f" Total Federal Tax {federal_tax:.2f}")
        # 5. Cleaned up HTML Output

        tax_data_dict = {
            "user_name": user_name,
            "user_age": user_age,
            "initial_income": initial_income,
            "income_part1": income_part1,
            "social_security_tax": social_security_tax,
            "adjusted_gross_income": adjusted_gross_income,
            "combined_income": combined_income,
            "total_deduction": total_deduction,
            "federal_taxable_income": federal_taxable_income,
            "federal_tax": federal_tax
        }
        print(f" Total Federal Tax {federal_tax:.2f}")
        filename = f"{user_name}_tax_data.json"
        with open(filename, "w") as data_file:
            json.dump(tax_data_dict, data_file, indent=4)

        fileName = user_name + "_tax_data.json"
        filename = fileName

        with open(filename, "r") as file:
            # 3. Load the data into a new Python dictionary
            saved_tax_data = json.load(file)

        # --- You can now use 'saved_tax_data' just like a normal dictionary ---

        # Example: Print the whole dictionary

        for label, key in tax_fields.items():
            # {label:.<25} pads the label with dots up to 25 characters
            print(f"{label:.<25} {saved_tax_data[key]}")

        html_response = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    @page {{
        size: A4;
        margin: 15mm 12mm;
        background-color: #faf8f5;
    }}
    body {{
        margin: 0;
        padding: 0;
        background-color: #faf8f5;
        font-family: system-ui, -apple-system, sans-serif;
    }}
    *, *::before, *::after {{ 
        box-sizing: border-box; 
    }}
</style>
</head>
<body>

<div style="max-width: 600px; margin: 0 auto; padding: 24px; background: #ffffff; border-radius: 12px; border: 10px solid #2596be;">

    <!-- Header Section -->
    <h2 style="margin: 0 0 16px 0; font-size: 24px; text-align: center; color: #111827;">
        Hello, <span style="color: #2563eb;">{user_name}</span> 👋
    </h2>

    <div style="margin-bottom: 12px; text-align: center; color: #4b5563; font-size: 20px;">
        <strong>Age:</strong> {user_age} years old
    </div>

    <!-- Total Income Section -->
    <hr style="padding-top: 16px; border: none; border-top: 5px solid black;">

    <div style="font-size: 24px; text-align: center; font-weight: 700; color: #000000; margin-bottom: 24px; text-transform: uppercase; letter-spacing: 0.05em;">
        Total Income
    </div>

    <div style="padding-top: 16px; font-size: 20px; font-weight: 700; color: #000000;">
        <strong>Total Annual Income..............</strong> ${initial_income:,.2f}
    </div><br>

    <hr style="padding-top: 16px; border: none; border-top: 5px solid black;">

    <!-- Income Details Table -->
    <table style="width: 100%; border-collapse: collapse; margin-top: 16px; margin-bottom: 16px; font-size: 18px;">
        <thead>
            <tr style="border-bottom: 2px solid #000000; text-align: left;">
                <th style="padding: 8px 0; color: #111827; font-weight: 700;">Income Details</th>
                <th style="padding: 8px 0; color: #111827; text-align: right; font-weight: 700;">Amount</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom: 1px dashed #cccccc;">
                <td style="padding: 10px 0; color: #4b5563;">Part 1 Income</td>
                <td style="padding: 8px 0; color: #4b5563; text-align: right;">${income_part1:,.2f}</td>
            </tr>
            <tr style="border-bottom: 1px dashed #cccccc;">
                <td style="padding: 8px 0; color: #4b5563;">Social Security 1/2 Tax</td>
                <td style="padding: 8px 0; color: #4b5563; text-align: right;">${social_security_tax:,.2f}</td>
            </tr>
            <tr style="border-bottom: 1px dashed #cccccc;">
                <td style="padding: 8px 0; color: #4b5563;">Adjustable Gross Income</td>
                <td style="padding: 8px 0; color: #4b5563; text-align: right;">${adjusted_gross_income:,.2f}</td>
            </tr>
            <tr>
                <td style="padding: 12px 0; color: #FF2B00; font-weight: 700;">Combined Income Taxable</td>
                <td style="padding: 12px 0; color: #FF2B00; font-weight: 700; text-align: right;">${combined_income:,.2f}</td>
            </tr>
        </tbody>
    </table>

    <!-- Deduction Details Section -->
    <hr style="border: none; border-top: 5px solid black; margin-top: 24px;">

    <table style="width: 100%; border-collapse: collapse; margin-top: 16px; margin-bottom: 16px; font-size: 18px;">
        <thead>
            <tr style="border-bottom: 2px solid #000000; text-align: left;">
                <th style="padding: 8px 0; color: #111827; font-weight: 700;">Deduction Details</th>
                <th style="padding: 8px 0; color: #111827; text-align: right; font-weight: 700;">Amount</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom: 1px dashed #cccccc;">
                <td style="padding: 8px 0; color: #4b5563;">Standard Deduction</td>
                <td style="padding: 8px 0; color: #4b5563; text-align: right;">$16,100</td>
            </tr>
            <tr style="border-bottom: 1px dashed #cccccc;">
                <td style="padding: 8px 0; color: #4b5563;">Senior Temporary Deduction</td>
                <td style="padding: 8px 0; color: #4b5563; text-align: right;">$6,000</td>
            </tr>
            <tr style="border-bottom: 1px dashed #cccccc;">
                <td style="padding: 8px 0; color: #4b5563;">Senior bonus deduction 65+</td>
                <td style="padding: 8px 0; color: #4b5563; text-align: right;">$2,050</td>
            </tr>
            <tr>
                <td style="padding: 12px 0; color: #FF2B00; font-weight: 700;">Total Deduction</td>
                <td style="padding: 12px 0; color: #FF2B00; font-weight: 700; text-align: right;">${total_deduction:,.2f}</td>
            </tr>
        </tbody>
    </table>

    <div style="padding-top: 16px; margin-bottom: 12px; color: #4b5563; font-size: 18px;">
        <strong>Federal Taxable Income..................</strong> ${federal_taxable_income:,.2f}
    </div>

    <hr style="border: none; border-top: 5px solid black; padding-top: 16px;">

    <!-- Estimated Tax Section -->
    <div style="text-align: center; padding-top: 16px; margin-bottom: 12px; font-weight: 700; color: #000000; font-size: 18px;">
        <strong>Year 2026 Estimated Tax</strong> 
    </div> 

    <div style="padding-top: 16px; margin-bottom: 12px; font-weight: 700; color: #F50253; font-size: 18px;">
        <strong>Federal Estimated Tax..........</strong> ${federal_tax:,.2f}
    </div> 

    <!-- Roth IRA Section -->
    <div style="padding-top: 16px; margin-bottom: 12px; color: #155DFD; font-size: 18px;">
        <strong>Roth IRA Basic Rule</strong><br>
        <hr style="border: none; border-top: 5px solid black;">

        <div style="margin-bottom: 12px; color: #000000; font-size: 16px; margin-top: 10px;">
            For 2026, the maximum amount you can contribute to a Roth IRA is $7,500 if you are under age 50, and $8,600 if you are age 50 or older.
        </div> 

        <div style="margin-bottom: 5px; color: #000000; font-size: 16px;">
            Tax-free and penalty-free at any time. Because you already paid income tax on this money before you contributed it, you can withdraw your original contributions at any time, at any age or reason, without paying taxes or penalties.
        </div> 
    </div>

    <!-- Medicare Health Rule Section -->
    <div style="padding-top: 16px; margin-bottom: 12px; color: #155DFD; font-size: 18px;">
        <strong>Medicare Health Rule</strong>
    </div>

    <hr style="border: none; border-top: 5px solid black; padding-top: 16px;">

    <div style="margin-bottom: 5px; color: #000000; font-size: 16px;">
        Medicare Part B (Medical Insurance) Your Cost: $202.90 per month. You will pay 
        the standard Part B premium for 2026, which is $202.90. Medicare premiums are income-based, 
        and high earners pay an extra surcharge called an Income-Related Monthly Adjustment Amount (IRMAA).
        However, for 2026, that surcharge only kicks in if your Modified Adjusted Gross Income (MAGI) from two years
        ago was higher than $109,000 as a single filer (or $218,000 if filing jointly).  
    </div> 

</div>

</body>
</html>
       """
    # final_html = html_template.format(**saved_tax_data)
    # pdf_filename = f"{saved_tax_data['user_name']}_Tax_Report.pdf"
    # weasyprint.HTML(string=final_html).write_pdf(pdf_filename)

    # print(f"Success! PDF saved as: {pdf_filename}")

    return html_response


if __name__ == '__main__':
    app.run(debug=True)