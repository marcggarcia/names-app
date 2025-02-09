from flask import Flask, request, render_template_string, redirect, url_for
from flask_babel import Babel, _
import pandas as pd
import re

app = Flask(__name__)

# Configuration for Babel
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'es']

babel = Babel(app)

@babel.localeselector
def get_locale():
    # Check if a language was passed as query parameter (?lang=es)
    lang = request.args.get('lang')
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        return lang
    # Otherwise, use best match from Accept-Language header
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

# Load the Excel file (which should contain columns: Name, Frequency, Country)
try:
    df = pd.read_excel("names.xlsx")
except Exception as e:
    raise Exception(_("Error reading 'names.xlsx'. Please ensure the file exists and is valid.")) from e

# If headers are missing, assume default names.
if df.columns.size >= 3 and not all(col in df.columns for col in ["Name", "Frequency", "Country"]):
    df.columns = ["Name", "Frequency", "Country"]

@app.route("/", methods=["GET", "POST"])
def search():
    results = None
    num_letters = ""
    letters = []      # The list of letter inputs
    condition = "exact"  # Default condition
    
    if request.method == "POST":
        num_letters = request.form.get("num_letters", "")
        condition = request.form.get("condition", "exact")
        try:
            n = int(num_letters)
        except ValueError:
            n = 0
        
        # Retrieve the letter inputs (one per position)
        letters = request.form.getlist("letters")
        # Ensure the list has exactly n items (pad with empty strings if necessary)
        if len(letters) < n:
            letters += [""] * (n - len(letters))
        elif len(letters) > n:
            letters = letters[:n]
        
        # Custom matching function
        def matches_name(name, pattern, cond, n):
            """Return True if name meets the length condition and letter pattern."""
            name = str(name)
            l = len(name)
            if cond == "exact":
                if l != n:
                    return False
                for i in range(n):
                    if pattern[i].strip() and name[i].lower() != pattern[i].lower():
                        return False
                return True
            elif cond == "less":
                if l > n:
                    return False
                for i in range(l):
                    if pattern[i].strip() and name[i].lower() != pattern[i].lower():
                        return False
                return True
            elif cond == "greater":
                if l < n:
                    return False
                for i in range(n):
                    if pattern[i].strip() and name[i].lower() != pattern[i].lower():
                        return False
                return True
            return False
        
        # Filter the DataFrame rows using the custom matching function.
        results = []
        for _, row in df.iterrows():
            if matches_name(row["Name"], letters, condition, n):
                results.append(row.to_dict())
    
    # Render the HTML template.
    # Notice all user-facing texts are wrapped in _() for translation.
    return render_template_string('''
<!DOCTYPE html>
<html lang="{{ get_locale() }}">
<head>
  <meta charset="UTF-8">
  <title>{{ _("Advanced Name Search") }}</title>
  <style>
    body {
      font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
      background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
      margin: 0;
      padding: 20px;
    }
    .container {
      max-width: 800px;
      background: #fff;
      margin: 40px auto;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    h1, h2 {
      text-align: center;
      color: #333;
    }
    form {
      margin-top: 20px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    label {
      font-weight: bold;
      display: block;
      margin-bottom: 8px;
      color: #555;
    }
    input[type="number"] {
      width: 100px;
      padding: 5px;
      font-size: 16px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    .condition-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .condition-group input[type="radio"] {
      margin-right: 5px;
    }
    #letterInputs {
      margin-top: 15px;
      text-align: center;
    }
    #letterInputs input {
      width: 45px;
      height: 45px;
      font-size: 24px;
      text-align: center;
      margin: 5px;
      border: 1px solid #bbb;
      border-radius: 4px;
      transition: border-color 0.3s;
    }
    #letterInputs input:focus {
      border-color: #007BFF;
      outline: none;
    }
    button {
      display: block;
      margin: 20px auto;
      padding: 10px 25px;
      font-size: 18px;
      background-color: #007BFF;
      color: #fff;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      transition: background-color 0.3s;
    }
    button:hover {
      background-color: #0056b3;
    }
    .results {
      margin-top: 30px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }
    table th, table td {
      border: 1px solid #ddd;
      padding: 12px;
      text-align: left;
    }
    table th {
      background-color: #f2f2f2;
    }
    .lang-switcher {
      text-align: right;
    }
    .lang-switcher a {
      margin-left: 10px;
      text-decoration: none;
      color: #007BFF;
    }
    .lang-switcher a:hover {
      text-decoration: underline;
    }
    @media (max-width: 600px) {
      #letterInputs input {
        width: 35px;
        height: 35px;
        font-size: 18px;
      }
      button {
        font-size: 16px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="lang-switcher">
      <a href="{{ url_for('search', lang='en') }}">English</a> | 
      <a href="{{ url_for('search', lang='es') }}">Español</a>
    </div>
    <h1>{{ _("Advanced Name Search") }}</h1>
    <form method="post" id="searchForm">
      <div class="form-group">
        <label for="num_letters">{{ _("Number of Letters:") }}</label>
        <input type="number" id="num_letters" name="num_letters" min="1" value="{{ num_letters if num_letters else '' }}">
      </div>
      <div class="form-group">
        <label>{{ _("Length Condition:") }}</label>
        <div class="condition-group">
          <input type="radio" name="condition" value="exact" id="cond_exact" 
            {% if condition == 'exact' %}checked{% endif %}>
          <label for="cond_exact">{{ _("Exact") }}</label>
          <input type="radio" name="condition" value="less" id="cond_less" 
            {% if condition == 'less' %}checked{% endif %}>
          <label for="cond_less">{{ _("Less than or equal") }}</label>
          <input type="radio" name="condition" value="greater" id="cond_greater" 
            {% if condition == 'greater' %}checked{% endif %}>
          <label for="cond_greater">{{ _("Greater than or equal") }}</label>
        </div>
      </div>
      <div id="letterInputs">
        <!-- Letter input boxes will be generated here -->
      </div>
      <button type="submit">{{ _("Search") }}</button>
    </form>
    
    <div class="results">
      {% if results is not none %}
        <h2>{{ _("Results") }}</h2>
        {% if results %}
          <table>
            <thead>
              <tr>
                <th>{{ _("Name") }}</th>
                <th>{{ _("Frequency") }}</th>
                <th>{{ _("Country") }}</th>
              </tr>
            </thead>
            <tbody>
              {% for row in results %}
                <tr>
                  <td>{{ row["Name"] }}</td>
                  <td>{{ row["Frequency"] }}</td>
                  <td>{{ row["Country"] }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <p style="text-align: center;">{{ _("No matching names found.") }}</p>
        {% endif %}
      {% endif %}
    </div>
  </div>
  
  <script>
    // Dynamically generate letter input boxes based on the number entered.
    function generateLetterInputs() {
      var numLetters = document.getElementById("num_letters").value;
      var container = document.getElementById("letterInputs");
      container.innerHTML = "";
      var prefilled = {{ letters|tojson|safe }};
      numLetters = parseInt(numLetters);
      if (isNaN(numLetters) || numLetters < 1) return;
      for (var i = 0; i < numLetters; i++) {
        var input = document.createElement("input");
        input.setAttribute("type", "text");
        input.setAttribute("name", "letters");
        input.setAttribute("maxlength", "1");
        if (prefilled && prefilled[i]) {
          input.value = prefilled[i];
        }
        container.appendChild(input);
      }
    }
    window.addEventListener("load", generateLetterInputs);
    document.getElementById("num_letters").addEventListener("change", generateLetterInputs);
  </script>
</body>
</html>
''', results=results, num_letters=num_letters, letters=letters, condition=condition)

if __name__ == '__main__':
    app.run(debug=True)

