import React, { useState } from 'react';
import { Send, Mail, MapPin, Linkedin, Github } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { useToast } from '../hooks/use-toast';
import { personalInfo } from '../data/mock';

const Contact = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Mock form submission - in production, integrate with backend or form service
    setTimeout(() => {
      toast({
        title: "Message Sent!",
        description: "Thanks for reaching out. I'll get back to you soon.",
      });
      setFormData({ name: '', email: '', subject: '', message: '' });
      setIsSubmitting(false);
    }, 1000);
  };

  return (
    <section id="contact" className="bg-[#0f0f10] py-24">
      <div className="max-w-[87.5rem] mx-auto px-8">
        {/* Section Header */}
        <div className="mb-16">
          <h2 className="font-black text-[clamp(2.5rem,6vw,4rem)] leading-[0.9] text-[#d9fb06] mb-4 uppercase">
            Get In Touch
          </h2>
          <div className="w-24 h-1 bg-[#d9fb06] mb-8"></div>
          <p className="text-[#888680] text-lg max-w-2xl">
            Have a project in mind or want to collaborate? I'd love to hear from you.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-12">
          {/* Contact Info - Left Side */}
          <div className="lg:col-span-2 space-y-8">
            {/* Email */}
            <div className="bg-[#1a1c1b] p-6 rounded-xl border border-[#3f4816]/50">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-[#d9fb06] rounded-full flex items-center justify-center flex-shrink-0">
                  <Mail size={20} className="text-[#1a1c1b]" />
                </div>
                <div>
                  <h3 className="text-[#dfddd6] font-semibold mb-1">Email</h3>
                  <a
                    href={`mailto:${personalInfo.email}`}
                    className="text-[#888680] hover:text-[#d9fb06] transition-colors break-all"
                  >
                    {personalInfo.email}
                  </a>
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="bg-[#1a1c1b] p-6 rounded-xl border border-[#3f4816]/50">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-[#d9fb06] rounded-full flex items-center justify-center flex-shrink-0">
                  <MapPin size={20} className="text-[#1a1c1b]" />
                </div>
                <div>
                  <h3 className="text-[#dfddd6] font-semibold mb-1">Location</h3>
                  <p className="text-[#888680]">{personalInfo.location}</p>
                </div>
              </div>
            </div>

            {/* Social Links */}
            <div className="bg-[#1a1c1b] p-6 rounded-xl border border-[#3f4816]/50">
              <h3 className="text-[#dfddd6] font-semibold mb-4">Connect With Me</h3>
              <div className="flex gap-4">
                <a
                  href={personalInfo.socials.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-12 h-12 bg-[#302f2c] rounded-full flex items-center justify-center text-[#888680] hover:text-[#d9fb06] hover:bg-[#3f4816] transition-all"
                  aria-label="GitHub"
                >
                  <Github size={20} />
                </a>
                <a
                  href={personalInfo.socials.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-12 h-12 bg-[#302f2c] rounded-full flex items-center justify-center text-[#888680] hover:text-[#d9fb06] hover:bg-[#3f4816] transition-all"
                  aria-label="LinkedIn"
                >
                  <Linkedin size={20} />
                </a>
              </div>
            </div>
          </div>

          {/* Contact Form - Right Side */}
          <div className="lg:col-span-3">
            <form onSubmit={handleSubmit} className="bg-[#1a1c1b] p-8 rounded-xl border border-[#3f4816]/50">
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label htmlFor="name" className="text-[#dfddd6] font-medium mb-2 block">
                    Name *
                  </label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    className="bg-[#302f2c] border-[#3f4816] text-[#dfddd6] focus:border-[#d9fb06] placeholder:text-[#888680]"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="text-[#dfddd6] font-medium mb-2 block">
                    Email *
                  </label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="bg-[#302f2c] border-[#3f4816] text-[#dfddd6] focus:border-[#d9fb06] placeholder:text-[#888680]"
                    placeholder="your.email@example.com"
                  />
                </div>
              </div>

              <div className="mb-6">
                <label htmlFor="subject" className="text-[#dfddd6] font-medium mb-2 block">
                  Subject *
                </label>
                <Input
                  id="subject"
                  name="subject"
                  type="text"
                  required
                  value={formData.subject}
                  onChange={handleChange}
                  className="bg-[#302f2c] border-[#3f4816] text-[#dfddd6] focus:border-[#d9fb06] placeholder:text-[#888680]"
                  placeholder="What's this about?"
                />
              </div>

              <div className="mb-6">
                <label htmlFor="message" className="text-[#dfddd6] font-medium mb-2 block">
                  Message *
                </label>
                <Textarea
                  id="message"
                  name="message"
                  required
                  value={formData.message}
                  onChange={handleChange}
                  rows={6}
                  className="bg-[#302f2c] border-[#3f4816] text-[#dfddd6] focus:border-[#d9fb06] placeholder:text-[#888680] resize-none"
                  placeholder="Tell me about your project..."
                />
              </div>

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full md:w-auto bg-[#d9fb06] text-[#1a1c1b] hover:bg-[#d9fb06]/90 font-semibold px-8 py-6 rounded-full uppercase tracking-wide transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  'Sending...'
                ) : (
                  <>
                    <Send size={20} className="mr-2" />
                    Send Message
                  </>
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Contact;
