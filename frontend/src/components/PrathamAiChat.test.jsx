import { act } from 'react';
import { createRoot } from 'react-dom/client';

jest.mock('../services/api', () => ({
  getChatSpeech: jest.fn(),
  sendChatMessage: jest.fn(),
}));

import PrathamAiChat from './PrathamAiChat';
import { getChatSpeech, sendChatMessage } from '../services/api';

const mockGetChatSpeech = getChatSpeech;
const mockSendChatMessage = sendChatMessage;

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));

describe('Pratham AI voice playback', () => {
  let container;
  let root;
  let audio;

  beforeEach(() => {
    global.IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    audio = { pause: jest.fn(), play: jest.fn().mockResolvedValue(), currentTime: 0, onended: null };
    global.Audio = jest.fn(() => audio);
    global.URL.createObjectURL = jest.fn(() => 'blob:pratham-tts');
    global.URL.revokeObjectURL = jest.fn();
    mockGetChatSpeech.mockReset();
    mockSendChatMessage.mockReset();
    act(() => {
      root.render(<PrathamAiChat />);
    });
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  const openChat = () => {
    act(() => {
      container.querySelector('button[aria-label="Open Pratham AI chat"]').click();
    });
  };

  test('requests a Blob, creates an Audio object, and plays returned TTS audio', async () => {
    mockGetChatSpeech.mockResolvedValue(new Blob(['RIFF'], { type: 'audio/wav' }));
    openChat();

    await act(async () => {
      [...container.querySelectorAll('button')].find((button) => button.textContent.includes('Listen')).click();
      await flushPromises();
    });

    expect(mockGetChatSpeech).toHaveBeenCalledWith(expect.stringContaining('Pratham AI'));
    expect(URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    expect(Audio).toHaveBeenCalledWith('blob:pratham-tts');
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(container.textContent).toContain('Stop');
  });

  test('clears the generating state and shows the existing fallback when TTS fails', async () => {
    mockGetChatSpeech.mockRejectedValue(new Error('network failed'));
    openChat();

    await act(async () => {
      [...container.querySelectorAll('button')].find((button) => button.textContent.includes('Listen')).click();
      await flushPromises();
    });

    expect(container.textContent).toContain('Voice unavailable right now.');
    expect(container.textContent).toContain('Listen');
  });
});
