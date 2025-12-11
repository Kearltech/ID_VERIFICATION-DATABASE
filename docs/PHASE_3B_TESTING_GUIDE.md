# Phase 3B Manual Testing Guide

## Quick Start

1. **Launch the app:**
   ```powershell
   cd 'c:\Users\Hp\Desktop\mobile_dev\ML\ID_-verification'
   python -m streamlit run app.py
   ```

2. **Access in browser:** http://localhost:8501

## Test Scenarios

### Scenario 1: Ghana Card Verification ✅

**Steps:**
1. Select "Ghana Card" from ID type dropdown
2. Observe dynamic form fields appear:
   - Ghana Card Number (PIN)
   - Surname
   - First Name
   - Middle Name (optional)
   - Date of Birth
   - Sex (dropdown: M/F/O)
   - Expiry Date
   - Nationality (optional)
   - Height (optional)

3. **Upload a Ghana Card image** (portrait)

4. **Fill form with test data:**
   ```
   Ghana Card Number: GHA-123456789-0
   Surname: Mensah
   First Name: Kwame
   Date of Birth: 1990-01-15
   Sex: M
   Expiry Date: 2030-01-15
   ```

5. **Submit and verify:**
   - ✅ Form validation passes
   - ✅ OCR extraction runs
   - ✅ Comparison metrics show (Passed/Failed/Missing counts)
   - ✅ Overall status displays (Success/Failure)
   - ✅ Expandable details show field-by-field comparison
   - ✅ Face matching results display

**Expected Results:**
- Dynamic form renders with 9 fields
- Sex field is dropdown (not text input)
- Help text shows field categories
- Validation uses Ghana Card specific rules
- OCR comparison shows intelligent matching

### Scenario 2: Passport Verification 🛂

**Steps:**
1. Select "Ghana Passport" from dropdown
2. Form should dynamically change to show:
   - Passport Number
   - Surname
   - Given Names
   - Nationality
   - Date of Birth
   - Date of Issue
   - Date of Expiry
   - Sex (dropdown)
   - Place of Birth (optional)
   - Authority

3. **Upload passport image**

4. **Fill with test data:**
   ```
   Passport Number: G1234567
   Surname: Adjei
   Given Names: Akosua
   Nationality: Ghanaian
   Date of Birth: 1985-03-20
   Date of Issue: 2020-01-10
   Date of Expiry: 2030-01-10
   Sex: F
   ```

5. **Submit and check results**

**Expected Results:**
- Different fields than Ghana Card
- Passport-specific validation rules
- OCR comparison for passport format

### Scenario 3: Bank Card with Sensitive Data 💳

**Steps:**
1. Select "Bank Card" from dropdown
2. Form shows:
   - Card Number
   - Cardholder Name
   - Expiry Date
   - CVV (should be password input)

3. **Fill with test data:**
   ```
   Card Number: 4532-1234-5678-9010
   Cardholder Name: KWAME MENSAH
   Expiry Date: 2025-12
   CVV: 123 (should appear as dots/asterisks)
   ```

4. **Verify CVV is masked**

**Expected Results:**
- CVV field shows `type='password'`
- Input appears as dots (•••)
- Only 4 fields (minimal for bank card)

### Scenario 4: Invalid Data Handling ⚠️

**Test 1: Invalid Ghana PIN Format**
```
Ghana Card Number: INVALID
→ Should show error: Invalid format
```

**Test 2: Missing Required Field**
```
Leave Ghana Card Number empty
→ Should show error: Required field
```

**Test 3: Invalid Date Format**
```
Date of Birth: 01/01/1990 (wrong format)
→ Should suggest: Use YYYY-MM-DD format
```

**Test 4: No Portrait Image**
```
Fill form but don't upload image
→ Should prompt: Upload portrait image
```

## Testing Checklist

### Form Generation ✅
- [ ] Ghana Card: 9 fields render correctly
- [ ] Ghana Passport: 10 fields render correctly
- [ ] Voter ID: 8 fields render correctly
- [ ] Driver's License: 9 fields render correctly
- [ ] Bank Card: 4 fields render correctly

### Field Type Detection ✅
- [ ] Sex/Gender fields show as dropdown
- [ ] Date fields show format hint (YYYY-MM-DD)
- [ ] CVV shows as password input
- [ ] Standard fields show as text input
- [ ] Help text displays field category

### Validation ✅
- [ ] Ghana PIN format validated (GHA-XXXXXXXXX-X)
- [ ] Passport number format validated
- [ ] Required fields enforced
- [ ] Date format validated (YYYY-MM-DD)
- [ ] Sex accepts M/F/O

### OCR Comparison Display ✅
- [ ] Metrics show: Passed count
- [ ] Metrics show: Failed count
- [ ] Metrics show: Missing count
- [ ] Overall status displays (Success/Failure)
- [ ] Detailed comparison expandable
- [ ] Passed fields: Green background, ✓ icon
- [ ] Failed fields: Red background, ✗ icon
- [ ] Missing fields: Yellow background, ? icon
- [ ] Shows user value vs OCR value
- [ ] Shows comparison type (Exact/Date/Fuzzy/Enum)

### Face Matching Display ✅
- [ ] Shows confidence score
- [ ] Shows 👤 emoji
- [ ] Color-coded status
- [ ] Clear match/no-match indication

### Error Handling ✅
- [ ] Graceful fallback if field mapping fails
- [ ] Clear error messages with field names
- [ ] Icons in error messages (⚠️)
- [ ] No crashes on invalid data
- [ ] Session state preserved on errors

## OCR Comparison Testing

### Test Different Match Types:

**1. Exact Match (Ghana PIN)**
```
User Input: GHA-123456789-0
OCR Extract: GHA-123456789-0
→ Should show: ✓ Exact match
```

**2. Date Normalization**
```
User Input: 1990-01-15 (YYYY-MM-DD)
OCR Extract: 15/01/1990 (DD/MM/YYYY)
→ Should show: ✓ Date match (normalized)
```

**3. Fuzzy Name Matching**
```
User Input: Kwame Mensah
OCR Extract: Kwame  Mensah (extra space)
→ Should show: ✓ Fuzzy match 95%
```

**4. Enum Comparison (Sex)**
```
User Input: M
OCR Extract: Male
→ Should show: ✓ Enum match
```

**5. Mismatch Detection**
```
User Input: GHA-123456789-0
OCR Extract: GHA-999999999-9
→ Should show: ✗ Mismatch
```

## Edge Cases

### Empty Data
- [ ] Empty user data → Shows missing fields
- [ ] Empty OCR data → Shows all fields missing
- [ ] Both empty → Graceful handling

### Special Characters
- [ ] Names with hyphens: O'Brien-McDonald
- [ ] Names with apostrophes: D'Angelo
- [ ] Names with dots: Dr. Smith Jr.
- [ ] Accented characters: Françoise

### Format Variations
- [ ] Date: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
- [ ] Sex: M/Male, F/Female, O/Other
- [ ] License class: A/A1, B/B1, etc.

## Performance Testing

- [ ] Form renders quickly (<1s)
- [ ] ID type switch is instant
- [ ] Validation is fast (<100ms)
- [ ] OCR comparison completes quickly
- [ ] No lag when switching ID types
- [ ] Session state persists correctly

## Browser Compatibility

Test in:
- [ ] Chrome
- [ ] Firefox
- [ ] Edge
- [ ] Safari (if available)

## Mobile Responsiveness

- [ ] Forms display correctly on mobile
- [ ] Dropdowns work on touch screens
- [ ] Upload button functional on mobile
- [ ] Metrics layout adapts to small screens

## Accessibility

- [ ] Field labels are clear
- [ ] Help text is readable
- [ ] Error messages are descriptive
- [ ] Color coding has sufficient contrast
- [ ] Keyboard navigation works

## Known Issues

1. **Test file needs updates**: ID type keys in tests need to match registry ('Ghana Card' not 'ghana_card')
2. **Date format**: Only YYYY-MM-DD currently accepted in forms (OCR comparison handles others)
3. **Optional fields**: May show in errors even when not required

## Troubleshooting

### App won't start
```powershell
# Check streamlit installation
pip install streamlit

# Run with python -m
python -m streamlit run app.py
```

### Import errors
```powershell
# Check all dependencies
pip install -r requirements.txt
```

### Form not rendering
- Check browser console for JavaScript errors
- Clear browser cache
- Restart streamlit server

### OCR not extracting
- Ensure portrait image is clear
- Check image format (JPG/PNG)
- Verify image size (not too large)

## Success Criteria

✅ **Phase 3B is successful if:**
1. All 5 ID types generate forms dynamically
2. Field types auto-detect correctly
3. Validation uses ID-specific rules
4. OCR comparison displays with metrics
5. Detailed field comparison shows correctly
6. No crashes on invalid data
7. User experience is intuitive
8. Performance is acceptable (<2s total)

## Reporting Issues

If you find issues:
1. Note the ID type selected
2. Record the exact input values
3. Check browser console for errors
4. Capture screenshots of unexpected behavior
5. Check logs for error messages

---

**Happy Testing! 🎉**

The app should now provide a smooth, intelligent ID verification experience with full transparency into what matches and what doesn't.
