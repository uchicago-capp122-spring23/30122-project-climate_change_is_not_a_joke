import pandas as pd
import json
import spacy
from collections import Counter

def clean_data():
    with open('adb_projects.json') as f:
        data = json.load(f)

    #remove null rows
    data = list(filter(lambda x: x is not None, data))

    #remove unnecessary fields
    field_list = ['Project Name', 'Project Number', 'Country / Economy', 'Project Status', 'Sector / Subsector', 'Description', 'commitment_date', 'Amount', 'project_url']
    cleaned_list = []
    #country_proj ={}
    #proj_id = {}
    for row in data:
        cleaned_project = {}
        for key in row.keys():
            if key in field_list:
                cleaned_project[key] = row[key]
        cleaned_list.append(cleaned_project)

    #convert to pandas df
    df = pd.DataFrame(cleaned_list)

    #convert amount to float
    df['Amount'] = df['Amount'].str.replace(',', '').astype(float)

    #remove zero Amount
    df.drop(df[df['Amount'] ==0].index, inplace = True)

    #convert amount to millions
    df["Commitment Amount"] = df["Amount"].where(df["Amount"] >= 30000, df["Amount"] * 1000000)

    #remove those with no effectivity date
    df.drop(df[df['commitment_date'] =='-'].index, inplace = True)

    #clean sector column
    df['Sector'] = (df['Sector / Subsector'].str.split('/').str[0]).str.strip()
    df = df.dropna(subset=['Sector'])

    #change country of multiple country projects to 'Regional'
    df['Country'] = df['Country / Economy'].copy()
    df.loc[df['Country'].str.contains('Regional'), 'Country'] = 'Regional'

    #cleaning country names based on official country_list
    df.loc[df['Country'].str.contains('China'), 'Country'] = "People's Republic of China"
    df.loc[df['Country'].str.contains('Micronesia'), 'Country'] = "Federated States of Micronesia"

    #Add column for Region
    country_list = pd.read_csv('Country_List.csv')
    df = df.merge(country_list[['Country', 'Region']], on='Country', how='left')
    df.loc[df['Country'] == 'Regional', 'Region'] = 'Regional'

    #dropping rows with no corresponding Region --this means the are not in the official Country_List
    df = df.dropna(subset=['Region'])

    #adding pre/post Paris Agreement tag
    target_date = pd.to_datetime('2016-11-04')
    df['Pre/Post Paris Agreement'] = df['commitment_date'].apply(lambda x: 0 if pd.to_datetime(x) < target_date else 1)

    #aligning column names
    df = df.rename(columns={'commitment_date': 'Effective Date', 'project_url': 'Project URL','Project Status' : 'Status', 'Description' : 'Project Description' })
    
    #dropping unnecessary columns
    df = df.drop(columns=["Country / Economy", "Project Number", "Sector / Subsector", "Amount"])

    #rearranging columns
    df = df[['Country', 'Region', 'Project Name', 'Project Description', 'Status', 'Project URL', 'Effective Date', 'Commitment Amount', 'Pre/Post Paris Agreement', 'Sector']]

    print(df)
    #convert to csv    
    df.to_csv("clean_df.csv", index=False)


def merg_climate_df():
    df_2019 = pd.read_csv('ADB Climate-2019.csv')
    df_2020 = pd.read_csv('ADB Climate-2020.csv')
    df_2021 = pd.read_csv('ADB Climate-2021.csv')

    df_2020.dropna(how='all', axis=1, inplace=True)
    new_df_2020 = df_2020.drop(['Other Sector(s) Covered'], axis = 1)
    
    frames = [df_2019, new_df_2020, df_2021]
    climate_df = pd.concat(frames)
    climate_df = climate_df.drop_duplicates(subset='Project Number', keep="first")
    return climate_df

def make_token_column(df, file_name):
    """
    Making tokens for description and making new column to datafram
    """

    sp = spacy.load("en_core_web_sm")
    stopwords = sp.Defaults.stop_words
    token_lst = []
    for index, row in df.itterows():
        doc = sp(row["Project Description"])
        for word in doc:
            if word not in stopwords:
                token_lst.append(word)
        df = df["Tokens"] = token_lst

def climate_tag_token_lst(df):
    df = merg_climate_df()
    sp = spacy.load("en_core_web_sm")
    token_d = {}
    token_lst = []
    for index, row in df.iterrows():

        doc =sp(row['Project Name'])
        # print(type(doc))
        # word_freq = Counter(doc)

        for token in doc:
        #     print(type(word))
            if token.is_stop or token.is_punct or token.like_num:
                continue
            token_lst.append(token.text)
            # if token.text in token_d:
            #     token_d[token.text] += 1
            # else:
            #    token_d[token.text] = 1
    word_freq = Counter(token_lst)
    top_tokens = word_freq.most_common(1000)
    df = pd.DataFrame(top_tokens) 
    with open('tokens', 'w') as f:
        df.to_csv('tokens.csv')
    







                
