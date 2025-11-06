# Requirements Document

## Introduction

This feature addresses a critical bug in the multi-category search functionality where queries combining shape categories (like "daire") with product categories (like "küpeşte") fail to return results. The system currently identifies both categories but only searches by one, resulting in zero results when it should find profiles matching both categories.

## Glossary

- **RAG Service**: Retrieval-Augmented Generation service that processes user queries and retrieves relevant profiles
- **Category Combination Search**: Search functionality that finds profiles belonging to multiple categories simultaneously
- **Shape Category**: Categories describing geometric shapes (e.g., DAİRE, L, T, U)
- **Product Category**: Categories describing product types (e.g., KÜPEŞTE, KAPAK, CAM TUTUCU)
- **Category Extraction**: Process of identifying category names from user queries

## Requirements

### Requirement 1

**User Story:** As a user, I want to search for profiles using combined shape and product categories (e.g., "daire şeklinde küpeşte"), so that I can find profiles that match both criteria.

#### Acceptance Criteria

1. WHEN a user submits a query containing both a shape category and a product category, THE RAG Service SHALL extract both categories from the query
2. WHEN both categories are extracted, THE RAG Service SHALL perform a combination search that returns only profiles belonging to both categories
3. WHEN the combination search completes, THE RAG Service SHALL return profiles that exist in both the shape category AND the product category
4. WHEN no profiles match both categories, THE RAG Service SHALL return an appropriate message indicating no matches were found for the combination

### Requirement 2

**User Story:** As a user, I want the system to correctly identify Turkish shape descriptors (like "daire şeklinde", "dairesel"), so that my searches work with natural Turkish language patterns.

#### Acceptance Criteria

1. WHEN a query contains "daire şeklinde", "dairesel", or "daire" followed by shape keywords, THE RAG Service SHALL identify the DAİRE category
2. WHEN a query contains "küpeşte", "kupeşte", "küpeste", or "kupeste", THE RAG Service SHALL identify the KÜPEŞTE category
3. WHEN multiple shape patterns exist in a query, THE RAG Service SHALL identify all matching shape categories
4. THE RAG Service SHALL normalize Turkish characters to handle encoding variations (ı/i, ş/s, ğ/g, ü/u, ö/o, ç/c)

### Requirement 3

**User Story:** As a developer, I want the category extraction logic to be consolidated and consistent, so that all category types are detected using the same method.

#### Acceptance Criteria

1. THE RAG Service SHALL use a single method to extract all categories from a query regardless of category type
2. WHEN the extraction method identifies at least two categories, THE RAG Service SHALL trigger combination search logic
3. WHEN the extraction method identifies exactly one category, THE RAG Service SHALL trigger single-category search logic
4. THE RAG Service SHALL log all extracted categories for debugging purposes

### Requirement 4

**User Story:** As a user, I want accurate search results when combining categories, so that I don't receive irrelevant profiles or miss relevant ones.

#### Acceptance Criteria

1. WHEN performing a combination search, THE RAG Service SHALL only return profiles that belong to ALL specified categories
2. THE RAG Service SHALL perform case-insensitive category matching to handle variations in category naming
3. WHEN a profile belongs to multiple categories, THE RAG Service SHALL check if all search categories are present in the profile's category list
4. THE RAG Service SHALL return results sorted by relevance with the most specific matches first
