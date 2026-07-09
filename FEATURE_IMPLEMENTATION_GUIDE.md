# Content Discovery to Continue Watching - Implementation Guide

## Feature Overview

This feature enables Casey (user) to:
1. **Browse** a list of assigned videos on the Content Discovery page
2. **Select** a video to watch
3. **Navigate** to the Continue Watching page with full video details
4. **Resume** from where they left off or start fresh

## Architecture

### Data Flow

```
demo-data.js (DEMO_DATA)
    ↓
prototype-api.js (PrototypeAPI methods)
    ↓
sessionStorage (selected_video)
    ↓
02.1-Content-Discovery.html (list view)
    ↓ (selectVideo)
    ↓
02.2-Continue-Watching.html (detail view)
```

### Component Breakdown

#### 02.1-Content-Discovery.html

**HTML Structure:**
```html
<main id="page-main-content">
  <div class="mb-6">
    <h1>Your Assigned Videos</h1>
    <p>Select a video to continue watching or start a new one</p>
  </div>
  
  <div id="videos-list-container" class="space-y-4">
    <!-- Dynamically populated video cards -->
    <div class="bg-white rounded-lg shadow-sm p-6 border cursor-pointer">
      <!-- Thumbnail, info, progress -->
    </div>
    <!-- Repeat for each video -->
  </div>
</main>
```

**JavaScript Functions:**

| Function | Purpose | Returns |
|----------|---------|---------|
| `loadAssignedVideos()` | Fetches videos from API and renders cards | void |
| `createVideoCard(video)` | Generates DOM element for single video | HTMLDivElement |
| `selectVideo(video)` | Stores video selection and navigates | void |

**Key Features:**
- Responsive grid layout (max-width: 4xl)
- Hover effects highlight interactive cards
- Progress bar shows watch percentage
- Empty/error states with helpful messages
- Direct API integration with PrototypeAPI

#### 02.2-Continue-Watching.html

**HTML Structure:**
```html
<main id="page-main-content">
  <div class="bg-white rounded-lg shadow-sm p-6">
    <!-- Single video detail card with player, progress, controls -->
    <div id="continue-watching-thumbnail"><!-- Video player area --></div>
    <div id="continue-watching-progress-bar"><!-- Progress indicator --></div>
    <button id="continue-watching-btn-resume"><!-- Resume/Start button --></button>
  </div>
</main>
```

**JavaScript Functions:**

| Function | Purpose | Returns |
|----------|---------|---------|
| `loadContinueWatching()` | Loads selected video or demo data | void |
| `displaySelectedVideo(video)` | Renders selected video details | void |
| `displayVideoData(data)` | Renders fallback demo video | void |
| `getTimestamp(minutes)` | Converts minutes to HH:MM format | string |

**Key Features:**
- Retrieves selected video from sessionStorage
- Calculates and displays watch progress
- Dynamic button labels based on progress
- Fallback to demo data if no selection
- Loading, loaded, empty, and error states

### Data Structure

#### Video Object

```javascript
{
  id: "video-1",
  skillName: "Data Visualization Fundamentals",
  status: "Assigned · Awaiting first watch",
  content: {
    title: "Data Visualization Fundamentals",
    source: "YouTube",
    durationMinutes: 28,
    approved: true,
    description: "Core principles of clear, honest data visualization."
  },
  watchProgress: 0  // 0-100 percentage
}
```

#### SessionStorage Keys

| Key | Purpose | Example Value |
|-----|---------|---|
| `talentpilot_prototype_data_scenario02` | Stores all demo data | `{...DEMO_DATA}` |
| `selected_video` | Stores selected video for Continue Watching | `{...video object}` |

### API Methods

#### PrototypeAPI.getAssignedVideos()
```javascript
// Returns all videos assigned to current user
const videos = await PrototypeAPI.getAssignedVideos();
// Returns: [video1, video2, video3, ...]
```

#### PrototypeAPI.selectVideo(videoId)
```javascript
// Stores video selection in sessionStorage
const selected = await PrototypeAPI.selectVideo('video-1');
// Returns: video object
// Side effect: Updates sessionStorage['selected_video']
```

#### PrototypeAPI.getSelectedVideo()
```javascript
// Retrieves previously selected video
const video = await PrototypeAPI.getSelectedVideo();
// Returns: video object or null
```

## UI/UX Details

### Video Card (Content Discovery)

**Visual Structure:**
```
┌─ Video Card ───────────────────────────────────────┐
│                                                    │
│  ┌──────────┐  Skill Name                      → │
│  │          │  Video Title                        │
│  │ Thumbnail│  Source · Duration · Approved      │
│  │          │  ▓▓▓▓░░░░░ 40% watched             │
│  └──────────┘                                      │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Interaction:**
- Click anywhere on card → Navigate to Continue Watching
- Hover → Shadow/border enhance
- Progress bar shows only if watchProgress > 0

### Styling Constants

| Element | Tailwind Classes |
|---------|-----------------|
| Card container | `bg-white rounded-lg shadow-sm p-6 border cursor-pointer hover:shadow-md hover:border-talentpilot-300` |
| Title | `font-semibold text-gray-900` |
| Subtitle | `text-sm text-gray-600` |
| Badge | `inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800` |
| Progress bar | `w-full h-1 bg-gray-100 rounded-full overflow-hidden` |

## Integration Checklist

- [x] Demo data includes 3 sample videos
- [x] PrototypeAPI has `getAssignedVideos()` method
- [x] PrototypeAPI has `selectVideo()` method
- [x] PrototypeAPI has `getSelectedVideo()` method
- [x] 02.1 HTML displays video list
- [x] 02.1 JavaScript loads and renders videos
- [x] 02.1 Video cards are clickable
- [x] 02.1 Click stores selection and navigates
- [x] 02.2 JavaScript checks for selected video
- [x] 02.2 Displays selected video details
- [x] 02.2 Falls back to demo data if needed
- [x] Progress bar renders based on watchProgress
- [x] Button labels update dynamically
- [x] Error states handled gracefully

## Testing Matrix

### Scenario 1: Normal Flow
| Step | Action | Expected Result |
|------|--------|---|
| 1 | Open 02.1-Content-Discovery.html | 3 videos display |
| 2 | Click "Advanced Excel Techniques" | Navigation to 02.2 |
| 3 | 02.2 loads | Shows Excel video details |
| 4 | Progress shown as "Start watching" | Correct (0% watched) |

### Scenario 2: In-Progress Video
| Step | Action | Expected Result |
|------|--------|---|
| 1 | Set watchProgress: 50 in demo data | - |
| 2 | Open 02.1 | Progress bar shows 50% |
| 3 | Click video | Selection stored |
| 4 | 02.2 loads | Shows "Resume at 14:00" |

### Scenario 3: No Video Selected
| Step | Action | Expected Result |
|------|--------|---|
| 1 | Direct navigation to 02.2 (no selection) | Falls back to demo data |
| 2 | Shows default video details | Correct |

### Scenario 4: Empty Video List
| Step | Action | Expected Result |
|------|--------|---|
| 1 | Remove videos from demo data | - |
| 2 | Open 02.1 | "No assigned videos" message |

## Debugging Commands

In browser console:
```javascript
// View all stored data
PrototypeAPI.getDebugInfo();

// View selected video
PrototypeAPI.getSelectedVideo();

// View all videos
PrototypeAPI.getAssignedVideos();

// Clear and reset data
PrototypeAPI.clearAllData();
// Then refresh page
```

## Performance Notes

- **No server required** - Works over file:// protocol
- **Fast load** - All data in memory (sessionStorage)
- **Low overhead** - Minimal DOM manipulation
- **Smooth navigation** - No page reload, direct href navigation

## Future Enhancements

### Phase 2
- [ ] Add video search/filter
- [ ] Add sorting options
- [ ] Add skill category grouping
- [ ] Add favorites system

### Phase 3
- [ ] Connect to real FastAPI backend
- [ ] Implement actual video player
- [ ] Add watch history tracking
- [ ] Add recommendation engine

### Phase 4
- [ ] Video preview on hover
- [ ] Collaborative recommendations from Rita
- [ ] Progress sync across devices
- [ ] Offline viewing support
