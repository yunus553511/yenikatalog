# Implementation Plan

- [x] 1. Update CatalogProfile data model to normalize field names


  - Modify `CatalogProfile.to_dict()` method in `backend/utils/catalog_parser.py`
  - Add `code` field that maps to `profile_no` value
  - Keep `profile_no` field for backward compatibility
  - Ensure both fields contain the same value
  - _Requirements: 1.3, 2.2_




- [x] 2. Enhance text formatter to support both Profile and Dict types





  - [x] 2.1 Update `format_profile_for_display()` function in `backend/utils/text_formatter.py`


    - Add type checking using `hasattr()` to detect Profile objects vs dicts
    - Extract `code` field from both Profile objects and dicts
    - Handle fallback to `profile_no` if `code` is not present
    - Support profiles without dimensions (catalog profiles)
    - Return formatted string with profile code prominently displayed
    - _Requirements: 1.1, 1.3, 2.3_

  - [ ]* 2.2 Write unit tests for format_profile_for_display function
    - Test with Profile object input
    - Test with dict input containing `code` field
    - Test with dict input containing only `profile_no` field
    - Test with missing code/profile_no fields (should show 'N/A')


    - Test with profiles that have dimensions


    - Test with profiles without dimensions


    - _Requirements: 2.3_

- [ ] 3. Update RAG service to use normalized field names
  - Modify `_format_catalog_answer()` method in `backend/services/rag_service.py`
  - Change `profile.get('profile_no')` to `profile.get('code')`
  - Ensure consistent formatting across all profile types
  - _Requirements: 1.1, 1.2, 2.2_

- [x]* 4. Add integration tests for catalog profile display


  - Create test file `backend/test_catalog_display.py`
  - Test catalog profile search returns profiles with `code` field



  - Test chat response includes profile codes in formatted message
  - Test both standard and catalog profiles display codes correctly
  - _Requirements: 1.1, 1.2_

- [ ] 5. Manual verification of frontend display
  - Start backend server
  - Open frontend in browser
  - Click on a catalog category button (e.g., "Ray", "Cam Tutucu")
  - Verify profile codes appear in chat response
  - Test standard profile search to ensure codes still display
  - Verify no regression in existing functionality
  - _Requirements: 1.1, 1.2_
