import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8002/api',
  timeout: 10000,
});

const request = async (promise) => {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    const message = error.response?.data?.detail || error.message || 'The backend is unavailable.';
    throw new Error(message);
  }
};

export const getProjects = () => request(api.get('/projects'));
export const getProjectAnalysis = (repoId) => request(api.get(`/projects/${repoId}/analysis`));
export const getCandidates = (status) => request(api.get('/candidates', { params: status ? { status } : {} }));
export const getCandidate = (candidateId) => request(api.get(`/candidates/${candidateId}`));
export const syncGitHub = () => request(api.post('/github/sync', undefined, { timeout: 120000 }));
export const evaluateProject = (repoId) => request(api.post(`/projects/${repoId}/evaluate`));
export const getPublishedProjects = () => request(api.get('/portfolio/projects'));
export const getPortfolioRanking = () => request(api.get('/portfolio/ranking'));
export const getPortfolioHealth = () => request(api.get('/portfolio/health'));
export const sendCandidateEmail = (candidateId) => request(api.post(`/candidates/${candidateId}/send-email`));
export const getApproval = (token) => request(api.get(`/approval/${encodeURIComponent(token)}`));
export const applyApproval = (token, action, projectName) => request(api.post(`/approval/${encodeURIComponent(token)}`, { action, ...(projectName ? { project_name: projectName } : {}) }));

export default api;
