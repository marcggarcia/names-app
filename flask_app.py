from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)

# Load the Excel file which should contain four columns: Name, Frequency, Country, Gender.
try:
    df = pd.read_excel("names.xlsx")
except Exception as e:
    raise Exception("Error reading 'names.xlsx'. Please ensure the file exists and is valid.") from e

# If the Excel file doesn't have headers, assume the columns are in this order.
if df.columns.size >= 4 and not all(col in df.columns for col in ["Name", "Frequency", "Country", "Gender"]):
    df.columns = ["Name", "Frequency", "Country", "Gender"]

def matches_name(name, condition, numbers, letters):
    """
    Returns True if the given name meets the length condition and letter filters.
    
    Parameters:
      - name: candidate name (string)
      - condition: one of "equal", "equal_or_lower", "equal_or_higher", "between"
      - numbers: an integer (for non-between) or a tuple (lower_bound, upper_bound) for "between"
      - letters: list of letter filters (blank entries act as wildcards)
    """
    name = str(name)
    L = len(name)
    name_lower = name.lower()
    
    if condition == "equal":
        if L != numbers:
            return False
        for i in range(numbers):
            if i < len(letters) and letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    elif condition == "equal_or_lower":
        if L > numbers:
            return False
        # Only check positions that exist in the name.
        for i in range(L):
            if i < len(letters) and letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    elif condition == "equal_or_higher":
        if L < numbers:
            return False
        # Check the first 'numbers' positions.
        for i in range(numbers):
            if i < len(letters) and letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    elif condition == "between":
        lower_bound, upper_bound = numbers
        if not (lower_bound <= L <= upper_bound):
            return False
        # Check only for positions that exist.
        for i in range(min(len(letters), L)):
            if letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    return False

@app.route("/", methods=["GET", "POST"])
def search():
    results = None  # Indicates that no search has been performed yet.
    # Default form field values.
    condition = "equal"
    num_letters = ""
    num_letters_lower = ""
    num_letters_upper = ""
    letters = []      # Letter filters.
    gender_filter = "Any"  # Default: no gender filtering

    if request.method == "POST":
        # Retrieve the length condition and gender filter from the form.
        condition = request.form.get("condition", "equal")
        gender_filter = request.form.get("gender", "Any")
        
        # Determine numeric values and number of letter boxes.
        if condition == "between":
            num_letters_lower = request.form.get("num_letters_lower", "")
            num_letters_upper = request.form.get("num_letters_upper", "")
            try:
                lower_bound = int(num_letters_lower)
                upper_bound = int(num_letters_upper)
            except ValueError:
                lower_bound, upper_bound = 0, 0
            numbers = (lower_bound, upper_bound)
            num_letter_inputs = upper_bound  # Use upper bound for letter boxes.
        else:
            num_letters = request.form.get("num_letters", "")
            try:
                num_int = int(num_letters)
            except ValueError:
                num_int = 0
            numbers = num_int
            num_letter_inputs = num_int

        # Retrieve the letter filters from the form.
        letters = request.form.getlist("letters")
        if len(letters) < num_letter_inputs:
            letters += [""] * (num_letter_inputs - len(letters))
        elif len(letters) > num_letter_inputs:
            letters = letters[:num_letter_inputs]

        # Filter rows from the DataFrame.
        results = []
        for _, row in df.iterrows():
            # Apply gender filter if set (ignore case and leading/trailing spaces).
            if gender_filter != "Any":
                if str(row["Gender"]).strip().lower() != gender_filter.strip().lower():
                    continue
            # Check name condition.
            if matches_name(row["Name"], condition, numbers, letters):
                results.append(row.to_dict())

    # Render the HTML template.
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Name Search</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f0f0f0;
      padding: 20px;
      margin: 0;
    }
    .container {
      max-width: 800px;
      margin: auto;
      background: #fff;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1, h2 {
      text-align: center;
      color: #333;
    }
    label {
      display: inline-block;
      margin-bottom: 10px;
      color: #555;
    }
    input[type="number"], select {
      width: 100px;
      padding: 5px;
      font-size: 16px;
      margin-right: 10px;
    }
    #letterInputs input {
      width: 40px;
      height: 40px;
      font-size: 24px;
      text-align: center;
      margin: 5px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    button {
      display: block;
      padding: 10px 20px;
      font-size: 16px;
      background: #007BFF;
      color: #fff;
      border: none;
      border-radius: 4px;
      margin: 20px auto;
      cursor: pointer;
    }
    button:hover {
      background: #0056b3;
    }
    .results {
      margin-top: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }
    table th, table td {
      border: 1px solid #ddd;
      padding: 10px;
      text-align: left;
    }
    table th {
      background: #f8f8f8;
    }
  </style>
</head>
<body>
<div class="container">
  <h1>Name Search</h1>
  <form method="post" id="searchForm">
    <div style="margin-bottom: 10px;">
      <label for="condition">Length Condition:</label>
      <select id="condition" name="condition" onchange="updateNumberInputs()">
        <option value="equal" {% if condition == 'equal' %}selected{% endif %}>Equal</option>
        <option value="equal_or_lower" {% if condition == 'equal_or_lower' %}selected{% endif %}>Equal or Lower</option>
        <option value="equal_or_higher" {% if condition == 'equal_or_higher' %}selected{% endif %}>Equal or Higher</option>
        <option value="between" {% if condition == 'between' %}selected{% endif %}>Between</option>
      </select>
      <span id="numberInputs">
        {% if condition == 'between' %}
          <input type="number" id="num_letters_lower" name="num_letters_lower" min="1" placeholder="Min" value="{{ num_letters_lower if num_letters_lower else '' }}"> 
          <input type="number" id="num_letters_upper" name="num_letters_upper" min="1" placeholder="Max" value="{{ num_letters_upper if num_letters_upper else '' }}">
        {% else %}
          <input type="number" id="num_letters" name="num_letters" min="1" value="{{ num_letters if num_letters else 5 }}">
        {% endif %}
      </span>
    </div>
    <div style="margin-bottom: 10px;">
      <label for="gender">Gender:</label>
      <select id="gender" name="gender">
        <option value="Any" {% if gender_filter == "Any" or not gender_filter %}selected{% endif %}>Any</option>
        <option value="Boy" {% if gender_filter == "Boy" %}selected{% endif %}>Boy</option>
        <option value="Girl" {% if gender_filter == "Girl" %}selected{% endif %}>Girl</option>
      </select>
    </div>
    <div id="letterInputs" style="margin-top: 15px;">
      <!-- The letter input boxes will be dynamically generated here -->
    </div>
    <button type="submit">Search</button>
  </form>
  
  <div class="results">
    {% if results is not none %}
      <h2>Results</h2>
      {% if results %}
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Frequency</th>
              <th>Country</th>
              <th>Gender</th>
            </tr>
          </thead>
          <tbody>
            {% for row in results %}
              <tr>
                <td>{{ row["Name"] }}</td>
                <td>{{ row["Frequency"] }}</td>
                <td>{{ row["Country"] }}</td>
                <td>{{ row["Gender"] }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p>No matching names found.</p>
      {% endif %}
    {% endif %}
  </div>
</div>

<script>
  // Update the numeric input fields based on the selected condition.
  function updateNumberInputs() {
    var condition = document.getElementById("condition").value;
    var numberInputsSpan = document.getElementById("numberInputs");
    if (condition === "between") {
      numberInputsSpan.innerHTML = '<input type="number" id="num_letters_lower" name="num_letters_lower" min="1" placeholder="Min"> ' +
                                   '<input type="number" id="num_letters_upper" name="num_letters_upper" min="1" placeholder="Max">';
    } else {
      numberInputsSpan.innerHTML = '<input type="number" id="num_letters" name="num_letters" min="1" value="5">';
    }
    generateLetterInputs(); // Regenerate letter boxes
  }
  
  // Dynamically generate letter input boxes based on the number specified.
  function generateLetterInputs() {
    var condition = document.getElementById("condition").value;
    var numLetters;
    if (condition === "between") {
      // Use the upper value (if available)
      numLetters = document.getElementById("num_letters_upper").value;
    } else {
      numLetters = document.getElementById("num_letters").value;
    }
    var container = document.getElementById("letterInputs");
    container.innerHTML = ""; // Clear previous inputs

    var prefilled = {{ letters|tojson|safe }};
    numLetters = parseInt(numLetters);
    if (isNaN(numLetters) || numLetters < 1) {
      return;
    }
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
  document.addEventListener("change", function(e) {
    if (e.target.id === "num_letters" || e.target.id === "num_letters_upper") {
      generateLetterInputs();
    }
  });
</script>
</body>
</html>
''', results=results, condition=condition, num_letters=num_letters, num_letters_lower=num_letters_lower, num_letters_upper=num_letters_upper, letters=letters, gender_filter=gender_filter)

if __name__ == '__main__':
    app.run(debug=True)
