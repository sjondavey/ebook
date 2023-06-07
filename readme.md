# Extracting nuanced information from a book
## A repo that needs a human in the loop

This project uses ChatGPT to 
1) create a list of people mentioned in; and 
2) summarise the content of

Andre de Ruyter's ebook "Truth to Power". For obvious copyright reasons, the ebook is not part of this repo. If you want to run this you will need to buy your own copy of the book in PDF format and save it in a directory "/inputs/". 

The structure of the project is simple but the project is manual. 

The code in `convert_book_to_text.py` contains some functions that turn the book PDF in chunks that can be sent to ChatGPT (3.5).

The notebook `01_sentiment_analysis.ipynb` and the code in `sentiment_analysis.py` contains the specific code for sentiment analysis.

The notebook `02_summarise_book.ipynb` contains its own code.


The code is specific to this book and will not work more generally. The rationale is that the end-to-end process here is one which requires human / LLM teamwork and cannot be "automated" without massive overhead which the task does not require. The code therefore is kept minimal and specific.



