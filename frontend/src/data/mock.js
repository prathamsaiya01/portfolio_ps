// src/data/mock.ts

export const personalInfo = {
  name: 'Pratham Saiya',
  tagline:
    'Third-year Diploma Computer Engineering student, developer, hackathon participant, and technical event leader building practical AI, web, and product experiences.',
  bio:
    "I’m a third-year Diploma student in Computer Engineering, a developer and hackathon participant with experience leading technical events and collaborative projects. I’m interested in AI, software, product development, and practical web experiences, and I’m currently building NOVA, an AI Smart Mirror with Virtual Try-On Clothes.",
  location: 'Goregaon (West), Mumbai – 400104',
  email: 'prathamsaiya01@gmail.com',
  // 👉 Update these with your real profiles
  socials: {
    github: 'https://github.com/prathamsaiya01',
    linkedin: 'https://www.linkedin.com/in/pratham-saiya-5512b7330?utm_source=share_via&utm_content=profile&utm_medium=member_android',
  },
  // put your PDF in /public and update the name if needed
  resumeUrl: '/PrathamS-Resume-Internship.pdf',
};

export const experience = [
  {
    id: 1,
    title: 'Technical Head',
    company: 'Spectrum 4.0',
    period: 'Aug 2025 – Oct 2025',
    description:
      'Led the technical team for events like CodePrism and CodeClash, building coding-based games and coordinating with design and event teams to deliver smooth event experiences.',
  },
  {
    id: 2,
    title: 'Student Class Representative (SCR)',
    company: 'SVKM’s SBMP',
    period: 'July 2025 – Present',
    description:
      'Acted as a bridge between students and faculty, supporting academic coordination and helping organise technical events and activities.',
  },
  {
    id: 3,
    title: 'Hackathon Participant – LoanWise (SIH)',
    company: 'Smart India Hackathon',
    period: 'Sep 2025',
    description: 'Worked on Loan Utilisation Tracker – LoanWise, a system to monitor and optimise loan usage, focusing on requirements, logic, and team collaboration.',
  },
  {
    id: 4,
    title: 'Hackathon Participant – RakhtSetu',
    company: 'RakhtSetu Hackathon',
    period: 'Aug 2025',
    description: 'Built RakhtSetu, a web platform connecting blood donors and recipients, contributing to UI design and backend database logic.',
  },
  {
    id: 5,
    title: 'Newsletter Editorial Head',
    company: 'College',
    period: '2024 – 2026',
    description: 'Led editorial and content coordination for college newsletter work, supporting clear communication and consistent presentation.',
  },
  {
    id: 6,
    title: 'Graphic Design Intern',
    company: 'CNK',
    period: 'Not specified',
    description: 'Graphic design internship experience.',
  },
  {
    id: 7,
    title: 'React.js Developer Intern',
    company: 'TEN',
    period: 'Not specified',
    description: 'React.js developer internship experience.',
  },
  {
    id: 8,
    title: 'Volunteer',
    company: 'Spectrum 3.0',
    period: 'Aug 2024 – Sept 2024',
    description:
      'Supported the Design and Technical teams, learning the importance of details, visual consistency, and the technical approach behind event execution.',
  },
  { id: 9, title: 'OOSC 4.0', company: 'IIIT Allahabad', period: 'Online · 2026', description: 'Participant.' },
  { id: 10, title: 'HackDevengers 1.0', company: 'Unstop', period: 'Online · 2026', description: 'Participant.' },
  { id: 11, title: 'Ignite 8.0', company: 'Not specified', period: 'Offline · 2026', description: 'Participant.' },
];

export const education = [
  {
    id: 1,
    degree: 'Diploma in Computer Engineering',
    school: 'SVKM’s Shri Bhagubhai Mafatlal Polytechnic & College of Engineering',
    period: '2024 – Present',
    description:
      '3rd-year Diploma student with distinction in Semester I (91.77%) and Semester II (91.33%), actively involved in technical events and leadership roles.',
  },
  {
    id: 2,
    degree: 'ICSE (Class 10)',
    school: 'GES English Medium School',
    period: '2012 – 2024',
    description:
      'Completed schooling with 94.50% in ICSE, building a strong foundation in academics and problem solving.',
  },
];

export const academicHighlights = [
  { value: '91.76%', label: 'Semester III' },
  { value: '94.11%', label: 'Semester IV' },
  { value: '96%', label: 'Award-Winning Subjects' },
];

export const skills = [
  {
    category: 'Programming & Web',
    items: [
      { name: 'JavaScript', level: 80 }, { name: 'TypeScript', level: null }, { name: 'React.js', level: 80 },
      { name: 'HTML & CSS', level: 85 }, { name: 'Java', level: 75 }, { name: 'C', level: 70 }, { name: 'Python', level: null },
    ],
  },
  {
    category: 'Backend & Database',
    items: [
      { name: 'Backend Development', level: null }, { name: 'Node.js', level: 60 }, { name: 'DBMS', level: 75 },
      { name: 'MySQL', level: 75 }, { name: 'MongoDB', level: null }, { name: 'Firebase', level: 60 }, { name: 'Supabase', level: null },
    ],
  },
  {
    category: 'AI, App & Tools',
    items: [
      { name: 'Basic Machine Learning', level: null }, { name: 'AI Development', level: null },
      { name: 'Flutter', level: null }, { name: 'Application Development', level: null },
      { name: 'Git & GitHub', level: 80 }, { name: 'UI/UX Thinking', level: 70 },
    ],
  },
  {
    category: 'Leadership & Professional',
    items: [
      { name: 'Event Management', level: 85 }, { name: 'Event Coordination', level: 85 },
      { name: 'Leadership', level: 85 }, { name: 'Teamwork', level: 85 }, { name: 'Communication', level: 80 },
      { name: 'Problem Solving', level: 80 }, { name: 'Creativity', level: 80 },
    ],
  },
];

export const projects = [
  {
    id: 1,
    title: 'ApnaAdda – Indian PocketParty',
    description:
      'A web app for college students to plan events, games, and social gatherings in an interactive way.',
    longDescription:
      'ApnaAdda is built as a one-stop hub for college students to create and manage events, informal gatherings, games and activities. It focuses on simplicity, visual clarity, and making it easy for friends to discover and join plans.',
    stack: ['React', 'Node.js', 'Firebase', 'JavaScript'],
    image: '/images/projects/apna-adda.jpg', // or any placeholder image
    demo: '#', // put your live link here
    repo: '#', // put your GitHub repo link here
  },
  {
    id: 2,
    title: 'FilmyRadar',
    description:
      'Movie discovery and recommendation platform with trending films and personalised suggestions.',
    longDescription:
      'FilmyRadar allows users to explore trending movies, view details, and get recommendations using data from TMDB. It focuses on clean UI and fast access to information.',
    stack: ['React', 'TMDB API', 'CSS'],
    image: '/images/projects/filmy-radar.jpg',
    demo: '#',
    repo: '#',
  },
  {
    id: 3,
    title: 'QuizMaster App',
    description:
      'React-based quiz platform with Admin Panel, Leaderboards and Analytics for tech events.',
    longDescription:
      'QuizMaster powers event-style quizzes with an admin dashboard to manage questions, track participants, and view rankings and basic analytics. Designed for college tech events and coding contests.',
    stack: ['React', 'TypeScript', 'Firebase'],
    image: '/images/projects/quizmaster.jpg',
    demo: '#',
    repo: '#',
  },
  {
    id: 4,
    title: 'Codeopoly – CodePrism Round',
    description:
      'A coding-themed Monopoly-style board game combining technical challenges and strategy.',
    longDescription:
      'Codeopoly is used as a fun, competitive round in CodePrism, where players move around a board, face coding challenges, and make strategic choices inspired by Monopoly mechanics.',
    stack: ['JavaScript', 'Game Logic', 'Event Tech'],
    image: '/images/projects/codeopoly.jpg',
    demo: '#',
    repo: '#',
  },
  {
    id: 5,
    title: 'RakhtSetu',
    description:
      'Socially impactful web platform that connects blood donors and recipients.',
    longDescription:
      'RakhtSetu aims to make blood donation easier by matching donors and recipients based on availability and location, with a focus on clear UI and reliable data handling.',
    stack: ['Web', 'Database', 'UI/UX'],
    image: '/images/projects/rakhtsetu.jpg',
    demo: '#',
    repo: '#',
  },
  {
    id: 6,
    title: 'Loan Utilisation Tracker – LoanWise (SIH)',
    description:
      'Prototype for tracking and monitoring loan utilisation for the Smart India Hackathon.',
    longDescription:
      'LoanWise helps track how loan amounts are used over time and provides visibility into spending categories, supporting better financial discipline and reporting.',
    stack: ['Web App', 'Database', 'Problem Solving'],
    image: '/images/projects/loanwise.jpg',
    demo: '#',
    repo: '#',
  },
  {
    id: 7,
    title: 'StockHub',
    description:
      'Java-based inventory management system with GUI using Swing and file handling.',
    longDescription:
      'StockHub provides a simple desktop interface to add, update, and track stock items. It demonstrates strong Java fundamentals, file handling, and UI design.',
    stack: ['Java', 'Swing', 'File Handling'],
    image: '/images/projects/stockhub.jpg',
    demo: '#',
    repo: '#',
  },
];

export const manualProjects = [
  {
    id: 'nova',
    title: 'NOVA',
    description: 'AI Smart Mirror with Virtual Try-On Clothes.',
    longDescription: 'AI Smart Mirror with Virtual Try-On Clothes. Currently in development.',
    stack: ['AI', 'Smart Mirror', 'Virtual Try-On'],
    image: '/images/profile-pratham.jpg',
    demo: null,
    repo: null,
    status: 'CURRENTLY BUILDING',
    featured: true,
  },
  {
    id: 'aitteacherbot',
    title: 'AITeacherBot',
    description: 'AI Teacher Bot project.',
    longDescription: 'AI Teacher Bot project. Coming soon.',
    stack: ['AI'],
    image: '/images/profile-pratham.jpg',
    demo: null,
    repo: null,
    status: 'COMING SOON',
  },
  {
    id: 'notely',
    title: 'Notely',
    description: 'Smart Notes / collaborative notes and reminders project.',
    longDescription: 'Smart Notes / collaborative notes and reminders project. Coming soon.',
    stack: ['Notes', 'Collaboration'],
    image: '/images/profile-pratham.jpg',
    demo: null,
    repo: null,
    status: 'COMING SOON',
  },
  {
    id: 'fitfreak',
    title: 'FitFreak',
    description: 'Fitness-related project.',
    longDescription: 'Fitness-related project. Coming soon.',
    stack: ['Fitness'],
    image: '/images/fitfreak-landing-page.png',
    demo: 'https://fittfreak.netlify.app/',
    repo: null,
    status: 'COMING SOON',
  },
  {
    id: 'reaction-time-game',
    title: 'Reaction Time Game',
    description: 'IoT-based Reaction Time Game project.',
    longDescription: 'IoT-based Reaction Time Game project. Coming soon.',
    stack: ['IoT', 'Game'],
    image: '/images/profile-pratham.jpg',
    demo: null,
    repo: null,
    status: 'COMING SOON',
  },
];
