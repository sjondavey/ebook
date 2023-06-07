import PyPDF2
from pathlib import Path
import re
import pandas as pd



def find_chapter_pages(pdf: PyPDF2.PdfReader):
    # Returns a list of each page that begins with a number
    chapter_pages = []

    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        text = page.extract_text()

        # split the page text into lines
        lines = text.split('\n')

        # check if the first line of the page is a number
        if re.match(r'^\d+$', lines[0]):
            chapter_pages.append(i)

    return chapter_pages

def find_page_starting_with(pdf: PyPDF2.PdfReader, start_string: str):
    # Returns the first page number that starts with the start_string. This is used to find the page where the Index 
    # starts so we know where the last chapter ends

    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        text = page.extract_text()

        # Split the page text into lines
        lines = text.split('\n')

        # Check if the first line of the page matches the start_string
        if lines[0] == start_string:
            return i  # return the page number

    return None  # return None if no match was found


def build_chapter_dictionary(pages_with_numbers: list):
    # Given a list of page numbers that correspond to the page where the chapter starts, this method creates a 
    # dictionary with the chapter number as the key and the start and end page numbers as the values.
    # Note that the last number in the input list is the page number where the Index starts

    # Create a dictionary to store chapter details
    chapter_dict = {}

    for i in range(1, len(pages_with_numbers)):
        # Define the start page and end page for each chapter
        start_page = pages_with_numbers[i - 1]
        end_page = pages_with_numbers[i] - 1 

        # Store start page and end page in the dictionary for each chapter
        chapter_dict[i] = {"start_page": start_page, "end_page": end_page}

    return chapter_dict



def extract_text_from_pages_inclusive(pdf: PyPDF2.PdfReader, start_page_number: int, end_page_number: int):
    # Given that the dictionary created in build_chapter_dictionary() has inclusive page numbers, this method 
    # will extract the text from the start page number to the end page number inclusive of both pages.
    if end_page_number < start_page_number:
        raise ValueError("End page number should be greater than start page number.")
    if end_page_number > len(pdf.pages):
        raise ValueError("End page number should not exceed the total number of pages.")
    
    text = ""

    for i in range(start_page_number, end_page_number+1):
        page = pdf.pages[i]
        text += page.extract_text()

    return text

def remove_chapter_header(chapter_text: str):
    # The chapters are formatted so that they begin with a chapter number and then
    # the chapter title. This method removes the chapter number and chapter title.
    # I do however note that some chapter titles are over two lines. I have not 
    # catered for this. I leave the LLM to cope with that
    lines = chapter_text.split('\n')
    if len(lines) > 2:
        body = '\n'.join(lines[2:])
    else:
        body = ""
    return body


def chunk_text(text: str, n: int):
    #A chunk is a a collection of paragraphs that is less than or equal to n words long. 

    # Split the text into paragraphs using punctuation marks followed by newline character
    paragraphs =re.split(r'(?<=[?!.])\n|(?<=[?!.]’)\n', text)
    chunks = []
    chunk = ''
    for para in paragraphs:
        para = para.replace('\n', ' ')
        if len(chunk.split()) + len(para.split()) <= n:
            chunk += para + '\n'
        else:
            if len(para.split()) > n:
                raise ValueError(f"A single paragraph is longer than the specified limit of {n} words.")
            else:
                chunks.append(chunk.strip())
                chunk = para + '\n'
    if chunk:
        chunks.append(chunk.strip())
    return chunks



def find_bad_csv_files(folder_path: str):
    # The LLM does not always return the csv files in the correct format. This method checks the csv files in the
    # folder and returns a list of files that are not in the correct format. The list contains tuples of the file
    # name and the reason why it is not in the correct format.
    #
    # Note: Manual Input is required to fix the files that are not in the correct format.
    folder_path = Path(folder_path)
    csv_files = [file for file in folder_path.iterdir() if file.suffix == '.csv']

    bad_files = []
    
    for file in csv_files:
        try:
            df = pd.read_csv(file, sep='|', encoding='utf-8')  # load the file using '|' as the delimiter
            df.columns = df.columns.str.strip()  # remove leading and trailing whitespaces from column names
        except Exception as e:
            # if there's an error when reading a file, we consider it as a bad file
            bad_files.append((file.name, str(e)))
            continue
        
        if not df.columns.tolist() == ['Name', 'Count', 'Sentiment', 'Reason']:
            bad_files.append((file.name, 'Columns mismatch'))
        elif df.isnull().values.any():
            bad_files.append((file.name, 'Null values found'))
        elif any(df.iloc[i-1,:].isnull().all() and df.iloc[i,:].isnull().all() for i in range(1, len(df))):
            bad_files.append((file.name, 'Consecutive blank lines found'))

    return bad_files