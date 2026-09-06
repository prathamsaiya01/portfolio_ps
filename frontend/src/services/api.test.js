jest.mock('axios', () => ({
  create: jest.fn(() => ({ get: jest.fn(), post: jest.fn() })),
}));

import { API_BASE_URL, CHAT_TIMEOUT_MS, TTS_TIMEOUT_MS, getChatSpeech, sendChatMessage } from './api';

const mockPost = require('axios').create.mock.results[0].value.post;

describe('chat API request timeouts', () => {
  beforeEach(() => {
    mockPost.mockReset();
  });

  test('/api/chat uses the normal chat timeout', async () => {
    mockPost.mockResolvedValue({ data: { reply: 'Hello' } });

    await sendChatMessage('Hello');

    expect(CHAT_TIMEOUT_MS).toBe(60000);
    expect(mockPost).toHaveBeenCalledWith('/chat', { message: 'Hello' }, { timeout: CHAT_TIMEOUT_MS });
  });

  test('the API client points to the configured local backend URL', () => {
    expect(API_BASE_URL).toBe('http://localhost:8002/api');
  });

  test('/api/chat/tts uses the longer voice timeout', async () => {
    mockPost.mockResolvedValue({ data: new Blob(['wav']) });

    await getChatSpeech('Hello');

    expect(TTS_TIMEOUT_MS).toBe(180000);
    expect(mockPost).toHaveBeenCalledWith('/chat/tts', { text: 'Hello' }, {
      responseType: 'blob',
      timeout: TTS_TIMEOUT_MS,
    });
  });

  test('TTS failures reject so the chat component can reset its loading state', async () => {
    mockPost.mockRejectedValue(new Error('timeout of 180000ms exceeded'));

    await expect(getChatSpeech('Hello')).rejects.toThrow('timeout of 180000ms exceeded');
  });
});
