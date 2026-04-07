import { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { KeyRound, CheckCircle, Mail, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export default function ResetPassword() {
  const { lang } = useLang();
  const t = translations[lang].reset;
  const [searchParams] = useSearchParams();
  const tokenParam = searchParams.get("token") || "";
  const emailParam = searchParams.get("email") || "";

  const [step, setStep] = useState(tokenParam ? "reset" : "request");
  const [email, setEmail] = useState(emailParam);
  const [token, setToken] = useState(tokenParam);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [debugLink, setDebugLink] = useState(null);

  const handleRequest = async (e) => {
    e.preventDefault();
    if (!email) { toast.error(t.enter_email); return; }
    setLoading(true);
    try {
      const { data } = await api.post("/auth/forgot-password", { email });
      toast.success(data.message);
      if (data.debug_link) setDebugLink(data.debug_link);
      if (!data.email_sent) {
        const url = new URL(data.debug_link);
        setToken(url.searchParams.get("token") || "");
        setStep("reset");
      }
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setLoading(false); }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) { toast.error(t.mismatch); return; }
    if (newPassword.length < 6) { toast.error(t.too_short); return; }
    setLoading(true);
    try {
      const { data } = await api.post("/auth/reset-password", { email, token, new_password: newPassword });
      toast.success(data.message);
      setDone(true);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setLoading(false); }
  };

  if (done) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" data-testid="reset-password-page">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="max-w-md w-full text-center">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-semibold text-[#0D2847] mb-3" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.success_title}</h2>
          <p className="text-sm text-slate-500 mb-6">{t.success_msg}</p>
          <Link to="/login"><Button className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full px-8" data-testid="reset-go-login">{t.go_login}</Button></Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" data-testid="reset-password-page">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-md w-full">
        <Link to="/login" className="flex items-center gap-1 text-sm text-slate-500 hover:text-[#1E56A0] mb-6" data-testid="reset-back-to-login">
          <ArrowLeft className="w-4 h-4" /> {t.back_to_login}
        </Link>
        <div className="w-14 h-14 rounded-full bg-[#1E56A0]/10 flex items-center justify-center mx-auto mb-4">
          <KeyRound className="w-7 h-7 text-[#1E56A0]" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-semibold text-[#0D2847] text-center mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
          {step === "request" ? t.request_title : t.reset_title}
        </h1>
        <p className="text-sm text-slate-500 text-center mb-6">
          {step === "request" ? t.request_subtitle : t.reset_subtitle}
        </p>

        {step === "request" ? (
          <form onSubmit={handleRequest} className="space-y-5">
            <div>
              <Label className="text-sm font-medium text-slate-700">{t.email_label}</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5 rounded-xl" data-testid="reset-email-input" required />
            </div>
            <Button type="submit" disabled={loading} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3" data-testid="reset-send-btn">
              {loading ? "..." : t.send_link}
            </Button>
            {debugLink && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-center">
                <p className="text-xs text-amber-700">{t.debug_notice}</p>
                <p className="text-xs text-amber-800 mt-1 break-all" data-testid="reset-debug-link">{debugLink}</p>
              </div>
            )}
          </form>
        ) : (
          <form onSubmit={handleReset} className="space-y-5">
            <div>
              <Label className="text-sm font-medium text-slate-700">{t.new_password}</Label>
              <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="mt-1.5 rounded-xl" data-testid="reset-new-password" required />
            </div>
            <div>
              <Label className="text-sm font-medium text-slate-700">{t.confirm_password}</Label>
              <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="mt-1.5 rounded-xl" data-testid="reset-confirm-password" required />
            </div>
            <Button type="submit" disabled={loading} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3" data-testid="reset-submit-btn">
              {loading ? "..." : t.reset_btn}
            </Button>
          </form>
        )}
      </motion.div>
    </div>
  );
}
