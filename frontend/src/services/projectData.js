import { projects as mockProjects } from '../data/mock';
import { manualProjects } from '../data/mock';
import { getPublishedProjects } from './api';

const fallbackImage = mockProjects[0]?.image || '';
const isExcludedProject = (project) => {
  const title = project?.title?.trim().toLowerCase() || '';
  return title.includes('filmyradar') || title.includes('loanwise');
};
export const localProjects = [...manualProjects, ...mockProjects].filter((project) => !isExcludedProject(project));

export const normalizePublishedProject = (project, index = 0) => {
  if (!project || typeof project !== 'object' || !project.title || !project.description) return null;
  const stack = Array.isArray(project.technologies) && project.technologies.length
    ? project.technologies
    : Array.isArray(project.languages) ? project.languages : [];
  return {
    id: project.github_repo_id || `published-${index}`,
    title: project.title,
    description: project.description,
    longDescription: project.description,
    stack,
    image: project.image_url || fallbackImage,
    demo: project.live_url || '#',
    repo: project.github_url || '#',
    status: project.status || 'PUBLISHED',
    featured: Boolean(project.featured),
  };
};

export const loadPortfolioProjects = async () => {
  try {
    const published = await getPublishedProjects();
    if (!Array.isArray(published)) return localProjects;
    const normalized = published.map(normalizePublishedProject).filter((project) => project && !isExcludedProject(project));
    if (!normalized.length) return localProjects;

    // Legacy projects remain visible until an explicit, safe migration supplies their database identities.
    const publishedTitles = new Set(normalized.map((project) => project.title.toLowerCase()));
    const legacyProjects = localProjects.filter((project) => !publishedTitles.has(project.title.toLowerCase()));
    return [...legacyProjects, ...normalized];
  } catch {
    return localProjects;
  }
};

export { mockProjects };
