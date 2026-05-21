import React from 'react';
import { MapPin, Mail } from 'lucide-react';
import { personalInfo, experience, education } from '../data/mock';

const About = () => {
  return (
    <section id="about" className="bg-[#1a1c1b] py-24">
      <div className="max-w-[87.5rem] mx-auto px-8">
        {/* Section Header */}
        <div className="mb-16">
          <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">
            About Me
          </h2>
          <div className="w-24 h-1 bg-[#d9fb06]"></div>
        </div>

        <div className="grid md:grid-cols-2 gap-12 lg:gap-20">
          {/* Left Column - Bio and Contact */}
          <div>
            {/* Profile Image Placeholder */}
            <div className="w-64 h-64 bg-[#302f2c] rounded-2xl mb-8 overflow-hidden">
              <img
                src="/images/profile-pratham.jpg"
                alt="Profile"
                className="w-full h-full object-cover"
              />
            </div>

            {/* Bio */}
            <p className="text-[#dfddd6] text-lg leading-relaxed mb-6">
              {personalInfo.bio}
            </p>

            {/* Contact Info */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-[#888680]">
                <MapPin size={20} className="text-[#d9fb06]" />
                <span>{personalInfo.location}</span>
              </div>
              <div className="flex items-center gap-3 text-[#888680]">
                <Mail size={20} className="text-[#d9fb06]" />
                <a href={`mailto:${personalInfo.email}`} className="hover:text-[#d9fb06] transition-colors">
                  {personalInfo.email}
                </a>
              </div>
            </div>
          </div>

          {/* Right Column - Experience & Education */}
          <div>
            {/* Experience */}
            <div className="mb-12">
              <h3 className="text-[#d9fb06] text-2xl font-bold mb-6 uppercase tracking-wide">Experience</h3>
              <div className="space-y-6">
                {experience.map((exp) => (
                  <div key={exp.id} className="border-l-2 border-[#3f4816] pl-6 pb-6">
                    <div className="relative">
                      <div className="absolute -left-[1.6rem] top-0 w-3 h-3 bg-[#d9fb06] rounded-full"></div>
                      <h4 className="text-[#dfddd6] text-lg font-semibold mb-1">{exp.title}</h4>
                      <p className="text-[#d9fb06] text-sm font-medium mb-1">{exp.company}</p>
                      <p className="text-[#888680] text-sm mb-2">{exp.period}</p>
                      <p className="text-[#888680] text-sm leading-relaxed">{exp.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Education */}
            <div>
              <h3 className="text-[#d9fb06] text-2xl font-bold mb-6 uppercase tracking-wide">Education</h3>
              <div className="space-y-6">
                {education.map((edu) => (
                  <div key={edu.id} className="border-l-2 border-[#3f4816] pl-6">
                    <div className="relative">
                      <div className="absolute -left-[1.6rem] top-0 w-3 h-3 bg-[#d9fb06] rounded-full"></div>
                      <h4 className="text-[#dfddd6] text-lg font-semibold mb-1">{edu.degree}</h4>
                      <p className="text-[#d9fb06] text-sm font-medium mb-1">{edu.school}</p>
                      <p className="text-[#888680] text-sm mb-2">{edu.period}</p>
                      <p className="text-[#888680] text-sm leading-relaxed">{edu.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
