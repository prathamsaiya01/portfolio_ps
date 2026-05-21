import React from 'react';
import { Download, Briefcase, GraduationCap } from 'lucide-react';
import { Button } from './ui/button';
import { personalInfo, experience, education } from '../data/mock';

const Resume = () => {
  const handleDownload = () => {
    // Mock download - in production, link to actual PDF
    window.open(personalInfo.resumeUrl, '_blank');
  };

  return (
    <section id="resume" className="bg-[#1a1c1b] py-24">
      <div className="max-w-[87.5rem] mx-auto px-8">
        {/* Section Header */}
        <div className="mb-16 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
          <div>
            <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">
              Resume
            </h2>
            <div className="w-24 h-1 bg-[#d9fb06] mb-4"></div>
            <p className="text-[#888680] text-lg max-w-2xl">
              My professional experience, education, and qualifications.
            </p>
          </div>
          <Button
            onClick={handleDownload}
            className="bg-[#d9fb06] text-[#1a1c1b] hover:bg-[#d9fb06]/90 font-semibold px-8 py-6 rounded-full uppercase tracking-wide transition-all hover:scale-105"
          >
            <Download size={20} className="mr-2" />
            Download PDF
          </Button>
        </div>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Experience Column */}
          <div>
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 bg-[#d9fb06] rounded-full flex items-center justify-center">
                <Briefcase size={24} className="text-[#1a1c1b]" />
              </div>
              <h3 className="text-[#d9fb06] text-2xl font-bold uppercase tracking-wide">Experience</h3>
            </div>
            <div className="space-y-8">
              {experience.map((exp) => (
                <div
                  key={exp.id}
                  className="bg-[#302f2c] p-6 rounded-xl border border-[#3f4816]/50 hover:border-[#d9fb06]/50 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="text-[#dfddd6] text-lg font-bold">{exp.title}</h4>
                  </div>
                  <p className="text-[#d9fb06] font-semibold mb-1">{exp.company}</p>
                  <p className="text-[#888680] text-sm mb-3">{exp.period}</p>
                  <p className="text-[#888680] leading-relaxed">{exp.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Education Column */}
          <div>
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 bg-[#d9fb06] rounded-full flex items-center justify-center">
                <GraduationCap size={24} className="text-[#1a1c1b]" />
              </div>
              <h3 className="text-[#d9fb06] text-2xl font-bold uppercase tracking-wide">Education</h3>
            </div>
            <div className="space-y-8">
              {education.map((edu) => (
                <div
                  key={edu.id}
                  className="bg-[#302f2c] p-6 rounded-xl border border-[#3f4816]/50 hover:border-[#d9fb06]/50 transition-all"
                >
                  <h4 className="text-[#dfddd6] text-lg font-bold mb-2">{edu.degree}</h4>
                  <p className="text-[#d9fb06] font-semibold mb-1">{edu.school}</p>
                  <p className="text-[#888680] text-sm mb-3">{edu.period}</p>
                  <p className="text-[#888680] leading-relaxed">{edu.description}</p>
                </div>
              ))}
            </div>

            {/* Certifications/Additional Info */}
          {/* Certifications/Additional Info */}
<div className="mt-12 bg-[#302f2c] p-6 rounded-xl border border-[#3f4816]/50">
  <h4 className="text-[#d9fb06] font-bold mb-4 uppercase text-sm tracking-wide">
    Key Highlights
  </h4>
  <ul className="space-y-2 text-[#888680]">
    <li className="flex items-start gap-2">
      <span className="text-[#d9fb06] mt-1">•</span>
      <span>Topper in Semester I &amp; II (91.77% and 91.33%).</span>
    </li>
    <li className="flex items-start gap-2">
      <span className="text-[#d9fb06] mt-1">•</span>
      <span>Technical Head of Spectrum 4.0 and active SCR (Student Class Representative).</span>
    </li>
    <li className="flex items-start gap-2">
      <span className="text-[#d9fb06] mt-1">•</span>
      <span>Hackathon experience in Smart India Hackathon (LoanWise) and RakhtSetu.</span>
    </li>
    <li className="flex items-start gap-2">
      <span className="text-[#d9fb06] mt-1">•</span>
      <span>Developed multiple tech-based and event projects including ApnaAdda, FilmyRadar and QuizMaster.</span>
    </li>
  </ul>
</div>

          </div>
        </div>
      </div>
    </section>
  );
};

export default Resume;
