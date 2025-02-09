import streamlit as st
import pandas as pd

# ------------------------------------------------
# Load the Excel file with caching for performance.
# ------------------------------------------------
@st.cache_data
def load_data():
    try:
        data = pd.read_excel("names.xlsx")
    except Exception as e:
        st.error("Error reading 'names.xlsx'. Please ensure the file exists and is valid.")
        return None

    # If the Excel file doesn't have the expected headers, assume the columns are in this order.
    if data.columns.size >= 4 and not all(col in data.columns for col in ["Name", "Frequency", "Country", "Gender"]):
        data.columns = ["Name", "Frequency", "Country", "Gender"]
    return data

df = load_data()
if df is None:
    st.stop()  # Stop if the data couldn’t be loaded.

# ------------------------------------------------
# Function to check if a given name meets the criteria.
# ------------------------------------------------
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
        for i in range(L):
            if i < len(letters) and letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    elif condition == "equal_or_higher":
        if L < numbers:
            return False
        for i in range(numbers):
            if i < len(letters) and letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    elif condition == "between":
        lower_bound, upper_bound = numbers
        if not (lower_bound <= L <= upper_bound):
            return False
        for i in range(min(len(letters), L)):
            if letters[i].strip():
                if name_lower[i] != letters[i].lower():
                    return False
        return True

    return False

# ------------------------------------------------
# Streamlit User Interface
# ------------------------------------------------
st.title("Name Search")
st.write("Search for names based on length and letter filters.")

with st.form("search_form"):
    # Select the length condition.
    condition = st.selectbox("Length Condition:", ["equal", "equal_or_lower", "equal_or_higher", "between"])

    # For the "between" condition, get min and max numbers; otherwise, get a single number.
    if condition == "between":
        lower_bound = st.number_input("Minimum letters:", min_value=1, value=1, step=1, key="lower_bound")
        upper_bound = st.number_input("Maximum letters:", min_value=1, value=5, step=1, key="upper_bound")
        numbers = (lower_bound, upper_bound)
        num_letter_inputs = upper_bound  # Use the upper bound for letter input boxes.
    else:
        num_letters = st.number_input("Number of letters:", min_value=1, value=5, step=1, key="num_letters")
        numbers = int(num_letters)
        num_letter_inputs = int(num_letters)

    # Select a gender filter.
    gender_filter = st.selectbox("Gender:", ["Any", "Boy", "Girl"])

    # Create letter input boxes dynamically.
    st.write("Enter letter filters for each position (leave blank for a wildcard):")
    letters = []
    # Use Streamlit columns to display the inputs side-by-side.
    cols = st.columns(num_letter_inputs)
    for i in range(num_letter_inputs):
        letter = cols[i].text_input(f"Letter {i+1}", value="", key=f"letter_{i}")
        letters.append(letter)

    submitted = st.form_submit_button("Search")

# ------------------------------------------------
# Perform the search and display results when the form is submitted.
# ------------------------------------------------
if submitted:
    results = []
    for _, row in df.iterrows():
        # Apply gender filter (ignoring case and extra spaces).
        if gender_filter != "Any":
            if str(row["Gender"]).strip().lower() != gender_filter.strip().lower():
                continue
        if matches_name(row["Name"], condition, numbers, letters):
            results.append(row.to_dict())

    if results:
        st.write("### Results")
        st.dataframe(pd.DataFrame(results))
    else:
        st.write("No matching names found.")
