const STR = {
  en: { home: "Home", browse: "Browse Courses", match: "Find a Mentor", dashboard: "Dashboard",
    chat: "Chat", profile: "Profile", login: "Login", signup: "Sign Up", logout: "Logout",
    search: "Search", enroll: "Enroll", pay: "Pay & Enroll", free: "Free", lessons: "Lessons",
    quiz: "Quiz", assignment: "Assignment", progress: "Progress", certificate: "Certificate",
    myCourses: "My Courses", transactions: "My Transactions", welcome: "Welcome to Skillhub",
    tagline: "One Platform to Learn Every Skill - in your language." },
  bn: { home: "হোম", browse: "কোর্স দেখুন", match: "মেন্টর খুঁজুন", dashboard: "ড্যাশবোর্ড",
    chat: "চ্যাট", profile: "প্রোফাইল", login: "লগইন", signup: "সাইনআপ", logout: "লগআউট",
    search: "খুঁজুন", enroll: "ভর্তি হন", pay: "পেমেন্ট ও ভর্তি", free: "ফ্রি", lessons: "পাঠ",
    quiz: "কুইজ", assignment: "অ্যাসাইনমেন্ট", progress: "অগ্রগতি", certificate: "সনদ",
    myCourses: "আমার কোর্স", transactions: "আমার লেনদেন", welcome: "স্কিলহাবে স্বাগতম",
    tagline: "একটি প্ল্যাটফর্মে সব দক্ষতা শিখুন - আপনার ভাষায়।" },
};
export function t(lang, key) {
  return (STR[lang] || STR.en)[key] || STR.en[key] || key;
}
