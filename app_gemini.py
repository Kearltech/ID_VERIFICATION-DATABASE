"""
Enhanced Streamlit app using Gemini API for card type detection and text extraction.
"""
import streamlit as st
import os
from PIL import Image
import pandas as pd
import json
import os
from verify import (
    pil_from_upload, 
    detect_faces, 
    face_match, 
    validate_fields, 
    save_submission,
    analyze_card_gemini,
    detect_card_type_gemini,
    extract_card_text_gemini,
    process_id_card_face
)

st.set_page_config(page_title='ID Verification with Gemini', layout='wide')

st.title('🆔 ID Verification System')
st.write('Upload a portrait and ID card. The system uses Google Gemini AI to automatically detect card type and extract text.')

# Sidebar for API configuration
with st.sidebar:
    st.header('⚙️ Configuration')
    # Prefill API key from environment variable if available
    env_api_key = os.environ.get('GEMINI_API_KEY', '')
    api_key = st.text_input(
        'Gemini API Key',
        value=env_api_key,
        type='password',
        help='Enter your Google Gemini API key. Get one from https://aistudio.google.com/app/apikeys'
    )
    use_gemini = st.checkbox('Use Gemini API for card analysis', value=True)
    st.markdown('---')
    st.info('This app uses Google Gemini Vision API to:\n1. Detect card type\n2. Extract labeled text fields\n3. Read text with OCR')

# Initialize session state
if 'card_analysis' not in st.session_state:
    st.session_state.card_analysis = None
if 'face_detection_result' not in st.session_state:
    st.session_state.face_detection_result = None

st.header('📸 Step 1: Upload Portrait')
col1, col2 = st.columns(2)
with col1:
    portrait_file = st.file_uploader('Upload a passport-style portrait', type=['png','jpg','jpeg'], key='portrait')
    portrait_img = pil_from_upload(portrait_file)
    if portrait_img is not None:
        st.image(portrait_img, caption='Uploaded portrait', width=220)
        faces = detect_faces(portrait_img)
        st.success(f'✓ Faces detected: {len(faces)}')
    else:
        st.info('📥 No portrait uploaded yet')

st.header('🎫 Step 2: Upload ID Card')
col1, col2 = st.columns([2, 1])
with col1:
    id_file = st.file_uploader('Upload ID card image', type=['png','jpg','jpeg','pdf'], key='idcard')
with col2:
    auto_analyze = st.checkbox('Auto-analyze on upload', value=True)

id_img = None
if id_file is not None:
    id_img = pil_from_upload(id_file)
    if id_img is not None:
        st.image(id_img, caption='Uploaded ID image', width=400)
        
        # Process face detection on ID card
        if st.checkbox('🔍 Detect & Extract Face from ID Card', value=True):
            with st.spinner('Detecting faces on ID card...'):
                face_result = process_id_card_face(
                    id_img, 
                    passport_img=portrait_img,
                    save_extracted=True
                )
                st.session_state.face_detection_result = face_result
                
                if face_result['success']:
                    st.success(f"✓ {face_result['message']}")
                    
                    # Show highlighted image with dotted boxes
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader('📍 Detected Faces (Highlighted)')
                            st.image(face_result['highlighted_img'], 
                                    caption=f"{face_result['faces_detected']} face(s) detected using {face_result['detection_method']}", 
                                    width='stretch')                    with col2:
                        if face_result['primary_face']:
                            st.subheader('👤 Extracted Face (Passport Size)')
                            st.image(face_result['primary_face'], 
                                    caption='Extracted and resized to standard passport dimensions',
                                    width=300)
                    
                    # Show face comparison if passport provided
                    if 'comparison' in face_result and portrait_img:
                        comp = face_result['comparison']
                        st.subheader('🔬 Face Match Analysis')
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            match_icon = '✅ MATCH' if comp.get('match') else '❌ NO MATCH'
                            st.metric('Match Result', match_icon)
                        with col2:
                            similarity = comp.get('similarity', 0)
                            st.metric('Similarity Score', f"{similarity:.1f}%")
                        with col3:
                            threshold = comp.get('threshold', 0.6)
                            st.metric('Threshold', f"{threshold*100:.0f}%")
                        
                        # Detailed scores
                        if 'scores' in comp:
                            with st.expander('📊 Detailed Comparison Scores'):
                                scores = comp['scores']
                                score_df = pd.DataFrame([
                                    {'Method': k, 'Score': f"{v:.1f}%"} 
                                    for k, v in scores.items()
                                ])
                                st.dataframe(score_df, width='stretch', hide_index=True)
                else:
                    st.warning(f"⚠️ {face_result.get('message', 'Face detection failed')}")
        
        # Automatic Gemini analysis if enabled
        if auto_analyze and use_gemini and api_key:
            st.subheader('🤖 AI Analysis in Progress...')
            with st.spinner('Analyzing card with Gemini...'):
                st.session_state.card_analysis = analyze_card_gemini(id_img, api_key)
    else:
        st.warning('⚠️ Uploaded file could not be processed as image')

# Display Gemini analysis results
if st.session_state.card_analysis and use_gemini:
    analysis = st.session_state.card_analysis
    
    st.header('📋 Gemini Analysis Results')
    
    # Card Type Detection
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Card Type Detection')
        card_type = analysis.get('card_type', 'Other')
        confidence = analysis.get('card_type_confidence', 0.0)
        st.metric('Detected Type', card_type, f'{confidence*100:.1f}% confidence')
    
    with col2:
        st.subheader('Overall Status')
        success = analysis.get('success', False)
        status_color = '✅' if success else '❌'
        st.write(f'{status_color} {analysis.get("message", "Analysis complete")}')
    
    # Text Extraction Results
    text_extraction = analysis.get('text_extraction', {})
    if text_extraction.get('success'):
        st.subheader('📝 Extracted Text Fields')
        text_fields = text_extraction.get('text_fields', {})
        
        if text_fields:
            # Display as formatted table
            field_data = []
            for field, value in text_fields.items():
                field_data.append({
                    'Field': field.replace('_', ' ').title(),
                    'Value': value
                })
            df_fields = pd.DataFrame(field_data)
            st.dataframe(df_fields, width='stretch', hide_index=True)
            
            # Option to copy as JSON
            json_output = json.dumps(text_fields, indent=2)
            st.write('**Extracted Fields as JSON:**')
            st.code(json_output, language='json')
        else:
            st.info('No text fields detected')
        
        # Raw OCR text
        raw_ocr = text_extraction.get('raw_ocr', '')
        if raw_ocr:
            with st.expander('📄 Full OCR Text', expanded=False):
                st.text(raw_ocr)
        
        # Confidence and notes
        col1, col2 = st.columns(2)
        with col1:
            ocr_confidence = text_extraction.get('confidence', 0.0)
            st.metric('OCR Confidence', f'{ocr_confidence*100:.1f}%')
        with col2:
            notes = text_extraction.get('notes', '')
            if notes:
                st.info(f'📌 Notes: {notes}')
    else:
        st.warning('❌ Text extraction failed: ' + text_extraction.get('message', 'Unknown error'))

st.header('👤 Step 3: Enter ID Details (Manual)')
with st.form('id_details'):
    col1, col2 = st.columns(2)
    with col1:
        id_number = st.text_input('ID Number')
        surname = st.text_input('Surname')
        firstname = st.text_input('First/Given Name')
    with col2:
        date_of_birth = st.text_input('Date of Birth (YYYY-MM-DD)')
        sex = st.selectbox('Sex', ['','M','F','Other'])
        issuing_country = st.text_input('Issuing Country', value='Ghana')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        id_type = st.selectbox('ID Type', ['Ghana Card','Driver\'s License','Voter\'s ID','Passport','Other'])
    with col2:
        save_btn = st.form_submit_button('💾 Save Details')
    with col3:
        validate_btn = st.form_submit_button('✓ Validate')

if save_btn:
    st.success('✓ Details saved in session')

if validate_btn and id_img is not None:
    st.subheader('✓ Validation Results')
    entered = {
        'id_number': id_number,
        'issuing_country': issuing_country,
        'date_of_birth': date_of_birth,
        'surname': surname,
        'firstname': firstname,
        'sex': sex
    }
    
    # Get OCR text
    ocr_text = ''
    if st.session_state.card_analysis and use_gemini:
        ocr_text = st.session_state.card_analysis.get('text_extraction', {}).get('raw_ocr', '')
    
    results = validate_fields(id_type, entered, ocr_text)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader('Field Validation')
        rows = []
        for k, v in results['fields'].items():
            rows.append({
                'Field': k.replace('_', ' ').title(),
                'Status': '✓ Pass' if v['pass'] else '✗ Fail',
                'Message': v['msg']
            })
        df_results = pd.DataFrame(rows)
        st.dataframe(df_results, width='stretch', hide_index=True)
    
    with col2:
        overall = results['overall']
        st.metric('Overall Validation', '✓ PASS' if overall else '✗ FAIL',
                 delta='Valid' if overall else 'Issues found')
    
    # Face matching
    if portrait_img is not None:
        st.subheader('👤 Face Matching')
        with st.spinner('Comparing faces...'):
            match, dist = face_match(portrait_img, id_img)
            if match is not None:
                match_status = '✓ Match' if match else '✗ No Match'
                st.write(f'Face Match Result: {match_status}')
                if dist is not None:
                    st.metric('Face Distance', f'{dist:.3f}', help='Lower values indicate better matches')
            else:
                st.info('Face comparison not available')
    
    # Save submission
    record = {
        'id_type': id_type,
        'id_number': id_number,
        'surname': surname,
        'firstname': firstname,
        'date_of_birth': date_of_birth,
        'validation_overall': bool(results['overall']),
        'face_match': match if portrait_img is not None else None,
        'gemini_card_type': analysis.get('card_type', '') if st.session_state.card_analysis else '',
        'gemini_confidence': analysis.get('card_type_confidence', 0.0) if st.session_state.card_analysis else 0.0
    }
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('📤 Save Submission'):
            ok = save_submission(record)
            if ok:
                st.success('✓ Saved submission to submissions.csv')
            else:
                st.warning('⚠️ Could not save submission')
    with col2:
        if st.button('📋 View as JSON'):
            st.json(record)

st.header('📊 Dashboard / History')
try:
    if os.path.exists('submissions.csv'):
        df_sub = pd.read_csv('submissions.csv')
        st.write(f'Total submissions: {len(df_sub)}')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox('Show recent submissions', value=True):
                st.subheader('Last 10 Submissions')
                st.dataframe(df_sub.tail(10), width='stretch')
        
        with col2:
            st.subheader('Validation Summary')
            if 'validation_overall' in df_sub.columns:
                val_counts = df_sub['validation_overall'].value_counts()
                st.bar_chart(val_counts)
    else:
        st.info('📭 No submissions yet')
except Exception as e:
    st.error(f'Error loading submissions: {e}')

# Footer
st.markdown('---')
st.markdown("""
### About this app
- **Card Detection**: Uses Google Gemini Vision API to identify card type
- **Text Extraction**: Extracts labeled fields based on card labels
- **Validation**: Cross-references extracted data with manual entry
- **Face Matching**: Compares portrait with ID card photo
- **Data Storage**: Submissions saved to CSV for auditing

**Privacy**: Images are sent to Google's API only when you enable Gemini analysis.
""")

