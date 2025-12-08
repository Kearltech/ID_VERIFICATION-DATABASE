import streamlit as st
from PIL import Image
import pandas as pd
from verify import (
    pil_from_upload, ocr_text_from_image, detect_faces, face_match, 
    validate_fields, save_submission, compare_ocr_with_user_input
)
import os

# Phase 2 Integration
from logger_config import setup_logging, audit_logger
from validators import InputValidator
from exceptions import create_error, ValidationError, CardDetectionError

# Phase 3B Integration
from id_field_mappings import (
    get_user_input_fields, get_id_type_fields, 
    ID_TYPE_REGISTRY, FieldCategory
)

# Setup logging
setup_logging()
validator = InputValidator()

st.set_page_config(page_title='ID Verification', layout='centered')

st.title('ID Verification')
st.write('Upload a portrait and an ID card, enter ID details, and run validation.')

st.header('1) Upload Portrait')
portrait_file = st.file_uploader('Upload a passport-style portrait', type=['png','jpg','jpeg'], key='portrait')
portrait_img = pil_from_upload(portrait_file)
if portrait_img is not None:
    st.image(portrait_img, caption='Uploaded portrait', width=220)
    audit_logger.logger.info('Portrait uploaded successfully', extra={'event': 'portrait_upload', 'size': portrait_img.size})
    faces = detect_faces(portrait_img)
    st.write('Faces detected:', len(faces))
    audit_logger.logger.debug(f'Face detection completed: {len(faces)} faces found', extra={'event': 'face_detection', 'count': len(faces)})
else:
    st.info('No portrait uploaded.')
    audit_logger.logger.debug('No portrait uploaded or upload failed', extra={'event': 'portrait_upload_failed'})

st.header('2) Select ID Type')
id_type = st.selectbox('Select ID type', list(ID_TYPE_REGISTRY.keys()))

st.header('3) Enter ID Details')
st.write(f"**{ID_TYPE_REGISTRY[id_type]['description']}**")

# Dynamic form generation based on selected ID type
with st.form('id_details'):
    form_data = {}
    
    # Get user input fields for this ID type
    try:
        # Get field names for selected ID type
        user_field_names = get_user_input_fields(id_type)
        # Get all fields with their metadata
        all_fields = get_id_type_fields(id_type)
        
        # Generate form fields dynamically
        for field_name in user_field_names:
            field_obj = all_fields[field_name]
            # Determine input type based on field characteristics
            if 'sex' in field_name.lower() or 'gender' in field_name.lower():
                value = st.selectbox(
                    field_obj.display_name,
                    ['', 'M', 'F', 'O'],
                    key=field_name,
                    help=f"Category: {field_obj.category.value}"
                )
            elif 'date' in field_name.lower():
                value = st.text_input(
                    field_obj.display_name,
                    placeholder='YYYY-MM-DD',
                    key=field_name,
                    help=f"Format: YYYY-MM-DD | Category: {field_obj.category.value}"
                )
            elif field_obj.category == FieldCategory.SECURITY and field_obj.sensitive:
                # Sensitive fields like CVV
                value = st.text_input(
                    field_obj.display_name,
                    type='password',
                    key=field_name,
                    help="⚠️ Sensitive field - will not be stored"
                )
            else:
                # Regular text input
                value = st.text_input(
                    field_obj.display_name,
                    key=field_name,
                    help=f"Category: {field_obj.category.value}"
                )
            
            if value:  # Only add non-empty values
                form_data[field_name] = value
    
    except Exception as e:
        # Fallback to basic fields if field mapping fails
        audit_logger.logger.error(f'Dynamic form generation failed: {e}', extra={
            'event': 'form_generation_error',
            'id_type': id_type
        })
        st.warning("Using basic form fields")
        form_data = {
            'id_number': st.text_input('ID Number'),
            'surname': st.text_input('Surname'),
            'firstname': st.text_input('First Name'),
            'date_of_birth': st.text_input('Date of Birth (YYYY-MM-DD)'),
        }
    
    save_btn = st.form_submit_button('Save Details')

if save_btn:
    audit_logger.logger.info('ID details form submitted', extra={
        'event': 'form_submit',
        'id_type': id_type,
        'fields_count': len(form_data)
    })
    
    # Validate form data using ID-type-specific validation
    is_valid, validation_errors, cleaned_data = validator.validate_form_data(form_data, id_type=id_type)
    
    if is_valid:
        st.success('✓ Details saved and validated successfully')
        # Store in session state for later use
        st.session_state['form_data'] = cleaned_data
        st.session_state['id_type'] = id_type
        audit_logger.logger.info('Form validation passed', extra={
            'event': 'form_valid',
            'fields_count': len(cleaned_data)
        })
    else:
        st.error(f'❌ Validation errors found ({len(validation_errors)}):')
        for field, error_msg in validation_errors.items():
            st.error(f"  • **{field}**: {error_msg}")
        audit_logger.logger.warning(f'Form validation failed with {len(validation_errors)} errors', extra={
            'event': 'form_invalid',
            'errors': validation_errors
        })

st.header('4) Upload ID Card')
id_file = st.file_uploader('Upload ID card (image or PDF)', type=['png','jpg','jpeg','pdf'], key='idcard')
id_img = None
ocr_text = ''
ocr_conf = 0.0
if id_file is not None:
    audit_logger.logger.info('ID card uploaded', extra={
        'event': 'idcard_upload',
        'file_name': id_file.name,
        'file_type': id_file.type
    })
    id_img = pil_from_upload(id_file)
    if id_img is not None:
        st.image(id_img, caption='Uploaded ID image', width=320)
        audit_logger.logger.debug('ID card image converted successfully', extra={'event': 'idcard_converted', 'size': id_img.size})
    else:
        st.info('Uploaded file cannot be previewed as image.')
        audit_logger.logger.warning('ID card upload: file could not be converted to image', extra={'event': 'idcard_convert_failed', 'file_name': id_file.name})
    
    ocr_text, ocr_conf = ocr_text_from_image(id_img)
    if ocr_text:
        st.subheader('OCR (excerpt)')
        st.write(ocr_text[:1000])
        audit_logger.logger.info('OCR extraction successful', extra={
            'event': 'ocr_extraction',
            'confidence': ocr_conf,
            'text_length': len(ocr_text)
        })
    else:
        audit_logger.logger.warning('OCR extraction failed or returned empty', extra={'event': 'ocr_failed'})

st.header('5) Validate')
if st.button('Run validation'):
    audit_logger.logger.info('Validation started', extra={'event': 'validation_start', 'id_type': id_type})
    
    # Get form data from session or use current values
    user_data = st.session_state.get('form_data', form_data)
    
    # Traditional field validation
    results = validate_fields(id_type, user_data, ocr_text)
    
    st.subheader('📋 Field-by-field Validation Results')
    rows = []
    for k, v in results['fields'].items():
        rows.append({'Field': k, 'Status': '✓' if v['pass'] else '✗', 'Message': v['msg']})
    df_results = pd.DataFrame(rows)
    st.table(df_results)
    
    # Phase 3B: OCR Comparison
    if ocr_text and user_data:
        st.subheader('🔍 OCR vs User Input Comparison')
        
        try:
            # Extract structured data from OCR text (simplified - in production, use Gemini)
            ocr_data = user_data.copy()  # Placeholder - real OCR extraction would parse ocr_text
            
            # Compare OCR with user input
            comparison = compare_ocr_with_user_input(id_type, user_data, ocr_data)
            
            # Display comparison results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✓ Passed", len(comparison['passed_fields']), 
                         delta=None, delta_color="normal")
            with col2:
                st.metric("✗ Failed", len(comparison['failed_fields']),
                         delta=None, delta_color="inverse")
            with col3:
                st.metric("? Missing", len(comparison['missing_fields']),
                         delta=None, delta_color="off")
            
            # Overall status
            if comparison['valid']:
                st.success(f"✓ **VERIFICATION SUCCESSFUL** - {comparison['message']}")
            else:
                st.error(f"✗ **VERIFICATION FAILED** - {comparison['message']}")
            
            # Detailed field comparison
            if comparison['details']:
                with st.expander("📊 Detailed Field Comparison"):
                    for field_name, details in comparison['details'].items():
                        status_icon = "✓" if details['match'] else "✗"
                        st.write(f"**{status_icon} {field_name}**")
                        st.write(f"  - User: `{details['user_value']}`")
                        st.write(f"  - OCR: `{details['ocr_value']}`")
                        st.write(f"  - Result: {details['message']} ({details['type']} comparison)")
                        st.divider()
            
            audit_logger.logger.info('OCR comparison completed', extra={
                'event': 'ocr_comparison_ui',
                'valid': comparison['valid'],
                'passed': len(comparison['passed_fields']),
                'failed': len(comparison['failed_fields'])
            })
        
        except Exception as e:
            st.warning(f"OCR comparison failed: {str(e)}")
            audit_logger.logger.error(f'OCR comparison error in UI: {e}', extra={
                'event': 'ocr_comparison_ui_error'
            })
    
    # Face matching
    match, dist = face_match(portrait_img, id_img)
    st.subheader('👤 Face Matching')
    if match is not None:
        if match:
            st.success(f'✓ Face match confirmed (distance: {dist:.3f})')
        else:
            st.error(f'✗ Face mismatch detected (distance: {dist:.3f})')
    else:
        st.warning('⚠️ Face matching not available')
    
    audit_logger.logger.info('Face matching completed', extra={
        'event': 'face_match',
        'match': bool(match) if match is not None else None,
        'distance': float(dist) if dist is not None else None
    })
    
    # Save submission
    record = {
        'id_type': id_type,
        **{k: v for k, v in user_data.items() if k in ['id_number', 'surname', 'firstname', 'date_of_birth']},
        'validation_overall': bool(results['overall']),
        'face_match': bool(match) if match is not None else None,
        'ocr_conf': float(ocr_conf or 0.0)
    }
    ok = save_submission(record)
    if ok:
        st.success('💾 Saved submission to submissions.csv')
        audit_logger.logger.info('Submission saved successfully', extra={
            'event': 'submission_saved',
            'id_type': id_type,
            'validation_passed': bool(results['overall'])
        })
    else:
        st.warning('⚠️ Could not save submission locally.')
        audit_logger.logger.error('Failed to save submission', extra={'event': 'submission_save_failed', 'id_type': id_type})

st.header('Admin / Dashboard')
try:
    if os.path.exists('submissions.csv'):
        df_sub = pd.read_csv('submissions.csv')
        st.dataframe(df_sub.tail(20))
    else:
        st.info('No saved submissions yet.')
except Exception as e:
    st.error(f'Error loading submissions: {e}')

