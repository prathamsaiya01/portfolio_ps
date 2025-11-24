# Personal Portfolio Website

A modern, responsive, and accessible personal portfolio website built with React, featuring smooth animations, project showcases, and a clean design aesthetic.

## 🌟 Features

### Core Sections
- **Hero Section**: Eye-catching introduction with rotating skill titles and call-to-action buttons
- **About Section**: Professional bio, experience timeline, and education
- **Projects Section**: Interactive project cards with filtering by technology stack
- **Skills Section**: Visual skill bars showing proficiency levels across different categories
- **Resume Section**: Downloadable PDF and detailed experience/education display
- **Contact Section**: Functional contact form with social media links
- **Footer**: Quick navigation and contact information

### Design Highlights
- **Modern Aesthetic**: Black background (#1a1c1b) with lime green (#d9fb06) accent colors
- **Smooth Animations**: Fade-in and slide-up effects for enhanced user experience
- **Responsive Design**: Fully optimized for mobile, tablet, and desktop devices
- **Interactive Elements**: 
  - Sticky header with active section highlighting
  - Smooth scroll navigation
  - Project filtering by technology
  - Project detail modal/dialog
  - Hover effects on cards and buttons
  - Mobile-friendly hamburger menu

### Technical Features
- **React 19**: Latest React version with hooks
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **Shadcn UI Components**: High-quality, accessible UI components
- **Lucide Icons**: Modern icon library
- **Mock Data**: Structured data in `/src/data/mock.js` for easy customization
- **Accessibility**: Semantic HTML, ARIA labels, and keyboard navigation
- **Performance**: Lazy loading images and optimized animations

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and yarn installed
- Basic knowledge of React and JavaScript

### Installation

1. **Install Dependencies**
   ```bash
   cd /app/frontend
   yarn install
   ```

2. **Start Development Server**
   ```bash
   yarn start
   ```
   The site will open at `http://localhost:3000`

### Building for Production
```bash
cd /app/frontend
yarn build
```
The production-ready files will be in the `build/` directory.

## 📝 Customization Guide

### 1. Personal Information
Edit `/app/frontend/src/data/mock.js`:

```javascript
export const personalInfo = {
  name: "Your Name",
  title: "Your Professional Title",
  tagline: "Your tagline",
  bio: "Your bio...",
  email: "your.email@example.com",
  location: "Your Location",
  resumeUrl: "/path-to-your-resume.pdf",
  socials: {
    github: "https://github.com/yourusername",
    linkedin: "https://linkedin.com/in/yourusername",
    twitter: "https://twitter.com/yourusername"
  }
};
```

### 2. Projects
Add or modify projects in the `projects` array:

```javascript
export const projects = [
  {
    id: "unique-id",
    title: "Project Name",
    description: "Short description",
    longDescription: "Detailed description for modal",
    stack: ["React", "Node.js", "MongoDB"],
    demo: "https://demo-link.com",
    repo: "https://github.com/username/repo",
    image: "https://image-url.com/image.jpg",
    featured: true
  },
  // Add more projects...
];
```

### 3. Skills
Update the `skills` array with your proficiency levels:

```javascript
export const skills = [
  {
    category: "Category Name",
    items: [
      { name: "Skill Name", level: 95 },
      // Add more skills...
    ]
  }
];
```

### 4. Experience & Education
Modify the `experience` and `education` arrays in `mock.js`.

### 5. Color Scheme
To change colors, edit `/app/frontend/src/index.css`:

```css
:root {
  --bg-page: #1a1c1b;           /* Main background */
  --text-primary: #d9fb06;       /* Primary accent color */
  --text-secondary: #888680;     /* Secondary text */
  --bg-card: #302f2c;            /* Card backgrounds */
}
```

### 6. Add Your Resume
Place your `resume.pdf` in `/app/frontend/public/` and update the `resumeUrl` in `mock.js`.

## 📱 Responsive Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1199px
- **Desktop**: ≥ 1200px

## ♿ Accessibility Features

- Semantic HTML5 elements
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus states on all interactive elements
- Alt text on images
- High contrast text and backgrounds
- Screen reader friendly

## 🎨 Design System

### Typography
- **Headings**: Bold, uppercase, large scale for impact
- **Body Text**: Readable, relaxed line height
- **Colors**: High contrast for readability

### Spacing
- Consistent 8px grid system
- Generous whitespace for clarity
- Responsive padding and margins

### Animations
- Subtle fade-in effects
- Smooth scroll behavior
- Hover transitions (300ms)
- Scale effects on buttons

## 🧪 Testing Checklist

- [x] Navigation works on all devices
- [x] Smooth scroll to sections
- [x] Project filtering works correctly
- [x] Project modal opens and closes
- [x] Contact form validation
- [x] Mobile menu toggles properly
- [x] All links open correctly
- [x] Images load properly
- [x] Resume downloads
- [x] Keyboard navigation works
- [x] Focus states are visible

## 🚀 Deployment

### GitHub Pages
1. Build the project: `yarn build`
2. Deploy the `build/` folder to GitHub Pages
3. Configure `homepage` in `package.json`

### Netlify
1. Connect your repository to Netlify
2. Set build command: `yarn build`
3. Set publish directory: `build`
4. Deploy!

### Vercel
1. Import your repository
2. Framework: Create React App
3. Build command: `yarn build`
4. Output directory: `build`
5. Deploy!

## 📦 Project Structure

```
/app/frontend/
├── public/
│   ├── index.html
│   └── resume.pdf (add your resume here)
├── src/
│   ├── components/
│   │   ├── ui/              # Shadcn UI components
│   │   ├── Header.jsx       # Sticky navigation
│   │   ├── Hero.jsx         # Hero section
│   │   ├── About.jsx        # About section
│   │   ├── Projects.jsx     # Projects grid
│   │   ├── Skills.jsx       # Skills section
│   │   ├── Resume.jsx       # Resume section
│   │   ├── Contact.jsx      # Contact form
│   │   └── Footer.jsx       # Footer
│   ├── data/
│   │   └── mock.js          # All customizable data
│   ├── hooks/
│   │   └── use-toast.js     # Toast notifications
│   ├── App.js               # Main app component
│   ├── App.css              # Custom animations
│   └── index.css            # Global styles
├── package.json
└── README.md
```

## 🔧 Advanced Customization

### Add Theme Toggle
You can add a light/dark theme toggle by:
1. Create a theme context
2. Add theme colors to CSS variables
3. Toggle classes based on theme state

### Integrate Backend
To connect the contact form to a backend:
1. Update the `handleSubmit` function in `Contact.jsx`
2. Make API call to your backend endpoint
3. Handle success/error responses

### Add Blog Section
1. Create a new `Blog.jsx` component
2. Add blog data to `mock.js`
3. Include in `App.js` navigation

### SEO Optimization
1. Update meta tags in `public/index.html`
2. Add Open Graph tags
3. Create a sitemap
4. Add structured data (JSON-LD)

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to fork this project and customize it for your own portfolio!

## 💡 Tips

1. **Keep it Updated**: Regularly update your projects and skills
2. **Quality Images**: Use high-quality images for projects (optimize for web)
3. **Real Content**: Replace placeholder content with your actual information
4. **Test Thoroughly**: Check on different devices and browsers
5. **Fast Loading**: Optimize images and minimize bundle size
6. **Personal Touch**: Add your unique style and personality

## 📞 Support

For questions or issues, please open an issue on the repository.

---

**Built with React, Tailwind CSS, and ❤️**
