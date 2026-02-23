export interface TopicCard {
  heading: string;
  description: string;
  icon?: string;
}

export interface Slide {
  id: string;
  type: "title" | "text-image" | "checklist" | "quiz" | "text-only" | "cards";
  cards?: TopicCard[];
  title: string;
  subtitle?: string;
  body?: string;
  image?: string;
  items?: ChecklistItem[];
  quizQuestion?: string;
  quizOptions?: string[];
  correctAnswer?: number;
  buttonLabel?: string;
}

export interface ChecklistItem {
  text: string;
  checked?: boolean;
}

export interface CourseSlides {
  courseTitle: string;
  slides: Slide[];
}

export const courseSlides: CourseSlides = {
  courseTitle: "Digital Marketing Fundamentals",
  slides: [
    {
      id: "s1",
      type: "title",
      title: "Digital Marketing Fundamentals",
      subtitle: "Master the core concepts of modern digital marketing and grow your skills.",
      buttonLabel: "Start Learning",
    },
    {
      id: "s2",
      type: "text-image",
      title: "Welcome to Digital Marketing!",
      body: "This course is all about helping you understand the digital landscape. We'll walk you through the essentials — from search engines to social media — so you can confidently build and execute campaigns that drive results.",
    },
    {
      id: "s3",
      type: "text-only",
      title: "The Digital Marketing Ecosystem",
      body: "Digital marketing is a complex web of channels, platforms, and tools. At its core, it connects businesses with customers where they spend time — online. Understanding this ecosystem helps you prioritize your efforts and maximize impact.",
    },
    {
      id: "s3b",
      type: "cards",
      title: "Core Pillars of Digital Marketing",
      cards: [
        { heading: "SEO", icon: "🔍", description: "Optimize your website to rank higher in search results and drive organic traffic consistently." },
        { heading: "Content Marketing", icon: "✍️", description: "Create valuable content that attracts, engages, and converts your target audience." },
        { heading: "Social Media", icon: "📱", description: "Build brand presence and community across the platforms your audience uses most." },
        { heading: "Email Campaigns", icon: "✉️", description: "Nurture leads with personalized messages that deliver the highest ROI of any channel." },
        { heading: "Paid Advertising", icon: "📊", description: "Reach new audiences instantly with targeted PPC and display ad campaigns." },
        { heading: "Analytics", icon: "📈", description: "Track performance metrics to make data-driven decisions and optimize results." },
      ],
    },
    {
      id: "s4",
      type: "checklist",
      title: "Your Marketing Channels Checklist",
      items: [
        { text: "Search Engine Optimization (SEO) — drive organic traffic through better content and structure.", checked: true },
        { text: "Pay-Per-Click Advertising (PPC) — reach audiences instantly with targeted paid ads." },
        { text: "Social Media Marketing — build brand awareness and community on the right platforms." },
        { text: "Email Marketing — nurture leads and retain customers with personalized messages." },
        { text: "Content Marketing — attract and engage audiences through valuable, relevant content." },
        { text: "Analytics & Reporting — measure performance and make data-driven decisions." },
        { text: "Conversion Rate Optimization — turn more visitors into customers through testing." },
      ],
    },
    {
      id: "s5",
      type: "text-image",
      title: "Setting SMART Marketing Goals",
      body: "Every successful campaign begins with a clear goal. The SMART framework — Specific, Measurable, Achievable, Relevant, and Time-bound — helps you turn vague ambitions into concrete, actionable targets that your whole team can rally around.",
    },
    {
      id: "s6",
      type: "text-only",
      title: "SEO: The Foundation of Visibility",
      body: "Search Engine Optimization is the practice of improving your website so it appears higher in search results. Unlike paid ads, SEO builds lasting visibility. It involves optimizing your content, site structure, and earning links from other reputable sites.",
    },
    {
      id: "s7",
      type: "quiz",
      title: "Knowledge Check",
      body: "Let's test what you've learned so far.",
      quizQuestion: "Which of the following best describes a SMART marketing goal?",
      quizOptions: [
        "Get more website visitors",
        "Increase organic traffic by 30% within 90 days",
        "Improve our social media presence",
        "Sell more products online",
      ],
      correctAnswer: 1,
    },
    {
      id: "s8",
      type: "text-image",
      title: "Social Media: Choose Wisely",
      body: "Not every platform is right for every brand. Instagram and TikTok thrive on visual content and younger audiences. LinkedIn dominates B2B conversations. Twitter drives real-time discussion. Focus on where your audience already spends their time.",
    },
    {
      id: "s9",
      type: "checklist",
      title: "Content Strategy Essentials",
      items: [
        { text: "Define your brand voice — consistent, recognizable, and authentic.", checked: true },
        { text: "Create a content calendar to plan posts and campaigns in advance." },
        { text: "Mix content types: educational, entertaining, promotional, and behind-the-scenes." },
        { text: "Repurpose content across formats — blogs to videos to infographics." },
        { text: "Engage genuinely with comments and messages to build community." },
        { text: "Track performance metrics to understand what resonates with your audience." },
      ],
    },
    {
      id: "s10",
      type: "text-only",
      title: "Email Marketing: Your Most Valuable Channel",
      body: "Your email list is one of the few digital assets you truly own. Unlike social media followers, email subscribers aren't subject to algorithm changes. With the right strategy — compelling subject lines, personalized content, and clear CTAs — email consistently delivers the highest ROI of any digital channel.",
    },
    {
      id: "s11",
      type: "quiz",
      title: "Final Assessment",
      body: "You've made it to the final quiz! Let's see what you've learned.",
      quizQuestion: "What is the primary advantage of email marketing over social media marketing?",
      quizOptions: [
        "It reaches a larger audience instantly",
        "You own your subscriber list and aren't subject to algorithm changes",
        "It requires less creative effort to produce",
        "It is always free to use",
      ],
      correctAnswer: 1,
    },
    {
      id: "s12",
      type: "title",
      title: "Congratulations! 🎉",
      subtitle: "You've completed Digital Marketing Fundamentals. You're now equipped with the knowledge to build and execute effective digital marketing campaigns.",
      buttonLabel: "Restart Course",
    },
  ],
};
