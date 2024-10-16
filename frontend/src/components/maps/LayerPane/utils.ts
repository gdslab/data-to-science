import { Project } from '../../pages/projects/ProjectList';

/**
 * Takes a date in YYYY-mm-dd format and returns it in Day, Month Date, Year format.
 * For example: 2024-03-13 to Wednesday, Mar 13, 2024
 * @param datestring Date string in YYYY-mm-dd format.
 * @returns Date string in Day, Month Date, Year format.
 */
function formatDate(datestring) {
  return new Date(datestring).toLocaleDateString('en-us', {
    timeZone: 'UTC',
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Checks local storage for previously stored projects.
 * @returns Array of projects retrieved from local storage.
 */
function getLocalStorageProjects(): Project[] | null {
  if ('projects' in localStorage) {
    const lsProjectsString = localStorage.getItem('projects');
    if (lsProjectsString) {
      const lsProjects: Project[] = JSON.parse(lsProjectsString);
      if (lsProjects && lsProjects.length > 0) {
        return lsProjects;
      }
    }
  }

  return null;
}

export { formatDate, getLocalStorageProjects };
