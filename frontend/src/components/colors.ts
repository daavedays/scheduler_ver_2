// colors.ts - Updated to use the new color system
// This file now imports from the centralized colorSystem.ts

import { 
  TASK_COLORS, 
  getWorkerColor as getWorkerColorFromSystem,
  getTaskColor as getTaskColorFromSystem 
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
 * Centralized color map for X tasks (and custom tasks).
 * Now imported from the centralized color system.
 */
export const X_TASK_COLORS: Record<string, string> = {
  'Guarding Duties': TASK_COLORS.x_task_guarding,
  'RASAR': TASK_COLORS.x_task_rasar,
  'Kitchen': TASK_COLORS.x_task_kitchen,
  'Custom': TASK_COLORS.x_task_custom,
};

/**
 * Centralized color map for Y tasks (with light/dark variants).
 */
export const Y_TASK_COLORS: Record<string, { light: string, dark: string }> = {
  'Supervisor':      { light: TASK_COLORS.y_task_supervisor, dark: TASK_COLORS.y_task_supervisor },
  'C&N Driver':      { light: TASK_COLORS.y_task_cn_driver, dark: TASK_COLORS.y_task_cn_driver },
  'C&N Escort':      { light: TASK_COLORS.y_task_cn_escort, dark: TASK_COLORS.y_task_cn_escort },
  'Southern Driver': { light: TASK_COLORS.y_task_southern_driver, dark: TASK_COLORS.y_task_southern_driver },
  'Southern Escort': { light: TASK_COLORS.y_task_southern_escort, dark: TASK_COLORS.y_task_southern_escort },
};

/**
 * Returns the color for a given X task name. Falls back to 'Custom' if not found.
 * @param {string} taskName
 * @param {boolean} darkMode - Whether the UI is in dark mode
 * @returns {string} CSS color
 */
export function getXTaskColor(taskName: string, darkMode: boolean = true): string {
  return getTaskColorFromSystem(taskName, darkMode);
}

/**
 * Returns the color for a given Y task name with theme adaptation.
 * @param {string} taskName
 * @param {boolean} darkMode - Whether the UI is in dark mode
 * @returns {string} CSS color
 */
export function getYTaskColor(taskName: string, darkMode: boolean = true): string {
  const taskColorMap: Record<string, string> = {
    'Supervisor': TASK_COLORS.y_task_supervisor,
    'C&N Driver': TASK_COLORS.y_task_cn_driver,
    'C&N Escort': TASK_COLORS.y_task_cn_escort,
    'Southern Driver': TASK_COLORS.y_task_southern_driver,
    'Southern Escort': TASK_COLORS.y_task_southern_escort,
  };
  
  return taskColorMap[taskName] || TASK_COLORS.x_task_custom;
} 