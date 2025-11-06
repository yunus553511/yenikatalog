# Requirements Document

## Introduction

This document outlines the requirements for an Aluminum Profile Similarity Search System. The system enables users to find visually similar aluminum profile cross-sections from a database of 3,610 textured 2D profile images. The system will be deployed as a web-based API that integrates with an existing chatbot, allowing users to query similar profiles by profile code and receive ranked results with similarity scores.

## Glossary

- **Similarity_System**: The aluminum profile similarity search application
- **Profile_Image**: A 2D cross-section rendering of an aluminum profile with texture applied (PNG format, 700 DPI)
- **Profile_Code**: A unique identifier for each aluminum profile (e.g., "AP0001", "A 3703")
- **Embedding_Vector**: A numerical representation of a profile image's visual features (2048-dimensional vector)
- **Similarity_Score**: A numerical value (0-100%) indicating how similar two profiles are
- **FAISS_Index**: Facebook AI Similarity Search index for fast vector similarity search
- **Chatbot_API**: The external chatbot system that will consume the similarity search API
- **Hybrid_Model**: A combination of AI-based deep learning embeddings and geometric shape descriptors
- **Geometric_Features**: Mathematical shape descriptors including contours, Hu moments, area, perimeter, and symmetry

## Requirements

### Requirement 1

**User Story:** As a chatbot user, I want to query similar aluminum profiles by profile code, so that I can discover profiles with similar cross-sectional shapes.

#### Acceptance Criteria

1. WHEN the Chatbot_API sends a profile code to the Similarity_System, THE Similarity_System SHALL retrieve the corresponding Profile_Image from storage
2. IF the requested Profile_Code does not exist in the database, THEN THE Similarity_System SHALL return an error response with HTTP status 404 and a descriptive error message
3. THE Similarity_System SHALL accept profile codes in various formats including alphanumeric codes with spaces and hyphens
4. THE Similarity_System SHALL respond to valid similarity queries within 500 milliseconds
5. THE Similarity_System SHALL provide a RESTful API endpoint that accepts profile code as a path parameter

### Requirement 2

**User Story:** As a chatbot user, I want to receive the top 30 most similar profiles with similarity scores, so that I can evaluate multiple similar options.

#### Acceptance Criteria

1. WHEN a valid similarity query is processed, THE Similarity_System SHALL return exactly 30 similar profiles ranked by Similarity_Score in descending order
2. THE Similarity_System SHALL include the Profile_Code and Similarity_Score for each result in the response
3. THE Similarity_System SHALL calculate Similarity_Score as a percentage value between 0 and 100
4. THE Similarity_System SHALL exclude the queried profile itself from the results
5. IF fewer than 30 profiles exist in the database, THEN THE Similarity_System SHALL return all available profiles except the queried one

### Requirement 3

**User Story:** As a system administrator, I want the system to use a hybrid AI and geometric approach, so that similarity detection is accurate for aluminum profile cross-sections.

#### Acceptance Criteria

1. THE Similarity_System SHALL use ResNet50 pre-trained model to extract Embedding_Vector from each Profile_Image
2. THE Similarity_System SHALL extract Geometric_Features including contour analysis, Hu moments, cross-sectional area, perimeter, and symmetry metrics from each Profile_Image
3. THE Similarity_System SHALL detect and analyze inner contours using hierarchical contour detection with RETR_TREE mode to accurately capture internal profile cavities
4. THE Similarity_System SHALL combine AI embeddings with a weight of 70% and Geometric_Features with a weight of 30% to calculate final Similarity_Score
5. THE Similarity_System SHALL normalize all Geometric_Features to a 0-1 scale before combining with AI embeddings
6. THE Similarity_System SHALL use FAISS_Index for efficient similarity search across all 3,610 Profile_Images

### Requirement 4

**User Story:** As a system administrator, I want all profile images to be pre-processed and indexed during system initialization, so that real-time queries are fast.

#### Acceptance Criteria

1. WHEN the Similarity_System initializes, THE Similarity_System SHALL load all Profile_Images from the specified directory
2. THE Similarity_System SHALL extract Embedding_Vector and Geometric_Features for each Profile_Image during initialization
3. THE Similarity_System SHALL build and persist the FAISS_Index to disk for reuse across system restarts
4. THE Similarity_System SHALL create a mapping between Profile_Code and vector indices
5. THE Similarity_System SHALL log the initialization progress and completion status

### Requirement 5

**User Story:** As a developer, I want the system to be deployable as a web service with clear API documentation, so that integration with the chatbot is straightforward.

#### Acceptance Criteria

1. THE Similarity_System SHALL expose a RESTful API using FastAPI framework
2. THE Similarity_System SHALL provide an API endpoint at `/api/similar/{profile_code}` that accepts GET requests
3. THE Similarity_System SHALL return JSON responses with profile codes and similarity scores
4. THE Similarity_System SHALL include OpenAPI/Swagger documentation accessible at `/docs`
5. THE Similarity_System SHALL implement proper error handling with appropriate HTTP status codes

### Requirement 6

**User Story:** As a system administrator, I want the system to handle errors gracefully and provide meaningful error messages, so that issues can be diagnosed quickly.

#### Acceptance Criteria

1. IF an error occurs during image processing, THEN THE Similarity_System SHALL log the error with the Profile_Code and continue processing remaining images
2. IF the FAISS_Index fails to load, THEN THE Similarity_System SHALL attempt to rebuild the index from Profile_Images
3. THE Similarity_System SHALL validate that Profile_Images are readable PNG files before processing
4. THE Similarity_System SHALL return structured error responses with error codes and descriptive messages
5. THE Similarity_System SHALL log all errors with timestamps and context information

### Requirement 7

**User Story:** As a system administrator, I want the system to be configurable through environment variables or configuration files, so that deployment settings can be adjusted without code changes.

#### Acceptance Criteria

1. THE Similarity_System SHALL read the Profile_Images directory path from configuration
2. THE Similarity_System SHALL read the FAISS_Index storage path from configuration
3. THE Similarity_System SHALL read the API server port and host from configuration
4. THE Similarity_System SHALL read the hybrid model weights (AI vs geometric) from configuration
5. THE Similarity_System SHALL read the number of similar results to return from configuration with a default value of 30


### Requirement 8

**User Story:** As a system administrator, I want the similarity scoring to be calibrated and realistic, so that only truly similar profiles receive high scores.

#### Acceptance Criteria

1. THE Similarity_System SHALL apply aggressive distance-based score calibration to prevent inflated similarity scores
2. THE Similarity_System SHALL ensure that visually distinct profiles receive Similarity_Score below 60%
3. THE Similarity_System SHALL ensure that moderately similar profiles receive Similarity_Score between 60% and 80%
4. THE Similarity_System SHALL ensure that highly similar profiles receive Similarity_Score above 80%
5. THE Similarity_System SHALL use non-linear score transformation with calibration parameters k >= 20.0 and threshold >= 0.90 to aggressively spread out the similarity distribution
6. THE Similarity_System SHALL ensure that the average similarity score across all queries is below 65%

### Requirement 9

**User Story:** As a system administrator, I want inner contours to be accurately detected and weighted in similarity calculations, so that profiles with different internal structures are properly distinguished.

#### Acceptance Criteria

1. THE Similarity_System SHALL use hierarchical contour detection to identify parent and child contours
2. THE Similarity_System SHALL extract inner contour features including count, total area, largest inner contour area, and inner contour complexity
3. THE Similarity_System SHALL weight inner contour features at minimum 40% of total geometric feature importance to ensure strong differentiation
4. THE Similarity_System SHALL normalize inner contour features relative to the outer contour dimensions
5. THE Similarity_System SHALL handle profiles with no inner contours without causing processing errors
6. THE Similarity_System SHALL apply amplification factor of at least 3.0 to inner contour feature differences to increase their impact on similarity scores
