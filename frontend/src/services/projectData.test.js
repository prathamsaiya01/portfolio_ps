jest.mock('./api', () => ({ getPublishedProjects: jest.fn() }));

import { getPublishedProjects } from './api';
import { localProjects, loadPortfolioProjects } from './projectData';

const expectedImages = {
  NOVA: '/images/nova.jpeg',
  AITeacherBot: '/images/aiteacher.jpeg',
  Notely: '/images/notely.jpeg',
  FitFreak: '/images/fitfreak-landing-page.png',
  CareerMitra: '/images/careermitra.jpeg',
  'ApnaAdda – Indian PocketParty': '/images/apna-adda.jpeg',
  'Reaction Time Game': '/images/rtg-iot.jpeg',
  StockHub: '/images/stockhub.jpeg',
  Codeopoly: '/images/codopoly.jpeg',
  QuizMaster: '/images/quiz.jpeg',
  RakhtSetu: '/images/rakhtsetu.jpeg',
};

describe('portfolio project data', () => {
  test('contains the final local project list with its specified snapshot images', () => {
    expect(localProjects).toHaveLength(11);
    expect(Object.fromEntries(localProjects.map((project) => [project.title, project.image]))).toEqual(expectedImages);
    expect(localProjects.map((project) => project.status)).not.toContain('COMING SOON');
  });

  test('does not reintroduce removed projects from published data', async () => {
    getPublishedProjects.mockResolvedValue([
      { github_repo_id: 'loanwise', title: 'LoanWise', description: 'Removed card' },
      { github_repo_id: 'filmyradar', title: 'FilmyRadar', description: 'Removed card' },
    ]);

    const projects = await loadPortfolioProjects();

    expect(projects.map((project) => project.title)).not.toEqual(expect.arrayContaining(['LoanWise', 'FilmyRadar']));
  });
});
