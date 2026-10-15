import "./globals.css";
import Chatbot from "@/components/Chatbot";
import { LangProvider } from "@/components/LangContext";
export const metadata = { title: "Skillhub - One Platform to Learn Every Skill",
  description: "Learn any skill, in your language. Courses, mentors, payments, certificates." };
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <LangProvider>{children}<Chatbot /></LangProvider>
      </body>
    </html>
  );
}