// colors.ts - COMPLETELY DYNAMIC COLOR SYSTEM
// This file now uses the centralized colorSystem.ts with NO hardcoded task names!

import { 
  getWorkerColor as getWorkerColorFromSystem,
  getTaskColor as getTaskColorFromSystem,
  generateXTaskColors,
  generateYTaskColors
} from './colorSystem';

/**
 * Returns a consistent HSL color string for a given worker (by id or name).
 * Used to color-code cells in all tables so each worker has a unique hue.
 *
 * @param {string} idOrName - The worker's id or name.
 * @param {boolean} darkMode - Whether the UI is in dark mode (affects lightness).
 * @returns {string} HSL color string for use in CSS.
 */
export function getWorkerColor(idOrName: string, darkMode: boolean) {
  return getWorkerColorFromSystem(idOrName, darkMode);
}

/**
 * DYNAMIC X task colors - generated automatically from backend task definitions.
 * No hardcoded task names - colors are generated dynamically!
 */
export function getXTaskColors(taskNames: string[], darkMode: boolean = true): Record<string, string> {
  return generateXTaskColors(taskNames, darkMode);
}

/**
 * DYNAMIC Y task colors - generated automatically from backend task definitions.
 * No hardcoded task names - colors are generated dynamically!
 */
export function getYTaskColors(taskNames: string[], darkMode: boolean = true): Record<string, { light: string, dark: string }> {
  return generateYTaskColors(taskNames, darkMode);
}

/**
 * Returns the color for a given X task name. 
 * Colors are generated dynamically - no hardcoded fallbacks!
 * @param {string} taskName - Any task name from the backend
 * @param {boolean} darkMode - Whether the UI is in dark mode
 * @returns {string} CSS color
 */
export function getXTaskColor(taskName: string, darkMode: boolean = true): string {
  return getTaskColorFromSystem(taskName, darkMode);
}

/**
 * Returns the color for a given Y task name with theme adaptation.
 * Colors are generated dynamically - no hardcoded fallbacks!
 * @param {string} taskName - Any task name from the backend
 * @param {boolean} darkMode - Whether the UI is in dark mode
 * @returns {string} CSS color
 */
export function getYTaskColor(taskName: string, darkMode: boolean = true): string {
  return getTaskColorFromSystem(taskName, darkMode);
}

// ============================================================================
// LEGACY COMPATIBILITY - These will be removed in future versions
// ============================================================================

/**
 * @deprecated Use getXTaskColors() with dynamic task names instead
 * This maintains backward compatibility but should be replaced
 */
export const X_TASK_COLORS: Record<string, string> = {};

/**
 * @deprecated Use getYTaskColors() with dynamic task names instead
 * This maintains backward compatibility but should be replaced
 */
export const Y_TASK_COLORS: Record<string, { light: string, dark: string }> = {};

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/*
 * HOW TO USE THE NEW DYNAMIC COLOR SYSTEM:
 * 
 * 1. For X Tasks (in XTaskPage.tsx):
 *    const xTaskNames = ['שמירות', 'רסר', 'מטבח']; // From backend
 *    const xTaskColors = getXTaskColors(xTaskNames, tableDarkMode);
 *    
 *    // Then use: xTaskColors[taskName] || '#default-color'
 * 
 * 2. For Y Tasks (in YTaskPage.tsx):
 *    const yTaskNames = ['מגש״ק תורן', 'נהג כבל רשת']; // From backend
 *    const yTaskColors = getYTaskColors(yTaskNames, tableDarkMode);
 *    
 *    // Then use: yTaskColors[taskName]?.[tableDarkMode ? 'dark' : 'light']
 * 
 * 3. For Individual Task Colors:
 *    const color = getXTaskColor('שמירות', darkMode);
 *    const yColor = getYTaskColor('מגש״ק תורן', darkMode);
 * 
 * BENEFITS:
 * - No hardcoded task names
 * - Colors automatically generated for any task
 * - Consistent colors across the application
 * - Easy to add/remove/modify tasks
 * - Future-proof design
 */ 