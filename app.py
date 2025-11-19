import streamlit as st
from PIL import Image
import pandas as pd
from verify import pil_from_upload, ocr_text_from_image, detect_faces, face_match, validate_fields, save_submission
import os

st.set_page_config(page_title='ID Verification', layout='centered')

st.title('ID Verification')
st.write('Upload a portrait and an ID card, enter ID details, and run validation.')

st.header('1) Upload Portrait')
portrait_file = st.file_uploader('Upload a passport-style portrait', type=['png','jpg','jpeg'], key='portrait')
portrait_img = pil_from_upload(portrait_file)
if portrait_img is not None:
    st.image(portrait_img, caption='Uploaded portrait', width=220)
    faces = detect_faces(portrait_img)
    st.write('Faces detected:', len(faces))
else:
    st.info('No portrait uploaded.')

st.header('2) Select ID Type')
id_type = st.selectbox('Select ID type', ['Ghana Card','Driver\'s License','Voter\'s ID','Passport'])

st.header('3) Enter ID Details')
with st.form('id_details'):
    id_number = st.text_input('ID Number')
    issuing_country = st.text_input('Issuing Country', value='Ghana')
    date_of_birth = st.text_input('Date of Birth (YYYY-MM-DD)')
    surname = st.text_input('Surname')
    firstname = st.text_input('First/Given Name')
    sex = st.selectbox('Sex', ['','M','F','Other'])
    save_btn = st.form_submit_button('Save Details')

if save_btn:
    st.success('Details saved in session.')

st.header('4) Upload ID Card')
id_file = st.file_uploader('Upload ID card (image or PDF)', type=['png','jpg','jpeg','pdf'], key='idcard')
id_img = None
ocr_text = ''
ocr_conf = 0.0
if id_file is not None:
    id_img = pil_from_upload(id_file)
    if id_img is not None:
        st.image(id_img, caption='Uploaded ID image', width=320)
    else:
        st.info('Uploaded file cannot be previewed as image.')
    ocr_text, ocr_conf = ocr_text_from_image(id_img)
    if ocr_text:
        st.subheader('OCR (excerpt)')
        st.write(ocr_text[:1000])

st.header('5) Validate')
if st.button('Run validation'):
    entered = {
        'id_number': id_number,
        'issuing_country': issuing_country,
        'date_of_birth': date_of_birth,
        'surname': surname,
        'firstname': firstname,
        'sex': sex
    }
    results = validate_fields(id_type, entered, ocr_text)
    st.subheader('Field-by-field results')
    rows = []
    for k,v in results['fields'].items():
        rows.append({'field': k, 'pass': v['pass'], 'msg': v['msg']})
    df_results = pd.DataFrame(rows)
    st.table(df_results)

    match, dist = face_match(portrait_img, id_img)
    st.write('Face match:', match)
    if dist is not None:
        st.write('Face distance:', dist)

    record = {
        'id_type': id_type,
        'id_number': id_number,
        'surname': surname,
        'firstname': firstname,
        'date_of_birth': date_of_birth,
        'validation_overall': bool(results['overall']),
        'face_match': bool(match) if match is not None else None,
        'ocr_conf': float(ocr_conf or 0.0)
    }
    ok = save_submission(record)
    if ok:
        st.success('Saved submission to submissions.csv')
    else:
        st.warning('Could not save submission locally.')

st.header('Admin / Dashboard')
try:
    if os.path.exists('submissions.csv'):
        df_sub = pd.read_csv('submissions.csv')
        st.dataframe(df_sub.tail(20))
    else:
        st.info('No saved submissions yet.')
except Exception as e:
    st.error(f'Error loading submissions: {e}')
