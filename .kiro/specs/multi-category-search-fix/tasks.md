# Implementation Plan

- [x] 1. Refactor category extraction logic

  - [x] 1.1 Create unified `_extract_all_categories()` method


    - Replace `_extract_multiple_categories()` and `_extract_category_name()` with single method
    - Implement noise word filtering (varmı, var mı, sanırım, galiba, etc.)
    - Implement Turkish character normalization function
    - Add shape letter detection (L, T, U, C, H, V, S, F, D, M, K, R) with regex patterns
    - Add special shape detection (DAİRE, DAIRESEL) with flexible patterns
    - Add product category detection (KÜPEŞTE, etc.) by catalog matching
    - Return all found categories without minimum count requirement
    - Add comprehensive logging for each detection step



    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 3.1_


  
  - [ ] 1.2 Remove deprecated methods
    - Remove `_extract_multiple_categories()` method

    - Remove `_extract_category_name()` method (keep module-level function if used elsewhere)


    - Update all references to use new `_extract_all_categories()` method
    - _Requirements: 3.1, 3.2_

- [ ] 2. Update catalog answer formatter
  - [x] 2.1 Refactor `_format_catalog_answer()` method

    - Replace category extraction calls with `_extract_all_categories()`
    - Implement decision logic: 2+ categories → combination, 1 category → single, 0 → general
    - Update logging to show extracted categories and chosen search method
    - Ensure company filter is still applied correctly

    - _Requirements: 1.1, 1.2, 3.2, 3.3_


  
  - [ ] 2.2 Improve error messages and fallback handling
    - Update combination search fallback when no results found
    - Ensure appropriate user messages for each scenario
    - Add result count logging
    - _Requirements: 1.4, 4.1_

- [ ] 3. Verify combination search logic
  - [ ] 3.1 Review `_search_by_category_combination()` method
    - Verify case-insensitive matching is working
    - Ensure all categories must be present in profile
    - Add additional logging if needed
    - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 4. Add comprehensive tests
  - [ ]* 4.1 Create unit tests for category extraction
    - Test single shape category extraction ("L şeklinde")
    - Test single product category extraction ("küpeşte")
    - Test shape + product combination ("daire şeklinde küpeşte")
    - Test Turkish character variations ("kupeste" → "KÜPEŞTE")
    - Test noise word filtering
    - Test multiple shape patterns
    - Test no categories found scenario
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 4.2 Create integration tests for search functionality
    - Test combination search returns correct results


    - Test combination search filters correctly (all categories present)


    - Test fallback to general search when combination fails
    - Test single category search still works
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3_
  
  - [ ]* 4.3 Update existing test file
    - Add new test cases to `backend/test_chat_combinations.py`
    - Verify "daire şeklinde küpeşte" returns results
    - Verify other combination queries work correctly
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 5. Manual testing and validation
  - [ ] 5.1 Test critical queries
    - Test "daire şeklinde küpeşte varmı" returns ~76 profiles
    - Test "L şeklinde cam tutucu" returns correct combinations
    - Test "T şeklinde kapak profili" returns correct combinations
    - Test "dairesel küpeşte" works same as "daire şeklinde küpeşte"
    - Test "kupeste daire" handles Turkish character variations
    - Verify logs show correct category extraction
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_
