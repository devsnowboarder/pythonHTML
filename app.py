from flask import Flask, render_template, request
import json



app = Flask(__name__)

def get_standard_deduction(age):
    """Calculates standard deduction based on age."""
    base_deduction = 16100
    if age >= 65:
        # Applies senior bonuses only if age is 65 or older
        base_deduction += 6000 + 2050
    return base_deduction


def calculate_taxes(user_age, yearly_income, social_security):
    """Handles all IRS tax logic and returns a dictionary of calculated values."""

    tier1_under_64_taxable = 12400 * 0.10
    tier1_base = 12400
    tier2_base = 50400

    total_deduction = get_standard_deduction(user_age)
    social_security_tax = social_security / 2

    initial_income = yearly_income + social_security
    income_part1 = yearly_income
    provisional_income = yearly_income + social_security_tax

    # Default fallbacks
    adjusted_gross_income = provisional_income
    combined_income = yearly_income
    federal_taxable_income = 0.0
    federal_tax = 0.0

    # Tax logic routing
    if provisional_income <= 40000:
        adjusted_gross_income = initial_income
        combined_income = initial_income
        federal_taxable_income = max(0, adjusted_gross_income - total_deduction)
        federal_tax = 0.0

    elif provisional_income <= 74000 and user_age >= 65 and social_security != 0:
        combined_income = yearly_income + social_security_tax
        tier1 = 4500
        tier2 = (combined_income - 34000) * 0.85
        taxable_social_security = min(tier1 + tier2, 33595)  # Cap at IRS max

        adjusted_gross_income = yearly_income + taxable_social_security
        federal_taxable_income = max(0, adjusted_gross_income - total_deduction)

        first_part = tier1_base * 0.10
        if federal_taxable_income < 59000:
            second_part = (federal_taxable_income - tier1_base) * 0.12
            federal_tax = first_part + second_part
        else:
            second_part = (tier2_base - 12401) * 0.12
            federal_tax = ((federal_taxable_income - tier2_base) * 0.22) + first_part + second_part

    elif provisional_income < 60000 and user_age <= 64 and social_security > 0:
        combined_income = social_security_tax + yearly_income
        initial_federal_tax = 4500 + (combined_income - 34000) * 0.85
        adjusted_gross_income = yearly_income + initial_federal_tax
        federal_taxable_income = max(0, adjusted_gross_income - total_deduction)

        tier2_tax = (federal_taxable_income - tier1_base) * 0.12
        federal_tax = 1240 + tier2_tax

    elif provisional_income >= 60000 and user_age <= 64 and social_security > 0:
        adjusted_gross_income = yearly_income + 30600
        federal_taxable_income = max(0, adjusted_gross_income - total_deduction)

        tier2_tax = (54000 - tier1_base) * 0.12
        tier3 = (federal_taxable_income - 50400) * 0.22
        federal_tax = tier1_under_64_taxable + tier2_tax + tier3

    else:
        # Zero social security fallback
        federal_taxable_income = max(0, yearly_income - total_deduction)
        tier1 = tier1_base * 0.10

        if yearly_income > 74000:
            tier2 = (50400 - 12400) * 0.12
            tier3 = (federal_taxable_income - 50401) * 0.22
            federal_tax = tier1 + tier2 + tier3
        else:
            tier2 = (federal_taxable_income - 12401) * 0.12
            federal_tax = tier1 + tier2

    return {
        "initial_income": initial_income,
        "income_part1": income_part1,
        "social_security_tax": social_security_tax,
        "adjusted_gross_income": adjusted_gross_income,
        "combined_income": combined_income,
        "total_deduction": total_deduction,
        "federal_taxable_income": federal_taxable_income,
        "federal_tax": federal_tax
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('form.html')

    if request.method == 'POST':
        # 1. Safely parse inputs
        try:
            user_name = request.form.get('first_name', 'Guest')
            user_age = int(request.form.get('age', 0))
            yearly_income = float(request.form.get('income', 0))
            social_security = float(request.form.get('ssn_income', 0))

        except ValueError:
            return "Invalid form input. Please enter valid numbers.", 400

        # 2. Calculate Taxes
        tax_data = calculate_taxes(user_age, yearly_income, social_security)

        # Add user details to the dictionary so it can be passed to the template
        tax_data["user_name"] = user_name
        tax_data["user_age"] = user_age

        # 3. Print to terminal (Optional, good for debugging)
        for key, value in tax_data.items():
            print(f"{key.replace('_', ' ').title():.<25} {value}")

        # 4. Save to JSON
        filename = f"{user_name}_tax_data.json"
        with open(filename, "w") as data_file:
            json.dump(tax_data, data_file, indent=4)

        rendered_html = render_template('result.html', **tax_data)



        # 5. Render Template (We use **tax_data to unpack the dictionary into variables)
        return render_template('result.html', **tax_data)


if __name__ == '__main__':
    app.run(debug=True)