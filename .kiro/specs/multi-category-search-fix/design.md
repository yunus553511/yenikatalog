# Design Document: Multi-Category Search Fix

## Overview

The current implementation has a critical bug where multi-category searches (e.g., "daire şeklinde küpeşte") fail because the category extraction logic is split between two methods that don't communicate properly. The `_extract_multiple_categories()` method finds categories but returns an empty list if fewer than 2 are found, while `_extract_category_name()` finds a single category separately. This causes the system to perform a single-category search instead of a combination search.

**Root Cause:**
- Query: "daire şeklinde küpeşte varmı"
- `_extract_multiple_categories()` finds: KÜPEŞTE (logs it, but returns [] because only 1 found)
- `_extract_category_name()` finds: DAİRE
- Result: Searches only by DAİRE, ignoring KÜPEŞTE → 0 results

**Solution:**
Consolidate category extraction into a single method that finds ALL categories (shape, product, standard) and returns them regardless of count. The calling code will decide whether to use combination search (2+) or single-category search (1).

## Architecture

### Current Flow (Broken)
```
User Query: "daire şeklinde küpeşte"
    ↓
_format_catalog_answer()
    ↓
_extract_multiple_categories() → finds KÜPEŞTE → returns [] (needs 2+)
    ↓
_extract_category_name() → finds DAİRE
    ↓
Single-category search by DAİRE only
    ↓
0 results (wrong!)
```

### New Flow (Fixed)
```
User Query: "daire şeklinde küpeşte"
    ↓
_format_catalog_answer()
    ↓
_extract_all_categories() → finds [KÜPEŞTE, DAİRE]
    ↓
if len(categories) >= 2:
    Combination search by KÜPEŞTE + DAİRE
else if len(categories) == 1:
    Single-category search
    ↓
76 results (correct!)
```

## Components and Interfaces

### 1. Enhanced Category Extraction Method

**Method:** `_extract_all_categories(query: str) -> List[str]`

**Purpose:** Single unified method to extract ALL categories from a query

**Logic Flow:**
1. Clean query (remove noise words: varmı, var mı, sanırım, galiba, etc.)
2. Normalize Turkish characters for consistent matching
3. Extract shape categories (L, T, U, etc.) using regex patterns
4. Extract special shape categories (DAİRE, DAIRESEL) using regex patterns
5. Extract product categories (KÜPEŞTE, KAPAK, CAM TUTUCU, etc.) by matching against catalog
6. Return ALL found categories (no minimum count requirement)

**Pattern Matching:**

Shape Letters (L, T, U, C, H, V, S, F, D, M, K, R):
- Pattern 1: `"X şeklinde"`, `"X şekl"`, `"X sekl"`
- Pattern 2: `"şekil X"`, `"şekli X"`
- Pattern 3: `"X şekilli"`

Special Shapes:
- DAİRE: `"daire"`, `"dairesel"`, `"daire şeklinde"`
- Match against catalog categories containing "daire" or "dairesel"

Product Categories:
- KÜPEŞTE: `"küpeşte"`, `"kupeşte"`, `"küpeste"`, `"kupeste"`
- Others: Direct string matching against all catalog categories

**Return Value:**
- List of category names (uppercase, as they appear in catalog)
- Empty list if no categories found
- No minimum count requirement

### 2. Updated Catalog Answer Formatter

**Method:** `_format_catalog_answer(query: str, top_k: int = 20) -> str`

**Changes:**
1. Replace `_extract_multiple_categories()` call with `_extract_all_categories()`
2. Remove `_extract_category_name()` call (redundant)
3. Decision logic:
   - If `len(categories) >= 2`: Use combination search
   - If `len(categories) == 1`: Use single-category search
   - If `len(categories) == 0`: Use general search

**Pseudo-code:**
```python
def _format_catalog_answer(self, query: str, top_k: int = 20) -> str:
    # Extract ALL categories
    categories = self._extract_all_categories(query)
    logger.info(f"Extracted categories: {categories}")
    
    # Extract company filter
    companies = self._extract_companies_from_query(query)
    
    # Decision tree
    if len(categories) >= 2:
        # Combination search
        results = self._search_by_category_combination(categories)
        if not results:
            # Fallback to general search
            results = catalog_service.search_profiles(query, limit=top_k)
        return self._format_combination_results(categories, results)
    
    elif len(categories) == 1:
        # Single-category search
        results = catalog_service.get_profiles_by_category(categories[0], companies)
        return self._format_single_category_results(categories[0], results)
    
    else:
        # General search
        results = catalog_service.search_profiles(query, limit=top_k)
        return self._format_general_results(results)
```

### 3. Category Combination Search

**Method:** `_search_by_category_combination(categories: List[str]) -> List[Dict]`

**Current Implementation:** Already correct - filters profiles that belong to ALL specified categories

**No changes needed** - this method works correctly once it receives the proper category list

## Data Models

### Category Extraction Result
```python
{
    "categories": List[str],  # e.g., ["KÜPEŞTE", "DAİRE"]
    "query_cleaned": str,     # Cleaned query for logging
    "companies": List[str] | None  # Company filter if specified
}
```

### Profile Category Structure
```python
{
    "code": str,
    "categories": List[str],  # e.g., ["KÜPEŞTE", "DAİRE", "SEKTÖREL"]
    "customer": str,
    "description": str,
    "mold_status": str
}
```

## Error Handling

### No Categories Found
- **Scenario:** Query doesn't contain any recognizable categories
- **Handling:** Fall back to general search using `catalog_service.search_profiles()`
- **User Message:** "Aramanıza uygun X profil buldum:"

### Single Category Found
- **Scenario:** Query contains only one category
- **Handling:** Use single-category search with optional company filter
- **User Message:** "**{CATEGORY}** kategorisinden **X profil** buldum:"

### Multiple Categories, No Results
- **Scenario:** Combination search returns 0 profiles
- **Handling:** Fall back to general search
- **User Message:** "Üzgünüm, **{CAT1} + {CAT2}** kombinasyonunda profil bulamadım."

### Turkish Character Encoding Issues
- **Scenario:** Different encodings for Turkish characters (ı/i, ş/s, etc.)
- **Handling:** Normalize all text before comparison using `normalize_turkish()` function
- **Implementation:** Apply to both query text and catalog category names

## Testing Strategy

### Unit Tests

**Test 1: Single Shape Category**
- Input: "L şeklinde profil"
- Expected: `["L"]`

**Test 2: Single Product Category**
- Input: "küpeşte profilleri"
- Expected: `["KÜPEŞTE"]`

**Test 3: Shape + Product Combination**
- Input: "daire şeklinde küpeşte"
- Expected: `["DAİRE", "KÜPEŞTE"]` or `["KÜPEŞTE", "DAİRE"]`

**Test 4: Multiple Shape Patterns**
- Input: "L veya T şeklinde"
- Expected: `["L", "T"]`

**Test 5: Turkish Character Variations**
- Input: "kupeste" (without Turkish chars)
- Expected: `["KÜPEŞTE"]`

**Test 6: Noise Word Filtering**
- Input: "daire şeklinde küpeşte varmı sanırım"
- Expected: `["DAİRE", "KÜPEŞTE"]` (noise words removed)

**Test 7: No Categories**
- Input: "30x30 lama"
- Expected: `[]`

### Integration Tests

**Test 1: Combination Search Returns Results**
- Query: "daire şeklinde küpeşte"
- Expected: Profiles belonging to both DAİRE and KÜPEŞTE categories
- Verify: Result count > 0

**Test 2: Combination Search Filters Correctly**
- Query: "L şeklinde kapak"
- Expected: Only profiles with BOTH "L" and "KAPAK" in categories
- Verify: All results have both categories

**Test 3: Fallback to General Search**
- Query: "XYZ şeklinde ABC" (non-existent combination)
- Expected: Falls back to general search
- Verify: Returns some results or appropriate message

**Test 4: Single Category Search**
- Query: "küpeşte profilleri"
- Expected: All profiles in KÜPEŞTE category
- Verify: All results have KÜPEŞTE in categories

### Manual Testing Scenarios

1. "daire şeklinde küpeşte varmı" → Should return ~76 profiles
2. "L şeklinde cam tutucu" → Should return profiles with both L and CAM TUTUCU
3. "T şeklinde kapak profili" → Should return profiles with both T and KAPAK
4. "dairesel küpeşte" → Should work same as "daire şeklinde küpeşte"
5. "kupeste daire" → Should handle Turkish character variations

## Implementation Notes

### Order of Category Detection
1. Clean query first (remove noise)
2. Detect shape letters (L, T, U, etc.) with strict patterns
3. Detect special shapes (DAİRE) with flexible patterns
4. Detect product categories by catalog matching
5. Return all found categories in order of detection

### Logging Strategy
- Log cleaned query for debugging
- Log each category as it's found with its type
- Log final category list before search
- Log search method chosen (combination vs single vs general)
- Log result count

### Performance Considerations
- Category extraction is O(n) where n = number of catalog categories
- Combination search is O(m) where m = number of profiles
- Both are acceptable for current dataset size (<10,000 profiles)
- No caching needed at this stage

### Backward Compatibility
- Existing single-category searches continue to work
- Existing dimension searches (30x30, 20 ye 20) unaffected
- No changes to API contracts or response formats
