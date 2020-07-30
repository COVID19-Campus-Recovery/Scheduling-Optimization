import pandas as pd
import time
import tabula as tb
import re
from urllib.request import urlopen


def scrape_pdf(url_residential, url_remote):
    r'''
    Scrape pdf file from the registrar office web page

        Parameters:
        -------------

        url_residential: str default=None
           the url of residential courses pdf file.

        url_remote: str, default = None
           the url of remote courses pdf file.

        Returns:
        -------------
        residential_tables: residential courses table
        remote_tables: remote courses table

        '''


    print("Scraping PDF files")

    residential_path = urlopen(url_residential)
    html_doc_residential = residential_path.read().decode('utf8')
    remote_path = urlopen(url_remote)
    html_doc_remote = remote_path.read().decode('utf8')
    residential_file = re.search(r'href="(.*?)pdf', html_doc_residential).group(1)+"pdf"
    global remote_file
    remote_file = re.search(r'href="(.*?)pdf', html_doc_remote).group(1)+"pdf"

    print("Extracting tables from .pdf file")
    residential_tables = tb.read_pdf(residential_file, pages="all", multiple_tables=True)
    remote_tables = tb.read_pdf(remote_file, pages="all", multiple_tables=True)

    return residential_tables, remote_tables



def convert_table_remote(tables):
    r'''
    Clean remote table

        Parameters:
        -------------
            tables: pd.Dataframe default=None
                remote table that need to be cleaned

        Returns:
        -------------
            table_out: pd.Dataframe
                cleaned remote table
        '''

    print("Clean remote table")

    tables[0] = tables[0].dropna(axis=1)

    tables[0].columns = ["CRN", "Subject Code", "Course Number", "Section", "Course Title", "Preferred Delivery Mode"]
    for i in range(1, len(tables)):
        tables[i] = tables[i].T.reset_index().T
        tables[i].columns = tables[0].columns

    table_out = pd.concat(tables)
    table_out[["index", "CRN"]] = table_out["CRN"].str.split(" ", expand=True)
    table_out = table_out.reset_index()
    table_out = table_out[
        ["CRN", "Subject Code", "Course Number", "Section", "Course Title", "Preferred Delivery Mode"]]


    return table_out


def convert_table_residential(tables):
    r'''
    Clean remote table

       Parameters:
       -------------
           tables: pd.Dataframe default=None
               residential table that need to be cleaned

       Returns:
       -------------
           table_out: pd.Dataframe
               cleaned residential table
       '''

    print("Clean residential table")

    tables[0] = tables[0].dropna(axis=1)
    tables[0][["index", "CRN", "Subject Code"]] = tables[0]["CRN Subject Code"].str.split(" ", expand=True)

    temp0 = tables[0]["Course Number Section Course Title"].str.split(" ", expand=True)
    tables[0][["Course Number", "Section"]] = temp0.loc[:, 0:1]

    tables[0]['Course Title'] = tables[0]["Course Number Section Course Title"].apply(
        lambda row: " ".join(row.split(" ")[2:]))

    tables[0] = tables[0][
        ["CRN", "Subject Code", "Course Number", "Section", "Course Title", "Delivery Mode Attribute"]]

    for i in range(1, len(tables)):
        tables[i] = tables[i].T.reset_index().T.reset_index(drop=True)

        tables[i][["index", "CRN", "Subject Code"]] = tables[i][0].str.split(" ", expand=True)
        tables[i] = tables[i][["CRN", "Subject Code", 1, 2, 3, 4]]

        tables[i].columns = tables[0].columns

        table_out = pd.concat(tables)
        table_out = table_out.reset_index(drop=True)

    return table_out

def output_file(result):
    r'''
    Generate Ouput file with date label

       Parameters:
       -------------
           result: pd.Dataframe default=None

       '''

    print("Output file generating")
    global remote_file
    date = remote_file.split("-")[-2][4:]
    date_ = date[:2]+"-"+date[2:]
    result.to_excel("Scraped Preference "+date_+".xlsx",index=False)

if __name__ == "__main__":
    start = time.time()

    residential_tables,remote_tables = scrape_pdf("https://registrar.gatech.edu/info/list-fall-2020-courses-indicated-preference-fully-residential-delivery",
                                              "https://registrar.gatech.edu/info/list-fall-2020-remote-courses")


    residential_tables_out = convert_table_remote(residential_tables)
    remote_tables_out = convert_table_residential(remote_tables)

    residential_tables_out = residential_tables_out.rename(columns={"Preferred Delivery Mode":"Delivery Mode Attribute"})
    result = pd.concat([remote_tables_out,residential_tables_out]).reset_index(drop=True)

    output_file(result)

    end = time.time()

    print("Run Time: ", end-start,"s")


