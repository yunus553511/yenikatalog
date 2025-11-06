# Aluminum Profile Similarity Search System

AI-powered similarity search for aluminum profile cross-sections using hybrid deep learning and geometric features.

## Features

- 🔍 **Hybrid Similarity Search**: Combines ResNet50 AI embeddings (70%) with geometric shape features (30%)
- ⚡ **Fast Search**: Sub-500ms query response time using FAISS indexing
- 🔄 **Auto-Indexing**: Automatically detects and indexes new profile images
- 🌐 **REST API**: Easy integration with chatbots and other systems
- 📊 **Similarity Scores**: Returns top 30 similar profiles with percentage scores
- 🐳 **Docker Ready**: Easy deployment with Docker and docker-compose

## Architecture

```
┌─────────────┐
│  Chatbot    │
└──────┬──────┘
       │ GET /api/similar/{code}
       ▼
┌─────────────────────────────┐
│   FastAPI Web Service       │
│  ┌──────────────────────┐   │
│  │ Hybrid Engine        │   │
│  │ • ResNet50 (AI)      │   │
│  │ • Geometric Features │   │
│  │ • FAISS Index        │   │
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │ File Watcher         │   │
│  │ (Auto-indexing)      │   │
│  └──────────────────────┘   │
└─────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- 4GB+ RAM
- Windows/Linux/macOS

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd aluminum-profile-similarity
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
```bash
cp .env.example .env
# Edit .env with your image directory path
```

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. Update `docker-compose.yml` with your image directory path

2. Build and run:
```bash
docker-compose up -d
```

3. Check logs:
```bash
docker-compose logs -f
```

## API Usage

### Find Similar Profiles

```bash
GET /api/similar/{profile_code}?top_k=30
```

**Example Request:**
```bash
curl http://localhost:8000/api/similar/AP0001?top_k=30
```

**Example Response:**
```json
{
  "query_profile": "AP0001",
  "results": [
    {
      "profile_code": "AP0002",
      "similarity_score": 94.5
    },
    {
      "profile_code": "AP0015",
      "similarity_score": 92.3
    }
  ],
  "count": 30,
  "processing_time_ms": 145.2
}
```

### Health Check

```bash
GET /health
```

**Example Response:**
```json
{
  "status": "healthy",
  "indexed_profiles": 3610,
  "watcher_active": true
}
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

Configuration can be set via:
1. Environment variables (highest priority)
2. `config/config.yaml` file
3. Default values (lowest priority)

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `IMAGE_DIRECTORY` | Path to PNG images | Required |
| `AI_WEIGHT` | Weight for AI features | 0.7 |
| `GEO_WEIGHT` | Weight for geometric features | 0.3 |
| `TOP_K_RESULTS` | Number of results to return | 30 |
| `API_PORT` | API server port | 8000 |
| `DEVICE` | Computation device (cpu/cuda) | cpu |

See `.env.example` for all options.

## How It Works

### 1. Initialization

On startup, the system:
1. Loads all PNG images from the configured directory
2. Extracts AI embeddings using ResNet50 (2048 dimensions)
3. Extracts geometric features (32 dimensions):
   - Contour analysis (area, perimeter, complexity)
   - Hu moments (rotation-invariant shape descriptors)
   - Symmetry features (horizontal, vertical, diagonal)
   - Spatial features (centroid, orientation, eccentricity)
   - Hole/cavity features
4. Combines features into 2080-dimensional hybrid vectors
5. Builds FAISS index for fast similarity search
6. Starts file watcher for auto-indexing new files

### 2. Similarity Search

When querying for similar profiles:
1. Loads the query profile image
2. Computes its hybrid vector
3. Searches FAISS index for nearest neighbors
4. Converts distances to similarity scores (0-100%)
5. Returns top-k results ranked by score

### 3. Auto-Indexing

The file watcher continuously monitors the image directory:
- Detects new PNG files automatically
- Processes and indexes them in real-time
- No API restart required
- Processing time: ~100-150ms per new profile

## Performance

- **Query Latency**: < 500ms (typically 100-200ms)
- **Initialization**: ~5-10 minutes for 3,610 images
- **Memory Usage**: ~2GB RAM
- **Index Size**: ~25MB for 3,610 profiles

## Troubleshooting

### Issue: "No PNG files found"
- Check `IMAGE_DIRECTORY` path in configuration
- Ensure PNG files exist in the directory

### Issue: "Failed to load FAISS index"
- Delete `data/faiss_index.bin` and restart (will rebuild)
- Check disk space and permissions

### Issue: Slow queries
- Consider using GPU by setting `DEVICE=cuda`
- Reduce `TOP_K_RESULTS` if you don't need 30 results

### Issue: File watcher not working
- Check directory permissions
- Verify `watchdog` package is installed
- Check logs for watcher errors

## Development

### Project Structure

```
aluminum-profile-similarity/
├── src/
│   ├── api/           # FastAPI routes and models
│   ├── core/          # Configuration and logging
│   ├── models/        # Data models
│   └── services/      # Core services (AI, geometric, FAISS, watcher)
├── config/            # Configuration files
├── data/              # FAISS index and metadata (generated)
├── tests/             # Unit and integration tests
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
└── Dockerfile         # Docker configuration
```

### Running Tests

```bash
pytest tests/
```

## Chatbot Integration Example

```python
import requests

def get_similar_profiles(profile_code: str, top_k: int = 30):
    """Get similar profiles from API."""
    url = f"http://localhost:8000/api/similar/{profile_code}"
    params = {"top_k": top_k}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data["results"]
    elif response.status_code == 404:
        return f"Profile {profile_code} not found"
    else:
        return "Error occurred"

# Usage in chatbot
user_query = "AP0001'in benzerlerini göster"
profile_code = "AP0001"  # Extract from query
similar = get_similar_profiles(profile_code)
print(f"Found {len(similar)} similar profiles")
```

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.
