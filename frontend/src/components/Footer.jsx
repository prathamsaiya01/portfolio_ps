import React from 'react';
import { Heart } from 'lucide-react';
import { personalInfo } from '../data/mock';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const scrollToSection = (sectionId) => {   // 👈 remove : string
    const element = document.getElementById(sectionId);
    if (element) {
      const offset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
    }
  };

  return (
    <footer className="bg-[#1a1c1b] border-t border-[#3f4816]/50 py-12">
      <div className="max-w-[87.5rem] mx-auto px-8">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          {/* Brand */}
          <div>
            <h3 className="text-[#d9fb06] font-bold text-2xl mb-3">PS</h3>
            <p className="text-[#888680] text-sm leading-relaxed">
              Diploma Computer Engineering student & aspiring software developer,
              building event tech, web apps, and smooth user experiences.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-[#dfddd6] font-semibold mb-4 uppercase text-sm tracking-wide">
              Quick Links
            </h4>
            <nav className="flex flex-col gap-2">
              {['home', 'about', 'projects', 'skills', 'resume', 'contact'].map((link) => (
                <button
                  key={link}
                  onClick={() => scrollToSection(link)}
                  className="text-[#888680] hover:text-[#d9fb06] transition-colors text-sm text-left capitalize"
                >
                  {link}
                </button>
              ))}
            </nav>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-[#dfddd6] font-semibold mb-4 uppercase text-sm tracking-wide">Contact</h4>
            <div className="space-y-2 text-sm">
              <p className="text-[#888680]">{personalInfo.location}</p>
              <a
                href={`mailto:${personalInfo.email}`}
                className="text-[#888680] hover:text-[#d9fb06] transition-colors block"
              >
                {personalInfo.email}
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[#3f4816]/50">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-[#888680] text-sm flex items-center gap-2">
              © {currentYear} {personalInfo.name}. Made with{' '}
              <Heart size={14} className="text-[#d9fb06] fill-[#d9fb06]" />
            </p>
            <p className="text-[#888680] text-sm">Built with React & Tailwind CSS</p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
