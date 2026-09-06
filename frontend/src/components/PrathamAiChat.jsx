import React, { useEffect, useRef, useState } from 'react';
import { Bot, LoaderCircle, MessageCircle, Send, Square, Volume2, X } from 'lucide-react';
import { getChatSpeech, sendChatMessage } from '../services/api';

const starterMessage = {
  id: 'welcome',
  role: 'assistant',
  text: "Hi, I’m Pratham AI. Ask me about Pratham’s work, skills, or how to get in touch.",
};

const PrathamAiChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([starterMessage]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [loadingVoiceId, setLoadingVoiceId] = useState(null);
  const [playingVoiceId, setPlayingVoiceId] = useState(null);
  const [voiceErrors, setVoiceErrors] = useState({});
  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const stopPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    setPlayingVoiceId(null);
  };

  useEffect(() => () => stopPlayback(), []);

  const sendMessage = async (event) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || isSending) return;

    const userMessage = { id: `user-${Date.now()}`, role: 'user', text: question };
    setMessages((current) => [
      ...current,
      userMessage,
    ]);
    setInput('');
    setIsSending(true);
    try {
      const response = await sendChatMessage(question);
      setMessages((current) => [...current, { id: `assistant-${Date.now()}`, role: 'assistant', text: response.reply }]);
    } catch (error) {
      setMessages((current) => [...current, {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        text: error.message || 'Pratham AI is temporarily unavailable. Please try again shortly.',
      }]);
    } finally {
      setIsSending(false);
    }
  };

  const playVoice = async (message) => {
    if (playingVoiceId === message.id) {
      stopPlayback();
      return;
    }

    stopPlayback();
    setLoadingVoiceId(message.id);
    setVoiceErrors((current) => ({ ...current, [message.id]: null }));
    try {
      const audioBlob = await getChatSpeech(message.text);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audioUrlRef.current = audioUrl;
      audio.onended = stopPlayback;
      await audio.play();
      setPlayingVoiceId(message.id);
    } catch (error) {
      console.error('[Pratham AI TTS] playback failed', error);
      stopPlayback();
      setVoiceErrors((current) => ({ ...current, [message.id]: 'Voice unavailable right now.' }));
    } finally {
      setLoadingVoiceId(null);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-[60] flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      {isOpen && (
        <section
          className="flex h-[min(34rem,calc(100dvh-7.5rem))] w-[calc(100vw-2rem)] max-w-[25rem] flex-col overflow-hidden rounded-3xl border border-[#d9fb06]/35 bg-[#1a1c1b] shadow-2xl shadow-black/50"
          aria-label="Pratham AI chat"
        >
          <header className="flex items-center justify-between border-b border-[#3f4816] bg-[#20231d] px-5 py-4">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#d9fb06] text-[#1a1c1b]">
                <Bot size={20} aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-sm font-bold tracking-wide text-[#dfddd6]">Pratham AI</h2>
                <p className="text-xs text-[#9ca091]">Portfolio assistant</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded-full p-2 text-[#888680] transition-colors hover:bg-[#302f2c] hover:text-[#d9fb06]"
              aria-label="Close Pratham AI chat"
            >
              <X size={19} aria-hidden="true" />
            </button>
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-5">
            {messages.map((message) => (
              <div key={message.id} className={`max-w-[88%] ${message.role === 'user' ? 'ml-auto' : ''}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  message.role === 'user'
                    ? 'rounded-br-md bg-[#d9fb06] text-[#1a1c1b]'
                    : 'rounded-bl-md border border-[#3f4816] bg-[#242724] text-[#dfddd6]'
                  }`}
                >
                  {message.text}
                </div>
                {message.role === 'assistant' && (
                  <>
                    <button
                      type="button"
                      onClick={() => playVoice(message)}
                      disabled={loadingVoiceId === message.id}
                      className="mt-2 inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium text-[#d9fb06] transition-colors hover:bg-[#3f4816]/50 disabled:cursor-wait disabled:opacity-70"
                    >
                      {loadingVoiceId === message.id ? <LoaderCircle size={13} className="animate-spin" /> : playingVoiceId === message.id ? <Square size={12} fill="currentColor" /> : <Volume2 size={14} />}
                      {loadingVoiceId === message.id ? 'Generating voice…' : playingVoiceId === message.id ? 'Stop' : 'Listen'}
                    </button>
                    {voiceErrors[message.id] && <p className="mt-1 text-xs text-[#888680]">{voiceErrors[message.id]}</p>}
                  </>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={sendMessage} className="flex gap-2 border-t border-[#3f4816] bg-[#20231d] p-3">
            <label className="sr-only" htmlFor="pratham-ai-message">Ask Pratham AI a question</label>
            <input
              ref={inputRef}
              id="pratham-ai-message"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about Pratham…"
              disabled={isSending}
              className="min-w-0 flex-1 rounded-full border border-[#3f4816] bg-[#1a1c1b] px-4 py-2.5 text-sm text-[#dfddd6] outline-none placeholder:text-[#888680] focus:border-[#d9fb06]"
            />
            <button
              type="submit"
              disabled={isSending}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#d9fb06] text-[#1a1c1b] transition-transform hover:scale-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d9fb06]"
              aria-label="Send message"
            >
              <Send size={17} aria-hidden="true" />
            </button>
          </form>
        </section>
      )}

      <div className="group relative">
        <span className="pointer-events-none absolute bottom-1/2 right-[calc(100%+0.75rem)] w-max translate-y-1/2 rounded-md border border-[#3f4816] bg-[#20231d] px-3 py-2 text-xs font-medium text-[#dfddd6] opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
          Chat with Pratham AI
        </span>
        <button
          type="button"
          onClick={() => setIsOpen((open) => !open)}
          className="flex h-14 w-14 items-center justify-center rounded-full border border-[#d9fb06]/80 bg-[#1a1c1b] text-[#d9fb06] shadow-lg shadow-black/40 transition duration-200 hover:-translate-y-1 hover:scale-105 hover:bg-[#d9fb06] hover:text-[#1a1c1b] hover:shadow-[#d9fb06]/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d9fb06]"
          aria-label={isOpen ? 'Close Pratham AI chat' : 'Open Pratham AI chat'}
          aria-expanded={isOpen}
          aria-controls="pratham-ai-message"
        >
          {isOpen ? <X size={23} aria-hidden="true" /> : <MessageCircle size={23} aria-hidden="true" />}
        </button>
      </div>
    </div>
  );
};

export default PrathamAiChat;
