import axios from 'axios';

export const CHAT_TIMEOUT_MS = 60000;
export const TTS_TIMEOUT_MS = 180000;
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: CHAT_TIMEOUT_MS,
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
export const sendChatMessage = (message, history = []) => request(api.post('/chat', { message, ...(history.length ? { history } : {}) }, { timeout: CHAT_TIMEOUT_MS }));
export const getChatSpeech = async (text) => {
  try {
    const response = await api.post('/chat/tts', { text }, {
      responseType: 'blob',
      timeout: TTS_TIMEOUT_MS,
    });
    console.info('[Pratham AI TTS] response received', {
      status: response.status,
      contentType: response.headers?.['content-type'],
    });
    return response.data;
  } catch (error) {
    console.error('[Pratham AI TTS] request failed', {
      status: error.response?.status,
      contentType: error.response?.headers?.['content-type'],
      message: error.message,
    });
    const message = error.response?.data?.detail || error.message || 'Voice unavailable right now.';
    throw new Error(message);
  }
};
export const sendCandidateEmail = (candidateId) => request(api.post(`/candidates/${candidateId}/send-email`));
export const getApproval = (token) => request(api.get(`/approval/${encodeURIComponent(token)}`));
export const applyApproval = (token, action, projectName) => request(api.post(`/approval/${encodeURIComponent(token)}`, { action, ...(projectName ? { project_name: projectName } : {}) }));

export default api;
