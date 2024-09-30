from flask import Flask, render_template, request
import pandas as pd
from fuzzywuzzy import fuzz, process
import phonetics
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import numpy as np

app = Flask(__name__)

#example dataset
data = {
    "Record ID": list(range(1, 28)),
    "Name (Devanagari)": [
        "राम शर्मा", "श्याम कुमार", "सुनीता गुप्ता", "सूरज सिंह", "सुमित शंकर",
        "राजेश वर्मा", "सुरेश वर्मा", "आदित्य जोशी", "प्रीति शर्मा", "कुंदन चौधरी",
        "अजय बत्रा", "सीमा पांडे", "विजय नाथ", "ऋषि चंद्र", "मोहित गुप्ता", 
        "किरण सिंग", "सौरभ दास", "नीता मित्तल", "शुभम वर्मा", "शाम शर्मा",
        "सूरज सिंग", "दीपक मेता", "सुमित शंखर", "राजेश वर्मा", "सुरेश वर्मा", 
        "सुमित संकर", "अजय बत्रा"
    ],
    "Name (English)": [
        "Ram Sharma", "Shyam Kumar", "Sunita Gupta", "Sooraj Singh", "Sumit Shankar",
        np.nan, np.nan, "Aditya Joshi", "Preeti Sharma", "Kundan Chaudhary", 
        "Ajay Batra", "Seema Pandey", "Vijay Nath", "Rishi Chandra", np.nan, 
        "Kiran Singh", "Saurabh Das", "Neeta Mittal", np.nan, np.nan,
        "Sooraj Singh", np.nan, "Sumit Shankar", "Rajesh Verma", 
        "Suresh Verma", "Sumit Shankar", "Ajay Batra"
    ],
    "Role": [
        "Witness", "Suspect", "Victim", "Witness", "Victim", 
        "Suspect", "Suspect", "Witness", "Victim", "Suspect", 
        "Victim", "Suspect", "Witness", "Victim", "Suspect",
        "Witness", "Victim", "Suspect", "Witness", "Witness",
        "Victim", "Suspect", "Victim", "Witness", "Suspect", 
        "Victim", "Witness"
    ]
}


df = pd.DataFrame(data)


def transliterate_to_roman(name_in_devanagari):
    if pd.notna(name_in_devanagari):
        return transliterate(name_in_devanagari, sanscript.DEVANAGARI, sanscript.ITRANS)
    return None


df["Transliterated Name (Roman)"] = df["Name (Devanagari)"].apply(transliterate_to_roman)


def generate_phonetic_code(name):
    if pd.notna(name):
        return phonetics.dmetaphone(name)
    return None


df["Phonetic Code (Roman)"] = df["Transliterated Name (Roman)"].apply(generate_phonetic_code)


def fuzzy_match_english(name, english_names, threshold=80):
    all_matches = process.extract(name, english_names.dropna())  
    
    filtered_matches = sorted([(match, score) for match, score, idx in all_matches if score >= threshold], key=lambda x: x[1], reverse=True)
    return filtered_matches


def phonetic_match_devanagari(name, phonetic_codes, threshold=80):
    phonetic_code = generate_phonetic_code(name)
    matches = []

    for choice, record_id in zip(phonetic_codes, df['Record ID']):
        score = fuzz.ratio(phonetic_code, choice)
        if score >= threshold:
            matches.append((record_id, score))

   
    return sorted(matches, key=lambda x: x[1], reverse=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        name_to_search = request.form['name']
        threshold = int(request.form['threshold'])

        english_names = df["Name (English)"]
        phonetic_codes = df["Phonetic Code (Roman)"]

        
        fuzzy_matches = fuzzy_match_english(name_to_search, english_names, threshold)

        
        phonetic_matches = phonetic_match_devanagari(name_to_search, phonetic_codes, threshold)

        result = {
            'fuzzy_matches': fuzzy_matches,
            'phonetic_matches': phonetic_matches,
            'threshold': threshold,
            'name': name_to_search
        }

    return render_template('index.html', result=result, df=df)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
