# Interlinked-Focused Interview Preparation

## Core Interlinked Technical Questions

### Q1: Microservices Architecture at Interlinked

**Question:** Walk me through the microservices architecture you built at Interlinked. How do the services communicate and what challenges did you face?

**Answer:**
"At Interlinked, I architected a microservices system with three main services:

**Service Architecture:**
```yaml
# docker-compose.yml structure
services:
  api:          # Main REST API service
  harvester:    # Data collection service  
  analyzer:     # Data processing service
  postgres:     # Shared database
  redis:        # Cache/queue (planned)
```

**Service Responsibilities:**
1. **API Service**: 
   - RESTful endpoints for frontend
   - Authentication/authorization
   - Business logic coordination
   
2. **Harvester Service**:
   - Scheduled data collection
   - External API integration
   - Data validation and storage

3. **Analyzer Service**:
   - Data processing pipelines
   - Alert generation
   - Report compilation

**Communication Patterns:**
- **Synchronous**: REST APIs between services for real-time requests
- **Asynchronous**: Planning to implement message queues for event-driven communication
- **Shared Database**: Currently using shared PostgreSQL with logical separation

**Challenges & Solutions:**
1. **Data Consistency**: Used database transactions and row-level locking
2. **Service Discovery**: Docker Compose DNS for local, environment variables for production
3. **Deployment Complexity**: Multi-stage Docker builds, orchestrated with docker-compose
4. **Monitoring**: Implemented health checks and structured logging"

### Q2: Node.js + Express + PostgreSQL Stack

**Question:** Why did you choose Node.js/Express over other backend frameworks for Interlinked?

**Answer:**
"The technology choice was strategic based on several factors:

**Node.js/Express Benefits:**
1. **JavaScript Everywhere**: Same language for frontend/backend reduced context switching
2. **Non-blocking I/O**: Perfect for our I/O-heavy operations (database queries, API calls)
3. **NPM Ecosystem**: Rich middleware for auth, validation, rate limiting
4. **Real-time Capabilities**: WebSocket support for future live updates

**PostgreSQL Choice:**
1. **Spatial Data**: PostGIS extension for disaster location queries
2. **JSONB Support**: Flexible schema for varying disaster data
3. **ACID Compliance**: Critical for disaster response coordination
4. **Advanced Queries**: Window functions for analytics

**Express Implementation:**
```javascript
// Middleware stack example
app.use(helmet()); // Security headers
app.use(cors(corsOptions)); // CORS configuration
app.use(rateLimiter); // Rate limiting
app.use(authenticate); // JWT validation
app.use(errorHandler); // Centralized error handling
```

**Performance Optimizations:**
- Connection pooling with pg-pool
- Query optimization with EXPLAIN ANALYZE
- Caching strategy for frequently accessed data"

### Q3: Peewee ORM Implementation

**Question:** Tell me about your experience with Peewee ORM. How did you handle complex queries?

**Answer:**
"While Interlinked primarily uses Peewee ORM for our Python services, here's how I implemented it:

**Model Design:**
```python
from peewee import *

class Agency(Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=255)
    type = CharField(choices=['fire', 'police', 'medical'])
    location = PointField()  # PostGIS integration
    
    class Meta:
        database = db
        indexes = (
            (('type', 'location'), False),  # Composite index
        )

class Disaster(Model):
    id = UUIDField(primary_key=True)
    severity = IntegerField(constraints=[Check('severity BETWEEN 1 AND 5')])
    affected_area = PolygonField()
    
    @property
    def nearby_agencies(self):
        return Agency.select().where(
            ST_DWithin(Agency.location, self.location, 10000)  # 10km radius
        )
```

**Complex Query Examples:**
```python
# Finding available resources near active disasters
available_resources = (
    Resource
    .select(Resource, Agency, Disaster)
    .join(Agency)
    .switch(Resource)
    .join(DisasterResponse, JOIN.LEFT_OUTER)
    .join(Disaster)
    .where(
        (Resource.status == 'available') &
        (Disaster.status == 'active') &
        (ST_DWithin(Resource.location, Disaster.location, 50000))
    )
    .order_by(ST_Distance(Resource.location, Disaster.location))
)

# Aggregation with window functions
disaster_stats = (
    Disaster
    .select(
        Disaster,
        fn.COUNT(DisasterResponse.id).over(
            partition_by=[Disaster.type]
        ).alias('type_response_count')
    )
    .join(DisasterResponse)
    .group_by(Disaster)
)
```

**ORM Optimization Strategies:**
1. **N+1 Prevention**: Used prefetch() for related objects
2. **Raw Queries**: Dropped to raw SQL for complex spatial queries
3. **Query Caching**: Implemented query result caching
4. **Batch Operations**: Used insert_many() for bulk inserts"

### Q4: Frontend Architecture & Component Library

**Question:** Describe your approach to building the reusable component library at Interlinked.

**Answer:**
"I built a comprehensive component library focusing on reusability and consistency:

**Component Structure:**
```typescript
// src/components/ui/DataTable/DataTable.tsx
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  onSort?: (column: string) => void;
  pagination?: PaginationConfig;
  loading?: boolean;
  emptyMessage?: string;
}

export function DataTable<T>({ data, columns, ...props }: DataTableProps<T>) {
  // Implementation with virtualization for performance
}

// Compound components pattern
DataTable.Header = DataTableHeader;
DataTable.Body = DataTableBody;
DataTable.Row = DataTableRow;
DataTable.Pagination = DataTablePagination;
```

**Design System Implementation:**
1. **Consistent Theming**: CSS variables for colors, spacing, typography
2. **Responsive Design**: Mobile-first approach with breakpoints
3. **Accessibility**: ARIA labels, keyboard navigation, screen reader support
4. **Documentation**: Storybook stories for each component

**Key Components Built:**
- **Form Components**: Input, Select, DatePicker with validation
- **Data Display**: Table, Card, List with sorting/filtering
- **Navigation**: Sidebar, Breadcrumb, Tabs
- **Feedback**: Alert, Toast, Modal, Loading states

**Performance Considerations:**
```typescript
// Memoization for expensive renders
const MemoizedRow = React.memo(({ item, columns }) => {
  return <tr>...</tr>;
}, (prevProps, nextProps) => {
  return prevProps.item.id === nextProps.item.id;
});

// Virtual scrolling for large datasets
import { FixedSizeList } from 'react-window';
```"

### Q5: Docker & Containerization Strategy

**Question:** How did you implement the containerization strategy and why multi-stage builds?

**Answer:**
"Our containerization strategy was crucial for consistent environments and efficient deployments:

**Multi-Stage Build Implementation:**
```dockerfile
# Build stage - compile dependencies
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Development stage - full dev environment
FROM node:18-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "dev"]

# Production stage - minimal runtime
FROM node:18-alpine AS production
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**Benefits Achieved:**
1. **Size Reduction**: 1.2GB → 180MB (85% smaller)
2. **Security**: No build tools in production image
3. **Caching**: Layer caching speeds up builds
4. **Environment Parity**: Same base image across environments

**Docker Compose for Local Development:**
```yaml
version: '3.8'
services:
  frontend:
    build:
      context: ./Interlinked-Frontend
      target: development
    volumes:
      - ./Interlinked-Frontend:/app
      - /app/node_modules  # Preserve node_modules
    environment:
      - VITE_API_URL=http://api:8000
    depends_on:
      - api

  api:
    build:
      context: ./Interlinked-Backend
      target: api
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/interlinked
      - NODE_ENV=development
    depends_on:
      postgres:
        condition: service_healthy
```

**Container Orchestration Decisions:**
- Used health checks for proper startup ordering
- Volume mounts for hot reloading in development
- Network isolation between services
- Environment-specific configurations"

### Q6: API Design & RESTful Architecture

**Question:** How did you design the RESTful APIs for Interlinked? Show me some examples.

**Answer:**
"I designed the APIs following REST principles with a focus on consistency and usability:

**API Design Principles:**
1. **Resource-Based URLs**: Nouns, not verbs
2. **HTTP Methods**: Proper use of GET, POST, PUT, PATCH, DELETE
3. **Status Codes**: Meaningful responses
4. **Versioning**: URL-based versioning (/api/v1/)

**Example Endpoints:**
```javascript
// Agency resource endpoints
GET    /api/v1/agencies              // List all agencies
GET    /api/v1/agencies/:id          // Get specific agency
POST   /api/v1/agencies              // Create new agency
PUT    /api/v1/agencies/:id          // Update entire agency
PATCH  /api/v1/agencies/:id          // Partial update
DELETE /api/v1/agencies/:id          // Delete agency

// Nested resources
GET    /api/v1/agencies/:id/resources    // Agency's resources
POST   /api/v1/agencies/:id/resources    // Add resource to agency

// Filtering and pagination
GET    /api/v1/disasters?status=active&severity=4,5&page=2&limit=20
```

**Request/Response Design:**
```javascript
// Consistent response format
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 2,
      "limit": 20,
      "total": 156,
      "pages": 8
    }
  },
  "meta": {
    "timestamp": "2025-01-22T10:30:00Z",
    "version": "1.0"
  }
}

// Error response format
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Agency with ID 123 not found",
    "details": {
      "id": "123",
      "resource": "agency"
    }
  }
}
```

**Implementation Details:**
```javascript
// Middleware for consistent responses
const apiResponse = (req, res, next) => {
  res.success = (data, meta = {}) => {
    res.json({
      success: true,
      data,
      meta: { ...meta, timestamp: new Date().toISOString() }
    });
  };
  
  res.error = (error, statusCode = 400) => {
    res.status(statusCode).json({
      success: false,
      error
    });
  };
  next();
};

// Route implementation
router.get('/agencies', async (req, res) => {
  try {
    const { page = 1, limit = 20, status } = req.query;
    const offset = (page - 1) * limit;
    
    const query = Agency.query();
    if (status) query.where('status', status);
    
    const [items, total] = await Promise.all([
      query.offset(offset).limit(limit),
      query.count()
    ]);
    
    res.success({
      items,
      pagination: {
        page: Number(page),
        limit: Number(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    res.error({
      code: 'QUERY_ERROR',
      message: error.message
    }, 500);
  }
});
```"

### Q7: Performance Optimization Journey

**Question:** You mentioned improving API response times by 81%. Walk me through the optimization process.

**Answer:**
"The optimization was a systematic process involving profiling, analysis, and targeted improvements:

**Initial Performance Profile:**
- Dashboard API: 800ms average response time
- Database queries: 600ms (75% of total time)
- Serialization: 150ms
- Network overhead: 50ms

**Step 1: Query Analysis**
```sql
-- Original N+1 query problem
-- 1 query for users + N queries for each user's resources
SELECT * FROM users WHERE agency_id = ?;
-- Then for each user:
SELECT * FROM resources WHERE user_id = ?;

-- Optimized with JOIN
SELECT 
  u.*,
  json_agg(r.*) as resources
FROM users u
LEFT JOIN resources r ON r.user_id = u.id
WHERE u.agency_id = ?
GROUP BY u.id;
```

**Step 2: Index Optimization**
```sql
-- Added composite indexes for common queries
CREATE INDEX idx_users_agency_status 
  ON users(agency_id, status) 
  WHERE status = 'active';

CREATE INDEX idx_resources_user_type 
  ON resources(user_id, resource_type);

CREATE INDEX idx_disasters_location_time 
  ON disasters USING GIST(location, created_at);
```

**Step 3: Frontend Caching**
```typescript
// Implemented smart caching strategy
class APICache {
  private cache = new Map<string, CacheEntry>();
  
  async get(key: string, fetcher: () => Promise<any>, ttl = 300000) {
    const cached = this.cache.get(key);
    
    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.data;
    }
    
    const data = await fetcher();
    this.cache.set(key, { data, timestamp: Date.now() });
    return data;
  }
  
  invalidate(pattern: string) {
    // Invalidate matching cache entries
    for (const [key] of this.cache) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}
```

**Step 4: Database Connection Pooling**
```javascript
// Optimized connection pool settings
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,                    // Maximum connections
  idleTimeoutMillis: 30000,   // Close idle connections
  connectionTimeoutMillis: 2000
});

// Reuse connections efficiently
const query = async (text, params) => {
  const client = await pool.connect();
  try {
    return await client.query(text, params);
  } finally {
    client.release();
  }
};
```

**Results:**
- Query time: 600ms → 100ms (83% reduction)
- Overall API response: 800ms → 150ms (81% reduction)
- Database CPU usage: 60% → 25%
- User satisfaction: Significantly improved"

### Q8: Security Implementation

**Question:** How do you handle security in the Interlinked application?

**Answer:**
"Security is critical for a disaster management system. Here's my comprehensive approach:

**Authentication & Authorization:**
```javascript
// JWT implementation with refresh tokens
class AuthService {
  generateTokens(user) {
    const accessToken = jwt.sign(
      { id: user.id, role: user.role },
      process.env.ACCESS_SECRET,
      { expiresIn: '15m' }
    );
    
    const refreshToken = jwt.sign(
      { id: user.id, tokenFamily: uuid() },
      process.env.REFRESH_SECRET,
      { expiresIn: '7d' }
    );
    
    // Store refresh token family in database
    return { accessToken, refreshToken };
  }
  
  async refreshTokens(oldRefreshToken) {
    const decoded = jwt.verify(oldRefreshToken, process.env.REFRESH_SECRET);
    
    // Check if token has been used (replay attack)
    const tokenRecord = await Token.findOne({ 
      userId: decoded.id, 
      family: decoded.tokenFamily 
    });
    
    if (tokenRecord.used) {
      // Revoke entire token family
      await Token.revokeFamily(decoded.tokenFamily);
      throw new Error('Token reuse detected');
    }
    
    // Mark as used and generate new tokens
    await tokenRecord.markUsed();
    return this.generateTokens({ id: decoded.id });
  }
}
```

**Input Validation & Sanitization:**
```javascript
// Using Joi for validation
const agencySchema = Joi.object({
  name: Joi.string().max(255).required(),
  type: Joi.string().valid('fire', 'police', 'medical').required(),
  location: Joi.object({
    lat: Joi.number().min(-90).max(90).required(),
    lng: Joi.number().min(-180).max(180).required()
  })
});

// Middleware for validation
const validate = (schema) => (req, res, next) => {
  const { error, value } = schema.validate(req.body);
  if (error) {
    return res.error({
      code: 'VALIDATION_ERROR',
      details: error.details
    }, 400);
  }
  req.validatedBody = value;
  next();
};
```

**Rate Limiting & DDoS Protection:**
```javascript
const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
  // Different limits for different endpoints
  keyGenerator: (req) => {
    return req.ip + ':' + req.path;
  }
});

// Stricter limits for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  skipSuccessfulRequests: true
});
```

**Security Headers & CORS:**
```javascript
// Helmet for security headers
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// CORS configuration
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = process.env.ALLOWED_ORIGINS.split(',');
    if (!origin || allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
};
```"

### Q9: Testing Strategy

**Question:** What's your testing approach for Interlinked?

**Answer:**
"I implement comprehensive testing across the stack:

**Frontend Testing (React/TypeScript):**
```typescript
// Component testing with React Testing Library
describe('DataTable Component', () => {
  it('should handle sorting correctly', async () => {
    const mockData = [
      { id: 1, name: 'Agency A', type: 'fire' },
      { id: 2, name: 'Agency B', type: 'police' }
    ];
    
    const onSort = jest.fn();
    const { getByRole } = render(
      <DataTable 
        data={mockData} 
        columns={columns} 
        onSort={onSort}
      />
    );
    
    const nameHeader = getByRole('columnheader', { name: /name/i });
    await userEvent.click(nameHeader);
    
    expect(onSort).toHaveBeenCalledWith('name');
  });
  
  it('should be accessible', async () => {
    const { container } = render(<DataTable {...props} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

**Backend Testing (Node.js):**
```javascript
// API endpoint testing
describe('POST /api/v1/agencies', () => {
  beforeEach(async () => {
    await db.migrate.latest();
    await db.seed.run();
  });
  
  afterEach(async () => {
    await db.migrate.rollback();
  });
  
  it('should create agency with valid data', async () => {
    const response = await request(app)
      .post('/api/v1/agencies')
      .set('Authorization', `Bearer ${validToken}`)
      .send({
        name: 'Test Fire Department',
        type: 'fire',
        location: { lat: 40.7128, lng: -74.0060 }
      });
      
    expect(response.status).toBe(201);
    expect(response.body.success).toBe(true);
    expect(response.body.data).toMatchObject({
      name: 'Test Fire Department',
      type: 'fire'
    });
  });
  
  it('should enforce rate limiting', async () => {
    // Make 6 requests (limit is 5)
    const requests = Array(6).fill(null).map(() => 
      request(app).post('/api/v1/auth/login').send(credentials)
    );
    
    const responses = await Promise.all(requests);
    const tooManyRequests = responses.filter(r => r.status === 429);
    expect(tooManyRequests.length).toBeGreaterThan(0);
  });
});
```

**Integration Testing:**
```javascript
// Database transaction testing
describe('Disaster Response Coordination', () => {
  it('should handle concurrent resource assignments', async () => {
    const disaster = await createDisaster();
    const resources = await createResources(5);
    
    // Simulate concurrent assignments
    const assignments = resources.map(resource => 
      assignResourceToDisaster(resource.id, disaster.id)
    );
    
    await Promise.all(assignments);
    
    // Verify no double assignments
    const assignedResources = await getAssignedResources(disaster.id);
    expect(assignedResources.length).toBe(5);
    expect(new Set(assignedResources.map(r => r.id)).size).toBe(5);
  });
});
```

**Performance Testing:**
```javascript
// Load testing with k6
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function () {
  const response = http.get('https://api.interlinked.com/v1/disasters');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```"

### Q10: Challenges & Problem Solving

**Question:** What was the most challenging problem you faced at Interlinked and how did you solve it?

**Answer (STAR Format):**
**Situation:** We discovered that during large-scale disasters, multiple agencies were trying to claim the same resources simultaneously, causing data inconsistencies and coordination failures.

**Task:** Design a system that ensures resource allocation integrity while maintaining real-time performance for emergency responders.

**Action:** 
1. **Analyzed the Problem**: Used logging to identify race conditions in resource assignment
2. **Researched Solutions**: Evaluated optimistic locking, pessimistic locking, and distributed locks
3. **Implemented Solution**:
   ```javascript
   // Optimistic locking with retry logic
   async function assignResource(resourceId, disasterId, agencyId) {
     const maxRetries = 3;
     let retries = 0;
     
     while (retries < maxRetries) {
       try {
         return await db.transaction(async (trx) => {
           // Get resource with current version
           const resource = await trx('resources')
             .where({ id: resourceId })
             .first();
             
           if (resource.status !== 'available') {
             throw new Error('Resource not available');
           }
           
           // Update with version check
           const updated = await trx('resources')
             .where({ 
               id: resourceId, 
               version: resource.version 
             })
             .update({
               status: 'assigned',
               assigned_to: agencyId,
               disaster_id: disasterId,
               version: resource.version + 1
             });
             
           if (updated === 0) {
             throw new Error('Concurrent modification');
           }
           
           // Log assignment
           await trx('resource_assignments').insert({
             resource_id: resourceId,
             agency_id: agencyId,
             disaster_id: disasterId,
             assigned_at: new Date()
           });
           
           return { success: true };
         });
       } catch (error) {
         if (error.message === 'Concurrent modification' && retries < maxRetries - 1) {
           retries++;
           await new Promise(resolve => setTimeout(resolve, 100 * retries));
           continue;
         }
         throw error;
       }
     }
   }
   ```

**Result:** 
- Eliminated resource double-assignment issues
- Maintained sub-200ms response times
- System successfully handled 500+ concurrent assignment requests during disaster drills
- Received positive feedback from emergency coordinators

## Common Behavioral Questions for Interlinked

### Why are you passionate about working on Interlinked?

"Working on Interlinked combines my technical skills with meaningful impact. Building systems that help coordinate disaster response and potentially save lives is incredibly motivating. The technical challenges—real-time coordination, high reliability, complex data visualization—push me to grow as an engineer while contributing to public safety."

### How do you prioritize tasks when everything seems urgent?

"In a disaster management system, I use a framework based on:
1. **Life Safety Impact**: Features affecting immediate emergency response get top priority
2. **System Stability**: Critical bugs that could cause downtime
3. **User Blocking Issues**: Problems preventing agencies from using core features
4. **Performance**: Optimizations that improve response times
5. **Enhancements**: New features and nice-to-haves

I document decisions and communicate with stakeholders to ensure alignment."

### Describe a time you had to make a technical decision with incomplete information

"When designing the real-time alerting system for Interlinked, we didn't have complete requirements for all agency notification preferences. I made the decision to build a flexible notification pipeline that could accommodate multiple channels (email, SMS, push) with configurable rules. This allowed us to start with basic email notifications and progressively add channels as requirements became clearer, without major refactoring."

## Questions to Ask Interviewers

1. **Technical Challenges**: "What are the most interesting technical challenges the Interlinked team is currently facing?"

2. **Scale**: "How many agencies and concurrent users does Interlinked currently support, and what are the growth projections?"

3. **Tech Debt**: "How does the team balance adding new features with addressing technical debt?"

4. **Testing**: "What's the current test coverage, and what testing practices does the team follow?"

5. **Deployment**: "How often does Interlinked deploy to production, and what does the release process look like?"

6. **On-Call**: "Is there an on-call rotation for Interlinked, given its critical nature?"

7. **Architecture Evolution**: "Are there plans to evolve the architecture (e.g., event-driven, microservices)?"

8. **Team Growth**: "How is the Interlinked team structured, and how do you see it growing?"

## AWS & Cloud Infrastructure Questions

### Q11: AWS Lambda & Serverless Architecture

**Question:** How would you migrate parts of Interlinked to AWS Lambda? What are the benefits and challenges?

**Answer:**
"For Interlinked, I'd identify specific functions that are good candidates for Lambda migration:

**Lambda Migration Strategy:**
```typescript
// Example: Data processing Lambda function
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { DynamoDB } from 'aws-sdk';

export const processDisasterAlert = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    const { disaster } = JSON.parse(event.body || '{}');
    
    // Process disaster data
    const processedData = await analyzeDisasterSeverity(disaster);
    
    // Store in DynamoDB
    const dynamodb = new DynamoDB.DocumentClient();
    await dynamodb.put({
      TableName: 'DisasterAlerts',
      Item: {
        id: generateId(),
        ...processedData,
        timestamp: Date.now()
      }
    }).promise();
    
    // Trigger SNS notification
    await sendAlertNotifications(processedData);
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ success: true, data: processedData })
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
```

**Good Lambda Candidates:**
1. **Data Processing**: Alert analysis, report generation
2. **Scheduled Tasks**: Daily data aggregation, cleanup
3. **Event-Driven**: Webhook handlers, notification triggers
4. **Image Processing**: Map tile generation, photo analysis

**Lambda Benefits:**
- **Cost Efficiency**: Pay only for execution time
- **Auto Scaling**: Handles traffic spikes automatically
- **No Server Management**: Focus on code, not infrastructure
- **Event Integration**: Natural fit with SNS, SQS, S3

**Challenges & Solutions:**
```typescript
// Cold start optimization
export const handler = async (event: any) => {
  // Reuse connections across invocations
  if (!global.dbConnection) {
    global.dbConnection = await createDatabaseConnection();
  }
  
  // Provisioned concurrency for critical functions
  return processRequest(event);
};

// Memory and timeout tuning
const lambdaConfig = {
  memorySize: 1024, // Optimal for our workload
  timeout: 30, // Balance between cost and reliability
  reservedConcurrency: 100 // Prevent runaway costs
};
```

**Hybrid Architecture:**
- Keep real-time APIs in containers (consistent latency)
- Move batch processing to Lambda (cost optimization)
- Use API Gateway for Lambda endpoints
- Implement circuit breakers for reliability"

### Q12: Next.js Architecture & Performance

**Question:** How would you structure a Next.js application for Interlinked's frontend? Focus on performance and SEO.

**Answer:**
"For a mission-critical application like Interlinked, I'd leverage Next.js's full-stack capabilities:

**Project Structure:**
```
interlinked-next/
├── pages/
│   ├── api/           # API routes
│   ├── dashboard/     # Dynamic routes
│   ├── _app.tsx       # App wrapper
│   └── _document.tsx  # HTML document
├── components/
│   ├── ui/           # Reusable components
│   ├── dashboard/    # Page-specific
│   └── forms/        # Form components
├── lib/
│   ├── auth.ts       # Authentication
│   ├── api.ts        # API client
│   └── utils.ts      # Utilities
├── styles/
├── types/
└── middleware.ts     # Route protection
```

**Performance Optimizations:**
```typescript
// pages/dashboard/index.tsx - Static generation where possible
import { GetStaticProps, GetStaticPaths } from 'next';
import { revalidate } from 'lib/cache';

export const getStaticProps: GetStaticProps = async () => {
  const agencies = await fetchAgencies();
  
  return {
    props: { agencies },
    revalidate: 300, // ISR - revalidate every 5 minutes
  };
};

// Dynamic imports for code splitting
const DisasterMap = dynamic(() => import('components/DisasterMap'), {
  loading: () => <MapSkeleton />,
  ssr: false // Client-side only for maps
});

// Image optimization
import Image from 'next/image';

const AgencyCard = ({ agency }: { agency: Agency }) => (
  <div className="card">
    <Image
      src={agency.logo}
      alt={agency.name}
      width={100}
      height={100}
      priority={false}
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
    />
  </div>
);
```

**API Routes for Backend Integration:**
```typescript
// pages/api/disasters/[id].ts
import { NextApiRequest, NextApiResponse } from 'next';
import { withAuth } from 'lib/auth';
import { rateLimit } from 'lib/rate-limit';

async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { id } = req.query;
  
  if (req.method === 'GET') {
    try {
      const disaster = await fetch(`${process.env.API_URL}/disasters/${id}`, {
        headers: {
          'Authorization': `Bearer ${req.headers.authorization}`
        }
      });
      
      return res.json(await disaster.json());
    } catch (error) {
      return res.status(500).json({ error: 'Failed to fetch disaster' });
    }
  }
  
  return res.status(405).json({ error: 'Method not allowed' });
}

export default withAuth(rateLimit(handler));
```

**SEO & Meta Optimization:**
```typescript
// components/SEOHead.tsx
import Head from 'next/head';

interface SEOProps {
  title: string;
  description: string;
  canonical?: string;
}

export const SEOHead = ({ title, description, canonical }: SEOProps) => (
  <Head>
    <title>{title} | Interlinked</title>
    <meta name="description" content={description} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="og:type" content="website" />
    {canonical && <link rel="canonical" href={canonical} />}
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </Head>
);

// Usage in pages
const DashboardPage = () => (
  <>
    <SEOHead 
      title="Emergency Dashboard"
      description="Real-time disaster management and response coordination"
    />
    <DashboardContent />
  </>
);
```

**Middleware for Authentication:**
```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { verifyJWT } from 'lib/auth';

export async function middleware(request: NextRequest) {
  // Protect dashboard routes
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    const token = request.cookies.get('auth-token')?.value;
    
    if (!token || !(await verifyJWT(token))) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
  
  // Rate limiting for API routes
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const ip = request.ip || 'unknown';
    const isRateLimited = await checkRateLimit(ip);
    
    if (isRateLimited) {
      return new NextResponse('Too Many Requests', { status: 429 });
    }
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*']
};
```"

### Q13: TypeScript Advanced Patterns

**Question:** Show me how you'd implement type-safe API calls and state management in TypeScript.

**Answer:**
"I focus on leveraging TypeScript's type system for runtime safety and developer experience:

**Type-Safe API Client:**
```typescript
// types/api.ts - Define API contract
interface APIEndpoints {
  'GET /api/agencies': {
    query?: { status?: string; page?: number };
    response: { agencies: Agency[]; pagination: Pagination };
  };
  'POST /api/agencies': {
    body: CreateAgencyRequest;
    response: Agency;
  };
  'GET /api/disasters/:id': {
    params: { id: string };
    response: Disaster;
  };
}

// Generic API client with type safety
class TypedAPIClient {
  async request<T extends keyof APIEndpoints>(
    endpoint: T,
    config: APIEndpoints[T] extends { query: infer Q }
      ? { query?: Q }
      : APIEndpoints[T] extends { body: infer B }
      ? { body: B }
      : APIEndpoints[T] extends { params: infer P }
      ? { params: P }
      : {}
  ): Promise<APIEndpoints[T]['response']> {
    const [method, path] = endpoint.split(' ') as [string, string];
    
    let url = path;
    
    // Handle path parameters
    if ('params' in config) {
      Object.entries(config.params as Record<string, string>).forEach(
        ([key, value]) => {
          url = url.replace(`:${key}`, value);
        }
      );
    }
    
    // Handle query parameters
    if ('query' in config) {
      const searchParams = new URLSearchParams(config.query as any);
      url += `?${searchParams}`;
    }
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: 'body' in config ? JSON.stringify(config.body) : undefined
    });
    
    if (!response.ok) {
      throw new APIError(response.status, await response.text());
    }
    
    return response.json();
  }
}

// Usage with full type safety
const api = new TypedAPIClient();

// TypeScript knows the exact shape of response
const agencies = await api.request('GET /api/agencies', {
  query: { status: 'active', page: 1 } // Type checked
});

const newAgency = await api.request('POST /api/agencies', {
  body: { // Type checked against CreateAgencyRequest
    name: 'Fire Dept',
    type: 'fire',
    location: { lat: 40.7, lng: -74.0 }
  }
});
```

**Advanced Type Patterns:**
```typescript
// Discriminated unions for different disaster types
type DisasterBase = {
  id: string;
  location: Coordinates;
  severity: 1 | 2 | 3 | 4 | 5;
};

type FireDisaster = DisasterBase & {
  type: 'fire';
  burnArea: number;
  containmentPercent: number;
};

type FloodDisaster = DisasterBase & {
  type: 'flood';
  waterLevel: number;
  affectedAreas: string[];
};

type EarthquakeDisaster = DisasterBase & {
  type: 'earthquake';
  magnitude: number;
  depth: number;
};

type Disaster = FireDisaster | FloodDisaster | EarthquakeDisaster;

// Type-safe disaster handling
function getDisasterResponse(disaster: Disaster): ResponsePlan {
  switch (disaster.type) {
    case 'fire':
      // TypeScript knows this is FireDisaster
      return {
        requiredEquipment: ['fire-truck', 'water-tanker'],
        estimatedContainmentTime: disaster.burnArea / 10,
        evacuationRadius: disaster.containmentPercent < 50 ? 5000 : 2000
      };
    case 'flood':
      // TypeScript knows this is FloodDisaster
      return {
        requiredEquipment: ['rescue-boat', 'pump'],
        affectedPopulation: calculateAffectedPopulation(disaster.affectedAreas)
      };
    case 'earthquake':
      // TypeScript knows this is EarthquakeDisaster
      return {
        requiredEquipment: ['search-rescue', 'medical'],
        structuralAssessment: disaster.magnitude > 6.0
      };
    default:
      // TypeScript ensures exhaustive checking
      const _exhaustive: never = disaster;
      throw new Error('Unknown disaster type');
  }
}
```

**State Management with TypeScript:**
```typescript
// Zustand store with TypeScript
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface DisasterState {
  disasters: Disaster[];
  selectedDisaster: Disaster | null;
  loading: boolean;
  error: string | null;
}

interface DisasterActions {
  fetchDisasters: () => Promise<void>;
  selectDisaster: (id: string) => void;
  updateDisaster: (id: string, updates: Partial<Disaster>) => void;
  clearError: () => void;
}

type DisasterStore = DisasterState & DisasterActions;

export const useDisasterStore = create<DisasterStore>()()
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // State
        disasters: [],
        selectedDisaster: null,
        loading: false,
        error: null,
        
        // Actions
        fetchDisasters: async () => {
          set((state) => {
            state.loading = true;
            state.error = null;
          });
          
          try {
            const response = await api.request('GET /api/disasters');
            set((state) => {
              state.disasters = response.disasters;
              state.loading = false;
            });
          } catch (error) {
            set((state) => {
              state.error = error.message;
              state.loading = false;
            });
          }
        },
        
        selectDisaster: (id: string) => {
          set((state) => {
            state.selectedDisaster = state.disasters.find(d => d.id === id) || null;
          });
        },
        
        updateDisaster: (id: string, updates: Partial<Disaster>) => {
          set((state) => {
            const index = state.disasters.findIndex(d => d.id === id);
            if (index !== -1) {
              Object.assign(state.disasters[index], updates);
            }
          });
        },
        
        clearError: () => {
          set((state) => {
            state.error = null;
          });
        }
      }))
    ),
    { name: 'disaster-store' }
  )
);

// React hooks with TypeScript
function usePaginatedDisasters(page: number, limit: number) {
  const [data, setData] = useState<{
    disasters: Disaster[];
    pagination: Pagination;
  } | null>(null);
  
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await api.request('GET /api/disasters', {
          query: { page, limit }
        });
        setData(response);
      } catch (error) {
        console.error('Failed to fetch disasters:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [page, limit]);
  
  return { data, loading };
}
```"

### Q14: AWS Deployment & Infrastructure

**Question:** How would you deploy the Interlinked application to AWS using modern best practices?

**Answer:**
"I'd design a scalable, secure AWS architecture leveraging multiple services:

**Infrastructure as Code (CDK):**
```typescript
// lib/interlinked-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

export class InterlinkedStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // VPC with public/private subnets
    const vpc = new ec2.Vpc(this, 'InterlinkedVPC', {
      maxAzs: 3,
      natGateways: 2,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC
        },
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS
        },
        {
          cidrMask: 24,
          name: 'Database',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED
        }
      ]
    });
    
    // RDS PostgreSQL with Multi-AZ
    const database = new rds.DatabaseInstance(this, 'InterlinkedDB', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MEDIUM
      ),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      multiAz: true,
      backupRetention: cdk.Duration.days(7),
      deletionProtection: true,
      storageEncrypted: true
    });
    
    // ElastiCache Redis cluster
    const redisSubnetGroup = new elasticache.CfnSubnetGroup(this, 'RedisSubnetGroup', {
      description: 'Subnet group for Redis',
      subnetIds: vpc.privateSubnets.map(subnet => subnet.subnetId)
    });
    
    const redis = new elasticache.CfnCacheCluster(this, 'InterlinkedRedis', {
      cacheNodeType: 'cache.t3.micro',
      engine: 'redis',
      numCacheNodes: 1,
      cacheSubnetGroupName: redisSubnetGroup.ref
    });
    
    // ECS Cluster for containerized apps
    const cluster = new ecs.Cluster(this, 'InterlinkedCluster', {
      vpc,
      containerInsights: true
    });
    
    // Fargate service for API
    const apiTaskDefinition = new ecs.FargateTaskDefinition(this, 'APITask', {
      memoryLimitMiB: 1024,
      cpu: 512
    });
    
    const apiContainer = apiTaskDefinition.addContainer('APIContainer', {
      image: ecs.ContainerImage.fromRegistry('interlinked/api:latest'),
      environment: {
        NODE_ENV: 'production',
        DATABASE_URL: `postgresql://user:pass@${database.instanceEndpoint.hostname}:5432/interlinked`,
        REDIS_URL: `redis://${redis.attrRedisEndpointAddress}:6379`
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'interlinked-api'
      })
    });
    
    apiContainer.addPortMappings({
      containerPort: 8000,
      protocol: ecs.Protocol.TCP
    });
    
    // Lambda functions for event processing
    const disasterProcessor = new lambda.Function(this, 'DisasterProcessor', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/disaster-processor'),
      environment: {
        DATABASE_URL: database.instanceEndpoint.hostname
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 512
    });
    
    // API Gateway for Lambda functions
    const api = new apigateway.RestApi(this, 'InterlinkedAPI', {
      restApiName: 'Interlinked Service',
      description: 'API for Interlinked disaster management'
    });
    
    const disasterResource = api.root.addResource('disasters');
    disasterResource.addMethod('POST', new apigateway.LambdaIntegration(disasterProcessor));
  }
}
```

**Container Deployment Pipeline:**
```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
        
      - name: Build and push API image
        run: |
          docker build -t $ECR_REGISTRY/interlinked-api:$GITHUB_SHA ./api
          docker tag $ECR_REGISTRY/interlinked-api:$GITHUB_SHA $ECR_REGISTRY/interlinked-api:latest
          docker push $ECR_REGISTRY/interlinked-api:$GITHUB_SHA
          docker push $ECR_REGISTRY/interlinked-api:latest
          
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster interlinked-cluster \
            --service interlinked-api \
            --force-new-deployment
            
      - name: Deploy Lambda functions
        run: |
          cd lambda/disaster-processor
          npm ci
          npm run build
          aws lambda update-function-code \
            --function-name disaster-processor \
            --zip-file fileb://dist.zip
```

**Monitoring & Observability:**
```typescript
// Custom CloudWatch metrics
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

class MetricsService {
  private cloudwatch = new CloudWatchClient({ region: 'us-east-1' });
  
  async recordAPILatency(endpoint: string, duration: number) {
    await this.cloudwatch.send(new PutMetricDataCommand({
      Namespace: 'Interlinked/API',
      MetricData: [{
        MetricName: 'RequestDuration',
        Dimensions: [{
          Name: 'Endpoint',
          Value: endpoint
        }],
        Value: duration,
        Unit: 'Milliseconds',
        Timestamp: new Date()
      }]
    }));
  }
  
  async recordActiveDisasters(count: number) {
    await this.cloudwatch.send(new PutMetricDataCommand({
      Namespace: 'Interlinked/Business',
      MetricData: [{
        MetricName: 'ActiveDisasters',
        Value: count,
        Unit: 'Count',
        Timestamp: new Date()
      }]
    }));
  }
}
```

**Benefits of This Architecture:**
1. **Scalability**: Auto-scaling ECS services, Lambda concurrency
2. **Reliability**: Multi-AZ deployments, health checks
3. **Security**: VPC isolation, encrypted storage, IAM roles
4. **Cost Optimization**: Fargate spot instances, Lambda pay-per-use
5. **Monitoring**: CloudWatch metrics, X-Ray tracing
6. **Disaster Recovery**: Automated backups, cross-region replication"

Your Interlinked experience demonstrates strong full-stack capabilities, architecture design skills, and the ability to build mission-critical systems. Focus on the impact and technical depth of your contributions!