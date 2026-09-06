import React, { useEffect, useState } from 'react';
import { Github, Linkedin } from 'lucide-react';
import { Button } from './ui/button';
import { personalInfo } from '../data/mock';

const Hero = () => {
  const skills = [
    'Computer Engineering Student',
    'React & JavaScript Developer',
    'Technical Head – Spectrum 4.0',
    'Event Tech & UI/UX Enthusiast',
  ];
  const [currentSkill, setCurrentSkill] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSkill((prev) => (prev + 1) % skills.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const scrollToSection = (sectionId) => {   // 👈 no : string here
    const element = document.getElementById(sectionId);
    if (element) {
      const offset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
    }
  };

  return (
    <section id="home" className="min-h-screen bg-[#1a1c1b] flex items-center relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 left-10 w-64 h-64 bg-[#d9fb06] rounded-full blur-[120px]"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#3f4816] rounded-full blur-[150px]"></div>
      </div>

      <div className="max-w-[87.5rem] mx-auto px-8 py-20 relative z-10 w-full">
        <div className="max-w-4xl">
          {/* Greeting */}
          <div className="mb-6 animate-fadeIn">
            <span className="text-[#888680] text-lg font-medium uppercase tracking-wider">
              Hello, I&apos;m
            </span>
          </div>

          {/* Name */}
          <h1 className="font-black text-[clamp(3rem,8vw,7rem)] leading-[0.9] text-[#d9fb06] mb-6 uppercase animate-slideUp">
            {personalInfo.name}
          </h1>

          {/* Rotating title */}
          <div className="mb-8 h-16 flex items-center animate-slideUp" style={{ animationDelay: '0.2s' }}>
            <h2 className="text-[#dfddd6] text-2xl md:text-3xl font-semibold">
              <span className="transition-all duration-500">{skills[currentSkill]}</span>
            </h2>
          </div>

          {/* Tagline */}
          <p
            className="text-[#888680] text-lg md:text-xl max-w-2xl mb-12 leading-relaxed animate-slideUp"
            style={{ animationDelay: '0.4s' }}
          >
            {personalInfo.tagline}
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap gap-4 mb-12 animate-slideUp" style={{ animationDelay: '0.6s' }}>
            <Button
              onClick={() => scrollToSection('projects')}
              className="bg-[#d9fb06] text-[#1a1c1b] hover:bg-[#d9fb06]/90 font-semibold text-base px-8 py-6 rounded-full uppercase tracking-wide transition-all hover:scale-105"
            >
              View My Work
            </Button>
            <Button
              onClick={() => scrollToSection('contact')}
              className="bg-transparent text-[#d9fb06] border-2 border-[#d9fb06] hover:bg-[#d9fb06] hover:text-[#1a1c1b] font-semibold text-base px-8 py-6 rounded-full uppercase tracking-wide transition-all hover:scale-105"
            >
              Get In Touch
            </Button>
          </div>

          {/* Social Links */}
          <div className="flex gap-4 animate-slideUp" style={{ animationDelay: '0.8s' }}>
            <a
              href={personalInfo.socials.github}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#888680] hover:text-[#d9fb06] transition-colors p-2"
              aria-label="GitHub"
            >
              <Github size={24} />
            </a>
            <a
              href={personalInfo.socials.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#888680] hover:text-[#d9fb06] transition-colors p-2"
              aria-label="LinkedIn"
            >
              <Linkedin size={24} />
            </a>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-[#888680] rounded-full flex justify-center pt-2">
          <div className="w-1.5 h-3 bg-[#d9fb06] rounded-full"></div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
