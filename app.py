import base64
import streamlit as st
import pandas as pd
from stqdm import stqdm
from datetime import datetime
import plotly.express as px

from scrapper import scrap_data, get_article_data
from global_variables import DATASET, URL, es_month_trad

import git

stqdm.pandas()

st.title('IGN Spain scraper')
st.subheader('Scraper results : ')

today = datetime.today()


def display_df(path: str):
    """
    Function to display data when present and compute few KPIs
    :param path: path where to find data if they exist
    :return:
    """
    try:
        df_old = pd.read_csv(path)
        df_old.published_date = pd.to_datetime(df_old.published_date)
        n_articles_old = df_old.shape[0]

        author_number = len(df_old.author.unique())
        most_prolific_writer = df_old['author'].value_counts().idxmax()
        most_prolific_writer_n_articles = df_old[df_old['author'] == most_prolific_writer].shape[0]
    except Exception as e:
        df_old = pd.DataFrame(columns=['title', 'link', 'author', 'published_date'])
        n_articles_old = 0

        author_number = 0
        most_prolific_writer = None
        most_prolific_writer_n_articles = None

    return df_old, n_articles_old, author_number, \
           most_prolific_writer, most_prolific_writer_n_articles


st.sidebar.title('Lancer le scraper')

if st.sidebar.button('Scrap 🚀', on_click=display_df, args=(DATASET,)):
    st.sidebar.info(f'Last article count : {st.session_state.n_articles_old}')
    df_new = scrap_data(URL)
    df_new['additional_content'] = df_new.link.progress_apply(lambda x: get_article_data(x))
    df_new['author'] = df_new.additional_content.apply(lambda x: x[0])

    df_new['published_date'] = df_new.additional_content.apply(lambda x: x[1].replace('de ', '').replace('a las ', ''))
    df_new['published_date'] = df_new.published_date.apply(lambda x: ''.join([elt.zfill(2) if elt not in es_month_trad
                                                                              else str(es_month_trad[elt] + 1).zfill(2)
                                                                              for elt in x.split()]))
    df_new['published_date'] = df_new.published_date.apply(lambda x: x if ':' not in x else x.split(':')[0][:-2])
    df_new['published_date'] = df_new.published_date.apply(lambda x: datetime.strptime(x, '%d%m%Y'))
    df_new['published_date'] = pd.to_datetime(df_new.published_date)

    df_new = df_new.drop(['additional_content'], axis=1)

    st.session_state.df_old = pd.concat([st.session_state.df_old, df_new], axis=0).drop_duplicates().reset_index(
        drop=True)
    st.session_state.df_old = st.session_state.df_old.fillna('None')
    st.session_state.df_old.to_csv(DATASET, index=False)
    st.session_state.n_articles_new = st.session_state.df_old.shape[0]
    st.sidebar.success(f'New article count : {st.session_state.n_articles_new}')

to_display_df = display_df(DATASET)

st.session_state.df_old = to_display_df[0]
st.session_state.n_articles_old = to_display_df[1]
st.session_state.author_number = to_display_df[2]
st.session_state.most_prolific_writer = to_display_df[3]
st.session_state.most_prolific_writer_n_articles = to_display_df[4]

if st.session_state.df_old.shape[0] > 0:
    n_articles_current_month = int((st.session_state.df_old.published_date.dt.month == today.month).sum())
    n_articles_last_month = int((st.session_state.df_old.published_date.dt.month == today.month-1).sum())
else:
    n_articles_current_month = 0
    n_articles_last_month = 0

col1, col2, col3 = st.columns(3)
col1.metric("Number of author", f'{st.session_state.author_number}')
col2.metric("Number of articles (current month)", f'{n_articles_current_month}',
            n_articles_current_month-n_articles_last_month)
col3.metric("Most prolific writer", f'{st.session_state.most_prolific_writer}',
            st.session_state.most_prolific_writer_n_articles)

if st.session_state.df_old.shape[0] > 0:
    agg = st.session_state.df_old.groupby(['author', 'published_date']).size().reset_index()
    agg.columns = ['author', 'date', 'articles published']

    fig = px.line(agg.sort_values(by='date', ascending=True), x='date', y='articles published',
                  color='author')
    fig.update_traces(mode='lines+markers')
    st.plotly_chart(fig, use_container_width=True)

    st.write(st.session_state.df_old)
else:
    st.write('No data to display')

if st.button('Download data') and st.session_state.df_old.shape[0] > 0:
    csv = st.session_state.df_old.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings
    href = f'<a href="data:file/csv;base64,{b64}" download="ign_spain_{today.year}{str(today.month).zfill(2)}' \
           f'{str(today.day).zfill(2)}.csv">Download csv file</a>'
    st.markdown(href, unsafe_allow_html=True)

#repo = git.Repo()
#repo.remotes[0].add('test_.csv', 'https://github.com/RomainCoville/ign_scraper.git')
#repo.remotes[0].commit('spain file upload')
#repo.remotes[0].push('test_.csv')
