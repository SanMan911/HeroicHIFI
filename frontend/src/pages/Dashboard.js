import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import { motion } from "framer-motion";
import { LayoutDashboard } from "lucide-react";

export default function Dashboard() {
  const { user, loading } = useAuth();
  const { lang } = useLang();
  const t = translations[lang].dashboard;

  if (loading) return <div className="min-h-screen flex items-center justify-center text-stone-400">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen py-12" data-testid="dashboard-page">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center">
              <LayoutDashboard className="w-6 h-6 text-[#1E56A0]" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">
                {t.title}
              </h1>
              <p className="text-sm text-stone-500">{t.welcome}, {user.name || user.email}</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-8 sm:p-12 border border-sky-100 shadow-sm text-center" data-testid="dashboard-placeholder">
            <div className="w-20 h-20 rounded-full bg-[#EBF3F9] flex items-center justify-center mx-auto mb-6">
              <LayoutDashboard className="w-10 h-10 text-stone-300" />
            </div>
            <p className="text-base text-stone-500 leading-relaxed max-w-md mx-auto">{t.placeholder}</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
