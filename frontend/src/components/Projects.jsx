import React, { useEffect, useState } from 'react';
import { ExternalLink, Github, X } from 'lucide-react';
import { Button } from './ui/button';
import { loadPortfolioProjects, mockProjects } from '../services/projectData';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';

const Projects = () => {
  const [projects, setProjects] = useState(mockProjects);
  const [filter, setFilter] = useState('all');
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    let active = true;
    loadPortfolioProjects().then((loadedProjects) => {
      if (active) setProjects(loadedProjects);
    });
    return () => { active = false; };
  }, []);

  // Get unique tech stacks for filtering
  const allTechs = [...new Set(projects.flatMap(p => p.stack))];
  const popularTechs = ['React', 'Node.js', 'TypeScript', 'MongoDB'];

  const filteredProjects = filter === 'all'
    ? projects
    : projects.filter(p => p.stack.includes(filter));

  return (
    <section id="projects" className="bg-[#1a1c1b] py-24">
      <div className="max-w-[87.5rem] mx-auto px-8">
        {/* Section Header */}
        <div className="mb-16">
          <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">
            Featured Projects
          </h2>
          <div className="w-24 h-1 bg-[#d9fb06] mb-8"></div>
          <p className="text-[#888680] text-lg max-w-2xl">
            A collection of projects showcasing my expertise in web development, UI/UX design, and problem-solving.
          </p>
        </div>

        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-3 mb-12">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-2 rounded-full font-medium text-sm uppercase tracking-wide transition-all ${
              filter === 'all'
                ? 'bg-[#d9fb06] text-[#1a1c1b]'
                : 'bg-[#302f2c] text-[#888680] hover:text-[#d9fb06]'
            }`}
          >
            All
          </button>
          {popularTechs.map((tech) => (
            <button
              key={tech}
              onClick={() => setFilter(tech)}
              className={`px-6 py-2 rounded-full font-medium text-sm uppercase tracking-wide transition-all ${
                filter === tech
                  ? 'bg-[#d9fb06] text-[#1a1c1b]'
                  : 'bg-[#302f2c] text-[#888680] hover:text-[#d9fb06]'
              }`}
            >
              {tech}
            </button>
          ))}
        </div>

        {/* Projects Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              className="bg-[#302f2c] rounded-2xl overflow-hidden border border-[#3f4816]/50 hover:border-[#d9fb06]/50 transition-all duration-300 hover:transform hover:scale-[1.02] cursor-pointer group"
              onClick={() => setSelectedProject(project)}
            >
              {/* Project Image */}
              <div className="h-48 overflow-hidden bg-[#1a1c1b]">
                <img
                  src={project.image}
                  alt={project.title}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  loading="lazy"
                />
              </div>

              {/* Project Content */}
              <div className="p-6">
                <h3 className="text-[#dfddd6] text-xl font-bold mb-2 group-hover:text-[#d9fb06] transition-colors">
                  {project.title}
                </h3>
                <p className="text-[#888680] text-sm mb-4 line-clamp-2">
                  {project.description}
                </p>

                {/* Tech Stack */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {project.stack.slice(0, 3).map((tech, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-[#1a1c1b] text-[#d9fb06] text-xs font-medium rounded-full"
                    >
                      {tech}
                    </span>
                  ))}
                  {project.stack.length > 3 && (
                    <span className="px-3 py-1 bg-[#1a1c1b] text-[#888680] text-xs font-medium rounded-full">
                      +{project.stack.length - 3}
                    </span>
                  )}
                </div>

                {/* Links */}
                <div className="flex gap-3">
                  <a
                    href={project.demo}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-2 text-[#d9fb06] hover:text-[#d9fb06]/80 text-sm font-medium transition-colors"
                  >
                    <ExternalLink size={16} />
                    Demo
                  </a>
                  <a
                    href={project.repo}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-2 text-[#888680] hover:text-[#d9fb06] text-sm font-medium transition-colors"
                  >
                    <Github size={16} />
                    Code
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Project Detail Modal */}
      <Dialog open={!!selectedProject} onOpenChange={() => setSelectedProject(null)}>
        <DialogContent className="bg-[#302f2c] border-[#3f4816] text-[#dfddd6] max-w-3xl max-h-[90vh] overflow-y-auto">
          {selectedProject && (
            <>
              <DialogHeader>
                <DialogTitle className="text-[#d9fb06] text-2xl font-bold mb-2">
                  {selectedProject.title}
                </DialogTitle>
                <DialogDescription className="text-[#888680]">
                  {selectedProject.longDescription}
                </DialogDescription>
              </DialogHeader>

              <div className="mt-4">
                {/* Project Image */}
                <img
                  src={selectedProject.image}
                  alt={selectedProject.title}
                  className="w-full h-64 object-cover rounded-lg mb-6"
                />

                {/* Tech Stack */}
                <div className="mb-6">
                  <h4 className="text-[#d9fb06] font-semibold mb-3 uppercase text-sm tracking-wide">Tech Stack</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedProject.stack.map((tech, index) => (
                      <span
                        key={index}
                        className="px-4 py-2 bg-[#1a1c1b] text-[#d9fb06] text-sm font-medium rounded-full"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Links */}
                <div className="flex gap-4">
                  <Button
                    onClick={() => window.open(selectedProject.demo, '_blank')}
                    className="bg-[#d9fb06] text-[#1a1c1b] hover:bg-[#d9fb06]/90 font-semibold rounded-full"
                  >
                    <ExternalLink size={16} className="mr-2" />
                    View Demo
                  </Button>
                  <Button
                    onClick={() => window.open(selectedProject.repo, '_blank')}
                    className="bg-transparent text-[#d9fb06] border-2 border-[#d9fb06] hover:bg-[#d9fb06] hover:text-[#1a1c1b] font-semibold rounded-full"
                  >
                    <Github size={16} className="mr-2" />
                    View Code
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
};

export default Projects;
