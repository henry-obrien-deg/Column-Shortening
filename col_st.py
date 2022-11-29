# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 08:42:54 2022

@author: hobrien
"""
import streamlit as st
import pandas as pd
import plotly.express as px

st.title('ETABS Output Visualization')

@st.cache
def load_col_con():
    df = pd.read_excel('ETABS_Output.xlsx',
                       sheet_name='Column Object Connectivity',
                       header=1)
    df = df.drop(0)
    df = df.drop(columns=['GUID', 'ColumnBay'], axis=1)
    df = df.rename(columns={'Unique Name':'UniqueName'})
    return df


@st.cache
def load_joints():
    df_joints = pd.read_excel('ETABS_Output.xlsx',
                              sheet_name='Point Object Connectivity',
                              header=1)
    df_joints = df_joints.drop(0)
    df_joints = df_joints.drop(columns=['PointBay', 'IsSpecial', 'GUID',
                                        'Is Auto Point'])
    return df_joints


@st.cache
def load_disp():
    df_disp = pd.read_excel('ETABS_Output.xlsx',
                            sheet_name='Joint Displacements',
                            header=1)
    df_disp = df_disp.drop(0)
    df_disp = df_disp.rename(columns={'Unique Name':'UniqueName'})
    df_disp = df_disp[df_disp['Output Case'] != 'Modal']
    return df_disp


@st.cache
def merge_data(df1, df2, onCols):
    df_m = pd.merge(df1, df2, on=onCols)
    return df_m


@st.cache
def col_to_numeric(df, col):
    df[col] = pd.to_numeric(df[col])
    return df


@st.experimental_memo
def filter_col_joints_only(dfjoints, dfcolcon):
    df2 = dfjoints[(dfjoints['UniqueName'].isin(dfcolcon['UniquePtI'])) |
                   (dfjoints['UniqueName'].isin(dfcolcon['UniquePtJ']))]
    return df2


# Load data
df = load_col_con()
df_joints = load_joints()
df_disp = load_disp()

df_m = merge_data(df_disp, df_joints, ['UniqueName', 'Story'])
df_m = col_to_numeric(df_m, 'Uz')
df2 = filter_col_joints_only(df_m, df)

st.sidebar.header('Filters')
story = st.sidebar.selectbox('Story:', df_m['Story'].unique())
load_case = st.sidebar.selectbox('Load Case:', df_m['Output Case'].unique())
scale = st.sidebar.slider('Scale Factor:', 1, 10, 1)

df2['Uz'] = df_m['Uz'] * scale
df2['NormUz'] = (1.0 - (df2['Uz'] - df2['Uz'].min()) / (df2['Uz'].max() -
                                                        df2['Uz'].min()))

dfplot = df2[(df2['Story'] == story) & (df2['Output Case'] == load_case)]
dfplot['Uz'] = dfplot['Uz'] * scale

fig = px.scatter(dfplot, x='X',  y='Y', color='Uz', size='NormUz',
                 hover_data=['X', 'Y', 'Uz'],
                 title='Vertical Displacement - ' + story)

dfshow = dfplot.drop(columns=['Step Type', 'Step Number', 'Step Label',
                              'NormUz', 'Label', 'Case Type', 'UniqueName',
                              'Story'])

st.subheader('Plan View Plot')
st.plotly_chart(fig, use_container_width=True)
st.subheader('Data')
st.write("Scale factor = ", scale)
st.dataframe(dfshow, use_container_width=True)

csv = dfshow.to_csv()

st.download_button("Download as CSV", csv)