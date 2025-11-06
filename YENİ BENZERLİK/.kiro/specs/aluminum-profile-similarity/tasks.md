# Implementation Plan

- [x] 1. Set up project structure and dependencies


  - Create project directory structure (src, tests, data, config)
  - Create requirements.txt with all dependencies (FastAPI, PyTorch, OpenCV, FAISS, watchdog)
  - Create configuration file structure (config.yaml, .env.example)
  - Set up logging configuration
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_



- [ ] 2. Implement configuration management
  - Create Config dataclass with all configuration parameters
  - Implement environment variable loading with fallback to defaults
  - Implement YAML config file loading




  - Add configuration validation logic
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 3. Implement AI embedder component
  - [x] 3.1 Create AIEmbedder class with ResNet50 initialization

    - Load pre-trained ResNet50 model
    - Remove final FC layer to get 2048-dim embeddings
    - Set model to evaluation mode
    - Implement image preprocessing transforms (resize, normalize)
    - _Requirements: 3.1_

  - [x] 3.2 Implement embedding extraction method


    - Write extract_embedding() method that accepts numpy array
    - Handle image format conversion (BGR to RGB)
    - Apply preprocessing transforms




    - Run inference and extract features
    - Return 2048-dimensional numpy array
    - _Requirements: 3.1_

  - [ ] 3.3 Add batch processing support
    - Implement batch_extract_embeddings() for multiple images

    - Optimize for GPU if available
    - Add progress logging
    - _Requirements: 3.1_

- [ ] 4. Implement enhanced geometric feature extractor with inner contour detection

  - [ ] 4.1 Create GeometricFeatureExtractor class with hierarchical contour detection
    - Implement adaptive thresholding for better contour detection
    - Implement hierarchical contour detection using RETR_TREE mode
    - Implement contour separation logic to identify outer vs inner contours
    - _Requirements: 3.3, 9.1_

  - [ ] 4.2 Implement outer contour feature extraction
    - Extract 10 outer contour features (area, perimeter, complexity, etc.)
    - Implement convex hull and bounding box calculations
    - Calculate shape metrics (solidity, extent, circularity)
    - _Requirements: 3.2_

  - [ ] 4.3 Implement enhanced inner contour feature extraction
    - Extract 13 inner contour features including count, areas, and spatial distribution
    - Calculate inner contour area ratios and density metrics
    - Compute inner contour complexity and shape characteristics
    - Handle profiles with no inner contours gracefully
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 4.4 Implement additional feature extraction methods
    - Implement Hu moments calculation (7 features)
    - Implement symmetry feature extraction (4 features)
    - Implement spatial feature extraction (6 features)
    - Implement legacy hole features for backward compatibility (5 features)
    - _Requirements: 3.2_

  - [ ] 4.5 Implement feature normalization
    - Write normalization logic to scale all 45 features to [0, 1]
    - Handle edge cases (division by zero, empty contours)
    - Return 45-dimensional numpy array
    - _Requirements: 3.5_

  - [ ] 4.6 Add error handling for image processing
    - Handle grayscale conversion errors
    - Handle threshold failures
    - Handle contour detection failures
    - Log warnings for problematic images
    - _Requirements: 6.1, 6.3_

- [ ] 5. Implement FAISS index manager with score calibration

  - [x] 5.1 Create FAISSIndexManager class


    - Initialize IndexFlatIP with dimension 2093 (updated for 45 geometric features)
    - Implement vector normalization for cosine similarity
    - Create profile_codes list for mapping
    - Add score calibration parameters (k=10.0, threshold=0.5)
    - _Requirements: 3.6_

  - [x] 5.2 Implement aggressive score calibration logic


    - Write _calibrate_scores() method using sigmoid transformation
    - Apply aggressive non-linear transformation with k >= 20.0 and threshold >= 0.90
    - Ensure distinct profiles score below 60%
    - Ensure moderately similar profiles score 60-80%
    - Ensure highly similar profiles score above 80%
    - Ensure average similarity score is below 65%
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 5.3 Implement index building and search with calibration
    - Write build_index() method for batch vector addition
    - Write search() method for k-nearest neighbor search with calibrated scores
    - Exclude query profile from results
    - _Requirements: 3.6, 2.4, 8.1_

  - [ ] 5.4 Implement index persistence
    - Write save() method to persist index to disk
    - Write load() method to load index from disk
    - Handle file I/O errors gracefully
    - _Requirements: 4.3, 6.2_

  - [ ] 5.5 Implement incremental index updates
    - Write add_vector() method for single vector addition
    - Ensure thread-safe operations
    - Update profile_codes mapping
    - _Requirements: 3.6_





- [ ] 6. Implement hybrid similarity engine with inner contour amplification
  - [ ] 6.1 Create HybridSimilarityEngine class
    - Initialize AIEmbedder and GeometricFeatureExtractor
    - Initialize FAISSIndexManager with aggressive calibration parameters (k=20.0, threshold=0.90)
    - Load configuration for weights (70% AI, 30% geometric)
    - Set inner contour amplification factor to 3.0
    - Create profile_metadata dictionary
    - _Requirements: 3.1, 3.2, 3.3, 9.6_



  - [ ] 6.2 Implement hybrid vector computation with inner contour amplification
    - Write _compute_hybrid_vector() method
    - Extract AI embedding (2048 dims)
    - Extract enhanced geometric features (45 dims including inner contours)
    - Apply 3.0x amplification factor to inner contour features (indices 10-22)
    - Concatenate into 2093-dim vector
    - Apply weighted combination based on config (70% AI, 30% geometric with amplification)
    - _Requirements: 3.3, 3.4, 9.3, 9.6_

  - [x] 6.3 Implement initialization and indexing




    - Write initialize() method to process all images
    - Scan image directory for PNG files
    - Process images in batches with progress logging
    - Build FAISS index from all vectors

    - Save index and metadata to disk
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 6.4 Implement similarity search with aggressive calibrated scoring
    - Write find_similar() method accepting profile_code and top_k
    - Retrieve profile metadata by code
    - Search FAISS index for nearest neighbors with aggressively calibrated scores
    - Verify calibrated scores follow distribution (distinct < 60%, moderate 60-80%, high > 80%)
    - Verify average similarity score is below 65%
    - Return ranked list of SimilarityResult objects
    - _Requirements: 1.1, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 8.2, 8.3, 8.4, 8.6_

  - [x] 6.5 Add profile addition method

    - Write add_profile() method for single profile
    - Compute hybrid vector
    - Add to FAISS index incrementally
    - Update metadata


    - Persist changes to disk
    - _Requirements: 3.5, 4.3_

- [x] 7. Implement file watcher service

  - [ ] 7.1 Create FileWatcherService class
    - Initialize watchdog Observer
    - Set up event handler for file system events
    - Maintain processed_files set to avoid duplicates
    - _Requirements: 4.1_



  - [ ] 7.2 Implement file event handling
    - Write on_new_file() method triggered by file creation
    - Filter for PNG files only
    - Extract profile code from filename
    - Call similarity engine to process and add profile
    - Log success or errors


    - _Requirements: 4.1, 6.1_

  - [ ] 7.3 Implement watcher lifecycle
    - Write start() method to begin monitoring
    - Write stop() method for graceful shutdown
    - Handle watcher errors and restart if needed
    - _Requirements: 4.1_




- [ ] 8. Implement FastAPI web service
  - [ ] 8.1 Create FastAPI application and data models
    - Initialize FastAPI app with metadata
    - Create Pydantic models (SimilarityResponse, ErrorResponse)
    - Set up CORS middleware if needed
    - _Requirements: 5.1, 5.3_

  - [ ] 8.2 Implement similarity search endpoint
    - Create GET /api/similar/{profile_code} endpoint
    - Add optional top_k query parameter (default 30)
    - Call HybridSimilarityEngine.find_similar()
    - Format response with profile codes and scores
    - Add processing time measurement
    - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 5.2_

  - [ ] 8.3 Implement error handling
    - Handle ProfileNotFoundError with 404 response
    - Handle processing errors with 500 response
    - Return structured error responses
    - _Requirements: 1.2, 6.4_

  - [ ] 8.4 Implement health check endpoint
    - Create GET /health endpoint
    - Return system status and indexed profile count
    - _Requirements: 5.1_

  - [ ] 8.5 Add startup and shutdown events
    - Implement startup event to initialize similarity engine
    - Load or build FAISS index on startup
    - Start file watcher service
    - Implement shutdown event to stop file watcher
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 9. Implement logging and error handling
  - Create custom exception classes (ProfileNotFoundError, ImageProcessingError)
  - Set up structured logging with timestamps and levels
  - Add logging to all major operations (initialization, queries, errors)
  - Implement error recovery strategies (skip bad images, rebuild index)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 10. Create main application entry point
  - Create main.py with application initialization
  - Load configuration from environment/file
  - Initialize all components in correct order
  - Start uvicorn server with configured host/port
  - Add graceful shutdown handling
  - _Requirements: 5.1, 7.1, 7.2, 7.3_

- [ ] 11. Create Docker deployment configuration
  - Create Dockerfile with Python 3.9 base image
  - Install system dependencies (libgl1-mesa-glx for OpenCV)
  - Copy application code and install Python dependencies
  - Set up volume mounts for images and index data
  - Configure environment variables
  - Set CMD to run uvicorn server
  - _Requirements: 5.1, 7.1, 7.2, 7.3_

- [ ] 12. Create documentation and examples
  - Write README.md with setup instructions
  - Document API endpoints with request/response examples
  - Create example configuration files (config.yaml, .env)
  - Document deployment steps (local, Docker, cloud)
  - Add troubleshooting guide
  - _Requirements: 5.4_

- [ ]* 13. Write unit tests
  - [ ]* 13.1 Write tests for AIEmbedder
    - Test embedding extraction with sample images
    - Test output dimensions and data types
    - Test batch processing
    - _Requirements: 3.1_

  - [ ]* 13.2 Write tests for GeometricFeatureExtractor
    - Test feature extraction with synthetic shapes
    - Test normalization logic
    - Test error handling for edge cases
    - _Requirements: 3.2_

  - [ ]* 13.3 Write tests for FAISSIndexManager
    - Test index building and search
    - Test save/load persistence
    - Test incremental additions
    - _Requirements: 3.5_

  - [ ]* 13.4 Write tests for HybridSimilarityEngine
    - Test hybrid vector computation
    - Test similarity score calculation
    - Test find_similar() with mock data
    - _Requirements: 3.3_

- [ ]* 14. Write integration tests
  - [ ]* 14.1 Write end-to-end API tests
    - Test successful similarity query
    - Test 404 error for non-existent profile
    - Test response format validation
    - Test query latency (< 500ms)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3_

  - [ ]* 14.2 Write initialization tests
    - Test full system initialization with sample images
    - Test index persistence and reload
    - Test file watcher integration
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 15. Perform manual validation and optimization
  - [ ]* 15.1 Manual accuracy validation
    - Select 20 random profiles
    - Verify top 5 results are visually similar
    - Document accuracy metrics
    - _Requirements: 3.3_

  - [ ]* 15.2 Performance optimization
    - Measure query latency and optimize if needed
    - Measure initialization time for 3,610 images
    - Optimize batch processing if needed
    - Profile memory usage
    - _Requirements: 1.4_
