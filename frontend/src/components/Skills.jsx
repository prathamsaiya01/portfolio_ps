import React from 'react';
import { skills } from '../data/mock';

const Skills = () => {
  return (
    <section id="skills" className="bg-[#0f0f10] py-24">
      <div className="max-w-[87.5rem] mx-auto px-8">
        {/* Section Header */}
        <div className="mb-16">
          <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">
            Skills & Expertise
          </h2>
          <div className="w-24 h-1 bg-[#d9fb06] mb-8"></div>
          <p className="text-[#888680] text-lg max-w-2xl">
            A comprehensive overview of my technical skills and proficiency levels across different domains.
          </p>
        </div>

        {/* Skills Grid */}
        <div className="grid md:grid-cols-2 gap-12">
          {skills.map((category, index) => (
            <div key={index} className="bg-[#1a1c1b] p-8 rounded-2xl border border-[#3f4816]/50">
              <h3 className="text-[#d9fb06] text-2xl font-bold mb-6 uppercase tracking-wide">
                {category.category}
              </h3>
              <div className="space-y-6">
                {category.items.map((skill, skillIndex) => (
                  <div key={skillIndex}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[#dfddd6] font-medium">{skill.name}</span>
                      <span className="text-[#888680] text-sm">{skill.level}%</span>
                    </div>
                    <div className="w-full h-2 bg-[#302f2c] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#d9fb06] rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${skill.level}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Skills;
