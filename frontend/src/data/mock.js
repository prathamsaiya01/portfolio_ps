// Mock data for portfolio website

export const personalInfo = {
  name: "Alex Morgan",
  title: "Full-Stack Developer & UI/UX Designer",
  tagline: "Building beautiful, functional web experiences",
  bio: "Passionate developer with 5+ years of experience creating modern web applications. I specialize in React, Node.js, and creating intuitive user experiences that solve real problems.",
  email: "alex.morgan@example.com",
  location: "San Francisco, CA",
  resumeUrl: "/resume.pdf",
  socials: {
    github: "https://github.com/alexmorgan",
    linkedin: "https://linkedin.com/in/alexmorgan",
    twitter: "https://twitter.com/alexmorgan",
    portfolio: "https://alexmorgan.dev"
  }
};

export const projects = [
  {
    id: "proj-01",
    title: "TaskFlow — Productivity App",
    description: "A lightweight task manager with drag-and-drop lists, keyboard shortcuts, and real-time collaboration. Built for teams who value simplicity.",
    longDescription: "TaskFlow revolutionizes team productivity with an intuitive interface that focuses on what matters. Features include drag-and-drop task organization, keyboard shortcuts for power users, real-time collaboration, and smart notifications.",
    stack: ["React", "Node.js", "MongoDB", "Socket.io", "Tailwind CSS"],
    demo: "https://taskflow-demo.example.com",
    repo: "https://github.com/alexmorgan/taskflow",
    image: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&q=80",
    featured: true
  },
  {
    id: "proj-02",
    title: "WeatherHub — Weather Dashboard",
    description: "Real-time weather tracking with beautiful visualizations, hourly forecasts, and location-based alerts.",
    longDescription: "WeatherHub provides accurate weather data with stunning visual representations. Track multiple locations, receive severe weather alerts, and plan your day with confidence.",
    stack: ["React", "TypeScript", "OpenWeather API", "Chart.js"],
    demo: "https://weatherhub-demo.example.com",
    repo: "https://github.com/alexmorgan/weatherhub",
    image: "https://images.unsplash.com/photo-1592210454359-9043f067919b?w=800&q=80",
    featured: true
  },
  {
    id: "proj-03",
    title: "Portfolio Site (This Site)",
    description: "Modern portfolio showcasing projects with smooth animations, responsive design, and accessibility-first approach.",
    longDescription: "This portfolio site demonstrates modern web development practices including responsive design, smooth animations, and comprehensive accessibility features.",
    stack: ["React", "Tailwind CSS", "Framer Motion", "React Router"],
    demo: "https://alexmorgan.dev",
    repo: "https://github.com/alexmorgan/portfolio",
    image: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80",
    featured: false
  },
  {
    id: "proj-04",
    title: "ChatConnect — Real-time Chat",
    description: "Secure messaging platform with end-to-end encryption, file sharing, and video calls.",
    longDescription: "ChatConnect provides secure, real-time communication for teams and individuals. Features include end-to-end encryption, file sharing, group chats, and integrated video calling.",
    stack: ["React", "Firebase", "WebRTC", "Material-UI"],
    demo: "https://chatconnect-demo.example.com",
    repo: "https://github.com/alexmorgan/chatconnect",
    image: "https://images.unsplash.com/photo-1611606063065-ee7946f0787a?w=800&q=80",
    featured: true
  },
  {
    id: "proj-05",
    title: "EcoTrack — Sustainability Tracker",
    description: "Track your carbon footprint and get personalized recommendations to reduce environmental impact.",
    longDescription: "EcoTrack helps individuals and businesses monitor their environmental impact with data-driven insights and actionable recommendations for sustainability.",
    stack: ["React", "Node.js", "PostgreSQL", "D3.js"],
    demo: "https://ecotrack-demo.example.com",
    repo: "https://github.com/alexmorgan/ecotrack",
    image: "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800&q=80",
    featured: false
  },
  {
    id: "proj-06",
    title: "CodeSnippet — Developer Tools",
    description: "Share and discover code snippets with syntax highlighting, tags, and community ratings.",
    longDescription: "CodeSnippet is a community-driven platform for developers to share, discover, and learn from code snippets across multiple programming languages.",
    stack: ["React", "Express", "MongoDB", "Prism.js"],
    demo: "https://codesnippet-demo.example.com",
    repo: "https://github.com/alexmorgan/codesnippet",
    image: "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80",
    featured: false
  }
];

export const skills = [
  {
    category: "Frontend",
    items: [
      { name: "React", level: 95 },
      { name: "TypeScript", level: 90 },
      { name: "HTML/CSS", level: 95 },
      { name: "Tailwind CSS", level: 90 },
      { name: "Next.js", level: 85 }
    ]
  },
  {
    category: "Backend",
    items: [
      { name: "Node.js", level: 90 },
      { name: "Express", level: 85 },
      { name: "Python", level: 80 },
      { name: "FastAPI", level: 75 },
      { name: "REST APIs", level: 90 }
    ]
  },
  {
    category: "Database & Tools",
    items: [
      { name: "MongoDB", level: 85 },
      { name: "PostgreSQL", level: 80 },
      { name: "Git", level: 95 },
      { name: "Docker", level: 75 },
      { name: "AWS", level: 70 }
    ]
  },
  {
    category: "Design & UX",
    items: [
      { name: "Figma", level: 85 },
      { name: "UI/UX Design", level: 80 },
      { name: "Responsive Design", level: 95 },
      { name: "Accessibility", level: 85 },
      { name: "Wireframing", level: 80 }
    ]
  }
];

export const experience = [
  {
    id: 1,
    title: "Senior Full-Stack Developer",
    company: "TechCorp Inc.",
    period: "2021 - Present",
    description: "Lead development of customer-facing web applications. Mentored junior developers and implemented best practices."
  },
  {
    id: 2,
    title: "Full-Stack Developer",
    company: "StartupXYZ",
    period: "2019 - 2021",
    description: "Built scalable web applications using React and Node.js. Improved application performance by 40%."
  },
  {
    id: 3,
    title: "Frontend Developer",
    company: "Digital Agency Co.",
    period: "2018 - 2019",
    description: "Developed responsive websites for clients across various industries. Focused on accessibility and user experience."
  }
];

export const education = [
  {
    id: 1,
    degree: "Bachelor of Science in Computer Science",
    school: "University of California",
    period: "2014 - 2018",
    description: "Focus on Software Engineering and Human-Computer Interaction"
  }
];
