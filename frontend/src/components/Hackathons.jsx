import React from 'react';
import { Trophy } from 'lucide-react';
import { hackathons } from '../data/portfolioUpdates';

const Hackathons = () => (
  <section id="achievements" className="bg-[#1a1c1b] py-24">
    <div className="max-w-[87.5rem] mx-auto px-8">
      <div className="mb-12">
        <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">Hackathons & Achievements</h2>
        <div className="w-24 h-1 bg-[#d9fb06]" />
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {hackathons.map((event) => (
          <article key={event.name} className="bg-[#302f2c] border border-[#3f4816]/50 rounded-xl p-6 hover:border-[#d9fb06]/50 transition-colors">
            <div className="flex items-start justify-between gap-4 mb-6">
              <Trophy size={22} className="text-[#d9fb06]" />
              <span className="px-2 py-1 rounded-full bg-[#1a1c1b] text-[#d9fb06] text-[10px] font-bold tracking-wide">{event.badge}</span>
            </div>
            <h3 className="text-[#dfddd6] text-lg font-bold">{event.name}</h3>
            <p className="text-[#d9fb06] text-sm mt-2">{event.role}</p>
            <p className="text-[#888680] text-sm mt-2">{event.organizer} · {event.detail}</p>
          </article>
        ))}
      </div>
    </div>
  </section>
);

export default Hackathons;
