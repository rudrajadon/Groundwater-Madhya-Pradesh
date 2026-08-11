# Frontend Display Fixes
**Date:** 2026-08-09  
**Issue:** Map showing `"Block — "` instead of trend labels

## Problems Fixed

### 1. Dash Placeholder Instead of Trend Label

**Issue:** Frontend was displaying:
```
SIND-040-PZ
Indore —
```

The `—` was a placeholder for missing data, but the API was actually returning `trend_label: "Stable"`.

**Root Cause:** Frontend code at `frontend/components/Map.tsx` line 74:
```tsx
{w.block} — {w.aquifer_zone}
```

This was showing the `aquifer_zone` field (which is often null) instead of the `trend_label`.

**Fix:**
```tsx
{w.block} - {w.trend_label || 'Unknown'}
```

Now displays:
```
SIND-040-PZ
Indore - Stable

PANNA092A-OW
Shahnagar - Unknown

BPL033A-OW
Fanda - Critical
```

### 2. Colored Map Markers by Trend

**Issue:** User requested to NOT show colored spots on map based on trend status.

**Original Code:**
```tsx
pathOptions={{ 
  color: trendColor(w.trend_label), 
  fillColor: trendColor(w.trend_label), 
  fillOpacity: 0.8 
}}
```

This made wells appear as:
- 🔴 Red for Critical
- 🟡 Amber for Watch
- 🟢 Green for Stable
- ⚪ Gray for Unknown

**Fix:**
```tsx
pathOptions={{ 
  color: "#3b82f6",      // Blue
  fillColor: "#3b82f6",  // Blue
  fillOpacity: 0.6 
}}
```

Now all wells show as **uniform blue markers** 🔵 regardless of trend status.

### 3. Map Center and Zoom

**Before:**
```tsx
const INDORE_CENTER: [number, number] = [22.72, 75.86];
<MapContainer center={INDORE_CENTER} zoom={10} ... />
```

This centered on Indore district only, making it hard to see wells in other districts.

**After:**
```tsx
const MP_CENTER: [number, number] = [23.47, 77.95];
<MapContainer center={MP_CENTER} zoom={7} ... />
```

Now centers on entire Madhya Pradesh with appropriate zoom level to show all 1,196 wells across 18 districts.

### 4. Removed Unused Code

Cleaned up the `trendColor()` function which is no longer needed after removing colored markers:

```tsx
// REMOVED:
function trendColor(label?: string | null): string {
  switch (label) {
    case "Critical": return "#dc2626";
    case "Watch": return "#f59e0b";
    case "Stable": return "#16a34a";
    default: return "#6b7280";
  }
}
```

## Files Modified

1. **`frontend/components/Map.tsx`**
   - Changed popup text from `{w.block} — {w.aquifer_zone}` to `{w.block} - {w.trend_label || 'Unknown'}`
   - Changed marker color from trend-based to uniform blue
   - Updated map center from Indore to MP-wide
   - Updated zoom from 10 (city level) to 7 (state level)
   - Removed unused `trendColor()` function

## Rebuild Required

Since the frontend runs as a production build in Docker, changes required a full rebuild:

```bash
cd /Users/rudrajadon/Downloads/groundwater-app
docker compose -f infra/docker-compose.yml build frontend
docker compose -f infra/docker-compose.yml up -d frontend
```

**Note:** The frontend does NOT have hot-reload in production mode. Any future changes to frontend code require rebuilding the Docker image.

## User Experience Improvements

### Before Fix
- ❌ Popup shows `"Indore —"` with trailing dash
- ❌ Can't see trend status without clicking
- ❌ Map centered on Indore only
- ❌ Wells in other districts off-screen
- ❌ Confusing colored markers

### After Fix
- ✅ Popup shows `"Indore - Stable"` with actual trend
- ✅ Trend visible in popup on click
- ✅ Map shows entire Madhya Pradesh
- ✅ All 1,196 wells visible at once
- ✅ Uniform blue markers (clear and simple)

## API Data Used

The frontend now correctly displays data from the `/api/v1/wells` endpoint:

```json
{
  "well_id": "SIND-040-PZ",
  "lat": 22.633333,
  "lon": 75.906944,
  "block": "Indore",
  "aquifer_zone": null,
  "trend_label": "Stable"
}
```

**Popup Display:**
```
SIND-040-PZ
Indore - Stable
```

## Alternative Design Considerations

### Option A: Show Trend in Marker (Not Implemented)
Could add trend as a letter inside the circle marker:
- C for Critical
- W for Watch
- S for Stable
- ? for Unknown

**Pros:** Visible without clicking  
**Cons:** Cluttered, hard to read at state-wide zoom

### Option B: Colored Markers (User Rejected)
Original design with color-coded markers based on trend.

**Pros:** Immediate visual indication of problem areas  
**Cons:** User requested removal, too "busy" visually

### Option C: Current Design (Implemented) ✅
Uniform blue markers with trend shown in popup.

**Pros:** Clean, simple, all wells look the same  
**Cons:** Need to click each well to see trend

## Future Enhancement Ideas

1. **Filter Controls:** Add buttons to filter by trend (show only Critical, etc.)
2. **Legend:** Add map legend explaining marker colors if restored
3. **Clustering:** Group nearby wells at high zoom levels for performance
4. **Search:** Add well ID search to quickly locate specific wells
5. **Trend in Tooltip:** Show trend on hover (tooltip) instead of just in popup

## Testing Checklist

✅ Well popup shows `block - trend_label` format  
✅ All markers are uniform blue color  
✅ Map centers on MP state (not just Indore)  
✅ All 1,196 wells visible when zoomed out  
✅ Wells from all districts (Sagar, Bhopal, Jabalpur, etc.) visible  
✅ Clicking well shows popup with trend  
✅ Unknown trend shows as "Unknown" not null

## Verification URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/wells
- **Backend Health:** http://localhost:8000/health

## Performance Notes

- Build time: ~2-3 minutes for frontend rebuild
- Map loads all 1,196 wells without performance issues
- Leaflet handles rendering efficiently with CircleMarkers
- No lag or slowdown observed with full dataset

## Deployment Notes

For production deployment:
1. Rebuild frontend image with latest code
2. Ensure `NEXT_PUBLIC_API_BASE` env var points to production backend
3. Consider CDN for static assets
4. Enable gzip compression for faster load times
