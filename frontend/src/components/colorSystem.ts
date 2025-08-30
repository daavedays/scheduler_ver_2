/**
 * DYNAMIC COLOR SYSTEM - Centralized Color Management
 * ==================================================
 * 
 * This file contains ALL colors used throughout the application.
 * Change colors here to instantly update the entire UI.
 * 
 * IMPORTANT: This system is now completely dynamic - no hardcoded task names!
 * Colors are generated automatically based on task names from the backend.
 * 
 * COLOR NAMING CONVENTION:
 * - Primary colors: primary_*
 * - Secondary colors: secondary_*
 * - Background colors: bg_*
 * - Text colors: text_*
 * - Interactive colors: interactive_*
 * - Status colors: status_*
 * - Table colors: table_*
 * - Dynamic task colors: generated automatically
 * 
 * 🎨 QUICK REFERENCE - MOST COMMONLY CHANGED COLORS:
 * ==================================================
 * 1. PRIMARY_COLORS.primary_main (#3a86ff) - Main blue for buttons, links
 * 2. PRIMARY_COLORS.secondary_main (#ff006e) - Secondary pink for highlights  
 * 3. TABLE_COLORS.table_header_bg (#1e3a5c) - Table header background
 * 4. BACKGROUND_COLORS.bg_main (#0a1929) - Main app background
 * 5. TEXT_COLORS.text_primary (#f8f9fa) - Main text color
 * 
 * 💡 MODERN COLOR SUGGESTIONS:
 * ============================
 * - Replace indigo (#4f46e5) with modern purple (#7c3aed) for elegance
 * - Replace blue (#3a86ff) with emerald (#059669) for freshness
 * - Replace pink (#ff006e) with cyan (#0891b2) for professionalism
 * - Use warm orange (#ea580c) for energy and warmth
 * - Try sophisticated brown (#7c2d12) for earthy tones
 */

// ============================================================================
// PRIMARY COLOR PALETTE
// ============================================================================

export const PRIMARY_COLORS = {
  // Main brand color - used for primary buttons, links, and accents
  primary_main: '#6366f1', // Modern indigo - primary buttons, main actions
  
  // Secondary brand color - used for secondary actions and highlights
  secondary_main: '#ec4899', // Modern pink - secondary buttons, highlights
  
  // Accent colors for special elements
  accent_teal: '#14b8a6', // Modern teal - success states, positive actions
  accent_orange: '#f97316', // Modern orange - warnings, attention-grabbing
  accent_purple: '#8b5cf6', // Modern purple - premium features, special elements
};

// ============================================================================
// BACKGROUND COLORS
// ============================================================================

export const BACKGROUND_COLORS = {
  // Main application background
  bg_main: '#0f172a', // Modern slate - main app background
  
  // Secondary backgrounds for cards, panels, etc.
  bg_secondary: 'rgba(30, 41, 59, 0.95)', // Modern slate - card backgrounds
  
  // Light mode backgrounds
  bg_light_main: '#f8fafc', // Modern slate - light mode main background
  bg_light_secondary: '#ffffff', // Pure white - light mode card backgrounds
  
  // Transparent backgrounds for overlays
  bg_transparent: 'rgba(255, 255, 255, 0.1)', // Subtle overlay
  bg_glass: 'rgba(255, 255, 255, 0.05)', // Glass effect
};

// ============================================================================
// TEXT COLORS
// ============================================================================

export const TEXT_COLORS = {
  // Primary text colors
  text_primary: '#f8f9fa', // Almost white - main text in dark mode
  text_secondary: '#adb5bd', // Light gray - secondary text in dark mode
  
  // Light mode text colors
  text_light_primary: '#212529', // Dark gray - main text in light mode
  text_light_secondary: '#6c757d', // Medium gray - secondary text in light mode
  
  // Interactive text colors
  text_link: '#3a86ff', // Blue - clickable links
  text_link_hover: '#2563eb', // Darker blue - links on hover
};

// ============================================================================
// INTERACTIVE ELEMENT COLORS
// ============================================================================

export const INTERACTIVE_COLORS = {
  // Button colors
  button_primary: '#3a86ff', // Blue - primary buttons
  button_primary_hover: '#2563eb', // Darker blue - primary buttons on hover
  button_secondary: '#ff006e', // Pink - secondary buttons
  button_secondary_hover: '#dc2626', // Darker pink - secondary buttons on hover
  
  // Form element colors
  input_border: '#6b7280', // Gray - input field borders
  input_border_focus: '#3a86ff', // Blue - input field borders when focused
  input_bg: 'rgba(255, 255, 255, 0.05)', // Subtle - input field backgrounds
  
  // Hover and focus states
  hover_bg: 'rgba(255, 255, 255, 0.1)', // Subtle white - hover backgrounds
  focus_ring: 'rgba(58, 134, 255, 0.3)', // Blue with transparency - focus rings
};

// ============================================================================
// TABLE COLORS
// ============================================================================

export const TABLE_COLORS = {
  // Table backgrounds
  table_header_bg: '#1e293b', // Modern slate - table header background
  table_header_bg_light: '#e2e8f0', // Modern slate - light mode table header
  
  // Table borders
  table_border: '#475569', // Modern slate - table cell borders
  table_border_light: '#cbd5e1', // Modern slate - light mode table borders
  
  // Table row backgrounds
  table_row_even: 'rgba(255, 255, 255, 0.02)', // Very subtle - even rows
  table_row_odd: 'rgba(255, 255, 255, 0.05)', // Subtle - odd rows
  table_row_even_light: '#f8fafc', // Modern slate - light mode even rows
  table_row_odd_light: '#ffffff', // White - light mode odd rows
  
  // Sticky column backgrounds (for worker names and dates)
  table_sticky_bg: '#334155', // Modern slate - sticky column background
  table_sticky_bg_light: '#f1f5f9', // Modern slate - light mode sticky columns
};

// ============================================================================
// DYNAMIC TASK COLORS - NO HARDCODED TASK NAMES!
// ============================================================================

// Color palettes for automatic task color generation
const TASK_COLOR_PALETTES = {
  // Modern blues and purples
  blue_purple: ['#3b82f6', '#8b5cf6', '#6366f1', '#7c3aed', '#9333ea', '#7c2d12'],
  // Modern greens and teals
  green_teal: ['#10b981', '#059669', '#0891b2', '#06b6d4', '#14b8a6', '#16a34a'],
  // Modern oranges and ambers
  orange_amber: ['#f59e0b', '#ea580c', '#f97316', '#fb923c', '#fbbf24', '#d97706'],
  // Modern reds and pinks
  red_pink: ['#ef4444', '#dc2626', '#ec4899', '#f43f5e', '#f97316', '#be185d'],
  // Modern grays and slates
  gray_slate: ['#64748b', '#475569', '#334155', '#1e293b', '#0f172a', '#475569']
};

// ============================================================================
// STATUS COLORS
// ============================================================================

export const STATUS_COLORS = {
  // Success states
  success_main: '#4caf50', // Green - success messages, completed tasks
  success_light: '#81c784', // Light green - success backgrounds
  
  // Warning states
  warning_main: '#ffb74d', // Orange - warnings, attention needed
  warning_light: '#ffcc02', // Light orange - warning backgrounds
  
  // Error states
  error_main: '#ff5252', // Red - errors, failed actions
  error_light: '#ef5350', // Light red - error backgrounds
  
  // Info states
  info_main: '#64b5f6', // Blue - informational messages
  info_light: '#90caf9', // Light blue - info backgrounds
};

// ============================================================================
// NAVIGATION COLORS
// ============================================================================

export const NAVIGATION_COLORS = {
  // Header and navigation
  nav_bg: 'linear-gradient(90deg, #0a1929 0%, #1e3a5c 100%)', // Gradient - navigation background
  nav_text: '#ffffff', // White - navigation text
  nav_text_hover: '#e0e6ed', // Light gray - navigation text on hover
  
  // Sidebar colors
  sidebar_bg: '#1e293b', // Dark blue-gray - sidebar background
  sidebar_bg_light: '#f1f5f9', // Light gray - light mode sidebar
  sidebar_text: '#e2e8f0', // Light gray - sidebar text
  sidebar_text_light: '#475569', // Dark gray - light mode sidebar text
};

// ============================================================================
// CARD AND PANEL COLORS
// ============================================================================

export const CARD_COLORS = {
  // Card backgrounds
  card_bg: 'rgba(16, 32, 54, 0.85)', // Semi-transparent navy - card backgrounds
  card_bg_light: '#ffffff', // White - light mode card backgrounds
  
  // Card borders and shadows
  card_border: 'rgba(255, 255, 255, 0.1)', // Subtle white - card borders
  card_border_light: '#e5e7eb', // Light gray - light mode card borders
  card_shadow: '0 8px 16px rgba(0,0,0,0.1)', // Subtle shadow - card shadows
  card_shadow_light: '0 2px 8px rgba(0,0,0,0.05)', // Lighter shadow - light mode
};

// ============================================================================
// MODAL AND POPUP COLORS
// ============================================================================

export const MODAL_COLORS = {
  // Modal backgrounds
  modal_bg: '#ffffff', // White - modal background (high contrast)
  modal_bg_dark: '#1e293b', // Dark blue-gray - dark mode modal background
  
  // Modal borders and shadows
  modal_border: '#e5e7eb', // Light gray - modal borders
  modal_border_dark: '#475569', // Dark gray - dark mode modal borders
  modal_shadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)', // Strong shadow - modal shadows
};

// ============================================================================
// DYNAMIC COLOR GENERATION FUNCTIONS
// ============================================================================

/**
 * Generate a consistent hash from a string
 * @param str - String to hash
 * @returns Numeric hash value
 */
function generateHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

/**
 * Get a color from a palette based on hash
 * @param hash - Hash value
 * @param palette - Array of colors to choose from
 * @returns Color string
 */
function getColorFromPalette(hash: number, palette: string[]): string {
  return palette[hash % palette.length];
}

/**
 * Get task color with theme adaptation - COMPLETELY DYNAMIC!
 * @param taskName - Name of the task (any string, no hardcoded names!)
 * @param isDarkMode - Whether the app is in dark mode
 * @returns The appropriate color for the task
 */
export function getTaskColor(taskName: string, isDarkMode: boolean): string {
  const hash = generateHash(taskName);
  
  // Select palette based on hash
  const paletteNames = Object.keys(TASK_COLOR_PALETTES);
  const paletteName = paletteNames[hash % paletteNames.length];
  const palette = TASK_COLOR_PALETTES[paletteName as keyof typeof TASK_COLOR_PALETTES];
  
  // Get color from palette
  return getColorFromPalette(hash, palette);
}

/**
 * Get worker color with theme adaptation
 * @param workerId - Worker identifier
 * @param isDarkMode - Whether the app is in dark mode
 * @returns A consistent color for the worker
 */
export function getWorkerColor(workerId: string, isDarkMode: boolean): string {
  const hash = generateHash(workerId);
  const hue = hash % 360;
  const saturation = 45;
  const lightness = isDarkMode ? 35 : 70;
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Generate a complete color map for X tasks dynamically
 * @param taskNames - Array of X task names from backend
 * @param isDarkMode - Whether the app is in dark mode
 * @returns Object mapping task names to colors
 */
export function generateXTaskColors(taskNames: string[], isDarkMode: boolean): Record<string, string> {
  const colorMap: Record<string, string> = {};
  
  taskNames.forEach(taskName => {
    colorMap[taskName] = getTaskColor(taskName, isDarkMode);
  });
  
  return colorMap;
}

/**
 * Generate a complete color map for Y tasks dynamically
 * @param taskNames - Array of Y task names from backend
 * @param isDarkMode - Whether the app is in dark mode
 * @returns Object mapping task names to colors with light/dark variants
 */
export function generateYTaskColors(taskNames: string[], isDarkMode: boolean): Record<string, { light: string, dark: string }> {
  const colorMap: Record<string, { light: string, dark: string }> = {};
  
  taskNames.forEach(taskName => {
    const baseColor = getTaskColor(taskName, isDarkMode);
    // For Y tasks, we use the same color for both light and dark modes
    // but you could adjust lightness/saturation if needed
    colorMap[taskName] = {
      light: baseColor,
      dark: baseColor
    };
  });
  
  return colorMap;
}

/**
 * Get the appropriate color based on current theme
 * @param darkColor - Color to use in dark mode
 * @param lightColor - Color to use in light mode
 * @param isDarkMode - Whether the app is in dark mode
 * @returns The appropriate color for the current theme
 */
export function getThemeColor(darkColor: string, lightColor: string, isDarkMode: boolean): string {
  return isDarkMode ? darkColor : lightColor;
}

// ============================================================================
// EXPORT ALL COLORS FOR EASY ACCESS
// ============================================================================

export const ALL_COLORS = {
  ...PRIMARY_COLORS,
  ...BACKGROUND_COLORS,
  ...TEXT_COLORS,
  ...INTERACTIVE_COLORS,
  ...TABLE_COLORS,
  ...STATUS_COLORS,
  ...NAVIGATION_COLORS,
  ...CARD_COLORS,
  ...MODAL_COLORS,
};

// ============================================================================
// QUICK REFERENCE - MOST COMMONLY CHANGED COLORS
// ============================================================================

/**
 * QUICK REFERENCE - Change these colors for instant visual impact:
 * 
 * 1. PRIMARY_COLORS.primary_main - Main blue color (buttons, links)
 * 2. PRIMARY_COLORS.secondary_main - Secondary pink color (highlights)
 * 3. TABLE_COLORS.table_header_bg - Table header background
 * 4. BACKGROUND_COLORS.bg_main - Main app background
 * 5. TEXT_COLORS.text_primary - Main text color
 * 
 * To change a color:
 * 1. Find the color in this file
 * 2. Change the hex value
 * 3. Save the file
 * 4. The change will apply immediately across the entire app
 * 
 * IMPORTANT: Task colors are now generated automatically - no need to hardcode!
 */
