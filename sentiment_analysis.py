import openai
import PyPDF2
import pandas as pd
from convert_book_to_text import find_chapter_pages, \
                                 find_page_starting_with,\
                                 extract_text_from_pages_inclusive, \
                                 build_chapter_dictionary, \
                                 remove_chapter_header, \
                                 chunk_text, \
                                 find_bad_csv_files

from pathlib import Path



def save_people_named_in_chapters(chapter_range_start: int, chapter_range_end: int, chapter_start_and_end: dict, pdf: PyPDF2.PdfReader, output_folder: str):
    # turn output_folder into a Path object
    folder_path = Path(output_folder)



    for i in range(chapter_range_start, chapter_range_end):
        chapter_number = i
        start = chapter_start_and_end[i]["start_page"]
        end = chapter_start_and_end[i]["end_page"]

        print("processing chapter: ", str(chapter_number) + " from page " + str(start) + " to page " + str(end))
        text = remove_chapter_header(extract_text_from_pages_inclusive(pdf, start, end))
        chunked_text = chunk_text(text, 800)

        for chunk in chunked_text:
            #create a filename using folder_pah + "chapter" + chapter_number + "_" + index of chunk + ".csv"
            filename = folder_path / ("chapter_" + str(chapter_number) + "_" + str(chunked_text.index(chunk)) + ".csv")
            if not Path(filename).exists():
                print("processing chunk " + str(chunked_text.index(chunk)) + " out of " + str(len(chunked_text)))
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You will be presented with text. You need to create a table in pipe delimited format, with the columns: Name, Count, Sentiment, Reason. For each person mentioned in the text, you need to count the number of times they are mentioned in the text and create a sentiment ranking from 0 (extremely negative) to 10 (extremely positive). The 'Reason' column should contain a short description of why you arrived at the sentiment rank."},
                        {"role": "user", "content": chunk},
                    ]
                )
                # write the value in response['choices'][0]['message']['content'] to the file with the name chapter_name_i.csv where i is the index of the chunk
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(response['choices'][0]['message']['content'])
            else:
                print("The file " + str(filename) + " already exists so skipping it")
  

def combine_csvs(directory):
    directory_path = Path(directory)
    csv_files = directory_path.glob('*.csv')

    df_list = []

    for filepath in csv_files:
        df = pd.read_csv(filepath, encoding='utf-8', delimiter='|')
        df.columns = df.columns.str.strip()  # remove leading and trailing whitespaces from column names

        markdown_values = ["-----", "----", "---", "-"]
        df = df[~df["Name"].str.strip().isin(markdown_values)]

        df["Chapter"] = filepath.stem
        df_list.append(df)

    combined_df = pd.concat(df_list, ignore_index=True)
    
    return combined_df


def aggregate_sentiment(name: str, output_folder: str, manual_list: pd.DataFrame):
    filename = output_folder + "/" + name + ".txt"
    subset = manual_list[manual_list["Name"] == name]
    if len(subset) > 1:
        print("Found " + str(len(subset)) + " entries for " + name)
        pipe_delimited_string = subset.to_csv(encoding='utf-8', index=False, sep='|')

        system_instruction = "The user will provide a table with the sentiment analysis for one person or organization from various places in a book. Scores in the Sentiment column are on a scale from 0 (extremely negative) to 10 (extremely positive). Please provide one overall sentiment analysis and one consolidated, summary Reason for the person or organization by aggregating all these into a single item. The one aggregate Sentiment score and reason should weight Sentiment Scores more highly if the Reason they have is compelling. The one aggregate Sentiment score should discount Neutral Ratings or ratings that correspond to Reasons that are not compelling. The aggregate Reason should be a short summary that supports the score. Do not provide any text other than the Aggregate Score and Aggregate Reason."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": pipe_delimited_string},
            ]
        )
        output = response['choices'][0]['message']['content']
        with open(filename, "w", encoding='utf-8') as f:
            f.write(output)

    elif len(subset) == 1:
        print("Found one entry for " + name)
        # create the output string using subset["Sentiment"] and subset["Reason"]
        output = "Sentiment: " + str(subset.loc["Sentiment"][0]) + "\nReason: " + subset.loc["Reason"][0]
        with open(filename, "w", encoding='utf-8') as f:
            f.write(output)
    else:
        print("No entry found for " + name)
        output = ""

    return output
