import camelot
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import argparse
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
languages_path = os.path.join(script_dir, "languages.json")

with open(languages_path, "r", encoding="utf-8") as file:
    LANGUAGES = json.load(file)

def get_file_input(file_path=None, lang="en"):
    if file_path:
        if not os.path.isfile(file_path):
            print(LANGUAGES[lang]["file_not_found"].format(file_path))
            return get_file_input(None, lang)
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            file_type = 'pdf'
        elif file_extension == '.csv':
            file_type = 'csv'
        elif file_extension in ['.xlsx', '.xls']:
            file_type = 'excel'
        else:
            print(LANGUAGES[lang]["unsupported_format"])
            return get_file_input(None, lang)

        print(LANGUAGES[lang]["using_file"].format(file_path))
        print(LANGUAGES[lang]["detected_file_type"].format(file_type))
        return file_type, file_path
    
    while True:
        file_path = input(LANGUAGES[lang]["enter_file_path"]).strip()

        if not os.path.isfile(file_path):
            print(LANGUAGES[lang]["file_not_found"].format(file_path))
            continue

        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            file_type = 'pdf'
        elif file_extension == '.csv':
            file_type = 'csv'
        elif file_extension in ['.xlsx', '.xls']:
            file_type = 'excel'
        else:
            print(LANGUAGES[lang]["unsupported_format"])
            continue

        print(LANGUAGES[lang]["detected_file_type"].format(file_type))
        return file_type, file_path

def extract_table(file_type, file_path, lang="en"):
    if file_type == "pdf":

        tables = camelot.read_pdf(file_path, flavor="stream", pages="all")
        
        if not tables or tables[0].df.empty:
            tables = camelot.read_pdf(file_path, flavor="lattice", pages="all")
        
        if not tables or tables[0].df.empty:
            print(LANGUAGES[lang]["no_tables"])
            raise ValueError("No tables found in PDF")
            
        return pd.concat([table.df for table in tables], ignore_index=True)
    elif file_type == "csv":
        return pd.read_csv(file_path)
    elif file_type == "excel":
        return pd.read_excel(file_path)
    else:
        return

def get_valid_plot_title(title=None, lang="en"):
    if title:
        if title.strip() == "":
            print(LANGUAGES[lang]["invalid_title"])
            return get_valid_plot_title(None, lang)
        return title
    
    while True:
        title = input(LANGUAGES[lang]["enter_title"])
        if title.strip() == "":
            print(LANGUAGES[lang]["invalid_title"])
        else:
            return title

def get_column(table, is_pdf=False, lang="en"):
    if is_pdf:
        while True:
            print(LANGUAGES[lang]["enter_column_index"].format(len(table.columns) - 1))
            try:
                column_index = int(input())
                if 0 <= column_index < len(table.columns):
                    return column_index
                else:
                    print(LANGUAGES[lang]["invalid_column_index"].format(len(table.columns) - 1))
            except ValueError:
                print(LANGUAGES[lang]["invalid_integer"])
    else:
        while True:
            print(LANGUAGES[lang]["enter_column"])
            column_name = input()
            if column_name in table.columns:
                return column_name
            else:
                print(LANGUAGES[lang]["column_not_found"].format(column_name))
                print(LANGUAGES[lang]["available_columns"].format(", ".join(table.columns)))

def analyze_grades(table, column, thresshold, is_pdf=False):    
    if is_pdf:
        values = table.iloc[:, column].astype(str).str.replace(r"[^\d.]", "", regex=True)
        values = pd.to_numeric(values, errors='coerce').dropna()
    else:
        values = pd.to_numeric(table[column], errors='coerce').dropna()

    stats = {
        'total': len(values),
        'passing': len(values[values >= thresshold]),
        'failing': len(values[values < thresshold]),
    }
    
    stats['passing_pct'] = (stats['passing'] / stats['total']) * 100 if stats['total'] > 0 else 0
    stats['failing_pct'] = (stats['failing'] / stats['total']) * 100 if stats['total'] > 0 else 0
    
    return values, stats

def display_statistics(stats, lang="en"):
    print(LANGUAGES[lang]["total"].format(stats['total']))
    print(LANGUAGES[lang]["passing"].format(stats['passing'], stats['passing_pct']))
    print(LANGUAGES[lang]["failing"].format(stats['failing'], stats['failing_pct']))

def complete_value_counts(values, min_val=0, max_val=10):
    has_decimals = any(value != int(value) for value in values if isinstance(value, (int, float)))
    
    step = 0.5 if has_decimals else 1
    
    all_possible_values = np.arange(min_val, max_val + step, step)
    
    actual_counts = values.value_counts().sort_index()
    
    complete_counts = pd.Series(0, index=all_possible_values)
    
    for idx in actual_counts.index:
        if idx in complete_counts.index:
            complete_counts[idx] = actual_counts[idx]
    
    return complete_counts

def plot_grade_distribution(values, stats, title, output_path="plot.png", lang="en"):
    value_counts = complete_value_counts(values)
    
    plt.figure(figsize=(10, 6))
    ax = value_counts.plot(kind='bar', color='skyblue')
    
    max_value = value_counts.max()
    y_offset = max_value * 0.005 

    for i, v in enumerate(value_counts):
        if v == 0: 
            continue
        ax.text(i, v + y_offset, str(int(v)), ha='center')
    
    plt.title(title, y=1.15, fontsize=18)
    plt.xlabel(LANGUAGES[lang]["grade"], labelpad=5)
    plt.ylabel(LANGUAGES[lang]["frequency"], labelpad=10)
    
    text = (f"{LANGUAGES[lang]['total'].format(stats['total'])}\n"
            f"{LANGUAGES[lang]['passing'].format(stats['passing'], stats['passing_pct'])}\n"
            f"{LANGUAGES[lang]['failing'].format(stats['failing'], stats['failing_pct'])}")

    plt.suptitle(text, fontsize=12)

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(LANGUAGES[lang]["plot_saved"].format(output_path))

def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue

def main():
    parser = argparse.ArgumentParser(description='Analyze grade data from a file and generate a visualization.')
    parser.add_argument('--file', help='Path to the input file (PDF, CSV, or Excel)')
    parser.add_argument('--title', help='Title for the plot')
    parser.add_argument('--output', default='plot.png', help='Output file path for the plot (default: plot.png)')
    parser.add_argument('--lang', default='en', help='Language code (default: en)')
    parser.add_argument('--rows', default=10, type=positive_int, help='The amount of rows of the table that will be printed')
    parser.add_argument('--thresshold', default=5, type=positive_int, help=' Minimum grade required to consider a student as "passing"')
   
    args = parser.parse_args()
    
    file_path = args.file
    title = args.title
    output_path = args.output
    lang = args.lang
    thresshold = args.thresshold

    if lang not in LANGUAGES:
        print("Invalid language. Defaulting to English.")
        lang = "en"

    file_type, file_path = get_file_input(file_path, lang)

    table = extract_table(file_type, file_path, lang)
    print("\n" + LANGUAGES[lang]["first_rows"])
    print(table.head(args.rows))

    column = get_column(table, file_type == "pdf", lang)
    title = get_valid_plot_title(title, lang)

    values, stats = analyze_grades(table, column, thresshold, file_type == "pdf")
    display_statistics(stats, lang)

    plot_grade_distribution(values, stats, title, output_path, lang)

if __name__ == "__main__":
    main()