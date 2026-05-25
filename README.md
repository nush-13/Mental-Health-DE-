Key Features
 Emotional Intelligence

    Intelligent Mood Logging: Log daily moods with intensity tracking and automated sentiment analysis.
    Private Journal Vault: A secure space for thoughts with AI summaries and theme extraction.
    Sentiment Mapping: Continuous emotional trend analysis powered by NLP.

 Holistic Wellness

    Mind Sanctuary: Comprehensive meditation hub with session tracking and mindfulness stats.
    Habit Architecture: Streak-based habit tracking for consistent personal growth.
    Gamified Progress: XP and Level systems to maintain user engagement and milestone rewards.

🤖 AI-Driven Therapy

    Virtual Therapist: 24/7 preparation and reflection support powered by Google Gemini.
    Therapeutic Modules: Multi-day journeys covering Anxiety, Mood Disorders, Trauma, and more.
    Dynamic Assessments: Smart quizzes that calculate clinical severity and provide AI-generated reflections.

Tech Stack 
Layer 	Technology
Framework 	Next.js 14 (App Router) / React 18
Language 	TypeScript
Database 	SQLite + Prisma ORM
Auth 	NextAuth.js
AI/ML 	Google Gemini API (Gen AI SDK)
Design 	Tailwind CSS (Glassmorphism)
Charts 	Chart.js & react-chartjs-2


    NextAuth Integration: Secure profile management with Prisma adapters.
    Service Layer: Decoupled API logic in /app/api for Mood analysis, Habit tracking, and AI reflections.
    Gamification Engine: Centralized context provider (GamificationProvider) managing global user state.
    Static Content CMS: lib/therapyContent.ts serves as the centralized source for therapeutic curriculum.


    1:N Relationships: A single User owns multiple Mood logs, Journal entries, Habits, and Therapy progress records.
    Relational Integrity: Uses Cascade Deletes to ensure data consistency across the User profile.
    Persistence: Efficient data fetching via Prisma Client singletons.

