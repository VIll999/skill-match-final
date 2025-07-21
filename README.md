# Skill Match - Intelligent Job-Skill Alignment Platform

> A comprehensive web application that helps users evaluate how well their skills align with current job market demands through automated job data aggregation, intelligent skill mapping, and personalized recommendations.

## 🎯 Programming Assessment Response

This project fully addresses the **Skill-Matching Web Application** requirements:

### ✅ Requirements Implementation

**1. Job Data Aggregation**
- ✅ **Automated web scraper** with Adzuna API integration
- ✅ **Daily automated runs** via Docker cron scheduling
- ✅ **Structured database storage** with PostgreSQL
- ✅ **Comprehensive parsing** of job titles, descriptions, skills, and locations
- ✅ **Multi-source support** (Adzuna, with extensible architecture for LinkedIn, Indeed)

**2. Skill Mapping Engine**
- ✅ **Advanced skill categorization** using EMSI Skills Database (26,000+ skills)
- ✅ **SkillNER integration** for intelligent skill extraction and mapping
- ✅ **Technical and soft skill classification** with confidence scoring
- ✅ **Real-time demand distribution** analysis across roles and industries

**3. User Resume Analysis**
- ✅ **Multi-format document support** (PDF, DOCX, TXT)
- ✅ **Intelligent text extraction** with PyMuPDF and python-docx
- ✅ **Structured data parsing** for experience, education, and skills
- ✅ **EMSI-powered skill matching** with proficiency level detection
- ✅ **Dynamic alignment scoring** based on skill overlap and confidence

**4. Recommendation Engine**
- ✅ **Multi-algorithm matching** (TF-IDF, cosine similarity, Jaccard index)
- ✅ **Ranked job recommendations** with comprehensive scoring
- ✅ **Visual skill gap analysis** with actionable improvement suggestions
- ✅ **Personalized learning resource recommendations**

### 🎁 Bonus Features Implemented

**Dashboard & Visualizations**
- ✅ **Real-time skill demand trends** across industries with interactive charts
- ✅ **User skill alignment timeline** showing progression over time
- ✅ **Industry alignment tracking** with historical data
- ✅ **Market insights dashboard** with comprehensive analytics

**Advanced NLP & Embeddings**
- ✅ **SkillNER integration** for semantic skill extraction
- ✅ **SBERT embeddings** for improved skill matching
- ✅ **Multi-pass extraction pipeline** with confidence scoring
- ✅ **Context-aware skill detection** with type classification

## 🚀 Quick Start

### One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd skill-match

# Start all services (backend + frontend)
./start-all.sh
```

**That's it!** The application will be available at `http://localhost:5173`

### Alternative: Step-by-Step Setup

```bash
# 1. Start backend services only
./start.sh

# 2. In a new terminal, start frontend
./start-frontend.sh
```

## 📋 Prerequisites

- **Docker & Docker Compose** (for backend services)
- **Node.js 18+** (for frontend development)
- **Git** (for cloning the repository)

## 🏗️ Architecture Overview

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

## 🚨 Troubleshooting

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
```bash
# Check Node.js version
node --version  # Should be 18+

# Reinstall dependencies
cd apps/web-ui
rm -rf node_modules
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
3. **Real-time Updates:** WebSocket-based live updates
4. **Mobile Application:** React Native companion app
5. **Enterprise Features:** Team analytics, bulk processing

## 📄 License

This project is created for programming assessment purposes.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs -f`
3. Verify configuration in environment files
4. Ensure all prerequisites are installed

---

**🎉 Ready to explore intelligent skill matching? Start with `./start-all.sh` and visit `http://localhost:5173`!**