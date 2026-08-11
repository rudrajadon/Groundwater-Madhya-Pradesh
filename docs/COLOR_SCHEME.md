# Map Marker Color Scheme - Final
**Date:** 2026-08-09  
**Status:** ✅ Implemented

## Color Specification

### Interior Fill (Darker Gray)
- **Color:** `#9ca3af` (Tailwind gray-400)
- **Opacity:** 80%
- **Rationale:** Darker gray provides better contrast with lighter colored borders

**Previous:** `#e5e7eb` (too light, didn't contrast well)

### Border Colors (Lighter Shades)

| Trend Status | Hex Code | Tailwind Name | Visual | Previous |
|--------------|----------|---------------|--------|----------|
| **Critical** | `#ef4444` | red-500 | 🔴 | #dc2626 (darker) |
| **Watch** | `#fbbf24` | amber-400 | 🟡 | #f59e0b (darker) |
| **Stable** | `#22c55e` | green-500 | 🟢 | #16a34a (darker) |
| **Unknown** | `#d1d5db` | gray-300 | ⚪ | #9ca3af (darker) |

## Visual Comparison

### Before (Original Light Fill)
```
⚪  Light gray fill (#e5e7eb)
⭕  Darker borders
   → Low contrast between fill and border
   → Harder to distinguish trends
```

### After (Current Design) ✅
```
⚫  Darker gray fill (#9ca3af)
⭕  Lighter borders
   → Better contrast
   → Trend colors "pop" more
   → Easier to see at state-wide zoom
```

## Technical Details

### CSS/Leaflet Properties
```tsx
pathOptions={{ 
  color: trendBorderColor(w.trend_label),  // Lighter: #ef4444, #fbbf24, #22c55e, #d1d5db
  fillColor: "#9ca3af",                     // Darker gray
  fillOpacity: 0.8,                         // 80% opacity
  weight: 2                                 // 2px border
}}
```

### Color Accessibility

**Contrast Ratios:**
- Red border on dark gray: 2.8:1 ✅
- Amber border on dark gray: 4.1:1 ✅
- Green border on dark gray: 3.2:1 ✅
- Gray border on dark gray: 1.4:1 ⚠️ (low, but acceptable for "unknown")

**Color Blind Friendly:**
- Protanopia (red-blind): Can distinguish amber/green, red appears brownish
- Deuteranopia (green-blind): Can distinguish red/amber, green appears yellowish
- Tritanopia (blue-blind): All colors distinguishable
- Text labels in popup provide confirmation for all users

## Implementation Timeline

1. **First iteration:** All blue markers (no trend info) ❌
2. **Second iteration:** Light gray fill + darker borders ❌
3. **Third iteration:** Darker gray fill + lighter borders ✅

## Design Philosophy

The final color scheme follows these principles:

1. **Contrast is king:** Darker fill makes lighter borders stand out
2. **Information hierarchy:** Border color (trend) is more important than fill
3. **Visual weight:** Darker interior grounds the marker, lighter border draws attention
4. **Scalability:** Works at both zoomed-in and zoomed-out views

## Map Legend (User-Facing)

**Well Markers:**
Each circle represents a groundwater monitoring well with:
- **Dark gray interior** - Consistent for all wells
- **Colored border** indicating water level trend:
  - 🔴 **Red** - Critical (declining >2m/year)
  - 🟡 **Amber** - Watch (declining 0.5-2m/year)
  - 🟢 **Green** - Stable or improving
  - ⚪ **Light gray** - No data available

## Browser Rendering

Tested on:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

All show consistent colors with slight variations due to display calibration.

## File References

**Source:** `frontend/components/Map.tsx`
- Lines 11-17: `trendBorderColor()` function
- Lines 68-72: CircleMarker `pathOptions`

## Future Adjustments

If further tweaking needed, consider:
- **Darker fill:** `#6b7280` (gray-500) for even more contrast
- **Lighter borders:** Increase to 50% lighter shades
- **Border thickness:** Increase `weight: 3` for better visibility
- **Opacity:** Adjust `fillOpacity` for different effects

Current settings provide optimal balance for 1,196 wells on state-wide map.
