import React from 'react';
import { Award } from 'lucide-react';
import { academicHighlights } from '../data/portfolioUpdates';

const AcademicHighlights = () => (
  <section id="academics" className="bg-[#0f0f10] py-24">
    <div className="max-w-[87.5rem] mx-auto px-8">
      <div className="mb-12">
        <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">Academic Highlights</h2>
        <div className="w-24 h-1 bg-[#d9fb06]" />
      </div>
      <div className="grid sm:grid-cols-3 gap-6">
        {academicHighlights.map((item) => (
          <div key={item.label} className="bg-[#1a1c1b] border border-[#3f4816]/50 rounded-2xl p-7 hover:border-[#d9fb06]/50 transition-colors">
            <Award size={22} className="text-[#d9fb06] mb-6" />
            <p className="text-[#d9fb06] text-4xl sm:text-5xl font-black">{item.value}</p>
            <p className="text-[#dfddd6] mt-3 font-semibold">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export default AcademicHighlights;
