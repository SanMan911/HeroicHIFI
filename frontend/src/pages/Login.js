import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { MEDIA } from "../data/missions";
import { motion } from "framer-motion";
import { toast } from "sonner";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const { lang } = useLang();
  const t = translations[lang].login;
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => { setForm({ ...form, [e.target.name]: e.target.value }); setError(""); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (isRegister) {
        await register(form.name, form.email, form.password);
      } else {
        await login(form.email, form.password);
      }
      toast.success(isRegister ? "Account created successfully!" : "Logged in successfully!");
      navigate("/dashboard");
    } catch (err) {
      const msg = formatApiError(err.response?.data?.detail) || err.message;
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      <div className="hidden lg:flex lg:w-1/2 relative">
        <img src={MEDIA.volunteers} alt="" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-[#1E56A0]/80" />
        <div className="relative z-10 flex flex-col justify-center px-16">
          <img src={MEDIA.logo} alt="Logo" className="w-20 h-auto rounded-xl mb-8" />
          <h2 className="text-4xl font-semibold text-white tracking-tight mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            Heroic HIFI Foundation
          </h2>
          <p className="text-lg text-blue-200 leading-relaxed">
            {lang === "hi" ? "हृदय और उद्देश्य से मानवता की सेवा" : "Serving Humanity with Heart & Purpose"}
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <img src={MEDIA.logo} alt="Logo" className="w-12 h-auto rounded-lg" />
            <span className="text-lg font-semibold text-[#1E56A0]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Heroic HIFI Foundation</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="login-title">
            {isRegister ? t.register_title : t.title}
          </h1>
          <p className="text-sm text-stone-500 mb-8">{isRegister ? t.register_subtitle : t.subtitle}</p>

          {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-3 mb-6" data-testid="login-error">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-5" data-testid="login-form">
            {isRegister && (
              <div>
                <Label htmlFor="login-name" className="text-sm font-medium text-stone-700">{t.name}</Label>
                <Input id="login-name" name="name" value={form.name} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="login-name-input" required />
              </div>
            )}
            <div>
              <Label htmlFor="login-email" className="text-sm font-medium text-stone-700">{t.email}</Label>
              <Input id="login-email" name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="login-email-input" required />
            </div>
            <div>
              <Label htmlFor="login-password" className="text-sm font-medium text-stone-700">{t.password}</Label>
              <Input id="login-password" name="password" type="password" value={form.password} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="login-password-input" required />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#1E56A0] hover:bg-[#1E56A0]/90 text-white rounded-full py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
              data-testid="login-submit-btn"
            >
              {loading ? "..." : isRegister ? t.register_btn : t.login_btn}
            </Button>
          </form>

          <p className="text-sm text-stone-500 mt-6 text-center">
            {isRegister ? t.login_prompt : t.register_prompt}{" "}
            <button onClick={() => { setIsRegister(!isRegister); setError(""); }} className="text-[#1E56A0] font-medium hover:underline" data-testid="toggle-auth-mode">
              {isRegister ? t.login_link : t.register_link}
            </button>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
