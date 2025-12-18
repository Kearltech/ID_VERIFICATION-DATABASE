"""
Enhanced Streamlit app using Gemini API for card type detection and text extraction.
"""
import streamlit as st
import os
from PIL import Image
import pandas as pd
import json
import os
from datetime import datetime
from verify import (
    pil_from_upload, 
    detect_faces, 
    face_match, 
    validate_fields, 
    save_submission,
    analyze_card_gemini,
    detect_card_type_gemini,
    extract_card_text_gemini,
    process_id_card_face,
    compare_ocr_with_user_input
)

# Database imports
try:
    from database.connection import initialize_database, get_database
    from database.db_utils import get_db_service
    DATABASE_AVAILABLE = True
except Exception as e:
    DATABASE_AVAILABLE = False
    print(f"Database not available: {e}")

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
    
    # Database configuration
    st.markdown('---')
    st.subheader('🗄️ Database')
    if DATABASE_AVAILABLE:
        db_connected = st.session_state.get('db_connected', False)
        if db_connected:
            st.success('✅ Database Connected')
            if st.button('View Statistics'):
                st.session_state['show_stats'] = True
        else:
            st.info('Database available. Configure connection below.')
            with st.expander('Database Settings', expanded=False):
                db_host = st.text_input('Host', value='127.0.0.1')
                db_port = st.number_input('Port', value=3306, min_value=1, max_value=65535)
                db_user = st.text_input('Username', value='root')
                db_password = st.text_input('Password', type='password')
                db_name = st.text_input('Database', value='IDverification')
                
                if st.button('Connect to Database'):
                    try:
                        db = initialize_database(db_host, db_port, db_user, db_password, db_name)
                        if db.test_connection():
                            st.session_state['db_connected'] = True
                            try:
                                db_service = get_db_service()
                                st.session_state['current_user_id'] = db_service.get_or_create_user(
                                    username='default_user',
                                    email='default_user@idverification.local',
                                    full_name='Default User'
                                )
                            except Exception as user_err:
                                st.warning(f'Connected but could not set default user: {user_err}')
                            st.success('Database connected successfully!')
                            st.rerun()
                        else:
                            st.error('Failed to connect to database')
                    except Exception as e:
                        st.error(f'Database connection error: {e}')
    else:
        st.warning('Database module not available. Install dependencies: pip install mysql-connector-python SQLAlchemy cryptography')

# Initialize session state
if 'card_analysis' not in st.session_state:
    st.session_state.card_analysis = None
if 'face_detection_result' not in st.session_state:
    st.session_state.face_detection_result = None
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = 'default_user'

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
                        if face_result.get('highlighted_img'):
                            st.image(face_result['highlighted_img'], 
                                caption=f"{face_result.get('faces_detected', 0)} face(s) detected using {face_result.get('detection_method', 'unknown')}", 
                                width='stretch')
                    with col2:
                        if face_result.get('primary_face'):
                            st.subheader('👤 Extracted Face (Passport Size)')
                            st.image(face_result['primary_face'], 
                                caption='Extracted and resized to standard passport dimensions',
                                width=300)
                    
                    # Show face comparison if passport provided
                    if face_result.get('comparison') and portrait_img:
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
    
    # Map form fields to standard field names based on ID type
    if id_type == 'Ghana Card':
        entered = {
            'ghana_pin': id_number,  # ✅ Use correct field name for Ghana Card
            'surname': surname,
            'firstname': firstname,
            'full_name': f"{firstname} {surname}".strip() if firstname or surname else '',
            'date_of_birth': date_of_birth,
            'sex': sex,
            'issuing_country': issuing_country,
            'id_number': id_number  # Keep for backward compatibility
        }
    elif id_type == 'Passport':
        entered = {
            'passport_number': id_number,
            'surname': surname,
            'firstname': firstname,
            'full_name': f"{firstname} {surname}".strip() if firstname or surname else '',
            'date_of_birth': date_of_birth,
            'sex': sex,
            'issuing_country': issuing_country,
            'id_number': id_number
        }
    elif id_type == "Voter's ID":
        entered = {
            'voter_id_number': id_number,
            'surname': surname,
            'firstname': firstname,
            'full_name': f"{firstname} {surname}".strip() if firstname or surname else '',
            'date_of_birth': date_of_birth,
            'sex': sex,
            'id_number': id_number
        }
    elif id_type == "Driver's License":
        entered = {
            'licence_number': id_number,
            'surname': surname,
            'firstname': firstname,
            'full_name': f"{firstname} {surname}".strip() if firstname or surname else '',
            'date_of_birth': date_of_birth,
            'sex': sex,
            'issuing_country': issuing_country,
            'id_number': id_number
        }
    else:
        entered = {
            'id_number': id_number,
            'issuing_country': issuing_country,
            'date_of_birth': date_of_birth,
            'surname': surname,
            'firstname': firstname,
            'full_name': f"{firstname} {surname}".strip() if firstname or surname else '',
            'sex': sex
        }
    
    # Get OCR text and extracted fields from Gemini
    ocr_text = ''
    ocr_data = {}
    if st.session_state.card_analysis and use_gemini:
        text_extraction = st.session_state.card_analysis.get('text_extraction', {})
        ocr_text = text_extraction.get('raw_ocr', '')
        raw_ocr_fields = text_extraction.get('text_fields', {})
        
        # ✅ Normalize Gemini field names to standard field names
        ocr_data = {}
        for key, value in raw_ocr_fields.items():
            key_lower = key.lower().replace('_', '').replace(' ', '')
            
            # Skip previous/other names - these are not the primary name fields
            if 'previous' in key_lower or 'othername' in key_lower or 'formerlyknownas' in key_lower:
                ocr_data[key] = value  # Keep for reference but don't map to full_name
                continue
            
            # Map Gemini field names to standard names
            if 'personalid' in key_lower or 'personalnumber' in key_lower or 'ghanacard' in key_lower:
                ocr_data['ghana_pin'] = value
            elif 'passport' in key_lower and 'number' in key_lower:
                ocr_data['passport_number'] = value
            elif 'voter' in key_lower or 'voterid' in key_lower:
                ocr_data['voter_id_number'] = value
            elif 'license' in key_lower or 'licence' in key_lower:
                ocr_data['licence_number'] = value
            elif key_lower in ['surname', 'lastname']:
                ocr_data['surname'] = value
            elif key_lower in ['firstname', 'givenname', 'firstgivenname']:
                ocr_data['firstname'] = value
            elif 'fullname' in key_lower or 'name' in key_lower:
                ocr_data['full_name'] = value
            elif 'dateofbirth' in key_lower or 'dob' in key_lower:
                ocr_data['date_of_birth'] = value
            elif key_lower in ['sex', 'gender']:
                ocr_data['sex'] = value
            elif 'nationality' in key_lower:
                ocr_data['nationality'] = value
            elif 'issuing' in key_lower and 'country' in key_lower:
                ocr_data['issuing_country'] = value
            else:
                # Keep original key for unmapped fields
                ocr_data[key] = value
        
        # Construct full_name from firstname and surname if not already set
        if 'full_name' not in ocr_data and ('firstname' in ocr_data or 'surname' in ocr_data):
            fname = ocr_data.get('firstname', '').strip()
            sname = ocr_data.get('surname', '').strip()
            if fname or sname:
                ocr_data['full_name'] = f"{fname} {sname}".strip()
    
    # Traditional field validation (format checks only)
    results = validate_fields(id_type, entered, ocr_text)
    
    # Add OCR comparison if we have extracted fields (THIS IS THE PRIMARY VALIDATION)
    ocr_comparison = None
    if ocr_data:
        st.info('🤖 Comparing user input with Gemini-extracted data...')
        ocr_comparison = compare_ocr_with_user_input(id_type, entered, ocr_data)
    
    # ✅ Determine final validation status
    # If OCR comparison is available, it takes precedence over basic validation
    if ocr_comparison:
        final_valid = ocr_comparison['valid']
        final_message = 'OCR Match Verified' if final_valid else 'OCR Mismatch Detected'
    else:
        final_valid = results['overall']
        final_message = 'Format Valid' if final_valid else 'Format Issues'
    
    # Display overall validation status at the top
    if final_valid:
        st.success(f'✅ **VALIDATION PASSED** - {final_message}')
    else:
        st.error(f'❌ **VALIDATION FAILED** - {final_message}')
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader('Field Validation (Format Check)')
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
        st.metric('Format Validation', '✓ PASS' if overall else '✗ FAIL',
                 delta='Valid Format' if overall else 'Format Issues')
    
    # ✅ Display OCR comparison results if available (PRIMARY VALIDATION)
    if ocr_comparison:
        st.subheader('🔍 OCR vs User Input Comparison (Primary Validation)')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✓ Matched", len(ocr_comparison['passed_fields']), 
                     delta=None, delta_color="normal")
        with col2:
            failed_count = len(ocr_comparison['failed_fields'])
            st.metric("✗ Mismatched", failed_count,
                     delta=None, delta_color="inverse")
        with col3:
            st.metric("? Missing", len(ocr_comparison['missing_fields']),
                     delta=None, delta_color="off")
        
        # Show detailed field comparison prominently
        if ocr_comparison['details']:
            st.subheader("📊 Field-by-Field Comparison Details")
            for field_name, details in ocr_comparison['details'].items():
                # Color code based on match status
                if details['match']:
                    with st.container():
                        col_a, col_b, col_c = st.columns([1, 3, 3])
                        with col_a:
                            st.success("✓ MATCH")
                        with col_b:
                            st.write(f"**{field_name.replace('_', ' ').title()}**")
                        with col_c:
                            st.write(f"`{details['user_value']}`")
                else:
                    with st.container():
                        st.error(f"❌ **MISMATCH: {field_name.replace('_', ' ').title()}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**👤 You Entered:**")
                            st.code(details['user_value'], language=None)
                        with col2:
                            st.write(f"**🤖 Card Shows:**")
                            st.code(details['ocr_value'], language=None)
                        st.caption(f"⚠️ {details['message']} ({details['type']} comparison)")
                st.divider()
    else:
        st.warning('⚠️ No OCR data available for comparison. Please ensure Gemini API is enabled and card analysis completed.')
    
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
    
    # Save to database if connected
    if DATABASE_AVAILABLE and st.session_state.get('db_connected', False):
        try:
            db_service = get_db_service()
            
            # Prepare form data
            form_data = {
                'id_number': id_number,
                'surname': surname,
                'firstname': firstname,
                'date_of_birth': date_of_birth,
                'sex': sex,
                'issuing_country': issuing_country
            }
            
            # Prepare validation results
            validation_results = {
                'overall': bool(results['overall']),
                'fields': results['fields']
            }
            
            # Prepare face match results
            face_match_results = None
            if portrait_img is not None and match is not None:
                face_match_results = {
                    'match': match,
                    'distance': dist
                }
            
            # Prepare Gemini results
            gemini_results = None
            if st.session_state.card_analysis:
                gemini_results = {
                    'card_type': analysis.get('card_type', ''),
                    'confidence': analysis.get('card_type_confidence', 0.0),
                    'text_fields': analysis.get('text_extraction', {}).get('text_fields', {})
                }
            
            # Save to database
            submission_id = db_service.save_submission(
                user_id=st.session_state.current_user_id,
                id_type=id_type,
                form_data=form_data,
                validation_results=validation_results,
                ocr_results=ocr_comparison,
                face_match_results=face_match_results,
                gemini_results=gemini_results
            )
            
            # Save detailed validation logs
            db_service.save_validation_logs(submission_id, results['fields'])
            
            # Log audit event
            db_service.log_audit_event(
                event_type='validation_completed',
                event_category='validation',
                description=f'ID verification completed for {id_type}',
                user_id=st.session_state.current_user_id,
                severity='info',
                event_data={
                    'submission_id': submission_id,
                    'validation_result': bool(results['overall']),
                    'id_type': id_type
                }
            )
            
            st.success(f'✅ Submission saved to database (ID: {submission_id[:8]}...)')
            
        except Exception as e:
            st.warning(f'⚠️ Database save failed: {e}. Falling back to CSV.')
            save_submission(record)
    else:
        # Fallback to CSV
        save_submission(record)
    
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
# Statistics Dashboard
if DATABASE_AVAILABLE and st.session_state.get('show_stats', False):
    st.markdown('---')
    st.header('📊 Statistics Dashboard')
    
    try:
        db_service = get_db_service()
        stats = db_service.get_user_statistics(st.session_state.current_user_id, days=30)
        
        # Submission statistics
        st.subheader('Verification Statistics (Last 30 Days)')
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Submissions", stats['submissions']['total_submissions'])
        with col2:
            st.metric("Passed", stats['submissions']['passed'], 
                     delta=f"{stats['submissions']['success_rate']}%")
        with col3:
            st.metric("Failed", stats['submissions']['failed'])
        with col4:
            st.metric("Success Rate", f"{stats['submissions']['success_rate']}%")
        
        # ID Type breakdown
        if stats['submissions']['id_type_breakdown']:
            st.subheader('Submissions by ID Type')
            breakdown_df = pd.DataFrame(
                list(stats['submissions']['id_type_breakdown'].items()),
                columns=['ID Type', 'Count']
            )
            st.bar_chart(breakdown_df.set_index('ID Type'))
        
        # API Usage statistics
        st.subheader('API Usage Statistics')
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total API Calls", stats['api_usage']['total_api_calls'])
        with col2:
            st.metric("Total Tokens", f"{stats['api_usage']['total_tokens']:,}")
        with col3:
            st.metric("Total Cost", f"${stats['api_usage']['total_cost_usd']:.4f}")
        
        # Recent submissions
        st.subheader('Recent Submissions')
        submissions = db_service.get_user_submissions(st.session_state.current_user_id, limit=10)
        
        if submissions:
            submission_data = []
            for sub in submissions:
                submission_data.append({
                    'Date': sub.created_at.strftime('%Y-%m-%d %H:%M'),
                    'ID Type': sub.id_type,
                    'Result': '✅ Valid' if sub.validation_overall else '❌ Invalid',
                    'Face Match': '✅' if sub.face_match else '❌' if sub.face_match is not None else '-',
                    'Confidence': f"{sub.gemini_confidence:.1%}" if sub.gemini_confidence else '-'
                })
            
            df = pd.DataFrame(submission_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info('No submissions yet')
        
        if st.button('Close Statistics'):
            st.session_state['show_stats'] = False
            st.rerun()
            
    except Exception as e:
        st.error(f'Error loading statistics: {e}')

st.header('📊 Dashboard / History')
try:
    if os.path.exists('submissions.csv'):
        try:
            df_sub = pd.read_csv('submissions.csv', on_bad_lines='skip')
        except Exception as parse_err:
            st.error(f"Error loading submissions.csv: {parse_err}")
            if st.button('🧹 Reset corrupted CSV'):
                try:
                    os.remove('submissions.csv')
                    st.success('submissions.csv removed. New submissions will create a fresh file.')
                    st.rerun()
                except Exception as rm_err:
                    st.error(f'Could not remove submissions.csv: {rm_err}')
            # Stop rendering the CSV dashboard if corrupted
            st.stop()

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

