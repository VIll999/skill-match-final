# Skill Match - Intelligent Job-Skill Alignment Platform


## Quick Start

### Prerequisites

**Required Software:**
- **Docker & Docker Compose** (for backend services)
  - *Windows:* [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - *macOS:* [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - *Linux:* [Docker Engine](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/)
- **Node.js 18+** (for frontend development)
  - Download from: [nodejs.org](https://nodejs.org/)
- **Git** (for cloning the repository)
  - *Windows:* [Git for Windows](https://gitforwindows.org/)
  - *macOS/Linux:* Usually pre-installed

**⚠️ Important for Windows Users:**
- Make sure Docker Desktop is running before starting the application
- Use PowerShell or Command Prompt as Administrator for best results
- If using WSL2, ensure it's properly configured with Docker Desktop

### One-Command Setup

**Linux/macOS:**
```bash
# Make sure Docker is running
docker --version

# Clone the repository
git clone https://github.com/VIll999/skill-match-final.git
cd skill-match-final

# Start all services (backend + frontend)
./start-all.sh
```

**Windows (Easy Way - Double-click):**
```cmd
# Make sure Docker Desktop is running
# Clone the repository
git clone https://github.com/VIll999/skill-match-final.git
cd skill-match-final

# Double-click start-all.bat to start everything!
# OR run in Command Prompt:
start-all.bat

# Note: You'll be prompted to restore sample database (16MB of job data)
# Choose 'y' to populate with real job postings and skills for testing
```

**Windows (PowerShell):**
```powershell
# Make sure Docker is running
docker --version

# Clone the repository
git clone https://github.com/VIll999/skill-match-final.git
cd skill-match-final

# Start backend services
docker-compose down --remove-orphans
docker-compose up -d db
Start-Sleep 15
docker-compose up -d api
Start-Sleep 10
docker-compose up -d scraper

# Start frontend (in new PowerShell window)
cd apps/web-ui
npm install
npm run dev
```

**Windows (Command Prompt):**
```cmd
REM Make sure Docker is running
docker --version

REM Clone the repository
git clone https://github.com/VIll999/skill-match-final.git
cd skill-match-final

REM Start backend services
docker-compose down --remove-orphans
docker-compose up -d db
timeout /t 15
docker-compose up -d api
timeout /t 10
docker-compose up -d scraper

REM Start frontend (in new Command Prompt window)
cd apps\web-ui
npm install
npm run dev
```

**That's it!** The application will be available at `http://localhost:5173`

### 📊 Database Setup

The repository includes a **16MB database backup** with real job postings and skills for testing:

**Automatic Restoration (Recommended):**
- When you first run the startup scripts, you'll be prompted to restore sample data
- Choose 'y' to populate the database with job postings and skills

**Manual Restoration:**
```bash
# Linux/macOS
./restore-data.sh

# Windows
restore-data.bat
```

### Alternative: Step-by-Step Setup

**Linux/macOS:**
```bash
# 1. Start backend services only
./start.sh

# 2. In a new terminal, start frontend
./start-frontend.sh
```

**Windows:**
```cmd
REM Option 1: Use batch files (Easy)
start.bat              REM Start backend services (includes database prompt)
start-frontend.bat     REM Start frontend (in new window)

REM Option 2: Manual commands
docker-compose up -d   REM Start backend services
restore-data.bat       REM Restore sample database (optional)

REM In a new Command Prompt window:
cd apps\web-ui
npm install
npm run dev
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI       │    │   PostgreSQL    │
│   (Vite + TS)   │◄──►│   Backend       │◄──►│   Database      │
│   Port: 5173    │    │   Port: 8000    │    │   Port: 5442    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Job Scraper   │
                       │   (Daily Cron)  │
                       │   Adzuna API    │
                       └─────────────────┘
```


### Requirements Implementation

**1. Job Data Aggregation**
- **Automated web scraper** with Adzuna API integration
- **Daily automated runs** via Docker cron scheduling
- **Structured database storage** with PostgreSQL
-  **Comprehensive parsing** of job titles, descriptions, skills, and locations
-  **Multi-source support** (Adzuna, with extensible architecture for LinkedIn, Indeed)

**2. Skill Mapping Engine**
-  **Advanced skill categorization** using EMSI Skills Database (26,000+ skills)
-  **SkillNER integration** for intelligent skill extraction and mapping
-  **Technical and soft skill classification** with confidence scoring
-  **Real-time demand distribution** analysis across roles and industries

**3. User Resume Analysis**
-  **Multi-format document support** (PDF, DOCX, TXT)
-  **Intelligent text extraction** with PyMuPDF and python-docx
-  **Structured data parsing** for experience, education, and skills
-  **EMSI-powered skill matching** with proficiency level detection
-  **Dynamic alignment scoring** based on skill overlap and confidence

**4. Recommendation Engine**
-  **Multi-algorithm matching** (TF-IDF, cosine similarity, Jaccard index)
-  **Ranked job recommendations** with comprehensive scoring
-  **Visual skill gap analysis** with actionable improvement suggestions
-  **Personalized learning resource recommendations**

###  Bonus Features Implemented

**Dashboard & Visualizations**
-  **Real-time skill demand trends** across industries with interactive charts
-  **User skill alignment timeline** showing progression over time
-  **Industry alignment tracking** with historical data
-  **Market insights dashboard** with comprehensive analytics

**Advanced NLP & Embeddings**
-  **SkillNER integration** for semantic skill extraction
-  **SBERT embeddings** for improved skill matching
-  **Multi-pass extraction pipeline** with confidence scoring
-  **Context-aware skill detection** with type classification
### Technology Stack

**Frontend:**
- React 19 + TypeScript + Vite
- Tailwind CSS for styling
- Framer Motion for animations
- Recharts for data visualization
- React Router for navigation

**Backend:**
- FastAPI (Python) for REST API
- SQLAlchemy ORM with PostgreSQL
- SkillNER for intelligent skill extraction
- EMSI Skills Database (26,000+ skills)
- PyMuPDF + python-docx for document processing

**Infrastructure:**
- Docker & Docker Compose for containerization
- PostgreSQL for data persistence
- Automated cron jobs for daily scraping
- RESTful API architecture

## 🔧 Configuration

### Environment Variables

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:8000
VITE_USER_ID=1
VITE_ENV=development
```

**API Credentials (secrets/.env.adzuna):**
```bash
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

### Adzuna API Setup

1. Register at [Adzuna API](https://developer.adzuna.com/)
2. Get your App ID and Key
3. Update `secrets/.env.adzuna` with your credentials
4. Restart the scraper: `docker-compose restart scraper`

## 📊 Features & Usage

### 1. Resume Analysis
- Upload PDF/DOCX resumes
- Automatic skill extraction using SkillNER
- Experience and education parsing
- Skill proficiency assessment

### 2. Job Matching
- AI-powered job recommendations
- Multiple similarity algorithms
- Skill coverage analysis
- Gap identification and suggestions

### 3. Market Intelligence
- Real-time skill demand trends
- Industry-specific insights
- Historical progression tracking
- Competitive skill analysis

### 4. Personalized Dashboard
- Skill alignment timeline
- Industry compatibility scores
- Learning resource recommendations
- Progress tracking over time

## 🧪 Testing the Application

### 1. Upload a Resume
1. Navigate to `http://localhost:5173`
2. Click "Upload Resume"
3. Select a PDF or DOCX file
4. View extracted skills and experience

### 2. Explore Job Matches
1. Go to "Job Matches" section
2. View ranked job recommendations
3. Analyze skill coverage and gaps
4. Review improvement suggestions

### 3. Market Analysis
1. Visit "Skill Demand" dashboard
2. Explore trending skills by industry
3. View historical demand patterns
4. Identify growth opportunities

## 📈 API Endpoints

### Core Endpoints
- `GET /api/health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /api/v1/resumes/upload` - Resume upload and processing
- `GET /api/v1/match/jobs/{user_id}` - Get job matches
- `GET /api/v1/skills/demand/top` - Top demanded skills
- `GET /api/v1/jobs/stats` - Job statistics

### Skill Analysis
- `GET /api/v1/profile/skills/emsi/{user_id}` - User skill profile
- `GET /api/v1/skill-demand/trending` - Trending skills
- `GET /api/v1/skill-demand/alignment-timeline/{user_id}` - Skill alignment over time

## 🐳 Docker Services

### Database (PostgreSQL)
- **Port:** 5442
- **Credentials:** dev/dev
- **Database:** skillmatch

### API (FastAPI)
- **Port:** 8000
- **Health:** http://localhost:8000/api/health
- **Docs:** http://localhost:8000/docs

### Scraper (Automated)
- **Schedule:** Daily at 2 AM
- **Source:** Adzuna API
- **Logs:** `docker-compose logs scraper`

## 📊 Database Schema

### Core Tables
- `job_postings` - Scraped job data
- `emsi_skills` - EMSI skills database (26,000+ skills)
- `user_skills_emsi` - User skill profiles
- `job_skills_emsi` - Job-skill relationships
- `job_matches` - Computed job matches
- `resumes` - Uploaded resume metadata

### Analytics Tables
- `user_industry_alignment` - Industry alignment tracking
- `skill_alignment_snapshot` - Historical skill progression
- `user_skill_history` - Skill change events

## 🔍 Key Algorithms

### 1. Skill Extraction Pipeline
1. **Document Processing:** PyMuPDF/python-docx text extraction
2. **SkillNER Analysis:** EMSI-powered skill identification
3. **Confidence Scoring:** Multi-factor confidence assessment
4. **Type Classification:** Technical vs. soft skill categorization

### 2. Job Matching Engine
1. **TF-IDF Vectorization:** Skill importance weighting
2. **Cosine Similarity:** Semantic skill alignment
3. **Jaccard Index:** Binary skill overlap
4. **Weighted Scoring:** Experience and proficiency factors

### 3. Market Analysis
1. **Demand Aggregation:** Cross-industry skill frequency
2. **Trend Detection:** Time-series demand analysis
3. **Growth Prediction:** Historical pattern extrapolation
4. **Alignment Tracking:** User skill progression monitoring

## Troubleshooting

### Common Issues

**1. API Not Starting**
```bash
# Check logs
docker-compose logs api

# Restart services
docker-compose restart api
```

**2. Database Connection Issues**
```bash
# Check database status
docker-compose logs db

# Reset database
docker-compose down -v
./start.sh
```

**3. Frontend Not Loading**

*Linux/macOS:*
```bash
# Check Node.js version
node --version  # Should be 18+

# Reinstall dependencies
cd apps/web-ui
rm -rf node_modules
npm install
```

*Windows:*
```powershell
# Check Node.js version
node --version  # Should be 18+

# Reinstall dependencies
cd apps/web-ui
Remove-Item -Recurse -Force node_modules
npm install
```

**4. Scraper Not Working**
- Check Adzuna credentials in `secrets/.env.adzuna`
- Verify API quota limits
- Check scraper logs: `docker-compose logs scraper`

### Performance Optimization

**For Large Resume Files:**
- Ensure sufficient Docker memory allocation
- Monitor processing times in logs
- Consider file size limits for production

**For High Job Volume:**
- Implement database indexing
- Configure connection pooling
- Monitor scraper performance

## 📝 Architecture Decisions & Assumptions

### Key Design Decisions

**1. EMSI Skills Database Integration**
- **Rationale:** Industry-standard skill taxonomy with 26,000+ skills
- **Benefit:** Consistent, comprehensive skill classification
- **Trade-off:** Dependency on external skill definitions

**2. Multi-Algorithm Matching**
- **Rationale:** Different algorithms capture different aspects of skill alignment
- **Benefit:** Robust, comprehensive matching scores
- **Trade-off:** Increased computational complexity

**3. Docker-First Architecture**
- **Rationale:** Simplified deployment and environment consistency
- **Benefit:** Easy setup, reproducible environments
- **Trade-off:** Docker dependency for development

**4. Microservices Separation**
- **Rationale:** Independent scaling and maintenance
- **Benefit:** Clear separation of concerns
- **Trade-off:** Increased architectural complexity

### Assumptions Made

**Data Quality:**
- Assumes job descriptions contain meaningful skill information
- Assumes resume formats follow standard conventions
- Assumes consistent skill naming across sources

**User Behavior:**
- Users will upload well-formatted resumes
- Users are interested in skill development recommendations
- Users value quantitative skill alignment metrics

**Technical Environment:**
- Docker and Docker Compose availability
- Sufficient system resources for ML processing
- Stable internet connection for API access

### Future Enhancements

**Planned Improvements:**
1. **Multi-source Integration:** LinkedIn, Indeed, Glassdoor APIs
2. **Advanced NLP:** GPT integration for semantic understanding

## License

This project is created for programming assessment purposes.

