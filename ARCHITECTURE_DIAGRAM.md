# TalentPilot-AI System Architecture

```mermaid
graph TB
    subgraph Client["🖥️ Frontend - React/TypeScript/Vite"]
        direction TB
        Auth["🔐 Auth Context<br/>- Session Management<br/>- RequireAuth Guards"]
        Router["🧭 React Router<br/>- /login<br/>- /hr/dashboard<br/>- /employee/content<br/>- /assignments/:id/watch"]
        
        HRPages["HR Pages<br/>- Dashboard.tsx<br/>- AssignmentModal.tsx"]
        EmployeePages["Employee Pages<br/>- ContentDiscovery.tsx<br/>- AssignmentWatch.tsx"]
        
        Components["🎨 Shared Components<br/>- VideoPlayer.tsx<br/>- DashboardPage.tsx<br/>- AssignmentsList.tsx<br/>- StatusBadge.tsx<br/>- ContinueWatchingCard.tsx<br/>- ProvenanceDrillDownModal.tsx"]
        
        State["📊 State Management<br/>- React Hooks<br/>- useState/useEffect<br/>- useRef (Polling)<br/>- useImperativeHandle"]
        
        API["📡 HTTP Client<br/>- dashboardApi<br/>- axios"]
    end
    
    subgraph BackendAPI["⚙️ Backend API - Node.js/Express"]
        direction TB
        AppServer["Express App<br/>main.ts"]
        
        AuthRouter["🔐 Auth Routes<br/>- POST /auth/login<br/>- POST /auth/logout<br/>- POST /auth/verify"]
        
        AssignRouter["📋 Assignment Routes<br/>- GET /assignments<br/>- POST /assignments<br/>- PUT /assignments/:id<br/>- DELETE /assignments/:id"]
        
        DashboardRouter["📊 Dashboard Routes<br/>- GET /dashboard<br/>- GET /dashboard/summary"]
        
        VideoRouter["🎥 Video Routes<br/>- GET /videos<br/>- POST /videos/:id/watch<br/>- PUT /videos/:id/progress"]
        
        Services["🔧 Business Logic<br/>- AuthService<br/>- AssignmentService<br/>- DashboardService<br/>- VideoService"]
        
        Middleware["⚔️ Middleware<br/>- Auth Guard<br/>- Error Handler<br/>- Request Logging<br/>- CORS"]
    end
    
    subgraph Database["💾 PostgreSQL Database"]
        direction TB
        Users["👥 Users Table<br/>- id (PK)<br/>- email<br/>- password_hash<br/>- role (HR/Employee)<br/>- created_at"]
        
        Assignments["📋 Assignments Table<br/>- id (PK)<br/>- employee_id (FK)<br/>- skill_id (FK)<br/>- status<br/>- created_at<br/>- updated_at"]
        
        Skills["🎯 Skills Table<br/>- id (PK)<br/>- name<br/>- description<br/>- category"]
        
        Videos["🎬 Videos Table<br/>- id (PK)<br/>- skill_id (FK)<br/>- url<br/>- title<br/>- duration<br/>- thumbnail"]
        
        Progress["📈 Progress Table<br/>- id (PK)<br/>- assignment_id (FK)<br/>- employee_id (FK)<br/>- watch_time<br/>- status_percentage<br/>- provenance<br/>- last_updated"]
    end
    
    subgraph Polling["🔄 Auto-Polling System"]
        direction TB
        PollInterval["12-Second Interval<br/>window.setInterval"]
        PollLogic["Poll Logic<br/>- Check visibility<br/>- Skip if in-flight<br/>- Snapshot requestId"]
        DiffCalc["Diff Detection<br/>- Status changes<br/>- Provenance changes<br/>- Progress % changes"]
        Announce["📢 Announce via aria-live<br/>Screen Reader Support"]
    end
    
    subgraph External["🌐 External Services"]
        YouTube["YouTube API<br/>- Video Search<br/>- Metadata<br/>- Thumbnails"]
    end
    
    subgraph Infrastructure["🚀 Infrastructure - Docker Compose"]
        direction TB
        FrontendContainer["Frontend Container<br/>React Dev Server<br/>Port 5173"]
        BackendContainer["Backend Container<br/>Node.js/Express<br/>Port 3000"]
        PostgresContainer["PostgreSQL Container<br/>Port 5432<br/>Volume: postgres_data"]
    end
    
    %% Client Layer
    Auth --> Router
    Router --> HRPages
    Router --> EmployeePages
    Router --> Components
    HRPages --> Components
    EmployeePages --> Components
    Components --> State
    State --> API
    
    %% Frontend to Backend
    API -->|HTTP GET/POST/PUT/DELETE| AppServer
    
    %% Backend Structure
    AppServer --> AuthRouter
    AppServer --> AssignRouter
    AppServer --> DashboardRouter
    AppServer --> VideoRouter
    AppServer --> Middleware
    
    AuthRouter --> Services
    AssignRouter --> Services
    DashboardRouter --> Services
    VideoRouter --> Services
    
    %% Backend to Database
    Services -->|Query| Users
    Services -->|Query| Assignments
    Services -->|Query| Skills
    Services -->|Query| Videos
    Services -->|Query| Progress
    
    %% Auto-Polling
    Components -->|Triggers| Polling
    PollInterval --> PollLogic
    PollLogic --> DiffCalc
    DiffCalc --> Announce
    Announce -->|Updates UI| Components
    
    %% External
    Services -.->|API Call| YouTube
    
    %% Infrastructure
    Infrastructure -->|runs| FrontendContainer
    Infrastructure -->|runs| BackendContainer
    Infrastructure -->|runs| PostgresContainer
    FrontendContainer -->|serves| Client
    BackendContainer -->|hosts| BackendAPI
    PostgresContainer -->|hosts| Database
    
    %% Styling
    classDef frontend fill:#61dafb,stroke:#333,stroke-width:2px,color:#000
    classDef backend fill:#68a063,stroke:#333,stroke-width:2px,color:#fff
    classDef database fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    classDef polling fill:#ffc107,stroke:#333,stroke-width:2px,color:#000
    classDef external fill:#ff5722,stroke:#333,stroke-width:2px,color:#fff
    classDef infra fill:#2196f3,stroke:#333,stroke-width:2px,color:#fff
    
    class Client frontend
    class BackendAPI,AppServer,AuthRouter,AssignRouter,DashboardRouter,VideoRouter,Services,Middleware backend
    class Database,Users,Assignments,Skills,Videos,Progress database
    class Polling,PollInterval,PollLogic,DiffCalc,Announce polling
    class External,YouTube external
    class Infrastructure,FrontendContainer,BackendContainer,PostgresContainer infra
```

## Architecture Components

### 🖥️ Frontend Layer (React/TypeScript)

**Routing & Authentication:**
- `AuthContext` - Manages user session and role-based access
- `RequireAuth` - Guards protected routes
- React Router - Handles navigation between pages

**Pages:**
- **HR Routes**: Dashboard for skill assignments, create/manage assignments
- **Employee Routes**: Content discovery, video watching, progress tracking

**Components:**
- `DashboardPage` - Main HR interface with auto-polling, grouped by employee
- `VideoPlayer` - Embedded video playback with controls
- `ProvenanceDrillDownModal` - HR can view and override assignment status
- `StatusBadge` - Visual status indicators (Not Started, In Progress, Completed)
- `ContinueWatchingCard` - Resume from where employee left off

**State Management:**
- React Hooks for local state
- `useRef` for polling interval and in-flight tracking
- `useImperativeHandle` for exposing dashboard refresh method
- Toast notifications for user feedback

### ⚙️ Backend Layer (Node.js/Express)

**Route Modules:**
- **Auth Routes** - Login, logout, session verification
- **Assignment Routes** - CRUD operations for skill assignments
- **Dashboard Routes** - Aggregated assignment data for HR view
- **Video Routes** - Video metadata, watch tracking, progress updates

**Services:**
- Business logic layer handling validation and data operations
- Calls repositories to interact with database

**Middleware:**
- Authentication guard for protected endpoints
- Global error handler
- Request logging
- CORS configuration

### 💾 Database Layer (PostgreSQL)

**Tables:**
- **Users** - Employee and HR accounts with roles
- **Assignments** - Skill assignments linking employees to skills
- **Skills** - Available training skills/competencies
- **Videos** - Training video metadata and URLs
- **Progress** - Tracks employee progress on assignments (watch time, completion %, provenance)

### 🔄 Auto-Polling System

**Features:**
- 12-second polling interval while dashboard is visible
- Detects changes in: status, provenance, completion percentage
- Uses `requestId` to prevent race conditions from slow responses
- Announces changes via aria-live region for screen reader accessibility
- Pauses when browser tab is hidden (visibility API)

### 🚀 Infrastructure (Docker Compose)

**Services:**
- **Frontend Container** - React dev server on port 5173
- **Backend Container** - Node.js/Express API on port 3000
- **PostgreSQL Container** - Database on port 5432 with persistent volume

## Data Flow

1. **Authentication**: User → Frontend → Backend → Database (session created)
2. **View Dashboard**: Frontend polls → Backend aggregates → Database queries
3. **Create Assignment**: HR form → Backend CRUD → Database + toast notification
4. **Auto-Update**: 12s polling → Diff detection → aria-live announcement → UI refresh
5. **Watch Video**: Employee → Video player → Backend tracks progress → Database update
6. **Progress Tracking**: Video metadata → Progress calculation → Status update
