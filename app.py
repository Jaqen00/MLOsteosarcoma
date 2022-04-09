import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pysurvival.utils import load_model

st.set_page_config(layout="wide")

@st.cache
def load_setting():
    settings = {
        'Age': {'values': [0, 100], 'type': 'slider', 'init_value': 50, 'add_after': ', year'},
        'Gender': {'values': ["Male", "Female"], 'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Martial status': {'values': ["Not married", "Married"], 'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Stage': {'values': ["I", "II", "III", 'IV'], 'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Grade': {
            'values': ["Well differentiated", "Moderately differentiated", "Poorly differentiated", 'Undifferentiated'],
            'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Surgery': {'values': ["None", "Local treatment", "Radical excision with limb salvage", 'Amputation'],
                    'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Radiotherapy': {'values': ["No", "Yes"], 'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Tumor size': {'values': [0, 1000], 'type': 'slider', 'init_value': 135, 'add_after': ', mm'},
        'Tumor extension': {'values': ["No break in periosteum", "Extension beyond periosteum", "Further extension"],
                            'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Distant metastasis': {'values': ["None", "Lung only", "Other distant organ"], 'type': 'selectbox',
                               'init_value': 1,
                               'add_after': ''},
    }
    input_keys = ['Age', 'Distant metastasis', 'Gender', 'Grade', 'Martial status', 'Radiotherapy', 'Stage', 'Surgery',
                  'Tumor extension', 'Tumor size']
    return settings, input_keys


settings, input_keys = load_setting()


@st.cache
def get_model():
    model = load_model('./deepsurv_2022_04_09.zip')
    return model


def get_code():
    sidebar_code = []
    for key in settings:
        if settings[key]['type'] == 'slider':
            sidebar_code.append(
                "{} = st.slider('{}',{},{})".format(
                    key.replace(' ', '____'),
                    key + settings[key]['add_after'],
                    # settings[key]['values'][0],
                    ','.join(['{}'.format(value) for value in settings[key]['values']]),
                    settings[key]['init_value'],
                )
            )
        if settings[key]['type'] == 'selectbox':
            sidebar_code.append('{} = st.selectbox("{}",({}),{})'.format(
                key.replace(' ', '____'),
                key + settings[key]['add_after'],
                ','.join('"{}"'.format(value) for value in settings[key]['values']),
                settings[key]['init_value'],
            )
            )
    return sidebar_code


deepsurv_model = get_model()
sidebar_code = get_code()

# print('\n'.join(sidebar_code))

if 'patients' not in st.session_state:
    st.session_state['patients'] = []
if 'display' not in st.session_state:
    st.session_state['display'] = 1


def plot_survival():
    pd_data = pd.concat(
        [
            pd.DataFrame(
                {
                    'Survival': item['survival'],
                    'Time': item['times'],
                    'Patients': [item['No'] for i in item['times']]
                }
            ) for item in st.session_state['patients']
        ]
    )
    if st.session_state['display']:
        fig = px.line(pd_data, x="Time", y="Survival", color='Patients', range_y=[0, 1])
    else:
        fig = px.line(pd_data.loc[pd_data['Patients'] == pd_data['Patients'].to_list()[-1], :], x="Time", y="Survival",
                      range_y=[0, 1])
    fig.update_layout(template='simple_white',
                      title={
                          'text': 'Estimated Survival Probability',
                          'y': 0.9,
                          'x': 0.5,
                          'xanchor': 'center',
                          'yanchor': 'top',
                          'font': dict(
                              size=25
                          )
                      },
                      plot_bgcolor="white",
                      xaxis_title="Time, month",
                      yaxis_title="Survival probability",
                      )
    st.plotly_chart(fig, use_container_width=True)


def plot_patients():
    patients = pd.concat(
        [
            pd.DataFrame(
                dict(
                    {
                        'Patients': [item['No']],
                        '3-Year': ["{:.2f}%".format(item['3-year'] * 100)],
                        '5-Year': ["{:.2f}%".format(item['5-year'] * 100)]
                    },
                    **item['arg']
                )
            ) for item in st.session_state['patients']
        ]
    ).reset_index(drop=True)
    st.dataframe(patients)


def predict(arg):
    input = []
    for key in arg:
        if isinstance(arg[key], int):
            input.append(arg[key])
        if isinstance(arg[key], str):
            input.append(settings[key]['values'].index(arg[key]))
    survival = deepsurv_model.predict_survival(np.array(input), t=None)
    data = {
        'survival': survival.flatten(),
        'times': [i for i in range(0, len(survival.flatten()))],
        'No': len(st.session_state['patients']) + 1,
        'arg': arg,
        '3-year': survival[0, 36],
        '5-year': survival[0, 60]
    }
    if not st.session_state['patients'] or arg != st.session_state['patients'][-1]['arg']:
        st.session_state['patients'].append(
            data
        )


st.header('DeepSurv-based model for predicting survival of osteosarcoma', anchor='survival-of-osteosarcoma')
if st.session_state['patients']:
    col1, col2 = st.columns([1, 9])
    col3, col4, col5, col6 = st.columns([2, 3, 3, 2])
    with col1:
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.session_state['display'] = ['Single', 'Multiple'].index(
            st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
    with col2:
        plot_survival()
    with col4:
        st.metric(
            label='3-Year survival probility',
            value="{:.2f}%".format(st.session_state['patients'][-1]['3-year'] * 100)
        )
    with col5:
        st.metric(
            label='5-Year survival probility',
            value="{:.2f}%".format(st.session_state['patients'][-1]['5-year'] * 100)
        )
    st.write('')
    st.write('')
    st.write('')
    plot_patients()
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    
st.subheader("Instructions:")
st.write("1. Select patient's infomation on the left\n2. Press predict button\n3. The model will generate predictions")
st.write('***Note: this model is still a research subject, and the accuracy of the results cannot be guaranteed!***')
with st.sidebar:
    for code in sidebar_code:
        exec(code)
    col7, col8, col9 = st.columns([3, 4, 3])
    with col8:
        prediction = st.button(
            'Predict',
            on_click=predict,
            args=[{key: eval(key.replace(' ', '____')) for key in input_keys}]
        )

# predict({key: eval(key.replace(' ', '____')) for key in input_keys})
# st.write(prediction)
