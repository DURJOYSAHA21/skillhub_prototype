import "./globals.css";
export const metadata = { title: "Skillhub - One Platform to Learn Every Skill",
  description: "Learn any skill, in your language. Courses, mentors, payments, certificates." };
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
