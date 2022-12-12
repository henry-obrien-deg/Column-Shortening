# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 08:42:54 2022

@author: hobrien
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

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
                   (dfjoints['UniqueName'].isin(dfcolcon['UniquePtJ']))].copy()
    return df2


# Load data
df = load_col_con()
df_joints = load_joints()
df_disp = load_disp()

# Sidebar widgets and text
st.sidebar.header('Filters')
story = st.sidebar.selectbox('Story:', df_disp['Story'].unique())
load_case = st.sidebar.selectbox('Load Case:', df_disp['Output Case'].unique())
direction = st.sidebar.selectbox('Displacement', ['Ux', 'Uy', 'Uz'], index=2)
scale = st.sidebar.slider('Scale Factor:', 1, 10, 1)
st.sidebar.write('This is an example based on a simple 4 story ETABS model.')
st.sidebar.image('model.png')

# Merge displacement and joint dataframes
# Filter the joints so that only joints with column connectivity are kept
df_m = merge_data(df_disp, df_joints, ['UniqueName', 'Story'])
df_m = col_to_numeric(df_m, direction)
df2 = filter_col_joints_only(df_m, df)

# Apply scale factor to displacement
# Normalize displacement for use in bubble plot
df2[direction] = df_m[direction] * scale
df2['NormDisp'] = (1.0 - (df2[direction] - df2[direction].min()) /
                   (df2[direction].max() - df2[direction].min()))

# Filter data to include the selected story and output case
dfplot = df2[(df2['Story'] == story) & (df2['Output Case'] == load_case)]

# Create plot
fig = go.Figure(data=(go.Scatter(x=dfplot['X'], y=dfplot['Y'],
                                 mode='markers',
                                 hovertext=dfplot[direction],
                                 marker=dict(
                                     size=dfplot['NormDisp']*40+1,
                                     color=dfplot[direction],
                                     colorscale='Viridis',
                                     reversescale=True,
                                     cmin=df2[direction].min(),
                                     cmax=df2[direction].max(),
                                     colorbar=dict(
                                         title='Deflection (in)',
                                         ticks='outside',
                                         thickness=10)
                                     )
                                 )))

# Add background image
grids = Image.open('grid.png')
fig.add_layout_image(
    dict(
        source=grids,
        xref="x",
        yref="y",
        x=-13.33,
        y=102,
        sizex=107.25,
        sizey=105,
        sizing="stretch",
        opacity=1,
        layer="below"
        ))

# Update figure graphics
fig.update_xaxes(range=[-12, 93], tickvals=[0, 30, 60, 90], showgrid=False,
                 zeroline=False, mirror=True, ticks='outside', showline=True)
fig.update_yaxes(range=[-3, 102], tickvals=[0, 30, 60, 90], showgrid=False,
                 zeroline=False, mirror=True, ticks='outside', showline=True)
fig.update_layout(title=(direction + ' Displacement - ' + story),
                  autosize=False, height=600)

# Create a stripped down dataframe for displaying in the dashboard
dfshow = dfplot.drop(columns=['Step Type', 'Step Number', 'Step Label',
                              'NormDisp', 'Label', 'Case Type', 'UniqueName',
                              'Story'])

# Add plot, text, and dataframe to the dashboard
st.subheader('Plan View Plot')
st.plotly_chart(fig, use_container_width=True)
st.subheader('Data')
st.write("Scale factor = ", scale)
st.dataframe(dfshow, use_container_width=True)

# Create csv for download button option
csv = dfshow.to_csv()

# Download button
st.download_button("Download as CSV", csv)
