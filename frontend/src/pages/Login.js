import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { MEDIA } from "../data/missions";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, ShieldCheck, Mail } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { lang } = useLang();
  const t = translations[lang].login;
  const tHero = translations[lang].hero;
  const [isRegister, setIsRegister] = useState(false);
  const [regStep, setRegStep] = useState(1);
  const [form, setForm] = useState({ name: "", email: "", password: "", phone: "", age: "", dob: "", address: "", pan_number: "", aadhaar_number: "", role: "member" });
  const [otp, setOtp] = useState("");
  const [otpToken, setOtpToken] = useState("");
  const [otpDebug, setOtpDebug] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const updated = { ...form, [e.target.name]: e.target.value };
    if (e.target.name === "dob" && e.target.value) {
      const birth = new Date(e.target.value);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
      updated.age = age > 0 ? String(age) : "";
    }
    setForm(updated);
    setError("");
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      await login(form.email, form.password);
      toast.success(t.login_success);
      navigate("/dashboard");
    } catch (err) {
      const msg = formatApiError(err.response?.data?.detail, err);
      setError(msg); toast.error(msg);
    } finally { setLoading(false); }
  };

  const handleSendOtp = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.password || !form.phone || !form.pan_number || !form.aadhaar_number) {
      setError(t.fill_mandatory); return;
    }
    setLoading(true); setError("");
    try {
      const { data } = await api.post("/auth/send-otp", { email: form.email, purpose: "registration" });
      toast.success(data.message);
      if (data.otp_debug) setOtpDebug(data.otp_debug);
      setRegStep(2);
    } catch (err) {
      const msg = formatApiError(err.response?.data?.detail, err);
      setError(msg); toast.error(msg);
    } finally { setLoading(false); }
  };

  const handleVerifyAndRegister = async (e) => {
    e.preventDefault();
    if (!otp) { setError(t.enter_otp_err); return; }
    setLoading(true); setError("");
    try {
      const { data: verifyData } = await api.post("/auth/verify-otp", { email: form.email, otp, purpose: "registration" });
      const { data: regData } = await api.post("/auth/register", {
        ...form, age: form.age ? parseInt(form.age) : null, otp_token: verifyData.otp_token,
      });
      localStorage.setItem("hhf_token", regData.token);
      localStorage.setItem("hhf_user", JSON.stringify(regData.user));
      toast.success(t.account_created);
      window.location.href = "/dashboard";
    } catch (err) {
      const msg = formatApiError(err.response?.data?.detail, err);
      setError(msg); toast.error(msg);
    } finally { setLoading(false); }
  };

  const switchMode = () => { setIsRegister(!isRegister); setRegStep(1); setError(""); setOtp(""); setOtpDebug(null); };

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
            {tHero.subtitle.split(".")[0]}.
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-12 overflow-y-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <img src={MEDIA.logo} alt="Logo" className="w-12 h-auto rounded-lg" />
            <span className="text-lg font-semibold text-[#1E56A0]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Heroic HIFI Foundation</span>
          </div>

          {!isRegister ? (
            <>
              <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="login-title">{t.title}</h1>
              <p className="text-sm text-slate-500 mb-8">{t.subtitle}</p>
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-3 mb-6" data-testid="login-error">{error}</div>}
              <form onSubmit={handleLogin} className="space-y-5" data-testid="login-form">
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.email}</Label>
                  <Input name="email" type="email" value={form.email} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="login-email-input" required />
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.password}</Label>
                  <Input name="password" type="password" value={form.password} onChange={handleChange} className="mt-1.5 rounded-xl" data-testid="login-password-input" required />
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3 text-base font-medium" data-testid="login-submit-btn">
                  {loading ? "..." : t.login_btn}
                </Button>
              </form>
              <div className="text-center mt-4">
                <Link to="/reset-password" className="text-sm text-[#1E56A0] hover:underline" data-testid="forgot-password-link">
                  {lang === "hi" ? "पासवर्ड भूल गए?" : "Forgot Password?"}
                </Link>
              </div>
              <p className="text-sm text-slate-500 mt-4 text-center">
                {t.register_prompt}{" "}
                <button onClick={switchMode} className="text-[#1E56A0] font-medium hover:underline" data-testid="toggle-auth-mode">{t.register_link}</button>
              </p>
            </>
          ) : regStep === 1 ? (
            <>
              <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="register-title">{t.register_title}</h1>
              <p className="text-sm text-slate-500 mb-6">{t.register_subtitle}</p>
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-3 mb-4">{error}</div>}
              <form onSubmit={handleSendOtp} className="space-y-4" data-testid="register-form">
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.name} *</Label>
                  <Input name="name" value={form.name} onChange={handleChange} className="mt-1 rounded-xl" data-testid="register-name-input" required />
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.email} *</Label>
                  <Input name="email" type="email" value={form.email} onChange={handleChange} className="mt-1 rounded-xl" data-testid="register-email-input" required />
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.password} *</Label>
                  <Input name="password" type="password" value={form.password} onChange={handleChange} className="mt-1 rounded-xl" data-testid="register-password-input" required />
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.phone} *</Label>
                  <Input name="phone" value={form.phone} onChange={handleChange} className="mt-1 rounded-xl" data-testid="register-phone-input" required />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.dob}</Label>
                    <Input name="dob" type="date" value={form.dob} onChange={handleChange} className="mt-1 rounded-xl" data-testid="register-dob-input" />
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.age}</Label>
                    <Input name="age" type="number" value={form.age} readOnly className="mt-1 rounded-xl bg-slate-50" data-testid="register-age-input" placeholder={lang === "hi" ? "DOB से ऑटो" : "Auto from DOB"} />
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.address}</Label>
                  <Input name="address" value={form.address} onChange={handleChange} className="mt-1 rounded-xl" data-testid="register-address-input" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.pan_label} *</Label>
                    <Input name="pan_number" value={form.pan_number} onChange={handleChange} placeholder="ABCDE1234F" className="mt-1 rounded-xl" data-testid="register-pan-input" required />
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.aadhaar_label} *</Label>
                    <Input name="aadhaar_number" value={form.aadhaar_number} onChange={handleChange} placeholder="1234 5678 9012" className="mt-1 rounded-xl" data-testid="register-aadhaar-input" required />
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{lang === "hi" ? "मैं पंजीकरण कर रहा/रही हूँ:" : "I am registering as:"} *</Label>
                  <div className="flex gap-3 mt-2">
                    <button type="button" onClick={() => setForm({ ...form, role: "member" })}
                      className={`flex-1 p-3 rounded-xl border-2 text-center transition-all ${form.role === "member" ? "border-[#1E56A0] bg-[#1E56A0]/5" : "border-sky-100 hover:border-sky-200"}`}
                      data-testid="role-member-btn">
                      <p className="text-sm font-medium text-[#0D2847]">{lang === "hi" ? "सदस्य" : "Member"}</p>
                      <p className="text-[10px] text-slate-400 mt-1">{lang === "hi" ? "अपडेट और दान" : "Updates & donations"}</p>
                    </button>
                    <button type="button" onClick={() => setForm({ ...form, role: "volunteer" })}
                      className={`flex-1 p-3 rounded-xl border-2 text-center transition-all ${form.role === "volunteer" ? "border-[#1E56A0] bg-[#1E56A0]/5" : "border-sky-100 hover:border-sky-200"}`}
                      data-testid="role-volunteer-btn">
                      <p className="text-sm font-medium text-[#0D2847]">{lang === "hi" ? "स्वयंसेवक" : "Volunteer"}</p>
                      <p className="text-[10px] text-slate-400 mt-1">{lang === "hi" ? "सक्रिय भागीदारी" : "Active participation"}</p>
                    </button>
                  </div>
                </div>
                <div className="bg-sky-50 border border-sky-200 rounded-xl p-3 flex gap-2 items-start">
                  <ShieldCheck className="w-4 h-4 text-[#1E56A0] mt-0.5 shrink-0" />
                  <p className="text-xs text-slate-600">{t.pan_aadhaar_note}</p>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3 text-base font-medium" data-testid="register-send-otp-btn">
                  {loading ? t.sending_otp : t.verify_register} <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </form>
              <p className="text-sm text-slate-500 mt-6 text-center">
                {t.login_prompt}{" "}
                <button onClick={switchMode} className="text-[#1E56A0] font-medium hover:underline" data-testid="toggle-auth-mode">{t.login_link}</button>
              </p>
            </>
          ) : (
            <>
              <button onClick={() => setRegStep(1)} className="flex items-center gap-1 text-sm text-slate-500 hover:text-[#1E56A0] mb-6" data-testid="back-to-form-btn">
                <ArrowLeft className="w-4 h-4" /> {t.back_to_form}
              </button>
              <div className="w-14 h-14 rounded-full bg-[#1E56A0]/10 flex items-center justify-center mx-auto mb-4">
                <Mail className="w-7 h-7 text-[#1E56A0]" />
              </div>
              <h2 className="text-2xl font-semibold text-[#0D2847] text-center mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.verify_email}</h2>
              <p className="text-sm text-slate-500 text-center mb-6">
                {t.otp_sent_to} <strong className="text-[#0D2847]">{form.email}</strong>
              </p>
              {otpDebug && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 text-center">
                  <p className="text-xs text-amber-700">{t.debug_otp_notice}</p>
                  <p className="text-2xl font-bold text-amber-800 tracking-[0.3em] mt-1" data-testid="debug-otp">{otpDebug}</p>
                </div>
              )}
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-3 mb-4">{error}</div>}
              <form onSubmit={handleVerifyAndRegister} className="space-y-5">
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.enter_otp}</Label>
                  <Input value={otp} onChange={(e) => { setOtp(e.target.value); setError(""); }} placeholder="000000" maxLength={6}
                    className="mt-1.5 rounded-xl text-center text-2xl tracking-[0.3em] font-semibold" data-testid="otp-input" required />
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full py-3 text-base font-medium" data-testid="verify-otp-btn">
                  {loading ? t.verifying : t.verify_create}
                </Button>
                <button type="button" onClick={handleSendOtp} className="block w-full text-center text-sm text-[#1E56A0] hover:underline" data-testid="resend-otp-btn">
                  {t.resend_otp}
                </button>
              </form>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}
